"""
주파수 필터 모듈

저역통과, 고역통과, 대역통과 필터를 제공합니다.
"""

from typing import Optional, Tuple, Union
from enum import Enum
import numpy as np


class FilterDesign(Enum):
    """필터 설계 방법"""
    BUTTERWORTH = "butterworth"
    CHEBYSHEV = "chebyshev"
    BESSEL = "bessel"
    FIR = "fir"


class LowPassFilter:
    """
    저역통과 필터

    특정 차단 주파수 이하의 주파수 성분만 통과시킵니다.

    Example:
        >>> lpf = LowPassFilter(cutoff_freq=100, sampling_rate=1000, order=4)
        >>> filtered = lpf.apply(signal)
    """

    def __init__(self,
                 cutoff_freq: float,
                 sampling_rate: float,
                 order: int = 4,
                 design: FilterDesign = FilterDesign.BUTTERWORTH):
        """
        초기화

        Args:
            cutoff_freq: 차단 주파수 (Hz)
            sampling_rate: 샘플링 레이트 (Hz)
            order: 필터 차수
            design: 필터 설계 방법
        """
        self.cutoff_freq = cutoff_freq
        self.sampling_rate = sampling_rate
        self.order = order
        self.design = design

        # 정규화된 차단 주파수
        self.normalized_cutoff = cutoff_freq / (sampling_rate / 2)

        # 필터 계수 계산
        self._b, self._a = self._design_filter()

        # 필터 상태 (연속 처리용)
        self._zi = np.zeros(max(len(self._a), len(self._b)) - 1)

    def _design_filter(self) -> Tuple[np.ndarray, np.ndarray]:
        """필터 계수 설계"""
        wc = self.normalized_cutoff * np.pi  # 디지털 주파수

        if self.design == FilterDesign.BUTTERWORTH:
            return self._butterworth_lowpass(wc, self.order)
        elif self.design == FilterDesign.FIR:
            return self._fir_lowpass(wc, self.order * 10), np.array([1.0])
        else:
            # 기본값: Butterworth
            return self._butterworth_lowpass(wc, self.order)

    def _butterworth_lowpass(self, wc: float, order: int) -> Tuple[np.ndarray, np.ndarray]:
        """Butterworth 저역통과 필터 설계"""
        # 간단한 1차 IIR 필터로 근사
        # 더 정확한 구현을 위해서는 scipy.signal 사용 권장

        # 단순화된 Butterworth 구현
        alpha = np.tan(wc / 2)

        if order == 1:
            b = np.array([alpha, alpha]) / (1 + alpha)
            a = np.array([1, (alpha - 1) / (alpha + 1)])
        elif order == 2:
            alpha_sq = alpha * alpha
            sqrt2 = np.sqrt(2)
            norm = 1 + sqrt2 * alpha + alpha_sq
            b = np.array([alpha_sq, 2 * alpha_sq, alpha_sq]) / norm
            a = np.array([1,
                          2 * (alpha_sq - 1) / norm,
                          (1 - sqrt2 * alpha + alpha_sq) / norm])
        else:
            # 고차 필터는 2차 필터의 캐스케이드로 구현
            # 여기서는 2차로 제한
            return self._butterworth_lowpass(wc, 2)

        return b, a

    def _fir_lowpass(self, wc: float, tap_count: int) -> np.ndarray:
        """FIR 저역통과 필터 설계 (윈도우 방법)"""
        if tap_count % 2 == 0:
            tap_count += 1

        n = np.arange(tap_count)
        center = tap_count // 2

        # sinc 함수 기반 이상적 저역통과
        h = np.zeros(tap_count)
        for i in range(tap_count):
            if i == center:
                h[i] = wc / np.pi
            else:
                h[i] = np.sin(wc * (i - center)) / (np.pi * (i - center))

        # 해밍 윈도우 적용
        window = 0.54 - 0.46 * np.cos(2 * np.pi * n / (tap_count - 1))
        h = h * window

        # 정규화
        h = h / np.sum(h)

        return h

    def apply(self, data: Union[np.ndarray, list], reset: bool = False) -> np.ndarray:
        """
        필터 적용

        Args:
            data: 입력 신호
            reset: 필터 상태 초기화 여부

        Returns:
            np.ndarray: 필터링된 신호
        """
        data = np.asarray(data, dtype=float)

        if reset:
            self._zi = np.zeros(max(len(self._a), len(self._b)) - 1)

        if len(self._a) == 1:
            # FIR 필터
            return np.convolve(data, self._b, mode='same')
        else:
            # IIR 필터
            return self._iir_filter(data, self._b, self._a)

    def _iir_filter(self, data: np.ndarray, b: np.ndarray, a: np.ndarray) -> np.ndarray:
        """IIR 필터 적용"""
        n = len(data)
        output = np.zeros(n)

        # 과거 입력/출력 버퍼
        x_buf = np.zeros(len(b))
        y_buf = np.zeros(len(a))

        for i in range(n):
            # 입력 버퍼 업데이트
            x_buf = np.roll(x_buf, 1)
            x_buf[0] = data[i]

            # 출력 계산
            y = np.dot(b, x_buf)
            if len(a) > 1:
                y -= np.dot(a[1:], y_buf[:-1])
            y /= a[0]

            # 출력 버퍼 업데이트
            y_buf = np.roll(y_buf, 1)
            y_buf[0] = y

            output[i] = y

        return output

    def get_frequency_response(self, num_points: int = 512) -> Tuple[np.ndarray, np.ndarray]:
        """
        주파수 응답 계산

        Args:
            num_points: 주파수 포인트 수

        Returns:
            Tuple[np.ndarray, np.ndarray]: (주파수 배열 Hz, 크기 응답 dB)
        """
        w = np.linspace(0, np.pi, num_points)
        freqs = w * self.sampling_rate / (2 * np.pi)

        # 주파수 응답 계산
        h = np.zeros(num_points, dtype=complex)
        for i, wi in enumerate(w):
            num = np.sum(self._b * np.exp(-1j * wi * np.arange(len(self._b))))
            den = np.sum(self._a * np.exp(-1j * wi * np.arange(len(self._a))))
            h[i] = num / den

        magnitude_db = 20 * np.log10(np.abs(h) + 1e-10)

        return freqs, magnitude_db

    def reset(self) -> None:
        """필터 상태 초기화"""
        self._zi = np.zeros(max(len(self._a), len(self._b)) - 1)


