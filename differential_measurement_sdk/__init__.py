"""
차동측정 기반 범용분석시스템 SDK (Differential Measurement Analysis SDK)

이 SDK는 차동측정 기법을 활용한 범용 신호 분석 시스템을 제공합니다.

v72 주요 업데이트 (MPK-RDR-MFG-SPEC v2.2 기반):
- 리더기 인터페이스 (Reader Interface) - E12 12핀 에지 커넥터
- 전기화학 측정 (Electrochemistry) - OCP/CA/CV/DPV/SWV/EIS
- 하드웨어 제어 (Hardware) - ADS1256 ADC, LMP91000 AFE, BQ24195 전원관리
- NFC 태그 관리 (NFC Tag) - NTAG216 카트리지 식별
- 데이터 프레임 (Data Frame) - 원시 샘플 로깅 및 직렬화
- FAI/검사 (FAI Inspection) - LLCR, 내구시험, 세정 SOP

v71 주요 기능:
- 휴대형 카트리지 모듈 (Portable Cartridge)
- 비표적 역설계분석시스템 (Non-Targeted Analysis)
- 상 가변형 인터페이스 (Phase-Variable Interface)
- 기체 시료 분석 (Gas Sampling)
- 다중 경로 보정 (Multi-Path Calibration)
- 데이터 보안 모듈 (Security)
- RAFE (Reconfigurable Analog Front-End)

기존 기능:
- 차동측정 (Differential Measurement)
- 노이즈 필터링 (Noise Filtering)
- 스펙트럼 분석 (Spectrum Analysis)
- 통계 분석 (Statistical Analysis)
- 데이터 입출력 (Data I/O)
- 시각화 (Visualization)
"""

__version__ = "72.0.0"
__author__ = "Differential Measurement SDK Team"
__patent_reference__ = "만파식_최종특허출원명세서_v71"

# Core modules
from .core import (
    DifferentialMeasurement,
    MeasurementChannel,
    CalibrationManager,
    MeasurementSession,
)

# Filters
from .filters import (
    NoiseFilter,
    LowPassFilter,
    HighPassFilter,
    BandPassFilter,
    AdaptiveFilter,
)

# Analysis
from .analysis import (
    SpectrumAnalyzer,
    StatisticalAnalyzer,
    TrendAnalyzer,
)

# I/O
from .io import (
    DataReader,
    DataWriter,
)

# Visualization
from .visualization import (
    MeasurementPlotter,
)

# v71 New Modules - Portable Cartridge
from .portable import (
    PortableCartridge,
    PortableCartridgeManager,
    PortableFormFactor,
    WirelessProtocol,
    PowerState,
    WirelessInterface,
    PortableElectrodeAssembly,
    PortableSignalProcessor,
)

# v71 New Modules - Non-Targeted Analysis
from .non_targeted import (
    NonTargetedAnalysisSystem,
    CrossReactiveSensorArray,
    FingerprintGenerator,
    AnomalyDetector,
    InverseInferenceEngine,
    SensorElement,
    SensorElementType,
    AnomalyDetectionMethod,
    SubstanceClass,
)

# v71 New Modules - Phase-Variable Interface
from .phase_variable import (
    PhaseVariableInterface,
    ConductiveMediatingLayer,
    SolidSampleAnalyzer,
    MultiPhaseSampleHandler,
    SamplePhase,
    MediatingLayerType,
    InterfaceMode,
)

# v71 New Modules - Gas Sampling
from .gas_sampling import (
    GasSamplingSystem,
    IonWindGenerator,
    EmitterElectrode,
    ParticleConcentrator,
    GasSensorArray,
    GasAnalysisResult,
    IonWindMode,
    DischargeType,
    GasType,
)

# v71 New Modules - Multi-Path Calibration
from .multi_path_calibration import (
    MultiPathCalibrationSystem,
    OpticalCalibrationUnit,
    ElectronicCalibrationUnit,
    WirelessCalibrationUnit,
    ManualCalibrationUnit,
    HybridCalibrationResult,
    PathCalibrationResult,
    CalibrationPath,
    CalibrationStatus,
    CalibrationQuality,
)

# v71 New Modules - Security
from .security import (
    SecurePacketManager,
    DataPacket,
    PacketHeader,
    MeasurementPayload,
    SecureSession,
    SecureSessionManager,
    DataIntegrityChecker,
    PacketType,
    EncryptionMode,
)

