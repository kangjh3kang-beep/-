#!/usr/bin/env python
"""
데이터 입출력 예제

이 예제는 다양한 형식으로 데이터를 읽고 쓰는 방법을 보여줍니다.
"""

import numpy as np
import sys
import os
sys.path.insert(0, '..')

from differential_measurement_sdk import DataReader, DataWriter
from differential_measurement_sdk.utils import generate_test_signal


def main():
    print("=" * 60)
    print("차동측정 SDK - 데이터 입출력 예제")
    print("=" * 60)

    # 출력 디렉토리 생성
    output_dir = "output_data"
    os.makedirs(output_dir, exist_ok=True)

    # 1. 테스트 데이터 생성
    print("\n[1] 테스트 데이터 생성")
    sampling_rate = 1000
    duration = 1.0

    timestamps, signal1 = generate_test_signal('sine', frequency=10, sampling_rate=sampling_rate, duration=duration)
    _, signal2 = generate_test_signal('sine', frequency=25, sampling_rate=sampling_rate, duration=duration)
    _, signal3 = generate_test_signal('square', frequency=5, sampling_rate=sampling_rate, duration=duration)

    data = {
        'timestamp': timestamps,
        'channel_1': signal1,
        'channel_2': signal2,
        'channel_3': signal3,
    }

    metadata = {
        'sampling_rate': sampling_rate,
        'duration': duration,
        'description': '테스트 측정 데이터',
        'operator': 'SDK 예제',
    }

    print(f"  - 샘플 수: {len(timestamps)}")
    print(f"  - 채널 수: 3")

    # 2. 데이터 쓰기
    print("\n[2] 데이터 쓰기 (다양한 형식)")
    writer = DataWriter()

    # CSV 형식
    csv_path = os.path.join(output_dir, "measurement.csv")
    writer.write_csv(csv_path, data, metadata, include_timestamps=False)
    print(f"  - CSV 저장: {csv_path}")

    # JSON 형식
    json_path = os.path.join(output_dir, "measurement.json")
    writer.write_json(json_path, data, metadata)
    print(f"  - JSON 저장: {json_path}")

    # NumPy .npy 형식
    npy_path = os.path.join(output_dir, "measurement.npy")
    writer.write_numpy(npy_path, data)
    print(f"  - NPY 저장: {npy_path}")

    # NumPy .npz 형식 (압축)
    npz_path = os.path.join(output_dir, "measurement.npz")
    writer.write_numpy_archive(npz_path, data, compressed=True)
    print(f"  - NPZ 저장 (압축): {npz_path}")

    # 바이너리 형식
    bin_path = os.path.join(output_dir, "measurement.bin")
    writer.write_binary(bin_path, {'channel_1': signal1}, dtype='float32')
    print(f"  - BIN 저장: {bin_path}")

    # 리포트 생성
    report_path = os.path.join(output_dir, "measurement_report.txt")
    writer.export_report(report_path, data, title="측정 데이터 리포트")
    print(f"  - 리포트 저장: {report_path}")

    # 3. 데이터 읽기
    print("\n[3] 데이터 읽기 (다양한 형식)")
    reader = DataReader(default_sampling_rate=sampling_rate)

    # CSV 읽기
    csv_data, csv_info = reader.read_csv(csv_path)
    print(f"\n  CSV 파일 정보:")
    print(f"    - 파일명: {csv_info.filename}")
    print(f"    - 채널: {csv_info.channels}")
    print(f"    - 샘플 수: {csv_info.sample_count}")

    # JSON 읽기
    json_data, json_info = reader.read_json(json_path)
    print(f"\n  JSON 파일 정보:")
    print(f"    - 파일명: {json_info.filename}")
    print(f"    - 채널: {json_info.channels}")
    print(f"    - 메타데이터: {json_info.metadata}")

    # NumPy .npz 읽기
    npz_data, npz_info = reader.read_numpy_archive(npz_path)
    print(f"\n  NPZ 파일 정보:")
    print(f"    - 파일명: {npz_info.filename}")
    print(f"    - 채널: {npz_info.channels}")

    # 자동 형식 감지
    auto_data, auto_info = reader.read(csv_path)
    print(f"\n  자동 형식 감지:")
    print(f"    - 감지된 형식: {auto_info.format}")

    # 4. 데이터 검증
    print("\n[4] 데이터 검증")

    # 원본과 읽은 데이터 비교
    original_ch1 = data['channel_1']
    loaded_ch1 = csv_data.get('channel_1', np.array([]))

    if len(loaded_ch1) > 0:
        max_diff = np.max(np.abs(original_ch1 - loaded_ch1))
        print(f"  - 원본 vs CSV 최대 차이: {max_diff:.10f}")

    loaded_json_ch1 = np.array(json_data.get('channel_1', []))
    if len(loaded_json_ch1) > 0:
        max_diff_json = np.max(np.abs(original_ch1 - loaded_json_ch1))
        print(f"  - 원본 vs JSON 최대 차이: {max_diff_json:.10f}")

    # 5. 파일 정보만 읽기
    print("\n[5] 파일 정보만 읽기 (데이터 로드 없음)")
    info_only = reader.get_file_info(csv_path)
    print(f"  - 파일: {info_only.filename}")
    print(f"  - 형식: {info_only.format}")
    print(f"  - 채널: {info_only.channels}")

    # 6. 파일 크기 비교
    print("\n[6] 파일 크기 비교")
    files = [csv_path, json_path, npy_path, npz_path, bin_path]
    for f in files:
        size = os.path.getsize(f)
        print(f"  - {os.path.basename(f):25s}: {size:,} bytes")

    print("\n" + "=" * 60)
    print("데이터 입출력 예제 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
