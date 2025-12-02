"""
스펙트럼 분석 모듈

FFT 기반 주파수 영역 분석을 제공합니다.
"""

from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np


class WindowType(Enum):
    """윈도우 함수 유형"""
    RECTANGULAR = "rectangular"
    HANNING = "hanning"
    HAMMING = "hamming"
    BLACKMAN = "blackman"
    KAISER = "kaiser"
    FLAT_TOP = "flat_top"


class AveragingType(Enum):
    """평균화 유형"""
    LINEAR = "linear"       # 선형 평균
    EXPONENTIAL = "exponential"  # 지수 평균
    PEAK_HOLD = "peak_hold"  # 피크 홀드


@dataclass
class SpectrumResult:
    """스펙트럼 분석 결과"""

    frequencies: np.ndarray  # 주파수 배열 (Hz)
    magnitude: np.ndarray    # 크기 스펙트럼
    phase: np.ndarray        # 위상 스펙트럼 (rad)
    magnitude_db: np.ndarray  # 크기 스펙트럼 (dB)
    power_spectrum: np.ndarray  # 파워 스펙트럼
    psd: np.ndarray          # 파워 스펙트럼 밀도 (V^2/Hz)

    # 주요 특성
    dominant_frequency: float = 0.0
    total_power: float = 0.0
    thd: float = 0.0  # Total Harmonic Distortion
    snr: float = 0.0  # Signal-to-Noise Ratio

    # 메타데이터
    fft_size: int = 0
    sampling_rate: float = 0.0
    window_type: str = ""
    resolution: float = 0.0  # 주파수 분해능 (Hz)


