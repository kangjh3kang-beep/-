"""
휴대형 카트리지 모듈 (Portable Cartridge Module)

사용자가 신체에 부착, 장착, 또는 손에 쥐어 휴대할 수 있는 소형 구조체로서,
외부 단말과의 근접 접촉만으로 전력 공급과 결과 확인이 동시에 이루어지는 시스템.

특허 참조: 실시예 10, 11 (도 19, 20, 21, 22)
"""

from typing import Dict, List, Optional, Tuple, Union, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import numpy as np


class PortableFormFactor(Enum):
    """휴대형 카트리지 형태"""
    RING = "ring"           # 환형 (반지형)
    CAP = "cap"             # 캡형 (뚜껑형)
    PATCH = "patch"         # 박막형 (패치형)
    BAND = "band"           # 밴드형 (손목밴드)
    CARD = "card"           # 카드형
    PENDANT = "pendant"     # 펜던트형
    CLIP = "clip"           # 클립형
    KEYCHAIN = "keychain"   # 키체인형


class WirelessProtocol(Enum):
    """무선 통신 프로토콜"""
    NFC = "nfc"             # Near Field Communication
    RFID = "rfid"           # Radio Frequency Identification
    BLE = "ble"             # Bluetooth Low Energy
    UWB = "uwb"             # Ultra-Wideband


class PowerState(Enum):
    """전원 상태"""
    UNPOWERED = "unpowered"     # 전원 없음
    HARVESTING = "harvesting"   # 에너지 수확 중
    POWERED = "powered"         # 전원 공급됨
    LOW_POWER = "low_power"     # 저전력 모드
    MEASURING = "measuring"     # 측정 중


@dataclass
class WirelessConfig:
    """무선 인터페이스 설정"""
    protocol: WirelessProtocol = WirelessProtocol.NFC
    frequency_mhz: float = 13.56  # NFC 기본 주파수
    max_power_mw: float = 10.0    # 최대 수확 전력
    data_rate_kbps: float = 424   # 데이터 전송률
    range_cm: float = 4.0         # 통신 범위


@dataclass
class EnergyHarvestingStatus:
    """에너지 수확 상태"""
    is_harvesting: bool = False
    input_power_mw: float = 0.0
    output_voltage_v: float = 0.0
    efficiency: float = 0.0
    storage_level: float = 0.0  # 0-1 (에너지 저장 레벨)


@dataclass
class PortableMeasurementResult:
    """휴대형 카트리지 측정 결과"""
    timestamp: datetime = field(default_factory=datetime.now)
    differential_signal: float = 0.0
    sensing_signal: float = 0.0
    reference_signal: float = 0.0
    temperature: Optional[float] = None
    battery_level: float = 1.0
    calibration_applied: bool = False
    quality_score: float = 1.0  # 측정 품질 (0-1)
    metadata: dict = field(default_factory=dict)


class WirelessInterface:
    """
    무선 인터페이스 클래스

    외부 단말과의 근접 접촉에 의해 무선으로 전력을 수신하고,
    측정 결과 데이터를 송신하는 인터페이스.
    """

    def __init__(self, config: Optional[WirelessConfig] = None):
        """
        초기화

        Args:
            config: 무선 인터페이스 설정
        """
        self.config = config or WirelessConfig()
        self._is_connected = False
        self._harvest_status = EnergyHarvestingStatus()

        # 콜백
        self._on_connect_callback: Optional[Callable] = None
        self._on_disconnect_callback: Optional[Callable] = None
        self._on_data_received_callback: Optional[Callable] = None

    def detect_field(self) -> bool:
        """
        외부 단말의 RF 필드 감지

        Returns:
            bool: 필드 감지 여부
        """
        # 실제 구현에서는 RF 필드 감지 하드웨어와 연동
        return self._is_connected

    def start_harvesting(self) -> EnergyHarvestingStatus:
        """
        에너지 수확 시작

        Returns:
            EnergyHarvestingStatus: 에너지 수확 상태
        """
        if self.detect_field():
            self._harvest_status.is_harvesting = True
            # 시뮬레이션 값
            self._harvest_status.input_power_mw = self.config.max_power_mw * 0.8
            self._harvest_status.output_voltage_v = 3.3
            self._harvest_status.efficiency = 0.75
        else:
            self._harvest_status.is_harvesting = False
            self._harvest_status.input_power_mw = 0.0

        return self._harvest_status

    def stop_harvesting(self) -> None:
        """에너지 수확 중지"""
        self._harvest_status.is_harvesting = False
        self._harvest_status.input_power_mw = 0.0

    def transmit_data(self, data: bytes) -> bool:
        """
        데이터 전송

        Args:
            data: 전송할 데이터

        Returns:
            bool: 전송 성공 여부
        """
        if not self._is_connected:
            return False

        # 실제 구현에서는 NFC/RFID 데이터 전송
        return True

    def receive_data(self, timeout_ms: int = 1000) -> Optional[bytes]:
        """
        데이터 수신

        Args:
            timeout_ms: 타임아웃 (밀리초)

        Returns:
            Optional[bytes]: 수신된 데이터
        """
        if not self._is_connected:
            return None

        # 실제 구현에서는 NFC/RFID 데이터 수신
        return None

    def connect(self) -> bool:
        """외부 단말과 연결"""
        if self.detect_field():
            self._is_connected = True
            if self._on_connect_callback:
                self._on_connect_callback()
            return True
        return False

    def disconnect(self) -> None:
        """연결 해제"""
        self._is_connected = False
        self.stop_harvesting()
        if self._on_disconnect_callback:
            self._on_disconnect_callback()

    def set_on_connect(self, callback: Callable) -> None:
        """연결 콜백 설정"""
        self._on_connect_callback = callback

    def set_on_disconnect(self, callback: Callable) -> None:
        """연결 해제 콜백 설정"""
        self._on_disconnect_callback = callback

    @property
    def is_connected(self) -> bool:
        """연결 상태"""
        return self._is_connected

    @property
    def harvest_status(self) -> EnergyHarvestingStatus:
        """에너지 수확 상태"""
        return self._harvest_status


