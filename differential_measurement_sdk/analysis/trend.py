"""
트렌드 분석 모듈

시계열 데이터의 트렌드 분석을 제공합니다.
"""

from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np


class TrendType(Enum):
    """트렌드 유형"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    OSCILLATING = "oscillating"
    UNKNOWN = "unknown"


@dataclass
class TrendResult:
    """트렌드 분석 결과"""

    trend_type: TrendType = TrendType.UNKNOWN
    slope: float = 0.0          # 기울기
    intercept: float = 0.0      # 절편
    r_squared: float = 0.0      # 결정계수
    trend_line: np.ndarray = field(default_factory=lambda: np.array([]))
    detrended: np.ndarray = field(default_factory=lambda: np.array([]))

    # 추가 정보
    rate_of_change: float = 0.0  # 변화율 (%/단위시간)
    stability_index: float = 0.0  # 안정성 지수 (0-1, 높을수록 안정)
    drift: float = 0.0           # 드리프트 (시작점 대비 변화)


class TrendAnalyzer:
    """
    트렌드 분석기

    시계열 데이터의 트렌드를 분석합니다.

    Example:
        >>> analyzer = TrendAnalyzer()
        >>> result = analyzer.analyze(time_series_data)
        >>> print(f"트렌드: {result.trend_type.value}, 기울기: {result.slope}")
    """

    def __init__(self,
                 stability_threshold: float = 0.1,
                 min_trend_r_squared: float = 0.5):
        """
        초기화

        Args:
            stability_threshold: 안정 판정 임계값 (기울기/평균)
            min_trend_r_squared: 트렌드 판정 최소 R² 값
        """
        self.stability_threshold = stability_threshold
        self.min_trend_r_squared = min_trend_r_squared

    def analyze(self,
                data: Union[np.ndarray, list],
                timestamps: Optional[Union[np.ndarray, list]] = None) -> TrendResult:
        """
        트렌드 분석 수행

        Args:
            data: 입력 데이터
            timestamps: 타임스탬프 (없으면 인덱스 사용)

        Returns:
            TrendResult: 분석 결과
        """
        data = np.asarray(data, dtype=float)

        if timestamps is None:
            timestamps = np.arange(len(data))
        else:
            timestamps = np.asarray(timestamps, dtype=float)

        n = len(data)
        if n < 2:
            return TrendResult(trend_type=TrendType.UNKNOWN)

        # 선형 회귀
        slope, intercept = self._linear_regression(timestamps, data)

        # 트렌드 라인
        trend_line = slope * timestamps + intercept

        # 결정계수 (R²)
        ss_res = np.sum((data - trend_line) ** 2)
        ss_tot = np.sum((data - np.mean(data)) ** 2)
        r_squared = 1 - ss_res / (ss_tot + 1e-10)

        # 디트렌드 데이터
        detrended = data - trend_line

        # 변화율 (시작값 대비)
        if abs(data[0]) > 1e-10:
            rate_of_change = (data[-1] - data[0]) / data[0] * 100
        else:
            rate_of_change = 0.0

        # 드리프트
        drift = data[-1] - data[0]

        # 안정성 지수
        data_range = np.max(data) - np.min(data)
        mean_val = np.mean(np.abs(data))
        if mean_val > 1e-10:
            stability_index = 1 - min(1, data_range / mean_val)
        else:
            stability_index = 1.0

        # 트렌드 유형 결정
        trend_type = self._determine_trend_type(
            slope, data, r_squared, detrended
        )

        return TrendResult(
            trend_type=trend_type,
            slope=slope,
            intercept=intercept,
            r_squared=r_squared,
            trend_line=trend_line,
            detrended=detrended,
            rate_of_change=rate_of_change,
            stability_index=stability_index,
            drift=drift,
        )

    def _linear_regression(self, x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
        """선형 회귀"""
        n = len(x)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x ** 2)

        denom = n * sum_x2 - sum_x ** 2
        if abs(denom) < 1e-10:
            return 0.0, np.mean(y)

        slope = (n * sum_xy - sum_x * sum_y) / denom
        intercept = (sum_y - slope * sum_x) / n

        return slope, intercept

    def _determine_trend_type(self,
                              slope: float,
                              data: np.ndarray,
                              r_squared: float,
                              detrended: np.ndarray) -> TrendType:
        """트렌드 유형 결정"""
        mean_val = np.mean(np.abs(data))

        # 상대적 기울기
        if mean_val > 1e-10:
            relative_slope = abs(slope) / mean_val
        else:
            relative_slope = abs(slope)

        # R²가 낮으면 진동 또는 불명확
        if r_squared < self.min_trend_r_squared:
            # 진동 확인
            zero_crossings = np.sum(np.diff(np.sign(detrended)) != 0)
            if zero_crossings > len(data) * 0.3:
                return TrendType.OSCILLATING
            return TrendType.UNKNOWN

        # 기울기로 트렌드 판정
        if relative_slope < self.stability_threshold:
            return TrendType.STABLE
        elif slope > 0:
            return TrendType.INCREASING
        else:
            return TrendType.DECREASING

    def detect_change_points(self,
                             data: Union[np.ndarray, list],
                             threshold: float = 2.0) -> List[int]:
        """
        변화점 검출

        Args:
            data: 입력 데이터
            threshold: 임계값 (표준편차 배수)

        Returns:
            List[int]: 변화점 인덱스 리스트
        """
        data = np.asarray(data, dtype=float)
        n = len(data)

        if n < 4:
            return []

        # 차분
        diff = np.diff(data)

        # 이동 평균과 표준편차
        window = max(5, n // 10)
        change_points = []

        for i in range(window, n - 1):
            local_std = np.std(diff[max(0, i - window):i])
            if local_std < 1e-10:
                local_std = np.std(diff)

            if abs(diff[i]) > threshold * local_std:
                # 연속 변화점 방지
                if not change_points or i - change_points[-1] > window:
                    change_points.append(i)

        return change_points

    def exponential_smoothing(self,
                              data: Union[np.ndarray, list],
                              alpha: float = 0.3) -> np.ndarray:
        """
        지수 평활 (Exponential Smoothing)

        Args:
            data: 입력 데이터
            alpha: 평활 계수 (0-1)

        Returns:
            np.ndarray: 평활된 데이터
        """
        data = np.asarray(data, dtype=float)
        smoothed = np.zeros_like(data)
        smoothed[0] = data[0]

        for i in range(1, len(data)):
            smoothed[i] = alpha * data[i] + (1 - alpha) * smoothed[i - 1]

        return smoothed

    def double_exponential_smoothing(self,
                                     data: Union[np.ndarray, list],
                                     alpha: float = 0.3,
                                     beta: float = 0.1) -> Tuple[np.ndarray, np.ndarray]:
        """
        이중 지수 평활 (Holt's Method)

        트렌드를 포함한 예측에 사용됩니다.

        Args:
            data: 입력 데이터
            alpha: 레벨 평활 계수
            beta: 트렌드 평활 계수

        Returns:
            Tuple[np.ndarray, np.ndarray]: (평활 데이터, 트렌드)
        """
        data = np.asarray(data, dtype=float)
        n = len(data)

        level = np.zeros(n)
        trend = np.zeros(n)

        # 초기화
        level[0] = data[0]
        trend[0] = data[1] - data[0] if n > 1 else 0

        for i in range(1, n):
            level[i] = alpha * data[i] + (1 - alpha) * (level[i - 1] + trend[i - 1])
            trend[i] = beta * (level[i] - level[i - 1]) + (1 - beta) * trend[i - 1]

        smoothed = level + trend

        return smoothed, trend

    def forecast(self,
                 data: Union[np.ndarray, list],
                 steps: int = 10,
                 method: str = 'linear') -> np.ndarray:
        """
        예측

        Args:
            data: 입력 데이터
            steps: 예측 스텝 수
            method: 예측 방법 ('linear', 'exponential', 'holt')

        Returns:
            np.ndarray: 예측 값
        """
        data = np.asarray(data, dtype=float)
        n = len(data)

        if method == 'linear':
            result = self.analyze(data)
            future_times = np.arange(n, n + steps)
            forecast_values = result.slope * future_times + result.intercept

        elif method == 'exponential':
            smoothed = self.exponential_smoothing(data)
            # 마지막 값을 유지
            forecast_values = np.full(steps, smoothed[-1])

        elif method == 'holt':
            level, trend = self.double_exponential_smoothing(data)
            # 마지막 레벨과 트렌드로 예측
            forecast_values = np.array([
                level[-1] + (i + 1) * trend[-1]
                for i in range(steps)
            ])

        else:
            raise ValueError(f"지원하지 않는 예측 방법: {method}")

        return forecast_values

    def seasonal_decompose(self,
                           data: Union[np.ndarray, list],
                           period: int) -> Dict[str, np.ndarray]:
        """
        계절성 분해 (간단한 방법)

        Args:
            data: 입력 데이터
            period: 주기

        Returns:
            Dict: {'trend': ..., 'seasonal': ..., 'residual': ...}
        """
        data = np.asarray(data, dtype=float)
        n = len(data)

        if n < 2 * period:
            return {
                "trend": data.copy(),
                "seasonal": np.zeros_like(data),
                "residual": np.zeros_like(data),
            }

        # 이동 평균으로 트렌드 추출
        trend = np.zeros(n)
        half_period = period // 2

        for i in range(n):
            start = max(0, i - half_period)
            end = min(n, i + half_period + 1)
            trend[i] = np.mean(data[start:end])

        # 계절성 성분
        detrended = data - trend
        seasonal = np.zeros(n)

        # 각 주기 위치의 평균
        seasonal_pattern = np.zeros(period)
        for i in range(period):
            indices = np.arange(i, n, period)
            seasonal_pattern[i] = np.mean(detrended[indices])

        # 계절성 패턴 적용
        for i in range(n):
            seasonal[i] = seasonal_pattern[i % period]

        # 잔차
        residual = data - trend - seasonal

        return {
            "trend": trend,
            "seasonal": seasonal,
            "residual": residual,
        }
