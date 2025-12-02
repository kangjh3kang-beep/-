"""
차동측정 핵심 모듈

차동측정(Differential Measurement)은 두 개의 신호 간의 차이를 측정하여
공통 모드 노이즈를 제거하고 정확한 신호를 추출하는 기법입니다.
"""

from typing import List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from datetime import datetime


class MeasurementMode(Enum):
    """측정 모드"""
    SINGLE_ENDED = "single_ended"      # 단일 종단 측정
    DIFFERENTIAL = "differential"       # 차동 측정
    PSEUDO_DIFFERENTIAL = "pseudo_diff" # 유사 차동 측정
    RATIOMETRIC = "ratiometric"         # 비율 측정


class SignalType(Enum):
    """신호 유형"""
    VOLTAGE = "voltage"
    CURRENT = "current"
    RESISTANCE = "resistance"
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    FORCE = "force"
    ACCELERATION = "acceleration"
    CUSTOM = "custom"


@dataclass
class MeasurementChannel:
    """측정 채널 클래스"""

    channel_id: int
    name: str
    signal_type: SignalType = SignalType.VOLTAGE
    unit: str = "V"
    gain: float = 1.0
    offset: float = 0.0
    sampling_rate: float = 1000.0  # Hz
    resolution: int = 16  # bits
    range_min: float = -10.0
    range_max: float = 10.0
    enabled: bool = True

    # 채널 데이터
    _data: np.ndarray = field(default_factory=lambda: np.array([]))
    _timestamps: np.ndarray = field(default_factory=lambda: np.array([]))

    def __post_init__(self):
        """초기화 후 처리"""
        if isinstance(self._data, list):
            self._data = np.array(self._data)
        if isinstance(self._timestamps, list):
            self._timestamps = np.array(self._timestamps)

    def set_data(self, data: Union[List[float], np.ndarray],
                 timestamps: Optional[Union[List[float], np.ndarray]] = None) -> None:
        """채널 데이터 설정"""
        self._data = np.array(data)
        if timestamps is not None:
            self._timestamps = np.array(timestamps)
        else:
            # 타임스탬프가 없으면 샘플링 레이트로 생성
            self._timestamps = np.arange(len(self._data)) / self.sampling_rate

    def get_data(self) -> np.ndarray:
        """보정된 데이터 반환"""
        return self._data * self.gain + self.offset

    def get_raw_data(self) -> np.ndarray:
        """원시 데이터 반환"""
        return self._data

    def get_timestamps(self) -> np.ndarray:
        """타임스탬프 반환"""
        return self._timestamps

    def clear(self) -> None:
        """데이터 초기화"""
        self._data = np.array([])
        self._timestamps = np.array([])

    @property
    def sample_count(self) -> int:
        """샘플 개수"""
        return len(self._data)

    @property
    def duration(self) -> float:
        """측정 기간 (초)"""
        if len(self._timestamps) < 2:
            return 0.0
        return self._timestamps[-1] - self._timestamps[0]


@dataclass
class DifferentialResult:
    """차동측정 결과"""

    differential_signal: np.ndarray
    timestamps: np.ndarray
    common_mode_signal: np.ndarray
    cmrr_db: float  # Common Mode Rejection Ratio (dB)
    snr_improvement_db: float  # SNR 개선 (dB)
    positive_channel: MeasurementChannel
    negative_channel: MeasurementChannel
    measurement_time: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


