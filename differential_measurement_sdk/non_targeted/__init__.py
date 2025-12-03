"""
비표적 역설계분석시스템 (Non-Targeted Reverse Engineering Analysis System)

교차반응성 센서 어레이와 역추론 알고리즘을 통해 학습 데이터베이스에 포함된 물질과
포함되지 않은 미지의 물질을 모두 탐지하는 시스템.

특허 참조: 실시예 12, 13, 14 (도 23, 24, 25)
"""

from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import numpy as np


class SensorElementType(Enum):
    """반특이적 감지 소자 유형"""
    BROAD_OXIDASE = "broad_oxidase"             # 광범위 산화효소
    NON_SPECIFIC_IG = "non_specific_ig"         # 비특이적 면역글로불린
    PH_SENSITIVE = "ph_sensitive"               # pH 민감 전극
    CONDUCTIVITY = "conductivity"               # 전도도 센서
    REDOX_POTENTIAL = "redox_potential"         # 산화환원 전위 센서
    SURFACTANT = "surfactant"                   # 계면활성 감지 센서
    METAL_ION = "metal_ion"                     # 금속 이온 민감 센서
    AROMATIC = "aromatic"                       # 방향족 감지 센서
    VOLATILE_ORGANIC = "volatile_organic"       # 휘발성 유기물 센서
    THIOL = "thiol"                             # 티올 감지 센서


class AnomalyDetectionMethod(Enum):
    """이상 탐지 방법"""
    AUTOENCODER = "autoencoder"                 # 오토인코더
    ONE_CLASS_SVM = "one_class_svm"             # 1-클래스 서포트 벡터 머신
    ISOLATION_FOREST = "isolation_forest"       # 격리 포레스트
    LOCAL_OUTLIER = "local_outlier"             # 지역 이상치 인자
    MAHALANOBIS = "mahalanobis"                 # 마할라노비스 거리
    ENSEMBLE = "ensemble"                       # 앙상블


class SubstanceClass(Enum):
    """물질 클래스"""
    KNOWN = "known"                   # 학습된 알려진 물질
    UNKNOWN = "unknown"               # 미지의 물질
    ORGANIC = "organic"               # 유기물 계열
    INORGANIC = "inorganic"           # 무기물 계열
    BIOLOGICAL = "biological"         # 생물학적 물질
    PHARMACEUTICAL = "pharmaceutical"  # 의약품 계열
    TOXIN = "toxin"                   # 독소 계열
    HEAVY_METAL = "heavy_metal"       # 중금속 계열
    VOLATILE = "volatile"             # 휘발성 물질


@dataclass
class SensorElement:
    """반특이적 감지 소자"""
    element_id: int
    element_type: SensorElementType
    sensitivity: float = 1.0  # 감도 계수
    response_range: Tuple[float, float] = (0.0, 1.0)
    noise_level: float = 0.01
    is_active: bool = True

    def generate_response(self, analyte_profile: np.ndarray) -> float:
        """
        분석물 프로파일에 대한 응답 생성

        각 반특이적 감지 소자는 복수의 분석물에 대해 상이한 반응 패턴을 생성
        """
        # 소자 유형에 따른 응답 특성 매트릭스
        type_weights = self._get_type_weights()

        # 가중 합으로 응답 계산
        response = np.dot(analyte_profile, type_weights) * self.sensitivity

        # 노이즈 추가
        response += np.random.normal(0, self.noise_level)

        # 범위 제한
        return np.clip(response, self.response_range[0], self.response_range[1])

    def _get_type_weights(self) -> np.ndarray:
        """소자 유형별 응답 가중치"""
        # 각 유형별 분석물 클래스에 대한 응답 특성
        weights_map = {
            SensorElementType.BROAD_OXIDASE: [0.8, 0.3, 0.5, 0.1, 0.7],
            SensorElementType.NON_SPECIFIC_IG: [0.2, 0.9, 0.6, 0.4, 0.1],
            SensorElementType.PH_SENSITIVE: [0.1, 0.2, 0.9, 0.3, 0.2],
            SensorElementType.CONDUCTIVITY: [0.5, 0.4, 0.3, 0.9, 0.6],
            SensorElementType.REDOX_POTENTIAL: [0.9, 0.3, 0.4, 0.2, 0.8],
            SensorElementType.SURFACTANT: [0.3, 0.6, 0.2, 0.5, 0.4],
            SensorElementType.METAL_ION: [0.1, 0.2, 0.1, 0.8, 0.3],
            SensorElementType.AROMATIC: [0.4, 0.1, 0.3, 0.2, 0.9],
            SensorElementType.VOLATILE_ORGANIC: [0.6, 0.2, 0.4, 0.3, 0.7],
            SensorElementType.THIOL: [0.7, 0.5, 0.2, 0.4, 0.3],
        }
        return np.array(weights_map.get(self.element_type, [0.5] * 5))


