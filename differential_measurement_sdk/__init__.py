"""
차동측정 기반 범용분석시스템 SDK (Differential Measurement Analysis SDK)

이 SDK는 차동측정 기법을 활용한 범용 신호 분석 시스템을 제공합니다.

주요 기능:
- 차동측정 (Differential Measurement)
- 노이즈 필터링 (Noise Filtering)
- 스펙트럼 분석 (Spectrum Analysis)
- 통계 분석 (Statistical Analysis)
- 데이터 입출력 (Data I/O)
- 시각화 (Visualization)
"""

__version__ = "1.0.0"
__author__ = "Differential Measurement SDK Team"

from .core import (
    DifferentialMeasurement,
    MeasurementChannel,
    CalibrationManager,
    MeasurementSession,
)
from .filters import (
    NoiseFilter,
    LowPassFilter,
    HighPassFilter,
    BandPassFilter,
    AdaptiveFilter,
)
from .analysis import (
    SpectrumAnalyzer,
    StatisticalAnalyzer,
    TrendAnalyzer,
)
from .io import (
    DataReader,
    DataWriter,
)
from .visualization import (
    MeasurementPlotter,
)

__all__ = [
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
]
