"""
차동측정 기반 범용분석시스템 SDK (Differential Measurement Analysis SDK)

이 SDK는 차동측정 기법을 활용한 범용 신호 분석 시스템을 제공합니다.

v71 주요 업데이트:
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

__version__ = "71.0.0"
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
]