class HighPassFilter:
    """
    고역통과 필터

    특정 차단 주파수 이상의 주파수 성분만 통과시킵니다.

    Example:
        >>> hpf = HighPassFilter(cutoff_freq=10, sampling_rate=1000, order=4)
        >>> filtered = hpf.apply(signal)
    """

    def __init__(self,
                 cutoff_freq: float,
                 sampling_rate: float,
                 order: int = 4,
                 design: FilterDesign = FilterDesign.BUTTERWORTH):
        """
        초기화

        Args:
            cutoff_freq: 차단 주파수 (Hz)
            sampling_rate: 샘플링 레이트 (Hz)
            order: 필터 차수
            design: 필터 설계 방법
        """
        self.cutoff_freq = cutoff_freq
        self.sampling_rate = sampling_rate
        self.order = order
        self.design = design

        self.normalized_cutoff = cutoff_freq / (sampling_rate / 2)

        self._b, self._a = self._design_filter()
        self._zi = np.zeros(max(len(self._a), len(self._b)) - 1)

    def _design_filter(self) -> Tuple[np.ndarray, np.ndarray]:
        """필터 계수 설계"""
        wc = self.normalized_cutoff * np.pi

        if self.design == FilterDesign.BUTTERWORTH:
            return self._butterworth_highpass(wc, self.order)
        else:
            return self._butterworth_highpass(wc, self.order)

    def _butterworth_highpass(self, wc: float, order: int) -> Tuple[np.ndarray, np.ndarray]:
        """Butterworth 고역통과 필터 설계"""
        alpha = np.tan(wc / 2)

        if order == 1:
            b = np.array([1, -1]) / (1 + alpha)
            a = np.array([1, (alpha - 1) / (alpha + 1)])
        elif order == 2:
            alpha_sq = alpha * alpha
            sqrt2 = np.sqrt(2)
            norm = 1 + sqrt2 * alpha + alpha_sq
            b = np.array([1, -2, 1]) / norm
            a = np.array([1,
                          2 * (alpha_sq - 1) / norm,
                          (1 - sqrt2 * alpha + alpha_sq) / norm])
        else:
            return self._butterworth_highpass(wc, 2)

        return b, a

    def apply(self, data: Union[np.ndarray, list], reset: bool = False) -> np.ndarray:
        """필터 적용"""
        data = np.asarray(data, dtype=float)

        if reset:
            self._zi = np.zeros(max(len(self._a), len(self._b)) - 1)

        return self._iir_filter(data, self._b, self._a)

    def _iir_filter(self, data: np.ndarray, b: np.ndarray, a: np.ndarray) -> np.ndarray:
        """IIR 필터 적용"""
        n = len(data)
        output = np.zeros(n)

        x_buf = np.zeros(len(b))
        y_buf = np.zeros(len(a))

        for i in range(n):
            x_buf = np.roll(x_buf, 1)
            x_buf[0] = data[i]

            y = np.dot(b, x_buf)
            if len(a) > 1:
                y -= np.dot(a[1:], y_buf[:-1])
            y /= a[0]

            y_buf = np.roll(y_buf, 1)
            y_buf[0] = y

            output[i] = y

        return output

    def reset(self) -> None:
        """필터 상태 초기화"""
        self._zi = np.zeros(max(len(self._a), len(self._b)) - 1)


