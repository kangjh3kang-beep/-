"""
캘리브레이션 모듈

측정 시스템의 정확도를 높이기 위한 보정 기능을 제공합니다.
"""

from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from datetime import datetime
import json


class CalibrationType(Enum):
    """캘리브레이션 유형"""
    ZERO_OFFSET = "zero_offset"         # 영점 보정
    GAIN = "gain"                        # 게인 보정
    LINEARITY = "linearity"              # 선형성 보정
    TEMPERATURE = "temperature"          # 온도 보상
    MULTI_POINT = "multi_point"          # 다점 보정


@dataclass
class CalibrationPoint:
    """캘리브레이션 포인트"""
    reference_value: float  # 기준값
    measured_value: float   # 측정값
    timestamp: datetime = field(default_factory=datetime.now)
    temperature: Optional[float] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class CalibrationCertificate:
    """캘리브레이션 인증서"""
    certificate_id: str
    calibration_date: datetime
    expiry_date: datetime
    calibration_type: CalibrationType
    channel_id: int
    points: List[CalibrationPoint]
    gain: float
    offset: float
    linearity_error: float  # 선형성 오차 (%)
    uncertainty: float      # 측정 불확도
    technician: str = ""
    notes: str = ""

    def is_valid(self) -> bool:
        """유효 여부 확인"""
        return datetime.now() < self.expiry_date

    def to_dict(self) -> dict:
        """딕셔너리 변환"""
        return {
            "certificate_id": self.certificate_id,
            "calibration_date": self.calibration_date.isoformat(),
            "expiry_date": self.expiry_date.isoformat(),
            "calibration_type": self.calibration_type.value,
            "channel_id": self.channel_id,
            "points": [
                {
                    "reference": p.reference_value,
                    "measured": p.measured_value,
                    "timestamp": p.timestamp.isoformat(),
                    "temperature": p.temperature,
                }
                for p in self.points
            ],
            "gain": self.gain,
            "offset": self.offset,
            "linearity_error": self.linearity_error,
            "uncertainty": self.uncertainty,
            "technician": self.technician,
            "notes": self.notes,
        }


