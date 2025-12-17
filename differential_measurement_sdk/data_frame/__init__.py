"""
데이터 프레임 구조 모듈 (Data Frame Structure Module)

원시 데이터 로깅 및 패킷화 (MPK-RDR-MFG-SPEC v2.2 섹션 3.2)

주요 기능:
- 원시 ADC 샘플 + 메타데이터 프레임 구조
- 타임스탬프 관리
- 측정 모드/설정 기록
- NFC 메타데이터 통합
- 바이너리/JSON 직렬화
- 재해석/재학습용 데이터 포맷
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
import struct
import json
import hashlib
import zlib
import numpy as np


class FrameType(Enum):
    """프레임 타입"""
    RAW_SAMPLE = 0x01        # 원시 ADC 샘플
    MEASUREMENT = 0x02       # 측정 결과
    CALIBRATION = 0x03       # 캘리브레이션
    SYSTEM_STATUS = 0x04     # 시스템 상태
    NFC_DATA = 0x05          # NFC 메타데이터
    EVENT_LOG = 0x06         # 이벤트 로그
    MULTI_CHANNEL = 0x07     # 다채널 동시 샘플


class CompressionType(Enum):
    """압축 타입"""
    NONE = 0x00
    ZLIB = 0x01
    LZ4 = 0x02


class ChannelConfig(Enum):
    """채널 구성"""
    SINGLE_ENDED = 0x00
    DIFFERENTIAL = 0x01


@dataclass
class FrameHeader:
    """
    프레임 헤더 (24 bytes)

    모든 데이터 프레임의 공통 헤더
    """
    # 매직 넘버 (4 bytes) - 'MPSK'
    magic: bytes = b'MPSK'

    # 버전 (2 bytes)
    version_major: int = 1
    version_minor: int = 0

    # 프레임 타입 (1 byte)
    frame_type: FrameType = FrameType.RAW_SAMPLE

    # 플래그 (1 byte)
    # Bit 0: 압축 여부
    # Bit 1: 암호화 여부
    # Bit 2-7: 예약
    flags: int = 0

    # 시퀀스 번호 (4 bytes)
    sequence: int = 0

    # 타임스탬프 (8 bytes) - microseconds since epoch
    timestamp_us: int = 0

    # 페이로드 길이 (4 bytes)
    payload_length: int = 0

    HEADER_SIZE: int = 24

    def to_bytes(self) -> bytes:
        """바이트 직렬화"""
        return struct.pack(
            '<4sBBBBIQI',
            self.magic,
            self.version_major,
            self.version_minor,
            self.frame_type.value,
            self.flags,
            self.sequence,
            self.timestamp_us,
            self.payload_length
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> 'FrameHeader':
        """바이트에서 역직렬화"""
        if len(data) < cls.HEADER_SIZE:
            raise ValueError("Insufficient data for header")

        magic, v_maj, v_min, ftype, flags, seq, ts, plen = struct.unpack(
            '<4sBBBBIQI', data[:24]
        )

        return cls(
            magic=magic,
            version_major=v_maj,
            version_minor=v_min,
            frame_type=FrameType(ftype),
            flags=flags,
            sequence=seq,
            timestamp_us=ts,
            payload_length=plen
        )


@dataclass
class ADCConfig:
    """ADC 설정 (8 bytes)"""
    data_rate_code: int = 0      # 1 byte
    gain_code: int = 0           # 1 byte
    channel_positive: int = 0    # 1 byte
    channel_negative: int = 1    # 1 byte
    input_mode: ChannelConfig = ChannelConfig.DIFFERENTIAL  # 1 byte
    buffer_enabled: int = 1      # 1 byte
    reserved: int = 0            # 2 bytes

    def to_bytes(self) -> bytes:
        return struct.pack(
            '<BBBBBBH',
            self.data_rate_code,
            self.gain_code,
            self.channel_positive,
            self.channel_negative,
            self.input_mode.value,
            self.buffer_enabled,
            self.reserved
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> 'ADCConfig':
        dr, gain, ch_p, ch_n, mode, buf, res = struct.unpack('<BBBBBBH', data[:8])
        return cls(
            data_rate_code=dr,
            gain_code=gain,
            channel_positive=ch_p,
            channel_negative=ch_n,
            input_mode=ChannelConfig(mode),
            buffer_enabled=buf,
            reserved=res
        )


@dataclass
class AFEConfig:
    """AFE 설정 (8 bytes)"""
    tia_gain_code: int = 0       # 1 byte
    rload_code: int = 0          # 1 byte
    internal_zero: int = 50      # 1 byte (%)
    bias_sign: int = 0           # 1 byte
    bias_percent: int = 0        # 1 byte
    shorting: int = 0            # 1 byte
    reserved: int = 0            # 2 bytes

    def to_bytes(self) -> bytes:
        return struct.pack(
            '<BBBBBBH',
            self.tia_gain_code,
            self.rload_code,
            self.internal_zero,
            self.bias_sign,
            self.bias_percent,
            self.shorting,
            self.reserved
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> 'AFEConfig':
        tia, rload, zero, sign, bias, short, res = struct.unpack('<BBBBBBH', data[:8])
        return cls(
            tia_gain_code=tia,
            rload_code=rload,
            internal_zero=zero,
            bias_sign=sign,
            bias_percent=bias,
            shorting=short,
            reserved=res
        )


@dataclass
class ModeConfig:
    """측정 모드 설정 (16 bytes)"""
    mode_code: int = 0           # 1 byte (OCP=0, CA=1, CV=2, ...)
    sub_mode: int = 0            # 1 byte
    reserved1: int = 0           # 2 bytes

    # 모드별 파라미터
    param1: float = 0.0          # 4 bytes (예: 전압)
    param2: float = 0.0          # 4 bytes (예: 시간)
    param3: float = 0.0          # 4 bytes (예: 스캔레이트)

    def to_bytes(self) -> bytes:
        return struct.pack(
            '<BBHfff',
            self.mode_code,
            self.sub_mode,
            self.reserved1,
            self.param1,
            self.param2,
            self.param3
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> 'ModeConfig':
        mode, sub, res, p1, p2, p3 = struct.unpack('<BBHfff', data[:16])
        return cls(
            mode_code=mode,
            sub_mode=sub,
            reserved1=res,
            param1=p1,
            param2=p2,
            param3=p3
        )


@dataclass
class EnvironmentData:
    """환경 데이터 (16 bytes)"""
    temperature_c: float = 25.0      # 4 bytes - 보드 온도
    humidity_rh: float = 50.0        # 4 bytes - 습도
    supply_voltage_v: float = 3.7    # 4 bytes - 전원 전압
    battery_soc: float = 100.0       # 4 bytes - 배터리 SOC (%)

    def to_bytes(self) -> bytes:
        return struct.pack(
            '<ffff',
            self.temperature_c,
            self.humidity_rh,
            self.supply_voltage_v,
            self.battery_soc
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> 'EnvironmentData':
        temp, hum, vsup, soc = struct.unpack('<ffff', data[:16])
        return cls(
            temperature_c=temp,
            humidity_rh=hum,
            supply_voltage_v=vsup,
            battery_soc=soc
        )


@dataclass
class NFCMetadata:
    """NFC 메타데이터 (64 bytes)"""
    # UID (8 bytes, 7-byte UID + padding)
    uid: bytes = field(default_factory=lambda: bytes(8))

    # 시리얼/LOT (각 16 bytes)
    serial_number: str = ""
    lot_number: str = ""

    # 캘리브레이션 계수 (8 bytes)
    cal_slope: float = 1.0
    cal_intercept: float = 0.0

    # 사용 정보 (8 bytes)
    max_uses: int = 0
    current_uses: int = 0
    reserved: int = 0

    NFC_META_SIZE: int = 64

    def to_bytes(self) -> bytes:
        data = bytearray(self.NFC_META_SIZE)

        # UID
        data[0:8] = self.uid[:8].ljust(8, b'\x00')

        # Serial
        serial_bytes = self.serial_number[:16].encode('ascii')
        data[8:24] = serial_bytes.ljust(16, b'\x00')

        # LOT
        lot_bytes = self.lot_number[:16].encode('ascii')
        data[24:40] = lot_bytes.ljust(16, b'\x00')

        # Calibration
        data[40:48] = struct.pack('<ff', self.cal_slope, self.cal_intercept)

        # Usage
        data[48:56] = struct.pack('<HHI', self.max_uses, self.current_uses, self.reserved)

        return bytes(data)

    @classmethod
    def from_bytes(cls, data: bytes) -> 'NFCMetadata':
        uid = data[0:8]
        serial = data[8:24].decode('ascii', errors='ignore').strip('\x00')
        lot = data[24:40].decode('ascii', errors='ignore').strip('\x00')
        slope, intercept = struct.unpack('<ff', data[40:48])
        max_u, cur_u, res = struct.unpack('<HHI', data[48:56])

        return cls(
            uid=uid,
            serial_number=serial,
            lot_number=lot,
            cal_slope=slope,
            cal_intercept=intercept,
            max_uses=max_u,
            current_uses=cur_u,
            reserved=res
        )


@dataclass
class RawSampleFrame:
    """
    원시 샘플 프레임

    구조:
    - Header (24 bytes)
    - ADC Config (8 bytes)
    - AFE Config (8 bytes)
    - Mode Config (16 bytes)
    - Environment (16 bytes)
    - NFC Metadata (64 bytes)
    - Sample Count (4 bytes)
    - Raw Samples (N * 4 bytes, int32)
    - Timestamps (N * 4 bytes, uint32, microseconds relative)
    - CRC32 (4 bytes)
    """
    header: FrameHeader
    adc_config: ADCConfig
    afe_config: AFEConfig
    mode_config: ModeConfig
    environment: EnvironmentData
    nfc_metadata: NFCMetadata

    sample_count: int = 0
    raw_samples: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.int32))
    timestamps_us: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.uint32))

    crc32: int = 0

    def calculate_crc(self) -> int:
        """CRC32 계산"""
        data = self.to_bytes_without_crc()
        return zlib.crc32(data) & 0xFFFFFFFF

    def to_bytes_without_crc(self) -> bytes:
        """CRC 제외 직렬화"""
        data = bytearray()

        # 메타데이터
        data.extend(self.header.to_bytes())
        data.extend(self.adc_config.to_bytes())
        data.extend(self.afe_config.to_bytes())
        data.extend(self.mode_config.to_bytes())
        data.extend(self.environment.to_bytes())
        data.extend(self.nfc_metadata.to_bytes())

        # 샘플 수
        data.extend(struct.pack('<I', self.sample_count))

        # 원시 샘플
        data.extend(self.raw_samples.astype(np.int32).tobytes())

        # 타임스탬프
        data.extend(self.timestamps_us.astype(np.uint32).tobytes())

        return bytes(data)

    def to_bytes(self) -> bytes:
        """전체 직렬화 (CRC 포함)"""
        data = self.to_bytes_without_crc()
        self.crc32 = zlib.crc32(data) & 0xFFFFFFFF
        data += struct.pack('<I', self.crc32)
        return data

    @classmethod
    def from_bytes(cls, data: bytes) -> 'RawSampleFrame':
        """역직렬화"""
        offset = 0

        # 헤더
        header = FrameHeader.from_bytes(data[offset:offset + 24])
        offset += 24

        # ADC Config
        adc_config = ADCConfig.from_bytes(data[offset:offset + 8])
        offset += 8

        # AFE Config
        afe_config = AFEConfig.from_bytes(data[offset:offset + 8])
        offset += 8

        # Mode Config
        mode_config = ModeConfig.from_bytes(data[offset:offset + 16])
        offset += 16

        # Environment
        environment = EnvironmentData.from_bytes(data[offset:offset + 16])
        offset += 16

        # NFC Metadata
        nfc_metadata = NFCMetadata.from_bytes(data[offset:offset + 64])
        offset += 64

        # Sample count
        sample_count = struct.unpack('<I', data[offset:offset + 4])[0]
        offset += 4

        # Raw samples
        samples_size = sample_count * 4
        raw_samples = np.frombuffer(data[offset:offset + samples_size], dtype=np.int32)
        offset += samples_size

        # Timestamps
        timestamps_us = np.frombuffer(data[offset:offset + samples_size], dtype=np.uint32)
        offset += samples_size

        # CRC
        crc32 = struct.unpack('<I', data[offset:offset + 4])[0]

        frame = cls(
            header=header,
            adc_config=adc_config,
            afe_config=afe_config,
            mode_config=mode_config,
            environment=environment,
            nfc_metadata=nfc_metadata,
            sample_count=sample_count,
            raw_samples=raw_samples,
            timestamps_us=timestamps_us,
            crc32=crc32
        )

        return frame

    def verify_crc(self) -> bool:
        """CRC 검증"""
        expected = self.calculate_crc()
        return expected == self.crc32

    def to_voltage_array(self, vref: float = 2.5, gain: int = 1) -> np.ndarray:
        """원시 코드를 전압으로 변환"""
        return (self.raw_samples / (2**23 - 1)) * vref / gain


@dataclass
class MultiChannelFrame:
    """다채널 동시 샘플 프레임"""
    header: FrameHeader
    num_channels: int
    channels_data: Dict[int, RawSampleFrame] = field(default_factory=dict)

    def add_channel(self, channel_id: int, frame: RawSampleFrame) -> None:
        """채널 데이터 추가"""
        self.channels_data[channel_id] = frame
        self.num_channels = len(self.channels_data)


class DataFrameLogger:
    """
    데이터 프레임 로거

    원시 데이터 로깅 및 파일 관리
    """

    def __init__(self, logger_id: str = "LOGGER_001"):
        """
        Args:
            logger_id: 로거 식별자
        """
        self.logger_id = logger_id

        # 시퀀스 번호
        self.sequence_counter = 0

        # 버퍼
        self.frame_buffer: List[RawSampleFrame] = []
        self.max_buffer_size = 1000

        # 통계
        self.total_frames = 0
        self.total_samples = 0

    def create_frame(self,
                    raw_samples: np.ndarray,
                    timestamps_us: np.ndarray,
                    adc_config: ADCConfig = None,
                    afe_config: AFEConfig = None,
                    mode_config: ModeConfig = None,
                    environment: EnvironmentData = None,
                    nfc_metadata: NFCMetadata = None) -> RawSampleFrame:
        """
        원시 샘플 프레임 생성
        """
        # 헤더 생성
        header = FrameHeader(
            frame_type=FrameType.RAW_SAMPLE,
            sequence=self.sequence_counter,
            timestamp_us=int(datetime.now().timestamp() * 1e6),
            payload_length=len(raw_samples) * 8 + 140  # 근사값
        )

        self.sequence_counter += 1

        frame = RawSampleFrame(
            header=header,
            adc_config=adc_config or ADCConfig(),
            afe_config=afe_config or AFEConfig(),
            mode_config=mode_config or ModeConfig(),
            environment=environment or EnvironmentData(),
            nfc_metadata=nfc_metadata or NFCMetadata(),
            sample_count=len(raw_samples),
            raw_samples=raw_samples.astype(np.int32),
            timestamps_us=timestamps_us.astype(np.uint32)
        )

        # 버퍼에 추가
        self.frame_buffer.append(frame)
        if len(self.frame_buffer) > self.max_buffer_size:
            self.frame_buffer.pop(0)

        self.total_frames += 1
        self.total_samples += len(raw_samples)

        return frame

    def save_to_binary(self, filepath: str, frames: List[RawSampleFrame] = None) -> int:
        """
        바이너리 파일로 저장

        Returns:
            저장된 프레임 수
        """
        if frames is None:
            frames = self.frame_buffer

        with open(filepath, 'wb') as f:
            # 파일 헤더
            file_header = struct.pack(
                '<4sHHI',
                b'MPLG',  # Magic
                1, 0,     # Version
                len(frames)
            )
            f.write(file_header)

            # 프레임들
            for frame in frames:
                frame_bytes = frame.to_bytes()
                # 프레임 길이 + 데이터
                f.write(struct.pack('<I', len(frame_bytes)))
                f.write(frame_bytes)

        return len(frames)

    def load_from_binary(self, filepath: str) -> List[RawSampleFrame]:
        """바이너리 파일에서 로드"""
        frames = []

        with open(filepath, 'rb') as f:
            # 파일 헤더
            file_header = f.read(12)
            magic, v_maj, v_min, num_frames = struct.unpack('<4sHHI', file_header)

            if magic != b'MPLG':
                raise ValueError("Invalid file format")

            # 프레임들
            for _ in range(num_frames):
                frame_len = struct.unpack('<I', f.read(4))[0]
                frame_bytes = f.read(frame_len)
                frame = RawSampleFrame.from_bytes(frame_bytes)
                frames.append(frame)

        return frames

    def save_to_json(self, filepath: str, frames: List[RawSampleFrame] = None) -> int:
        """JSON 파일로 저장 (재해석/디버깅용)"""
        if frames is None:
            frames = self.frame_buffer

        data = {
            'logger_id': self.logger_id,
            'export_timestamp': datetime.now().isoformat(),
            'num_frames': len(frames),
            'frames': []
        }

        for frame in frames:
            frame_data = {
                'sequence': frame.header.sequence,
                'timestamp_us': frame.header.timestamp_us,
                'frame_type': frame.header.frame_type.value,
                'adc_config': {
                    'data_rate_code': frame.adc_config.data_rate_code,
                    'gain_code': frame.adc_config.gain_code,
                    'channel_positive': frame.adc_config.channel_positive,
                    'channel_negative': frame.adc_config.channel_negative,
                },
                'afe_config': {
                    'tia_gain_code': frame.afe_config.tia_gain_code,
                    'internal_zero': frame.afe_config.internal_zero,
                    'bias_percent': frame.afe_config.bias_percent,
                },
                'mode_config': {
                    'mode_code': frame.mode_config.mode_code,
                    'param1': frame.mode_config.param1,
                    'param2': frame.mode_config.param2,
                    'param3': frame.mode_config.param3,
                },
                'environment': {
                    'temperature_c': frame.environment.temperature_c,
                    'humidity_rh': frame.environment.humidity_rh,
                    'supply_voltage_v': frame.environment.supply_voltage_v,
                    'battery_soc': frame.environment.battery_soc,
                },
                'nfc': {
                    'uid': frame.nfc_metadata.uid.hex(),
                    'serial_number': frame.nfc_metadata.serial_number,
                    'lot_number': frame.nfc_metadata.lot_number,
                    'cal_slope': frame.nfc_metadata.cal_slope,
                    'cal_intercept': frame.nfc_metadata.cal_intercept,
                },
                'sample_count': frame.sample_count,
                'raw_samples': frame.raw_samples.tolist(),
                'timestamps_us': frame.timestamps_us.tolist(),
                'crc32': frame.crc32,
                'crc_valid': frame.verify_crc()
            }
            data['frames'].append(frame_data)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return len(frames)

    def get_statistics(self) -> Dict[str, Any]:
        """통계 정보"""
        return {
            'logger_id': self.logger_id,
            'total_frames': self.total_frames,
            'total_samples': self.total_samples,
            'buffer_size': len(self.frame_buffer),
            'sequence_counter': self.sequence_counter
        }

    def clear_buffer(self) -> None:
        """버퍼 초기화"""
        self.frame_buffer.clear()


class RealTimeFrameStreamer:
    """실시간 프레임 스트리머"""

    def __init__(self, streamer_id: str = "STREAM_001"):
        self.streamer_id = streamer_id
        self.logger = DataFrameLogger(f"{streamer_id}_LOG")

        # 스트리밍 설정
        self.is_streaming = False
        self.sample_rate_hz = 1000.0

        # 콜백
        self._on_frame_callbacks: List[callable] = []

    def start_streaming(self) -> None:
        """스트리밍 시작"""
        self.is_streaming = True

    def stop_streaming(self) -> None:
        """스트리밍 중지"""
        self.is_streaming = False

    def add_frame_callback(self, callback: callable) -> None:
        """프레임 수신 콜백 추가"""
        self._on_frame_callbacks.append(callback)

    def push_samples(self,
                    raw_samples: np.ndarray,
                    timestamps_us: np.ndarray = None,
                    **config) -> Optional[RawSampleFrame]:
        """샘플 푸시"""
        if not self.is_streaming:
            return None

        if timestamps_us is None:
            # 자동 타임스탬프 생성
            period_us = int(1e6 / self.sample_rate_hz)
            timestamps_us = np.arange(len(raw_samples)) * period_us

        frame = self.logger.create_frame(
            raw_samples=raw_samples,
            timestamps_us=timestamps_us,
            **config
        )

        # 콜백 호출
        for callback in self._on_frame_callbacks:
            try:
                callback(frame)
            except:
                pass

        return frame


# 편의 함수
def create_data_logger(logger_id: str = "DEFAULT") -> DataFrameLogger:
    """데이터 로거 생성 헬퍼"""
    return DataFrameLogger(logger_id=logger_id)


def create_frame_streamer(streamer_id: str = "DEFAULT") -> RealTimeFrameStreamer:
    """프레임 스트리머 생성 헬퍼"""
    return RealTimeFrameStreamer(streamer_id=streamer_id)


def quick_frame_from_samples(samples: np.ndarray,
                            sample_rate_hz: float = 1000.0) -> RawSampleFrame:
    """샘플 배열에서 빠른 프레임 생성"""
    logger = DataFrameLogger()

    period_us = int(1e6 / sample_rate_hz)
    timestamps = np.arange(len(samples)) * period_us

    return logger.create_frame(
        raw_samples=samples.astype(np.int32),
        timestamps_us=timestamps.astype(np.uint32)
    )


__all__ = [
    # Enums
    'FrameType',
    'CompressionType',
    'ChannelConfig',
    # Classes
    'FrameHeader',
    'ADCConfig',
    'AFEConfig',
    'ModeConfig',
    'EnvironmentData',
    'NFCMetadata',
    'RawSampleFrame',
    'MultiChannelFrame',
    'DataFrameLogger',
    'RealTimeFrameStreamer',
    # Functions
    'create_data_logger',
    'create_frame_streamer',
    'quick_frame_from_samples',
]
