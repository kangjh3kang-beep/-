"""
상 가변형 인터페이스 모듈 (Phase-Variable Interface Module)

액체, 기체, 고체를 포함하는 다양한 상태의 시료를 단일 플랫폼에서 분석.
전도성 매개층(하이드로겔)을 통한 고체 시료 직접 측정 지원.

특허 참조: 실시예 8 (도 17, 18)
"""

from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np


class SamplePhase(Enum):
    """시료 상태"""
    LIQUID = "liquid"       # 액체
    GAS = "gas"             # 기체
    SOLID = "solid"         # 고체
    AEROSOL = "aerosol"     # 에어로졸
    SLURRY = "slurry"       # 슬러리
    GEL = "gel"             # 젤
    POWDER = "powder"       # 분말


class MediatingLayerType(Enum):
    """전도성 매개층 유형"""
    HYDROGEL = "hydrogel"               # 하이드로겔
    IONIC_LIQUID = "ionic_liquid"       # 이온성 액체
    CONDUCTIVE_POLYMER = "conductive_polymer"  # 전도성 고분자
    ELECTROLYTE_GEL = "electrolyte_gel"  # 전해질 젤
    MOISTURE_FILM = "moisture_film"     # 수분 필름


class InterfaceMode(Enum):
    """인터페이스 모드"""
    DIRECT_CONTACT = "direct_contact"       # 직접 접촉
    MEDIATED_CONTACT = "mediated_contact"   # 매개층 접촉
    GAS_DIFFUSION = "gas_diffusion"         # 기체 확산
    DISSOLUTION = "dissolution"             # 용해
    EXTRACTION = "extraction"               # 추출


@dataclass
class ConductiveMediatingLayer:
    """
    전도성 매개층 (Conductive Mediating Layer)

    수분과 전해질을 함유한 하이드로겔로 구성되어,
    고체 시료와 전극 사이에 이온 전도 경로를 형성.
    """
    layer_type: MediatingLayerType = MediatingLayerType.HYDROGEL
    thickness_um: float = 100.0         # 두께 (μm)
    conductivity_s_m: float = 0.1       # 전도도 (S/m)
    moisture_content: float = 0.8       # 수분 함량 (0-1)
    electrolyte_concentration_m: float = 0.1  # 전해질 농도 (M)
    ph: float = 7.0                     # pH
    temperature_c: float = 25.0         # 온도 (°C)

    def calculate_impedance(self, frequency_hz: float = 1000.0) -> complex:
        """
        임피던스 계산

        Args:
            frequency_hz: 주파수 (Hz)

        Returns:
            complex: 임피던스 (Ω)
        """
        # 저항 성분 (두께와 전도도에 의존)
        area_m2 = 1e-6  # 1 mm² 가정
        thickness_m = self.thickness_um * 1e-6
        resistance = thickness_m / (self.conductivity_s_m * area_m2)

        # 용량 성분 (하이드로겔의 유전 특성)
        epsilon_r = 80 * self.moisture_content  # 수분 함량에 비례
        epsilon_0 = 8.854e-12
        capacitance = epsilon_0 * epsilon_r * area_m2 / thickness_m

        # 임피던스 계산
        omega = 2 * np.pi * frequency_hz
        z_c = 1 / (1j * omega * capacitance)
        z_total = resistance + z_c

        return z_total

    def dissolution_rate(self, sample_solubility: float) -> float:
        """
        고체 시료 용해 속도 계산

        Args:
            sample_solubility: 시료 용해도 (g/L)

        Returns:
            float: 용해 속도 (g/s)
        """
        # 수분 함량과 온도에 의존하는 용해 속도
        base_rate = sample_solubility * 1e-6
        temp_factor = np.exp((self.temperature_c - 25) / 20)
        moisture_factor = self.moisture_content ** 0.5

        return base_rate * temp_factor * moisture_factor


@dataclass
class PhaseVariableConfig:
    """상 가변형 인터페이스 설정"""
    target_phase: SamplePhase = SamplePhase.LIQUID
    interface_mode: InterfaceMode = InterfaceMode.DIRECT_CONTACT
    mediating_layer: Optional[ConductiveMediatingLayer] = None
    contact_time_s: float = 10.0        # 접촉 시간
    temperature_c: float = 25.0         # 작동 온도
    humidity_percent: float = 50.0      # 상대 습도


