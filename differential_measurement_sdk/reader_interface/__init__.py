"""
리더기 인터페이스 모듈 (Reader Interface Module)

E12 12핀 에지 커넥터 인터페이스 표준 (MPK-RDR-MFG-SPEC v2.2)

주요 기능:
- E12 12핀 에지 커넥터 정의 및 관리
- 4×(WE/RE) + CE + AUX 센서 페어 구성
- 접점 상태 모니터링 (LLCR, 연속성)
- 카트리지 삽입/탈거 감지
- 도금 타입 (Hard Gold/ENIG) 관리
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import numpy as np


class E12Pin(Enum):
    """E12 12핀 에지 커넥터 핀 정의"""
    GND = 1      # 공통 접지
    VCC = 2      # 3.3V 전원 (카트리지 능동소자용)
    S1_WE1 = 3   # 감지 전극 1 (센서페어 SP1)
    R1_RE1 = 4   # 참조 전극 1 (센서페어 SP1)
    S2_WE2 = 5   # 감지 전극 2 (센서페어 SP2)
    R2_RE2 = 6   # 참조 전극 2 (센서페어 SP2)
    S3_WE3 = 7   # 감지 전극 3 (센서페어 SP3)
    R3_RE3 = 8   # 참조 전극 3 (센서페어 SP3)
    S4_WE4 = 9   # 감지 전극 4 (센서페어 SP4)
    R4_RE4 = 10  # 참조 전극 4 (센서페어 SP4)
    CE = 11      # 상대 전극 (공통 CE)
    AUX = 12     # 보조 신호 (온도센서/확장)


class PinDirection(Enum):
    """핀 방향"""
    INPUT = "in"
    OUTPUT = "out"
    BIDIRECTIONAL = "io"
    POWER = "power"
    GROUND = "gnd"


class PlatingType(Enum):
    """도금 타입"""
    HARD_GOLD = "hard_gold"  # 경질 금 (Au 0.76~1.27 µm, Ni 2.5~5.0 µm)
    ENIG = "enig"            # IPC-4552 준수 (Ni 3~6 µm, Au ≥0.05 µm)


class ContactState(Enum):
    """접점 상태"""
    GOOD = "good"              # 정상
    MARGINAL = "marginal"      # 경계 (주의 필요)
    DEGRADED = "degraded"      # 열화
    FAILED = "failed"          # 실패
    UNKNOWN = "unknown"        # 미확인


class CartridgeState(Enum):
    """카트리지 상태"""
    NOT_INSERTED = "not_inserted"
    INSERTING = "inserting"
    INSERTED = "inserted"
    READY = "ready"
    MEASURING = "measuring"
    REMOVING = "removing"
    ERROR = "error"


@dataclass
class PinDefinition:
    """핀 정의"""
    pin_number: int
    signal_name: str
    direction: PinDirection
    description: str
    voltage_range: Tuple[float, float] = (0.0, 3.3)  # V
    current_limit_ma: float = 50.0
    is_analog: bool = True


@dataclass
class ContactResistance:
    """접점 저항 측정 결과 (LLCR)"""
    pin: E12Pin
    resistance_mohm: float  # mΩ
    timestamp: datetime = field(default_factory=datetime.now)
    temperature_c: float = 25.0

    # 기준값 (EIA-364-23 준용)
    INITIAL_MAX_MOHM: float = 50.0  # 초기 최대
    LIFECYCLE_MAX_MOHM: float = 70.0  # 수명 후 최대
    DELTA_MAX_MOHM: float = 20.0  # 최대 변화량

    def get_state(self, initial_value: Optional[float] = None) -> ContactState:
        """접점 상태 판정"""
        if self.resistance_mohm > self.LIFECYCLE_MAX_MOHM:
            return ContactState.FAILED

        if initial_value is not None:
            delta = self.resistance_mohm - initial_value
            if delta > self.DELTA_MAX_MOHM:
                return ContactState.DEGRADED

        if self.resistance_mohm > self.INITIAL_MAX_MOHM:
            return ContactState.MARGINAL

        return ContactState.GOOD


@dataclass
class SensorPair:
    """센서 페어 (WE/RE 쌍)"""
    pair_id: int  # 1-4
    we_pin: E12Pin  # Working Electrode
    re_pin: E12Pin  # Reference Electrode

    # 측정값
    differential_voltage: float = 0.0
    we_current_na: float = 0.0
    re_current_na: float = 0.0

    # 상태
    is_active: bool = False
    is_calibrated: bool = False

    # 캘리브레이션 계수
    gain: float = 1.0
    offset: float = 0.0
    k_temp: float = 0.0  # 온도 보정 계수
    k_drift: float = 0.0  # 드리프트 보정 계수

    def measure_differential(self,
                            we_signal: float,
                            re_signal: float,
                            delta_temp: float = 0.0,
                            delta_time: float = 0.0) -> float:
        """
        차동 측정 수행

        I_diff(t) = (I_S(t) - I_R(t)) - k_T·ΔT - k_drift·Δt
        """
        raw_diff = we_signal - re_signal
        temp_correction = self.k_temp * delta_temp
        drift_correction = self.k_drift * delta_time

        corrected = raw_diff - temp_correction - drift_correction
        calibrated = self.gain * corrected + self.offset

        self.differential_voltage = calibrated
        return calibrated


@dataclass
class E12Specification:
    """E12 커넥터 기계적 사양"""
    # 핀/피치
    num_pins: int = 12
    pitch_mm: float = 1.27

    # 카트리지 탭
    tab_thickness_mm: float = 1.00
    tab_thickness_tol_mm: float = 0.10

    # 패드
    pad_width_mm: float = 0.60
    pad_width_tol_mm: float = 0.05
    pad_length_mm: float = 4.50
    pad_length_tol_mm: float = 0.10
    pad_gap_mm: float = 0.67

    # 베벨
    bevel_angle_deg: float = 30.0
    bevel_angle_tol_deg: float = 5.0
    bevel_length_mm: float = 0.6

    # 유효 접촉 길이
    min_contact_length_mm: float = 3.0

    # 와이핑 스트로크
    wiping_stroke_min_mm: float = 1.5
    wiping_stroke_max_mm: float = 2.0


class E12EdgeConnector:
    """
    E12 12핀 에지 커넥터

    MPK-RDR-MFG-SPEC v2.2 동결안 기준
    """

    # 표준 핀 정의
    PIN_DEFINITIONS: Dict[E12Pin, PinDefinition] = {
        E12Pin.GND: PinDefinition(1, "GND", PinDirection.GROUND, "공통 접지", (-0.3, 0.3)),
        E12Pin.VCC: PinDefinition(2, "VCC", PinDirection.OUTPUT, "3.3V 전원", (3.0, 3.6), 100.0, False),
        E12Pin.S1_WE1: PinDefinition(3, "S1(WE1)", PinDirection.INPUT, "감지 전극 1"),
        E12Pin.R1_RE1: PinDefinition(4, "R1(RE1)", PinDirection.INPUT, "참조 전극 1"),
        E12Pin.S2_WE2: PinDefinition(5, "S2(WE2)", PinDirection.INPUT, "감지 전극 2"),
        E12Pin.R2_RE2: PinDefinition(6, "R2(RE2)", PinDirection.INPUT, "참조 전극 2"),
        E12Pin.S3_WE3: PinDefinition(7, "S3(WE3)", PinDirection.INPUT, "감지 전극 3"),
        E12Pin.R3_RE3: PinDefinition(8, "R3(RE3)", PinDirection.INPUT, "참조 전극 3"),
        E12Pin.S4_WE4: PinDefinition(9, "S4(WE4)", PinDirection.INPUT, "감지 전극 4"),
        E12Pin.R4_RE4: PinDefinition(10, "R4(RE4)", PinDirection.INPUT, "참조 전극 4"),
        E12Pin.CE: PinDefinition(11, "CE", PinDirection.OUTPUT, "상대 전극"),
        E12Pin.AUX: PinDefinition(12, "AUX", PinDirection.BIDIRECTIONAL, "보조 신호", (0, 3.3), 10.0),
    }

    def __init__(self,
                 connector_id: str = "E12_001",
                 plating_type: PlatingType = PlatingType.ENIG):
        """
        Args:
            connector_id: 커넥터 식별자
            plating_type: 도금 타입
        """
        self.connector_id = connector_id
        self.plating_type = plating_type
        self.spec = E12Specification()

        # 센서 페어 초기화
        self.sensor_pairs: Dict[int, SensorPair] = {
            1: SensorPair(1, E12Pin.S1_WE1, E12Pin.R1_RE1),
            2: SensorPair(2, E12Pin.S2_WE2, E12Pin.R2_RE2),
            3: SensorPair(3, E12Pin.S3_WE3, E12Pin.R3_RE3),
            4: SensorPair(4, E12Pin.S4_WE4, E12Pin.R4_RE4),
        }

        # 상태
        self.cartridge_state = CartridgeState.NOT_INSERTED
        self.vcc_enabled = False
        self.ce_enabled = False

        # 접점 저항 기록
        self.contact_resistances: Dict[E12Pin, List[ContactResistance]] = {
            pin: [] for pin in E12Pin
        }
        self.initial_llcr: Dict[E12Pin, float] = {}

        # 삽입 카운터
        self.insertion_count = 0
        self.max_insertion_cycles = 10000  # 양산 목표

    def insert_cartridge(self) -> bool:
        """카트리지 삽입"""
        if self.cartridge_state != CartridgeState.NOT_INSERTED:
            return False

        self.cartridge_state = CartridgeState.INSERTING

        # 삽입 시퀀스
        # 1. GND 먼저 접촉 (GND-first staggered)
        # 2. VCC 소프트 스타트
        # 3. 신호 라인 활성화

        self.insertion_count += 1
        self.cartridge_state = CartridgeState.INSERTED

        return True

    def remove_cartridge(self) -> bool:
        """카트리지 제거"""
        if self.cartridge_state == CartridgeState.NOT_INSERTED:
            return False

        self.cartridge_state = CartridgeState.REMOVING

        # 제거 시퀀스
        # 1. 신호 라인 비활성화
        # 2. VCC 차단
        # 3. GND 마지막 분리

        self.disable_vcc()
        self.disable_ce()

        for pair in self.sensor_pairs.values():
            pair.is_active = False

        self.cartridge_state = CartridgeState.NOT_INSERTED
        return True

    def enable_vcc(self, soft_start: bool = True) -> bool:
        """VCC 전원 활성화"""
        if self.cartridge_state == CartridgeState.NOT_INSERTED:
            return False

        # 소프트 스타트 (돌입전류 제한)
        self.vcc_enabled = True
        return True

    def disable_vcc(self) -> None:
        """VCC 전원 비활성화"""
        self.vcc_enabled = False

    def enable_ce(self) -> bool:
        """상대 전극 활성화"""
        if self.cartridge_state == CartridgeState.NOT_INSERTED:
            return False

        self.ce_enabled = True
        return True

    def disable_ce(self) -> None:
        """상대 전극 비활성화"""
        self.ce_enabled = False

    def activate_sensor_pair(self, pair_id: int) -> bool:
        """센서 페어 활성화"""
        if pair_id not in self.sensor_pairs:
            return False

        if self.cartridge_state != CartridgeState.INSERTED:
            return False

        self.sensor_pairs[pair_id].is_active = True
        return True

    def deactivate_sensor_pair(self, pair_id: int) -> None:
        """센서 페어 비활성화"""
        if pair_id in self.sensor_pairs:
            self.sensor_pairs[pair_id].is_active = False

    def measure_llcr(self, pin: E12Pin,
                     test_current_ma: float = 10.0) -> ContactResistance:
        """
        저레벨 접촉저항(LLCR) 측정

        EIA-364-23 준용
        """
        # 시뮬레이션: 실제로는 4선식 측정 필요
        base_resistance = 20.0  # mΩ

        # 삽입 횟수에 따른 열화
        degradation = 0.005 * self.insertion_count  # 삽입당 0.005 mΩ 증가

        # 노이즈
        noise = np.random.normal(0, 2.0)

        resistance = base_resistance + degradation + noise
        resistance = max(0.1, resistance)  # 최소값

        result = ContactResistance(
            pin=pin,
            resistance_mohm=resistance,
            timestamp=datetime.now()
        )

        self.contact_resistances[pin].append(result)

        if pin not in self.initial_llcr:
            self.initial_llcr[pin] = resistance

        return result

    def measure_all_llcr(self) -> Dict[E12Pin, ContactResistance]:
        """모든 핀의 LLCR 측정"""
        results = {}
        for pin in E12Pin:
            if pin != E12Pin.GND:  # GND는 측정 기준점
                results[pin] = self.measure_llcr(pin)
        return results

    def check_continuity(self) -> Dict[E12Pin, bool]:
        """연속성 검사 (오픈/쇼트)"""
        results = {}

        for pin in E12Pin:
            # 시뮬레이션: 정상 연결 가정
            llcr = self.measure_llcr(pin)

            # 오픈: LLCR > 1000 mΩ
            # 쇼트: 인접 핀과의 저항 < 1 mΩ (별도 검사 필요)
            is_open = llcr.resistance_mohm > 1000
            results[pin] = not is_open

        return results

    def get_contact_health(self) -> Dict[E12Pin, ContactState]:
        """전체 접점 건강상태 조회"""
        health = {}

        for pin in E12Pin:
            if pin in self.contact_resistances and self.contact_resistances[pin]:
                latest = self.contact_resistances[pin][-1]
                initial = self.initial_llcr.get(pin)
                health[pin] = latest.get_state(initial)
            else:
                health[pin] = ContactState.UNKNOWN

        return health

    def get_remaining_life_cycles(self) -> int:
        """잔여 삽입 수명"""
        return max(0, self.max_insertion_cycles - self.insertion_count)

    def get_status(self) -> Dict[str, Any]:
        """상태 정보 반환"""
        return {
            'connector_id': self.connector_id,
            'plating_type': self.plating_type.value,
            'cartridge_state': self.cartridge_state.value,
            'vcc_enabled': self.vcc_enabled,
            'ce_enabled': self.ce_enabled,
            'insertion_count': self.insertion_count,
            'remaining_life_cycles': self.get_remaining_life_cycles(),
            'active_sensor_pairs': [
                pid for pid, pair in self.sensor_pairs.items()
                if pair.is_active
            ],
            'contact_health': {
                pin.name: state.value
                for pin, state in self.get_contact_health().items()
            }
        }


class ReaderInterface:
    """
    리더기 인터페이스 관리자

    E12 커넥터 + NFC를 통한 카트리지 연결 관리
    """

    def __init__(self, reader_id: str = "READER_001"):
        """
        Args:
            reader_id: 리더기 식별자
        """
        self.reader_id = reader_id
        self.connector = E12EdgeConnector(f"{reader_id}_E12")

        # NFC 상태 (별도 모듈에서 상세 구현)
        self.nfc_detected = False
        self.nfc_uid: Optional[str] = None

        # 온도
        self.board_temperature_c = 25.0

        # 에러 로그
        self.error_log: List[Dict[str, Any]] = []

    def detect_cartridge(self) -> bool:
        """카트리지 감지 (물리적 삽입 + NFC)"""
        # 물리적 삽입 감지 (시뮬레이션)
        physical_inserted = True

        # NFC 감지
        nfc_detected = self.nfc_detected

        return physical_inserted and nfc_detected

    def initialize_cartridge(self) -> bool:
        """카트리지 초기화 시퀀스"""
        if not self.connector.insert_cartridge():
            self._log_error("CART_INSERT_FAIL", "카트리지 삽입 실패")
            return False

        # 연속성 검사
        continuity = self.connector.check_continuity()
        if not all(continuity.values()):
            failed_pins = [pin.name for pin, ok in continuity.items() if not ok]
            self._log_error("CONTINUITY_FAIL", f"연속성 실패: {failed_pins}")
            return False

        # LLCR 측정
        llcr_results = self.connector.measure_all_llcr()
        for pin, result in llcr_results.items():
            if result.get_state() == ContactState.FAILED:
                self._log_error("LLCR_FAIL", f"LLCR 실패: {pin.name}")
                return False

        # VCC 활성화
        if not self.connector.enable_vcc():
            self._log_error("VCC_FAIL", "VCC 활성화 실패")
            return False

        self.connector.cartridge_state = CartridgeState.READY
        return True

    def start_measurement(self, sensor_pairs: List[int] = None) -> bool:
        """측정 시작"""
        if self.connector.cartridge_state != CartridgeState.READY:
            return False

        pairs_to_activate = sensor_pairs or [1, 2, 3, 4]

        for pair_id in pairs_to_activate:
            self.connector.activate_sensor_pair(pair_id)

        self.connector.enable_ce()
        self.connector.cartridge_state = CartridgeState.MEASURING

        return True

    def stop_measurement(self) -> None:
        """측정 중지"""
        self.connector.disable_ce()

        for pair_id in self.connector.sensor_pairs:
            self.connector.deactivate_sensor_pair(pair_id)

        if self.connector.cartridge_state == CartridgeState.MEASURING:
            self.connector.cartridge_state = CartridgeState.READY

    def eject_cartridge(self) -> bool:
        """카트리지 배출"""
        self.stop_measurement()
        return self.connector.remove_cartridge()

    def _log_error(self, code: str, message: str) -> None:
        """에러 로그"""
        self.error_log.append({
            'timestamp': datetime.now().isoformat(),
            'code': code,
            'message': message
        })

    def get_status(self) -> Dict[str, Any]:
        """상태 정보"""
        return {
            'reader_id': self.reader_id,
            'connector': self.connector.get_status(),
            'nfc_detected': self.nfc_detected,
            'nfc_uid': self.nfc_uid,
            'board_temperature_c': self.board_temperature_c,
            'error_count': len(self.error_log)
        }


# 편의 함수
def create_reader_interface(reader_id: str = "DEFAULT") -> ReaderInterface:
    """리더 인터페이스 생성 헬퍼"""
    return ReaderInterface(reader_id=reader_id)


def create_e12_connector(connector_id: str = "E12",
                        plating: PlatingType = PlatingType.ENIG) -> E12EdgeConnector:
    """E12 커넥터 생성 헬퍼"""
    return E12EdgeConnector(connector_id=connector_id, plating_type=plating)


__all__ = [
    # Enums
    'E12Pin',
    'PinDirection',
    'PlatingType',
    'ContactState',
    'CartridgeState',
    # Classes
    'PinDefinition',
    'ContactResistance',
    'SensorPair',
    'E12Specification',
    'E12EdgeConnector',
    'ReaderInterface',
    # Functions
    'create_reader_interface',
    'create_e12_connector',
]
