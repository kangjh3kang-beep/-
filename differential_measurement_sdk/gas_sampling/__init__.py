"""
기체 시료 분석 모듈 (Gas Sampling Module)

이온풍(electrohydrodynamic) 기반 기체 시료 흡입 및 분석 시스템
특허 실시예 7 기반 구현

주요 기능:
- 코로나 방전 기반 이온풍 생성
- 무소음 기체 흡입
- 입자 농축 및 센서 표면 집적
- 실시간 기체 성분 분석
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import numpy as np


class IonWindMode(Enum):
    """이온풍 동작 모드"""
    OFF = "off"
    LOW_POWER = "low_power"  # 저전력 모드
    NORMAL = "normal"  # 일반 모드
    HIGH_CONCENTRATION = "high_concentration"  # 고농축 모드
    PULSED = "pulsed"  # 펄스 모드


class DischargeType(Enum):
    """방전 타입"""
    CORONA = "corona"  # 코로나 방전
    BARRIER = "barrier"  # 유전체 장벽 방전
    GLOW = "glow"  # 글로우 방전


class GasType(Enum):
    """기체 유형"""
    VOC = "voc"  # 휘발성 유기화합물
    INORGANIC = "inorganic"  # 무기가스
    AEROSOL = "aerosol"  # 에어로졸
    PARTICULATE = "particulate"  # 미립자
    MIXED = "mixed"  # 혼합


class SamplingState(Enum):
    """샘플링 상태"""
    IDLE = "idle"
    WARMING_UP = "warming_up"
    SAMPLING = "sampling"
    CONCENTRATING = "concentrating"
    ANALYZING = "analyzing"
    CLEANING = "cleaning"


@dataclass
class EmitterElectrode:
    """
    이미터 전극 (코로나 방전용)

    뾰족한 전극 구조로 코로나 방전을 발생시켜 이온풍 생성
    """
    electrode_id: str
    tip_radius_um: float = 10.0  # 전극 팁 반경 (마이크로미터)
    material: str = "tungsten"  # 전극 재질
    gap_distance_mm: float = 5.0  # 전극 간 거리
    max_voltage_kv: float = 10.0  # 최대 인가 전압

    # 동작 상태
    current_voltage_kv: float = 0.0
    discharge_current_ua: float = 0.0  # 방전 전류 (마이크로암페어)
    is_active: bool = False

    # 성능 파라미터
    ionization_efficiency: float = 0.85
    lifetime_hours: float = 10000.0
    accumulated_hours: float = 0.0

    def activate(self, voltage_kv: float) -> bool:
        """전극 활성화 및 코로나 방전 시작"""
        if voltage_kv > self.max_voltage_kv:
            return False

        self.current_voltage_kv = voltage_kv
        self.is_active = True

        # 코로나 방전 전류 계산 (Peek의 법칙 기반)
        # I = K * V * (V - V_onset)
        onset_voltage = 2.5  # 방전 시작 전압 (kV)
        if voltage_kv > onset_voltage:
            k_factor = 0.1  # 형상 계수
            self.discharge_current_ua = k_factor * voltage_kv * (voltage_kv - onset_voltage)
        else:
            self.discharge_current_ua = 0.0

        return True

    def deactivate(self) -> None:
        """전극 비활성화"""
        self.current_voltage_kv = 0.0
        self.discharge_current_ua = 0.0
        self.is_active = False

    def get_ion_production_rate(self) -> float:
        """이온 생성률 계산 (ions/s)"""
        if not self.is_active:
            return 0.0

        # 방전 전류로부터 이온 생성률 추정
        # 1 μA ≈ 6.24 × 10^12 ions/s
        return self.discharge_current_ua * 6.24e12 * self.ionization_efficiency

    def get_remaining_lifetime(self) -> float:
        """잔여 수명 (시간)"""
        return max(0.0, self.lifetime_hours - self.accumulated_hours)


@dataclass
class IonWindGenerator:
    """
    이온풍 생성기

    코로나 방전으로 생성된 이온이 중성 기체 분자와 충돌하여
    이온풍(electrohydrodynamic wind)을 발생시킴
    """
    generator_id: str
    emitter: EmitterElectrode
    collector_area_cm2: float = 4.0  # 컬렉터 면적
    channel_length_mm: float = 20.0  # 채널 길이

    # 동작 모드
    mode: IonWindMode = IonWindMode.OFF
    discharge_type: DischargeType = DischargeType.CORONA

    # 성능 특성
    max_flow_rate_ml_min: float = 100.0  # 최대 유량
    current_flow_rate_ml_min: float = 0.0
    power_consumption_mw: float = 0.0

    # 노이즈 특성 (무소음 장점)
    noise_level_db: float = 15.0  # 거의 무소음

    def set_mode(self, mode: IonWindMode) -> None:
        """동작 모드 설정"""
        self.mode = mode

        mode_voltages = {
            IonWindMode.OFF: 0.0,
            IonWindMode.LOW_POWER: 3.0,
            IonWindMode.NORMAL: 5.0,
            IonWindMode.HIGH_CONCENTRATION: 7.0,
            IonWindMode.PULSED: 6.0
        }

        voltage = mode_voltages.get(mode, 0.0)

        if mode == IonWindMode.OFF:
            self.emitter.deactivate()
            self.current_flow_rate_ml_min = 0.0
        else:
            self.emitter.activate(voltage)
            self._calculate_flow_rate()

        self._calculate_power()

    def _calculate_flow_rate(self) -> None:
        """유량 계산"""
        if not self.emitter.is_active:
            self.current_flow_rate_ml_min = 0.0
            return

        # 이온풍 속도는 전압의 제곱에 비례
        # v ∝ V^2 / d^2 (d: 전극 간격)
        voltage_ratio = self.emitter.current_voltage_kv / self.emitter.max_voltage_kv

        # 유량 계산
        base_flow = self.max_flow_rate_ml_min * (voltage_ratio ** 2)

        # 모드별 효율 적용
        mode_efficiency = {
            IonWindMode.LOW_POWER: 0.5,
            IonWindMode.NORMAL: 0.8,
            IonWindMode.HIGH_CONCENTRATION: 1.0,
            IonWindMode.PULSED: 0.7
        }

        efficiency = mode_efficiency.get(self.mode, 0.0)
        self.current_flow_rate_ml_min = base_flow * efficiency

    def _calculate_power(self) -> None:
        """전력 소비 계산"""
        # P = V * I
        self.power_consumption_mw = (
            self.emitter.current_voltage_kv * 1000 *
            self.emitter.discharge_current_ua / 1000
        )

    def get_status(self) -> Dict[str, Any]:
        """상태 정보 반환"""
        return {
            'generator_id': self.generator_id,
            'mode': self.mode.value,
            'voltage_kv': self.emitter.current_voltage_kv,
            'discharge_current_ua': self.emitter.discharge_current_ua,
            'flow_rate_ml_min': self.current_flow_rate_ml_min,
            'power_mw': self.power_consumption_mw,
            'noise_db': self.noise_level_db,
            'ion_rate': self.emitter.get_ion_production_rate()
        }


@dataclass
class ParticleConcentrator:
    """
    입자 농축기

    이온풍으로 흡입된 기체 중 입자/분자를 센서 표면에 농축
    """
    concentrator_id: str
    collection_area_mm2: float = 10.0  # 수집 면적

    # 농축 특성
    concentration_factor: float = 10.0  # 농축 배율
    collection_efficiency: float = 0.75  # 수집 효율

    # 전기영동 농축 파라미터
    electric_field_v_cm: float = 100.0  # 전기장 강도
    is_electrophoretic: bool = True  # 전기영동 모드

    # 축적된 물질
    accumulated_mass_ng: float = 0.0  # 축적 질량 (나노그램)
    accumulation_start_time: Optional[datetime] = None

    def start_concentration(self) -> None:
        """농축 시작"""
        self.accumulation_start_time = datetime.now()
        self.accumulated_mass_ng = 0.0

    def accumulate(self,
                   flow_rate_ml_min: float,
                   particle_concentration_ng_ml: float,
                   duration_sec: float) -> float:
        """
        입자 축적

        Args:
            flow_rate_ml_min: 유량 (mL/min)
            particle_concentration_ng_ml: 입자 농도 (ng/mL)
            duration_sec: 시간 (초)

        Returns:
            축적된 질량 (ng)
        """
        # 유입된 총 기체 부피
        volume_ml = flow_rate_ml_min * (duration_sec / 60.0)

        # 유입된 총 입자 질량
        total_mass = volume_ml * particle_concentration_ng_ml

        # 농축 효과 적용
        collected_mass = total_mass * self.collection_efficiency * self.concentration_factor

        self.accumulated_mass_ng += collected_mass
        return collected_mass

    def get_surface_concentration(self) -> float:
        """표면 농도 반환 (ng/mm²)"""
        if self.collection_area_mm2 <= 0:
            return 0.0
        return self.accumulated_mass_ng / self.collection_area_mm2

    def clean(self) -> float:
        """농축기 청소, 축적 물질 제거"""
        removed = self.accumulated_mass_ng
        self.accumulated_mass_ng = 0.0
        self.accumulation_start_time = None
        return removed


@dataclass
class GasSensorArray:
    """
    기체 센서 어레이

    다중 기체 감지를 위한 센서 어레이
    """
    array_id: str
    num_sensors: int = 8

    # 센서 특성 (센서별 감도 매트릭스)
    sensitivity_matrix: Optional[np.ndarray] = None  # (num_sensors x num_gases)
    baseline: Optional[np.ndarray] = None

    # 측정 상태
    current_response: Optional[np.ndarray] = None
    temperature_c: float = 25.0
    humidity_rh: float = 50.0

    # 타겟 기체 목록
    target_gases: List[str] = field(default_factory=lambda: [
        'CO', 'NO2', 'NH3', 'H2S', 'CH4', 'C2H5OH', 'HCHO', 'VOC_mix'
    ])

    def __post_init__(self):
        if self.sensitivity_matrix is None:
            # 기본 감도 매트릭스 생성 (교차반응성 포함)
            self.sensitivity_matrix = self._generate_sensitivity_matrix()
        if self.baseline is None:
            self.baseline = np.ones(self.num_sensors) * 1.0  # 기준 저항값

    def _generate_sensitivity_matrix(self) -> np.ndarray:
        """감도 매트릭스 생성 (교차반응성 반영)"""
        num_gases = len(self.target_gases)
        matrix = np.random.uniform(0.1, 2.0, (self.num_sensors, num_gases))

        # 각 센서가 특정 가스에 더 민감하도록 설정
        for i in range(min(self.num_sensors, num_gases)):
            matrix[i, i] = np.random.uniform(3.0, 5.0)

        return matrix

    def measure(self, gas_concentrations: Dict[str, float]) -> np.ndarray:
        """
        기체 농도 측정

        Args:
            gas_concentrations: 기체별 농도 (ppm)

        Returns:
            센서 응답 배열
        """
        # 농도 벡터 생성
        conc_vector = np.zeros(len(self.target_gases))
        for i, gas in enumerate(self.target_gases):
            if gas in gas_concentrations:
                conc_vector[i] = gas_concentrations[gas]

        # 센서 응답 계산 (비선형 응답 모델)
        # R/R0 = 1 + Σ(Si * Ci^n)
        response = self.baseline.copy()

        for i in range(self.num_sensors):
            for j in range(len(self.target_gases)):
                sensitivity = self.sensitivity_matrix[i, j]
                concentration = conc_vector[j]
                # Power law response (n ≈ 0.5 for most gas sensors)
                response[i] += sensitivity * (concentration ** 0.5)

        # 온도/습도 보정
        temp_factor = 1.0 + 0.02 * (self.temperature_c - 25.0)
        humidity_factor = 1.0 + 0.01 * (self.humidity_rh - 50.0)
        response *= temp_factor * humidity_factor

        # 노이즈 추가
        noise = np.random.normal(0, 0.01, self.num_sensors)
        response += noise

        self.current_response = response
        return response

    def estimate_concentrations(self, response: np.ndarray) -> Dict[str, float]:
        """
        센서 응답으로부터 기체 농도 추정 (역산)

        최소자승법 기반 농도 추정
        """
        # 정규화된 응답
        normalized = (response - self.baseline) / self.baseline

        # 의사역행렬을 이용한 농도 추정
        # C = (S^T * S)^-1 * S^T * R
        S = self.sensitivity_matrix
        try:
            S_pinv = np.linalg.pinv(S)
            concentrations = S_pinv @ normalized
            concentrations = np.maximum(concentrations, 0) ** 2  # 역 power law
        except:
            concentrations = np.zeros(len(self.target_gases))

        # 결과 딕셔너리 생성
        result = {}
        for i, gas in enumerate(self.target_gases):
            result[gas] = float(concentrations[i])

        return result


@dataclass
class GasAnalysisResult:
    """기체 분석 결과"""
    timestamp: datetime
    sample_id: str

    # 농도 정보
    detected_gases: Dict[str, float]  # 기체별 농도 (ppm)
    total_voc_ppb: float  # 총 VOC 농도 (ppb)

    # 센서 데이터
    raw_response: np.ndarray
    processed_response: np.ndarray

    # 분석 조건
    sampling_duration_sec: float
    flow_rate_ml_min: float
    temperature_c: float
    humidity_rh: float

    # 품질 지표
    confidence: float  # 신뢰도 (0-1)
    snr_db: float  # 신호 대 잡음비

    def get_dominant_gas(self) -> Tuple[str, float]:
        """주요 검출 기체 반환"""
        if not self.detected_gases:
            return ("none", 0.0)

        dominant = max(self.detected_gases.items(), key=lambda x: x[1])
        return dominant

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'sample_id': self.sample_id,
            'detected_gases': self.detected_gases,
            'total_voc_ppb': self.total_voc_ppb,
            'dominant_gas': self.get_dominant_gas(),
            'confidence': self.confidence,
            'snr_db': self.snr_db,
            'conditions': {
                'duration_sec': self.sampling_duration_sec,
                'flow_rate_ml_min': self.flow_rate_ml_min,
                'temperature_c': self.temperature_c,
                'humidity_rh': self.humidity_rh
            }
        }


class GasSamplingSystem:
    """
    기체 시료 분석 시스템

    이온풍 기반 무소음 기체 흡입 및 분석 통합 시스템
    """

    def __init__(self,
                 system_id: str = "GAS_SAMPLER_001",
                 num_sensors: int = 8):
        """
        Args:
            system_id: 시스템 식별자
            num_sensors: 센서 수
        """
        self.system_id = system_id
        self.state = SamplingState.IDLE

        # 컴포넌트 초기화
        self.emitter = EmitterElectrode(
            electrode_id=f"{system_id}_EMITTER",
            tip_radius_um=10.0,
            material="tungsten"
        )

        self.ion_wind_generator = IonWindGenerator(
            generator_id=f"{system_id}_ION_WIND",
            emitter=self.emitter
        )

        self.concentrator = ParticleConcentrator(
            concentrator_id=f"{system_id}_CONCENTRATOR"
        )

        self.sensor_array = GasSensorArray(
            array_id=f"{system_id}_SENSORS",
            num_sensors=num_sensors
        )

        # 측정 이력
        self.measurement_history: List[GasAnalysisResult] = []

        # 설정
        self.default_sampling_duration_sec: float = 30.0
        self.warmup_time_sec: float = 5.0

    def start_sampling(self,
                       mode: IonWindMode = IonWindMode.NORMAL,
                       duration_sec: Optional[float] = None) -> bool:
        """
        샘플링 시작

        Args:
            mode: 이온풍 모드
            duration_sec: 샘플링 시간 (초)

        Returns:
            성공 여부
        """
        if self.state != SamplingState.IDLE:
            return False

        # 워밍업
        self.state = SamplingState.WARMING_UP
        self.ion_wind_generator.set_mode(IonWindMode.LOW_POWER)

        # 메인 샘플링 모드로 전환
        self.state = SamplingState.SAMPLING
        self.ion_wind_generator.set_mode(mode)
        self.concentrator.start_concentration()

        return True

    def stop_sampling(self) -> None:
        """샘플링 중지"""
        self.ion_wind_generator.set_mode(IonWindMode.OFF)
        self.state = SamplingState.IDLE

    def analyze(self,
                sample_id: Optional[str] = None,
                gas_concentrations: Optional[Dict[str, float]] = None) -> GasAnalysisResult:
        """
        기체 분석 수행

        Args:
            sample_id: 시료 ID
            gas_concentrations: 시뮬레이션용 기체 농도 (실제 측정시 None)

        Returns:
            분석 결과
        """
        if sample_id is None:
            sample_id = f"GAS_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.state = SamplingState.ANALYZING

        # 센서 측정
        if gas_concentrations is None:
            # 실제 측정 시뮬레이션 (기본값)
            gas_concentrations = {
                'CO': np.random.uniform(0, 10),
                'NO2': np.random.uniform(0, 0.5),
                'VOC_mix': np.random.uniform(0, 100)
            }

        raw_response = self.sensor_array.measure(gas_concentrations)

        # 기준선 보정
        processed_response = raw_response - self.sensor_array.baseline

        # 농도 추정
        estimated_concentrations = self.sensor_array.estimate_concentrations(raw_response)

        # 총 VOC 계산
        total_voc = estimated_concentrations.get('VOC_mix', 0) * 1000  # ppm -> ppb

        # SNR 계산
        signal_power = np.mean(processed_response ** 2)
        noise_power = 0.01 ** 2  # 추정 노이즈
        snr_db = 10 * np.log10(signal_power / noise_power + 1e-10)

        # 신뢰도 계산
        confidence = min(1.0, snr_db / 40.0)

        # 결과 생성
        result = GasAnalysisResult(
            timestamp=datetime.now(),
            sample_id=sample_id,
            detected_gases=estimated_concentrations,
            total_voc_ppb=total_voc,
            raw_response=raw_response,
            processed_response=processed_response,
            sampling_duration_sec=self.default_sampling_duration_sec,
            flow_rate_ml_min=self.ion_wind_generator.current_flow_rate_ml_min,
            temperature_c=self.sensor_array.temperature_c,
            humidity_rh=self.sensor_array.humidity_rh,
            confidence=confidence,
            snr_db=snr_db
        )

        self.measurement_history.append(result)
        self.state = SamplingState.IDLE

        return result

    def continuous_monitoring(self,
                              interval_sec: float = 10.0,
                              num_samples: int = 10) -> List[GasAnalysisResult]:
        """
        연속 모니터링

        Args:
            interval_sec: 측정 간격 (초)
            num_samples: 측정 횟수

        Returns:
            분석 결과 목록
        """
        results = []

        self.start_sampling(IonWindMode.NORMAL)

        for i in range(num_samples):
            # 농축
            self.concentrator.accumulate(
                self.ion_wind_generator.current_flow_rate_ml_min,
                np.random.uniform(0.1, 1.0),  # 시뮬레이션 농도
                interval_sec
            )

            # 분석
            result = self.analyze(sample_id=f"CONTINUOUS_{i+1:04d}")
            results.append(result)

        self.stop_sampling()
        return results

    def clean_system(self) -> None:
        """시스템 청소"""
        self.state = SamplingState.CLEANING

        # 고출력 이온풍으로 잔류물 제거
        self.ion_wind_generator.set_mode(IonWindMode.HIGH_CONCENTRATION)

        # 농축기 청소
        self.concentrator.clean()

        # 정상 상태로 복귀
        self.ion_wind_generator.set_mode(IonWindMode.OFF)
        self.state = SamplingState.IDLE

    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 반환"""
        return {
            'system_id': self.system_id,
            'state': self.state.value,
            'ion_wind': self.ion_wind_generator.get_status(),
            'concentrator': {
                'accumulated_mass_ng': self.concentrator.accumulated_mass_ng,
                'surface_concentration': self.concentrator.get_surface_concentration()
            },
            'sensor_array': {
                'num_sensors': self.sensor_array.num_sensors,
                'temperature_c': self.sensor_array.temperature_c,
                'humidity_rh': self.sensor_array.humidity_rh
            },
            'measurements_count': len(self.measurement_history),
            'emitter_lifetime_remaining': self.emitter.get_remaining_lifetime()
        }

    def calibrate_sensors(self,
                          reference_gas: str,
                          reference_concentration: float) -> Dict[str, float]:
        """
        센서 캘리브레이션

        Args:
            reference_gas: 기준 기체
            reference_concentration: 기준 농도 (ppm)

        Returns:
            캘리브레이션 결과
        """
        # 기준 가스 측정
        response = self.sensor_array.measure({reference_gas: reference_concentration})

        # 감도 업데이트
        gas_idx = self.sensor_array.target_gases.index(reference_gas) if reference_gas in self.sensor_array.target_gases else -1

        if gas_idx >= 0:
            expected_response = reference_concentration ** 0.5
            actual_response = (response - self.sensor_array.baseline) / self.sensor_array.baseline

            correction_factors = expected_response / (actual_response + 1e-10)

            for i in range(self.sensor_array.num_sensors):
                self.sensor_array.sensitivity_matrix[i, gas_idx] *= correction_factors[i]

        return {
            'reference_gas': reference_gas,
            'reference_concentration': reference_concentration,
            'response': response.tolist(),
            'calibration_status': 'completed'
        }


# 편의 함수
def create_gas_sampling_system(system_id: str = "DEFAULT") -> GasSamplingSystem:
    """기체 샘플링 시스템 생성 헬퍼"""
    return GasSamplingSystem(system_id=system_id)


def quick_gas_analysis(gas_concentrations: Dict[str, float]) -> GasAnalysisResult:
    """빠른 기체 분석"""
    system = GasSamplingSystem()
    system.start_sampling()
    result = system.analyze(gas_concentrations=gas_concentrations)
    system.stop_sampling()
    return result


__all__ = [
    # Enums
    'IonWindMode',
    'DischargeType',
    'GasType',
    'SamplingState',
    # Classes
    'EmitterElectrode',
    'IonWindGenerator',
    'ParticleConcentrator',
    'GasSensorArray',
    'GasAnalysisResult',
    'GasSamplingSystem',
    # Functions
    'create_gas_sampling_system',
    'quick_gas_analysis',
]