class PortableElectrodeAssembly:
    """
    휴대형 전극부 클래스

    감지 전극과 참조 전극이 시료 접촉 가능한 위치에 노출 배치됨.
    """

    def __init__(self,
                 sensing_area_mm2: float = 1.0,
                 reference_area_mm2: float = 1.0,
                 electrode_gap_mm: float = 0.5):
        """
        초기화

        Args:
            sensing_area_mm2: 감지 전극 면적 (mm²)
            reference_area_mm2: 참조 전극 면적 (mm²)
            electrode_gap_mm: 전극 간격 (mm)
        """
        self.sensing_area_mm2 = sensing_area_mm2
        self.reference_area_mm2 = reference_area_mm2
        self.electrode_gap_mm = electrode_gap_mm

        self._is_sample_contacted = False
        self._sensing_signal = 0.0
        self._reference_signal = 0.0

    def detect_sample_contact(self) -> bool:
        """
        시료 접촉 감지

        Returns:
            bool: 시료 접촉 여부
        """
        # 실제 구현에서는 임피던스 변화로 접촉 감지
        return self._is_sample_contacted

    def measure_sensing_electrode(self) -> float:
        """
        감지 전극 신호 측정

        Returns:
            float: 감지 전극 신호
        """
        return self._sensing_signal

    def measure_reference_electrode(self) -> float:
        """
        참조 전극 신호 측정

        Returns:
            float: 참조 전극 신호
        """
        return self._reference_signal

    def set_sample_contact(self, contacted: bool) -> None:
        """시료 접촉 상태 설정 (시뮬레이션용)"""
        self._is_sample_contacted = contacted

    def set_signals(self, sensing: float, reference: float) -> None:
        """신호 설정 (시뮬레이션용)"""
        self._sensing_signal = sensing
        self._reference_signal = reference


class PortableSignalProcessor:
    """
    휴대형 신호 처리부 클래스

    저전력 차동 연산을 수행하는 소형화된 신호 처리기.
    """

    def __init__(self,
                 adc_resolution: int = 12,
                 sampling_rate: float = 100.0,
                 gain: float = 1.0):
        """
        초기화

        Args:
            adc_resolution: ADC 해상도 (비트)
            sampling_rate: 샘플링 레이트 (Hz)
            gain: 신호 이득
        """
        self.adc_resolution = adc_resolution
        self.sampling_rate = sampling_rate
        self.gain = gain

        self._offset_sensing = 0.0
        self._offset_reference = 0.0

    def calibrate_offset(self, sensing_offset: float, reference_offset: float) -> None:
        """
        오프셋 캘리브레이션

        Args:
            sensing_offset: 감지 전극 오프셋
            reference_offset: 참조 전극 오프셋
        """
        self._offset_sensing = sensing_offset
        self._offset_reference = reference_offset

    def process_differential(self,
                            sensing_signal: float,
                            reference_signal: float) -> float:
        """
        차동 연산 수행

        Args:
            sensing_signal: 감지 전극 신호
            reference_signal: 참조 전극 신호

        Returns:
            float: 차동 신호
        """
        # 오프셋 보정
        sensing_corrected = sensing_signal - self._offset_sensing
        reference_corrected = reference_signal - self._offset_reference

        # 차동 연산
        differential = (sensing_corrected - reference_corrected) * self.gain

        return differential

    def quantize(self, value: float, v_ref: float = 3.3) -> int:
        """
        ADC 양자화

        Args:
            value: 아날로그 값
            v_ref: 기준 전압

        Returns:
            int: 디지털 값
        """
        max_code = (1 << self.adc_resolution) - 1
        normalized = (value + v_ref) / (2 * v_ref)  # -Vref ~ +Vref -> 0 ~ 1
        normalized = np.clip(normalized, 0, 1)
        return int(normalized * max_code)

    def dequantize(self, code: int, v_ref: float = 3.3) -> float:
        """
        ADC 역양자화

        Args:
            code: 디지털 값
            v_ref: 기준 전압

        Returns:
            float: 아날로그 값
        """
        max_code = (1 << self.adc_resolution) - 1
        normalized = code / max_code
        return normalized * 2 * v_ref - v_ref