# v71 New Modules - RAFE
from .rafe import (
    RAFE,
    RAFEManager,
    RAFEConfiguration,
    InputMultiplexer,
    ProgrammableGainAmplifier,
    ConfigurableFilter,
    AntiAliasingFilter,
    ADCController,
    InputRange,
    GainSetting,
    FilterType,
    ADCResolution,
)

# v72 New Modules - Reader Interface (MPK-RDR-MFG-SPEC)
from .reader_interface import (
    E12Pin,
    PinDirection,
    PlatingType,
    ContactState,
    CartridgeState,
    PinDefinition,
    ContactResistance,
    SensorPair,
    E12Specification,
    E12EdgeConnector,
    ReaderInterface,
    create_reader_interface,
    create_e12_connector,
)

# v72 New Modules - Electrochemistry
from .electrochemistry import (
    MeasurementMode,
    ScanDirection,
    WaveformType,
    OCPParameters,
    CAParameters,
    CVParameters,
    DPVParameters,
    SWVParameters,
    EISParameters,
    MeasurementResult,
    EISResult,
    WaveformGenerator,
    ElectrochemicalCell,
    ElectrochemistryEngine,
    create_electrochemistry_engine,
    quick_cv_scan,
)

# v72 New Modules - Hardware Control
from .hardware import (
    ADCDataRate,
    ADCGain,
    ADCChannel,
    ADCInputMode,
    TIAGain,
    BiasPolarity,
    BiasPercentage,
    PowerSource,
    ChargingState,
    ADCSample,
    ADS1256,
    LMP91000,
    SwitchMatrix,
    BQ24195,
    HardwareManager,
    create_hardware_manager,
    create_adc,
    create_afe,
)

# v72 New Modules - NFC Tag Management
from .nfc_tag import (
    NFCTagType,
    TagLockState,
    CartridgeType,
    NTAG216Spec,
    CalibrationData,
    CartridgeInfo,
    NFCMemoryLayout,
    NTAG216,
    NFCCartridgeManager,
    create_ntag216,
    create_nfc_manager,
    create_test_cartridge,
)

# v72 New Modules - Data Frame
from .data_frame import (
    FrameType,
    CompressionType,
    ChannelConfig,
    FrameHeader,
    ADCConfig,
    AFEConfig,
    ModeConfig,
    EnvironmentData,
    NFCMetadata,
    RawSampleFrame,
    MultiChannelFrame,
    DataFrameLogger,
    RealTimeFrameStreamer,
    create_data_logger,
    create_frame_streamer,
    quick_frame_from_samples,
)

