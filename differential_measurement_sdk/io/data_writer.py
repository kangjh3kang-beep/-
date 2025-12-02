"""
데이터 쓰기 모듈

측정 데이터를 다양한 형식으로 저장합니다.
"""

from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import numpy as np
import json
import csv
from datetime import datetime


class DataWriter:
    """
    데이터 라이터

    측정 데이터를 다양한 형식으로 저장합니다.

    지원 형식:
    - CSV
    - JSON
    - NumPy (.npy, .npz)
    - 바이너리
    - MATLAB (.mat) - scipy 필요

    Example:
        >>> writer = DataWriter()
        >>> data = {'ch1': np.array([1, 2, 3]), 'ch2': np.array([4, 5, 6])}
        >>> writer.write_csv("output.csv", data)
    """

    def __init__(self,
                 default_encoding: str = 'utf-8',
                 float_precision: int = 6):
        """
        초기화

        Args:
            default_encoding: 기본 텍스트 인코딩
            float_precision: 부동소수점 정밀도
        """
        self.default_encoding = default_encoding
        self.float_precision = float_precision

    def write(self,
              filepath: str,
              data: Dict[str, np.ndarray],
              metadata: Optional[Dict] = None) -> None:
        """
        파일 형식 자동 감지하여 쓰기

        Args:
            filepath: 파일 경로
            data: {채널명: 데이터} 딕셔너리
            metadata: 메타데이터
        """
        path = Path(filepath)
        suffix = path.suffix.lower()

        if suffix == '.csv':
            self.write_csv(filepath, data, metadata)
        elif suffix == '.json':
            self.write_json(filepath, data, metadata)
        elif suffix == '.npy':
            self.write_numpy(filepath, data)
        elif suffix == '.npz':
            self.write_numpy_archive(filepath, data)
        elif suffix in ['.bin', '.dat']:
            self.write_binary(filepath, data)
        elif suffix == '.mat':
            self.write_matlab(filepath, data, metadata)
        else:
            # 기본값: CSV
            self.write_csv(filepath, data, metadata)

    def write_csv(self,
                  filepath: str,
                  data: Dict[str, np.ndarray],
                  metadata: Optional[Dict] = None,
                  delimiter: str = ',',
                  include_timestamps: bool = False,
                  sampling_rate: float = 1000.0) -> None:
        """
        CSV 파일 쓰기

        Args:
            filepath: 파일 경로
            data: {채널명: 데이터} 딕셔너리
            metadata: 메타데이터 (주석으로 저장)
            delimiter: 구분자
            include_timestamps: 타임스탬프 열 포함 여부
            sampling_rate: 샘플링 레이트 (타임스탬프 생성용)
        """
        if not data:
            return

        channels = list(data.keys())
        arrays = [np.asarray(data[ch]) for ch in channels]

        # 길이 확인
        max_len = max(len(arr) for arr in arrays)

        with open(filepath, 'w', newline='', encoding=self.default_encoding) as f:
            writer = csv.writer(f, delimiter=delimiter)

            # 메타데이터 주석
            if metadata:
                for key, value in metadata.items():
                    f.write(f"# {key}: {value}\n")

            # 헤더
            if include_timestamps:
                headers = ['timestamp'] + channels
            else:
                headers = channels
            writer.writerow(headers)

            # 데이터
            for i in range(max_len):
                row = []
                if include_timestamps:
                    row.append(f"{i / sampling_rate:.{self.float_precision}f}")

                for arr in arrays:
                    if i < len(arr):
                        row.append(f"{arr[i]:.{self.float_precision}g}")
                    else:
                        row.append('')

                writer.writerow(row)

    def write_json(self,
                   filepath: str,
                   data: Dict[str, np.ndarray],
                   metadata: Optional[Dict] = None,
                   indent: int = 2) -> None:
        """
        JSON 파일 쓰기

        Args:
            filepath: 파일 경로
            data: {채널명: 데이터} 딕셔너리
            metadata: 메타데이터
            indent: 들여쓰기
        """
        output = {
            'metadata': metadata or {},
            'data': {},
        }

        # 타임스탬프 추가
        output['metadata']['created'] = datetime.now().isoformat()
        output['metadata']['channels'] = list(data.keys())

        # 데이터 변환 (numpy -> list)
        for key, arr in data.items():
            arr = np.asarray(arr)
            output['data'][key] = arr.tolist()

        with open(filepath, 'w', encoding=self.default_encoding) as f:
            json.dump(output, f, indent=indent, ensure_ascii=False)

    def write_numpy(self,
                    filepath: str,
                    data: Dict[str, np.ndarray]) -> None:
        """
        NumPy .npy 파일 쓰기 (2D 배열로 저장)

        Args:
            filepath: 파일 경로
            data: {채널명: 데이터} 딕셔너리
        """
        # 2D 배열로 결합
        arrays = [np.asarray(data[ch]) for ch in sorted(data.keys())]
        max_len = max(len(arr) for arr in arrays)

        # 길이 맞추기
        padded = []
        for arr in arrays:
            if len(arr) < max_len:
                arr = np.pad(arr, (0, max_len - len(arr)), constant_values=np.nan)
            padded.append(arr)

        combined = np.column_stack(padded)
        np.save(filepath, combined)

    def write_numpy_archive(self,
                            filepath: str,
                            data: Dict[str, np.ndarray],
                            compressed: bool = True) -> None:
        """
        NumPy .npz 파일 쓰기 (채널별 저장)

        Args:
            filepath: 파일 경로
            data: {채널명: 데이터} 딕셔너리
            compressed: 압축 여부
        """
        # 키 이름에서 특수문자 제거
        clean_data = {
            key.replace(' ', '_').replace('-', '_'): np.asarray(val)
            for key, val in data.items()
        }

        if compressed:
            np.savez_compressed(filepath, **clean_data)
        else:
            np.savez(filepath, **clean_data)

    def write_binary(self,
                     filepath: str,
                     data: Dict[str, np.ndarray],
                     dtype: str = 'float64',
                     interleaved: bool = True) -> None:
        """
        바이너리 파일 쓰기

        Args:
            filepath: 파일 경로
            data: {채널명: 데이터} 딕셔너리
            dtype: 데이터 타입
            interleaved: 인터리브드 형식 여부
        """
        arrays = [np.asarray(data[ch]).astype(dtype) for ch in sorted(data.keys())]

        if len(arrays) == 1:
            combined = arrays[0]
        elif interleaved:
            # 인터리브드: [ch0[0], ch1[0], ch0[1], ch1[1], ...]
            max_len = max(len(arr) for arr in arrays)
            combined = np.zeros(max_len * len(arrays), dtype=dtype)
            for i, arr in enumerate(arrays):
                combined[i::len(arrays)][:len(arr)] = arr
        else:
            # 순차적: [ch0[...], ch1[...], ...]
            combined = np.concatenate(arrays)

        combined.tofile(filepath)

    def write_matlab(self,
                     filepath: str,
                     data: Dict[str, np.ndarray],
                     metadata: Optional[Dict] = None) -> None:
        """
        MATLAB .mat 파일 쓰기

        Args:
            filepath: 파일 경로
            data: {채널명: 데이터} 딕셔너리
            metadata: 메타데이터
        """
        try:
            from scipy.io import savemat
        except ImportError:
            raise ImportError(
                "MATLAB 파일 지원을 위해서는 scipy를 설치하세요: pip install scipy"
            )

        mat_data = {}

        # 데이터 저장 (변수명 정리)
        for key, arr in data.items():
            clean_key = key.replace(' ', '_').replace('-', '_')
            mat_data[clean_key] = np.asarray(arr)

        # 메타데이터 저장
        if metadata:
            mat_data['metadata'] = metadata

        savemat(filepath, mat_data)

    def write_hdf5(self,
                   filepath: str,
                   data: Dict[str, np.ndarray],
                   metadata: Optional[Dict] = None,
                   compression: str = 'gzip') -> None:
        """
        HDF5 파일 쓰기

        Args:
            filepath: 파일 경로
            data: {채널명: 데이터} 딕셔너리
            metadata: 메타데이터
            compression: 압축 방식
        """
        try:
            import h5py
        except ImportError:
            raise ImportError(
                "HDF5 파일 지원을 위해서는 h5py를 설치하세요: pip install h5py"
            )

        with h5py.File(filepath, 'w') as f:
            # 메타데이터 저장
            if metadata:
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float)):
                        f.attrs[key] = value

            # 데이터 저장
            for key, arr in data.items():
                f.create_dataset(key, data=np.asarray(arr), compression=compression)

    def export_report(self,
                      filepath: str,
                      data: Dict[str, np.ndarray],
                      statistics: Optional[Dict] = None,
                      title: str = "Measurement Report") -> None:
        """
        측정 리포트 생성 (텍스트 형식)

        Args:
            filepath: 파일 경로
            data: {채널명: 데이터} 딕셔너리
            statistics: 통계 정보
            title: 리포트 제목
        """
        lines = [
            "=" * 60,
            title.center(60),
            "=" * 60,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "-" * 60,
            "Data Summary",
            "-" * 60,
        ]

        for channel, arr in data.items():
            arr = np.asarray(arr)
            lines.extend([
                f"\nChannel: {channel}",
                f"  Samples: {len(arr)}",
                f"  Min: {np.min(arr):.6g}",
                f"  Max: {np.max(arr):.6g}",
                f"  Mean: {np.mean(arr):.6g}",
                f"  Std: {np.std(arr):.6g}",
            ])

        if statistics:
            lines.extend([
                "",
                "-" * 60,
                "Additional Statistics",
                "-" * 60,
            ])
            for key, value in statistics.items():
                if isinstance(value, float):
                    lines.append(f"  {key}: {value:.6g}")
                else:
                    lines.append(f"  {key}: {value}")

        lines.extend([
            "",
            "=" * 60,
            "End of Report".center(60),
            "=" * 60,
        ])

        with open(filepath, 'w', encoding=self.default_encoding) as f:
            f.write('\n'.join(lines))