class CalibrationManager:
    """
    캘리브레이션 관리자

    측정 채널의 보정 데이터를 관리하고 적용합니다.

    Example:
        >>> cal_mgr = CalibrationManager()
        >>> cal_mgr.add_calibration_point(0, 1.0, 0.998)
        >>> cal_mgr.add_calibration_point(0, 5.0, 4.995)
        >>> cal_mgr.calculate_calibration(0)
        >>> corrected = cal_mgr.apply_calibration(0, measured_data)
    """

    def __init__(self):
        """초기화"""
        # 채널별 캘리브레이션 포인트
        self._calibration_points: Dict[int, List[CalibrationPoint]] = {}

        # 채널별 캘리브레이션 파라미터
        self._calibration_params: Dict[int, Dict] = {}

        # 캘리브레이션 인증서
        self._certificates: Dict[int, CalibrationCertificate] = {}

        # 온도 보상 계수
        self._temp_coefficients: Dict[int, float] = {}

    def add_calibration_point(self,
                              channel_id: int,
                              reference_value: float,
                              measured_value: float,
                              temperature: Optional[float] = None) -> None:
        """
        캘리브레이션 포인트 추가

        Args:
            channel_id: 채널 ID
            reference_value: 기준값 (알려진 정확한 값)
            measured_value: 측정값 (실제 측정된 값)
            temperature: 측정 시 온도
        """
        if channel_id not in self._calibration_points:
            self._calibration_points[channel_id] = []

        point = CalibrationPoint(
            reference_value=reference_value,
            measured_value=measured_value,
            temperature=temperature
        )
        self._calibration_points[channel_id].append(point)

    def clear_calibration_points(self, channel_id: int) -> None:
        """캘리브레이션 포인트 초기화"""
        self._calibration_points[channel_id] = []

    def calculate_calibration(self,
                              channel_id: int,
                              method: str = "linear") -> Dict[str, float]:
        """
        캘리브레이션 계수 계산

        Args:
            channel_id: 채널 ID
            method: 보정 방법 ("linear", "polynomial", "spline")

        Returns:
            Dict: 캘리브레이션 파라미터
        """
        points = self._calibration_points.get(channel_id, [])
        if len(points) < 2:
            raise ValueError(f"채널 {channel_id}에 최소 2개의 캘리브레이션 포인트가 필요합니다.")

        references = np.array([p.reference_value for p in points])
        measured = np.array([p.measured_value for p in points])

        if method == "linear":
            # 선형 회귀
            coeffs = np.polyfit(measured, references, 1)
            gain = coeffs[0]
            offset = coeffs[1]

            # 선형성 오차 계산
            predicted = measured * gain + offset
            linearity_error = np.max(np.abs(predicted - references)) / np.ptp(references) * 100

            # 불확도 계산 (표준 편차 기반)
            residuals = references - predicted
            uncertainty = np.std(residuals)

            params = {
                "method": "linear",
                "gain": gain,
                "offset": offset,
                "linearity_error": linearity_error,
                "uncertainty": uncertainty,
                "coefficients": coeffs.tolist(),
            }

        elif method == "polynomial":
            # 다항식 회귀 (3차)
            degree = min(3, len(points) - 1)
            coeffs = np.polyfit(measured, references, degree)

            predicted = np.polyval(coeffs, measured)
            linearity_error = np.max(np.abs(predicted - references)) / np.ptp(references) * 100
            residuals = references - predicted
            uncertainty = np.std(residuals)

            params = {
                "method": "polynomial",
                "degree": degree,
                "coefficients": coeffs.tolist(),
                "linearity_error": linearity_error,
                "uncertainty": uncertainty,
            }
            # 선형 근사 (참고용)
            linear_coeffs = np.polyfit(measured, references, 1)
            params["gain"] = linear_coeffs[0]
            params["offset"] = linear_coeffs[1]

        else:
            raise ValueError(f"지원하지 않는 캘리브레이션 방법: {method}")

        self._calibration_params[channel_id] = params
        return params

    def apply_calibration(self,
                          channel_id: int,
                          data: Union[float, np.ndarray],
                          temperature: Optional[float] = None) -> Union[float, np.ndarray]:
        """
        캘리브레이션 적용

        Args:
            channel_id: 채널 ID
            data: 측정 데이터
            temperature: 현재 온도 (온도 보상용)

        Returns:
            보정된 데이터
        """
        if channel_id not in self._calibration_params:
            raise ValueError(f"채널 {channel_id}의 캘리브레이션이 설정되지 않았습니다.")

        params = self._calibration_params[channel_id]
        data = np.asarray(data)

        if params["method"] == "linear":
            corrected = data * params["gain"] + params["offset"]
        elif params["method"] == "polynomial":
            corrected = np.polyval(params["coefficients"], data)
        else:
            corrected = data

        # 온도 보상
        if temperature is not None and channel_id in self._temp_coefficients:
            temp_coeff = self._temp_coefficients[channel_id]
            reference_temp = 25.0  # 기준 온도
            temp_correction = 1 + temp_coeff * (temperature - reference_temp)
            corrected = corrected * temp_correction

        return corrected

    def set_temperature_coefficient(self, channel_id: int, coefficient: float) -> None:
        """
        온도 계수 설정

        Args:
            channel_id: 채널 ID
            coefficient: 온도 계수 (ppm/°C)
        """
        self._temp_coefficients[channel_id] = coefficient / 1e6

    def generate_certificate(self,
                             channel_id: int,
                             certificate_id: str,
                             validity_days: int = 365,
                             technician: str = "",
                             notes: str = "") -> CalibrationCertificate:
        """
        캘리브레이션 인증서 생성

        Args:
            channel_id: 채널 ID
            certificate_id: 인증서 ID
            validity_days: 유효 기간 (일)
            technician: 담당 기술자
            notes: 비고

        Returns:
            CalibrationCertificate: 캘리브레이션 인증서
        """
        if channel_id not in self._calibration_params:
            raise ValueError(f"채널 {channel_id}의 캘리브레이션이 설정되지 않았습니다.")

        params = self._calibration_params[channel_id]
        points = self._calibration_points.get(channel_id, [])

        from datetime import timedelta

        cert = CalibrationCertificate(
            certificate_id=certificate_id,
            calibration_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=validity_days),
            calibration_type=CalibrationType.MULTI_POINT if len(points) > 2 else CalibrationType.GAIN,
            channel_id=channel_id,
            points=points,
            gain=params.get("gain", 1.0),
            offset=params.get("offset", 0.0),
            linearity_error=params.get("linearity_error", 0.0),
            uncertainty=params.get("uncertainty", 0.0),
            technician=technician,
            notes=notes,
        )

        self._certificates[channel_id] = cert
        return cert

    def get_certificate(self, channel_id: int) -> Optional[CalibrationCertificate]:
        """캘리브레이션 인증서 조회"""
        return self._certificates.get(channel_id)

    def export_calibration(self, channel_id: int, filepath: str) -> None:
        """
        캘리브레이션 데이터 내보내기

        Args:
            channel_id: 채널 ID
            filepath: 파일 경로 (.json)
        """
        data = {
            "channel_id": channel_id,
            "parameters": self._calibration_params.get(channel_id, {}),
            "points": [
                {
                    "reference": p.reference_value,
                    "measured": p.measured_value,
                    "timestamp": p.timestamp.isoformat(),
                    "temperature": p.temperature,
                }
                for p in self._calibration_points.get(channel_id, [])
            ],
            "temperature_coefficient": self._temp_coefficients.get(channel_id),
            "export_time": datetime.now().isoformat(),
        }

        if channel_id in self._certificates:
            data["certificate"] = self._certificates[channel_id].to_dict()

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def import_calibration(self, filepath: str) -> int:
        """
        캘리브레이션 데이터 가져오기

        Args:
            filepath: 파일 경로 (.json)

        Returns:
            int: 가져온 채널 ID
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        channel_id = data["channel_id"]

        # 파라미터 복원
        if "parameters" in data:
            self._calibration_params[channel_id] = data["parameters"]

        # 포인트 복원
        if "points" in data:
            self._calibration_points[channel_id] = [
                CalibrationPoint(
                    reference_value=p["reference"],
                    measured_value=p["measured"],
                    timestamp=datetime.fromisoformat(p["timestamp"]),
                    temperature=p.get("temperature"),
                )
                for p in data["points"]
            ]

        # 온도 계수 복원
        if data.get("temperature_coefficient") is not None:
            self._temp_coefficients[channel_id] = data["temperature_coefficient"]

        return channel_id