@dataclass
class Fingerprint:
    """핑거프린트 벡터"""
    vector: np.ndarray
    timestamp: datetime = field(default_factory=datetime.now)
    normalized: bool = False
    quality_score: float = 1.0
    metadata: dict = field(default_factory=dict)


@dataclass
class AnomalyDetectionResult:
    """이상 탐지 결과"""
    is_anomaly: bool = False
    anomaly_score: float = 0.0  # 이상 점수 (높을수록 이상)
    threshold: float = 0.5
    confidence: float = 0.0
    method: AnomalyDetectionMethod = AnomalyDetectionMethod.ENSEMBLE
    details: dict = field(default_factory=dict)


@dataclass
class InverseInferenceResult:
    """역추론 결과"""
    detected_substances: List[str] = field(default_factory=list)
    substance_class: SubstanceClass = SubstanceClass.UNKNOWN
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    is_unknown: bool = True
    estimated_concentration: Optional[float] = None
    warning_flags: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class CrossReactiveSensorArray:
    """
    교차반응성 센서 어레이 (Cross-Reactive Sensor Array)

    복수의 반특이적 감지 소자를 포함하며, 각 소자는 복수의 분석물에 대해
    상이한 반응 패턴을 생성함.

    특허 참조: 도 23
    """

    def __init__(self,
                 n_elements: int = 8,
                 element_types: Optional[List[SensorElementType]] = None):
        """
        초기화

        Args:
            n_elements: 감지 소자 개수
            element_types: 감지 소자 유형 리스트
        """
        self.n_elements = n_elements

        # 기본 센서 유형 배열
        if element_types is None:
            element_types = [
                SensorElementType.BROAD_OXIDASE,
                SensorElementType.NON_SPECIFIC_IG,
                SensorElementType.PH_SENSITIVE,
                SensorElementType.CONDUCTIVITY,
                SensorElementType.REDOX_POTENTIAL,
                SensorElementType.SURFACTANT,
                SensorElementType.METAL_ION,
                SensorElementType.AROMATIC,
            ][:n_elements]

        # 감지 소자 생성
        self.elements: List[SensorElement] = []
        for i, etype in enumerate(element_types):
            element = SensorElement(
                element_id=i,
                element_type=etype,
                sensitivity=1.0 + np.random.uniform(-0.1, 0.1)
            )
            self.elements.append(element)

        # 참조 소자 (각 감지 소자에 대응)
        self.reference_elements: List[SensorElement] = []
        for elem in self.elements:
            ref_elem = SensorElement(
                element_id=elem.element_id + 100,
                element_type=elem.element_type,
                sensitivity=elem.sensitivity,
                is_active=True
            )
            # 참조 소자는 분석물에 반응하지 않음
            ref_elem.sensitivity = 0.0
            self.reference_elements.append(ref_elem)

    def measure(self, sample_profile: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        시료 측정

        Args:
            sample_profile: 시료 프로파일 벡터

        Returns:
            Tuple[np.ndarray, np.ndarray]: (감지 신호 배열, 참조 신호 배열)
        """
        sensing_signals = []
        reference_signals = []

        for elem, ref_elem in zip(self.elements, self.reference_elements):
            if elem.is_active:
                # 감지 소자 응답
                sensing = elem.generate_response(sample_profile)
                sensing_signals.append(sensing)

                # 참조 소자 응답 (분석물에 반응하지 않고 환경 노이즈만)
                ref = np.random.normal(0, elem.noise_level)
                reference_signals.append(ref)

        return np.array(sensing_signals), np.array(reference_signals)

    def differential_measure(self, sample_profile: np.ndarray) -> np.ndarray:
        """
        차동 측정

        Args:
            sample_profile: 시료 프로파일 벡터

        Returns:
            np.ndarray: 차동 신호 배열
        """
        sensing, reference = self.measure(sample_profile)
        return sensing - reference

    def get_element_info(self) -> List[dict]:
        """감지 소자 정보 조회"""
        return [
            {
                "id": elem.element_id,
                "type": elem.element_type.value,
                "sensitivity": elem.sensitivity,
                "is_active": elem.is_active,
            }
            for elem in self.elements
        ]


class FingerprintGenerator:
    """
    핑거프린트 생성부 (Fingerprint Generation Unit)

    각 채널의 차동 신호를 정규화하고 벡터화하여 시료 고유의 핑거프린트 패턴을 생성.

    특허 참조: 도 24
    """

    def __init__(self,
                 normalization_method: str = 'minmax',
                 feature_extraction: str = 'raw'):
        """
        초기화

        Args:
            normalization_method: 정규화 방법 ('minmax', 'zscore', 'l2')
            feature_extraction: 특징 추출 방법 ('raw', 'gradient', 'fft')
        """
        self.normalization_method = normalization_method
        self.feature_extraction = feature_extraction

        # 정규화 파라미터
        self._min_values: Optional[np.ndarray] = None
        self._max_values: Optional[np.ndarray] = None
        self._mean_values: Optional[np.ndarray] = None
        self._std_values: Optional[np.ndarray] = None

    def fit(self, reference_data: np.ndarray) -> None:
        """
        정규화 파라미터 학습

        Args:
            reference_data: 참조 데이터 (n_samples x n_features)
        """
        if self.normalization_method == 'minmax':
            self._min_values = np.min(reference_data, axis=0)
            self._max_values = np.max(reference_data, axis=0)
        elif self.normalization_method == 'zscore':
            self._mean_values = np.mean(reference_data, axis=0)
            self._std_values = np.std(reference_data, axis=0)

    def generate(self,
                 differential_signals: np.ndarray,
                 timestamp: Optional[datetime] = None) -> Fingerprint:
        """
        핑거프린트 생성

        Args:
            differential_signals: 차동 신호 배열
            timestamp: 타임스탬프

        Returns:
            Fingerprint: 핑거프린트 객체
        """
        # 특징 추출
        if self.feature_extraction == 'gradient':
            features = np.gradient(differential_signals)
        elif self.feature_extraction == 'fft':
            features = np.abs(np.fft.fft(differential_signals))[:len(differential_signals)//2]
        else:
            features = differential_signals.copy()

        # 정규화
        normalized = self._normalize(features)

        # 품질 점수 계산
        quality = self._calculate_quality(differential_signals)

        return Fingerprint(
            vector=normalized,
            timestamp=timestamp or datetime.now(),
            normalized=True,
            quality_score=quality,
        )

    def _normalize(self, features: np.ndarray) -> np.ndarray:
        """정규화"""
        if self.normalization_method == 'minmax':
            if self._min_values is not None and self._max_values is not None:
                range_vals = self._max_values - self._min_values
                range_vals[range_vals == 0] = 1
                return (features - self._min_values) / range_vals
            else:
                min_val, max_val = features.min(), features.max()
                if max_val - min_val == 0:
                    return np.zeros_like(features)
                return (features - min_val) / (max_val - min_val)

        elif self.normalization_method == 'zscore':
            if self._mean_values is not None and self._std_values is not None:
                std_vals = self._std_values.copy()
                std_vals[std_vals == 0] = 1
                return (features - self._mean_values) / std_vals
            else:
                mean, std = features.mean(), features.std()
                if std == 0:
                    return np.zeros_like(features)
                return (features - mean) / std

        elif self.normalization_method == 'l2':
            norm = np.linalg.norm(features)
            if norm == 0:
                return features
            return features / norm

        return features

    def _calculate_quality(self, signals: np.ndarray) -> float:
        """품질 점수 계산"""
        # 신호 강도와 변동성 기반 품질
        signal_strength = np.mean(np.abs(signals))
        signal_variance = np.var(signals)

        quality = min(1.0, signal_strength * 0.5 + (1 - min(1, signal_variance)) * 0.5)
        return quality


class AnomalyDetector:
    """
    이상 탐지부 (Anomaly Detection Unit)

    핑거프린트 벡터를 정상 패턴 데이터베이스와 비교하여 이상 여부를 판정.
    오토인코더, 1-클래스 SVM, 격리 포레스트 등의 알고리즘 지원.

    특허 참조: 도 25
    """

    def __init__(self,
                 method: AnomalyDetectionMethod = AnomalyDetectionMethod.ENSEMBLE,
                 threshold: float = 0.5,
                 contamination: float = 0.1):
        """
        초기화

        Args:
            method: 이상 탐지 방법
            threshold: 이상 판정 임계값
            contamination: 예상 이상치 비율
        """
        self.method = method
        self.threshold = threshold
        self.contamination = contamination

        # 학습된 정상 패턴
        self._normal_patterns: Optional[np.ndarray] = None
        self._normal_mean: Optional[np.ndarray] = None
        self._normal_cov: Optional[np.ndarray] = None

        # 오토인코더 가중치 (간단한 구현)
        self._autoencoder_weights: Optional[dict] = None

    def fit(self, normal_fingerprints: np.ndarray) -> None:
        """
        정상 패턴 학습

        Args:
            normal_fingerprints: 정상 핑거프린트 배열 (n_samples x n_features)
        """
        self._normal_patterns = normal_fingerprints
        self._normal_mean = np.mean(normal_fingerprints, axis=0)
        self._normal_cov = np.cov(normal_fingerprints.T) + np.eye(normal_fingerprints.shape[1]) * 1e-6

        # 오토인코더 학습 (간단한 PCA 기반 구현)
        if self.method in [AnomalyDetectionMethod.AUTOENCODER, AnomalyDetectionMethod.ENSEMBLE]:
            self._train_autoencoder(normal_fingerprints)

    def _train_autoencoder(self, data: np.ndarray, latent_dim: int = 4) -> None:
        """간단한 오토인코더 학습 (PCA 기반)"""
        # 중심화
        centered = data - self._normal_mean

        # SVD를 이용한 PCA
        U, S, Vt = np.linalg.svd(centered, full_matrices=False)

        # 인코더/디코더 행렬
        self._autoencoder_weights = {
            'encoder': Vt[:latent_dim].T,
            'decoder': Vt[:latent_dim],
            'mean': self._normal_mean,
        }

    def detect(self, fingerprint: Fingerprint) -> AnomalyDetectionResult:
        """
        이상 탐지

        Args:
            fingerprint: 핑거프린트 객체

        Returns:
            AnomalyDetectionResult: 이상 탐지 결과
        """
        vector = fingerprint.vector

        if self._normal_patterns is None:
            return AnomalyDetectionResult(
                is_anomaly=True,
                anomaly_score=1.0,
                confidence=0.0,
                details={"error": "No normal patterns trained"}
            )

        scores = {}

        # 방법별 이상 점수 계산
        if self.method in [AnomalyDetectionMethod.MAHALANOBIS, AnomalyDetectionMethod.ENSEMBLE]:
            scores['mahalanobis'] = self._mahalanobis_score(vector)

        if self.method in [AnomalyDetectionMethod.AUTOENCODER, AnomalyDetectionMethod.ENSEMBLE]:
            scores['autoencoder'] = self._autoencoder_score(vector)

        if self.method in [AnomalyDetectionMethod.ISOLATION_FOREST, AnomalyDetectionMethod.ENSEMBLE]:
            scores['isolation_forest'] = self._isolation_forest_score(vector)

        if self.method in [AnomalyDetectionMethod.ONE_CLASS_SVM, AnomalyDetectionMethod.ENSEMBLE]:
            scores['one_class_svm'] = self._one_class_svm_score(vector)

        if self.method in [AnomalyDetectionMethod.LOCAL_OUTLIER, AnomalyDetectionMethod.ENSEMBLE]:
            scores['local_outlier'] = self._local_outlier_score(vector)

        # 최종 점수 계산
        if len(scores) > 0:
            final_score = np.mean(list(scores.values()))
        else:
            final_score = 0.5

        # 이상 판정
        is_anomaly = final_score > self.threshold
        confidence = abs(final_score - self.threshold) / max(self.threshold, 1 - self.threshold)

        return AnomalyDetectionResult(
            is_anomaly=is_anomaly,
            anomaly_score=final_score,
            threshold=self.threshold,
            confidence=min(1.0, confidence),
            method=self.method,
            details=scores,
        )

    def _mahalanobis_score(self, vector: np.ndarray) -> float:
        """마할라노비스 거리 기반 점수"""
        diff = vector - self._normal_mean
        try:
            inv_cov = np.linalg.inv(self._normal_cov)
            distance = np.sqrt(diff @ inv_cov @ diff)
        except np.linalg.LinAlgError:
            distance = np.linalg.norm(diff)

        # 정규화 (chi-square 분포 기반)
        df = len(vector)
        threshold_99 = df + 2 * np.sqrt(2 * df)  # 99% 신뢰구간 근사
        return min(1.0, distance / threshold_99)

    def _autoencoder_score(self, vector: np.ndarray) -> float:
        """오토인코더 재구성 오차 기반 점수"""
        if self._autoencoder_weights is None:
            return 0.5

        # 인코딩
        centered = vector - self._autoencoder_weights['mean']
        latent = centered @ self._autoencoder_weights['encoder']

        # 디코딩
        reconstructed = latent @ self._autoencoder_weights['decoder']
        reconstructed += self._autoencoder_weights['mean']

        # 재구성 오차
        mse = np.mean((vector - reconstructed) ** 2)

        # 정규화
        return min(1.0, mse / 0.1)

    def _isolation_forest_score(self, vector: np.ndarray) -> float:
        """격리 포레스트 기반 점수 (간단한 구현)"""
        # 평균과의 거리 기반 간단한 근사
        distances = np.linalg.norm(self._normal_patterns - vector, axis=1)
        avg_distance = np.mean(distances)
        normal_avg = np.mean(np.linalg.norm(
            self._normal_patterns - self._normal_mean, axis=1
        ))

        return min(1.0, avg_distance / (normal_avg * 3 + 1e-6))

    def _one_class_svm_score(self, vector: np.ndarray) -> float:
        """1-클래스 SVM 기반 점수 (간단한 RBF 거리 구현)"""
        # RBF 커널 기반 거리
        gamma = 1.0 / len(vector)
        kernel_values = np.exp(-gamma * np.sum((self._normal_patterns - vector) ** 2, axis=1))
        decision = np.mean(kernel_values)

        # 점수 변환 (낮은 커널 값 = 이상)
        return 1.0 - min(1.0, decision)

    def _local_outlier_score(self, vector: np.ndarray, k: int = 5) -> float:
        """지역 이상치 인자 기반 점수"""
        distances = np.linalg.norm(self._normal_patterns - vector, axis=1)
        k_nearest = np.sort(distances)[:k]
        local_density = 1.0 / (np.mean(k_nearest) + 1e-6)

        # 정상 데이터의 평균 지역 밀도
        normal_densities = []
        for p in self._normal_patterns[:min(50, len(self._normal_patterns))]:
            d = np.linalg.norm(self._normal_patterns - p, axis=1)
            d_sorted = np.sort(d)[1:k+1]  # 자기 자신 제외
            normal_densities.append(1.0 / (np.mean(d_sorted) + 1e-6))

        avg_normal_density = np.mean(normal_densities)

        # LOF 점수
        lof = avg_normal_density / (local_density + 1e-6)
        return min(1.0, max(0.0, (lof - 1) / 2))


class InverseInferenceEngine:
    """
    역추론부 (Inverse Inference Unit)

    이상으로 판정된 경우 핑거프린트 벡터를 역분석하여 원인 물질을 추정.
    학습 데이터베이스에 포함된 물질과 포함되지 않은 미지의 물질을 모두 탐지.

    특허 참조: 도 25
    """

    def __init__(self):
        """초기화"""
        # 학습된 물질 데이터베이스
        self._substance_database: Dict[str, np.ndarray] = {}
        self._substance_classes: Dict[str, SubstanceClass] = {}

        # 물질 클래스별 프로토타입
        self._class_prototypes: Dict[SubstanceClass, np.ndarray] = {}

    def add_substance(self,
                      name: str,
                      fingerprint: np.ndarray,
                      substance_class: SubstanceClass = SubstanceClass.KNOWN) -> None:
        """
        물질 데이터베이스에 추가

        Args:
            name: 물질 이름
            fingerprint: 핑거프린트 벡터
            substance_class: 물질 클래스
        """
        self._substance_database[name] = fingerprint
        self._substance_classes[name] = substance_class

        # 클래스 프로토타입 업데이트
        if substance_class not in self._class_prototypes:
            self._class_prototypes[substance_class] = fingerprint.copy()
        else:
            self._class_prototypes[substance_class] = (
                self._class_prototypes[substance_class] + fingerprint
            ) / 2

    def infer(self,
              fingerprint: Fingerprint,
              anomaly_result: AnomalyDetectionResult,
              top_k: int = 3) -> InverseInferenceResult:
        """
        역추론 수행

        Args:
            fingerprint: 핑거프린트 객체
            anomaly_result: 이상 탐지 결과
            top_k: 상위 후보 개수

        Returns:
            InverseInferenceResult: 역추론 결과
        """
        vector = fingerprint.vector
        warning_flags = []

        # 이상이 아닌 경우 (정상 시료)
        if not anomaly_result.is_anomaly:
            return InverseInferenceResult(
                detected_substances=["normal"],
                substance_class=SubstanceClass.KNOWN,
                confidence_scores={"normal": 1.0 - anomaly_result.anomaly_score},
                is_unknown=False,
            )

        # 데이터베이스가 비어있는 경우
        if not self._substance_database:
            return InverseInferenceResult(
                detected_substances=[],
                substance_class=SubstanceClass.UNKNOWN,
                is_unknown=True,
                warning_flags=["empty_database"],
            )

        # 알려진 물질과의 유사도 계산
        similarities = {}
        for name, db_fingerprint in self._substance_database.items():
            # 코사인 유사도
            similarity = self._cosine_similarity(vector, db_fingerprint)
            similarities[name] = similarity

        # 상위 K개 후보
        sorted_substances = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
        top_substances = sorted_substances[:top_k]

        # 최고 유사도 확인
        max_similarity = top_substances[0][1] if top_substances else 0

        # 미지 물질 판정
        is_unknown = max_similarity < 0.7  # 유사도 임계값

        if is_unknown:
            # 물질 클래스 추정
            estimated_class = self._estimate_class(vector)
            warning_flags.append("unknown_substance")

            return InverseInferenceResult(
                detected_substances=[],
                substance_class=estimated_class,
                confidence_scores={},
                is_unknown=True,
                warning_flags=warning_flags,
                metadata={
                    "max_similarity": max_similarity,
                    "closest_known": top_substances[0][0] if top_substances else None,
                }
            )
        else:
            # 알려진 물질로 동정
            detected = [name for name, _ in top_substances if similarities[name] > 0.5]
            confidence_scores = {name: sim for name, sim in top_substances}

            # 물질 클래스
            if detected:
                substance_class = self._substance_classes.get(
                    detected[0], SubstanceClass.KNOWN
                )
            else:
                substance_class = SubstanceClass.UNKNOWN

            return InverseInferenceResult(
                detected_substances=detected,
                substance_class=substance_class,
                confidence_scores=confidence_scores,
                is_unknown=False,
                metadata={
                    "all_similarities": similarities,
                }
            )

    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """코사인 유사도 계산"""
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return np.dot(v1, v2) / (norm1 * norm2)

    def _estimate_class(self, vector: np.ndarray) -> SubstanceClass:
        """물질 클래스 추정"""
        if not self._class_prototypes:
            return SubstanceClass.UNKNOWN

        best_class = SubstanceClass.UNKNOWN
        best_similarity = -1

        for cls, prototype in self._class_prototypes.items():
            similarity = self._cosine_similarity(vector, prototype)
            if similarity > best_similarity:
                best_similarity = similarity
                best_class = cls

        # 유사도가 너무 낮으면 미지 물질
        if best_similarity < 0.3:
            return SubstanceClass.UNKNOWN

        return best_class


class NonTargetedAnalysisSystem:
    """
    비표적 분석 시스템 (Non-Targeted Analysis System)

    교차반응성 센서 어레이와 역추론 알고리즘을 결합하여,
    학습 데이터베이스에 포함된 물질과 포함되지 않은 미지의 물질을 모두 탐지.

    Example:
        >>> system = NonTargetedAnalysisSystem()
        >>> system.train_normal_patterns(normal_samples)
        >>> system.add_known_substance("caffeine", caffeine_fingerprint)
        >>> result = system.analyze(sample_profile)
        >>> if result.is_anomaly:
        ...     print(f"이상 탐지: {result.inference.substance_class}")
    """

    def __init__(self,
                 n_sensor_elements: int = 8,
                 anomaly_threshold: float = 0.5):
        """
        초기화

        Args:
            n_sensor_elements: 센서 소자 개수
            anomaly_threshold: 이상 판정 임계값
        """
        # 구성 요소
        self.sensor_array = CrossReactiveSensorArray(n_elements=n_sensor_elements)
        self.fingerprint_generator = FingerprintGenerator()
        self.anomaly_detector = AnomalyDetector(
            method=AnomalyDetectionMethod.ENSEMBLE,
            threshold=anomaly_threshold
        )
        self.inference_engine = InverseInferenceEngine()

        # 상태
        self._is_trained = False
        self._normal_fingerprints: List[Fingerprint] = []

    def train_normal_patterns(self, normal_samples: np.ndarray) -> None:
        """
        정상 패턴 학습

        Args:
            normal_samples: 정상 시료 프로파일 배열 (n_samples x n_features)
        """
        fingerprint_vectors = []

        for sample in normal_samples:
            # 차동 측정
            diff_signals = self.sensor_array.differential_measure(sample)

            # 핑거프린트 생성
            fp = self.fingerprint_generator.generate(diff_signals)
            self._normal_fingerprints.append(fp)
            fingerprint_vectors.append(fp.vector)

        fingerprint_matrix = np.array(fingerprint_vectors)

        # 핑거프린트 생성기 학습
        self.fingerprint_generator.fit(fingerprint_matrix)

        # 이상 탐지기 학습
        self.anomaly_detector.fit(fingerprint_matrix)

        self._is_trained = True

    def add_known_substance(self,
                            name: str,
                            sample_profile: np.ndarray,
                            substance_class: SubstanceClass = SubstanceClass.KNOWN) -> None:
        """
        알려진 물질 등록

        Args:
            name: 물질 이름
            sample_profile: 시료 프로파일
            substance_class: 물질 클래스
        """
        # 핑거프린트 생성
        diff_signals = self.sensor_array.differential_measure(sample_profile)
        fp = self.fingerprint_generator.generate(diff_signals)

        # 데이터베이스에 추가
        self.inference_engine.add_substance(name, fp.vector, substance_class)

    def analyze(self, sample_profile: np.ndarray) -> 'AnalysisResult':
        """
        시료 분석

        Args:
            sample_profile: 시료 프로파일 벡터

        Returns:
            AnalysisResult: 분석 결과
        """
        if not self._is_trained:
            raise RuntimeError("시스템이 학습되지 않았습니다. train_normal_patterns()를 먼저 호출하세요.")

        # 차동 측정
        sensing, reference = self.sensor_array.measure(sample_profile)
        diff_signals = sensing - reference

        # 핑거프린트 생성
        fingerprint = self.fingerprint_generator.generate(diff_signals)

        # 이상 탐지
        anomaly_result = self.anomaly_detector.detect(fingerprint)

        # 역추론
        inference_result = self.inference_engine.infer(fingerprint, anomaly_result)

        return AnalysisResult(
            fingerprint=fingerprint,
            anomaly=anomaly_result,
            inference=inference_result,
            raw_signals={
                'sensing': sensing,
                'reference': reference,
                'differential': diff_signals,
            }
        )


@dataclass
class AnalysisResult:
    """비표적 분석 결과"""
    fingerprint: Fingerprint
    anomaly: AnomalyDetectionResult
    inference: InverseInferenceResult
    raw_signals: Dict[str, np.ndarray] = field(default_factory=dict)

    @property
    def is_anomaly(self) -> bool:
        """이상 여부"""
        return self.anomaly.is_anomaly

    @property
    def is_unknown(self) -> bool:
        """미지 물질 여부"""
        return self.inference.is_unknown

    def summary(self) -> str:
        """결과 요약"""
        lines = [
            f"=== 비표적 분석 결과 ===",
            f"이상 여부: {'예' if self.is_anomaly else '아니오'}",
            f"이상 점수: {self.anomaly.anomaly_score:.3f}",
            f"미지 물질: {'예' if self.is_unknown else '아니오'}",
            f"물질 클래스: {self.inference.substance_class.value}",
        ]

        if self.inference.detected_substances:
            lines.append(f"검출 물질: {', '.join(self.inference.detected_substances)}")

        if self.inference.warning_flags:
            lines.append(f"경고: {', '.join(self.inference.warning_flags)}")

        return '\n'.join(lines)