class SpectrumAnalyzer:
    """
    스펙트럼 분석기

    FFT 기반 주파수 영역 분석을 수행합니다.

    Example:
        >>> analyzer = SpectrumAnalyzer(sampling_rate=10000)
        >>> result = analyzer.analyze(signal)
        >>> print(f"주파수 성분: {result.dominant_frequency} Hz")
    """

    def __init__(self,
                 sampling_rate: float = 1000.0,
                 fft_size: Optional[int] = None,
                 window: WindowType = WindowType.HANNING,
                 overlap: float = 0.5,
                 averaging: AveragingType = AveragingType.LINEAR,
                 averaging_count: int = 1):
        """
        초기화

        Args:
            sampling_rate: 샘플링 레이트 (Hz)
            fft_size: FFT 크기 (None이면 자동)
            window: 윈도우 함수 유형
            overlap: 오버랩 비율 (0-1)
            averaging: 평균화 유형
            averaging_count: 평균화 횟수
        """
        self.sampling_rate = sampling_rate
        self.fft_size = fft_size
        self.window_type = window
        self.overlap = overlap
        self.averaging_type = averaging
        self.averaging_count = averaging_count

        # 평균화용 버퍼
        self._avg_buffer: List[np.ndarray] = []
        self._exp_avg_spectrum: Optional[np.ndarray] = None
        self._peak_hold_spectrum: Optional[np.ndarray] = None

    def _get_window(self, size: int) -> np.ndarray:
        """윈도우 함수 생성"""
        if self.window_type == WindowType.RECTANGULAR:
            return np.ones(size)
        elif self.window_type == WindowType.HANNING:
            return np.hanning(size)
        elif self.window_type == WindowType.HAMMING:
            return np.hamming(size)
        elif self.window_type == WindowType.BLACKMAN:
            return np.blackman(size)
        elif self.window_type == WindowType.KAISER:
            return np.kaiser(size, beta=14)
        elif self.window_type == WindowType.FLAT_TOP:
            # Flat-top 윈도우 (정확한 진폭 측정용)
            n = np.arange(size)
            a0, a1, a2, a3, a4 = 0.21557895, 0.41663158, 0.277263158, 0.083578947, 0.006947368
            return (a0 - a1 * np.cos(2 * np.pi * n / (size - 1))
                    + a2 * np.cos(4 * np.pi * n / (size - 1))
                    - a3 * np.cos(6 * np.pi * n / (size - 1))
                    + a4 * np.cos(8 * np.pi * n / (size - 1)))
        else:
            return np.hanning(size)

    def analyze(self, data: Union[np.ndarray, list]) -> SpectrumResult:
        """
        스펙트럼 분석 수행

        Args:
            data: 입력 신호

        Returns:
            SpectrumResult: 분석 결과
        """
        data = np.asarray(data, dtype=float)

        # FFT 크기 결정
        n = len(data)
        if self.fft_size is None:
            # 2의 거듭제곱으로 올림
            fft_size = 2 ** int(np.ceil(np.log2(n)))
        else:
            fft_size = self.fft_size

        # 윈도우 적용
        window = self._get_window(min(n, fft_size))
        if n < fft_size:
            # 제로 패딩
            windowed = np.zeros(fft_size)
            windowed[:n] = data[:n] * window[:n]
        else:
            windowed = data[:fft_size] * window

        # 윈도우 보정 계수
        window_correction = len(window) / np.sum(window)

        # FFT 수행
        fft_result = np.fft.fft(windowed)

        # 단측 스펙트럼 (양의 주파수만)
        n_freq = fft_size // 2 + 1
        fft_single = fft_result[:n_freq]

        # 주파수 배열
        frequencies = np.fft.fftfreq(fft_size, 1 / self.sampling_rate)[:n_freq]

        # 크기 스펙트럼
        magnitude = np.abs(fft_single) * 2 / fft_size * window_correction
        magnitude[0] /= 2  # DC 성분 보정
        if fft_size % 2 == 0:
            magnitude[-1] /= 2  # Nyquist 성분 보정

        # 위상 스펙트럼
        phase = np.angle(fft_single)

        # 크기 (dB)
        magnitude_db = 20 * np.log10(magnitude + 1e-10)

        # 파워 스펙트럼
        power_spectrum = magnitude ** 2

        # 파워 스펙트럼 밀도 (V^2/Hz)
        freq_resolution = self.sampling_rate / fft_size
        psd = power_spectrum / freq_resolution

        # 평균화 적용
        if self.averaging_count > 1:
            magnitude_db = self._apply_averaging(magnitude_db)

        # 주요 특성 계산
        dominant_idx = np.argmax(magnitude[1:]) + 1  # DC 제외
        dominant_frequency = frequencies[dominant_idx]

        total_power = np.sum(power_spectrum)

        # THD 계산
        thd = self._calculate_thd(frequencies, magnitude, dominant_frequency)

        # SNR 계산
        snr = self._calculate_snr(magnitude, dominant_idx)

        return SpectrumResult(
            frequencies=frequencies,
            magnitude=magnitude,
            phase=phase,
            magnitude_db=magnitude_db,
            power_spectrum=power_spectrum,
            psd=psd,
            dominant_frequency=dominant_frequency,
            total_power=total_power,
            thd=thd,
            snr=snr,
            fft_size=fft_size,
            sampling_rate=self.sampling_rate,
            window_type=self.window_type.value,
            resolution=freq_resolution,
        )

    def _apply_averaging(self, spectrum: np.ndarray) -> np.ndarray:
        """스펙트럼 평균화"""
        if self.averaging_type == AveragingType.LINEAR:
            self._avg_buffer.append(spectrum)
            if len(self._avg_buffer) > self.averaging_count:
                self._avg_buffer.pop(0)
            return np.mean(self._avg_buffer, axis=0)

        elif self.averaging_type == AveragingType.EXPONENTIAL:
            alpha = 2 / (self.averaging_count + 1)
            if self._exp_avg_spectrum is None:
                self._exp_avg_spectrum = spectrum
            else:
                self._exp_avg_spectrum = alpha * spectrum + (1 - alpha) * self._exp_avg_spectrum
            return self._exp_avg_spectrum

        elif self.averaging_type == AveragingType.PEAK_HOLD:
            if self._peak_hold_spectrum is None:
                self._peak_hold_spectrum = spectrum
            else:
                self._peak_hold_spectrum = np.maximum(self._peak_hold_spectrum, spectrum)
            return self._peak_hold_spectrum

        return spectrum

    def _calculate_thd(self, frequencies: np.ndarray, magnitude: np.ndarray,
                       fundamental_freq: float) -> float:
        """
        총 고조파 왜곡률 (THD) 계산

        THD = sqrt(sum(V_harmonic^2)) / V_fundamental * 100%
        """
        if fundamental_freq <= 0:
            return 0.0

        # 기본파 크기
        fund_idx = np.argmin(np.abs(frequencies - fundamental_freq))
        v_fundamental = magnitude[fund_idx]

        if v_fundamental < 1e-10:
            return 0.0

        # 고조파 성분 (2차~10차)
        harmonic_power = 0.0
        for h in range(2, 11):
            harmonic_freq = fundamental_freq * h
            if harmonic_freq >= self.sampling_rate / 2:
                break
            harm_idx = np.argmin(np.abs(frequencies - harmonic_freq))
            harmonic_power += magnitude[harm_idx] ** 2

        thd = np.sqrt(harmonic_power) / v_fundamental * 100
        return thd

    def _calculate_snr(self, magnitude: np.ndarray, signal_idx: int) -> float:
        """
        신호 대 잡음비 (SNR) 계산
        """
        signal_power = magnitude[signal_idx] ** 2

        # 신호 주변 제외한 노이즈 파워
        noise_indices = np.ones(len(magnitude), dtype=bool)
        noise_indices[max(0, signal_idx - 3):min(len(magnitude), signal_idx + 4)] = False
        noise_indices[0] = False  # DC 제외

        if np.sum(noise_indices) > 0:
            noise_power = np.mean(magnitude[noise_indices] ** 2)
        else:
            noise_power = 1e-10

        snr = 10 * np.log10(signal_power / (noise_power + 1e-10))
        return snr

    def welch_psd(self,
                  data: Union[np.ndarray, list],
                  segment_length: Optional[int] = None,
                  overlap: Optional[float] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Welch 방법으로 파워 스펙트럼 밀도 계산

        Args:
            data: 입력 신호
            segment_length: 세그먼트 길이
            overlap: 오버랩 비율

        Returns:
            Tuple[np.ndarray, np.ndarray]: (주파수, PSD)
        """
        data = np.asarray(data, dtype=float)
        n = len(data)

        if segment_length is None:
            segment_length = min(256, n)
        if overlap is None:
            overlap = self.overlap

        step = int(segment_length * (1 - overlap))
        n_segments = (n - segment_length) // step + 1

        if n_segments < 1:
            # 데이터가 너무 짧으면 일반 분석
            result = self.analyze(data)
            return result.frequencies, result.psd

        # 윈도우
        window = self._get_window(segment_length)
        window_power = np.sum(window ** 2)

        # 세그먼트별 PSD 계산 및 평균
        n_freq = segment_length // 2 + 1
        psd_sum = np.zeros(n_freq)

        for i in range(n_segments):
            start = i * step
            segment = data[start:start + segment_length] * window

            fft_result = np.fft.fft(segment)
            psd_segment = np.abs(fft_result[:n_freq]) ** 2

            psd_sum += psd_segment

        # 평균 및 정규화
        psd = psd_sum / n_segments
        psd = psd * 2 / (window_power * self.sampling_rate)
        psd[0] /= 2
        if segment_length % 2 == 0:
            psd[-1] /= 2

        frequencies = np.fft.fftfreq(segment_length, 1 / self.sampling_rate)[:n_freq]

        return frequencies, psd

    def spectrogram(self,
                    data: Union[np.ndarray, list],
                    segment_length: int = 256,
                    overlap: float = 0.75) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        스펙트로그램 계산

        Args:
            data: 입력 신호
            segment_length: 세그먼트 길이
            overlap: 오버랩 비율

        Returns:
            Tuple: (시간 배열, 주파수 배열, 스펙트로그램 (dB))
        """
        data = np.asarray(data, dtype=float)
        n = len(data)

        step = int(segment_length * (1 - overlap))
        n_segments = (n - segment_length) // step + 1

        if n_segments < 1:
            raise ValueError("데이터가 세그먼트 길이보다 짧습니다.")

        window = self._get_window(segment_length)
        n_freq = segment_length // 2 + 1

        specgram = np.zeros((n_freq, n_segments))
        times = np.zeros(n_segments)

        for i in range(n_segments):
            start = i * step
            segment = data[start:start + segment_length] * window

            fft_result = np.fft.fft(segment)
            magnitude = np.abs(fft_result[:n_freq]) * 2 / segment_length

            specgram[:, i] = 20 * np.log10(magnitude + 1e-10)
            times[i] = (start + segment_length / 2) / self.sampling_rate

        frequencies = np.fft.fftfreq(segment_length, 1 / self.sampling_rate)[:n_freq]

        return times, frequencies, specgram

    def find_peaks(self,
                   data: Union[np.ndarray, list],
                   threshold_db: float = -60,
                   min_distance_hz: float = 10) -> List[Dict]:
        """
        스펙트럼 피크 검출

        Args:
            data: 입력 신호
            threshold_db: 임계값 (dB)
            min_distance_hz: 최소 피크 간격 (Hz)

        Returns:
            List[Dict]: 피크 정보 리스트
        """
        result = self.analyze(data)
        frequencies = result.frequencies
        magnitude_db = result.magnitude_db

        # 임계값 이상인 포인트 찾기
        above_threshold = magnitude_db > threshold_db

        # 로컬 최대값 찾기
        peaks = []
        min_distance_bins = int(min_distance_hz * result.fft_size / self.sampling_rate)

        i = 1
        while i < len(magnitude_db) - 1:
            if above_threshold[i]:
                # 로컬 최대값 확인
                if (magnitude_db[i] >= magnitude_db[i - 1] and
                        magnitude_db[i] >= magnitude_db[i + 1]):
                    peaks.append({
                        "frequency": frequencies[i],
                        "magnitude_db": magnitude_db[i],
                        "magnitude": result.magnitude[i],
                        "phase": result.phase[i],
                        "bin_index": i,
                    })
                    i += min_distance_bins
                    continue
            i += 1

        # 크기 순으로 정렬
        peaks.sort(key=lambda x: x["magnitude_db"], reverse=True)

        return peaks

    def reset_averaging(self) -> None:
        """평균화 버퍼 초기화"""
        self._avg_buffer = []
        self._exp_avg_spectrum = None
        self._peak_hold_spectrum = None
