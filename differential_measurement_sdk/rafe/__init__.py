"""
RAFE - 재구성 가능 아날로그 프론트엔드 (Reconfigurable Analog Front-End)

프로그래머블 아날로그 신호 처리 체인

주요 기능:
- 동적 입력 범위 선택
- 프로그래머블 이득 증폭기 (PGA)
- 재구성 가능 필터
- 안티앨리어싱 필터
- 다채널 멀티플렉서
- ADC 제어
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime
import numpy as np


class InputRange(Enum):
    """입력 범위"""
    RANGE_10MV = "±10mV"
    RANGE_100MV = "±100mV"
    RANGE_1V = "±1V"
    RANGE_10V = "±10V"


class GainSetting(Enum):
    """이득 설정"""
    GAIN_1X = 1
    GAIN_2X = 2
    GAIN_4X = 4
    GAIN_8X = 8
    GAIN_16X = 16
    GAIN_32X = 32
    GAIN_64X = 64
    GAIN_128X = 128


class FilterType(Enum):
    """필터 유형"""
    BYPASS = "bypass"
    LOWPASS = "lowpass"
    HIGHPASS = "highpass"
    BANDPASS = "bandpass"
    NOTCH = "notch"


class ADCResolution(Enum):
    """ADC 해상도"""
    BITS_12 = 12
    BITS_14 = 14
    BITS_16 = 16
    BITS_18 = 18
    BITS_20 = 20
    BITS_24 = 24


class ADCMode(Enum):
    """ADC 동작 모드"""
    SINGLE_ENDED = "single_ended"
    DIFFERENTIAL = "differential"
    PSEUDO_DIFFERENTIAL = "pseudo_differential"


class MuxChannel(Enum):
    """멀티플렉서 채널"""
    CH0 = 0
    CH1 = 1
    CH2 = 2
    CH3 = 3
    CH4 = 4
    CH5 = 5
    CH6 = 6
    CH7 = 7
    INTERNAL_REF = 100
    GND = 101


@dataclass
class InputMultiplexer:
    """
    입력 멀티플렉서

    다중 입력 채널 선택 및 라우팅
    """
    mux_id: str
    num_channels: int = 8

    # 현재 선택된 채널
    selected_positive: MuxChannel = MuxChannel.CH0
    selected_negative: MuxChannel = MuxChannel.GND

    # 채널별 임피던스 (Ω)
    channel_impedances: Dict[int, float] = field(default_factory=lambda: {
        i: 1e6 for i in range(8)  # 1 MΩ 기본 입력 임피던스
    })

    # 상태
    is_enabled: bool = True

    def select_channel(self,
                       positive: MuxChannel,
                       negative: MuxChannel = MuxChannel.GND) -> None:
        """채널 선택"""
        self.selected_positive = positive
        self.selected_negative = negative

    def select_differential_pair(self, channel_pair: int) -> None:
        """차동 채널 쌍 선택 (0-3)"""
        if 0 <= channel_pair <= 3:
            self.selected_positive = MuxChannel(channel_pair * 2)
            self.selected_negative = MuxChannel(channel_pair * 2 + 1)

    def get_on_resistance(self) -> float:
        """온저항 반환 (Ω)"""
        return 100.0  # 100Ω 전형적 값

    def get_crosstalk_db(self) -> float:
        """채널간 누화 (dB)"""
        return -80.0  # -80 dB 전형적 값


@dataclass
class ProgrammableGainAmplifier:
    """
    프로그래머블 이득 증폭기 (PGA)

    소프트웨어 제어 가능한 이득 설정
    """
    pga_id: str

    # 이득 설정
    gain: GainSetting = GainSetting.GAIN_1X
    fine_gain_adjust: float = 1.0  # 미세 이득 조정 (0.9 - 1.1)

    # 성능 특성
    bandwidth_hz: float = 1e6  # 대역폭
    input_noise_nv_sqrt_hz: float = 10.0  # 입력 노이즈 밀도
    cmrr_db: float = 100.0  # 동상모드제거비
    input_offset_uv: float = 10.0  # 입력 오프셋

    # 입력 범위
    input_range: InputRange = InputRange.RANGE_10V
    output_swing_v: float = 4.5  # ±4.5V 출력 스윙

    def set_gain(self, gain: GainSetting) -> None:
        """이득 설정"""
        self.gain = gain

    def get_effective_gain(self) -> float:
        """실효 이득 반환"""
        return self.gain.value * self.fine_gain_adjust

    def amplify(self, input_signal: np.ndarray) -> np.ndarray:
        """
        신호 증폭

        Args:
            input_signal: 입력 신호

        Returns:
            증폭된 신호
        """
        gain = self.get_effective_gain()

        # 증폭
        output = input_signal * gain

        # 오프셋 추가
        output += self.input_offset_uv * 1e-6 * gain

        # 노이즈 추가 (시뮬레이션)
        noise_rms = self.input_noise_nv_sqrt_hz * 1e-9 * np.sqrt(self.bandwidth_hz)
        noise = np.random.normal(0, noise_rms * gain, len(output))
        output += noise

        # 출력 클리핑
        output = np.clip(output, -self.output_swing_v, self.output_swing_v)

        return output

    def auto_range(self, signal_peak: float) -> GainSetting:
        """
        자동 범위 설정

        Args:
            signal_peak: 신호 피크값

        Returns:
            최적 이득 설정
        """
        # 출력의 80%를 목표로 함
        target_output = self.output_swing_v * 0.8
        required_gain = target_output / (signal_peak + 1e-10)

        # 가장 가까운 이득 설정 찾기
        gains = list(GainSetting)
        for gain in reversed(gains):
            if gain.value <= required_gain:
                self.gain = gain
                return gain

        self.gain = GainSetting.GAIN_1X
        return GainSetting.GAIN_1X


@dataclass
class ConfigurableFilter:
    """
    재구성 가능 필터

    다양한 필터 특성을 소프트웨어로 설정
    """
    filter_id: str

    # 필터 설정
    filter_type: FilterType = FilterType.LOWPASS
    cutoff_freq_hz: float = 1000.0
    cutoff_freq_high_hz: float = 10000.0  # 밴드패스/노치용
    order: int = 4

    # 필터 계수 (IIR)
    b_coeffs: Optional[np.ndarray] = None
    a_coeffs: Optional[np.ndarray] = None

    # 상태
    filter_state: Optional[np.ndarray] = None

    def configure(self,
                  filter_type: FilterType,
                  cutoff_hz: float,
                  cutoff_high_hz: Optional[float] = None,
                  order: int = 4) -> None:
        """
        필터 구성

        Args:
            filter_type: 필터 유형
            cutoff_hz: 컷오프 주파수
            cutoff_high_hz: 상위 컷오프 (밴드패스/노치)
            order: 필터 차수
        """
        self.filter_type = filter_type
        self.cutoff_freq_hz = cutoff_hz
        self.cutoff_freq_high_hz = cutoff_high_hz or cutoff_hz * 10
        self.order = order

        # 필터 계수 계산 (버터워스 근사)
        self._compute_coefficients()

    def _compute_coefficients(self) -> None:
        """필터 계수 계산"""
        # 간단한 1차 IIR 필터 계수 (실제로는 scipy.signal 사용 권장)
        if self.filter_type == FilterType.BYPASS:
            self.b_coeffs = np.array([1.0])
            self.a_coeffs = np.array([1.0])
        else:
            # 단순화된 1차 저역통과 근사
            alpha = self.cutoff_freq_hz / (self.cutoff_freq_hz + 10000)
            self.b_coeffs = np.array([alpha])
            self.a_coeffs = np.array([1.0, -(1 - alpha)])

    def apply(self,
              signal: np.ndarray,
              sample_rate: float) -> np.ndarray:
        """
        필터 적용

        Args:
            signal: 입력 신호
            sample_rate: 샘플링 레이트

        Returns:
            필터링된 신호
        """
        if self.filter_type == FilterType.BYPASS:
            return signal

        if self.b_coeffs is None or self.a_coeffs is None:
            self._compute_coefficients()

        # 간단한 IIR 필터 적용
        filtered = np.zeros_like(signal)
        y_prev = 0.0

        for i, x in enumerate(signal):
            # y[n] = b[0]*x[n] - a[1]*y[n-1]
            y = self.b_coeffs[0] * x
            if len(self.a_coeffs) > 1:
                y -= self.a_coeffs[1] * y_prev
            filtered[i] = y
            y_prev = y

        return filtered

    def reset(self) -> None:
        """필터 상태 리셋"""
        self.filter_state = None


@dataclass
class AntiAliasingFilter:
    """
    안티앨리어싱 필터

    ADC 전단의 필수 저역통과 필터
    """
    filter_id: str

    # 설정
    cutoff_multiplier: float = 0.45  # 샘플레이트의 45%
    current_cutoff_hz: float = 0.0

    # 구현 방식
    is_active: bool = True  # True: 능동 필터, False: 수동 필터
    order: int = 4  # 필터 차수

    def set_for_sample_rate(self, sample_rate_hz: float) -> None:
        """샘플레이트에 맞게 설정"""
        self.current_cutoff_hz = sample_rate_hz * self.cutoff_multiplier

    def get_attenuation_at_nyquist(self) -> float:
        """나이퀴스트 주파수에서의 감쇠 (dB)"""
        # 버터워스 필터 근사
        # Attenuation = 20 * n * log10(f/fc) at f >> fc
        return -20 * self.order * np.log10(2)  # 나이퀴스트는 컷오프의 약 2.2배


@dataclass
class ADCController:
    """
    ADC 제어기

    아날로그-디지털 변환기 설정 및 제어
    """
    adc_id: str

    # ADC 사양
    resolution: ADCResolution = ADCResolution.BITS_16
    mode: ADCMode = ADCMode.DIFFERENTIAL
    reference_voltage: float = 2.5  # V

    # 샘플링 설정
    sample_rate_hz: float = 10000.0
    oversampling_ratio: int = 1

    # 성능 특성
    effective_bits: float = 15.5  # ENOB
    dnl_lsb: float = 0.5  # DNL
    inl_lsb: float = 1.0  # INL

    # 상태
    is_running: bool = False

    def configure(self,
                  resolution: ADCResolution,
                  sample_rate: float,
                  mode: ADCMode = ADCMode.DIFFERENTIAL) -> None:
        """ADC 구성"""
        self.resolution = resolution
        self.sample_rate_hz = sample_rate
        self.mode = mode

        # ENOB 계산 (이상적 값에서 노이즈로 인한 감소)
        ideal_bits = resolution.value
        self.effective_bits = ideal_bits - 0.5 - np.log2(self.oversampling_ratio)

    def get_lsb_voltage(self) -> float:
        """LSB 전압 반환"""
        full_scale = 2 * self.reference_voltage  # 차동
        return full_scale / (2 ** self.resolution.value)

    def convert(self, analog_voltage: float) -> int:
        """
        아날로그-디지털 변환

        Args:
            analog_voltage: 아날로그 입력 전압

        Returns:
            디지털 코드
        """
        lsb = self.get_lsb_voltage()
        max_code = 2 ** (self.resolution.value - 1) - 1

        # 양자화
        code = int(analog_voltage / lsb)

        # 노이즈 추가 (시뮬레이션)
        noise_lsb = 2 ** (self.resolution.value - self.effective_bits)
        code += int(np.random.normal(0, noise_lsb))

        # 클리핑
        code = max(-max_code - 1, min(max_code, code))

        return code

    def convert_array(self, analog_signal: np.ndarray) -> np.ndarray:
        """배열 변환"""
        return np.array([self.convert(v) for v in analog_signal])

    def to_voltage(self, digital_code: int) -> float:
        """디지털 코드를 전압으로 변환"""
        lsb = self.get_lsb_voltage()
        return digital_code * lsb

    def start(self) -> None:
        """ADC 시작"""
        self.is_running = True

    def stop(self) -> None:
        """ADC 중지"""
        self.is_running = False


@dataclass
class RAFEConfiguration:
    """RAFE 전체 구성"""
    config_id: str
    name: str = "Default"

    # 컴포넌트 설정
    mux_positive: MuxChannel = MuxChannel.CH0
    mux_negative: MuxChannel = MuxChannel.GND
    gain: GainSetting = GainSetting.GAIN_1X
    filter_type: FilterType = FilterType.LOWPASS
    filter_cutoff_hz: float = 1000.0
    adc_resolution: ADCResolution = ADCResolution.BITS_16
    sample_rate_hz: float = 10000.0

    # 메타데이터
    created_at: datetime = field(default_factory=datetime.now)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'config_id': self.config_id,
            'name': self.name,
            'mux_positive': self.mux_positive.value,
            'mux_negative': self.mux_negative.value,
            'gain': self.gain.value,
            'filter_type': self.filter_type.value,
            'filter_cutoff_hz': self.filter_cutoff_hz,
            'adc_resolution': self.adc_resolution.value,
            'sample_rate_hz': self.sample_rate_hz,
            'description': self.description
        }


class RAFE:
    """
    재구성 가능 아날로그 프론트엔드 (RAFE)

    완전한 아날로그 신호 처리 체인
    """

    def __init__(self, rafe_id: str = "RAFE_001"):
        """
        Args:
            rafe_id: RAFE 식별자
        """
        self.rafe_id = rafe_id

        # 컴포넌트 초기화
        self.mux = InputMultiplexer(mux_id=f"{rafe_id}_MUX")
        self.pga = ProgrammableGainAmplifier(pga_id=f"{rafe_id}_PGA")
        self.filter = ConfigurableFilter(filter_id=f"{rafe_id}_FILT")
        self.aa_filter = AntiAliasingFilter(filter_id=f"{rafe_id}_AA")
        self.adc = ADCController(adc_id=f"{rafe_id}_ADC")

        # 현재 구성
        self.current_config: Optional[RAFEConfiguration] = None

        # 프리셋 구성
        self.preset_configs: Dict[str, RAFEConfiguration] = {}
        self._create_default_presets()

        # 측정 이력
        self.measurement_count: int = 0

    def _create_default_presets(self) -> None:
        """기본 프리셋 생성"""
        # 고정밀 DC 측정
        self.preset_configs['precision_dc'] = RAFEConfiguration(
            config_id='precision_dc',
            name='고정밀 DC 측정',
            gain=GainSetting.GAIN_128X,
            filter_type=FilterType.LOWPASS,
            filter_cutoff_hz=10.0,
            adc_resolution=ADCResolution.BITS_24,
            sample_rate_hz=100.0,
            description='저속 고정밀 DC 전압 측정'
        )

        # 고속 AC 측정
        self.preset_configs['fast_ac'] = RAFEConfiguration(
            config_id='fast_ac',
            name='고속 AC 측정',
            gain=GainSetting.GAIN_1X,
            filter_type=FilterType.BANDPASS,
            filter_cutoff_hz=10000.0,
            adc_resolution=ADCResolution.BITS_12,
            sample_rate_hz=1000000.0,
            description='고속 AC 신호 측정'
        )

        # 저노이즈 미세신호
        self.preset_configs['low_noise'] = RAFEConfiguration(
            config_id='low_noise',
            name='저노이즈 미세신호',
            gain=GainSetting.GAIN_64X,
            filter_type=FilterType.LOWPASS,
            filter_cutoff_hz=100.0,
            adc_resolution=ADCResolution.BITS_20,
            sample_rate_hz=1000.0,
            description='저노이즈 미세 전압 측정'
        )

        # 범용 측정
        self.preset_configs['general'] = RAFEConfiguration(
            config_id='general',
            name='범용 측정',
            gain=GainSetting.GAIN_1X,
            filter_type=FilterType.LOWPASS,
            filter_cutoff_hz=1000.0,
            adc_resolution=ADCResolution.BITS_16,
            sample_rate_hz=10000.0,
            description='일반적인 측정 용도'
        )

    def apply_configuration(self, config: RAFEConfiguration) -> None:
        """구성 적용"""
        # 멀티플렉서 설정
        self.mux.select_channel(config.mux_positive, config.mux_negative)

        # PGA 설정
        self.pga.set_gain(config.gain)

        # 필터 설정
        self.filter.configure(
            config.filter_type,
            config.filter_cutoff_hz
        )

        # 안티앨리어싱 필터 설정
        self.aa_filter.set_for_sample_rate(config.sample_rate_hz)

        # ADC 설정
        self.adc.configure(
            config.adc_resolution,
            config.sample_rate_hz
        )

        self.current_config = config

    def load_preset(self, preset_name: str) -> bool:
        """프리셋 로드"""
        if preset_name in self.preset_configs:
            self.apply_configuration(self.preset_configs[preset_name])
            return True
        return False

    def save_preset(self, name: str, config: RAFEConfiguration) -> None:
        """프리셋 저장"""
        self.preset_configs[name] = config

    def process_signal(self,
                       input_signal: np.ndarray,
                       sample_rate: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        신호 처리 파이프라인

        Args:
            input_signal: 입력 신호 (전압)
            sample_rate: 입력 샘플링 레이트

        Returns:
            (아날로그 출력, 디지털 출력) 튜플
        """
        # 1. PGA 증폭
        amplified = self.pga.amplify(input_signal)

        # 2. 구성 가능 필터 적용
        filtered = self.filter.apply(amplified, sample_rate)

        # 3. 안티앨리어싱 필터 (시뮬레이션에서는 생략)
        analog_output = filtered

        # 4. ADC 변환
        digital_output = self.adc.convert_array(analog_output)

        self.measurement_count += 1

        return (analog_output, digital_output)

    def auto_configure(self, sample_signal: np.ndarray) -> RAFEConfiguration:
        """
        신호 기반 자동 구성

        Args:
            sample_signal: 샘플 신호

        Returns:
            최적 구성
        """
        # 신호 특성 분석
        signal_peak = np.max(np.abs(sample_signal))
        signal_rms = np.sqrt(np.mean(sample_signal ** 2))

        # 주파수 특성 분석 (간단한 제로크로싱 기반)
        zero_crossings = np.sum(np.diff(np.sign(sample_signal)) != 0)
        estimated_freq = zero_crossings / (2 * len(sample_signal) / 10000)  # 10kHz 가정

        # 최적 이득 선택
        optimal_gain = self.pga.auto_range(signal_peak)

        # 필터 컷오프 선택
        if estimated_freq < 10:
            filter_cutoff = 100.0
            filter_type = FilterType.LOWPASS
        elif estimated_freq < 1000:
            filter_cutoff = estimated_freq * 10
            filter_type = FilterType.LOWPASS
        else:
            filter_cutoff = estimated_freq * 2
            filter_type = FilterType.BANDPASS

        # ADC 해상도 선택
        dynamic_range_db = 20 * np.log10(signal_peak / (signal_rms / 1000 + 1e-10))
        if dynamic_range_db > 100:
            adc_resolution = ADCResolution.BITS_24
        elif dynamic_range_db > 80:
            adc_resolution = ADCResolution.BITS_20
        elif dynamic_range_db > 60:
            adc_resolution = ADCResolution.BITS_16
        else:
            adc_resolution = ADCResolution.BITS_12

        config = RAFEConfiguration(
            config_id='auto_' + datetime.now().strftime('%Y%m%d%H%M%S'),
            name='자동 구성',
            gain=optimal_gain,
            filter_type=filter_type,
            filter_cutoff_hz=filter_cutoff,
            adc_resolution=adc_resolution,
            sample_rate_hz=max(1000.0, estimated_freq * 10),
            description=f'자동 구성 (피크: {signal_peak:.3f}V, 추정 주파수: {estimated_freq:.1f}Hz)'
        )

        self.apply_configuration(config)
        return config

    def get_status(self) -> Dict[str, Any]:
        """상태 정보 반환"""
        return {
            'rafe_id': self.rafe_id,
            'current_config': self.current_config.to_dict() if self.current_config else None,
            'mux': {
                'positive': self.mux.selected_positive.name,
                'negative': self.mux.selected_negative.name,
                'enabled': self.mux.is_enabled
            },
            'pga': {
                'gain': self.pga.gain.value,
                'effective_gain': self.pga.get_effective_gain(),
                'bandwidth_hz': self.pga.bandwidth_hz
            },
            'filter': {
                'type': self.filter.filter_type.value,
                'cutoff_hz': self.filter.cutoff_freq_hz
            },
            'adc': {
                'resolution': self.adc.resolution.value,
                'sample_rate_hz': self.adc.sample_rate_hz,
                'effective_bits': self.adc.effective_bits,
                'is_running': self.adc.is_running
            },
            'measurement_count': self.measurement_count
        }

    def get_noise_floor(self) -> float:
        """노이즈 플로어 추정 (V rms)"""
        # PGA 노이즈
        pga_noise = self.pga.input_noise_nv_sqrt_hz * 1e-9 * np.sqrt(self.pga.bandwidth_hz)

        # ADC 양자화 노이즈
        adc_lsb = self.adc.get_lsb_voltage()
        adc_noise = adc_lsb / np.sqrt(12)  # 균일 분포 양자화 노이즈

        # 총 노이즈 (RSS)
        total_noise = np.sqrt(pga_noise ** 2 + adc_noise ** 2)

        return total_noise

    def get_dynamic_range_db(self) -> float:
        """동적 범위 (dB)"""
        max_signal = self.pga.output_swing_v
        noise_floor = self.get_noise_floor()

        return 20 * np.log10(max_signal / (noise_floor + 1e-15))