# v72 New Modules - FAI Inspection
from .fai_inspection import (
    InspectionResult,
    AQLLevel,
    ContaminationType,
    CleaningMethod,
    LLCRSpec,
    DurabilitySpec,
    EnvironmentalSpec,
    LLCRMeasurement,
    ContinuityTest,
    VisualInspection,
    DimensionalMeasurement,
    CleaningStep,
    CleaningSOP,
    FAITestSuite,
    DurabilityTester,
    CleaningSOPManager,
    create_fai_suite,
    create_durability_tester,
    run_quick_fai,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__patent_reference__",

    # Core
    "DifferentialMeasurement",
    "MeasurementChannel",
    "CalibrationManager",
    "MeasurementSession",

    # Filters
    "NoiseFilter",
    "LowPassFilter",
    "HighPassFilter",
    "BandPassFilter",
    "AdaptiveFilter",

    # Analysis
    "SpectrumAnalyzer",
    "StatisticalAnalyzer",
    "TrendAnalyzer",

    # I/O
    "DataReader",
    "DataWriter",

    # Visualization
    "MeasurementPlotter",

    # v71 - Portable Cartridge
    "PortableCartridge",
    "PortableCartridgeManager",
    "PortableFormFactor",
    "WirelessProtocol",
    "PowerState",
    "WirelessInterface",
    "PortableElectrodeAssembly",
    "PortableSignalProcessor",

    # v71 - Non-Targeted Analysis
    "NonTargetedAnalysisSystem",
    "CrossReactiveSensorArray",
    "FingerprintGenerator",
    "AnomalyDetector",
    "InverseInferenceEngine",
    "SensorElement",
    "SensorElementType",
    "AnomalyDetectionMethod",
    "SubstanceClass",

    # v71 - Phase-Variable Interface
    "PhaseVariableInterface",
    "ConductiveMediatingLayer",
    "SolidSampleAnalyzer",
    "MultiPhaseSampleHandler",
    "SamplePhase",
    "MediatingLayerType",
    "InterfaceMode",

    # v71 - Gas Sampling
    "GasSamplingSystem",
    "IonWindGenerator",
    "EmitterElectrode",
    "ParticleConcentrator",
    "GasSensorArray",
    "GasAnalysisResult",
    "IonWindMode",
    "DischargeType",
    "GasType",

    # v71 - Multi-Path Calibration
    "MultiPathCalibrationSystem",
    "OpticalCalibrationUnit",
    "ElectronicCalibrationUnit",
    "WirelessCalibrationUnit",
    "ManualCalibrationUnit",
    "HybridCalibrationResult",
    "PathCalibrationResult",
    "CalibrationPath",
    "CalibrationStatus",
    "CalibrationQuality",

    # v71 - Security
    "SecurePacketManager",
    "DataPacket",
    "PacketHeader",
    "MeasurementPayload",
    "SecureSession",
    "SecureSessionManager",
    "DataIntegrityChecker",
    "PacketType",
    "EncryptionMode",

    # v71 - RAFE
    "RAFE",
    "RAFEManager",
    "RAFEConfiguration",
    "InputMultiplexer",
    "ProgrammableGainAmplifier",
    "ConfigurableFilter",
    "AntiAliasingFilter",
    "ADCController",
    "InputRange",
    "GainSetting",
    "FilterType",
    "ADCResolution",

    # v72 - Reader Interface
    "E12Pin",
    "PinDirection",
    "PlatingType",
    "ContactState",
    "CartridgeState",
    "PinDefinition",
    "ContactResistance",
    "SensorPair",
    "E12Specification",
    "E12EdgeConnector",
    "ReaderInterface",
    "create_reader_interface",
    "create_e12_connector",

    # v72 - Electrochemistry
    "MeasurementMode",
    "ScanDirection",
    "WaveformType",
    "OCPParameters",
    "CAParameters",
    "CVParameters",
    "DPVParameters",
    "SWVParameters",
    "EISParameters",
    "MeasurementResult",
    "EISResult",
    "WaveformGenerator",
    "ElectrochemicalCell",
    "ElectrochemistryEngine",
    "create_electrochemistry_engine",
    "quick_cv_scan",

    # v72 - Hardware Control
    "ADCDataRate",
    "ADCGain",
    "ADCChannel",
    "ADCInputMode",
    "TIAGain",
    "BiasPolarity",
    "BiasPercentage",
    "PowerSource",
    "ChargingState",
    "ADCSample",
    "ADS1256",
    "LMP91000",
    "SwitchMatrix",
    "BQ24195",
    "HardwareManager",
    "create_hardware_manager",
    "create_adc",
    "create_afe",

    # v72 - NFC Tag Management
    "NFCTagType",
    "TagLockState",
    "CartridgeType",
    "NTAG216Spec",
    "CalibrationData",
    "CartridgeInfo",
    "NFCMemoryLayout",
    "NTAG216",
    "NFCCartridgeManager",
    "create_ntag216",
    "create_nfc_manager",
    "create_test_cartridge",

    # v72 - Data Frame
    "FrameType",
    "CompressionType",
    "ChannelConfig",
    "FrameHeader",
    "ADCConfig",
    "AFEConfig",
    "ModeConfig",
    "EnvironmentData",
    "NFCMetadata",
    "RawSampleFrame",
    "MultiChannelFrame",
    "DataFrameLogger",
    "RealTimeFrameStreamer",
    "create_data_logger",
    "create_frame_streamer",
    "quick_frame_from_samples",

    # v72 - FAI Inspection
    "InspectionResult",
    "AQLLevel",
    "ContaminationType",
    "CleaningMethod",
    "LLCRSpec",
    "DurabilitySpec",
    "EnvironmentalSpec",
    "LLCRMeasurement",
    "ContinuityTest",
    "VisualInspection",
    "DimensionalMeasurement",
    "CleaningStep",
    "CleaningSOP",
    "FAITestSuite",
    "DurabilityTester",
    "CleaningSOPManager",
    "create_fai_suite",
    "create_durability_tester",
    "run_quick_fai",
]