class PortableCartridge:
    """
    휴대형 카트리지 클래스

    사용자가 신체에 부착, 장착, 또는 손에 쥐어 휴대할 수 있는 소형 구조체.
    외부 단말과의 근접 접촉에 의해 전력 수신 및 결과 전송이 수행됨.

    Example:
        >>> cartridge = PortableCartridge(form_factor=PortableFormFactor.RING)
        >>> cartridge.contact_sample()
        >>> cartridge.touch_terminal()  # 외부 단말에 터치
        >>> result = cartridge.get_result()
    """

    def __init__(self,
                 form_factor: PortableFormFactor = PortableFormFactor.CARD,
                 wireless_config: Optional[WirelessConfig] = None,
                 cartridge_id: str = ""):
        """
        초기화

        Args:
            form_factor: 카트리지 형태
            wireless_config: 무선 인터페이스 설정
            cartridge_id: 카트리지 고유 ID
        """
        self.form_factor = form_factor
        self.cartridge_id = cartridge_id or self._generate_id()

        # 구성 요소
        self.wireless_interface = WirelessInterface(wireless_config)
        self.electrode_assembly = PortableElectrodeAssembly()
        self.signal_processor = PortableSignalProcessor()

        # 상태
        self._power_state = PowerState.UNPOWERED
        self._is_sample_contacted = False
        self._measurement_result: Optional[PortableMeasurementResult] = None

        # 보정 데이터
        self._calibration_data: dict = {}

        # 콜백
        self.wireless_interface.set_on_connect(self._on_terminal_connected)
        self.wireless_interface.set_on_disconnect(self._on_terminal_disconnected)

    def _generate_id(self) -> str:
        """고유 ID 생성"""
        import random
        return f"PC-{random.randint(100000, 999999)}"

    def _on_terminal_connected(self) -> None:
        """외부 단말 연결 시 콜백"""
        self._power_state = PowerState.HARVESTING
        self.wireless_interface.start_harvesting()

        # 충분한 전력이 수확되면 측정 시작
        if self.wireless_interface.harvest_status.is_harvesting:
            self._power_state = PowerState.POWERED

    def _on_terminal_disconnected(self) -> None:
        """외부 단말 연결 해제 시 콜백"""
        self._power_state = PowerState.UNPOWERED

    def contact_sample(self, sensing_signal: float = 0.0, reference_signal: float = 0.0) -> bool:
        """
        시료에 전극 접촉

        Args:
            sensing_signal: 감지 신호 (시뮬레이션)
            reference_signal: 참조 신호 (시뮬레이션)

        Returns:
            bool: 접촉 성공 여부
        """
        self.electrode_assembly.set_sample_contact(True)
        self.electrode_assembly.set_signals(sensing_signal, reference_signal)
        self._is_sample_contacted = True
        return True

    def touch_terminal(self) -> bool:
        """
        외부 단말에 터치 (근접 접촉)

        전력 공급과 데이터 전송이 동시에 수행됨.

        Returns:
            bool: 성공 여부
        """
        # 연결 시도
        if not self.wireless_interface.connect():
            return False

        # 전력 수확
        harvest_status = self.wireless_interface.start_harvesting()
        if not harvest_status.is_harvesting:
            return False

        self._power_state = PowerState.POWERED

        # 시료 접촉 상태 확인 후 측정
        if self._is_sample_contacted:
            self._perform_measurement()

        return True

    def _perform_measurement(self) -> None:
        """측정 수행"""
        self._power_state = PowerState.MEASURING

        # 전극 신호 측정
        sensing = self.electrode_assembly.measure_sensing_electrode()
        reference = self.electrode_assembly.measure_reference_electrode()

        # 차동 연산
        differential = self.signal_processor.process_differential(sensing, reference)

        # 결과 저장
        self._measurement_result = PortableMeasurementResult(
            timestamp=datetime.now(),
            differential_signal=differential,
            sensing_signal=sensing,
            reference_signal=reference,
            calibration_applied=bool(self._calibration_data),
            quality_score=self._calculate_quality_score(sensing, reference),
            metadata={
                "form_factor": self.form_factor.value,
                "cartridge_id": self.cartridge_id,
            }
        )

        self._power_state = PowerState.POWERED

    def _calculate_quality_score(self, sensing: float, reference: float) -> float:
        """측정 품질 점수 계산"""
        # 신호 크기 및 안정성 기반 품질 점수
        signal_strength = min(1.0, (abs(sensing) + abs(reference)) / 2.0)
        return signal_strength

    def get_result(self) -> Optional[PortableMeasurementResult]:
        """
        측정 결과 조회

        Returns:
            Optional[PortableMeasurementResult]: 측정 결과
        """
        return self._measurement_result

    def transmit_result(self) -> bool:
        """
        결과 데이터 전송

        Returns:
            bool: 전송 성공 여부
        """
        if self._measurement_result is None:
            return False

        # 데이터 패킷 생성
        packet = self._create_data_packet()

        # 전송
        return self.wireless_interface.transmit_data(packet)

    def _create_data_packet(self) -> bytes:
        """데이터 패킷 생성"""
        import struct

        if self._measurement_result is None:
            return b''

        # 간단한 패킷 구조
        packet = struct.pack(
            '<ffffBf',
            self._measurement_result.differential_signal,
            self._measurement_result.sensing_signal,
            self._measurement_result.reference_signal,
            self._measurement_result.quality_score,
            1 if self._measurement_result.calibration_applied else 0,
            self._measurement_result.timestamp.timestamp()
        )

        return packet

    def set_calibration(self, calibration_data: dict) -> None:
        """보정 데이터 설정"""
        self._calibration_data = calibration_data

        if 'sensing_offset' in calibration_data and 'reference_offset' in calibration_data:
            self.signal_processor.calibrate_offset(
                calibration_data['sensing_offset'],
                calibration_data['reference_offset']
            )

    @property
    def power_state(self) -> PowerState:
        """전원 상태"""
        return self._power_state

    @property
    def is_ready(self) -> bool:
        """측정 준비 상태"""
        return self._power_state in [PowerState.POWERED, PowerState.MEASURING]

    def get_info(self) -> dict:
        """카트리지 정보 조회"""
        return {
            "cartridge_id": self.cartridge_id,
            "form_factor": self.form_factor.value,
            "power_state": self._power_state.value,
            "is_sample_contacted": self._is_sample_contacted,
            "has_result": self._measurement_result is not None,
            "wireless_protocol": self.wireless_interface.config.protocol.value,
        }


