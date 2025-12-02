"""
노이즈 필터 모듈

다양한 노이즈 제거 알고리즘을 제공합니다.
"""

from typing import Optional, Tuple, Union
from enum import Enum
import numpy as np


class NoiseFilterType(Enum):
    """노이즈 필터 유형"""
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL = "exponential"
    MEDIAN = "median"
    GAUSSIAN = "gaussian"
    SAVGOL = "savgol"
    KALMAN = "kalman"
    WIENER = "wiener"


class NoiseFilter:
    """
    노이즈 필터 클래스

    다양한 노이즈 제거 알고리즘을 제공합니다.

    Example:
        >>> nf = NoiseFilter(NoiseFilterType.MOVING_AVERAGE, window_size=5)
        >>> filtered = nf.apply(noisy_signal)
    """

    def __init__(self,
                 filter_type: NoiseFilterType = NoiseFilterType.MOVING_AVERAGE,
                 window_size: int = 5,
                 **kwargs):
        """
        초기화

        Args:
            filter_type: 필터 유형
            window_size: 윈도우 크기
            **kwargs: 필터별 추가 파라미터
        """
        self.filter_type = filter_type
        self.window_size = window_size
        self.kwargs = kwargs

        # 지수 필터 파라미터
        self.alpha = kwargs.get('alpha', 0.3)

        # Savitzky-Golay 필터 파라미터
        self.polyorder = kwargs.get('polyorder', 2)

        # 칼만 필터 상태
        self._kalman_state: Optional[float] = None
        self._kalman_covariance: float = 1.0
        self._kalman_process_noise = kwargs.get('process_noise', 0.01)
        self._kalman_measurement_noise = kwargs.get('measurement_noise', 0.1)

    def apply(self, data: Union[np.ndarray, list]) -> np.ndarray:
        """
        필터 적용

        Args:
            data: 입력 신호

        Returns:
            np.ndarray: 필터링된 신호
        """
        data = np.asarray(data, dtype=float)

        if len(data) == 0:
            return data

        if self.filter_type == NoiseFilterType.MOVING_AVERAGE:
            return self._moving_average(data)
        elif self.filter_type == NoiseFilterType.EXPONENTIAL:
            return self._exponential(data)
        elif self.filter_type == NoiseFilterType.MEDIAN:
            return self._median(data)
        elif self.filter_type == NoiseFilterType.GAUSSIAN:
            return self._gaussian(data)
        elif self.filter_type == NoiseFilterType.SAVGOL:
            return self._savgol(data)
        elif self.filter_type == NoiseFilterType.KALMAN:
            return self._kalman(data)
        elif self.filter_type == NoiseFilterType.WIENER:
            return self._wiener(data)
        else:
            return data

    def _moving_average(self, data: np.ndarray) -> np.ndarray:
        """이동 평균 필터"""
        kernel = np.ones(self.window_size) / self.window_size
        # 양쪽 끝 처리를 위해 'same' 모드 사용
        filtered = np.convolve(data, kernel, mode='same')

        # 경계 보정
        half_win = self.window_size // 2
        for i in range(half_win):
            filtered[i] = np.mean(data[:i + half_win + 1])
            filtered[-(i + 1)] = np.mean(data[-(i + half_win + 1):])

        return filtered

    def _exponential(self, data: np.ndarray) -> np.ndarray:
        """지수 이동 평균 필터"""
        filtered = np.zeros_like(data)
        filtered[0] = data[0]

        for i in range(1, len(data)):
            filtered[i] = self.alpha * data[i] + (1 - self.alpha) * filtered[i - 1]

        return filtered

    def _median(self, data: np.ndarray) -> np.ndarray:
        """중앙값 필터 (스파이크 노이즈 제거에 효과적)"""
        filtered = np.zeros_like(data)
        half_win = self.window_size // 2

        for i in range(len(data)):
            start = max(0, i - half_win)
            end = min(len(data), i + half_win + 1)
            filtered[i] = np.median(data[start:end])

        return filtered

    def _gaussian(self, data: np.ndarray) -> np.ndarray:
        """가우시안 필터"""
        sigma = self.kwargs.get('sigma', self.window_size / 4)

        # 가우시안 커널 생성
        x = np.arange(-self.window_size // 2 + 1, self.window_size // 2 + 1)
        kernel = np.exp(-x ** 2 / (2 * sigma ** 2))
        kernel = kernel / np.sum(kernel)

        filtered = np.convolve(data, kernel, mode='same')
        return filtered

    def _savgol(self, data: np.ndarray) -> np.ndarray:
        """Savitzky-Golay 필터 (스무딩하면서 피크 보존)"""
        window = self.window_size
        if window % 2 == 0:
            window += 1  # 홀수여야 함

        order = min(self.polyorder, window - 1)

        # 간단한 구현
        half_win = window // 2
        filtered = np.zeros_like(data)

        for i in range(len(data)):
            start = max(0, i - half_win)
            end = min(len(data), i + half_win + 1)
            segment = data[start:end]

            if len(segment) > order:
                x = np.arange(len(segment))
                coeffs = np.polyfit(x, segment, order)
                center_idx = i - start
                filtered[i] = np.polyval(coeffs, center_idx)
            else:
                filtered[i] = data[i]

        return filtered

    def _kalman(self, data: np.ndarray) -> np.ndarray:
        """칼만 필터 (예측 기반 노이즈 제거)"""
        Q = self._kalman_process_noise
        R = self._kalman_measurement_noise

        # 초기화
        x = data[0]  # 상태 추정값
        P = 1.0  # 추정 오차 공분산

        filtered = np.zeros_like(data)
        filtered[0] = x

        for i in range(1, len(data)):
            # 예측 단계
            x_pred = x
            P_pred = P + Q

            # 업데이트 단계
            K = P_pred / (P_pred + R)  # 칼만 이득
            x = x_pred + K * (data[i] - x_pred)
            P = (1 - K) * P_pred

            filtered[i] = x

        return filtered

    def _wiener(self, data: np.ndarray) -> np.ndarray:
        """위너 필터"""
        noise_power = self.kwargs.get('noise_power', None)

        if noise_power is None:
            # 노이즈 파워 추정 (신호의 표준편차 기반)
            noise_power = np.var(np.diff(data)) / 2

        signal_power = np.var(data)

        # 간단한 위너 필터 구현
        # H(f) = S(f) / (S(f) + N(f))
        snr = signal_power / (noise_power + 1e-10)
        gain = snr / (snr + 1)

        # 주파수 도메인에서 필터링
        fft_data = np.fft.fft(data)
        filtered_fft = fft_data * gain
        filtered = np.real(np.fft.ifft(filtered_fft))

        return filtered

    def reset(self) -> None:
        """필터 상태 초기화"""
        self._kalman_state = None
        self._kalman_covariance = 1.0

    def estimate_noise_level(self, data: np.ndarray) -> dict:
        """
        노이즈 레벨 추정

        Args:
            data: 입력 신호

        Returns:
            dict: 노이즈 추정 정보
        """
        data = np.asarray(data)

        # 1차 차분을 이용한 노이즈 추정
        diff = np.diff(data)
        noise_std = np.std(diff) / np.sqrt(2)

        # MAD (Median Absolute Deviation) 기반 추정
        median = np.median(data)
        mad = np.median(np.abs(data - median))
        noise_mad = mad * 1.4826  # 가우시안 분포 가정

        # SNR 추정
        signal_power = np.var(data)
        noise_power = noise_std ** 2
        snr_db = 10 * np.log10(signal_power / (noise_power + 1e-10))

        return {
            "noise_std": noise_std,
            "noise_mad": noise_mad,
            "signal_power": signal_power,
            "noise_power": noise_power,
            "snr_db": snr_db,
        }


class AdaptiveFilter:
    """
    적응형 필터 클래스

    LMS (Least Mean Squares) 및 RLS (Recursive Least Squares) 알고리즘을 제공합니다.
    노이즈 특성이 시간에 따라 변하는 경우에 효과적입니다.

    Example:
        >>> af = AdaptiveFilter(order=10, algorithm='lms')
        >>> # 참조 노이즈가 있는 경우
        >>> filtered = af.apply(primary_signal, reference_noise)
    """

    def __init__(self,
                 order: int = 10,
                 algorithm: str = 'lms',
                 mu: float = 0.01,
                 delta: float = 1.0,
                 lambda_: float = 0.99):
        """
        초기화

        Args:
            order: 필터 차수
            algorithm: 알고리즘 ('lms', 'nlms', 'rls')
            mu: 학습률 (LMS/NLMS)
            delta: 정규화 상수 (NLMS)
            lambda_: 망각 계수 (RLS)
        """
        self.order = order
        self.algorithm = algorithm.lower()
        self.mu = mu
        self.delta = delta
        self.lambda_ = lambda_

        # 필터 가중치
        self.weights = np.zeros(order)

        # RLS 용 파라미터
        self._P = np.eye(order) / delta

    def apply(self,
              primary: np.ndarray,
              reference: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        적응형 필터 적용

        Args:
            primary: 기본 신호 (신호 + 노이즈)
            reference: 참조 신호 (노이즈와 상관관계 있는 신호)

        Returns:
            Tuple[np.ndarray, np.ndarray]: (필터링된 신호, 에러 신호)
        """
        primary = np.asarray(primary)
        reference = np.asarray(reference)

        n_samples = min(len(primary), len(reference))
        output = np.zeros(n_samples)
        error = np.zeros(n_samples)

        # 참조 신호 버퍼
        ref_buffer = np.zeros(self.order)

        for i in range(n_samples):
            # 버퍼 업데이트
            ref_buffer = np.roll(ref_buffer, 1)
            ref_buffer[0] = reference[i]

            # 필터 출력 계산
            y = np.dot(self.weights, ref_buffer)

            # 에러 계산 (원하는 신호 = primary - 추정 노이즈)
            e = primary[i] - y
            error[i] = e
            output[i] = e  # 필터링된 출력

            # 가중치 업데이트
            if self.algorithm == 'lms':
                self.weights = self.weights + self.mu * e * ref_buffer

            elif self.algorithm == 'nlms':
                norm = np.dot(ref_buffer, ref_buffer) + self.delta
                self.weights = self.weights + (self.mu / norm) * e * ref_buffer

            elif self.algorithm == 'rls':
                # RLS 알고리즘
                k = np.dot(self._P, ref_buffer)
                k = k / (self.lambda_ + np.dot(ref_buffer, k))
                self.weights = self.weights + k * e
                self._P = (self._P - np.outer(k, np.dot(ref_buffer, self._P))) / self.lambda_

        return output, error

    def apply_single(self, primary_sample: float, reference_sample: float,
                     ref_buffer: np.ndarray) -> Tuple[float, float, np.ndarray]:
        """
        단일 샘플 적응형 필터링 (실시간 처리용)

        Args:
            primary_sample: 기본 신호 샘플
            reference_sample: 참조 신호 샘플
            ref_buffer: 참조 신호 버퍼

        Returns:
            Tuple: (필터링된 출력, 에러, 업데이트된 버퍼)
        """
        # 버퍼 업데이트
        ref_buffer = np.roll(ref_buffer, 1)
        ref_buffer[0] = reference_sample

        # 필터 출력
        y = np.dot(self.weights, ref_buffer)
        e = primary_sample - y

        # 가중치 업데이트
        if self.algorithm == 'lms':
            self.weights = self.weights + self.mu * e * ref_buffer
        elif self.algorithm == 'nlms':
            norm = np.dot(ref_buffer, ref_buffer) + self.delta
            self.weights = self.weights + (self.mu / norm) * e * ref_buffer

        return e, e, ref_buffer

    def reset(self) -> None:
        """필터 상태 초기화"""
        self.weights = np.zeros(self.order)
        self._P = np.eye(self.order) / self.delta

    def get_weights(self) -> np.ndarray:
        """현재 필터 가중치 반환"""
        return self.weights.copy()

    def set_weights(self, weights: np.ndarray) -> None:
        """필터 가중치 설정"""
        if len(weights) != self.order:
            raise ValueError(f"가중치 길이가 필터 차수({self.order})와 일치해야 합니다.")
        self.weights = np.asarray(weights)