class BandPassFilter:
    """
    대역통과 필터

    특정 주파수 대역의 성분만 통과시킵니다.

    Example:
        >>> bpf = BandPassFilter(low_freq=50, high_freq=150, sampling_rate=1000)
        >>> filtered = bpf.apply(signal)
    """

    def __init__(self,
                 low_freq: float,
                 high_freq: float,
                 sampling_rate: float,
                 order: int = 4):
        """
        초기화

        Args:
            low_freq: 하한 주파수 (Hz)
            high_freq: 상한 주파수 (Hz)
            sampling_rate: 샘플링 레이트 (Hz)
            order: 필터 차수
        """
        self.low_freq = low_freq
        self.high_freq = high_freq
        self.sampling_rate = sampling_rate
        self.order = order

        # 대역통과 = 저역통과 + 고역통과
        self._lpf = LowPassFilter(high_freq, sampling_rate, order)
        self._hpf = HighPassFilter(low_freq, sampling_rate, order)

    def apply(self, data: Union[np.ndarray, list], reset: bool = False) -> np.ndarray:
        """
        필터 적용

        Args:
            data: 입력 신호
            reset: 필터 상태 초기화 여부

        Returns:
            np.ndarray: 필터링된 신호
        """
        data = np.asarray(data, dtype=float)

        if reset:
            self._lpf.reset()
            self._hpf.reset()

        # 저역통과 후 고역통과
        temp = self._lpf.apply(data)
        return self._hpf.apply(temp)

    @property
    def center_frequency(self) -> float:
        """중심 주파수"""
        return np.sqrt(self.low_freq * self.high_freq)

    @property
    def bandwidth(self) -> float:
        """대역폭"""
        return self.high_freq - self.low_freq

    @property
    def q_factor(self) -> float:
        """Q 팩터"""
        return self.center_frequency / self.bandwidth

    def reset(self) -> None:
        """필터 상태 초기화"""
        self._lpf.reset()
        self._hpf.reset()


class NotchFilter:
    """
    노치 필터 (대역제거 필터)

    특정 주파수 대역을 제거합니다. (예: 전원 노이즈 60Hz 제거)

    Example:
        >>> nf = NotchFilter(notch_freq=60, q_factor=30, sampling_rate=1000)
        >>> filtered = nf.apply(signal)
    """

    def __init__(self,
                 notch_freq: float,
                 q_factor: float,
                 sampling_rate: float):
        """
        초기화

        Args:
            notch_freq: 제거할 주파수 (Hz)
            q_factor: Q 팩터 (높을수록 좁은 대역)
            sampling_rate: 샘플링 레이트 (Hz)
        """
        self.notch_freq = notch_freq
        self.q_factor = q_factor
        self.sampling_rate = sampling_rate

        # 필터 계수 계산
        self._b, self._a = self._design_notch()

    def _design_notch(self) -> Tuple[np.ndarray, np.ndarray]:
        """노치 필터 설계"""
        w0 = 2 * np.pi * self.notch_freq / self.sampling_rate
        bw = w0 / self.q_factor

        # 2차 IIR 노치 필터
        alpha = np.sin(w0) * np.sinh(np.log(2) / 2 * bw * w0 / np.sin(w0))

        b = np.array([1, -2 * np.cos(w0), 1])
        a = np.array([1 + alpha, -2 * np.cos(w0), 1 - alpha])

        # 정규화
        b = b / a[0]
        a = a / a[0]

        return b, a

    def apply(self, data: Union[np.ndarray, list]) -> np.ndarray:
        """필터 적용"""
        data = np.asarray(data, dtype=float)

        n = len(data)
        output = np.zeros(n)

        x_buf = np.zeros(len(self._b))
        y_buf = np.zeros(len(self._a))

        for i in range(n):
            x_buf = np.roll(x_buf, 1)
            x_buf[0] = data[i]

            y = np.dot(self._b, x_buf)
            if len(self._a) > 1:
                y -= np.dot(self._a[1:], y_buf[:-1])

            y_buf = np.roll(y_buf, 1)
            y_buf[0] = y

            output[i] = y

        return output
