"""
측정 세션 모듈

측정 세션을 관리하고 데이터를 기록합니다.
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import numpy as np
import threading
import time


class SessionState(Enum):
    """세션 상태"""
    IDLE = "idle"
    CONFIGURED = "configured"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class TriggerMode(Enum):
    """트리거 모드"""
    IMMEDIATE = "immediate"     # 즉시 시작
    SOFTWARE = "software"       # 소프트웨어 트리거
    LEVEL = "level"            # 레벨 트리거
    EDGE = "edge"              # 에지 트리거
    EXTERNAL = "external"       # 외부 트리거


@dataclass
class TriggerConfig:
    """트리거 설정"""
    mode: TriggerMode = TriggerMode.IMMEDIATE
    channel_id: int = 0
    level: float = 0.0
    hysteresis: float = 0.1
    edge: str = "rising"  # "rising" or "falling"
    pre_trigger_samples: int = 0
    post_trigger_samples: int = 1000


@dataclass
class SessionConfig:
    """세션 설정"""
    name: str = "Measurement Session"
    description: str = ""
    sampling_rate: float = 1000.0  # Hz
    duration: Optional[float] = None  # 측정 시간 (초), None이면 무한
    buffer_size: int = 10000
    trigger: TriggerConfig = field(default_factory=TriggerConfig)
    auto_save: bool = False
    save_path: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class SessionStatistics:
    """세션 통계"""
    total_samples: int = 0
    elapsed_time: float = 0.0
    trigger_count: int = 0
    overflow_count: int = 0
    error_count: int = 0
    min_value: float = float('inf')
    max_value: float = float('-inf')
    mean_value: float = 0.0
    std_value: float = 0.0


class MeasurementSession:
    """
    측정 세션 관리자

    측정 세션의 시작, 중지, 데이터 기록을 관리합니다.

    Example:
        >>> session = MeasurementSession()
        >>> session.configure(SessionConfig(name="Test", sampling_rate=10000))
        >>> session.add_channel(ch1)
        >>> session.add_channel(ch2)
        >>> session.start()
        >>> # ... 데이터 수집 ...
        >>> session.stop()
        >>> data = session.get_data()
    """

    def __init__(self):
        """초기화"""
        self._config: Optional[SessionConfig] = None
        self._state = SessionState.IDLE
        self._channels: Dict[int, Any] = {}  # MeasurementChannel

        # 데이터 버퍼
        self._data_buffers: Dict[int, List[float]] = {}
        self._timestamp_buffer: List[float] = []

        # 타이밍
        self._start_time: Optional[datetime] = None
        self._stop_time: Optional[datetime] = None
        self._pause_time: Optional[datetime] = None
        self._total_pause_duration: float = 0.0

        # 통계
        self._statistics = SessionStatistics()

        # 콜백
        self._on_data_callback: Optional[Callable] = None
        self._on_trigger_callback: Optional[Callable] = None
        self._on_error_callback: Optional[Callable] = None

        # 스레드 제어
        self._acquisition_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # 잠금
        self._lock = threading.Lock()

    @property
    def state(self) -> SessionState:
        """현재 상태"""
        return self._state

    @property
    def config(self) -> Optional[SessionConfig]:
        """세션 설정"""
        return self._config

    @property
    def statistics(self) -> SessionStatistics:
        """세션 통계"""
        return self._statistics

    def configure(self, config: SessionConfig) -> None:
        """
        세션 설정

        Args:
            config: 세션 설정
        """
        if self._state == SessionState.RUNNING:
            raise RuntimeError("실행 중인 세션은 설정할 수 없습니다.")

        self._config = config
        self._state = SessionState.CONFIGURED

        # 버퍼 초기화
        for channel_id in self._channels:
            self._data_buffers[channel_id] = []
        self._timestamp_buffer = []

        # 통계 초기화
        self._statistics = SessionStatistics()

    def add_channel(self, channel: Any) -> None:
        """
        채널 추가

        Args:
            channel: MeasurementChannel 인스턴스
        """
        if self._state == SessionState.RUNNING:
            raise RuntimeError("실행 중에는 채널을 추가할 수 없습니다.")

        self._channels[channel.channel_id] = channel
        self._data_buffers[channel.channel_id] = []

    def remove_channel(self, channel_id: int) -> None:
        """채널 제거"""
        if self._state == SessionState.RUNNING:
            raise RuntimeError("실행 중에는 채널을 제거할 수 없습니다.")

        if channel_id in self._channels:
            del self._channels[channel_id]
            del self._data_buffers[channel_id]

    def get_channels(self) -> Dict[int, Any]:
        """모든 채널 반환"""
        return self._channels.copy()

    def set_on_data_callback(self, callback: Callable[[Dict[int, float], float], None]) -> None:
        """데이터 수신 콜백 설정"""
        self._on_data_callback = callback

    def set_on_trigger_callback(self, callback: Callable[[float], None]) -> None:
        """트리거 콜백 설정"""
        self._on_trigger_callback = callback

    def set_on_error_callback(self, callback: Callable[[Exception], None]) -> None:
        """에러 콜백 설정"""
        self._on_error_callback = callback

    def start(self) -> None:
        """세션 시작"""
        if self._state not in [SessionState.CONFIGURED, SessionState.STOPPED]:
            raise RuntimeError(f"현재 상태({self._state.value})에서는 시작할 수 없습니다.")

        if not self._channels:
            raise RuntimeError("최소 하나의 채널이 필요합니다.")

        self._state = SessionState.RUNNING
        self._start_time = datetime.now()
        self._stop_event.clear()

        # 버퍼 초기화
        for channel_id in self._channels:
            self._data_buffers[channel_id] = []
        self._timestamp_buffer = []
        self._statistics = SessionStatistics()

    def stop(self) -> None:
        """세션 중지"""
        if self._state != SessionState.RUNNING and self._state != SessionState.PAUSED:
            return

        self._stop_event.set()
        self._state = SessionState.STOPPED
        self._stop_time = datetime.now()

        # 통계 업데이트
        if self._start_time:
            self._statistics.elapsed_time = (
                self._stop_time - self._start_time
            ).total_seconds() - self._total_pause_duration

    def pause(self) -> None:
        """세션 일시정지"""
        if self._state != SessionState.RUNNING:
            return

        self._state = SessionState.PAUSED
        self._pause_time = datetime.now()

    def resume(self) -> None:
        """세션 재개"""
        if self._state != SessionState.PAUSED:
            return

        if self._pause_time:
            self._total_pause_duration += (datetime.now() - self._pause_time).total_seconds()

        self._state = SessionState.RUNNING
        self._pause_time = None

    def add_sample(self, channel_id: int, value: float, timestamp: Optional[float] = None) -> None:
        """
        샘플 추가 (외부 데이터 소스용)

        Args:
            channel_id: 채널 ID
            value: 측정값
            timestamp: 타임스탬프 (없으면 자동 생성)
        """
        if self._state != SessionState.RUNNING:
            return

        with self._lock:
            if channel_id not in self._data_buffers:
                return

            # 버퍼 크기 제한
            if self._config and len(self._data_buffers[channel_id]) >= self._config.buffer_size:
                self._data_buffers[channel_id].pop(0)
                self._statistics.overflow_count += 1

            self._data_buffers[channel_id].append(value)

            # 타임스탬프
            if timestamp is None:
                if self._start_time:
                    timestamp = (datetime.now() - self._start_time).total_seconds()
                else:
                    timestamp = 0.0

            if channel_id == list(self._channels.keys())[0]:  # 첫 번째 채널만 타임스탬프 저장
                self._timestamp_buffer.append(timestamp)

            # 통계 업데이트
            self._statistics.total_samples += 1
            self._statistics.min_value = min(self._statistics.min_value, value)
            self._statistics.max_value = max(self._statistics.max_value, value)

            # 콜백 호출
            if self._on_data_callback:
                data = {channel_id: value}
                self._on_data_callback(data, timestamp)

    def add_samples_batch(self, data: Dict[int, List[float]], timestamps: List[float]) -> None:
        """
        배치 샘플 추가

        Args:
            data: {channel_id: [values]} 딕셔너리
            timestamps: 타임스탬프 리스트
        """
        if self._state != SessionState.RUNNING:
            return

        with self._lock:
            for channel_id, values in data.items():
                if channel_id not in self._data_buffers:
                    continue

                self._data_buffers[channel_id].extend(values)

                # 버퍼 크기 제한
                if self._config:
                    overflow = len(self._data_buffers[channel_id]) - self._config.buffer_size
                    if overflow > 0:
                        self._data_buffers[channel_id] = self._data_buffers[channel_id][overflow:]
                        self._statistics.overflow_count += overflow

            self._timestamp_buffer.extend(timestamps)
            if self._config:
                overflow = len(self._timestamp_buffer) - self._config.buffer_size
                if overflow > 0:
                    self._timestamp_buffer = self._timestamp_buffer[overflow:]

            # 통계 업데이트
            for values in data.values():
                self._statistics.total_samples += len(values)
                if values:
                    self._statistics.min_value = min(self._statistics.min_value, min(values))
                    self._statistics.max_value = max(self._statistics.max_value, max(values))

    def get_data(self, channel_id: Optional[int] = None) -> Dict[int, np.ndarray]:
        """
        데이터 조회

        Args:
            channel_id: 특정 채널 ID (None이면 모든 채널)

        Returns:
            Dict[int, np.ndarray]: {channel_id: data_array}
        """
        with self._lock:
            if channel_id is not None:
                if channel_id in self._data_buffers:
                    return {channel_id: np.array(self._data_buffers[channel_id])}
                return {}

            return {
                ch_id: np.array(data)
                for ch_id, data in self._data_buffers.items()
            }

    def get_timestamps(self) -> np.ndarray:
        """타임스탬프 조회"""
        with self._lock:
            return np.array(self._timestamp_buffer)

    def get_latest_samples(self, count: int = 1) -> Dict[int, np.ndarray]:
        """최근 샘플 조회"""
        with self._lock:
            return {
                ch_id: np.array(data[-count:])
                for ch_id, data in self._data_buffers.items()
            }

    def clear_buffer(self) -> None:
        """버퍼 초기화"""
        with self._lock:
            for channel_id in self._data_buffers:
                self._data_buffers[channel_id] = []
            self._timestamp_buffer = []

    def get_session_info(self) -> dict:
        """세션 정보 조회"""
        info = {
            "state": self._state.value,
            "channel_count": len(self._channels),
            "channels": list(self._channels.keys()),
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "stop_time": self._stop_time.isoformat() if self._stop_time else None,
            "statistics": {
                "total_samples": self._statistics.total_samples,
                "elapsed_time": self._statistics.elapsed_time,
                "overflow_count": self._statistics.overflow_count,
                "error_count": self._statistics.error_count,
                "min_value": self._statistics.min_value if self._statistics.min_value != float('inf') else None,
                "max_value": self._statistics.max_value if self._statistics.max_value != float('-inf') else None,
            }
        }

        if self._config:
            info["config"] = {
                "name": self._config.name,
                "description": self._config.description,
                "sampling_rate": self._config.sampling_rate,
                "duration": self._config.duration,
                "buffer_size": self._config.buffer_size,
            }

        return info

    def export_session(self, filepath: str) -> None:
        """세션 데이터 내보내기"""
        import json

        data = self.get_data()
        timestamps = self.get_timestamps()
        info = self.get_session_info()

        export_data = {
            "info": info,
            "timestamps": timestamps.tolist(),
            "data": {str(k): v.tolist() for k, v in data.items()},
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
