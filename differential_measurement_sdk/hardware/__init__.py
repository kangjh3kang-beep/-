"""
하드웨어 제어 모듈 (Hardware Control Module)

ADC, AFE, 전원관리 등 하드웨어 인터페이스 (MPK-RDR-MFG-SPEC v2.2 섹션 3)

주요 기능:
- ADC 제어 (ADS1256 24-bit)
- AFE (Analog Front-End) 제어
- 전기화학 AFE (LMP91000)
- 전원 관리 (BQ24195)
- 스위치 매트릭스
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
import numpy as np


class ADCDataRate(Enum):
    """ADS1256 데이터 레이트"""
    SPS_2_5 = 2.5
    SPS_5 = 5
    SPS_10 = 10
    SPS_15 = 15
    SPS_25 = 25
    SPS_30 = 30
    SPS_50 = 50
    SPS_60 = 60
    SPS_100 = 100
    SPS_500 = 500
    SPS_1000 = 1000
    SPS_2000 = 2000
    SPS_3750 = 3750
    SPS_7500 = 7500
    SPS_15000 = 15000
    SPS_30000 = 30000


class ADCGain(Enum):
    """ADS1256 PGA 게인"""
    GAIN_1 = 1
    GAIN_2 = 2
    GAIN_4 = 4
    GAIN_8 = 8
    GAIN_16 = 16
    GAIN_32 = 32
    GAIN_64 = 64


class ADCChannel(Enum):
    """ADS1256 입력 채널"""
    AIN0 = 0
    AIN1 = 1
    AIN2 = 2
    AIN3 = 3
    AIN4 = 4
    AIN5 = 5
    AIN6 = 6
    AIN7 = 7
    AINCOM = 8


class ADCInputMode(Enum):
    """ADC 입력 모드"""
    SINGLE_ENDED = "single_ended"
    DIFFERENTIAL = "differential"


class TIAGain(Enum):
    """LMP91000 TIA 게인 (저항값)"""
    EXTERNAL = 0     # 외부 저항
    R_2K75 = 2750
    R_3K5 = 3500
    R_7K = 7000
    R_14K = 14000
    R_35K = 35000
    R_120K = 120000
    R_350K = 350000


class BiasPolarity(Enum):
    """바이어스 극성"""
    NEGATIVE = "negative"
    POSITIVE = "positive"


class BiasPercentage(Enum):
    """바이어스 전압 (내부 기준전압 대비 %)"""
    PERCENT_0 = 0
    PERCENT_1 = 1
    PERCENT_2 = 2
    PERCENT_4 = 4
    PERCENT_6 = 6
    PERCENT_8 = 8
    PERCENT_10 = 10
    PERCENT_12 = 12
    PERCENT_14 = 14
    PERCENT_16 = 16
    PERCENT_18 = 18
    PERCENT_20 = 20
    PERCENT_22 = 22
    PERCENT_24 = 24


class PowerSource(Enum):
    """전원 소스"""
    BATTERY = "battery"
    USB = "usb"
    ADAPTER = "adapter"


class ChargingState(Enum):
    """충전 상태"""
    NOT_CHARGING = "not_charging"
    PRE_CHARGE = "pre_charge"
    FAST_CHARGE = "fast_charge"
    CHARGE_DONE = "charge_done"
    FAULT = "fault"


@dataclass
class ADCSample:
    """ADC 샘플 데이터"""
    raw_code: int          # 원시 ADC 코드 (24-bit signed)
    voltage_v: float       # 변환된 전압
    timestamp_us: int      # 타임스탬프 (마이크로초)
    channel_pos: ADCChannel
    channel_neg: ADCChannel
    gain: ADCGain
    data_rate: ADCDataRate

    def __post_init__(self):
        # 24-bit signed to voltage conversion
        if self.voltage_v == 0.0 and self.raw_code != 0:
            vref = 2.5  # V
            self.voltage_v = (self.raw_code / (2**23 - 1)) * vref / self.gain.value


@dataclass
class ADS1256:
    """
    ADS1256 24-bit ADC 모델

    TI ADS1256: 24-bit delta-sigma ADC
    - 최대 30kSPS
    - 8채널 멀티플렉서
    - 프로그래머블 게인 (1~64)
    """
    device_id: str = "ADS1256_001"

    # 설정
    data_rate: ADCDataRate = ADCDataRate.SPS_1000
    gain: ADCGain = ADCGain.GAIN_1
    input_mode: ADCInputMode = ADCInputMode.DIFFERENTIAL

    # 입력 채널
    channel_positive: ADCChannel = ADCChannel.AIN0
    channel_negative: ADCChannel = ADCChannel.AIN1

    # 기준 전압
    vref_v: float = 2.5

    # 상태
    is_running: bool = False
    buffer_enabled: bool = True
    auto_calibration: bool = True

    # 캘리브레이션 레지스터
    offset_cal: int = 0
    full_scale_cal: int = 0x400000

    # 노이즈 특성 (데이터레이트별 RMS 노이즈, nV)
    NOISE_TABLE: Dict[ADCDataRate, float] = field(default_factory=lambda: {
        ADCDataRate.SPS_2_5: 30,
        ADCDataRate.SPS_5: 40,
        ADCDataRate.SPS_10: 55,
        ADCDataRate.SPS_15: 68,
        ADCDataRate.SPS_25: 90,
        ADCDataRate.SPS_30: 100,
        ADCDataRate.SPS_50: 130,
        ADCDataRate.SPS_60: 140,
        ADCDataRate.SPS_100: 180,
        ADCDataRate.SPS_500: 410,
        ADCDataRate.SPS_1000: 580,
        ADCDataRate.SPS_2000: 820,
        ADCDataRate.SPS_3750: 1100,
        ADCDataRate.SPS_7500: 1600,
        ADCDataRate.SPS_15000: 2300,
        ADCDataRate.SPS_30000: 3200,
    })

    def configure(self,
                  data_rate: ADCDataRate = None,
                  gain: ADCGain = None,
                  channel_pos: ADCChannel = None,
                  channel_neg: ADCChannel = None) -> None:
        """ADC 구성"""
        if data_rate is not None:
            self.data_rate = data_rate
        if gain is not None:
            self.gain = gain
        if channel_pos is not None:
            self.channel_positive = channel_pos
        if channel_neg is not None:
            self.channel_negative = channel_neg

    def get_lsb_voltage(self) -> float:
        """LSB 전압 (V)"""
        full_scale = 2 * self.vref_v / self.gain.value
        return full_scale / (2**24)

    def get_noise_free_bits(self) -> float:
        """노이즈 프리 비트"""
        noise_nv = self.NOISE_TABLE.get(self.data_rate, 1000) * self.gain.value
        lsb_nv = self.get_lsb_voltage() * 1e9
        noise_bits = np.log2(6.6 * noise_nv / lsb_nv)
        return 24 - noise_bits

    def get_effective_resolution(self) -> float:
        """유효 분해능 (ENOB)"""
        return self.get_noise_free_bits()

    def read_single(self, input_voltage: float = None) -> ADCSample:
        """
        단일 샘플 읽기

        Args:
            input_voltage: 시뮬레이션용 입력 전압 (None이면 랜덤)
        """
        if input_voltage is None:
            input_voltage = np.random.uniform(-self.vref_v, self.vref_v) / self.gain.value

        # 전압 → ADC 코드 변환
        scaled_voltage = input_voltage * self.gain.value
        ideal_code = int(scaled_voltage / self.vref_v * (2**23 - 1))

        # 노이즈 추가
        noise_nv = self.NOISE_TABLE.get(self.data_rate, 1000) * self.gain.value
        noise_v = noise_nv * 1e-9 * np.random.randn()
        noise_code = int(noise_v / self.vref_v * (2**23 - 1))

        raw_code = ideal_code + noise_code

        # 클리핑
        raw_code = max(-(2**23), min(2**23 - 1, raw_code))

        # 오프셋/풀스케일 캘리브레이션 적용
        raw_code = raw_code - self.offset_cal
        raw_code = int(raw_code * self.full_scale_cal / 0x400000)

        # 전압으로 재변환
        voltage = (raw_code / (2**23 - 1)) * self.vref_v / self.gain.value

        return ADCSample(
            raw_code=raw_code,
            voltage_v=voltage,
            timestamp_us=int(datetime.now().timestamp() * 1e6),
            channel_pos=self.channel_positive,
            channel_neg=self.channel_negative,
            gain=self.gain,
            data_rate=self.data_rate
        )

    def read_continuous(self,
                       num_samples: int,
                       input_signal: np.ndarray = None) -> List[ADCSample]:
        """
        연속 샘플 읽기

        Args:
            num_samples: 샘플 수
            input_signal: 시뮬레이션용 입력 신호
        """
        samples = []
        sample_period_us = int(1e6 / self.data_rate.value)

        for i in range(num_samples):
            if input_signal is not None and i < len(input_signal):
                voltage = input_signal[i]
            else:
                voltage = None

            sample = self.read_single(voltage)
            sample.timestamp_us = i * sample_period_us
            samples.append(sample)

        return samples

    def self_calibrate(self) -> bool:
        """자가 캘리브레이션"""
        # 오프셋 캘리브레이션 (입력 단락)
        self.offset_cal = 0  # 시뮬레이션에서는 리셋

        # 풀스케일 캘리브레이션
        self.full_scale_cal = 0x400000

        return True

    def get_status(self) -> Dict[str, Any]:
        """상태 정보"""
        return {
            'device_id': self.device_id,
            'data_rate_sps': self.data_rate.value,
            'gain': self.gain.value,
            'channel_pos': self.channel_positive.name,
            'channel_neg': self.channel_negative.name,
            'vref_v': self.vref_v,
            'effective_resolution_bits': self.get_effective_resolution(),
            'noise_free_bits': self.get_noise_free_bits(),
            'lsb_voltage_uv': self.get_lsb_voltage() * 1e6,
            'is_running': self.is_running
        }


@dataclass
class LMP91000:
    """
    LMP91000 전기화학 AFE 모델

    TI LMP91000: Configurable AFE for Low-Power Chemical Sensing
    - 프로그래머블 TIA (트랜스임피던스 증폭기)
    - 내부 기준전압 생성
    - 온도 센서
    """
    device_id: str = "LMP91000_001"

    # TIA 설정
    tia_gain: TIAGain = TIAGain.R_35K
    rload_ohm: float = 100.0  # 부하 저항

    # 기준전압 설정
    internal_zero_percent: int = 50  # 내부 제로 (% of supply)
    bias_polarity: BiasPolarity = BiasPolarity.NEGATIVE
    bias_percent: BiasPercentage = BiasPercentage.PERCENT_0

    # 전원
    supply_voltage_v: float = 3.3

    # 상태
    is_enabled: bool = False
    is_three_lead: bool = False  # 3전극 모드

    # 온도
    temperature_c: float = 25.0

    def get_tia_gain_ohm(self) -> float:
        """TIA 게인 저항값 (Ω)"""
        if self.tia_gain == TIAGain.EXTERNAL:
            return 10000.0  # 기본 외부 저항 가정
        return self.tia_gain.value

    def get_internal_zero_voltage(self) -> float:
        """내부 제로 전압 (V)"""
        return self.supply_voltage_v * self.internal_zero_percent / 100

    def get_bias_voltage(self) -> float:
        """바이어스 전압 (V)"""
        internal_zero = self.get_internal_zero_voltage()
        bias_v = internal_zero * self.bias_percent.value / 100

        if self.bias_polarity == BiasPolarity.NEGATIVE:
            return -bias_v
        return bias_v

    def current_to_voltage(self, current_a: float) -> float:
        """
        전류를 TIA 출력 전압으로 변환

        Vout = Vzero - I * Rtia
        """
        v_zero = self.get_internal_zero_voltage()
        v_out = v_zero - current_a * self.get_tia_gain_ohm()

        # 클리핑 (레일 제한)
        v_out = max(0, min(self.supply_voltage_v, v_out))

        return v_out

    def voltage_to_current(self, voltage_v: float) -> float:
        """
        TIA 출력 전압을 전류로 역변환

        I = (Vzero - Vout) / Rtia
        """
        v_zero = self.get_internal_zero_voltage()
        current = (v_zero - voltage_v) / self.get_tia_gain_ohm()

        return current

    def get_current_range(self) -> Tuple[float, float]:
        """측정 가능 전류 범위 (A)"""
        rtia = self.get_tia_gain_ohm()
        v_zero = self.get_internal_zero_voltage()

        # 최대: Vzero까지 스윙 가능
        i_max = v_zero / rtia

        # 최소: (VCC - Vzero) / Rtia
        i_min = -(self.supply_voltage_v - v_zero) / rtia

        return (i_min, i_max)

    def get_temperature(self) -> float:
        """내부 온도 센서 읽기"""
        # 시뮬레이션: 노이즈 추가
        return self.temperature_c + np.random.normal(0, 0.5)

    def configure(self,
                 tia_gain: TIAGain = None,
                 bias_percent: BiasPercentage = None,
                 bias_polarity: BiasPolarity = None) -> None:
        """AFE 구성"""
        if tia_gain is not None:
            self.tia_gain = tia_gain
        if bias_percent is not None:
            self.bias_percent = bias_percent
        if bias_polarity is not None:
            self.bias_polarity = bias_polarity

    def enable(self) -> None:
        """AFE 활성화"""
        self.is_enabled = True

    def disable(self) -> None:
        """AFE 비활성화 (저전력 모드)"""
        self.is_enabled = False

    def get_status(self) -> Dict[str, Any]:
        """상태 정보"""
        i_range = self.get_current_range()
        return {
            'device_id': self.device_id,
            'is_enabled': self.is_enabled,
            'tia_gain_ohm': self.get_tia_gain_ohm(),
            'internal_zero_v': self.get_internal_zero_voltage(),
            'bias_voltage_v': self.get_bias_voltage(),
            'current_range_ua': (i_range[0] * 1e6, i_range[1] * 1e6),
            'temperature_c': self.get_temperature()
        }


@dataclass
class SwitchMatrix:
    """
    스위치 매트릭스

    채널 선택 및 신호 라우팅을 위한 아날로그 스위치
    """
    matrix_id: str = "SWITCH_001"

    # 채널 수
    num_inputs: int = 8
    num_outputs: int = 4

    # 연결 상태 (input -> output 매핑)
    connections: Dict[int, int] = field(default_factory=dict)

    # 스위치 특성
    on_resistance_ohm: float = 10.0
    off_leakage_na: float = 1.0
    charge_injection_pc: float = 5.0

    # 상태
    is_enabled: bool = True

    def connect(self, input_ch: int, output_ch: int) -> bool:
        """입력을 출력에 연결"""
        if input_ch >= self.num_inputs or output_ch >= self.num_outputs:
            return False

        # 기존 연결 해제
        self.disconnect_output(output_ch)

        self.connections[input_ch] = output_ch
        return True

    def disconnect_input(self, input_ch: int) -> None:
        """입력 연결 해제"""
        if input_ch in self.connections:
            del self.connections[input_ch]

    def disconnect_output(self, output_ch: int) -> None:
        """출력에서 모든 연결 해제"""
        to_remove = [inp for inp, out in self.connections.items() if out == output_ch]
        for inp in to_remove:
            del self.connections[inp]

    def disconnect_all(self) -> None:
        """모든 연결 해제"""
        self.connections.clear()

    def get_connected_input(self, output_ch: int) -> Optional[int]:
        """출력에 연결된 입력 채널"""
        for inp, out in self.connections.items():
            if out == output_ch:
                return inp
        return None

    def route_signal(self, signal: float, input_ch: int) -> Optional[Tuple[int, float]]:
        """신호 라우팅 (입력 → 출력)"""
        if not self.is_enabled:
            return None

        if input_ch not in self.connections:
            return None

        output_ch = self.connections[input_ch]

        # 온저항으로 인한 전압 강하 (부하 의존, 여기서는 무시)
        routed_signal = signal

        # 누설 전류 노이즈
        leakage = self.off_leakage_na * 1e-9 * np.random.randn()
        routed_signal += leakage

        return (output_ch, routed_signal)


@dataclass
class BQ24195:
    """
    BQ24195 전원관리 IC 모델

    TI BQ24195: I2C Controlled 2.5A Single Cell USB/Adapter Charger
    - 1셀 Li-ion 충전
    - USB/어댑터 입력
    - 동적 전원 경로 관리
    """
    device_id: str = "BQ24195_001"

    # 배터리 상태
    battery_voltage_v: float = 3.7
    battery_capacity_mah: float = 2000.0
    battery_soc_percent: float = 50.0  # State of Charge

    # 충전 설정
    charge_voltage_limit_v: float = 4.2
    charge_current_limit_ma: float = 500.0
    precharge_current_ma: float = 128.0
    termination_current_ma: float = 128.0

    # 입력 설정
    input_voltage_limit_v: float = 4.36
    input_current_limit_ma: float = 500.0

    # 상태
    power_source: PowerSource = PowerSource.BATTERY
    charging_state: ChargingState = ChargingState.NOT_CHARGING
    is_power_good: bool = False

    # 보호
    thermal_shutdown_c: float = 120.0
    die_temperature_c: float = 35.0

    # 시스템 출력
    sys_voltage_v: float = 3.7

    def connect_usb(self, voltage_v: float = 5.0, current_ma: float = 500.0) -> None:
        """USB 연결"""
        if voltage_v >= self.input_voltage_limit_v:
            self.power_source = PowerSource.USB
            self.is_power_good = True
            self.input_current_limit_ma = min(current_ma, 2400)  # 최대 2.4A
            self._update_charging_state()

    def disconnect_usb(self) -> None:
        """USB 분리"""
        if self.power_source == PowerSource.USB:
            self.power_source = PowerSource.BATTERY
            self.is_power_good = False
            self.charging_state = ChargingState.NOT_CHARGING

    def _update_charging_state(self) -> None:
        """충전 상태 업데이트"""
        if not self.is_power_good:
            self.charging_state = ChargingState.NOT_CHARGING
            return

        if self.battery_soc_percent >= 100:
            self.charging_state = ChargingState.CHARGE_DONE
        elif self.battery_voltage_v < 3.0:
            self.charging_state = ChargingState.PRE_CHARGE
        else:
            self.charging_state = ChargingState.FAST_CHARGE

    def get_system_voltage(self) -> float:
        """시스템 전압 (VSYS)"""
        if self.is_power_good:
            # USB 연결 시: MIN(VBAT, VBUS) + 보충
            self.sys_voltage_v = max(self.battery_voltage_v, 3.5)
        else:
            # 배터리 전용
            self.sys_voltage_v = self.battery_voltage_v

        return self.sys_voltage_v

    def get_charging_current(self) -> float:
        """현재 충전 전류 (mA)"""
        if self.charging_state == ChargingState.NOT_CHARGING:
            return 0.0
        elif self.charging_state == ChargingState.PRE_CHARGE:
            return self.precharge_current_ma
        elif self.charging_state == ChargingState.FAST_CHARGE:
            return self.charge_current_limit_ma
        elif self.charging_state == ChargingState.CHARGE_DONE:
            return self.termination_current_ma
        return 0.0

    def simulate_charge_step(self, time_step_s: float = 1.0) -> None:
        """충전 시뮬레이션 스텝"""
        current_ma = self.get_charging_current()

        if current_ma > 0:
            # 충전량 계산
            charge_mah = current_ma * time_step_s / 3600
            soc_increase = charge_mah / self.battery_capacity_mah * 100

            self.battery_soc_percent += soc_increase
            self.battery_soc_percent = min(100.0, self.battery_soc_percent)

            # 전압 업데이트 (간단한 선형 모델)
            self.battery_voltage_v = 3.0 + (self.battery_soc_percent / 100) * 1.2

            self._update_charging_state()

    def get_status(self) -> Dict[str, Any]:
        """상태 정보"""
        return {
            'device_id': self.device_id,
            'power_source': self.power_source.value,
            'charging_state': self.charging_state.value,
            'is_power_good': self.is_power_good,
            'battery_voltage_v': self.battery_voltage_v,
            'battery_soc_percent': self.battery_soc_percent,
            'system_voltage_v': self.get_system_voltage(),
            'charging_current_ma': self.get_charging_current(),
            'die_temperature_c': self.die_temperature_c
        }


class HardwareManager:
    """
    하드웨어 관리자

    모든 하드웨어 컴포넌트 통합 관리
    """

    def __init__(self, manager_id: str = "HW_MGR_001"):
        """
        Args:
            manager_id: 관리자 식별자
        """
        self.manager_id = manager_id

        # 컴포넌트 초기화
        self.adc = ADS1256(device_id=f"{manager_id}_ADC")
        self.afe = LMP91000(device_id=f"{manager_id}_AFE")
        self.switch_matrix = SwitchMatrix(matrix_id=f"{manager_id}_SW")
        self.power_mgr = BQ24195(device_id=f"{manager_id}_PWR")

        # 듀얼 ADC 옵션 (동시 샘플링)
        self.adc_secondary: Optional[ADS1256] = None
        self.dual_adc_enabled = False

        # 보드 온도
        self.board_temperature_c = 25.0

    def enable_dual_adc(self) -> None:
        """듀얼 ADC 모드 활성화 (완전 동시 샘플링)"""
        self.adc_secondary = ADS1256(device_id=f"{self.manager_id}_ADC2")
        self.dual_adc_enabled = True

    def configure_measurement_chain(self,
                                   channel: int,
                                   tia_gain: TIAGain = TIAGain.R_35K,
                                   adc_gain: ADCGain = ADCGain.GAIN_1,
                                   adc_rate: ADCDataRate = ADCDataRate.SPS_1000) -> None:
        """
        측정 체인 구성

        Args:
            channel: E12 센서 채널 (1-4)
            tia_gain: TIA 게인
            adc_gain: ADC PGA 게인
            adc_rate: ADC 데이터 레이트
        """
        # 스위치 매트릭스 설정
        # 채널 1-4를 ADC 입력에 매핑
        we_input = (channel - 1) * 2      # WE: 0, 2, 4, 6
        re_input = (channel - 1) * 2 + 1  # RE: 1, 3, 5, 7

        self.switch_matrix.connect(we_input, 0)  # WE → ADC 채널 0
        self.switch_matrix.connect(re_input, 1)  # RE → ADC 채널 1

        # AFE 설정
        self.afe.configure(tia_gain=tia_gain)
        self.afe.enable()

        # ADC 설정 (차동 모드)
        self.adc.configure(
            data_rate=adc_rate,
            gain=adc_gain,
            channel_pos=ADCChannel.AIN0,
            channel_neg=ADCChannel.AIN1
        )

    def acquire_single_sample(self,
                             input_current_a: float = None) -> Dict[str, Any]:
        """
        단일 샘플 획득

        전체 측정 체인을 통한 샘플 획득
        """
        # AFE를 통한 전류 → 전압 변환
        if input_current_a is not None:
            afe_output_v = self.afe.current_to_voltage(input_current_a)
        else:
            afe_output_v = None

        # ADC 샘플링
        sample = self.adc.read_single(afe_output_v)

        # 역변환으로 전류 계산
        measured_current = self.afe.voltage_to_current(sample.voltage_v)

        return {
            'raw_code': sample.raw_code,
            'adc_voltage_v': sample.voltage_v,
            'measured_current_a': measured_current,
            'timestamp_us': sample.timestamp_us,
            'gain': sample.gain.value,
            'data_rate_sps': sample.data_rate.value,
            'afe_tia_ohm': self.afe.get_tia_gain_ohm(),
            'temperature_c': self.board_temperature_c
        }

    def acquire_continuous(self,
                          num_samples: int,
                          input_signal: np.ndarray = None) -> List[Dict[str, Any]]:
        """연속 샘플 획득"""
        samples = []

        for i in range(num_samples):
            if input_signal is not None and i < len(input_signal):
                current = input_signal[i]
            else:
                current = None

            sample = self.acquire_single_sample(current)
            samples.append(sample)

        return samples

    def self_test(self) -> Dict[str, bool]:
        """자체 테스트"""
        results = {}

        # ADC 테스트
        try:
            self.adc.self_calibrate()
            sample = self.adc.read_single(0.0)
            results['adc'] = abs(sample.voltage_v) < 0.01  # 오프셋 < 10mV
        except:
            results['adc'] = False

        # AFE 테스트
        try:
            self.afe.enable()
            temp = self.afe.get_temperature()
            results['afe'] = 0 < temp < 85
        except:
            results['afe'] = False

        # 전원 테스트
        try:
            vsys = self.power_mgr.get_system_voltage()
            results['power'] = 3.0 < vsys < 4.5
        except:
            results['power'] = False

        # 스위치 매트릭스 테스트
        try:
            self.switch_matrix.connect(0, 0)
            results['switch'] = 0 in self.switch_matrix.connections
        except:
            results['switch'] = False

        return results

    def get_status(self) -> Dict[str, Any]:
        """전체 상태"""
        return {
            'manager_id': self.manager_id,
            'adc': self.adc.get_status(),
            'afe': self.afe.get_status(),
            'power': self.power_mgr.get_status(),
            'dual_adc_enabled': self.dual_adc_enabled,
            'board_temperature_c': self.board_temperature_c
        }


# 편의 함수
def create_hardware_manager(manager_id: str = "DEFAULT") -> HardwareManager:
    """하드웨어 관리자 생성 헬퍼"""
    return HardwareManager(manager_id=manager_id)


def create_adc(device_id: str = "ADC") -> ADS1256:
    """ADC 생성 헬퍼"""
    return ADS1256(device_id=device_id)


def create_afe(device_id: str = "AFE") -> LMP91000:
    """AFE 생성 헬퍼"""
    return LMP91000(device_id=device_id)


__all__ = [
    # Enums
    'ADCDataRate',
    'ADCGain',
    'ADCChannel',
    'ADCInputMode',
    'TIAGain',
    'BiasPolarity',
    'BiasPercentage',
    'PowerSource',
    'ChargingState',
    # Classes
    'ADCSample',
    'ADS1256',
    'LMP91000',
    'SwitchMatrix',
    'BQ24195',
    'HardwareManager',
    # Functions
    'create_hardware_manager',
    'create_adc',
    'create_afe',
]
