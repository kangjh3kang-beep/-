# 차동측정 기반 범용분석시스템 SDK v71

**Differential Measurement Analysis SDK v71**

차동측정(Differential Measurement) 기법을 활용한 범용 신호 분석 시스템 SDK입니다.

**v71 특허 기반**: 만파식_최종특허출원명세서_v71

## v71 주요 업데이트

### 신규 기능

- **휴대형 카트리지 (Portable Cartridge)**: NFC/RFID 무선 전력 수확 기반 휴대형 측정 모듈
- **비표적 역설계분석시스템 (Non-Targeted Analysis)**: 교차반응성 센서 어레이 기반 미지 물질 분석
- **상 가변형 인터페이스 (Phase-Variable Interface)**: 액체/기체/고체 시료 통합 처리
- **기체 시료 분석 (Gas Sampling)**: 이온풍(EHD) 기반 무소음 기체 흡입 및 분석
- **다중 경로 보정 (Multi-Path Calibration)**: 광학/전자/무선/수동 경로 융합 보정
- **데이터 보안 (Security)**: 암호화 패킷 구조 및 무결성 검증
- **RAFE (Reconfigurable Analog Front-End)**: 재구성 가능 아날로그 프론트엔드

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

### v71 - Portable Cartridge (휴대형 카트리지)
- **PortableCartridge**: NFC/RFID 무선 전력 수확 기반 휴대형 카트리지
- **WirelessInterface**: 무선 전력 전송 및 데이터 통신
- **PortableElectrodeAssembly**: 센싱/기준 전극 어셈블리
- **PortableSignalProcessor**: 차동 신호 처리기

### v71 - Non-Targeted Analysis (비표적 분석)
- **NonTargetedAnalysisSystem**: 비표적 역설계분석 통합 시스템
- **CrossReactiveSensorArray**: 교차반응성 센서 어레이
- **FingerprintGenerator**: 지문 벡터 생성기
- **AnomalyDetector**: 이상치 탐지 (오토인코더, One-Class SVM, Isolation Forest 등)
- **InverseInferenceEngine**: 역추론 엔진 (미지 물질 식별)

### v71 - Phase-Variable Interface (상 가변형 인터페이스)
- **PhaseVariableInterface**: 액체/기체/고체 시료 통합 인터페이스
- **ConductiveMediatingLayer**: 전도성 매개층 (하이드로겔)
- **SolidSampleAnalyzer**: 고체 시료 직접 분석기
- **MultiPhaseSampleHandler**: 다중 상 시료 처리기

### v71 - Gas Sampling (기체 시료 분석)
- **GasSamplingSystem**: 이온풍 기반 기체 흡입 및 분석 시스템
- **IonWindGenerator**: 코로나 방전 기반 이온풍 생성기
- **EmitterElectrode**: 이미터 전극 (코로나 방전용)
- **ParticleConcentrator**: 입자 농축기
- **GasSensorArray**: 다중 기체 센서 어레이

### v71 - Multi-Path Calibration (다중 경로 보정)
- **MultiPathCalibrationSystem**: 다중 경로 융합 보정 시스템
- **OpticalCalibrationUnit**: 광학 경로 보정 (LED/포토다이오드)
- **ElectronicCalibrationUnit**: 전자 경로 보정 (정밀 기준 저항)
- **WirelessCalibrationUnit**: 무선 경로 보정 (NFC/BLE)
- **HybridCalibrationResult**: 동적 가중치 하이브리드 융합 결과

### v71 - Security (보안)
- **SecurePacketManager**: 보안 패킷 관리자
- **DataPacket**: 암호화 데이터 패킷
- **DataIntegrityChecker**: 무결성 검사 (CRC32, SHA256, HMAC)

### v71 - RAFE (재구성 가능 아날로그 프론트엔드)
- **RAFE**: 통합 아날로그 프론트엔드
- **InputMultiplexer**: 다채널 멀티플렉서
- **ProgrammableGainAmplifier**: 프로그래머블 이득 증폭기 (PGA)
- **ConfigurableFilter**: 재구성 가능 필터
- **ADCController**: ADC 제어기

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

### v71 - 휴대형 카트리지 사용

