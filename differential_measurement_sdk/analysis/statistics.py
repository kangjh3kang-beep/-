"""
통계 분석 모듈

측정 데이터의 통계적 분석을 제공합니다.
"""

from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
import numpy as np


@dataclass
class StatisticsResult:
    """통계 분석 결과"""

    # 기본 통계
    count: int = 0
    mean: float = 0.0
    std: float = 0.0
    variance: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0
    range_value: float = 0.0
    median: float = 0.0

    # 추가 통계
    rms: float = 0.0          # Root Mean Square
    peak_to_peak: float = 0.0  # Peak-to-Peak
    crest_factor: float = 0.0  # Crest Factor (Peak/RMS)
    skewness: float = 0.0      # 왜도
    kurtosis: float = 0.0      # 첨도

    # 백분위수
    percentile_1: float = 0.0
    percentile_5: float = 0.0
    percentile_25: float = 0.0
    percentile_75: float = 0.0
    percentile_95: float = 0.0
    percentile_99: float = 0.0
    iqr: float = 0.0  # Inter-Quartile Range

    # 분포 특성
    histogram_bins: np.ndarray = field(default_factory=lambda: np.array([]))
    histogram_counts: np.ndarray = field(default_factory=lambda: np.array([]))


class StatisticalAnalyzer:
    """
    통계 분석기

    측정 데이터의 다양한 통계적 특성을 분석합니다.

    Example:
        >>> analyzer = StatisticalAnalyzer()
        >>> result = analyzer.analyze(measurement_data)
        >>> print(f"평균: {result.mean}, 표준편차: {result.std}")
    """

    def __init__(self,
                 histogram_bins: int = 50,
                 outlier_method: str = 'iqr',
                 outlier_threshold: float = 1.5):
        """
        초기화

        Args:
            histogram_bins: 히스토그램 빈 개수
            outlier_method: 이상치 검출 방법 ('iqr', 'zscore', 'mad')
            outlier_threshold: 이상치 임계값
        """
        self.histogram_bins = histogram_bins
        self.outlier_method = outlier_method
        self.outlier_threshold = outlier_threshold

    def analyze(self, data: Union[np.ndarray, list]) -> StatisticsResult:
        """
        통계 분석 수행

        Args:
            data: 입력 데이터

        Returns:
            StatisticsResult: 분석 결과
        """
        data = np.asarray(data, dtype=float)
        data = data[~np.isnan(data)]  # NaN 제거

        if len(data) == 0:
            return StatisticsResult()

        # 기본 통계
        count = len(data)
        mean = np.mean(data)
        std = np.std(data, ddof=1) if count > 1 else 0.0
        variance = std ** 2
        min_val = np.min(data)
        max_val = np.max(data)
        range_val = max_val - min_val
        median = np.median(data)

        # 추가 통계
        rms = np.sqrt(np.mean(data ** 2))
        peak_to_peak = max_val - min_val
        crest_factor = max(abs(max_val), abs(min_val)) / (rms + 1e-10)

        # 왜도 (Skewness)
        if std > 0:
            skewness = np.mean(((data - mean) / std) ** 3)
        else:
            skewness = 0.0

        # 첨도 (Kurtosis) - 초과 첨도 (정규분포 = 0)
        if std > 0:
            kurtosis = np.mean(((data - mean) / std) ** 4) - 3
        else:
            kurtosis = 0.0

        # 백분위수
        percentiles = np.percentile(data, [1, 5, 25, 75, 95, 99])
        iqr = percentiles[3] - percentiles[2]

        # 히스토그램
        hist_counts, hist_bins = np.histogram(data, bins=self.histogram_bins)

        return StatisticsResult(
            count=count,
            mean=mean,
            std=std,
            variance=variance,
            min_value=min_val,
            max_value=max_val,
            range_value=range_val,
            median=median,
            rms=rms,
            peak_to_peak=peak_to_peak,
            crest_factor=crest_factor,
            skewness=skewness,
            kurtosis=kurtosis,
            percentile_1=percentiles[0],
            percentile_5=percentiles[1],
            percentile_25=percentiles[2],
            percentile_75=percentiles[3],
            percentile_95=percentiles[4],
            percentile_99=percentiles[5],
            iqr=iqr,
            histogram_bins=hist_bins,
            histogram_counts=hist_counts,
        )

    def detect_outliers(self, data: Union[np.ndarray, list]) -> Tuple[np.ndarray, np.ndarray]:
        """
        이상치 검출

        Args:
            data: 입력 데이터

        Returns:
            Tuple[np.ndarray, np.ndarray]: (정상 데이터, 이상치 인덱스)
        """
        data = np.asarray(data, dtype=float)

        if self.outlier_method == 'iqr':
            q1 = np.percentile(data, 25)
            q3 = np.percentile(data, 75)
            iqr = q3 - q1
            lower = q1 - self.outlier_threshold * iqr
            upper = q3 + self.outlier_threshold * iqr
            outlier_mask = (data < lower) | (data > upper)

        elif self.outlier_method == 'zscore':
            mean = np.mean(data)
            std = np.std(data)
            z_scores = np.abs((data - mean) / (std + 1e-10))
            outlier_mask = z_scores > self.outlier_threshold

        elif self.outlier_method == 'mad':
            # Median Absolute Deviation
            median = np.median(data)
            mad = np.median(np.abs(data - median))
            modified_z = 0.6745 * (data - median) / (mad + 1e-10)
            outlier_mask = np.abs(modified_z) > self.outlier_threshold

        else:
            outlier_mask = np.zeros(len(data), dtype=bool)

        outlier_indices = np.where(outlier_mask)[0]
        clean_data = data[~outlier_mask]

        return clean_data, outlier_indices

    def calculate_uncertainty(self,
                              data: Union[np.ndarray, list],
                              confidence_level: float = 0.95) -> Dict[str, float]:
        """
        측정 불확도 계산

        Args:
            data: 측정 데이터
            confidence_level: 신뢰 수준 (0-1)

        Returns:
            Dict: 불확도 정보
        """
        data = np.asarray(data, dtype=float)
        n = len(data)

        if n < 2:
            return {
                "type_a": 0.0,
                "combined": 0.0,
                "expanded": 0.0,
                "coverage_factor": 0.0,
            }

        mean = np.mean(data)
        std = np.std(data, ddof=1)

        # Type A 불확도 (표준 불확도)
        type_a = std / np.sqrt(n)

        # 커버리지 인자 (정규분포 가정)
        # scipy 없이 근사값 사용

        # t 분포 근사 (자유도가 충분히 크면 z 값에 수렴)
        if n > 30:
            if confidence_level == 0.95:
                k = 1.96
            elif confidence_level == 0.99:
                k = 2.576
            else:
                k = 2.0
        else:
            # 작은 샘플: 간단한 근사
            k = 2.0 + 0.5 / np.sqrt(n)

        # 확장 불확도
        expanded = k * type_a

        return {
            "mean": mean,
            "std": std,
            "type_a": type_a,
            "combined": type_a,  # Type B가 없으므로 동일
            "expanded": expanded,
            "coverage_factor": k,
            "confidence_level": confidence_level,
            "sample_count": n,
        }

    def correlation(self,
                    data1: Union[np.ndarray, list],
                    data2: Union[np.ndarray, list]) -> Dict[str, float]:
        """
        상관관계 분석

        Args:
            data1: 첫 번째 데이터
            data2: 두 번째 데이터

        Returns:
            Dict: 상관관계 정보
        """
        data1 = np.asarray(data1, dtype=float)
        data2 = np.asarray(data2, dtype=float)

        # 길이 맞춤
        min_len = min(len(data1), len(data2))
        data1 = data1[:min_len]
        data2 = data2[:min_len]

        # 피어슨 상관계수
        mean1, mean2 = np.mean(data1), np.mean(data2)
        std1, std2 = np.std(data1), np.std(data2)

        if std1 < 1e-10 or std2 < 1e-10:
            pearson = 0.0
        else:
            pearson = np.mean((data1 - mean1) * (data2 - mean2)) / (std1 * std2)

        # 공분산
        covariance = np.cov(data1, data2)[0, 1]

        # R² (결정계수)
        r_squared = pearson ** 2

        # 스피어만 상관계수 (순위 기반)
        rank1 = np.argsort(np.argsort(data1))
        rank2 = np.argsort(np.argsort(data2))
        d = rank1 - rank2
        n = len(data1)
        spearman = 1 - 6 * np.sum(d ** 2) / (n * (n ** 2 - 1)) if n > 1 else 0.0

        return {
            "pearson": pearson,
            "spearman": spearman,
            "covariance": covariance,
            "r_squared": r_squared,
        }

    def moving_statistics(self,
                          data: Union[np.ndarray, list],
                          window_size: int = 10) -> Dict[str, np.ndarray]:
        """
        이동 통계 계산

        Args:
            data: 입력 데이터
            window_size: 윈도우 크기

        Returns:
            Dict: 이동 통계 배열들
        """
        data = np.asarray(data, dtype=float)
        n = len(data)

        if n < window_size:
            window_size = n

        moving_mean = np.zeros(n)
        moving_std = np.zeros(n)
        moving_min = np.zeros(n)
        moving_max = np.zeros(n)

        for i in range(n):
            start = max(0, i - window_size + 1)
            window = data[start:i + 1]
            moving_mean[i] = np.mean(window)
            moving_std[i] = np.std(window) if len(window) > 1 else 0
            moving_min[i] = np.min(window)
            moving_max[i] = np.max(window)

        return {
            "mean": moving_mean,
            "std": moving_std,
            "min": moving_min,
            "max": moving_max,
        }

    def normality_test(self, data: Union[np.ndarray, list]) -> Dict[str, float]:
        """
        정규성 검정 (간단한 방법)

        Args:
            data: 입력 데이터

        Returns:
            Dict: 정규성 검정 결과
        """
        data = np.asarray(data, dtype=float)
        stats_result = self.analyze(data)

        # Jarque-Bera 통계량 (근사)
        n = len(data)
        s = stats_result.skewness  # 왜도
        k = stats_result.kurtosis  # 초과 첨도

        jb_stat = n / 6 * (s ** 2 + k ** 2 / 4)

        # 정규분포에서는 JB 통계량이 작아야 함
        # chi-square(2) 분포의 95% 임계값 ≈ 5.99
        is_normal = jb_stat < 5.99

        return {
            "jarque_bera": jb_stat,
            "skewness": s,
            "kurtosis": k,
            "is_normal_95": is_normal,
            "critical_value_95": 5.99,
        }