class DifferentialMeasurement:
    """
    차동측정 클래스

    두 채널의 신호 차이를 계산하여 공통 모드 노이즈를 제거합니다.

    Example:
        >>> dm = DifferentialMeasurement()
        >>> ch_pos = MeasurementChannel(0, "CH+")
        >>> ch_neg = MeasurementChannel(1, "CH-")
        >>> ch_pos.set_data([1.1, 2.2, 3.3])
        >>> ch_neg.set_data([0.1, 0.2, 0.3])
        >>> result = dm.measure(ch_pos, ch_neg)
        >>> print(result.differential_signal)  # [1.0, 2.0, 3.0]
    """

    def __init__(self,
                 mode: MeasurementMode = MeasurementMode.DIFFERENTIAL,
                 averaging_count: int = 1,
                 auto_zero: bool = False):
        """
        초기화

        Args:
            mode: 측정 모드
            averaging_count: 평균화 횟수
            auto_zero: 자동 영점 조정 여부
        """
        self.mode = mode
        self.averaging_count = averaging_count
        self.auto_zero = auto_zero

        self._zero_offset_pos = 0.0
        self._zero_offset_neg = 0.0
        self._calibration_factor = 1.0

        # 사용자 정의 전처리/후처리 함수
        self._preprocessor: Optional[Callable] = None
        self._postprocessor: Optional[Callable] = None

    def set_preprocessor(self, func: Callable[[np.ndarray], np.ndarray]) -> None:
        """전처리 함수 설정"""
        self._preprocessor = func

    def set_postprocessor(self, func: Callable[[np.ndarray], np.ndarray]) -> None:
        """후처리 함수 설정"""
        self._postprocessor = func

    def calibrate_zero(self,
                       positive_channel: MeasurementChannel,
                       negative_channel: MeasurementChannel) -> Tuple[float, float]:
        """
        영점 보정

        입력이 단락되었을 때의 오프셋을 측정하여 저장합니다.
        """
        pos_data = positive_channel.get_data()
        neg_data = negative_channel.get_data()

        self._zero_offset_pos = np.mean(pos_data)
        self._zero_offset_neg = np.mean(neg_data)

        return self._zero_offset_pos, self._zero_offset_neg

    def measure(self,
                positive_channel: MeasurementChannel,
                negative_channel: MeasurementChannel,
                apply_calibration: bool = True) -> DifferentialResult:
        """
        차동측정 수행

        Args:
            positive_channel: 양극 채널
            negative_channel: 음극 채널
            apply_calibration: 보정 적용 여부

        Returns:
            DifferentialResult: 차동측정 결과
        """
        # 데이터 가져오기
        pos_data = positive_channel.get_data().copy()
        neg_data = negative_channel.get_data().copy()
        timestamps = positive_channel.get_timestamps()

        # 길이 확인 및 조정
        min_len = min(len(pos_data), len(neg_data))
        pos_data = pos_data[:min_len]
        neg_data = neg_data[:min_len]
        timestamps = timestamps[:min_len]

        # 전처리 적용
        if self._preprocessor:
            pos_data = self._preprocessor(pos_data)
            neg_data = self._preprocessor(neg_data)

        # 자동 영점 보정
        if self.auto_zero and apply_calibration:
            pos_data = pos_data - self._zero_offset_pos
            neg_data = neg_data - self._zero_offset_neg

        # 차동 신호 계산
        if self.mode == MeasurementMode.DIFFERENTIAL:
            differential = pos_data - neg_data
        elif self.mode == MeasurementMode.PSEUDO_DIFFERENTIAL:
            # 유사 차동: 음극을 기준 전압으로 사용
            differential = pos_data - np.mean(neg_data)
        elif self.mode == MeasurementMode.RATIOMETRIC:
            # 비율 측정
            differential = pos_data / (neg_data + 1e-10)  # 0 나눔 방지
        else:
            # 단일 종단
            differential = pos_data

        # 공통 모드 신호 계산
        common_mode = (pos_data + neg_data) / 2

        # 평균화
        if self.averaging_count > 1:
            kernel = np.ones(self.averaging_count) / self.averaging_count
            differential = np.convolve(differential, kernel, mode='same')

        # 보정 계수 적용
        if apply_calibration:
            differential = differential * self._calibration_factor

        # 후처리 적용
        if self._postprocessor:
            differential = self._postprocessor(differential)

        # CMRR 계산 (dB)
        cm_power = np.mean(common_mode ** 2) + 1e-10
        diff_power = np.mean(differential ** 2) + 1e-10
        cmrr_db = 10 * np.log10(diff_power / cm_power)

        # SNR 개선 추정
        single_noise = np.std(pos_data)
        diff_noise = np.std(differential)
        snr_improvement = 20 * np.log10((single_noise + 1e-10) / (diff_noise + 1e-10))

        return DifferentialResult(
            differential_signal=differential,
            timestamps=timestamps,
            common_mode_signal=common_mode,
            cmrr_db=cmrr_db,
            snr_improvement_db=snr_improvement,
            positive_channel=positive_channel,
            negative_channel=negative_channel,
            metadata={
                "mode": self.mode.value,
                "averaging_count": self.averaging_count,
                "auto_zero": self.auto_zero,
                "calibration_applied": apply_calibration,
            }
        )

    def measure_multi_channel(self,
                              channel_pairs: List[Tuple[MeasurementChannel, MeasurementChannel]],
                              ) -> List[DifferentialResult]:
        """
        다중 채널 차동측정

        Args:
            channel_pairs: (양극, 음극) 채널 쌍의 리스트

        Returns:
            List[DifferentialResult]: 각 채널 쌍의 측정 결과
        """
        results = []
        for pos_ch, neg_ch in channel_pairs:
            result = self.measure(pos_ch, neg_ch)
            results.append(result)
        return results

    def continuous_measure(self,
                          positive_channel: MeasurementChannel,
                          negative_channel: MeasurementChannel,
                          window_size: int = 100,
                          overlap: int = 50) -> List[DifferentialResult]:
        """
        연속 차동측정 (윈도우 기반)

        Args:
            positive_channel: 양극 채널
            negative_channel: 음극 채널
            window_size: 윈도우 크기 (샘플 수)
            overlap: 오버랩 (샘플 수)

        Returns:
            List[DifferentialResult]: 각 윈도우의 측정 결과
        """
        pos_data = positive_channel.get_data()
        neg_data = negative_channel.get_data()
        timestamps = positive_channel.get_timestamps()

        min_len = min(len(pos_data), len(neg_data))
        step = window_size - overlap

        results = []
        for start in range(0, min_len - window_size + 1, step):
            end = start + window_size

            # 임시 채널 생성
            temp_pos = MeasurementChannel(
                positive_channel.channel_id,
                positive_channel.name,
                sampling_rate=positive_channel.sampling_rate
            )
            temp_neg = MeasurementChannel(
                negative_channel.channel_id,
                negative_channel.name,
                sampling_rate=negative_channel.sampling_rate
            )

            temp_pos.set_data(pos_data[start:end], timestamps[start:end])
            temp_neg.set_data(neg_data[start:end], timestamps[start:end])

            result = self.measure(temp_pos, temp_neg)
            results.append(result)

        return results

    def set_calibration_factor(self, factor: float) -> None:
        """보정 계수 설정"""
        self._calibration_factor = factor

    def get_calibration_factor(self) -> float:
        """보정 계수 반환"""
        return self._calibration_factor
