"""
데이터 읽기 모듈

다양한 형식의 측정 데이터를 읽어옵니다.
"""

from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np
import json
import csv
from datetime import datetime


@dataclass
class DataInfo:
    """데이터 정보"""
    filename: str = ""
    format: str = ""
    channels: List[str] = field(default_factory=list)
    sample_count: int = 0
    sampling_rate: Optional[float] = None
    start_time: Optional[datetime] = None
    duration: Optional[float] = None
    metadata: dict = field(default_factory=dict)


class DataReader:
    """
    데이터 리더

    다양한 형식의 측정 데이터를 읽어옵니다.

    지원 형식:
    - CSV
    - JSON
    - NumPy (.npy, .npz)
    - 바이너리

    Example:
        >>> reader = DataReader()
        >>> data = reader.read_csv("measurement.csv")
        >>> print(data.keys())
    """

    def __init__(self,
                 default_sampling_rate: float = 1000.0,
                 default_encoding: str = 'utf-8'):
        """
        초기화

        Args:
            default_sampling_rate: 기본 샘플링 레이트
            default_encoding: 기본 텍스트 인코딩
        """
        self.default_sampling_rate = default_sampling_rate
        self.default_encoding = default_encoding

    def read(self, filepath: str) -> Tuple[Dict[str, np.ndarray], DataInfo]:
        """
        파일 형식 자동 감지하여 읽기

        Args:
            filepath: 파일 경로

        Returns:
            Tuple[Dict[str, np.ndarray], DataInfo]: (데이터, 정보)
        """
        path = Path(filepath)
        suffix = path.suffix.lower()

        if suffix == '.csv':
            return self.read_csv(filepath)
        elif suffix == '.json':
            return self.read_json(filepath)
        elif suffix == '.npy':
            return self.read_numpy(filepath)
        elif suffix == '.npz':
            return self.read_numpy_archive(filepath)
        elif suffix in ['.bin', '.dat']:
            return self.read_binary(filepath)
        else:
            # CSV로 시도
            try:
                return self.read_csv(filepath)
            except Exception:
                raise ValueError(f"지원하지 않는 파일 형식: {suffix}")

    def read_csv(self,
                 filepath: str,
                 delimiter: str = ',',
                 has_header: bool = True,
                 skip_rows: int = 0,
                 time_column: Optional[str] = None) -> Tuple[Dict[str, np.ndarray], DataInfo]:
        """
        CSV 파일 읽기

        Args:
            filepath: 파일 경로
            delimiter: 구분자
            has_header: 헤더 여부
            skip_rows: 건너뛸 행 수
            time_column: 시간 열 이름

        Returns:
            Tuple[Dict[str, np.ndarray], DataInfo]: (데이터, 정보)
        """
        path = Path(filepath)

        with open(filepath, 'r', encoding=self.default_encoding) as f:
            # 행 건너뛰기
            for _ in range(skip_rows):
                f.readline()

            reader = csv.reader(f, delimiter=delimiter)

            # 헤더 읽기
            if has_header:
                headers = next(reader)
                headers = [h.strip() for h in headers]
            else:
                first_row = next(reader)
                headers = [f"channel_{i}" for i in range(len(first_row))]
                # 첫 행을 데이터로 다시 처리해야 함
                f.seek(0)
                for _ in range(skip_rows):
                    f.readline()
                reader = csv.reader(f, delimiter=delimiter)

            # 데이터 읽기
            raw_data = []
            for row in reader:
                if row:
                    try:
                        raw_data.append([float(x) for x in row])
                    except ValueError:
                        continue  # 숫자가 아닌 행 건너뛰기

        if not raw_data:
            return {}, DataInfo(filename=path.name, format='csv')

        data_array = np.array(raw_data)

        # 채널별 딕셔너리로 변환
        data = {}
        for i, header in enumerate(headers):
            if i < data_array.shape[1]:
                data[header] = data_array[:, i]

        # 타임스탬프 추출
        timestamps = None
        if time_column and time_column in data:
            timestamps = data[time_column]
            # 샘플링 레이트 추정
            if len(timestamps) > 1:
                dt = np.mean(np.diff(timestamps))
                sampling_rate = 1.0 / dt if dt > 0 else self.default_sampling_rate
            else:
                sampling_rate = self.default_sampling_rate
        else:
            sampling_rate = self.default_sampling_rate

        info = DataInfo(
            filename=path.name,
            format='csv',
            channels=list(data.keys()),
            sample_count=data_array.shape[0],
            sampling_rate=sampling_rate,
            duration=data_array.shape[0] / sampling_rate,
        )

        return data, info

    def read_json(self, filepath: str) -> Tuple[Dict[str, np.ndarray], DataInfo]:
        """
        JSON 파일 읽기

        예상 형식:
        {
            "metadata": {...},
            "data": {
                "channel1": [1, 2, 3, ...],
                "channel2": [1, 2, 3, ...]
            }
        }
        """
        path = Path(filepath)

        with open(filepath, 'r', encoding=self.default_encoding) as f:
            content = json.load(f)

        metadata = content.get('metadata', {})
        raw_data = content.get('data', content)

        # 데이터가 바로 최상위에 있는 경우
        if 'data' not in content and isinstance(content, dict):
            # metadata와 data가 분리되지 않은 형식
            raw_data = {k: v for k, v in content.items()
                        if isinstance(v, list) and all(isinstance(x, (int, float)) for x in v[:10])}
            metadata = {k: v for k, v in content.items() if k not in raw_data}

        # numpy 배열로 변환
        data = {}
        for key, values in raw_data.items():
            if isinstance(values, list):
                data[key] = np.array(values, dtype=float)

        sampling_rate = metadata.get('sampling_rate', self.default_sampling_rate)
        sample_count = max((len(v) for v in data.values()), default=0)

        info = DataInfo(
            filename=path.name,
            format='json',
            channels=list(data.keys()),
            sample_count=sample_count,
            sampling_rate=sampling_rate,
            duration=sample_count / sampling_rate if sampling_rate else None,
            metadata=metadata,
        )

        return data, info

    def read_numpy(self, filepath: str) -> Tuple[Dict[str, np.ndarray], DataInfo]:
        """
        NumPy .npy 파일 읽기
        """
        path = Path(filepath)
        data_array = np.load(filepath)

        # 1D 또는 2D 배열 처리
        if data_array.ndim == 1:
            data = {'channel_0': data_array}
        elif data_array.ndim == 2:
            # 각 열을 채널로 처리
            data = {f'channel_{i}': data_array[:, i]
                    for i in range(data_array.shape[1])}
        else:
            raise ValueError(f"지원하지 않는 배열 차원: {data_array.ndim}")

        sample_count = data_array.shape[0]

        info = DataInfo(
            filename=path.name,
            format='npy',
            channels=list(data.keys()),
            sample_count=sample_count,
            sampling_rate=self.default_sampling_rate,
            duration=sample_count / self.default_sampling_rate,
        )

        return data, info

    def read_numpy_archive(self, filepath: str) -> Tuple[Dict[str, np.ndarray], DataInfo]:
        """
        NumPy .npz 파일 읽기
        """
        path = Path(filepath)
        npz = np.load(filepath)

        data = {key: npz[key] for key in npz.files}

        sample_count = max((len(v) for v in data.values()), default=0)

        info = DataInfo(
            filename=path.name,
            format='npz',
            channels=list(data.keys()),
            sample_count=sample_count,
            sampling_rate=self.default_sampling_rate,
            duration=sample_count / self.default_sampling_rate,
        )

        return data, info

    def read_binary(self,
                    filepath: str,
                    dtype: str = 'float64',
                    channels: int = 1,
                    header_bytes: int = 0) -> Tuple[Dict[str, np.ndarray], DataInfo]:
        """
        바이너리 파일 읽기

        Args:
            filepath: 파일 경로
            dtype: 데이터 타입 ('float64', 'float32', 'int16', etc.)
            channels: 채널 수
            header_bytes: 헤더 바이트 수

        Returns:
            Tuple[Dict[str, np.ndarray], DataInfo]: (데이터, 정보)
        """
        path = Path(filepath)

        with open(filepath, 'rb') as f:
            # 헤더 건너뛰기
            f.seek(header_bytes)
            raw_data = f.read()

        # numpy 배열로 변환
        data_array = np.frombuffer(raw_data, dtype=dtype)

        # 채널별 분리
        if channels > 1:
            # 인터리브드 데이터 가정
            samples = len(data_array) // channels
            data_array = data_array[:samples * channels].reshape(samples, channels)
            data = {f'channel_{i}': data_array[:, i] for i in range(channels)}
        else:
            data = {'channel_0': data_array}

        sample_count = len(data_array) if channels == 1 else data_array.shape[0]

        info = DataInfo(
            filename=path.name,
            format='binary',
            channels=list(data.keys()),
            sample_count=sample_count,
            sampling_rate=self.default_sampling_rate,
            duration=sample_count / self.default_sampling_rate,
            metadata={'dtype': dtype, 'header_bytes': header_bytes},
        )

        return data, info

    def read_tdms(self, filepath: str) -> Tuple[Dict[str, np.ndarray], DataInfo]:
        """
        NI TDMS 파일 읽기 (간단한 파서)

        Note: 완전한 TDMS 지원을 위해서는 nptdms 라이브러리 사용 권장
        """
        raise NotImplementedError(
            "TDMS 파일 지원을 위해서는 nptdms 라이브러리를 설치하세요: pip install nptdms"
        )

    def read_streaming(self,
                       filepath: str,
                       chunk_size: int = 10000,
                       dtype: str = 'float64') -> Any:
        """
        대용량 파일 스트리밍 읽기 (제너레이터)

        Args:
            filepath: 파일 경로
            chunk_size: 청크 크기 (샘플 수)
            dtype: 데이터 타입

        Yields:
            np.ndarray: 데이터 청크
        """
        path = Path(filepath)
        itemsize = np.dtype(dtype).itemsize

        with open(filepath, 'rb') as f:
            while True:
                raw = f.read(chunk_size * itemsize)
                if not raw:
                    break
                chunk = np.frombuffer(raw, dtype=dtype)
                yield chunk

    def get_file_info(self, filepath: str) -> DataInfo:
        """
        파일 정보만 읽기 (데이터는 읽지 않음)

        Args:
            filepath: 파일 경로

        Returns:
            DataInfo: 파일 정보
        """
        path = Path(filepath)
        suffix = path.suffix.lower()

        info = DataInfo(
            filename=path.name,
            format=suffix[1:] if suffix else 'unknown',
        )

        if suffix == '.json':
            with open(filepath, 'r', encoding=self.default_encoding) as f:
                content = json.load(f)
            metadata = content.get('metadata', {})
            data = content.get('data', {})
            info.channels = list(data.keys()) if isinstance(data, dict) else []
            info.metadata = metadata
            info.sampling_rate = metadata.get('sampling_rate')

        elif suffix == '.csv':
            with open(filepath, 'r', encoding=self.default_encoding) as f:
                reader = csv.reader(f)
                headers = next(reader, [])
                info.channels = [h.strip() for h in headers]

                # 행 수 세기
                row_count = sum(1 for _ in reader)
                info.sample_count = row_count

        return info
