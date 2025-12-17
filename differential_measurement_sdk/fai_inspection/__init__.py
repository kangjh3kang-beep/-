"""
FAI/검사 모듈 (First Article Inspection Module)

제조 검사 및 품질 관리 (MPK-RDR-MFG-SPEC v2.2 섹션 6, 7)

주요 기능:
- LLCR (Low Level Contact Resistance) 검사
- 연속성 검사 (오픈/쇼트)
- 내구 사이클 시험
- 도금 수명 시험
- 세정 SOP 체크리스트
- FAI 리포트 생성
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import numpy as np
import json


class InspectionResult(Enum):
    """검사 결과"""
    PASS = "pass"
    FAIL = "fail"
    MARGINAL = "marginal"
    NOT_TESTED = "not_tested"


class AQLLevel(Enum):
    """AQL 레벨"""
    AQL_0_65 = 0.65
    AQL_1_0 = 1.0
    AQL_2_5 = 2.5
    AQL_4_0 = 4.0


class PlatingType(Enum):
    """도금 타입"""
    HARD_GOLD = "hard_gold"
    ENIG = "enig"


class ContaminationType(Enum):
    """오염 유형"""
    BLOOD_PROTEIN = "blood_protein"
    SALT_SWEAT = "salt_sweat"
    CONDENSATION = "condensation"
    FLUX_RESIDUE = "flux_residue"


class CleaningMethod(Enum):
    """세정 방법"""
    DI_WATER = "di_water"
    IPA_70 = "ipa_70"
    NEUTRAL_DETERGENT = "neutral_detergent"
    ENZYME_CLEANER = "enzyme_cleaner"
    AIR_DRY = "air_dry"


@dataclass
class LLCRSpec:
    """LLCR 규격 (EIA-364-23 준용)"""
    initial_max_mohm: float = 50.0      # 초기 최대 (mΩ)
    lifecycle_max_mohm: float = 70.0    # 수명 후 최대
    delta_max_mohm: float = 20.0        # 최대 변화량
    test_current_ma: float = 10.0       # 테스트 전류


@dataclass
class DurabilitySpec:
    """내구 시험 규격 (EIA-364-09 준용)"""
    # EVT/DVT/양산 사이클
    evt_cycles: int = 1000
    dvt_cycles: int = 5000
    production_cycles: int = 10000

    # 삽입력/탈거력
    insertion_force_n: Tuple[float, float] = (0.5, 3.0)
    extraction_force_n: Tuple[float, float] = (0.5, 2.0)


@dataclass
class EnvironmentalSpec:
    """환경 시험 규격"""
    # 습열 시험 (85/85)
    humidity_test_temp_c: float = 85.0
    humidity_test_rh: float = 85.0
    humidity_test_hours: Tuple[float, float] = (48, 168)

    # 염수 분무 (ASTM B117)
    salt_spray_nacl_percent: float = 5.0
    salt_spray_hours: float = 24.0


@dataclass
class LLCRMeasurement:
    """LLCR 측정 결과"""
    pin_id: str
    resistance_mohm: float
    timestamp: datetime
    temperature_c: float = 25.0
    test_current_ma: float = 10.0

    def evaluate(self, spec: LLCRSpec, initial: float = None) -> InspectionResult:
        """규격 대비 평가"""
        if self.resistance_mohm > spec.lifecycle_max_mohm:
            return InspectionResult.FAIL

        if initial is not None:
            delta = self.resistance_mohm - initial
            if delta > spec.delta_max_mohm:
                return InspectionResult.FAIL

        if self.resistance_mohm > spec.initial_max_mohm:
            return InspectionResult.MARGINAL

        return InspectionResult.PASS


@dataclass
class ContinuityTest:
    """연속성 시험 결과"""
    pin_id: str
    is_open: bool
    is_short: bool
    short_with: Optional[str] = None
    resistance_mohm: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def evaluate(self) -> InspectionResult:
        """평가"""
        if self.is_open or self.is_short:
            return InspectionResult.FAIL
        return InspectionResult.PASS


@dataclass
class VisualInspection:
    """육안 검사 결과"""
    location: str
    description: str
    has_defect: bool
    defect_type: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    photo_path: Optional[str] = None

    def evaluate(self) -> InspectionResult:
        if self.has_defect:
            return InspectionResult.FAIL
        return InspectionResult.PASS


@dataclass
class DimensionalMeasurement:
    """치수 측정 결과"""
    feature_id: str
    feature_name: str
    nominal: float
    tolerance: float
    measured: float
    unit: str = "mm"
    timestamp: datetime = field(default_factory=datetime.now)

    def evaluate(self) -> InspectionResult:
        """규격 대비 평가"""
        deviation = abs(self.measured - self.nominal)
        if deviation > self.tolerance:
            return InspectionResult.FAIL
        if deviation > self.tolerance * 0.8:
            return InspectionResult.MARGINAL
        return InspectionResult.PASS

    @property
    def deviation(self) -> float:
        return self.measured - self.nominal


@dataclass
class CleaningStep:
    """세정 단계"""
    step_number: int
    method: CleaningMethod
    description: str
    duration_min: float
    temperature_c: Optional[float] = None
    completed: bool = False
    completed_at: Optional[datetime] = None


@dataclass
class CleaningSOP:
    """세정 SOP (Standard Operating Procedure)"""
    contamination_type: ContaminationType
    steps: List[CleaningStep] = field(default_factory=list)
    acceptance_criteria: Dict[str, Any] = field(default_factory=dict)

    # 기본 합격 기준
    DEFAULT_CRITERIA: Dict[str, Any] = field(default_factory=lambda: {
        'visual_residue': False,
        'visual_discoloration': False,
        'llcr_max_mohm': 70.0,
        'llcr_delta_mohm': 20.0,
        'rose_max_ug_cm2': 1.56  # NaCl eq
    })


class FAITestSuite:
    """
    FAI 테스트 스위트

    제조 검사 항목 관리 및 실행
    """

    def __init__(self, suite_id: str = "FAI_001"):
        """
        Args:
            suite_id: 테스트 스위트 식별자
        """
        self.suite_id = suite_id

        # 규격
        self.llcr_spec = LLCRSpec()
        self.durability_spec = DurabilitySpec()
        self.environmental_spec = EnvironmentalSpec()

        # 결과 저장
        self.llcr_results: List[LLCRMeasurement] = []
        self.continuity_results: List[ContinuityTest] = []
        self.visual_results: List[VisualInspection] = []
        self.dimensional_results: List[DimensionalMeasurement] = []

        # 초기 LLCR (기준값)
        self.initial_llcr: Dict[str, float] = {}

        # 메타데이터
        self.lot_number: str = ""
        self.serial_number: str = ""
        self.inspector: str = ""
        self.test_date: datetime = datetime.now()

    def set_unit_info(self,
                     lot_number: str,
                     serial_number: str,
                     inspector: str = "") -> None:
        """검사 대상 정보 설정"""
        self.lot_number = lot_number
        self.serial_number = serial_number
        self.inspector = inspector
        self.test_date = datetime.now()

    def measure_llcr(self,
                    pin_id: str,
                    resistance_mohm: float,
                    is_initial: bool = False) -> LLCRMeasurement:
        """LLCR 측정 기록"""
        measurement = LLCRMeasurement(
            pin_id=pin_id,
            resistance_mohm=resistance_mohm,
            timestamp=datetime.now(),
            test_current_ma=self.llcr_spec.test_current_ma
        )

        self.llcr_results.append(measurement)

        if is_initial:
            self.initial_llcr[pin_id] = resistance_mohm

        return measurement

    def test_continuity(self,
                       pin_id: str,
                       resistance_mohm: float,
                       open_threshold_mohm: float = 1000.0,
                       short_threshold_mohm: float = 1.0,
                       adjacent_pin: str = None) -> ContinuityTest:
        """연속성 시험"""
        is_open = resistance_mohm > open_threshold_mohm
        is_short = resistance_mohm < short_threshold_mohm and adjacent_pin is not None

        result = ContinuityTest(
            pin_id=pin_id,
            is_open=is_open,
            is_short=is_short,
            short_with=adjacent_pin if is_short else None,
            resistance_mohm=resistance_mohm
        )

        self.continuity_results.append(result)
        return result

    def add_visual_inspection(self,
                             location: str,
                             description: str,
                             has_defect: bool,
                             defect_type: str = None) -> VisualInspection:
        """육안 검사 기록"""
        result = VisualInspection(
            location=location,
            description=description,
            has_defect=has_defect,
            defect_type=defect_type
        )

        self.visual_results.append(result)
        return result

    def add_dimensional(self,
                       feature_id: str,
                       feature_name: str,
                       nominal: float,
                       tolerance: float,
                       measured: float,
                       unit: str = "mm") -> DimensionalMeasurement:
        """치수 측정 기록"""
        result = DimensionalMeasurement(
            feature_id=feature_id,
            feature_name=feature_name,
            nominal=nominal,
            tolerance=tolerance,
            measured=measured,
            unit=unit
        )

        self.dimensional_results.append(result)
        return result

    def evaluate_llcr_all(self) -> Dict[str, InspectionResult]:
        """전체 LLCR 평가"""
        results = {}

        for measurement in self.llcr_results:
            initial = self.initial_llcr.get(measurement.pin_id)
            result = measurement.evaluate(self.llcr_spec, initial)
            results[measurement.pin_id] = result

        return results

    def evaluate_continuity_all(self) -> Dict[str, InspectionResult]:
        """전체 연속성 평가"""
        return {
            test.pin_id: test.evaluate()
            for test in self.continuity_results
        }

    def evaluate_visual_all(self) -> Dict[str, InspectionResult]:
        """전체 육안 검사 평가"""
        return {
            f"{insp.location}": insp.evaluate()
            for insp in self.visual_results
        }

    def evaluate_dimensional_all(self) -> Dict[str, InspectionResult]:
        """전체 치수 평가"""
        return {
            dim.feature_id: dim.evaluate()
            for dim in self.dimensional_results
        }

    def get_overall_result(self) -> InspectionResult:
        """종합 판정"""
        all_results = []

        all_results.extend(self.evaluate_llcr_all().values())
        all_results.extend(self.evaluate_continuity_all().values())
        all_results.extend(self.evaluate_visual_all().values())
        all_results.extend(self.evaluate_dimensional_all().values())

        if InspectionResult.FAIL in all_results:
            return InspectionResult.FAIL
        if InspectionResult.MARGINAL in all_results:
            return InspectionResult.MARGINAL
        if not all_results:
            return InspectionResult.NOT_TESTED

        return InspectionResult.PASS

    def generate_report(self) -> Dict[str, Any]:
        """FAI 리포트 생성"""
        report = {
            'report_id': f"FAI_{self.serial_number}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'suite_id': self.suite_id,
            'lot_number': self.lot_number,
            'serial_number': self.serial_number,
            'inspector': self.inspector,
            'test_date': self.test_date.isoformat(),

            'overall_result': self.get_overall_result().value,

            'llcr_results': {
                'spec': {
                    'initial_max_mohm': self.llcr_spec.initial_max_mohm,
                    'lifecycle_max_mohm': self.llcr_spec.lifecycle_max_mohm,
                    'delta_max_mohm': self.llcr_spec.delta_max_mohm
                },
                'measurements': [
                    {
                        'pin_id': m.pin_id,
                        'resistance_mohm': m.resistance_mohm,
                        'result': m.evaluate(self.llcr_spec, self.initial_llcr.get(m.pin_id)).value
                    }
                    for m in self.llcr_results
                ],
                'evaluation': {k: v.value for k, v in self.evaluate_llcr_all().items()}
            },

            'continuity_results': {
                'tests': [
                    {
                        'pin_id': t.pin_id,
                        'is_open': t.is_open,
                        'is_short': t.is_short,
                        'result': t.evaluate().value
                    }
                    for t in self.continuity_results
                ],
                'evaluation': {k: v.value for k, v in self.evaluate_continuity_all().items()}
            },

            'visual_results': {
                'inspections': [
                    {
                        'location': v.location,
                        'has_defect': v.has_defect,
                        'defect_type': v.defect_type,
                        'result': v.evaluate().value
                    }
                    for v in self.visual_results
                ],
                'evaluation': {k: v.value for k, v in self.evaluate_visual_all().items()}
            },

            'dimensional_results': {
                'measurements': [
                    {
                        'feature_id': d.feature_id,
                        'feature_name': d.feature_name,
                        'nominal': d.nominal,
                        'tolerance': d.tolerance,
                        'measured': d.measured,
                        'deviation': d.deviation,
                        'unit': d.unit,
                        'result': d.evaluate().value
                    }
                    for d in self.dimensional_results
                ],
                'evaluation': {k: v.value for k, v in self.evaluate_dimensional_all().items()}
            }
        }

        return report

    def save_report(self, filepath: str) -> None:
        """리포트 저장"""
        report = self.generate_report()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)


class DurabilityTester:
    """
    내구 시험 관리

    삽입/탈거 사이클 시험 (EIA-364-09)
    """

    def __init__(self, tester_id: str = "DUR_001"):
        self.tester_id = tester_id
        self.spec = DurabilitySpec()

        # 시험 기록
        self.cycle_count = 0
        self.target_cycles = 0
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

        # LLCR 이력
        self.llcr_history: List[Tuple[int, Dict[str, float]]] = []

        # 결함 기록
        self.defects: List[Dict[str, Any]] = []

    def start_test(self, target_cycles: int, initial_llcr: Dict[str, float]) -> None:
        """시험 시작"""
        self.target_cycles = target_cycles
        self.cycle_count = 0
        self.start_time = datetime.now()
        self.llcr_history = [(0, initial_llcr.copy())]

    def record_cycle(self,
                    llcr_measurements: Dict[str, float] = None,
                    has_defect: bool = False,
                    defect_description: str = None) -> None:
        """사이클 기록"""
        self.cycle_count += 1

        if llcr_measurements:
            self.llcr_history.append((self.cycle_count, llcr_measurements.copy()))

        if has_defect:
            self.defects.append({
                'cycle': self.cycle_count,
                'description': defect_description,
                'timestamp': datetime.now().isoformat()
            })

    def end_test(self) -> None:
        """시험 종료"""
        self.end_time = datetime.now()

    def evaluate(self, llcr_spec: LLCRSpec) -> InspectionResult:
        """내구 시험 평가"""
        if not self.llcr_history or len(self.llcr_history) < 2:
            return InspectionResult.NOT_TESTED

        initial_llcr = self.llcr_history[0][1]
        final_llcr = self.llcr_history[-1][1]

        for pin_id, final_value in final_llcr.items():
            # 절대값 검사
            if final_value > llcr_spec.lifecycle_max_mohm:
                return InspectionResult.FAIL

            # 변화량 검사
            initial_value = initial_llcr.get(pin_id, 0)
            delta = final_value - initial_value
            if delta > llcr_spec.delta_max_mohm:
                return InspectionResult.FAIL

        if self.defects:
            return InspectionResult.MARGINAL

        return InspectionResult.PASS

    def get_report(self) -> Dict[str, Any]:
        """내구 시험 리포트"""
        return {
            'tester_id': self.tester_id,
            'target_cycles': self.target_cycles,
            'completed_cycles': self.cycle_count,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'llcr_initial': self.llcr_history[0][1] if self.llcr_history else {},
            'llcr_final': self.llcr_history[-1][1] if self.llcr_history else {},
            'defect_count': len(self.defects),
            'defects': self.defects
        }


class CleaningSOPManager:
    """
    세정 SOP 관리자

    오염 유형별 세정 절차 관리
    """

    def __init__(self):
        self.sops: Dict[ContaminationType, CleaningSOP] = {}
        self._init_default_sops()

    def _init_default_sops(self) -> None:
        """기본 SOP 초기화"""
        # 혈액/단백질 오염
        self.sops[ContaminationType.BLOOD_PROTEIN] = CleaningSOP(
            contamination_type=ContaminationType.BLOOD_PROTEIN,
            steps=[
                CleaningStep(1, CleaningMethod.DI_WATER, "오염 부위 블로팅 (문지르지 말 것)", 2.0),
                CleaningStep(2, CleaningMethod.DI_WATER, "DI Water로 충분히 적신 면봉으로 용해/제거", 5.0),
                CleaningStep(3, CleaningMethod.NEUTRAL_DETERGENT, "중성 세정제로 2차 세정", 3.0),
                CleaningStep(4, CleaningMethod.DI_WATER, "DI Water로 잔류 세정제 제거", 3.0),
                CleaningStep(5, CleaningMethod.IPA_70, "70% IPA로 최종 와이핑", 2.0),
                CleaningStep(6, CleaningMethod.AIR_DRY, "상온 에어건조", 10.0),
            ]
        )

        # 염류/땀 오염
        self.sops[ContaminationType.SALT_SWEAT] = CleaningSOP(
            contamination_type=ContaminationType.SALT_SWEAT,
            steps=[
                CleaningStep(1, CleaningMethod.DI_WATER, "DI Water로 염류 용해/제거", 5.0),
                CleaningStep(2, CleaningMethod.DI_WATER, "DI Water로 2차 헹굼", 3.0),
                CleaningStep(3, CleaningMethod.IPA_70, "70% IPA로 수분 치환/제거", 2.0),
                CleaningStep(4, CleaningMethod.AIR_DRY, "상온 에어건조", 10.0),
            ]
        )

        # 응축수/수분 유입
        self.sops[ContaminationType.CONDENSATION] = CleaningSOP(
            contamination_type=ContaminationType.CONDENSATION,
            steps=[
                CleaningStep(1, CleaningMethod.AIR_DRY, "에어로 1차 건조 (물방울 제거)", 3.0),
                CleaningStep(2, CleaningMethod.IPA_70, "70% IPA로 접점/슬롯 와이핑", 2.0),
                CleaningStep(3, CleaningMethod.AIR_DRY, "완전 건조", 10.0),
            ]
        )

    def get_sop(self, contamination_type: ContaminationType) -> Optional[CleaningSOP]:
        """SOP 조회"""
        return self.sops.get(contamination_type)

    def execute_sop(self, sop: CleaningSOP) -> List[CleaningStep]:
        """SOP 실행 (시뮬레이션)"""
        for step in sop.steps:
            step.completed = True
            step.completed_at = datetime.now()

        return sop.steps

    def verify_cleaning(self,
                       llcr_after: Dict[str, float],
                       llcr_initial: Dict[str, float],
                       visual_check: bool,
                       sop: CleaningSOP = None) -> Dict[str, Any]:
        """세정 후 검증"""
        criteria = sop.acceptance_criteria if sop else CleaningSOP.DEFAULT_CRITERIA

        results = {
            'visual_pass': not visual_check,  # visual_check=True means defect found
            'llcr_pass': True,
            'details': []
        }

        for pin_id, value in llcr_after.items():
            initial = llcr_initial.get(pin_id, 0)
            delta = value - initial

            if value > criteria.get('llcr_max_mohm', 70.0):
                results['llcr_pass'] = False
                results['details'].append(f"{pin_id}: LLCR {value:.1f} mΩ 초과")

            if delta > criteria.get('llcr_delta_mohm', 20.0):
                results['llcr_pass'] = False
                results['details'].append(f"{pin_id}: LLCR 변화량 {delta:.1f} mΩ 초과")

        results['overall_pass'] = results['visual_pass'] and results['llcr_pass']
        return results


# 편의 함수
def create_fai_suite(suite_id: str = "DEFAULT") -> FAITestSuite:
    """FAI 테스트 스위트 생성 헬퍼"""
    return FAITestSuite(suite_id=suite_id)


def create_durability_tester(tester_id: str = "DEFAULT") -> DurabilityTester:
    """내구 시험기 생성 헬퍼"""
    return DurabilityTester(tester_id=tester_id)


def run_quick_fai(lot: str, serial: str) -> Dict[str, Any]:
    """빠른 FAI 실행 (시뮬레이션)"""
    suite = FAITestSuite()
    suite.set_unit_info(lot, serial, "AUTO")

    # 시뮬레이션 LLCR 측정
    for i in range(12):
        resistance = np.random.uniform(15, 45)  # 정상 범위
        suite.measure_llcr(f"PIN_{i+1}", resistance, is_initial=True)

    # 시뮬레이션 연속성
    for i in range(12):
        resistance = np.random.uniform(10, 100)
        suite.test_continuity(f"PIN_{i+1}", resistance)

    # 시뮬레이션 육안검사
    suite.add_visual_inspection("EDGE_PADS", "패드 상태 양호", has_defect=False)
    suite.add_visual_inspection("PLATING", "도금 상태 양호", has_defect=False)

    return suite.generate_report()


__all__ = [
    # Enums
    'InspectionResult',
    'AQLLevel',
    'PlatingType',
    'ContaminationType',
    'CleaningMethod',
    # Spec Classes
    'LLCRSpec',
    'DurabilitySpec',
    'EnvironmentalSpec',
    # Result Classes
    'LLCRMeasurement',
    'ContinuityTest',
    'VisualInspection',
    'DimensionalMeasurement',
    # SOP Classes
    'CleaningStep',
    'CleaningSOP',
    # Main Classes
    'FAITestSuite',
    'DurabilityTester',
    'CleaningSOPManager',
    # Functions
    'create_fai_suite',
    'create_durability_tester',
    'run_quick_fai',
]
