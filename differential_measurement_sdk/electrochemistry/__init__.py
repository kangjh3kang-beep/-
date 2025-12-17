"""
전기화학 측정 모듈 (Electrochemistry Module)

전기화학 분석 기법 구현 (MPK-RDR-MFG-SPEC v2.2 섹션 5.2)

주요 기능:
- OCP (Open Circuit Potential): 개방회로전위
- CA (Chronoamperometry): 전류-시간 측정
- CV (Cyclic Voltammetry): 순환전압전류법
- DPV (Differential Pulse Voltammetry): 차동펄스전압전류법
- SWV (Square Wave Voltammetry): 구형파전압전류법
- EIS (Electrochemical Impedance Spectroscopy): 전기화학적 임피던스 분광법 (옵션)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime
import numpy as np


class MeasurementMode(Enum):
    """측정 모드"""
    OCP = "ocp"      # Open Circuit Potential
    CA = "ca"        # Chronoamperometry
    CV = "cv"        # Cyclic Voltammetry
    DPV = "dpv"      # Differential Pulse Voltammetry
    SWV = "swv"      # Square Wave Voltammetry
    EIS = "eis"      # Electrochemical Impedance Spectroscopy


class ScanDirection(Enum):
    """스캔 방향"""
    POSITIVE = "positive"  # 양방향 스캔
    NEGATIVE = "negative"  # 음방향 스캔
    BOTH = "both"         # 양방향 (CV)


class WaveformType(Enum):
    """파형 유형"""
    DC = "dc"
    STEP = "step"
    RAMP = "ramp"
    PULSE = "pulse"
    SQUARE_WAVE = "square_wave"
    SINE = "sine"


@dataclass
class OCPParameters:
    """OCP 측정 파라미터"""
    duration_s: float = 60.0           # 측정 시간
    sample_interval_ms: float = 100.0  # 샘플링 간격
    stability_threshold_mv: float = 1.0  # 안정화 기준 (mV/s)
    stability_window_s: float = 10.0   # 안정화 판정 윈도우


@dataclass
class CAParameters:
    """CA (Chronoamperometry) 파라미터"""
    potential_v: float = 0.0           # 인가 전위 (V)
    duration_s: float = 60.0           # 측정 시간
    sample_interval_ms: float = 10.0   # 샘플링 간격
    quiet_time_s: float = 2.0          # 초기 안정화 시간

    # 권장 범위 (MPK-RDR-MFG-SPEC)
    POTENTIAL_RANGE: Tuple[float, float] = (-0.8, 0.8)  # ±0.8V
    DURATION_RANGE: Tuple[float, float] = (0.01, 600)   # 10ms ~ 600s


@dataclass
class CVParameters:
    """CV (Cyclic Voltammetry) 파라미터"""
    start_potential_v: float = -0.5    # 시작 전위
    vertex1_potential_v: float = 0.5   # 정점 1 전위
    vertex2_potential_v: float = -0.5  # 정점 2 전위
    final_potential_v: float = -0.5    # 종료 전위

    scan_rate_mv_s: float = 50.0       # 스캔 속도 (mV/s)
    step_potential_mv: float = 5.0     # 스텝 전위 (mV)
    num_cycles: int = 3                # 사이클 수

    quiet_time_s: float = 2.0          # 안정화 시간

    # 권장 범위
    SCAN_RATE_RANGE: Tuple[float, float] = (1, 200)   # 1~200 mV/s
    STEP_RANGE: Tuple[float, float] = (1, 10)          # 1~10 mV


@dataclass
class DPVParameters:
    """DPV (Differential Pulse Voltammetry) 파라미터"""
    start_potential_v: float = -0.5
    end_potential_v: float = 0.5

    step_potential_mv: float = 5.0     # 스텝 전위
    pulse_amplitude_mv: float = 50.0   # 펄스 진폭
    pulse_width_ms: float = 50.0       # 펄스 폭
    pulse_period_ms: float = 200.0     # 펄스 주기

    quiet_time_s: float = 2.0

    # 권장 범위
    PULSE_AMPLITUDE_RANGE: Tuple[float, float] = (10, 100)  # 10~100 mV
    PULSE_WIDTH_RANGE: Tuple[float, float] = (10, 200)      # 10~200 ms


@dataclass
class SWVParameters:
    """SWV (Square Wave Voltammetry) 파라미터"""
    start_potential_v: float = -0.5
    end_potential_v: float = 0.5

    step_potential_mv: float = 5.0     # 스텝 전위
    amplitude_mv: float = 25.0         # 구형파 진폭
    frequency_hz: float = 25.0         # 주파수

    quiet_time_s: float = 2.0

    # 권장 범위
    FREQUENCY_RANGE: Tuple[float, float] = (1, 200)  # 1~200 Hz


@dataclass
class EISParameters:
    """EIS (Electrochemical Impedance Spectroscopy) 파라미터"""
    dc_potential_v: float = 0.0        # DC 바이어스 전위
    ac_amplitude_mv: float = 10.0      # AC 진폭

    start_frequency_hz: float = 100000  # 시작 주파수
    end_frequency_hz: float = 0.1       # 종료 주파수
    points_per_decade: int = 10         # 디케이드당 포인트 수

    quiet_time_s: float = 5.0

    # 권장 범위 (옵션)
    FREQUENCY_RANGE: Tuple[float, float] = (0.1, 10000)  # 0.1Hz ~ 10kHz (기본)
    # HF 옵션: 100kHz+


@dataclass
class MeasurementResult:
    """측정 결과"""
    mode: MeasurementMode
    timestamp: datetime
    sample_id: str

    # 시간/전위/전류 데이터
    time_s: np.ndarray
    potential_v: np.ndarray
    current_a: np.ndarray

    # 채널 정보
    channel_id: int = 0

    # 파라미터 스냅샷
    parameters: Dict[str, Any] = field(default_factory=dict)

    # 환경 조건
    temperature_c: float = 25.0
    humidity_rh: float = 50.0

    # 품질 지표
    noise_level_a: float = 0.0
    drift_rate_v_s: float = 0.0

    def get_peak_current(self) -> Tuple[float, float]:
        """피크 전류 및 해당 전위 반환"""
        peak_idx = np.argmax(np.abs(self.current_a))
        return (self.potential_v[peak_idx], self.current_a[peak_idx])

    def get_average_current(self,
                           start_time: float = None,
                           end_time: float = None) -> float:
        """평균 전류"""
        mask = np.ones(len(self.time_s), dtype=bool)

        if start_time is not None:
            mask &= self.time_s >= start_time
        if end_time is not None:
            mask &= self.time_s <= end_time

        return np.mean(self.current_a[mask])

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'mode': self.mode.value,
            'timestamp': self.timestamp.isoformat(),
            'sample_id': self.sample_id,
            'channel_id': self.channel_id,
            'data_points': len(self.time_s),
            'duration_s': float(self.time_s[-1] - self.time_s[0]) if len(self.time_s) > 0 else 0,
            'peak_current': self.get_peak_current(),
            'parameters': self.parameters,
            'temperature_c': self.temperature_c,
            'noise_level_a': self.noise_level_a
        }


@dataclass
class EISResult(MeasurementResult):
    """EIS 측정 결과"""
    frequency_hz: np.ndarray = field(default_factory=lambda: np.array([]))
    z_real_ohm: np.ndarray = field(default_factory=lambda: np.array([]))
    z_imag_ohm: np.ndarray = field(default_factory=lambda: np.array([]))
    phase_deg: np.ndarray = field(default_factory=lambda: np.array([]))
    magnitude_ohm: np.ndarray = field(default_factory=lambda: np.array([]))

    def get_nyquist_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Nyquist 플롯 데이터 (Z_real, -Z_imag)"""
        return (self.z_real_ohm, -self.z_imag_ohm)

    def get_bode_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Bode 플롯 데이터 (freq, magnitude, phase)"""
        return (self.frequency_hz, self.magnitude_ohm, self.phase_deg)


class WaveformGenerator:
    """
    파형 생성기

    전기화학 측정용 전위 파형 생성
    """

    @staticmethod
    def generate_step(start_v: float,
                      end_v: float,
                      duration_s: float,
                      sample_rate_hz: float) -> np.ndarray:
        """스텝 파형"""
        n_samples = int(duration_s * sample_rate_hz)
        waveform = np.ones(n_samples) * end_v
        waveform[0] = start_v
        return waveform

    @staticmethod
    def generate_ramp(start_v: float,
                      end_v: float,
                      duration_s: float,
                      sample_rate_hz: float) -> np.ndarray:
        """램프 파형"""
        n_samples = int(duration_s * sample_rate_hz)
        return np.linspace(start_v, end_v, n_samples)

    @staticmethod
    def generate_cv_waveform(params: CVParameters,
                            sample_rate_hz: float) -> np.ndarray:
        """CV 파형 생성"""
        scan_rate_v_s = params.scan_rate_mv_s / 1000.0

        waveform_parts = []

        # 시작 → 정점1
        duration1 = abs(params.vertex1_potential_v - params.start_potential_v) / scan_rate_v_s
        ramp1 = WaveformGenerator.generate_ramp(
            params.start_potential_v, params.vertex1_potential_v,
            duration1, sample_rate_hz
        )
        waveform_parts.append(ramp1)

        for cycle in range(params.num_cycles):
            # 정점1 → 정점2
            duration2 = abs(params.vertex2_potential_v - params.vertex1_potential_v) / scan_rate_v_s
            ramp2 = WaveformGenerator.generate_ramp(
                params.vertex1_potential_v, params.vertex2_potential_v,
                duration2, sample_rate_hz
            )
            waveform_parts.append(ramp2)

            # 정점2 → 정점1
            ramp3 = WaveformGenerator.generate_ramp(
                params.vertex2_potential_v, params.vertex1_potential_v,
                duration2, sample_rate_hz
            )
            waveform_parts.append(ramp3)

        # 정점1 → 종료
        duration_final = abs(params.final_potential_v - params.vertex1_potential_v) / scan_rate_v_s
        ramp_final = WaveformGenerator.generate_ramp(
            params.vertex1_potential_v, params.final_potential_v,
            duration_final, sample_rate_hz
        )
        waveform_parts.append(ramp_final)

        return np.concatenate(waveform_parts)

    @staticmethod
    def generate_dpv_waveform(params: DPVParameters,
                              sample_rate_hz: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        DPV 파형 생성

        Returns:
            (파형, 샘플링 마스크) - 마스크는 펄스 전/후 샘플링 포인트
        """
        step_v = params.step_potential_mv / 1000.0
        pulse_v = params.pulse_amplitude_mv / 1000.0

        num_steps = int(abs(params.end_potential_v - params.start_potential_v) / step_v)
        samples_per_period = int(params.pulse_period_ms * sample_rate_hz / 1000.0)
        samples_pulse = int(params.pulse_width_ms * sample_rate_hz / 1000.0)

        waveform = []
        sample_mask = []  # True = 샘플링 포인트

        direction = 1 if params.end_potential_v > params.start_potential_v else -1

        for step in range(num_steps):
            base_potential = params.start_potential_v + step * step_v * direction

            # 베이스 레벨 (펄스 전 샘플링)
            base_samples = samples_per_period - samples_pulse
            waveform.extend([base_potential] * base_samples)
            sample_mask.extend([False] * (base_samples - 1) + [True])  # 마지막에 샘플링

            # 펄스 레벨 (펄스 후 샘플링)
            pulse_potential = base_potential + pulse_v * direction
            waveform.extend([pulse_potential] * samples_pulse)
            sample_mask.extend([False] * (samples_pulse - 1) + [True])  # 마지막에 샘플링

        return np.array(waveform), np.array(sample_mask)

    @staticmethod
    def generate_swv_waveform(params: SWVParameters,
                              sample_rate_hz: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        SWV 파형 생성

        Returns:
            (파형, forward_mask, reverse_mask)
        """
        step_v = params.step_potential_mv / 1000.0
        amplitude_v = params.amplitude_mv / 1000.0
        period_s = 1.0 / params.frequency_hz
        samples_per_period = int(period_s * sample_rate_hz)
        half_period_samples = samples_per_period // 2

        num_steps = int(abs(params.end_potential_v - params.start_potential_v) / step_v)

        waveform = []
        forward_mask = []
        reverse_mask = []

        direction = 1 if params.end_potential_v > params.start_potential_v else -1

        for step in range(num_steps):
            base_potential = params.start_potential_v + step * step_v * direction

            # Forward 펄스 (+amplitude)
            forward_potential = base_potential + amplitude_v
            waveform.extend([forward_potential] * half_period_samples)
            forward_mask.extend([False] * (half_period_samples - 1) + [True])
            reverse_mask.extend([False] * half_period_samples)

            # Reverse 펄스 (-amplitude)
            reverse_potential = base_potential - amplitude_v
            waveform.extend([reverse_potential] * half_period_samples)
            forward_mask.extend([False] * half_period_samples)
            reverse_mask.extend([False] * (half_period_samples - 1) + [True])

        return np.array(waveform), np.array(forward_mask), np.array(reverse_mask)


class ElectrochemicalCell:
    """
    전기화학 셀 모델

    WE/RE/CE 3전극 구성 시뮬레이션
    """

    def __init__(self,
                 solution_resistance_ohm: float = 100.0,
                 charge_transfer_resistance_ohm: float = 1000.0,
                 double_layer_capacitance_f: float = 1e-6,
                 diffusion_coefficient: float = 1e-9):
        """
        Args:
            solution_resistance_ohm: 용액 저항 (Rs)
            charge_transfer_resistance_ohm: 전하이동 저항 (Rct)
            double_layer_capacitance_f: 이중층 커패시턴스 (Cdl)
            diffusion_coefficient: 확산 계수 (D)
        """
        self.Rs = solution_resistance_ohm
        self.Rct = charge_transfer_resistance_ohm
        self.Cdl = double_layer_capacitance_f
        self.D = diffusion_coefficient

        # Warburg 계수 (확산 임피던스)
        self.sigma_w = 100.0  # Ω·s^(-1/2)

    def get_current(self,
                    potential_v: float,
                    time_s: float = 1.0,
                    e0_v: float = 0.0,
                    n_electrons: int = 1,
                    concentration_m: float = 1e-3) -> float:
        """
        전류 계산 (Butler-Volmer + 확산 제한)
        """
        F = 96485  # Faraday constant
        R = 8.314  # Gas constant
        T = 298.15  # Temperature (K)

        # 과전위
        eta = potential_v - e0_v

        # Exchange current density (간단화)
        i0 = 1e-6  # A/cm²

        # Butler-Volmer
        alpha = 0.5
        bv_current = i0 * (np.exp(alpha * n_electrons * F * eta / (R * T)) -
                          np.exp(-(1 - alpha) * n_electrons * F * eta / (R * T)))

        # 확산 제한 (Cottrell)
        if time_s > 0:
            diffusion_limit = n_electrons * F * concentration_m * np.sqrt(self.D / (np.pi * time_s))
        else:
            diffusion_limit = float('inf')

        # 제한된 전류
        current = bv_current
        if abs(current) > abs(diffusion_limit):
            current = np.sign(current) * abs(diffusion_limit)

        # 노이즈 추가
        noise = np.random.normal(0, abs(current) * 0.01)
        current += noise

        return current

    def get_impedance(self, frequency_hz: float) -> complex:
        """
        임피던스 계산 (Randles 회로)

        Z = Rs + (Rct + Zw) // Cdl
        """
        omega = 2 * np.pi * frequency_hz

        # Warburg 임피던스
        if frequency_hz > 0:
            Zw = self.sigma_w / np.sqrt(omega) * (1 - 1j)
        else:
            Zw = complex(float('inf'), 0)

        # Cdl 임피던스
        if omega > 0:
            Zcdl = 1 / (1j * omega * self.Cdl)
        else:
            Zcdl = complex(float('inf'), 0)

        # 병렬 (Rct + Zw) // Cdl
        Z_parallel_num = (self.Rct + Zw) * Zcdl
        Z_parallel_den = (self.Rct + Zw) + Zcdl

        if abs(Z_parallel_den) > 1e-15:
            Z_parallel = Z_parallel_num / Z_parallel_den
        else:
            Z_parallel = complex(0, 0)

        # 총 임피던스
        Z_total = self.Rs + Z_parallel

        return Z_total


class ElectrochemistryEngine:
    """
    전기화학 측정 엔진

    모든 전기화학 측정 모드를 수행하는 메인 클래스
    """

    def __init__(self,
                 engine_id: str = "ECHEM_001",
                 sample_rate_hz: float = 1000.0):
        """
        Args:
            engine_id: 엔진 식별자
            sample_rate_hz: 기본 샘플링 레이트
        """
        self.engine_id = engine_id
        self.sample_rate_hz = sample_rate_hz

        # 전기화학 셀 모델
        self.cell = ElectrochemicalCell()

        # 파형 생성기
        self.waveform_gen = WaveformGenerator()

        # 측정 이력
        self.measurement_history: List[MeasurementResult] = []

        # 상태
        self.is_measuring = False
        self.current_mode: Optional[MeasurementMode] = None

    def measure_ocp(self,
                    params: OCPParameters = None,
                    channel_id: int = 0) -> MeasurementResult:
        """
        OCP (Open Circuit Potential) 측정

        전류 없이 평형 전위 측정
        """
        if params is None:
            params = OCPParameters()

        self.is_measuring = True
        self.current_mode = MeasurementMode.OCP

        n_samples = int(params.duration_s * 1000 / params.sample_interval_ms)
        time_s = np.linspace(0, params.duration_s, n_samples)

        # OCP 시뮬레이션 (안정화 + 드리프트 + 노이즈)
        initial_ocp = np.random.uniform(-0.3, 0.3)
        equilibrium_ocp = np.random.uniform(-0.1, 0.1)
        tau = 10.0  # 시정수

        potential_v = equilibrium_ocp + (initial_ocp - equilibrium_ocp) * np.exp(-time_s / tau)

        # 드리프트
        drift = 0.001 * time_s  # 1 mV/s 드리프트

        # 노이즈
        noise = np.random.normal(0, 0.001, n_samples)

        potential_v = potential_v + drift + noise

        # 전류는 0 (개방회로)
        current_a = np.zeros(n_samples)

        result = MeasurementResult(
            mode=MeasurementMode.OCP,
            timestamp=datetime.now(),
            sample_id=f"OCP_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            time_s=time_s,
            potential_v=potential_v,
            current_a=current_a,
            channel_id=channel_id,
            parameters=vars(params)
        )

        self.measurement_history.append(result)
        self.is_measuring = False

        return result

    def measure_ca(self,
                   params: CAParameters = None,
                   channel_id: int = 0) -> MeasurementResult:
        """
        CA (Chronoamperometry) 측정

        일정 전위에서 전류-시간 응답 측정
        """
        if params is None:
            params = CAParameters()

        self.is_measuring = True
        self.current_mode = MeasurementMode.CA

        n_samples = int(params.duration_s * 1000 / params.sample_interval_ms)
        time_s = np.linspace(0, params.duration_s, n_samples)

        # 전위 파형 (스텝)
        potential_v = np.ones(n_samples) * params.potential_v

        # 전류 응답 (Cottrell equation + 노이즈)
        current_a = np.zeros(n_samples)
        for i, t in enumerate(time_s):
            if t > 0.001:  # 초기 스파이크 방지
                current_a[i] = self.cell.get_current(params.potential_v, t)
            else:
                current_a[i] = self.cell.get_current(params.potential_v, 0.001)

        result = MeasurementResult(
            mode=MeasurementMode.CA,
            timestamp=datetime.now(),
            sample_id=f"CA_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            time_s=time_s,
            potential_v=potential_v,
            current_a=current_a,
            channel_id=channel_id,
            parameters=vars(params)
        )

        self.measurement_history.append(result)
        self.is_measuring = False

        return result

    def measure_cv(self,
                   params: CVParameters = None,
                   channel_id: int = 0) -> MeasurementResult:
        """
        CV (Cyclic Voltammetry) 측정

        순환 전압-전류 응답 측정
        """
        if params is None:
            params = CVParameters()

        self.is_measuring = True
        self.current_mode = MeasurementMode.CV

        # 파형 생성
        potential_v = self.waveform_gen.generate_cv_waveform(params, self.sample_rate_hz)
        n_samples = len(potential_v)
        time_s = np.arange(n_samples) / self.sample_rate_hz

        # 전류 응답
        current_a = np.zeros(n_samples)
        for i in range(n_samples):
            # 스캔 방향 고려
            if i > 0:
                scan_rate = (potential_v[i] - potential_v[i-1]) * self.sample_rate_hz
            else:
                scan_rate = 0

            current_a[i] = self.cell.get_current(potential_v[i], time_s[i] + 0.001)

            # 커패시턴스 전류 추가
            cap_current = self.cell.Cdl * scan_rate
            current_a[i] += cap_current

        result = MeasurementResult(
            mode=MeasurementMode.CV,
            timestamp=datetime.now(),
            sample_id=f"CV_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            time_s=time_s,
            potential_v=potential_v,
            current_a=current_a,
            channel_id=channel_id,
            parameters=vars(params)
        )

        self.measurement_history.append(result)
        self.is_measuring = False

        return result

    def measure_dpv(self,
                    params: DPVParameters = None,
                    channel_id: int = 0) -> MeasurementResult:
        """
        DPV (Differential Pulse Voltammetry) 측정
        """
        if params is None:
            params = DPVParameters()

        self.is_measuring = True
        self.current_mode = MeasurementMode.DPV

        # 파형 생성
        potential_full, sample_mask = self.waveform_gen.generate_dpv_waveform(
            params, self.sample_rate_hz
        )

        n_samples = len(potential_full)
        time_full = np.arange(n_samples) / self.sample_rate_hz

        # 전체 전류 계산
        current_full = np.zeros(n_samples)
        for i in range(n_samples):
            current_full[i] = self.cell.get_current(potential_full[i], time_full[i] + 0.001)

        # 샘플링 포인트에서 차동 전류 계산
        sampled_indices = np.where(sample_mask)[0]
        n_dpv_points = len(sampled_indices) // 2

        potential_v = np.zeros(n_dpv_points)
        current_a = np.zeros(n_dpv_points)

        for i in range(n_dpv_points):
            base_idx = sampled_indices[i * 2]
            pulse_idx = sampled_indices[i * 2 + 1]

            base_potential = potential_full[base_idx]
            diff_current = current_full[pulse_idx] - current_full[base_idx]

            potential_v[i] = base_potential
            current_a[i] = diff_current

        time_s = np.arange(n_dpv_points) * params.pulse_period_ms / 1000.0

        result = MeasurementResult(
            mode=MeasurementMode.DPV,
            timestamp=datetime.now(),
            sample_id=f"DPV_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            time_s=time_s,
            potential_v=potential_v,
            current_a=current_a,
            channel_id=channel_id,
            parameters=vars(params)
        )

        self.measurement_history.append(result)
        self.is_measuring = False

        return result

    def measure_swv(self,
                    params: SWVParameters = None,
                    channel_id: int = 0) -> MeasurementResult:
        """
        SWV (Square Wave Voltammetry) 측정
        """
        if params is None:
            params = SWVParameters()

        self.is_measuring = True
        self.current_mode = MeasurementMode.SWV

        # 파형 생성
        potential_full, forward_mask, reverse_mask = self.waveform_gen.generate_swv_waveform(
            params, self.sample_rate_hz
        )

        n_samples = len(potential_full)
        time_full = np.arange(n_samples) / self.sample_rate_hz

        # 전체 전류 계산
        current_full = np.zeros(n_samples)
        for i in range(n_samples):
            current_full[i] = self.cell.get_current(potential_full[i], time_full[i] + 0.001)

        # Forward/Reverse 샘플링 및 차동 전류 계산
        forward_indices = np.where(forward_mask)[0]
        reverse_indices = np.where(reverse_mask)[0]

        n_swv_points = min(len(forward_indices), len(reverse_indices))

        potential_v = np.zeros(n_swv_points)
        current_a = np.zeros(n_swv_points)

        step_v = params.step_potential_mv / 1000.0

        for i in range(n_swv_points):
            fwd_idx = forward_indices[i]
            rev_idx = reverse_indices[i]

            # 베이스 전위
            potential_v[i] = params.start_potential_v + i * step_v

            # 차동 전류 (forward - reverse)
            diff_current = current_full[fwd_idx] - current_full[rev_idx]
            current_a[i] = diff_current

        time_s = np.arange(n_swv_points) / params.frequency_hz

        result = MeasurementResult(
            mode=MeasurementMode.SWV,
            timestamp=datetime.now(),
            sample_id=f"SWV_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            time_s=time_s,
            potential_v=potential_v,
            current_a=current_a,
            channel_id=channel_id,
            parameters=vars(params)
        )

        self.measurement_history.append(result)
        self.is_measuring = False

        return result

    def measure_eis(self,
                    params: EISParameters = None,
                    channel_id: int = 0) -> EISResult:
        """
        EIS (Electrochemical Impedance Spectroscopy) 측정

        임피던스 스펙트럼 측정 (옵션)
        """
        if params is None:
            params = EISParameters()

        self.is_measuring = True
        self.current_mode = MeasurementMode.EIS

        # 주파수 포인트 생성 (로그 스케일)
        num_decades = np.log10(params.start_frequency_hz / params.end_frequency_hz)
        num_points = int(num_decades * params.points_per_decade)

        frequency_hz = np.logspace(
            np.log10(params.start_frequency_hz),
            np.log10(params.end_frequency_hz),
            num_points
        )

        # 임피던스 측정
        z_real_ohm = np.zeros(num_points)
        z_imag_ohm = np.zeros(num_points)

        for i, freq in enumerate(frequency_hz):
            Z = self.cell.get_impedance(freq)

            # 노이즈 추가
            noise_real = np.random.normal(0, abs(Z.real) * 0.01)
            noise_imag = np.random.normal(0, abs(Z.imag) * 0.01)

            z_real_ohm[i] = Z.real + noise_real
            z_imag_ohm[i] = Z.imag + noise_imag

        # 크기 및 위상
        magnitude_ohm = np.sqrt(z_real_ohm**2 + z_imag_ohm**2)
        phase_deg = np.degrees(np.arctan2(z_imag_ohm, z_real_ohm))

        # 시간/전위/전류는 EIS에서는 의미가 다름
        time_s = np.arange(num_points) * 0.1  # 가상 시간
        potential_v = np.ones(num_points) * params.dc_potential_v
        current_a = np.zeros(num_points)  # EIS에서는 AC 진폭으로 대체

        result = EISResult(
            mode=MeasurementMode.EIS,
            timestamp=datetime.now(),
            sample_id=f"EIS_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            time_s=time_s,
            potential_v=potential_v,
            current_a=current_a,
            channel_id=channel_id,
            parameters=vars(params),
            frequency_hz=frequency_hz,
            z_real_ohm=z_real_ohm,
            z_imag_ohm=z_imag_ohm,
            phase_deg=phase_deg,
            magnitude_ohm=magnitude_ohm
        )

        self.measurement_history.append(result)
        self.is_measuring = False

        return result

    def get_measurement_history(self,
                               mode: MeasurementMode = None,
                               limit: int = 10) -> List[MeasurementResult]:
        """측정 이력 조회"""
        history = self.measurement_history

        if mode is not None:
            history = [r for r in history if r.mode == mode]

        return history[-limit:]

    def clear_history(self) -> None:
        """이력 초기화"""
        self.measurement_history.clear()


# 편의 함수
def create_electrochemistry_engine(engine_id: str = "DEFAULT") -> ElectrochemistryEngine:
    """전기화학 엔진 생성 헬퍼"""
    return ElectrochemistryEngine(engine_id=engine_id)


def quick_cv_scan(start_v: float = -0.5,
                  end_v: float = 0.5,
                  scan_rate: float = 50.0) -> MeasurementResult:
    """빠른 CV 스캔"""
    engine = ElectrochemistryEngine()
    params = CVParameters(
        start_potential_v=start_v,
        vertex1_potential_v=end_v,
        vertex2_potential_v=start_v,
        final_potential_v=start_v,
        scan_rate_mv_s=scan_rate
    )
    return engine.measure_cv(params)


__all__ = [
    # Enums
    'MeasurementMode',
    'ScanDirection',
    'WaveformType',
    # Parameter Classes
    'OCPParameters',
    'CAParameters',
    'CVParameters',
    'DPVParameters',
    'SWVParameters',
    'EISParameters',
    # Result Classes
    'MeasurementResult',
    'EISResult',
    # Core Classes
    'WaveformGenerator',
    'ElectrochemicalCell',
    'ElectrochemistryEngine',
    # Functions
    'create_electrochemistry_engine',
    'quick_cv_scan',
]
