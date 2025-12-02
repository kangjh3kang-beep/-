"""
Core 모듈 테스트
"""

import numpy as np
import pytest
import sys
sys.path.insert(0, '..')

from differential_measurement_sdk import (
    DifferentialMeasurement,
    MeasurementChannel,
    CalibrationManager,
    MeasurementSession,
)
from differential_measurement_sdk.core.measurement import MeasurementMode, SignalType


class TestMeasurementChannel:
    """MeasurementChannel 테스트"""

    def test_channel_creation(self):
        """채널 생성 테스트"""
        ch = MeasurementChannel(
            channel_id=0,
            name="Test Channel",
            signal_type=SignalType.VOLTAGE,
            sampling_rate=1000.0
        )

        assert ch.channel_id == 0
        assert ch.name == "Test Channel"
        assert ch.signal_type == SignalType.VOLTAGE
        assert ch.sampling_rate == 1000.0

    def test_set_data(self):
        """데이터 설정 테스트"""
        ch = MeasurementChannel(0, "Test", sampling_rate=100)
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        ch.set_data(data)

        assert ch.sample_count == 5
        np.testing.assert_array_equal(ch.get_raw_data(), data)

    def test_gain_offset(self):
        """게인/오프셋 테스트"""
        ch = MeasurementChannel(0, "Test", gain=2.0, offset=1.0)
        ch.set_data([1.0, 2.0, 3.0])

        expected = np.array([3.0, 5.0, 7.0])  # data * 2 + 1
        np.testing.assert_array_equal(ch.get_data(), expected)


class TestDifferentialMeasurement:
    """DifferentialMeasurement 테스트"""

    def test_basic_differential(self):
        """기본 차동측정 테스트"""
        dm = DifferentialMeasurement()

        ch_pos = MeasurementChannel(0, "CH+")
        ch_neg = MeasurementChannel(1, "CH-")

        ch_pos.set_data([10.0, 20.0, 30.0])
        ch_neg.set_data([1.0, 2.0, 3.0])

        result = dm.measure(ch_pos, ch_neg)

        expected_diff = np.array([9.0, 18.0, 27.0])
        np.testing.assert_array_almost_equal(result.differential_signal, expected_diff)

    def test_common_mode_rejection(self):
        """공통 모드 제거 테스트"""
        dm = DifferentialMeasurement()

        # 공통 모드 노이즈
        common_noise = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        signal = np.array([0.0, 1.0, 2.0, 3.0, 4.0])

        ch_pos = MeasurementChannel(0, "CH+")
        ch_neg = MeasurementChannel(1, "CH-")

        ch_pos.set_data(signal + common_noise)
        ch_neg.set_data(common_noise)

        result = dm.measure(ch_pos, ch_neg)

        np.testing.assert_array_almost_equal(result.differential_signal, signal)

    def test_measurement_modes(self):
        """측정 모드 테스트"""
        ch_pos = MeasurementChannel(0, "CH+")
        ch_neg = MeasurementChannel(1, "CH-")
        ch_pos.set_data([10.0, 20.0, 30.0])
        ch_neg.set_data([2.0, 4.0, 6.0])

        # 차동 모드
        dm_diff = DifferentialMeasurement(mode=MeasurementMode.DIFFERENTIAL)
        result_diff = dm_diff.measure(ch_pos, ch_neg)
        np.testing.assert_array_almost_equal(
            result_diff.differential_signal,
            [8.0, 16.0, 24.0]
        )

        # 비율 모드
        dm_ratio = DifferentialMeasurement(mode=MeasurementMode.RATIOMETRIC)
        result_ratio = dm_ratio.measure(ch_pos, ch_neg)
        np.testing.assert_array_almost_equal(
            result_ratio.differential_signal,
            [5.0, 5.0, 5.0]
        )


class TestCalibrationManager:
    """CalibrationManager 테스트"""

    def test_linear_calibration(self):
        """선형 캘리브레이션 테스트"""
        cal = CalibrationManager()

        # 캘리브레이션 포인트 추가
        cal.add_calibration_point(0, 0.0, 0.1)   # 기준 0, 측정 0.1
        cal.add_calibration_point(0, 5.0, 4.9)   # 기준 5, 측정 4.9
        cal.add_calibration_point(0, 10.0, 9.8)  # 기준 10, 측정 9.8

        params = cal.calculate_calibration(0)

        assert 'gain' in params
        assert 'offset' in params

        # 보정 적용
        corrected = cal.apply_calibration(0, 4.9)
        assert abs(corrected - 5.0) < 0.1

    def test_calibration_export_import(self, tmp_path):
        """캘리브레이션 내보내기/가져오기 테스트"""
        cal = CalibrationManager()
        cal.add_calibration_point(0, 0.0, 0.0)
        cal.add_calibration_point(0, 10.0, 10.0)
        cal.calculate_calibration(0)

        filepath = str(tmp_path / "cal.json")
        cal.export_calibration(0, filepath)

        cal2 = CalibrationManager()
        cal2.import_calibration(filepath)

        assert 0 in cal2._calibration_params


class TestMeasurementSession:
    """MeasurementSession 테스트"""

    def test_session_lifecycle(self):
        """세션 라이프사이클 테스트"""
        from differential_measurement_sdk.core.session import SessionConfig, SessionState

        session = MeasurementSession()

        # 초기 상태
        assert session.state == SessionState.IDLE

        # 설정
        config = SessionConfig(name="Test Session", sampling_rate=1000)
        session.configure(config)
        assert session.state == SessionState.CONFIGURED

        # 채널 추가
        ch = MeasurementChannel(0, "Test")
        session.add_channel(ch)

        # 시작
        session.start()
        assert session.state == SessionState.RUNNING

        # 데이터 추가
        session.add_sample(0, 1.0)
        session.add_sample(0, 2.0)

        # 중지
        session.stop()
        assert session.state == SessionState.STOPPED

        # 데이터 확인
        data = session.get_data(0)
        assert 0 in data
        assert len(data[0]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
