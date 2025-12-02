# 차동측정 기반 범용분석시스템 SDK

**Differential Measurement Analysis SDK**

차동측정(Differential Measurement) 기법을 활용한 범용 신호 분석 시스템 SDK입니다.

## 주요 기능

### Core (핵심 모듈)
- **DifferentialMeasurement**: 차동측정 수행 및 공통 모드 노이즈 제거
- **MeasurementChannel**: 측정 채널 관리
- **CalibrationManager**: 캘리브레이션 및 보정
- **MeasurementSession**: 측정 세션 관리

### Filters (필터 모듈)
- **NoiseFilter**: 다양한 노이즈 필터 (이동평균, 중앙값, 칼만, 위너 등)
- **AdaptiveFilter**: LMS/RLS 적응형 필터
- **LowPassFilter / HighPassFilter / BandPassFilter**: 주파수 필터
- **NotchFilter**: 노치 필터 (특정 주파수 제거)

### Analysis (분석 모듈)
- **SpectrumAnalyzer**: FFT 기반 스펙트럼 분석
- **StatisticalAnalyzer**: 통계 분석
- **TrendAnalyzer**: 트렌드 분석

### I/O (입출력 모듈)
- **DataReader**: 다양한 형식 데이터 읽기 (CSV, JSON, NumPy, Binary)
- **DataWriter**: 다양한 형식 데이터 쓰기

### Visualization (시각화 모듈)
- **MeasurementPlotter**: matplotlib 기반 시각화

## 설치

```bash
# 기본 설치 (numpy만 필요)
pip install -e .

# 시각화 기능 포함
pip install -e ".[visualization]"

# 전체 기능 (scipy, h5py 포함)
pip install -e ".[full]"

# 개발용
pip install -e ".[dev]"
```

## 빠른 시작

### 기본 차동측정

```python
from differential_measurement_sdk import (
    DifferentialMeasurement,
    MeasurementChannel,
)

# 채널 설정
ch_positive = MeasurementChannel(0, "CH+", sampling_rate=10000)
ch_negative = MeasurementChannel(1, "CH-", sampling_rate=10000)

# 데이터 설정
ch_positive.set_data(positive_signal)
ch_negative.set_data(negative_signal)

# 차동측정 수행
dm = DifferentialMeasurement()
result = dm.measure(ch_positive, ch_negative)

# 결과 확인
print(f"CMRR: {result.cmrr_db:.2f} dB")
print(f"차동 신호: {result.differential_signal}")
```

### 노이즈 필터링

```python
from differential_measurement_sdk import NoiseFilter, NoiseFilterType

# 칼만 필터 적용
kf = NoiseFilter(NoiseFilterType.KALMAN, process_noise=0.01, measurement_noise=0.1)
filtered = kf.apply(noisy_signal)

# 노이즈 레벨 추정
noise_info = kf.estimate_noise_level(noisy_signal)
print(f"SNR: {noise_info['snr_db']:.2f} dB")
```

### 스펙트럼 분석

```python
from differential_measurement_sdk import SpectrumAnalyzer

analyzer = SpectrumAnalyzer(sampling_rate=10000)
result = analyzer.analyze(signal)

print(f"주요 주파수: {result.dominant_frequency} Hz")
print(f"THD: {result.thd:.2f}%")

# 피크 검출
peaks = analyzer.find_peaks(signal, threshold_db=-40)
for peak in peaks:
    print(f"{peak['frequency']:.1f} Hz: {peak['magnitude_db']:.1f} dB")
```

### 캘리브레이션

```python
from differential_measurement_sdk import CalibrationManager

cal = CalibrationManager()

# 캘리브레이션 포인트 추가
cal.add_calibration_point(channel_id=0, reference_value=0.0, measured_value=0.05)
cal.add_calibration_point(channel_id=0, reference_value=5.0, measured_value=4.95)
cal.add_calibration_point(channel_id=0, reference_value=10.0, measured_value=9.90)

# 캘리브레이션 계수 계산
params = cal.calculate_calibration(0)
print(f"게인: {params['gain']:.6f}")
print(f"오프셋: {params['offset']:.6f}")

# 보정 적용
corrected = cal.apply_calibration(0, measured_value)
```

### 데이터 입출력

```python
from differential_measurement_sdk import DataReader, DataWriter

# 데이터 쓰기
writer = DataWriter()
writer.write_csv("data.csv", {"ch1": signal1, "ch2": signal2})
writer.write_json("data.json", data, metadata)

# 데이터 읽기
reader = DataReader()
data, info = reader.read("data.csv")
print(f"채널: {info.channels}")
print(f"샘플 수: {info.sample_count}")
```

## 프로젝트 구조

```
differential_measurement_sdk/
├── __init__.py          # 메인 모듈
├── core/                # 핵심 기능
│   ├── measurement.py   # 차동측정
│   ├── calibration.py   # 캘리브레이션
│   └── session.py       # 세션 관리
├── filters/             # 필터
│   ├── noise_filter.py  # 노이즈 필터
│   └── frequency_filters.py  # 주파수 필터
├── analysis/            # 분석
│   ├── spectrum.py      # 스펙트럼 분석
│   ├── statistics.py    # 통계 분석
│   └── trend.py         # 트렌드 분석
├── io/                  # 입출력
│   ├── data_reader.py   # 데이터 읽기
│   └── data_writer.py   # 데이터 쓰기
├── visualization/       # 시각화
│   └── plotter.py       # 플로터
└── utils/               # 유틸리티
    └── helpers.py       # 헬퍼 함수
```

## 예제

`examples/` 디렉토리에서 다양한 예제를 확인할 수 있습니다:

- `basic_differential_measurement.py`: 기본 차동측정 예제
- `calibration_example.py`: 캘리브레이션 예제
- `spectrum_analysis_example.py`: 스펙트럼 분석 예제
- `data_io_example.py`: 데이터 입출력 예제

## 테스트

```bash
# 테스트 실행
pytest tests/ -v

# 커버리지 포함
pytest tests/ --cov=differential_measurement_sdk
```

## 요구사항

- Python >= 3.8
- NumPy >= 1.20.0
- (선택) Matplotlib >= 3.3.0 (시각화)
- (선택) SciPy >= 1.6.0 (추가 기능)

## 라이선스

MIT License

## 기여

버그 리포트, 기능 요청, 풀 리퀘스트를 환영합니다!