```python
from differential_measurement_sdk import (
    PortableCartridge,
    PortableFormFactor,
    WirelessProtocol,
)

# 카트리지 생성
cartridge = PortableCartridge(
    cartridge_id="CART_001",
    form_factor=PortableFormFactor.STRIP
)

# 무선 전력 수확 시뮬레이션
cartridge.wireless.start_power_harvesting()

# 측정 수행
result = cartridge.measure(test_sample_data)
print(f"측정값: {result.processed_value:.6f} V")
```

### v71 - 비표적 분석 사용

```python
from differential_measurement_sdk import (
    NonTargetedAnalysisSystem,
    AnomalyDetectionMethod,
)

# 시스템 초기화
nta_system = NonTargetedAnalysisSystem(
    system_id="NTA_001",
    num_sensors=16
)

# 알려진 물질로 학습
nta_system.learn_known_substance("에탄올", ethanol_fingerprints)
nta_system.learn_known_substance("메탄올", methanol_fingerprints)

# 미지 시료 분석
result = nta_system.analyze_unknown(unknown_sample)

if result.is_anomaly:
    print(f"미지 물질 감지! 신뢰도: {result.anomaly_score:.3f}")
else:
    print(f"식별된 물질: {result.identified_substance}")
```

### v71 - 기체 시료 분석

```python
from differential_measurement_sdk import (
    GasSamplingSystem,
    IonWindMode,
)

# 기체 샘플링 시스템 생성
gas_system = GasSamplingSystem(system_id="GAS_001")

# 이온풍 샘플링 시작
gas_system.start_sampling(mode=IonWindMode.NORMAL)

# 분석 수행
result = gas_system.analyze()

print(f"검출된 기체: {result.detected_gases}")
print(f"총 VOC: {result.total_voc_ppb:.1f} ppb")

gas_system.stop_sampling()
```

### v71 - RAFE 사용

```python
from differential_measurement_sdk import (
    RAFE,
    GainSetting,
    FilterType,
)

# RAFE 초기화
rafe = RAFE(rafe_id="RAFE_001")

# 프리셋 로드
rafe.load_preset('precision_dc')

# 또는 자동 구성
config = rafe.auto_configure(sample_signal)

# 신호 처리
analog_out, digital_out = rafe.process_signal(input_signal, sample_rate=10000)

print(f"동적 범위: {rafe.get_dynamic_range_db():.1f} dB")
```

## 프로젝트 구조

```
differential_measurement_sdk/
├── __init__.py              # 메인 모듈 (v71.0.0)
├── core/                    # 핵심 기능
│   ├── measurement.py       # 차동측정
│   ├── calibration.py       # 캘리브레이션
│   └── session.py           # 세션 관리
├── filters/                 # 필터
│   ├── noise_filter.py      # 노이즈 필터
│   └── frequency_filters.py # 주파수 필터
├── analysis/                # 분석
│   ├── spectrum.py          # 스펙트럼 분석
│   ├── statistics.py        # 통계 분석
│   └── trend.py             # 트렌드 분석
├── io/                      # 입출력
│   ├── data_reader.py       # 데이터 읽기
│   └── data_writer.py       # 데이터 쓰기
├── visualization/           # 시각화
│   └── plotter.py           # 플로터
├── utils/                   # 유틸리티
│   └── helpers.py           # 헬퍼 함수
├── portable/                # [v71] 휴대형 카트리지
│   └── __init__.py
├── non_targeted/            # [v71] 비표적 분석
│   └── __init__.py
├── phase_variable/          # [v71] 상 가변형 인터페이스
│   └── __init__.py
├── gas_sampling/            # [v71] 기체 시료 분석
│   └── __init__.py
├── multi_path_calibration/  # [v71] 다중 경로 보정
│   └── __init__.py
├── security/                # [v71] 보안
│   └── __init__.py
└── rafe/                    # [v71] RAFE
    └── __init__.py
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

## 특허 참조

이 SDK는 "만파식_최종특허출원명세서_v71" 특허 명세서를 기반으로 구현되었습니다.

## 기여

버그 리포트, 기능 요청, 풀 리퀘스트를 환영합니다!
