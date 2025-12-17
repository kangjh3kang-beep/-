"""
NFC 태그 관리 모듈 (NFC Tag Management Module)

NTAG216 기반 카트리지 식별 및 데이터 관리 (MPK-RDR-MFG-SPEC v2.2 섹션 4.2)

주요 기능:
- NFC Type 2 Tag (NTAG216) 읽기/쓰기
- 카트리지 UID/LOT/보정데이터 관리
- 사용횟수 카운터
- 무결성 검증 (서명)
- 추적성 관리
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
import hashlib
import hmac
import struct
import json
import secrets


class NFCTagType(Enum):
    """NFC 태그 타입"""
    NTAG213 = "ntag213"  # 144 bytes
    NTAG215 = "ntag215"  # 504 bytes
    NTAG216 = "ntag216"  # 888 bytes (권장)


class TagLockState(Enum):
    """태그 잠금 상태"""
    UNLOCKED = "unlocked"
    READ_ONLY = "read_only"
    LOCKED = "locked"


class CartridgeType(Enum):
    """카트리지 타입"""
    GLUCOSE = "glucose"           # 혈당
    LACTATE = "lactate"           # 젖산
    CHOLESTEROL = "cholesterol"   # 콜레스테롤
    MULTI_ANALYTE = "multi"       # 다중분석물
    GENERIC = "generic"           # 범용


@dataclass
class NTAG216Spec:
    """NTAG216 사양"""
    total_memory_bytes: int = 888      # 총 메모리
    user_memory_bytes: int = 888       # 사용자 메모리
    page_size_bytes: int = 4           # 페이지 크기
    total_pages: int = 231             # 총 페이지 수 (0-230)

    # 메모리 맵
    UID_START_PAGE: int = 0            # UID 시작
    STATIC_LOCK_PAGE: int = 2          # 정적 잠금 비트
    CC_PAGE: int = 3                   # Capability Container
    USER_DATA_START_PAGE: int = 4      # 사용자 데이터 시작
    USER_DATA_END_PAGE: int = 225      # 사용자 데이터 끝
    DYNAMIC_LOCK_PAGE: int = 226       # 동적 잠금 비트
    CFG0_PAGE: int = 227               # 설정 페이지 0
    CFG1_PAGE: int = 228               # 설정 페이지 1
    PWD_PAGE: int = 229                # 패스워드 페이지
    PACK_PAGE: int = 230               # 패스워드 ACK 페이지


@dataclass
class CalibrationData:
    """캘리브레이션 데이터"""
    # 보정 계수
    slope: float = 1.0
    intercept: float = 0.0

    # 온도 보정
    temp_coefficient: float = 0.0
    temp_reference_c: float = 25.0

    # 유효 기간
    calibration_date: str = ""
    expiry_date: str = ""

    # 메타데이터
    calibration_id: str = ""
    lab_id: str = ""

    def to_bytes(self) -> bytes:
        """바이트 직렬화"""
        data = struct.pack(
            '<ffff',
            self.slope,
            self.intercept,
            self.temp_coefficient,
            self.temp_reference_c
        )
        # 날짜 문자열 (8 bytes each)
        data += self.calibration_date[:8].ljust(8).encode('ascii')
        data += self.expiry_date[:8].ljust(8).encode('ascii')
        data += self.calibration_id[:16].ljust(16).encode('ascii')
        data += self.lab_id[:8].ljust(8).encode('ascii')
        return data  # Total: 56 bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> 'CalibrationData':
        """바이트에서 역직렬화"""
        slope, intercept, temp_coef, temp_ref = struct.unpack('<ffff', data[:16])

        return cls(
            slope=slope,
            intercept=intercept,
            temp_coefficient=temp_coef,
            temp_reference_c=temp_ref,
            calibration_date=data[16:24].decode('ascii').strip(),
            expiry_date=data[24:32].decode('ascii').strip(),
            calibration_id=data[32:48].decode('ascii').strip(),
            lab_id=data[48:56].decode('ascii').strip()
        )

    def is_valid(self) -> bool:
        """유효성 검사"""
        if not self.expiry_date:
            return True

        try:
            expiry = datetime.strptime(self.expiry_date, "%Y%m%d")
            return datetime.now() < expiry
        except:
            return False


@dataclass
class CartridgeInfo:
    """카트리지 정보"""
    # 식별 정보
    uid: str = ""                      # 7-byte UID (hex string)
    serial_number: str = ""            # 시리얼 번호
    lot_number: str = ""               # LOT 번호
    manufacturing_date: str = ""       # 제조일

    # 카트리지 타입
    cartridge_type: CartridgeType = CartridgeType.GENERIC
    sensor_count: int = 4              # 센서 수

    # 사용 정보
    max_uses: int = 1                  # 최대 사용 횟수
    current_uses: int = 0              # 현재 사용 횟수
    first_use_date: str = ""           # 첫 사용일
    last_use_date: str = ""            # 마지막 사용일

    # 캘리브레이션 데이터 (센서별)
    calibration_data: Dict[int, CalibrationData] = field(default_factory=dict)

    # 무결성
    signature: str = ""                # HMAC 서명

    def is_usable(self) -> bool:
        """사용 가능 여부"""
        if self.current_uses >= self.max_uses:
            return False

        # 캘리브레이션 유효성 확인
        for cal in self.calibration_data.values():
            if not cal.is_valid():
                return False

        return True

    def increment_use_count(self) -> bool:
        """사용 횟수 증가"""
        if self.current_uses >= self.max_uses:
            return False

        self.current_uses += 1
        self.last_use_date = datetime.now().strftime("%Y%m%d")

        if self.current_uses == 1:
            self.first_use_date = self.last_use_date

        return True


@dataclass
class NFCMemoryLayout:
    """NFC 메모리 레이아웃"""
    # 헤더 (페이지 4-7, 16 bytes)
    HEADER_START: int = 4
    HEADER_SIZE: int = 16

    # 카트리지 정보 (페이지 8-31, 96 bytes)
    CART_INFO_START: int = 8
    CART_INFO_SIZE: int = 96

    # 캘리브레이션 데이터 (페이지 32-95, 256 bytes)
    CAL_DATA_START: int = 32
    CAL_DATA_SIZE: int = 256

    # 사용 로그 (페이지 96-159, 256 bytes)
    USE_LOG_START: int = 96
    USE_LOG_SIZE: int = 256

    # 서명 (페이지 160-175, 64 bytes)
    SIGNATURE_START: int = 160
    SIGNATURE_SIZE: int = 64

    # 예약 영역 (페이지 176-225)
    RESERVED_START: int = 176


class NTAG216:
    """
    NTAG216 NFC 태그 모델

    NXP NTAG216: NFC Forum Type 2 Tag
    - 888 bytes 사용자 메모리
    - 7-byte UID (ISO/IEC 14443-3 cascade level 2)
    - 패스워드 보호 지원
    """

    def __init__(self, uid: str = None):
        """
        Args:
            uid: 7-byte UID (hex string, 14 chars)
        """
        self.spec = NTAG216Spec()
        self.layout = NFCMemoryLayout()

        # UID 생성 또는 할당
        if uid is None:
            # 랜덤 UID 생성 (04로 시작 - NXP 제조사 코드)
            self.uid = "04" + secrets.token_hex(6)
        else:
            self.uid = uid

        # 메모리 초기화 (바이트 배열)
        self.memory = bytearray(self.spec.total_memory_bytes)

        # UID 기록
        self._write_uid()

        # CC (Capability Container) 초기화
        self._init_cc()

        # 잠금 상태
        self.lock_state = TagLockState.UNLOCKED

        # 패스워드 (기본값)
        self.password = bytes([0xFF, 0xFF, 0xFF, 0xFF])
        self.pack = bytes([0x00, 0x00])

    def _write_uid(self) -> None:
        """UID를 메모리에 기록"""
        uid_bytes = bytes.fromhex(self.uid)
        # 페이지 0: UID 바이트 0-2 + BCC0
        self.memory[0:3] = uid_bytes[0:3]
        self.memory[3] = uid_bytes[0] ^ uid_bytes[1] ^ uid_bytes[2] ^ 0x88  # BCC0

        # 페이지 1: UID 바이트 3-6
        self.memory[4:8] = uid_bytes[3:7]

        # 페이지 2: BCC1 + Internal + Lock bytes
        self.memory[8] = uid_bytes[3] ^ uid_bytes[4] ^ uid_bytes[5] ^ uid_bytes[6]  # BCC1

    def _init_cc(self) -> None:
        """Capability Container 초기화"""
        # 페이지 3: CC
        self.memory[12] = 0xE1  # NDEF Magic Number
        self.memory[13] = 0x10  # Version 1.0
        self.memory[14] = 0x6D  # Size (109 * 8 = 872 bytes)
        self.memory[15] = 0x00  # Read/Write access

    def read_page(self, page: int) -> bytes:
        """페이지 읽기 (4 bytes)"""
        if page < 0 or page >= self.spec.total_pages:
            raise ValueError(f"Invalid page: {page}")

        start = page * self.spec.page_size_bytes
        end = start + self.spec.page_size_bytes

        return bytes(self.memory[start:end])

    def write_page(self, page: int, data: bytes) -> bool:
        """페이지 쓰기 (4 bytes)"""
        if page < 0 or page >= self.spec.total_pages:
            return False

        if len(data) != self.spec.page_size_bytes:
            return False

        if self.lock_state == TagLockState.LOCKED:
            return False

        # UID/CC 영역은 쓰기 보호
        if page < self.spec.USER_DATA_START_PAGE:
            return False

        start = page * self.spec.page_size_bytes
        self.memory[start:start + 4] = data

        return True

    def read_bytes(self, start_page: int, num_bytes: int) -> bytes:
        """연속 바이트 읽기"""
        start = start_page * self.spec.page_size_bytes
        end = start + num_bytes

        if end > len(self.memory):
            end = len(self.memory)

        return bytes(self.memory[start:end])

    def write_bytes(self, start_page: int, data: bytes) -> bool:
        """연속 바이트 쓰기"""
        if start_page < self.spec.USER_DATA_START_PAGE:
            return False

        start = start_page * self.spec.page_size_bytes

        if start + len(data) > len(self.memory):
            return False

        self.memory[start:start + len(data)] = data
        return True

    def get_uid(self) -> str:
        """UID 반환"""
        return self.uid

    def set_lock(self, state: TagLockState) -> None:
        """잠금 설정"""
        self.lock_state = state

    def authenticate(self, password: bytes) -> bool:
        """패스워드 인증"""
        return password == self.password


class NFCCartridgeManager:
    """
    NFC 카트리지 관리자

    카트리지 정보 읽기/쓰기 및 무결성 관리
    """

    # HMAC 키 (실제 환경에서는 보안 저장소에서 관리)
    _HMAC_KEY = b'ManpasikSecretKey2024'

    def __init__(self, manager_id: str = "NFC_MGR_001"):
        """
        Args:
            manager_id: 관리자 식별자
        """
        self.manager_id = manager_id

        # 현재 감지된 태그
        self.current_tag: Optional[NTAG216] = None

        # 캐시된 카트리지 정보
        self.cached_info: Optional[CartridgeInfo] = None

        # 연결 상태
        self.is_connected = False

        # 에러 로그
        self.error_log: List[str] = []

    def connect_tag(self, tag: NTAG216) -> bool:
        """태그 연결"""
        self.current_tag = tag
        self.is_connected = True

        # 정보 읽기 시도
        try:
            self.cached_info = self.read_cartridge_info()
            return True
        except Exception as e:
            self.error_log.append(f"Tag read error: {e}")
            return False

    def disconnect_tag(self) -> None:
        """태그 연결 해제"""
        self.current_tag = None
        self.cached_info = None
        self.is_connected = False

    def detect_tag(self) -> bool:
        """태그 감지 (시뮬레이션)"""
        # 실제로는 PN7160을 통한 폴링
        return self.is_connected and self.current_tag is not None

    def read_cartridge_info(self) -> CartridgeInfo:
        """카트리지 정보 읽기"""
        if self.current_tag is None:
            raise RuntimeError("No tag connected")

        layout = self.current_tag.layout

        # 헤더 읽기
        header = self.current_tag.read_bytes(layout.HEADER_START, layout.HEADER_SIZE)

        # 카트리지 정보 읽기
        cart_bytes = self.current_tag.read_bytes(layout.CART_INFO_START, layout.CART_INFO_SIZE)

        # 파싱
        info = CartridgeInfo(
            uid=self.current_tag.get_uid()
        )

        # 헤더에서 기본 정보 추출
        if len(header) >= 16:
            info.serial_number = header[0:8].decode('ascii', errors='ignore').strip('\x00')
            info.lot_number = header[8:16].decode('ascii', errors='ignore').strip('\x00')

        # 카트리지 정보 상세 추출
        if len(cart_bytes) >= 48:
            info.manufacturing_date = cart_bytes[0:8].decode('ascii', errors='ignore').strip('\x00')
            cart_type_byte = cart_bytes[8]
            info.cartridge_type = list(CartridgeType)[cart_type_byte % len(CartridgeType)]
            info.sensor_count = cart_bytes[9]
            info.max_uses = struct.unpack('<H', cart_bytes[10:12])[0]
            info.current_uses = struct.unpack('<H', cart_bytes[12:14])[0]
            info.first_use_date = cart_bytes[14:22].decode('ascii', errors='ignore').strip('\x00')
            info.last_use_date = cart_bytes[22:30].decode('ascii', errors='ignore').strip('\x00')

        # 캘리브레이션 데이터 읽기
        cal_bytes = self.current_tag.read_bytes(layout.CAL_DATA_START, layout.CAL_DATA_SIZE)

        for sensor_id in range(info.sensor_count):
            offset = sensor_id * 56  # CalibrationData는 56 bytes
            if offset + 56 <= len(cal_bytes):
                cal_data = CalibrationData.from_bytes(cal_bytes[offset:offset + 56])
                info.calibration_data[sensor_id] = cal_data

        # 서명 읽기
        sig_bytes = self.current_tag.read_bytes(layout.SIGNATURE_START, layout.SIGNATURE_SIZE)
        info.signature = sig_bytes.hex()

        return info

    def write_cartridge_info(self, info: CartridgeInfo) -> bool:
        """카트리지 정보 쓰기"""
        if self.current_tag is None:
            return False

        layout = self.current_tag.layout

        # 헤더 작성
        header = bytearray(layout.HEADER_SIZE)
        header[0:8] = info.serial_number[:8].ljust(8).encode('ascii')
        header[8:16] = info.lot_number[:8].ljust(8).encode('ascii')

        if not self.current_tag.write_bytes(layout.HEADER_START, bytes(header)):
            return False

        # 카트리지 정보 작성
        cart_bytes = bytearray(layout.CART_INFO_SIZE)
        cart_bytes[0:8] = info.manufacturing_date[:8].ljust(8).encode('ascii')
        cart_bytes[8] = list(CartridgeType).index(info.cartridge_type)
        cart_bytes[9] = info.sensor_count
        cart_bytes[10:12] = struct.pack('<H', info.max_uses)
        cart_bytes[12:14] = struct.pack('<H', info.current_uses)
        cart_bytes[14:22] = info.first_use_date[:8].ljust(8).encode('ascii')
        cart_bytes[22:30] = info.last_use_date[:8].ljust(8).encode('ascii')

        if not self.current_tag.write_bytes(layout.CART_INFO_START, bytes(cart_bytes)):
            return False

        # 캘리브레이션 데이터 작성
        cal_bytes = bytearray(layout.CAL_DATA_SIZE)
        for sensor_id, cal_data in info.calibration_data.items():
            offset = sensor_id * 56
            if offset + 56 <= len(cal_bytes):
                cal_bytes[offset:offset + 56] = cal_data.to_bytes()

        if not self.current_tag.write_bytes(layout.CAL_DATA_START, bytes(cal_bytes)):
            return False

        # 서명 생성 및 작성
        signature = self._generate_signature(info)
        sig_bytes = bytes.fromhex(signature)
        sig_bytes = sig_bytes[:layout.SIGNATURE_SIZE].ljust(layout.SIGNATURE_SIZE, b'\x00')

        if not self.current_tag.write_bytes(layout.SIGNATURE_START, sig_bytes):
            return False

        info.signature = signature
        self.cached_info = info

        return True

    def _generate_signature(self, info: CartridgeInfo) -> str:
        """HMAC 서명 생성"""
        # 서명 대상 데이터 구성
        sign_data = (
            info.uid +
            info.serial_number +
            info.lot_number +
            str(info.max_uses) +
            str(info.current_uses)
        ).encode('utf-8')

        # HMAC-SHA256
        signature = hmac.new(self._HMAC_KEY, sign_data, hashlib.sha256).hexdigest()

        return signature

    def verify_signature(self, info: CartridgeInfo = None) -> bool:
        """서명 검증"""
        if info is None:
            info = self.cached_info

        if info is None:
            return False

        expected = self._generate_signature(info)
        return hmac.compare_digest(info.signature[:64], expected[:64])

    def increment_use_count(self) -> bool:
        """사용 횟수 증가 및 저장"""
        if self.cached_info is None:
            return False

        if not self.cached_info.increment_use_count():
            return False

        return self.write_cartridge_info(self.cached_info)

    def is_cartridge_usable(self) -> Tuple[bool, str]:
        """카트리지 사용 가능 여부 및 사유"""
        if self.cached_info is None:
            return (False, "No cartridge detected")

        if not self.verify_signature():
            return (False, "Invalid signature - counterfeit suspected")

        if self.cached_info.current_uses >= self.cached_info.max_uses:
            return (False, f"Max uses exceeded ({self.cached_info.max_uses})")

        for sensor_id, cal in self.cached_info.calibration_data.items():
            if not cal.is_valid():
                return (False, f"Calibration expired for sensor {sensor_id}")

        return (True, "OK")

    def get_calibration_for_sensor(self, sensor_id: int) -> Optional[CalibrationData]:
        """특정 센서의 캘리브레이션 데이터"""
        if self.cached_info is None:
            return None

        return self.cached_info.calibration_data.get(sensor_id)

    def format_new_cartridge(self,
                            serial_number: str,
                            lot_number: str,
                            cartridge_type: CartridgeType,
                            sensor_count: int = 4,
                            max_uses: int = 1,
                            calibration_data: Dict[int, CalibrationData] = None) -> bool:
        """
        새 카트리지 포맷

        공장 초기화용
        """
        if self.current_tag is None:
            return False

        info = CartridgeInfo(
            uid=self.current_tag.get_uid(),
            serial_number=serial_number,
            lot_number=lot_number,
            manufacturing_date=datetime.now().strftime("%Y%m%d"),
            cartridge_type=cartridge_type,
            sensor_count=sensor_count,
            max_uses=max_uses,
            current_uses=0,
            calibration_data=calibration_data or {}
        )

        return self.write_cartridge_info(info)

    def get_status(self) -> Dict[str, Any]:
        """상태 정보"""
        status = {
            'manager_id': self.manager_id,
            'is_connected': self.is_connected,
            'tag_uid': self.current_tag.get_uid() if self.current_tag else None
        }

        if self.cached_info:
            usable, reason = self.is_cartridge_usable()
            status['cartridge'] = {
                'serial_number': self.cached_info.serial_number,
                'lot_number': self.cached_info.lot_number,
                'type': self.cached_info.cartridge_type.value,
                'uses': f"{self.cached_info.current_uses}/{self.cached_info.max_uses}",
                'is_usable': usable,
                'status_reason': reason,
                'signature_valid': self.verify_signature()
            }

        return status


# 편의 함수
def create_ntag216(uid: str = None) -> NTAG216:
    """NTAG216 태그 생성 헬퍼"""
    return NTAG216(uid=uid)


def create_nfc_manager(manager_id: str = "DEFAULT") -> NFCCartridgeManager:
    """NFC 관리자 생성 헬퍼"""
    return NFCCartridgeManager(manager_id=manager_id)


def create_test_cartridge() -> Tuple[NTAG216, CartridgeInfo]:
    """테스트용 카트리지 생성"""
    tag = NTAG216()
    manager = NFCCartridgeManager()
    manager.connect_tag(tag)

    # 테스트 캘리브레이션 데이터
    cal_data = {
        0: CalibrationData(
            slope=1.02,
            intercept=-0.05,
            calibration_date=datetime.now().strftime("%Y%m%d"),
            expiry_date=(datetime.now().replace(year=datetime.now().year + 1)).strftime("%Y%m%d")
        )
    }

    manager.format_new_cartridge(
        serial_number="TEST0001",
        lot_number="LOT24001",
        cartridge_type=CartridgeType.GLUCOSE,
        max_uses=10,
        calibration_data=cal_data
    )

    return (tag, manager.cached_info)


__all__ = [
    # Enums
    'NFCTagType',
    'TagLockState',
    'CartridgeType',
    # Classes
    'NTAG216Spec',
    'CalibrationData',
    'CartridgeInfo',
    'NFCMemoryLayout',
    'NTAG216',
    'NFCCartridgeManager',
    # Functions
    'create_ntag216',
    'create_nfc_manager',
    'create_test_cartridge',
]