class PortableCartridgeManager:
    """
    휴대형 카트리지 관리자

    복수의 휴대형 카트리지를 관리하고 측정 이력을 추적함.
    """

    def __init__(self):
        """초기화"""
        self._registered_cartridges: Dict[str, PortableCartridge] = {}
        self._measurement_history: List[PortableMeasurementResult] = []

    def register_cartridge(self, cartridge: PortableCartridge) -> None:
        """카트리지 등록"""
        self._registered_cartridges[cartridge.cartridge_id] = cartridge

    def unregister_cartridge(self, cartridge_id: str) -> bool:
        """카트리지 등록 해제"""
        if cartridge_id in self._registered_cartridges:
            del self._registered_cartridges[cartridge_id]
            return True
        return False

    def get_cartridge(self, cartridge_id: str) -> Optional[PortableCartridge]:
        """카트리지 조회"""
        return self._registered_cartridges.get(cartridge_id)

    def record_measurement(self, result: PortableMeasurementResult) -> None:
        """측정 결과 기록"""
        self._measurement_history.append(result)

    def get_history(self,
                    cartridge_id: Optional[str] = None,
                    limit: int = 100) -> List[PortableMeasurementResult]:
        """측정 이력 조회"""
        history = self._measurement_history

        if cartridge_id:
            history = [r for r in history
                      if r.metadata.get('cartridge_id') == cartridge_id]

        return history[-limit:]

    def list_cartridges(self) -> List[dict]:
        """등록된 카트리지 목록"""
        return [c.get_info() for c in self._registered_cartridges.values()]