@dataclass
class SampleCharacteristics:
    """시료 특성"""
    phase: SamplePhase
    conductivity_s_m: float = 0.0       # 전기 전도도
    viscosity_pa_s: float = 0.001       # 점도 (물 기준)
    density_kg_m3: float = 1000.0       # 밀도
    solubility_g_l: float = 0.0         # 용해도
    vapor_pressure_pa: float = 0.0      # 증기압
    particle_size_um: Optional[float] = None  # 입자 크기 (고체/분말)
    moisture_content: float = 0.0       # 수분 함량 (고체)


class PhaseVariableInterface:
    """
    상 가변형 샘플링 인터페이스 (Phase-Variable Sampling Interface)

    액체, 기체, 고체를 포함하는 다양한 상태의 시료를 단일 인터페이스에서 처리.

    Example:
        >>> interface = PhaseVariableInterface()
        >>> interface.configure(SamplePhase.SOLID)
        >>> result = interface.process_sample(solid_sample_data)
    """

    def __init__(self, config: Optional[PhaseVariableConfig] = None):
        """
        초기화

        Args:
            config: 인터페이스 설정
        """
        self.config = config or PhaseVariableConfig()

        # 기본 전도성 매개층
        self._mediating_layer = self.config.mediating_layer or ConductiveMediatingLayer()

        # 상태
        self._current_mode = self.config.interface_mode
        self._sample_characteristics: Optional[SampleCharacteristics] = None

    def configure(self,
                  target_phase: SamplePhase,
                  auto_select_mode: bool = True) -> InterfaceMode:
        """
        시료 상태에 따른 인터페이스 구성

        Args:
            target_phase: 목표 시료 상태
            auto_select_mode: 자동 모드 선택 여부

        Returns:
            InterfaceMode: 선택된 인터페이스 모드
        """
        self.config.target_phase = target_phase

        if auto_select_mode:
            self._current_mode = self._select_optimal_mode(target_phase)
        else:
            self._current_mode = self.config.interface_mode

        # 고체 시료인 경우 매개층 활성화
        if target_phase in [SamplePhase.SOLID, SamplePhase.POWDER]:
            self._current_mode = InterfaceMode.MEDIATED_CONTACT

        return self._current_mode

    def _select_optimal_mode(self, phase: SamplePhase) -> InterfaceMode:
        """최적 인터페이스 모드 선택"""
        mode_map = {
            SamplePhase.LIQUID: InterfaceMode.DIRECT_CONTACT,
            SamplePhase.GAS: InterfaceMode.GAS_DIFFUSION,
            SamplePhase.SOLID: InterfaceMode.MEDIATED_CONTACT,
            SamplePhase.AEROSOL: InterfaceMode.GAS_DIFFUSION,
            SamplePhase.SLURRY: InterfaceMode.DIRECT_CONTACT,
            SamplePhase.GEL: InterfaceMode.DIRECT_CONTACT,
            SamplePhase.POWDER: InterfaceMode.DISSOLUTION,
        }
        return mode_map.get(phase, InterfaceMode.DIRECT_CONTACT)

    def set_mediating_layer(self, layer: ConductiveMediatingLayer) -> None:
        """전도성 매개층 설정"""
        self._mediating_layer = layer
        self.config.mediating_layer = layer

    def process_sample(self,
                       sample_signal: np.ndarray,
                       sample_chars: Optional[SampleCharacteristics] = None,
                       reference_signal: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        시료 처리

        Args:
            sample_signal: 시료 신호
            sample_chars: 시료 특성
            reference_signal: 참조 신호

        Returns:
            Dict: 처리 결과
        """
        self._sample_characteristics = sample_chars

        # 인터페이스 모드에 따른 신호 처리
        if self._current_mode == InterfaceMode.DIRECT_CONTACT:
            processed = self._process_direct_contact(sample_signal)
        elif self._current_mode == InterfaceMode.MEDIATED_CONTACT:
            processed = self._process_mediated_contact(sample_signal)
        elif self._current_mode == InterfaceMode.GAS_DIFFUSION:
            processed = self._process_gas_diffusion(sample_signal)
        elif self._current_mode == InterfaceMode.DISSOLUTION:
            processed = self._process_dissolution(sample_signal)
        else:
            processed = self._process_extraction(sample_signal)

        # 차동 연산 (참조 신호가 있는 경우)
        if reference_signal is not None:
            differential = processed['signal'] - reference_signal
        else:
            differential = processed['signal']

        return {
            'processed_signal': processed['signal'],
            'differential_signal': differential,
            'interface_mode': self._current_mode.value,
            'contact_quality': processed.get('quality', 1.0),
            'impedance': processed.get('impedance', None),
            'metadata': processed.get('metadata', {}),
        }

    def _process_direct_contact(self, signal: np.ndarray) -> Dict[str, Any]:
        """직접 접촉 처리 (액체 시료)"""
        # 직접 접촉은 신호 그대로 전달
        return {
            'signal': signal.copy(),
            'quality': 1.0,
            'metadata': {'mode': 'direct_contact'},
        }

    def _process_mediated_contact(self, signal: np.ndarray) -> Dict[str, Any]:
        """매개층 접촉 처리 (고체 시료)"""
        # 매개층의 임피던스 영향 고려
        impedance = self._mediating_layer.calculate_impedance()

        # 신호 감쇠 (매개층 두께에 의한)
        attenuation = np.exp(-self._mediating_layer.thickness_um / 500)

        # 확산 지연 효과 (간단한 이동 평균으로 모사)
        window = max(3, int(self._mediating_layer.thickness_um / 50))
        if len(signal) > window:
            kernel = np.ones(window) / window
            processed = np.convolve(signal, kernel, mode='same') * attenuation
        else:
            processed = signal * attenuation

        # 접촉 품질 (수분 함량에 의존)
        quality = self._mediating_layer.moisture_content

        return {
            'signal': processed,
            'quality': quality,
            'impedance': impedance,
            'metadata': {
                'mode': 'mediated_contact',
                'attenuation': attenuation,
                'layer_thickness': self._mediating_layer.thickness_um,
            },
        }

    def _process_gas_diffusion(self, signal: np.ndarray) -> Dict[str, Any]:
        """기체 확산 처리"""
        # 기체의 확산 특성 고려
        diffusion_coeff = 0.1  # 확산 계수 (상대값)

        # 확산 필터 적용
        sigma = 2.0 / diffusion_coeff
        x = np.arange(-int(3*sigma), int(3*sigma)+1)
        gaussian = np.exp(-x**2 / (2*sigma**2))
        gaussian /= gaussian.sum()

        if len(signal) > len(gaussian):
            processed = np.convolve(signal, gaussian, mode='same')
        else:
            processed = signal.copy()

        return {
            'signal': processed,
            'quality': 0.9,
            'metadata': {
                'mode': 'gas_diffusion',
                'diffusion_coeff': diffusion_coeff,
            },
        }

    def _process_dissolution(self, signal: np.ndarray) -> Dict[str, Any]:
        """용해 처리 (분말 시료)"""
        # 용해 속도에 따른 신호 변화
        if self._sample_characteristics and self._sample_characteristics.solubility_g_l > 0:
            dissolution_rate = self._mediating_layer.dissolution_rate(
                self._sample_characteristics.solubility_g_l
            )
        else:
            dissolution_rate = 0.01

        # 시간에 따른 용해 프로파일
        time_constant = 1.0 / (dissolution_rate + 0.01)
        t = np.linspace(0, 1, len(signal))
        dissolution_profile = 1 - np.exp(-t / time_constant)

        processed = signal * dissolution_profile

        return {
            'signal': processed,
            'quality': 0.85,
            'metadata': {
                'mode': 'dissolution',
                'dissolution_rate': dissolution_rate,
            },
        }

    def _process_extraction(self, signal: np.ndarray) -> Dict[str, Any]:
        """추출 처리"""
        # 추출 효율에 따른 신호 스케일링
        extraction_efficiency = 0.7

        processed = signal * extraction_efficiency

        return {
            'signal': processed,
            'quality': extraction_efficiency,
            'metadata': {
                'mode': 'extraction',
                'efficiency': extraction_efficiency,
            },
        }

    def estimate_sample_phase(self, signal_characteristics: Dict[str, float]) -> SamplePhase:
        """
        신호 특성으로부터 시료 상태 추정

        Args:
            signal_characteristics: 신호 특성 딕셔너리

        Returns:
            SamplePhase: 추정된 시료 상태
        """
        impedance_magnitude = signal_characteristics.get('impedance_magnitude', 1000)
        noise_level = signal_characteristics.get('noise_level', 0.1)
        response_time = signal_characteristics.get('response_time', 1.0)

        # 임피던스가 매우 높으면 기체
        if impedance_magnitude > 1e6:
            return SamplePhase.GAS

        # 응답 시간이 긴 경우 고체
        if response_time > 5.0:
            return SamplePhase.SOLID

        # 노이즈가 높으면 에어로졸
        if noise_level > 0.3:
            return SamplePhase.AEROSOL

        # 기본값은 액체
        return SamplePhase.LIQUID

    @property
    def current_mode(self) -> InterfaceMode:
        """현재 인터페이스 모드"""
        return self._current_mode

    @property
    def mediating_layer(self) -> ConductiveMediatingLayer:
        """전도성 매개층"""
        return self._mediating_layer


class SolidSampleAnalyzer:
    """
    고체 시료 분석기

    전도성 매개층을 통해 고체 시료를 직접 측정.
    별도의 용해 과정 없이 고체 시료와 전극 사이에 이온 전도 경로 형성.

    특허 참조: 도 18
    """

    def __init__(self,
                 mediating_layer: Optional[ConductiveMediatingLayer] = None):
        """
        초기화

        Args:
            mediating_layer: 전도성 매개층
        """
        self.mediating_layer = mediating_layer or ConductiveMediatingLayer()
        self.interface = PhaseVariableInterface()
        self.interface.set_mediating_layer(self.mediating_layer)
        self.interface.configure(SamplePhase.SOLID)

    def analyze(self,
                sensing_signal: np.ndarray,
                reference_signal: np.ndarray,
                contact_duration_s: float = 10.0) -> Dict[str, Any]:
        """
        고체 시료 분석

        Args:
            sensing_signal: 감지 전극 신호
            reference_signal: 참조 전극 신호
            contact_duration_s: 접촉 시간 (초)

        Returns:
            Dict: 분석 결과
        """
        # 시료 특성 설정
        sample_chars = SampleCharacteristics(
            phase=SamplePhase.SOLID,
            conductivity_s_m=0.001,
            solubility_g_l=10.0,
        )

        # 인터페이스를 통한 처리
        result = self.interface.process_sample(
            sensing_signal,
            sample_chars,
            reference_signal
        )

        # 접촉 시간에 따른 신호 안정화 분석
        stability = self._analyze_stability(result['differential_signal'])

        result['stability'] = stability
        result['contact_duration'] = contact_duration_s
        result['layer_impedance'] = self.mediating_layer.calculate_impedance()

        return result

    def _analyze_stability(self, signal: np.ndarray) -> Dict[str, float]:
        """신호 안정성 분석"""
        if len(signal) < 10:
            return {'stable': True, 'drift': 0.0}

        # 후반부 신호의 표준편차로 안정성 판단
        tail = signal[-len(signal)//4:]
        std = np.std(tail)
        mean = np.mean(tail)

        # 드리프트 계산
        drift = (signal[-1] - signal[0]) / (len(signal) + 1)

        return {
            'stable': std < 0.1 * abs(mean) if mean != 0 else std < 0.01,
            'std': std,
            'drift': drift,
            'final_value': signal[-1],
        }


class MultiPhaseSampleHandler:
    """
    다상 시료 핸들러

    복합 시료(예: 슬러리, 에어로졸)를 처리하기 위한 통합 핸들러.
    """

    def __init__(self):
        """초기화"""
        self._liquid_interface = PhaseVariableInterface()
        self._liquid_interface.configure(SamplePhase.LIQUID)

        self._solid_interface = PhaseVariableInterface()
        self._solid_interface.configure(SamplePhase.SOLID)

        self._gas_interface = PhaseVariableInterface()
        self._gas_interface.configure(SamplePhase.GAS)

    def process(self,
                signal: np.ndarray,
                detected_phases: List[SamplePhase],
                reference_signal: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        다상 시료 처리

        Args:
            signal: 시료 신호
            detected_phases: 검출된 시료 상태 리스트
            reference_signal: 참조 신호

        Returns:
            Dict: 처리 결과
        """
        results = {}

        for phase in detected_phases:
            if phase == SamplePhase.LIQUID:
                results['liquid'] = self._liquid_interface.process_sample(
                    signal, None, reference_signal
                )
            elif phase in [SamplePhase.SOLID, SamplePhase.POWDER]:
                results['solid'] = self._solid_interface.process_sample(
                    signal, None, reference_signal
                )
            elif phase in [SamplePhase.GAS, SamplePhase.AEROSOL]:
                results['gas'] = self._gas_interface.process_sample(
                    signal, None, reference_signal
                )

        # 결합 결과
        if len(results) > 1:
            combined_signal = np.mean([
                r['differential_signal'] for r in results.values()
            ], axis=0)
        elif len(results) == 1:
            combined_signal = list(results.values())[0]['differential_signal']
        else:
            combined_signal = signal

        return {
            'phase_results': results,
            'combined_signal': combined_signal,
            'detected_phases': [p.value for p in detected_phases],
        }