class RAFEManager:
    """RAFE 관리자 - 다중 RAFE 관리"""

    def __init__(self):
        self.rafes: Dict[str, RAFE] = {}

    def create_rafe(self, rafe_id: str) -> RAFE:
        """새 RAFE 생성"""
        rafe = RAFE(rafe_id)
        self.rafes[rafe_id] = rafe
        return rafe

    def get_rafe(self, rafe_id: str) -> Optional[RAFE]:
        """RAFE 조회"""
        return self.rafes.get(rafe_id)

    def configure_all(self, config: RAFEConfiguration) -> None:
        """모든 RAFE에 동일 구성 적용"""
        for rafe in self.rafes.values():
            rafe.apply_configuration(config)

    def get_all_status(self) -> Dict[str, Dict]:
        """모든 RAFE 상태 반환"""
        return {
            rafe_id: rafe.get_status()
            for rafe_id, rafe in self.rafes.items()
        }


# 편의 함수
def create_rafe(rafe_id: str = "DEFAULT") -> RAFE:
    """RAFE 생성 헬퍼"""
    return RAFE(rafe_id=rafe_id)


def quick_measurement(signal: np.ndarray,
                      sample_rate: float = 10000.0) -> Tuple[np.ndarray, np.ndarray]:
    """빠른 측정"""
    rafe = RAFE()
    rafe.load_preset('general')
    return rafe.process_signal(signal, sample_rate)


__all__ = [
    # Enums
    'InputRange',
    'GainSetting',
    'FilterType',
    'ADCResolution',
    'ADCMode',
    'MuxChannel',
    # Classes
    'InputMultiplexer',
    'ProgrammableGainAmplifier',
    'ConfigurableFilter',
    'AntiAliasingFilter',
    'ADCController',
    'RAFEConfiguration',
    'RAFE',
    'RAFEManager',
    # Functions
    'create_rafe',
    'quick_measurement',
]
