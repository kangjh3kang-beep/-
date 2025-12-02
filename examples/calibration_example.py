#!/usr/bin/env python
"""
캘리브레이션 예제

이 예제는 측정 시스템의 캘리브레이션 과정을 보여줍니다.
"""

import numpy as np
import sys
sys.path.insert(0, '..')

from differential_measurement_sdk import (
    CalibrationManager,
    MeasurementChannel,
)
from differential_measurement_sdk.utils import generate_calibration_signal


def main():
    print("=" * 60)
    print("차동측정 SDK - 캘리브레이션 예제")
    print("=" * 60)

    # 1. 캘리브레이션 관리자 생성
    print("\n[1] 캘리브레이션 관리자 설정")
    cal_manager = CalibrationManager()
    channel_id = 0

    # 2. 캘리브레이션 포인트 추가 (시뮬레이션)
    print("\n[2] 캘리브레이션 포인트 추가")

    # 실제 기준값과 측정값 (약간의 오차 포함)
    reference_values = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    # 측정 시스템의 오차: 게인 0.98, 오프셋 0.05
    true_gain = 0.98
    true_offset = 0.05

    for ref in reference_values:
        # 시뮬레이션된 측정값 (오차 포함)
        measured = ref * true_gain + true_offset + np.random.normal(0, 0.01)
        cal_manager.add_calibration_point(channel_id, ref, measured)
        print(f"  기준값: {ref:.2f} V, 측정값: {measured:.4f} V")

    # 3. 캘리브레이션 계수 계산
    print("\n[3] 캘리브레이션 계수 계산")
    params = cal_manager.calculate_calibration(channel_id, method='linear')

    print(f"  - 게인 보정 계수: {params['gain']:.6f}")
    print(f"  - 오프셋 보정 계수: {params['offset']:.6f}")
    print(f"  - 선형성 오차: {params['linearity_error']:.4f}%")
    print(f"  - 측정 불확도: {params['uncertainty']:.6f}")

    # 4. 보정 적용 테스트
    print("\n[4] 보정 적용 테스트")

    # 새로운 측정값 (미보정)
    test_measured = np.array([0.05, 1.03, 2.01, 5.00, 9.88])
    test_expected = np.array([0.0, 1.0, 2.0, 5.0, 10.0])

    corrected = cal_manager.apply_calibration(channel_id, test_measured)

    print("  측정값 -> 보정값 (예상값)")
    for m, c, e in zip(test_measured, corrected, test_expected):
        error = abs(c - e)
        print(f"  {m:.4f} V -> {c:.4f} V (예상: {e:.2f} V, 오차: {error:.4f} V)")

    # 5. 온도 보상 설정
    print("\n[5] 온도 보상 설정")
    temp_coeff = 50  # 50 ppm/°C
    cal_manager.set_temperature_coefficient(channel_id, temp_coeff)

    # 다른 온도에서의 보정
    reference_temp = 25.0
    test_temp = 35.0

    corrected_25 = cal_manager.apply_calibration(channel_id, 5.0, temperature=reference_temp)
    corrected_35 = cal_manager.apply_calibration(channel_id, 5.0, temperature=test_temp)

    print(f"  - 온도 계수: {temp_coeff} ppm/°C")
    print(f"  - 기준 온도 ({reference_temp}°C) 보정값: {corrected_25:.6f} V")
    print(f"  - 테스트 온도 ({test_temp}°C) 보정값: {corrected_35:.6f} V")
    print(f"  - 온도 보상 차이: {(corrected_35 - corrected_25) * 1e6:.2f} µV")

    # 6. 캘리브레이션 인증서 생성
    print("\n[6] 캘리브레이션 인증서 생성")
    cert = cal_manager.generate_certificate(
        channel_id=channel_id,
        certificate_id="CAL-2024-001",
        validity_days=365,
        technician="측정기술팀",
        notes="정기 캘리브레이션"
    )

    print(f"  - 인증서 ID: {cert.certificate_id}")
    print(f"  - 캘리브레이션 일자: {cert.calibration_date.strftime('%Y-%m-%d')}")
    print(f"  - 유효 기간: {cert.expiry_date.strftime('%Y-%m-%d')}")
    print(f"  - 유효 여부: {'유효' if cert.is_valid() else '만료'}")
    print(f"  - 포인트 수: {len(cert.points)}")
    print(f"  - 게인: {cert.gain:.6f}")
    print(f"  - 오프셋: {cert.offset:.6f}")
    print(f"  - 선형성 오차: {cert.linearity_error:.4f}%")
    print(f"  - 불확도: {cert.uncertainty:.6f}")

    # 7. 캘리브레이션 데이터 내보내기
    print("\n[7] 캘리브레이션 데이터 내보내기")
    cal_manager.export_calibration(channel_id, "calibration_data.json")
    print("  - 저장 완료: calibration_data.json")

    print("\n" + "=" * 60)
    print("캘리브레이션 예제 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
