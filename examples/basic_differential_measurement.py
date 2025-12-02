#!/usr/bin/env python
"""
기본 차동측정 예제

이 예제는 차동측정 SDK의 기본 사용법을 보여줍니다.
"""

import numpy as np
import sys
sys.path.insert(0, '..')

from differential_measurement_sdk import (
    DifferentialMeasurement,
    MeasurementChannel,
    NoiseFilter,
    NoiseFilterType,
    SpectrumAnalyzer,
    StatisticalAnalyzer,
)
from differential_measurement_sdk.utils import generate_test_signal, add_noise


def main():
    print("=" * 60)
    print("차동측정 기반 범용분석시스템 SDK - 기본 예제")
    print("=" * 60)

    # 1. 테스트 신호 생성
    print("\n[1] 테스트 신호 생성")
    sampling_rate = 10000  # 10 kHz
    signal_freq = 100  # 100 Hz

    timestamps, clean_signal = generate_test_signal(
        signal_type='sine',
        frequency=signal_freq,
        amplitude=1.0,
        duration=0.5,
        sampling_rate=sampling_rate
    )

    # 공통 모드 노이즈 생성 (양극/음극 채널에 동일하게 추가)
    common_mode_noise = 0.5 * np.sin(2 * np.pi * 60 * timestamps)  # 60Hz 전원 노이즈

    # 양극 채널: 신호 + 공통모드노이즈 + 랜덤노이즈
    positive_signal = clean_signal + common_mode_noise + np.random.normal(0, 0.1, len(timestamps))

    # 음극 채널: 공통모드노이즈 + 랜덤노이즈 (신호 없음)
    negative_signal = common_mode_noise + np.random.normal(0, 0.1, len(timestamps))

    print(f"  - 샘플링 레이트: {sampling_rate} Hz")
    print(f"  - 신호 주파수: {signal_freq} Hz")
    print(f"  - 데이터 포인트: {len(timestamps)}")

    # 2. 측정 채널 설정
    print("\n[2] 측정 채널 설정")
    ch_positive = MeasurementChannel(
        channel_id=0,
        name="CH+ (Positive)",
        sampling_rate=sampling_rate
    )
    ch_positive.set_data(positive_signal, timestamps)

    ch_negative = MeasurementChannel(
        channel_id=1,
        name="CH- (Negative)",
        sampling_rate=sampling_rate
    )
    ch_negative.set_data(negative_signal, timestamps)

    print(f"  - 양극 채널: {ch_positive.name}")
    print(f"  - 음극 채널: {ch_negative.name}")

    # 3. 차동측정 수행
    print("\n[3] 차동측정 수행")
    dm = DifferentialMeasurement(averaging_count=1)
    result = dm.measure(ch_positive, ch_negative)

    print(f"  - CMRR: {result.cmrr_db:.2f} dB")
    print(f"  - SNR 개선: {result.snr_improvement_db:.2f} dB")

    # 4. 노이즈 필터 적용
    print("\n[4] 노이즈 필터 적용")
    noise_filter = NoiseFilter(
        filter_type=NoiseFilterType.MOVING_AVERAGE,
        window_size=5
    )
    filtered_signal = noise_filter.apply(result.differential_signal)

    # 노이즈 레벨 추정
    noise_info = noise_filter.estimate_noise_level(result.differential_signal)
    print(f"  - 필터 유형: 이동 평균 (window=5)")
    print(f"  - 추정 노이즈 표준편차: {noise_info['noise_std']:.6f}")
    print(f"  - 추정 SNR: {noise_info['snr_db']:.2f} dB")

    # 5. 스펙트럼 분석
    print("\n[5] 스펙트럼 분석")
    spectrum_analyzer = SpectrumAnalyzer(sampling_rate=sampling_rate)
    spectrum = spectrum_analyzer.analyze(filtered_signal)

    print(f"  - 주요 주파수: {spectrum.dominant_frequency:.2f} Hz")
    print(f"  - 총 파워: {spectrum.total_power:.6f}")
    print(f"  - THD: {spectrum.thd:.2f}%")
    print(f"  - SNR: {spectrum.snr:.2f} dB")

    # 6. 통계 분석
    print("\n[6] 통계 분석")
    stat_analyzer = StatisticalAnalyzer()
    stats = stat_analyzer.analyze(filtered_signal)

    print(f"  - 평균: {stats.mean:.6f}")
    print(f"  - 표준편차: {stats.std:.6f}")
    print(f"  - RMS: {stats.rms:.6f}")
    print(f"  - Peak-to-Peak: {stats.peak_to_peak:.6f}")
    print(f"  - Crest Factor: {stats.crest_factor:.2f}")

    # 7. 결과 비교
    print("\n[7] 결과 비교")
    original_std = np.std(positive_signal)
    diff_std = np.std(result.differential_signal)
    filtered_std = np.std(filtered_signal)

    print(f"  - 원본 신호 노이즈 (std): {original_std:.6f}")
    print(f"  - 차동 신호 노이즈 (std): {diff_std:.6f}")
    print(f"  - 필터링 후 노이즈 (std): {filtered_std:.6f}")
    print(f"  - 노이즈 감소율: {(1 - filtered_std/original_std) * 100:.1f}%")

    print("\n" + "=" * 60)
    print("예제 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
