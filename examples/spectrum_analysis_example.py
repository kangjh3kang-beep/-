#!/usr/bin/env python
"""
스펙트럼 분석 예제

이 예제는 FFT 기반 주파수 분석 기능을 보여줍니다.
"""

import numpy as np
import sys
sys.path.insert(0, '..')

from differential_measurement_sdk import SpectrumAnalyzer
from differential_measurement_sdk.analysis.spectrum import WindowType, AveragingType
from differential_measurement_sdk.utils import generate_test_signal, add_noise


def main():
    print("=" * 60)
    print("차동측정 SDK - 스펙트럼 분석 예제")
    print("=" * 60)

    # 1. 복합 테스트 신호 생성
    print("\n[1] 복합 테스트 신호 생성")
    sampling_rate = 10000  # 10 kHz
    duration = 1.0

    # 여러 주파수 성분을 가진 신호
    t = np.arange(int(duration * sampling_rate)) / sampling_rate

    signal = (
        1.0 * np.sin(2 * np.pi * 100 * t) +  # 100 Hz (기본파)
        0.3 * np.sin(2 * np.pi * 200 * t) +  # 200 Hz (2차 고조파)
        0.1 * np.sin(2 * np.pi * 300 * t) +  # 300 Hz (3차 고조파)
        0.05 * np.sin(2 * np.pi * 500 * t)   # 500 Hz (5차 고조파)
    )

    # 노이즈 추가
    noisy_signal = add_noise(signal, snr_db=30)

    print(f"  - 샘플링 레이트: {sampling_rate} Hz")
    print(f"  - 신호 길이: {duration} 초")
    print("  - 주파수 성분: 100Hz (1.0), 200Hz (0.3), 300Hz (0.1), 500Hz (0.05)")
    print(f"  - SNR: 30 dB")

    # 2. 기본 스펙트럼 분석
    print("\n[2] 기본 스펙트럼 분석")
    analyzer = SpectrumAnalyzer(
        sampling_rate=sampling_rate,
        window=WindowType.HANNING
    )

    result = analyzer.analyze(noisy_signal)

    print(f"  - FFT 크기: {result.fft_size}")
    print(f"  - 주파수 분해능: {result.resolution:.2f} Hz")
    print(f"  - 주요 주파수: {result.dominant_frequency:.2f} Hz")
    print(f"  - THD (총 고조파 왜곡): {result.thd:.2f}%")
    print(f"  - SNR: {result.snr:.2f} dB")

    # 3. 피크 검출
    print("\n[3] 피크 검출")
    peaks = analyzer.find_peaks(noisy_signal, threshold_db=-40, min_distance_hz=50)

    print(f"  감지된 피크 ({len(peaks)}개):")
    for i, peak in enumerate(peaks[:5]):  # 상위 5개만 표시
        print(f"    {i+1}. {peak['frequency']:.1f} Hz: {peak['magnitude_db']:.1f} dB")

    # 4. Welch PSD 분석
    print("\n[4] Welch 파워 스펙트럼 밀도 분석")
    freqs, psd = analyzer.welch_psd(noisy_signal, segment_length=1024, overlap=0.5)

    # PSD 피크 찾기
    psd_db = 10 * np.log10(psd + 1e-10)
    peak_idx = np.argmax(psd_db[1:]) + 1
    print(f"  - PSD 피크 주파수: {freqs[peak_idx]:.2f} Hz")
    print(f"  - PSD 피크 값: {psd_db[peak_idx]:.2f} dB/Hz")

    # 5. 다양한 윈도우 함수 비교
    print("\n[5] 윈도우 함수 비교")
    windows = [
        WindowType.RECTANGULAR,
        WindowType.HANNING,
        WindowType.HAMMING,
        WindowType.BLACKMAN
    ]

    for win in windows:
        analyzer_win = SpectrumAnalyzer(sampling_rate=sampling_rate, window=win)
        result_win = analyzer_win.analyze(noisy_signal)
        peaks_win = analyzer_win.find_peaks(noisy_signal, threshold_db=-30)
        print(f"  - {win.value:12s}: 주요 주파수 = {result_win.dominant_frequency:.1f} Hz, "
              f"피크 수 = {len(peaks_win)}")

    # 6. 스펙트로그램 분석
    print("\n[6] 스펙트로그램 분석")

    # 주파수가 변하는 신호 (처프)
    t_chirp = np.arange(int(2.0 * sampling_rate)) / sampling_rate
    chirp_signal = np.sin(2 * np.pi * (50 + 100 * t_chirp) * t_chirp)

    times, freqs_spec, specgram = analyzer.spectrogram(
        chirp_signal,
        segment_length=256,
        overlap=0.75
    )

    print(f"  - 시간 범위: {times[0]:.3f} ~ {times[-1]:.3f} 초")
    print(f"  - 주파수 범위: {freqs_spec[0]:.1f} ~ {freqs_spec[-1]:.1f} Hz")
    print(f"  - 스펙트로그램 크기: {specgram.shape}")

    # 7. 평균화 모드 비교
    print("\n[7] 평균화 모드 비교")

    # 여러 세그먼트로 분석
    segment_length = 1000
    n_segments = 5

    for avg_type in [AveragingType.LINEAR, AveragingType.EXPONENTIAL, AveragingType.PEAK_HOLD]:
        analyzer_avg = SpectrumAnalyzer(
            sampling_rate=sampling_rate,
            averaging=avg_type,
            averaging_count=n_segments
        )

        # 여러 세그먼트 분석
        for i in range(n_segments):
            start = i * segment_length
            end = start + segment_length
            segment = noisy_signal[start:end]
            result_avg = analyzer_avg.analyze(segment)

        print(f"  - {avg_type.value:12s}: 주요 주파수 = {result_avg.dominant_frequency:.1f} Hz")
        analyzer_avg.reset_averaging()

    print("\n" + "=" * 60)
    print("스펙트럼 분석 예제 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
