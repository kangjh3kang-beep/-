"""
다중 경로 보정 시스템 (Multi-Path Calibration System)

광학, 전자, 무선, 수동 경로를 통한 다중 보정 및
동적 가중치 하이브리드 보정 시스템

주요 기능:
- 광학 경로 보정 (LED/포토다이오드 기반)
- 전자 경로 보정 (내부 기준 저항)
- 무선 경로 보정 (외부 기준 장치)
- 수동 경로 보정 (사용자 입력)
- 동적 가중치 하이브리드 융합
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime, timedelta
import numpy as np


class CalibrationPath(Enum):
    """보정 경로 유형"""
    OPTICAL = "optical"  # 광학 경로
    ELECTRONIC = "electronic"  # 전자 경로
    WIRELESS = "wireless"  # 무선 경로
    MANUAL = "manual"  # 수동 경로


class CalibrationStatus(Enum):
    """보정 상태"""
    NOT_CALIBRATED = "not_calibrated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
    FAILED = "failed"


class CalibrationQuality(Enum):
    """보정 품질 등급"""
    EXCELLENT = "excellent"  # R² > 0.999
    GOOD = "good"  # R² > 0.995
    ACCEPTABLE = "acceptable"  # R² > 0.990
    POOR = "poor"  # R² > 0.980
    UNACCEPTABLE = "unacceptable"  # R² < 0.980


@dataclass
class CalibrationPoint:
    """개별 보정 포인트"""
    reference_value: float
    measured_value: float
    timestamp: datetime
    temperature_c: float = 25.0
    path: CalibrationPath = CalibrationPath.MANUAL
    uncertainty: float = 0.0


@dataclass
class OpticalCalibrationUnit:
    """
    광학 보정 유닛

    LED 광원과 포토다이오드를 이용한 광학 기반 보정
    """
    unit_id: str
    led_wavelength_nm: float = 850.0  # IR LED
    led_power_mw: float = 5.0
    photodiode_sensitivity_a_w: float = 0.5

    # 보정용 광학 경로 특성
    path_length_mm: float = 10.0
    reference_transmittance: float = 0.9

    # 상태
    is_active: bool = False
    last_calibration: Optional[datetime] = None

    # 측정값
    current_intensity: float = 0.0
    baseline_intensity: float = 1.0

    def activate(self) -> None:
        """광학 유닛 활성화"""
        self.is_active = True
        self.current_intensity = self.led_power_mw * self.reference_transmittance

    def deactivate(self) -> None:
        """광학 유닛 비활성화"""
        self.is_active = False
        self.current_intensity = 0.0

    def measure_reference(self) -> float:
        """기준 광학 신호 측정"""
        if not self.is_active:
            return 0.0

        # 광학 측정 시뮬레이션
        base_signal = self.led_power_mw * self.photodiode_sensitivity_a_w
        noise = np.random.normal(0, base_signal * 0.001)  # 0.1% 노이즈

        return base_signal * self.reference_transmittance + noise

    def get_correction_factor(self) -> float:
        """광학 보정 계수 계산"""
        if self.baseline_intensity <= 0:
            return 1.0

        measured = self.measure_reference()
        return self.baseline_intensity / (measured + 1e-10)


@dataclass
class ElectronicCalibrationUnit:
    """
    전자 보정 유닛

    내장 정밀 기준 저항을 이용한 전자적 보정
    """
    unit_id: str

    # 기준 저항 어레이
    reference_resistors: List[float] = field(default_factory=lambda: [
        100.0, 1000.0, 10000.0, 100000.0  # Ω
    ])
    resistor_tolerance_ppm: float = 10.0  # 10 ppm 정밀 저항

    # 기준 전압
    reference_voltage_v: float = 2.5
    voltage_tolerance_ppm: float = 5.0

    # 상태
    is_active: bool = False
    selected_resistor_idx: int = 0

    def activate(self, resistor_idx: int = 0) -> None:
        """전자 보정 유닛 활성화"""
        self.is_active = True
        self.selected_resistor_idx = min(resistor_idx, len(self.reference_resistors) - 1)

    def deactivate(self) -> None:
        """비활성화"""
        self.is_active = False

    def get_reference_resistance(self) -> float:
        """현재 선택된 기준 저항값 반환"""
        if not self.is_active:
            return 0.0

        nominal = self.reference_resistors[self.selected_resistor_idx]
        # 온도 드리프트 및 공차 포함
        tolerance = self.resistor_tolerance_ppm * 1e-6
        variation = np.random.uniform(-tolerance, tolerance)

        return nominal * (1 + variation)

    def get_reference_voltage(self) -> float:
        """기준 전압 반환"""
        tolerance = self.voltage_tolerance_ppm * 1e-6
        variation = np.random.uniform(-tolerance, tolerance)

        return self.reference_voltage_v * (1 + variation)

    def perform_self_test(self) -> Dict[str, Any]:
        """자체 테스트 수행"""
        results = {
            'status': 'passed',
            'voltage_error_ppm': 0.0,
            'resistor_errors_ppm': []
        }

        # 전압 테스트
        v_measured = self.get_reference_voltage()
        v_error = abs(v_measured - self.reference_voltage_v) / self.reference_voltage_v * 1e6
        results['voltage_error_ppm'] = v_error

        # 저항 테스트
        self.activate()
        for i, nominal in enumerate(self.reference_resistors):
            self.selected_resistor_idx = i
            measured = self.get_reference_resistance()
            error = abs(measured - nominal) / nominal * 1e6
            results['resistor_errors_ppm'].append(error)

        # 합격 판정
        if v_error > self.voltage_tolerance_ppm * 2:
            results['status'] = 'failed'
        if any(e > self.resistor_tolerance_ppm * 2 for e in results['resistor_errors_ppm']):
            results['status'] = 'failed'

        self.deactivate()
        return results


@dataclass
class WirelessCalibrationUnit:
    """
    무선 보정 유닛

    NFC/BLE를 통한 외부 기준 장치와의 무선 보정
    """
    unit_id: str
    protocol: str = "NFC"  # NFC, BLE, WiFi

    # 외부 기준 장치 정보
    external_reference_id: Optional[str] = None
    external_reference_value: float = 0.0
    external_uncertainty: float = 0.0

    # 통신 상태
    is_connected: bool = False
    signal_strength_dbm: float = -50.0
    last_sync: Optional[datetime] = None

    def connect(self, reference_id: str) -> bool:
        """외부 기준 장치 연결"""
        # 연결 시뮬레이션
        self.external_reference_id = reference_id
        self.is_connected = True
        self.last_sync = datetime.now()
        return True

    def disconnect(self) -> None:
        """연결 해제"""
        self.is_connected = False
        self.external_reference_id = None

    def receive_reference_value(self) -> Tuple[float, float]:
        """
        외부 기준값 수신

        Returns:
            (기준값, 불확도) 튜플
        """
        if not self.is_connected:
            return (0.0, float('inf'))

        # 무선 전송으로 인한 추가 불확도
        wireless_uncertainty = 0.01 * abs(self.signal_strength_dbm / -100)

        return (
            self.external_reference_value,
            self.external_uncertainty + wireless_uncertainty
        )

    def get_connection_quality(self) -> float:
        """연결 품질 (0-1)"""
        if not self.is_connected:
            return 0.0

        # 신호 강도 기반 품질 계산
        # -30 dBm: excellent, -90 dBm: poor
        quality = (self.signal_strength_dbm + 90) / 60
        return max(0.0, min(1.0, quality))


@dataclass
class ManualCalibrationUnit:
    """
    수동 보정 유닛

    사용자 입력 기반 보정
    """
    unit_id: str

    # 보정 포인트 저장
    calibration_points: List[CalibrationPoint] = field(default_factory=list)

    # 보정 범위
    min_value: float = 0.0
    max_value: float = 10.0
    num_points_required: int = 5

    def add_point(self,
                  reference: float,
                  measured: float,
                  temperature: float = 25.0) -> None:
        """보정 포인트 추가"""
        point = CalibrationPoint(
            reference_value=reference,
            measured_value=measured,
            timestamp=datetime.now(),
            temperature_c=temperature,
            path=CalibrationPath.MANUAL
        )
        self.calibration_points.append(point)

    def clear_points(self) -> None:
        """보정 포인트 초기화"""
        self.calibration_points.clear()

    def get_num_points(self) -> int:
        """현재 포인트 수"""
        return len(self.calibration_points)

    def is_complete(self) -> bool:
        """보정 완료 여부"""
        return len(self.calibration_points) >= self.num_points_required


@dataclass
class PathCalibrationResult:
    """경로별 보정 결과"""
    path: CalibrationPath
    timestamp: datetime

    # 보정 계수
    gain: float = 1.0
    offset: float = 0.0

    # 품질 지표
    r_squared: float = 0.0
    uncertainty: float = 0.0
    max_error: float = 0.0

    # 유효 기간
    validity_hours: float = 24.0

    def is_valid(self) -> bool:
        """유효성 검사"""
        elapsed = datetime.now() - self.timestamp
        return elapsed.total_seconds() < self.validity_hours * 3600

    def get_quality(self) -> CalibrationQuality:
        """품질 등급 반환"""
        if self.r_squared > 0.999:
            return CalibrationQuality.EXCELLENT
        elif self.r_squared > 0.995:
            return CalibrationQuality.GOOD
        elif self.r_squared > 0.990:
            return CalibrationQuality.ACCEPTABLE
        elif self.r_squared > 0.980:
            return CalibrationQuality.POOR
        else:
            return CalibrationQuality.UNACCEPTABLE


@dataclass
class HybridCalibrationResult:
    """하이브리드 융합 보정 결과"""
    timestamp: datetime

    # 융합 보정 계수
    fused_gain: float = 1.0
    fused_offset: float = 0.0
    fused_uncertainty: float = 0.0

    # 경로별 가중치
    path_weights: Dict[CalibrationPath, float] = field(default_factory=dict)

    # 경로별 결과
    path_results: Dict[CalibrationPath, PathCalibrationResult] = field(default_factory=dict)

    # AI 예측 가중치
    ai_prediction_weight: float = 0.0
    physical_measurement_weight: float = 1.0


class MultiPathCalibrationSystem:
    """
    다중 경로 보정 시스템

    광학, 전자, 무선, 수동 경로를 통한 다중 보정 및
    동적 가중치 하이브리드 융합 알고리즘
    """

    def __init__(self, system_id: str = "MULTI_PATH_CAL_001"):
        """
        Args:
            system_id: 시스템 식별자
        """
        self.system_id = system_id
        self.status = CalibrationStatus.NOT_CALIBRATED

        # 보정 유닛 초기화
        self.optical_unit = OpticalCalibrationUnit(unit_id=f"{system_id}_OPT")
        self.electronic_unit = ElectronicCalibrationUnit(unit_id=f"{system_id}_ELEC")
        self.wireless_unit = WirelessCalibrationUnit(unit_id=f"{system_id}_WL")
        self.manual_unit = ManualCalibrationUnit(unit_id=f"{system_id}_MANUAL")

        # 경로별 보정 결과
        self.path_results: Dict[CalibrationPath, PathCalibrationResult] = {}

        # 하이브리드 융합 결과
        self.hybrid_result: Optional[HybridCalibrationResult] = None

        # 동적 가중치 설정
        self.path_priorities: Dict[CalibrationPath, float] = {
            CalibrationPath.ELECTRONIC: 0.35,
            CalibrationPath.OPTICAL: 0.30,
            CalibrationPath.WIRELESS: 0.20,
            CalibrationPath.MANUAL: 0.15
        }

        # AI 예측 모델 상태
        self.ai_model_trained: bool = False
        self.ai_prediction_confidence: float = 0.0

        # 보정 이력
        self.calibration_history: List[HybridCalibrationResult] = []

    def calibrate_optical_path(self) -> PathCalibrationResult:
        """광학 경로 보정 수행"""
        self.status = CalibrationStatus.IN_PROGRESS

        self.optical_unit.activate()

        # 여러 포인트에서 측정
        references = []
        measurements = []

        # 기준 강도를 변화시키며 측정
        for intensity_factor in [0.2, 0.4, 0.6, 0.8, 1.0]:
            ref_value = intensity_factor * self.optical_unit.led_power_mw
            measured = self.optical_unit.measure_reference() * intensity_factor

            references.append(ref_value)
            measurements.append(measured)

        self.optical_unit.deactivate()

        # 선형 회귀
        gain, offset, r_squared, uncertainty = self._linear_regression(
            np.array(references),
            np.array(measurements)
        )

        result = PathCalibrationResult(
            path=CalibrationPath.OPTICAL,
            timestamp=datetime.now(),
            gain=gain,
            offset=offset,
            r_squared=r_squared,
            uncertainty=uncertainty,
            max_error=np.max(np.abs(np.array(measurements) - (gain * np.array(references) + offset)))
        )

        self.path_results[CalibrationPath.OPTICAL] = result
        return result

    def calibrate_electronic_path(self) -> PathCalibrationResult:
        """전자 경로 보정 수행"""
        self.status = CalibrationStatus.IN_PROGRESS

        references = []
        measurements = []

        self.electronic_unit.activate()

        for i in range(len(self.electronic_unit.reference_resistors)):
            self.electronic_unit.selected_resistor_idx = i
            ref_r = self.electronic_unit.reference_resistors[i]
            measured_r = self.electronic_unit.get_reference_resistance()

            references.append(ref_r)
            measurements.append(measured_r)

        self.electronic_unit.deactivate()

        # 로그 스케일 선형 회귀 (저항은 로그 스케일)
        log_ref = np.log10(references)
        log_meas = np.log10(measurements)

        gain, offset, r_squared, uncertainty = self._linear_regression(log_ref, log_meas)

        result = PathCalibrationResult(
            path=CalibrationPath.ELECTRONIC,
            timestamp=datetime.now(),
            gain=gain,
            offset=offset,
            r_squared=r_squared,
            uncertainty=uncertainty * np.mean(references),  # 선형 스케일로 변환
            max_error=np.max(np.abs(np.array(measurements) - np.array(references)))
        )

        self.path_results[CalibrationPath.ELECTRONIC] = result
        return result

    def calibrate_wireless_path(self,
                                external_reference_id: str,
                                external_reference_value: float,
                                external_uncertainty: float = 0.001) -> PathCalibrationResult:
        """무선 경로 보정 수행"""
        self.status = CalibrationStatus.IN_PROGRESS

        # 외부 기준 장치 연결
        self.wireless_unit.external_reference_value = external_reference_value
        self.wireless_unit.external_uncertainty = external_uncertainty

        if not self.wireless_unit.connect(external_reference_id):
            return PathCalibrationResult(
                path=CalibrationPath.WIRELESS,
                timestamp=datetime.now(),
                r_squared=0.0,
                uncertainty=float('inf')
            )

        references = []
        measurements = []

        # 여러 번 측정하여 평균
        for _ in range(10):
            ref, unc = self.wireless_unit.receive_reference_value()
            # 시뮬레이션: 로컬 측정값
            local_measured = ref * (1 + np.random.normal(0, 0.001))

            references.append(ref)
            measurements.append(local_measured)

        self.wireless_unit.disconnect()

        gain, offset, r_squared, uncertainty = self._linear_regression(
            np.array(references),
            np.array(measurements)
        )

        result = PathCalibrationResult(
            path=CalibrationPath.WIRELESS,
            timestamp=datetime.now(),
            gain=gain,
            offset=offset,
            r_squared=r_squared,
            uncertainty=uncertainty + external_uncertainty
        )

        self.path_results[CalibrationPath.WIRELESS] = result
        return result

    def calibrate_manual_path(self,
                              calibration_points: List[Tuple[float, float]]) -> PathCalibrationResult:
        """수동 경로 보정 수행"""
        self.status = CalibrationStatus.IN_PROGRESS

        self.manual_unit.clear_points()

        references = []
        measurements = []

        for ref, meas in calibration_points:
            self.manual_unit.add_point(ref, meas)
            references.append(ref)
            measurements.append(meas)

        if len(references) < 2:
            return PathCalibrationResult(
                path=CalibrationPath.MANUAL,
                timestamp=datetime.now(),
                r_squared=0.0,
                uncertainty=float('inf')
            )

        gain, offset, r_squared, uncertainty = self._linear_regression(
            np.array(references),
            np.array(measurements)
        )

        result = PathCalibrationResult(
            path=CalibrationPath.MANUAL,
            timestamp=datetime.now(),
            gain=gain,
            offset=offset,
            r_squared=r_squared,
            uncertainty=uncertainty,
            max_error=np.max(np.abs(np.array(measurements) - (gain * np.array(references) + offset)))
        )

        self.path_results[CalibrationPath.MANUAL] = result
        return result

    def _linear_regression(self,
                           x: np.ndarray,
                           y: np.ndarray) -> Tuple[float, float, float, float]:
        """
        선형 회귀 수행

        Returns:
            (기울기, 절편, R², 불확도)
        """
        n = len(x)
        if n < 2:
            return (1.0, 0.0, 0.0, float('inf'))

        # 최소자승법
        x_mean = np.mean(x)
        y_mean = np.mean(y)

        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)

        if abs(denominator) < 1e-10:
            return (1.0, 0.0, 0.0, float('inf'))

        gain = numerator / denominator
        offset = y_mean - gain * x_mean

        # R² 계산
        y_pred = gain * x + offset
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y_mean) ** 2)

        r_squared = 1 - ss_res / (ss_tot + 1e-10)

        # 표준 불확도
        residuals = y - y_pred
        uncertainty = np.std(residuals) / np.sqrt(n)

        return (gain, offset, r_squared, uncertainty)

    def compute_dynamic_weights(self) -> Dict[CalibrationPath, float]:
        """
        동적 가중치 계산

        각 경로의 보정 품질과 유효성에 기반한 가중치 계산
        """
        weights = {}
        total_weight = 0.0

        for path, priority in self.path_priorities.items():
            if path not in self.path_results:
                weights[path] = 0.0
                continue

            result = self.path_results[path]

            # 유효성 검사
            if not result.is_valid():
                weights[path] = 0.0
                continue

            # 품질 기반 가중치
            quality_factor = result.r_squared ** 2  # R²의 제곱

            # 불확도 기반 가중치 (낮을수록 높은 가중치)
            uncertainty_factor = 1.0 / (1.0 + result.uncertainty * 100)

            # 최종 가중치
            weight = priority * quality_factor * uncertainty_factor
            weights[path] = weight
            total_weight += weight

        # 정규화
        if total_weight > 0:
            for path in weights:
                weights[path] /= total_weight

        return weights

    def hybrid_fusion_calibration(self) -> HybridCalibrationResult:
        """
        하이브리드 융합 보정

        다중 경로의 보정 결과를 동적 가중치로 융합
        """
        # 동적 가중치 계산
        weights = self.compute_dynamic_weights()

        # 가중 평균으로 융합
        fused_gain = 0.0
        fused_offset = 0.0
        fused_uncertainty_sq = 0.0

        for path, weight in weights.items():
            if weight <= 0 or path not in self.path_results:
                continue

            result = self.path_results[path]
            fused_gain += weight * result.gain
            fused_offset += weight * result.offset
            fused_uncertainty_sq += (weight * result.uncertainty) ** 2

        fused_uncertainty = np.sqrt(fused_uncertainty_sq)

        # AI 예측과 물리 측정의 동적 가중치 결정
        ai_weight = self.ai_prediction_confidence if self.ai_model_trained else 0.0
        physical_weight = 1.0 - ai_weight

        result = HybridCalibrationResult(
            timestamp=datetime.now(),
            fused_gain=fused_gain if fused_gain != 0 else 1.0,
            fused_offset=fused_offset,
            fused_uncertainty=fused_uncertainty,
            path_weights=weights,
            path_results=self.path_results.copy(),
            ai_prediction_weight=ai_weight,
            physical_measurement_weight=physical_weight
        )

        self.hybrid_result = result
        self.calibration_history.append(result)
        self.status = CalibrationStatus.COMPLETED

        return result

    def apply_calibration(self, raw_value: float) -> float:
        """
        보정 적용

        Args:
            raw_value: 원시 측정값

        Returns:
            보정된 값
        """
        if self.hybrid_result is None:
            return raw_value

        # y = gain * x + offset 의 역변환
        # x_corrected = (y - offset) / gain
        corrected = (raw_value - self.hybrid_result.fused_offset) / self.hybrid_result.fused_gain

        return corrected

    def apply_calibration_with_uncertainty(self,
                                           raw_value: float) -> Tuple[float, float]:
        """
        불확도와 함께 보정 적용

        Returns:
            (보정값, 불확도) 튜플
        """
        corrected = self.apply_calibration(raw_value)

        if self.hybrid_result is None:
            return (corrected, float('inf'))

        # 불확도 전파
        uncertainty = self.hybrid_result.fused_uncertainty / abs(self.hybrid_result.fused_gain)

        return (corrected, uncertainty)

    def auto_calibrate(self) -> HybridCalibrationResult:
        """
        자동 다중 경로 보정

        사용 가능한 모든 경로를 순차적으로 보정하고 융합
        """
        # 1. 전자 경로 보정 (가장 안정적)
        self.calibrate_electronic_path()

        # 2. 광학 경로 보정
        self.calibrate_optical_path()

        # 3. 하이브리드 융합
        return self.hybrid_fusion_calibration()

    def get_calibration_status(self) -> Dict[str, Any]:
        """보정 상태 정보 반환"""
        path_status = {}
        for path in CalibrationPath:
            if path in self.path_results:
                result = self.path_results[path]
                path_status[path.value] = {
                    'status': 'valid' if result.is_valid() else 'expired',
                    'quality': result.get_quality().value,
                    'r_squared': result.r_squared,
                    'uncertainty': result.uncertainty,
                    'age_hours': (datetime.now() - result.timestamp).total_seconds() / 3600
                }
            else:
                path_status[path.value] = {'status': 'not_calibrated'}

        return {
            'system_id': self.system_id,
            'overall_status': self.status.value,
            'path_status': path_status,
            'hybrid_result': {
                'gain': self.hybrid_result.fused_gain if self.hybrid_result else None,
                'offset': self.hybrid_result.fused_offset if self.hybrid_result else None,
                'uncertainty': self.hybrid_result.fused_uncertainty if self.hybrid_result else None,
                'path_weights': {k.value: v for k, v in self.hybrid_result.path_weights.items()} if self.hybrid_result else {}
            },
            'calibration_count': len(self.calibration_history)
        }

    def export_calibration(self, filepath: str) -> None:
        """보정 데이터 내보내기"""
        import json

        data = {
            'system_id': self.system_id,
            'export_timestamp': datetime.now().isoformat(),
            'status': self.status.value,
            'path_results': {},
            'hybrid_result': None
        }

        for path, result in self.path_results.items():
            data['path_results'][path.value] = {
                'gain': result.gain,
                'offset': result.offset,
                'r_squared': result.r_squared,
                'uncertainty': result.uncertainty,
                'timestamp': result.timestamp.isoformat()
            }

        if self.hybrid_result:
            data['hybrid_result'] = {
                'fused_gain': self.hybrid_result.fused_gain,
                'fused_offset': self.hybrid_result.fused_offset,
                'fused_uncertainty': self.hybrid_result.fused_uncertainty,
                'path_weights': {k.value: v for k, v in self.hybrid_result.path_weights.items()},
                'timestamp': self.hybrid_result.timestamp.isoformat()
            }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def import_calibration(self, filepath: str) -> bool:
        """보정 데이터 가져오기"""
        import json

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for path_str, result_data in data.get('path_results', {}).items():
                path = CalibrationPath(path_str)
                self.path_results[path] = PathCalibrationResult(
                    path=path,
                    timestamp=datetime.fromisoformat(result_data['timestamp']),
                    gain=result_data['gain'],
                    offset=result_data['offset'],
                    r_squared=result_data['r_squared'],
                    uncertainty=result_data['uncertainty']
                )

            if data.get('hybrid_result'):
                hr = data['hybrid_result']
                self.hybrid_result = HybridCalibrationResult(
                    timestamp=datetime.fromisoformat(hr['timestamp']),
                    fused_gain=hr['fused_gain'],
                    fused_offset=hr['fused_offset'],
                    fused_uncertainty=hr['fused_uncertainty'],
                    path_weights={CalibrationPath(k): v for k, v in hr['path_weights'].items()}
                )
                self.status = CalibrationStatus.COMPLETED

            return True

        except Exception as e:
            print(f"Import failed: {e}")
            return False


# 편의 함수
def create_multi_path_calibrator(system_id: str = "DEFAULT") -> MultiPathCalibrationSystem:
    """다중 경로 보정 시스템 생성 헬퍼"""
    return MultiPathCalibrationSystem(system_id=system_id)


def quick_auto_calibration() -> HybridCalibrationResult:
    """빠른 자동 보정"""
    system = MultiPathCalibrationSystem()
    return system.auto_calibrate()


__all__ = [
    # Enums
    'CalibrationPath',
    'CalibrationStatus',
    'CalibrationQuality',
    # Classes
    'CalibrationPoint',
    'OpticalCalibrationUnit',
    'ElectronicCalibrationUnit',
    'WirelessCalibrationUnit',
    'ManualCalibrationUnit',
    'PathCalibrationResult',
    'HybridCalibrationResult',
    'MultiPathCalibrationSystem',
    # Functions
    'create_multi_path_calibrator',
    'quick_auto_calibration',
]
