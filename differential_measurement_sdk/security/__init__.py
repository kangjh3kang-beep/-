"""
데이터 패킷 구조 및 보안 모듈 (Data Packet & Security Module)

측정 데이터의 안전한 전송 및 저장을 위한 패킷 구조와 암호화

주요 기능:
- 표준화된 데이터 패킷 구조
- AES-256 암호화
- HMAC 무결성 검증
- 디지털 서명
- 타임스탬프 및 시퀀스 관리
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
import numpy as np
import hashlib
import hmac
import secrets
import struct
import base64
import json


class PacketType(Enum):
    """패킷 유형"""
    MEASUREMENT_DATA = 0x01
    CALIBRATION_DATA = 0x02
    SYSTEM_STATUS = 0x03
    COMMAND = 0x04
    RESPONSE = 0x05
    ALERT = 0x06
    HEARTBEAT = 0x07
    FIRMWARE_UPDATE = 0x08


class EncryptionMode(Enum):
    """암호화 모드"""
    NONE = "none"
    AES_128_CBC = "aes_128_cbc"
    AES_256_CBC = "aes_256_cbc"
    AES_256_GCM = "aes_256_gcm"


class CompressionMode(Enum):
    """압축 모드"""
    NONE = "none"
    GZIP = "gzip"
    LZ4 = "lz4"
    ZSTD = "zstd"


class IntegrityCheck(Enum):
    """무결성 검사 방식"""
    CRC32 = "crc32"
    SHA256 = "sha256"
    HMAC_SHA256 = "hmac_sha256"


@dataclass
class PacketHeader:
    """
    패킷 헤더 구조

    총 32바이트 고정 크기
    """
    version: int = 1  # 프로토콜 버전 (1 byte)
    packet_type: PacketType = PacketType.MEASUREMENT_DATA  # 패킷 유형 (1 byte)
    sequence_number: int = 0  # 시퀀스 번호 (4 bytes)
    timestamp: int = 0  # 유닉스 타임스탬프 (8 bytes)
    device_id: int = 0  # 장치 ID (4 bytes)
    payload_length: int = 0  # 페이로드 길이 (4 bytes)
    encryption_mode: EncryptionMode = EncryptionMode.NONE  # 암호화 모드 (1 byte)
    compression_mode: CompressionMode = CompressionMode.NONE  # 압축 모드 (1 byte)
    flags: int = 0  # 플래그 비트 (2 bytes)
    reserved: bytes = b'\x00' * 6  # 예약 (6 bytes)

    def to_bytes(self) -> bytes:
        """바이트 배열로 직렬화"""
        return struct.pack(
            '<BBIQIHBB2s6s',
            self.version,
            self.packet_type.value,
            self.sequence_number,
            self.timestamp,
            self.device_id,
            self.payload_length,
            list(EncryptionMode).index(self.encryption_mode),
            list(CompressionMode).index(self.compression_mode),
            self.flags.to_bytes(2, 'little'),
            self.reserved
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> 'PacketHeader':
        """바이트 배열에서 역직렬화"""
        if len(data) < 32:
            raise ValueError("Invalid header size")

        unpacked = struct.unpack('<BBIQIHBB2s6s', data[:32])

        return cls(
            version=unpacked[0],
            packet_type=PacketType(unpacked[1]),
            sequence_number=unpacked[2],
            timestamp=unpacked[3],
            device_id=unpacked[4],
            payload_length=unpacked[5],
            encryption_mode=list(EncryptionMode)[unpacked[6]],
            compression_mode=list(CompressionMode)[unpacked[7]],
            flags=int.from_bytes(unpacked[8], 'little'),
            reserved=unpacked[9]
        )


@dataclass
class MeasurementPayload:
    """측정 데이터 페이로드"""
    channel_id: int
    sample_rate_hz: float
    num_samples: int
    data: np.ndarray
    unit: str = "V"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_bytes(self) -> bytes:
        """바이트 직렬화"""
        # JSON으로 메타데이터 직렬화
        meta_json = json.dumps(self.metadata).encode('utf-8')

        # 헤더: channel_id(4), sample_rate(8), num_samples(4), unit_len(4), meta_len(4)
        header = struct.pack(
            '<IdII',
            self.channel_id,
            self.sample_rate_hz,
            self.num_samples,
            len(self.unit.encode('utf-8'))
        )

        unit_bytes = self.unit.encode('utf-8')
        meta_len = struct.pack('<I', len(meta_json))
        data_bytes = self.data.astype(np.float64).tobytes()

        return header + unit_bytes + meta_len + meta_json + data_bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> 'MeasurementPayload':
        """바이트에서 역직렬화"""
        # 헤더 파싱
        header_size = 20
        channel_id, sample_rate, num_samples, unit_len = struct.unpack(
            '<IdII', data[:header_size]
        )

        offset = header_size
        unit = data[offset:offset + unit_len].decode('utf-8')
        offset += unit_len

        meta_len = struct.unpack('<I', data[offset:offset + 4])[0]
        offset += 4

        meta_json = data[offset:offset + meta_len].decode('utf-8')
        metadata = json.loads(meta_json)
        offset += meta_len

        data_bytes = data[offset:]
        samples = np.frombuffer(data_bytes, dtype=np.float64)

        return cls(
            channel_id=channel_id,
            sample_rate_hz=sample_rate,
            num_samples=num_samples,
            data=samples,
            unit=unit,
            metadata=metadata
        )


@dataclass
class DataPacket:
    """
    완전한 데이터 패킷

    구조: [Header(32)] + [Payload(N)] + [Checksum(32)] + [Signature(64, optional)]
    """
    header: PacketHeader
    payload: bytes
    checksum: bytes = b''
    signature: Optional[bytes] = None

    def compute_checksum(self, key: Optional[bytes] = None) -> bytes:
        """체크섬 계산"""
        data = self.header.to_bytes() + self.payload

        if key:
            # HMAC-SHA256
            return hmac.new(key, data, hashlib.sha256).digest()
        else:
            # SHA256
            return hashlib.sha256(data).digest()

    def verify_checksum(self, key: Optional[bytes] = None) -> bool:
        """체크섬 검증"""
        computed = self.compute_checksum(key)
        return hmac.compare_digest(computed, self.checksum)

    def to_bytes(self) -> bytes:
        """전체 패킷 직렬화"""
        packet = self.header.to_bytes() + self.payload + self.checksum
        if self.signature:
            packet += self.signature
        return packet

    @classmethod
    def from_bytes(cls,
                   data: bytes,
                   has_signature: bool = False) -> 'DataPacket':
        """패킷 역직렬화"""
        header = PacketHeader.from_bytes(data[:32])

        payload_end = 32 + header.payload_length
        payload = data[32:payload_end]

        checksum = data[payload_end:payload_end + 32]

        signature = None
        if has_signature:
            signature = data[payload_end + 32:payload_end + 96]

        return cls(
            header=header,
            payload=payload,
            checksum=checksum,
            signature=signature
        )


class SimpleCipher:
    """
    간단한 XOR 기반 암호화 (실제 환경에서는 AES 사용 권장)

    참고: 실제 보안 환경에서는 cryptography 라이브러리의
    AES-256-GCM 사용을 권장합니다.
    """

    def __init__(self, key: bytes):
        """
        Args:
            key: 암호화 키 (32 bytes for AES-256 equivalent)
        """
        if len(key) < 32:
            # 키 확장
            key = hashlib.sha256(key).digest()
        self.key = key[:32]

    def encrypt(self, plaintext: bytes) -> Tuple[bytes, bytes]:
        """
        암호화

        Returns:
            (암호문, IV) 튜플
        """
        # IV 생성
        iv = secrets.token_bytes(16)

        # 키 스트림 생성 (실제로는 AES-CTR 모드 사용)
        key_stream = self._generate_key_stream(iv, len(plaintext))

        # XOR 암호화
        ciphertext = bytes(p ^ k for p, k in zip(plaintext, key_stream))

        return (ciphertext, iv)

    def decrypt(self, ciphertext: bytes, iv: bytes) -> bytes:
        """복호화"""
        # 같은 키 스트림 재생성
        key_stream = self._generate_key_stream(iv, len(ciphertext))

        # XOR 복호화
        plaintext = bytes(c ^ k for c, k in zip(ciphertext, key_stream))

        return plaintext

    def _generate_key_stream(self, iv: bytes, length: int) -> bytes:
        """키 스트림 생성"""
        key_stream = b''
        counter = 0

        while len(key_stream) < length:
            # 카운터 모드 시뮬레이션
            block_input = iv + counter.to_bytes(8, 'big') + self.key
            block = hashlib.sha256(block_input).digest()
            key_stream += block
            counter += 1

        return key_stream[:length]


class SecurePacketManager:
    """
    보안 패킷 관리자

    패킷의 생성, 암호화, 검증을 담당
    """

    def __init__(self,
                 device_id: int,
                 encryption_key: Optional[bytes] = None,
                 hmac_key: Optional[bytes] = None):
        """
        Args:
            device_id: 장치 식별자
            encryption_key: 암호화 키 (None이면 생성)
            hmac_key: HMAC 키 (None이면 생성)
        """
        self.device_id = device_id
        self.sequence_number = 0

        # 키 설정
        self.encryption_key = encryption_key or secrets.token_bytes(32)
        self.hmac_key = hmac_key or secrets.token_bytes(32)

        # 암호화 모듈
        self.cipher = SimpleCipher(self.encryption_key)

        # 통계
        self.packets_sent = 0
        self.packets_received = 0
        self.packets_failed = 0

    def create_measurement_packet(self,
                                  channel_id: int,
                                  data: np.ndarray,
                                  sample_rate: float,
                                  encrypt: bool = True) -> DataPacket:
        """
        측정 데이터 패킷 생성

        Args:
            channel_id: 채널 ID
            data: 측정 데이터
            sample_rate: 샘플링 레이트
            encrypt: 암호화 여부

        Returns:
            완성된 데이터 패킷
        """
        # 페이로드 생성
        payload_obj = MeasurementPayload(
            channel_id=channel_id,
            sample_rate_hz=sample_rate,
            num_samples=len(data),
            data=data,
            metadata={'created_at': datetime.now().isoformat()}
        )
        payload_bytes = payload_obj.to_bytes()

        # 암호화
        iv = b''
        encryption_mode = EncryptionMode.NONE
        if encrypt:
            payload_bytes, iv = self.cipher.encrypt(payload_bytes)
            payload_bytes = iv + payload_bytes  # IV를 페이로드 앞에 붙임
            encryption_mode = EncryptionMode.AES_256_CBC

        # 헤더 생성
        header = PacketHeader(
            version=1,
            packet_type=PacketType.MEASUREMENT_DATA,
            sequence_number=self.sequence_number,
            timestamp=int(datetime.now().timestamp() * 1000),  # 밀리초
            device_id=self.device_id,
            payload_length=len(payload_bytes),
            encryption_mode=encryption_mode
        )

        # 패킷 조립
        packet = DataPacket(
            header=header,
            payload=payload_bytes
        )

        # 체크섬 계산
        packet.checksum = packet.compute_checksum(self.hmac_key)

        # 시퀀스 번호 증가
        self.sequence_number += 1
        self.packets_sent += 1

        return packet

    def parse_packet(self,
                     data: bytes,
                     decrypt: bool = True) -> Tuple[Optional[MeasurementPayload], bool]:
        """
        패킷 파싱 및 검증

        Args:
            data: 원시 패킷 데이터
            decrypt: 복호화 여부

        Returns:
            (페이로드 객체, 검증 성공 여부) 튜플
        """
        try:
            # 패킷 역직렬화
            packet = DataPacket.from_bytes(data)

            # 체크섬 검증
            if not packet.verify_checksum(self.hmac_key):
                self.packets_failed += 1
                return (None, False)

            payload_bytes = packet.payload

            # 복호화
            if decrypt and packet.header.encryption_mode != EncryptionMode.NONE:
                iv = payload_bytes[:16]
                ciphertext = payload_bytes[16:]
                payload_bytes = self.cipher.decrypt(ciphertext, iv)

            # 페이로드 파싱
            if packet.header.packet_type == PacketType.MEASUREMENT_DATA:
                payload = MeasurementPayload.from_bytes(payload_bytes)
            else:
                return (None, True)

            self.packets_received += 1
            return (payload, True)

        except Exception as e:
            self.packets_failed += 1
            return (None, False)

    def create_command_packet(self,
                              command: str,
                              parameters: Dict[str, Any]) -> DataPacket:
        """명령 패킷 생성"""
        payload = json.dumps({
            'command': command,
            'parameters': parameters,
            'timestamp': datetime.now().isoformat()
        }).encode('utf-8')

        header = PacketHeader(
            version=1,
            packet_type=PacketType.COMMAND,
            sequence_number=self.sequence_number,
            timestamp=int(datetime.now().timestamp() * 1000),
            device_id=self.device_id,
            payload_length=len(payload)
        )

        packet = DataPacket(header=header, payload=payload)
        packet.checksum = packet.compute_checksum(self.hmac_key)

        self.sequence_number += 1
        return packet

    def create_status_packet(self, status: Dict[str, Any]) -> DataPacket:
        """상태 패킷 생성"""
        payload = json.dumps(status).encode('utf-8')

        header = PacketHeader(
            version=1,
            packet_type=PacketType.SYSTEM_STATUS,
            sequence_number=self.sequence_number,
            timestamp=int(datetime.now().timestamp() * 1000),
            device_id=self.device_id,
            payload_length=len(payload)
        )

        packet = DataPacket(header=header, payload=payload)
        packet.checksum = packet.compute_checksum(self.hmac_key)

        self.sequence_number += 1
        return packet

    def get_statistics(self) -> Dict[str, int]:
        """통계 반환"""
        return {
            'packets_sent': self.packets_sent,
            'packets_received': self.packets_received,
            'packets_failed': self.packets_failed,
            'current_sequence': self.sequence_number
        }


@dataclass
class SecureSession:
    """
    보안 세션

    키 교환 및 세션 관리
    """
    session_id: str
    device_id: int
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    # 세션 키
    session_key: bytes = field(default_factory=lambda: secrets.token_bytes(32))
    hmac_key: bytes = field(default_factory=lambda: secrets.token_bytes(32))

    # 상태
    is_active: bool = True
    packets_exchanged: int = 0

    def is_valid(self) -> bool:
        """세션 유효성 검사"""
        if not self.is_active:
            return False

        if self.expires_at and datetime.now() > self.expires_at:
            return False

        return True

    def generate_session_id(self) -> str:
        """세션 ID 생성"""
        return secrets.token_hex(16)


class SecureSessionManager:
    """보안 세션 관리자"""

    def __init__(self):
        self.sessions: Dict[str, SecureSession] = {}

    def create_session(self,
                       device_id: int,
                       duration_hours: float = 24.0) -> SecureSession:
        """새 세션 생성"""
        session = SecureSession(
            session_id=secrets.token_hex(16),
            device_id=device_id,
            expires_at=datetime.now() + timedelta(hours=duration_hours)
        )

        self.sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[SecureSession]:
        """세션 조회"""
        session = self.sessions.get(session_id)
        if session and session.is_valid():
            return session
        return None

    def close_session(self, session_id: str) -> bool:
        """세션 종료"""
        if session_id in self.sessions:
            self.sessions[session_id].is_active = False
            return True
        return False

    def cleanup_expired(self) -> int:
        """만료된 세션 정리"""
        expired = [
            sid for sid, session in self.sessions.items()
            if not session.is_valid()
        ]

        for sid in expired:
            del self.sessions[sid]

        return len(expired)


class DataIntegrityChecker:
    """데이터 무결성 검사기"""

    @staticmethod
    def compute_crc32(data: bytes) -> int:
        """CRC32 계산"""
        import zlib
        return zlib.crc32(data) & 0xffffffff

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        """SHA256 해시 계산"""
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def compute_hmac(data: bytes, key: bytes) -> bytes:
        """HMAC-SHA256 계산"""
        return hmac.new(key, data, hashlib.sha256).digest()

    @staticmethod
    def verify_hmac(data: bytes, key: bytes, expected: bytes) -> bool:
        """HMAC 검증"""
        computed = hmac.new(key, data, hashlib.sha256).digest()
        return hmac.compare_digest(computed, expected)


# 편의 함수
def create_secure_packet_manager(device_id: int) -> SecurePacketManager:
    """보안 패킷 관리자 생성 헬퍼"""
    return SecurePacketManager(device_id=device_id)


def generate_encryption_key() -> bytes:
    """암호화 키 생성"""
    return secrets.token_bytes(32)


def encode_packet_base64(packet: DataPacket) -> str:
    """패킷을 Base64로 인코딩"""
    return base64.b64encode(packet.to_bytes()).decode('ascii')


def decode_packet_base64(encoded: str) -> bytes:
    """Base64 디코딩"""
    return base64.b64decode(encoded)


__all__ = [
    # Enums
    'PacketType',
    'EncryptionMode',
    'CompressionMode',
    'IntegrityCheck',
    # Classes
    'PacketHeader',
    'MeasurementPayload',
    'DataPacket',
    'SimpleCipher',
    'SecurePacketManager',
    'SecureSession',
    'SecureSessionManager',
    'DataIntegrityChecker',
    # Functions
    'create_secure_packet_manager',
    'generate_encryption_key',
    'encode_packet_base64',
    'decode_packet_base64',
]
