"""
헬퍼 함수 모듈

측정 및 분석에 유용한 유틸리티 함수들을 제공합니다.
"""

from typing import Optional, Tuple, Union, List
import numpy as np


def generate_test_signal(signal_type: str = 'sine',
                         frequency: float = 100.0,
                         amplitude: float = 1.0,
                         duration: float = 1.0,
                         sampling_rate: float = 10000.0,
                         phase: float = 0.0,
                         dc_offset: float = 0.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    테스트 신호 생성

    Args:
        signal_type: 신호 유형 ('sine', 'square', 'triangle', 'sawtooth', 'pulse')
        frequency: 주파수 (Hz)
        amplitude: 진폭
        duration: 지속 시간 (초)
        sampling_rate: 샘플링 레이트 (Hz)
        phase: 위상 (라디안)
        dc_offset: DC 오프셋

    Returns:
        Tuple[np.ndarray, np.ndarray]: (타임스탬프, 신호)
    """
    n_samples = int(duration * sampling_rate)
    timestamps = np.arange(n_samples) / sampling_rate
    t = 2 * np.pi * frequency * timestamps + phase

    if signal_type == 'sine':
        signal = amplitude * np.sin(t) + dc_offset

    elif signal_type == 'square':
        signal = amplitude * np.sign(np.sin(t)) + dc_offset

    elif signal_type == 'triangle':
        signal = amplitude * (2 * np.abs(2 * (t / (2 * np.pi) - np.floor(t / (2 * np.pi) + 0.5))) - 1) + dc_offset

    elif signal_type == 'sawtooth':
        signal = amplitude * (2 * (t / (2 * np.pi) - np.floor(t / (2 * np.pi) + 0.5))) + dc_offset

    elif signal_type == 'pulse':
        duty_cycle = 0.1
        signal = amplitude * (np.sin(t) > np.cos(np.pi * duty_cycle)).astype(float) + dc_offset

    elif signal_type == 'chirp':
        # 처프 신호 (주파수 스윕)
        end_freq = frequency * 10
        signal = amplitude * np.sin(2 * np.pi * (frequency + (end_freq - frequency) * timestamps / duration / 2) * timestamps) + dc_offset

    else:
        raise ValueError(f"지원하지 않는 신호 유형: {signal_type}")

    return timestamps, signal


def add_noise(signal: np.ndarray,
              noise_type: str = 'gaussian',
              snr_db: Optional[float] = None,
              noise_level: float = 0.1) -> np.ndarray:
    """
    노이즈 추가

    Args:
        signal: 원본 신호
        noise_type: 노이즈 유형 ('gaussian', 'uniform', 'pink', 'impulse')
        snr_db: 신호 대 잡음비 (dB), None이면 noise_level 사용
        noise_level: 노이즈 레벨 (신호 표준편차의 배수)

    Returns:
        np.ndarray: 노이즈가 추가된 신호
    """
    signal = np.asarray(signal)

    # SNR로 노이즈 레벨 결정
    if snr_db is not None:
        signal_power = np.mean(signal ** 2)
        noise_power = signal_power / (10 ** (snr_db / 10))
        noise_std = np.sqrt(noise_power)
    else:
        noise_std = np.std(signal) * noise_level

    if noise_type == 'gaussian':
        noise = np.random.normal(0, noise_std, len(signal))

    elif noise_type == 'uniform':
        noise = np.random.uniform(-noise_std * np.sqrt(3), noise_std * np.sqrt(3), len(signal))

    elif noise_type == 'pink':
        # 핑크 노이즈 (1/f 노이즈) 근사
        white = np.random.normal(0, noise_std, len(signal))
        # 간단한 적분 필터로 핑크 노이즈 근사
        b = np.array([0.049922035, -0.095993537, 0.050612699, -0.004408786])
        a = np.array([1, -2.494956002, 2.017265875, -0.522189400])
        noise = np.zeros_like(white)
        for i in range(len(white)):
            noise[i] = white[i]
            for j in range(1, min(i + 1, len(b))):
                noise[i] += b[j] * white[i - j]
            for j in range(1, min(i + 1, len(a))):
                noise[i] -= a[j] * noise[i - j]

    elif noise_type == 'impulse':
        # 임펄스 노이즈 (스파이크)
        noise = np.zeros(len(signal))
        n_impulses = int(len(signal) * 0.01)
        impulse_indices = np.random.choice(len(signal), n_impulses, replace=False)
        noise[impulse_indices] = np.random.choice([-1, 1], n_impulses) * noise_std * 10

    else:
        raise ValueError(f"지원하지 않는 노이즈 유형: {noise_type}")

    return signal + noise


def generate_calibration_signal(n_points: int = 10,
                                range_min: float = 0.0,
                                range_max: float = 10.0,
                                dwell_time: float = 1.0,
                                sampling_rate: float = 1000.0,
                                noise_level: float = 0.001) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    캘리브레이션 신호 생성 (계단형)

    Args:
        n_points: 캘리브레이션 포인트 수
        range_min: 최소값
        range_max: 최대값
        dwell_time: 각 포인트 유지 시간 (초)
        sampling_rate: 샘플링 레이트 (Hz)
        noise_level: 노이즈 레벨

    Returns:
        Tuple: (타임스탬프, 신호, 기준값 배열)
    """
    samples_per_step = int(dwell_time * sampling_rate)
    total_samples = samples_per_step * n_points

    timestamps = np.arange(total_samples) / sampling_rate
    reference_values = np.linspace(range_min, range_max, n_points)

    signal = np.zeros(total_samples)
    for i, ref in enumerate(reference_values):
        start = i * samples_per_step
        end = (i + 1) * samples_per_step
        signal[start:end] = ref

    # 노이즈 추가
    signal = add_noise(signal, noise_level=noise_level)

    return timestamps, signal, reference_values


def resample(signal: np.ndarray,
             original_rate: float,
             target_rate: float) -> np.ndarray:
    """
    리샘플링

    Args:
        signal: 원본 신호
        original_rate: 원본 샘플링 레이트 (Hz)
        target_rate: 목표 샘플링 레이트 (Hz)

    Returns:
        np.ndarray: 리샘플링된 신호
    """
    signal = np.asarray(signal)

    ratio = target_rate / original_rate
    new_length = int(len(signal) * ratio)

    # 선형 보간
    original_indices = np.arange(len(signal))
    new_indices = np.linspace(0, len(signal) - 1, new_length)

    resampled = np.interp(new_indices, original_indices, signal)

    return resampled


def align_signals(signal1: np.ndarray,
                  signal2: np.ndarray,
                  max_lag: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray, int]:
    """
    두 신호 정렬 (상호상관 기반)

    Args:
        signal1: 첫 번째 신호 (기준)
        signal2: 두 번째 신호 (정렬 대상)
        max_lag: 최대 지연 (샘플)

    Returns:
        Tuple: (정렬된 signal1, 정렬된 signal2, 지연 샘플)
    """
    signal1 = np.asarray(signal1)
    signal2 = np.asarray(signal2)

    if max_lag is None:
        max_lag = len(signal1) // 4

    # 상호상관 계산
    correlation = np.correlate(signal1, signal2, mode='full')
    center = len(correlation) // 2

    # 최대 상관 위치 찾기 (max_lag 범위 내)
    search_range = correlation[center - max_lag:center + max_lag + 1]
    lag = np.argmax(search_range) - max_lag

    # 신호 정렬
    if lag > 0:
        aligned1 = signal1[lag:]
        aligned2 = signal2[:len(aligned1)]
    elif lag < 0:
        aligned2 = signal2[-lag:]
        aligned1 = signal1[:len(aligned2)]
    else:
        min_len = min(len(signal1), len(signal2))
        aligned1 = signal1[:min_len]
        aligned2 = signal2[:min_len]

    return aligned1, aligned2, lag


def calculate_delay(signal1: np.ndarray,
                    signal2: np.ndarray,
                    sampling_rate: float = 1.0) -> dict:
    """
    두 신호 간의 지연 계산

    Args:
        signal1: 첫 번째 신호
        signal2: 두 번째 신호
        sampling_rate: 샘플링 레이트 (Hz)

    Returns:
        dict: 지연 정보 (샘플, 시간, 상관계수)
    """
    signal1 = np.asarray(signal1) - np.mean(signal1)
    signal2 = np.asarray(signal2) - np.mean(signal2)

    # 상호상관
    correlation = np.correlate(signal1, signal2, mode='full')
    center = len(correlation) // 2

    # 최대 상관 위치
    max_idx = np.argmax(correlation)
    delay_samples = max_idx - center
    delay_time = delay_samples / sampling_rate

    # 최대 상관 계수 (정규화)
    max_corr = correlation[max_idx]
    norm_factor = np.sqrt(np.sum(signal1 ** 2) * np.sum(signal2 ** 2))
    correlation_coefficient = max_corr / (norm_factor + 1e-10)

    return {
        "delay_samples": delay_samples,
        "delay_time": delay_time,
        "correlation_coefficient": correlation_coefficient,
    }


def normalize(signal: np.ndarray,
              method: str = 'minmax',
              target_range: Tuple[float, float] = (0, 1)) -> np.ndarray:
    """
    신호 정규화

    Args:
        signal: 입력 신호
        method: 정규화 방법 ('minmax', 'zscore', 'rms', 'peak')
        target_range: 목표 범위 (minmax용)

    Returns:
        np.ndarray: 정규화된 신호
    """
    signal = np.asarray(signal, dtype=float)

    if method == 'minmax':
        min_val = np.min(signal)
        max_val = np.max(signal)
        if max_val - min_val == 0:
            return np.zeros_like(signal) + target_range[0]
        normalized = (signal - min_val) / (max_val - min_val)
        normalized = normalized * (target_range[1] - target_range[0]) + target_range[0]

    elif method == 'zscore':
        mean = np.mean(signal)
        std = np.std(signal)
        if std == 0:
            return np.zeros_like(signal)
        normalized = (signal - mean) / std

    elif method == 'rms':
        rms = np.sqrt(np.mean(signal ** 2))
        if rms == 0:
            return signal
        normalized = signal / rms

    elif method == 'peak':
        peak = np.max(np.abs(signal))
        if peak == 0:
            return signal
        normalized = signal / peak

    else:
        raise ValueError(f"지원하지 않는 정규화 방법: {method}")

    return normalized


def db_to_linear(db_value: Union[float, np.ndarray],
                 power: bool = True) -> Union[float, np.ndarray]:
    """
    dB를 선형 값으로 변환

    Args:
        db_value: dB 값
        power: 파워 비율 여부 (False면 진폭 비율)

    Returns:
        선형 값
    """
    if power:
        return 10 ** (db_value / 10)
    else:
        return 10 ** (db_value / 20)


def linear_to_db(linear_value: Union[float, np.ndarray],
                 power: bool = True) -> Union[float, np.ndarray]:
    """
    선형 값을 dB로 변환

    Args:
        linear_value: 선형 값
        power: 파워 비율 여부 (False면 진폭 비율)

    Returns:
        dB 값
    """
    linear_value = np.maximum(linear_value, 1e-10)  # 0 방지

    if power:
        return 10 * np.log10(linear_value)
    else:
        return 20 * np.log10(linear_value)


def calculate_snr(signal: np.ndarray,
                  noise: Optional[np.ndarray] = None,
                  noise_region: Optional[Tuple[int, int]] = None) -> float:
    """
    SNR 계산

    Args:
        signal: 신호 (노이즈 포함)
        noise: 노이즈 신호 (알려진 경우)
        noise_region: 노이즈 영역 인덱스 (start, end)

    Returns:
        float: SNR (dB)
    """
    signal = np.asarray(signal)

    if noise is not None:
        noise = np.asarray(noise)
        signal_power = np.mean(signal ** 2)
        noise_power = np.mean(noise ** 2)
    elif noise_region is not None:
        start, end = noise_region
        noise_power = np.var(signal[start:end])
        signal_power = np.var(signal) - noise_power
        signal_power = max(signal_power, 1e-10)
    else:
        # 노이즈를 고주파 성분으로 추정
        diff = np.diff(signal)
        noise_power = np.var(diff) / 2
        signal_power = np.var(signal) - noise_power
        signal_power = max(signal_power, 1e-10)

    snr = 10 * np.log10(signal_power / (noise_power + 1e-10))
    return snr


def moving_average(signal: np.ndarray, window_size: int) -> np.ndarray:
    """
    이동 평균

    Args:
        signal: 입력 신호
        window_size: 윈도우 크기

    Returns:
        np.ndarray: 이동 평균 신호
    """
    signal = np.asarray(signal)
    kernel = np.ones(window_size) / window_size
    return np.convolve(signal, kernel, mode='same')


def find_zero_crossings(signal: np.ndarray) -> np.ndarray:
    """
    영점 교차 찾기

    Args:
        signal: 입력 신호

    Returns:
        np.ndarray: 영점 교차 인덱스
    """
    signal = np.asarray(signal)
    return np.where(np.diff(np.signbit(signal)))[0]


def estimate_frequency(signal: np.ndarray,
                       sampling_rate: float,
                       method: str = 'zero_crossing') -> float:
    """
    주파수 추정

    Args:
        signal: 입력 신호
        sampling_rate: 샘플링 레이트 (Hz)
        method: 추정 방법 ('zero_crossing', 'fft')

    Returns:
        float: 추정 주파수 (Hz)
    """
    signal = np.asarray(signal)

    if method == 'zero_crossing':
        zero_crossings = find_zero_crossings(signal)
        if len(zero_crossings) < 2:
            return 0.0
        avg_period = np.mean(np.diff(zero_crossings)) * 2 / sampling_rate
        return 1 / avg_period if avg_period > 0 else 0.0

    elif method == 'fft':
        fft = np.abs(np.fft.fft(signal))
        freqs = np.fft.fftfreq(len(signal), 1 / sampling_rate)
        positive_mask = freqs > 0
        peak_idx = np.argmax(fft[positive_mask])
        return freqs[positive_mask][peak_idx]

    else:
        raise ValueError(f"지원하지 않는 방법: {method}")
