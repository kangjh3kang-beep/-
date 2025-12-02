"""
시각화 모듈

측정 데이터의 시각화 기능을 제공합니다.
matplotlib 기반으로 다양한 플롯을 생성합니다.
"""

from typing import Dict, List, Optional, Tuple, Union, Any
import numpy as np


class MeasurementPlotter:
    """
    측정 데이터 시각화 클래스

    다양한 형태의 측정 데이터 플롯을 생성합니다.

    Note:
        matplotlib이 설치되어 있어야 합니다.
        설치: pip install matplotlib

    Example:
        >>> plotter = MeasurementPlotter()
        >>> plotter.plot_time_series(data, timestamps)
        >>> plotter.show()
    """

    def __init__(self,
                 style: str = 'default',
                 figsize: Tuple[int, int] = (12, 6),
                 dpi: int = 100):
        """
        초기화

        Args:
            style: matplotlib 스타일
            figsize: 기본 그림 크기
            dpi: 해상도
        """
        self.figsize = figsize
        self.dpi = dpi
        self.style = style

        self._plt = None
        self._fig = None
        self._axes = None

        self._check_matplotlib()

    def _check_matplotlib(self) -> None:
        """matplotlib 설치 확인"""
        try:
            import matplotlib.pyplot as plt
            self._plt = plt
            if self.style != 'default':
                try:
                    plt.style.use(self.style)
                except Exception:
                    pass
        except ImportError:
            self._plt = None

    def _ensure_matplotlib(self) -> Any:
        """matplotlib 사용 가능 확인"""
        if self._plt is None:
            raise ImportError(
                "시각화를 위해 matplotlib을 설치하세요: pip install matplotlib"
            )
        return self._plt

    def plot_time_series(self,
                         data: Union[np.ndarray, Dict[str, np.ndarray]],
                         timestamps: Optional[np.ndarray] = None,
                         title: str = "Time Series",
                         xlabel: str = "Time (s)",
                         ylabel: str = "Amplitude",
                         legend: bool = True,
                         grid: bool = True) -> Any:
        """
        시계열 플롯

        Args:
            data: 데이터 (배열 또는 {채널명: 데이터} 딕셔너리)
            timestamps: 타임스탬프
            title: 제목
            xlabel: X축 레이블
            ylabel: Y축 레이블
            legend: 범례 표시 여부
            grid: 그리드 표시 여부

        Returns:
            matplotlib Figure 객체
        """
        plt = self._ensure_matplotlib()

        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

        if isinstance(data, dict):
            for label, arr in data.items():
                arr = np.asarray(arr)
                if timestamps is None:
                    t = np.arange(len(arr))
                else:
                    t = timestamps[:len(arr)]
                ax.plot(t, arr, label=label)
        else:
            data = np.asarray(data)
            if timestamps is None:
                timestamps = np.arange(len(data))
            ax.plot(timestamps, data)

        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        if grid:
            ax.grid(True, alpha=0.3)

        if legend and isinstance(data, dict) and len(data) > 0:
            ax.legend()

        plt.tight_layout()
        self._fig = fig
        self._axes = ax

        return fig

    def plot_differential(self,
                          positive: np.ndarray,
                          negative: np.ndarray,
                          differential: np.ndarray,
                          timestamps: Optional[np.ndarray] = None,
                          title: str = "Differential Measurement") -> Any:
        """
        차동측정 플롯 (3개 서브플롯)

        Args:
            positive: 양극 채널 데이터
            negative: 음극 채널 데이터
            differential: 차동 신호
            timestamps: 타임스탬프
            title: 제목

        Returns:
            matplotlib Figure 객체
        """
        plt = self._ensure_matplotlib()

        fig, axes = plt.subplots(3, 1, figsize=(self.figsize[0], self.figsize[1] * 1.5),
                                 dpi=self.dpi, sharex=True)

        positive = np.asarray(positive)
        negative = np.asarray(negative)
        differential = np.asarray(differential)

        if timestamps is None:
            timestamps = np.arange(len(positive))

        # 양극 채널
        axes[0].plot(timestamps[:len(positive)], positive, 'b-', label='Positive')
        axes[0].set_ylabel('CH+ (V)')
        axes[0].legend(loc='upper right')
        axes[0].grid(True, alpha=0.3)

        # 음극 채널
        axes[1].plot(timestamps[:len(negative)], negative, 'r-', label='Negative')
        axes[1].set_ylabel('CH- (V)')
        axes[1].legend(loc='upper right')
        axes[1].grid(True, alpha=0.3)

        # 차동 신호
        axes[2].plot(timestamps[:len(differential)], differential, 'g-', label='Differential')
        axes[2].set_xlabel('Time (s)')
        axes[2].set_ylabel('Diff (V)')
        axes[2].legend(loc='upper right')
        axes[2].grid(True, alpha=0.3)

        fig.suptitle(title)
        plt.tight_layout()

        self._fig = fig
        self._axes = axes

        return fig

    def plot_spectrum(self,
                      frequencies: np.ndarray,
                      magnitude_db: np.ndarray,
                      title: str = "Frequency Spectrum",
                      xlabel: str = "Frequency (Hz)",
                      ylabel: str = "Magnitude (dB)",
                      xlim: Optional[Tuple[float, float]] = None,
                      ylim: Optional[Tuple[float, float]] = None) -> Any:
        """
        스펙트럼 플롯

        Args:
            frequencies: 주파수 배열
            magnitude_db: 크기 (dB)
            title: 제목
            xlabel: X축 레이블
            ylabel: Y축 레이블
            xlim: X축 범위
            ylim: Y축 범위

        Returns:
            matplotlib Figure 객체
        """
        plt = self._ensure_matplotlib()

        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

        ax.plot(frequencies, magnitude_db, 'b-', linewidth=0.8)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)

        if xlim:
            ax.set_xlim(xlim)
        if ylim:
            ax.set_ylim(ylim)

        plt.tight_layout()
        self._fig = fig
        self._axes = ax

        return fig

    def plot_spectrogram(self,
                         times: np.ndarray,
                         frequencies: np.ndarray,
                         spectrogram: np.ndarray,
                         title: str = "Spectrogram",
                         vmin: Optional[float] = None,
                         vmax: Optional[float] = None,
                         cmap: str = 'viridis') -> Any:
        """
        스펙트로그램 플롯

        Args:
            times: 시간 배열
            frequencies: 주파수 배열
            spectrogram: 스펙트로그램 데이터 (dB)
            title: 제목
            vmin: 최소값
            vmax: 최대값
            cmap: 컬러맵

        Returns:
            matplotlib Figure 객체
        """
        plt = self._ensure_matplotlib()

        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

        im = ax.pcolormesh(times, frequencies, spectrogram,
                           shading='auto', cmap=cmap, vmin=vmin, vmax=vmax)

        ax.set_title(title)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Frequency (Hz)')

        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label('Magnitude (dB)')

        plt.tight_layout()
        self._fig = fig
        self._axes = ax

        return fig

    def plot_histogram(self,
                       data: np.ndarray,
                       bins: int = 50,
                       title: str = "Histogram",
                       xlabel: str = "Value",
                       ylabel: str = "Count",
                       density: bool = False) -> Any:
        """
        히스토그램 플롯

        Args:
            data: 데이터
            bins: 빈 개수
            title: 제목
            xlabel: X축 레이블
            ylabel: Y축 레이블
            density: 확률 밀도 여부

        Returns:
            matplotlib Figure 객체
        """
        plt = self._ensure_matplotlib()

        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

        data = np.asarray(data)
        ax.hist(data, bins=bins, density=density, alpha=0.7, edgecolor='black')

        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel if not density else 'Density')
        ax.grid(True, alpha=0.3)

        # 통계 표시
        mean = np.mean(data)
        std = np.std(data)
        ax.axvline(mean, color='r', linestyle='--', label=f'Mean: {mean:.4g}')
        ax.axvline(mean + std, color='g', linestyle=':', alpha=0.7)
        ax.axvline(mean - std, color='g', linestyle=':', alpha=0.7,
                   label=f'Std: {std:.4g}')
        ax.legend()

        plt.tight_layout()
        self._fig = fig
        self._axes = ax

        return fig

    def plot_comparison(self,
                        data_list: List[np.ndarray],
                        labels: List[str],
                        timestamps: Optional[np.ndarray] = None,
                        title: str = "Signal Comparison") -> Any:
        """
        신호 비교 플롯

        Args:
            data_list: 데이터 리스트
            labels: 레이블 리스트
            timestamps: 타임스탬프
            title: 제목

        Returns:
            matplotlib Figure 객체
        """
        plt = self._ensure_matplotlib()

        n_signals = len(data_list)
        fig, axes = plt.subplots(n_signals, 1,
                                 figsize=(self.figsize[0], self.figsize[1] * n_signals / 2),
                                 dpi=self.dpi, sharex=True)

        if n_signals == 1:
            axes = [axes]

        for i, (data, label) in enumerate(zip(data_list, labels)):
            data = np.asarray(data)
            if timestamps is None:
                t = np.arange(len(data))
            else:
                t = timestamps[:len(data)]

            axes[i].plot(t, data, linewidth=0.8)
            axes[i].set_ylabel(label)
            axes[i].grid(True, alpha=0.3)

        axes[-1].set_xlabel('Time (s)')
        fig.suptitle(title)
        plt.tight_layout()

        self._fig = fig
        self._axes = axes

        return fig

    def plot_xy(self,
                x: np.ndarray,
                y: np.ndarray,
                title: str = "XY Plot",
                xlabel: str = "X",
                ylabel: str = "Y",
                scatter: bool = False) -> Any:
        """
        XY 플롯

        Args:
            x: X 데이터
            y: Y 데이터
            title: 제목
            xlabel: X축 레이블
            ylabel: Y축 레이블
            scatter: 산점도 여부

        Returns:
            matplotlib Figure 객체
        """
        plt = self._ensure_matplotlib()

        fig, ax = plt.subplots(figsize=(self.figsize[1], self.figsize[1]), dpi=self.dpi)

        x = np.asarray(x)
        y = np.asarray(y)

        if scatter:
            ax.scatter(x, y, alpha=0.5, s=10)
        else:
            ax.plot(x, y, linewidth=0.8)

        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal', adjustable='box')

        plt.tight_layout()
        self._fig = fig
        self._axes = ax

        return fig

    def plot_calibration(self,
                         reference: np.ndarray,
                         measured: np.ndarray,
                         fit_line: Optional[Tuple[float, float]] = None,
                         title: str = "Calibration Plot") -> Any:
        """
        캘리브레이션 플롯

        Args:
            reference: 기준값
            measured: 측정값
            fit_line: (기울기, 절편) 튜플
            title: 제목

        Returns:
            matplotlib Figure 객체
        """
        plt = self._ensure_matplotlib()

        fig, ax = plt.subplots(figsize=(self.figsize[1], self.figsize[1]), dpi=self.dpi)

        reference = np.asarray(reference)
        measured = np.asarray(measured)

        # 데이터 포인트
        ax.scatter(measured, reference, s=50, c='blue', label='Calibration Points')

        # 피팅 라인
        if fit_line:
            slope, intercept = fit_line
            x_range = np.array([measured.min(), measured.max()])
            y_fit = slope * x_range + intercept
            ax.plot(x_range, y_fit, 'r-', linewidth=2,
                    label=f'Fit: y = {slope:.4f}x + {intercept:.4f}')

        # 이상적인 1:1 라인
        ideal_range = np.array([min(measured.min(), reference.min()),
                                max(measured.max(), reference.max())])
        ax.plot(ideal_range, ideal_range, 'k--', alpha=0.5, label='Ideal (1:1)')

        ax.set_title(title)
        ax.set_xlabel('Measured Value')
        ax.set_ylabel('Reference Value')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal', adjustable='box')

        plt.tight_layout()
        self._fig = fig
        self._axes = ax

        return fig

    def create_dashboard(self,
                         time_data: Dict[str, np.ndarray],
                         spectrum_data: Optional[Tuple[np.ndarray, np.ndarray]] = None,
                         statistics: Optional[Dict] = None,
                         timestamps: Optional[np.ndarray] = None,
                         title: str = "Measurement Dashboard") -> Any:
        """
        대시보드 생성 (다중 플롯)

        Args:
            time_data: 시계열 데이터
            spectrum_data: (주파수, 크기) 튜플
            statistics: 통계 정보
            timestamps: 타임스탬프
            title: 제목

        Returns:
            matplotlib Figure 객체
        """
        plt = self._ensure_matplotlib()

        # 레이아웃 결정
        n_plots = 1 + (1 if spectrum_data else 0) + (1 if statistics else 0)

        fig = plt.figure(figsize=(self.figsize[0], self.figsize[1] * n_plots / 2),
                         dpi=self.dpi)

        plot_idx = 1

        # 시계열 플롯
        ax1 = fig.add_subplot(n_plots, 1, plot_idx)
        for label, data in time_data.items():
            data = np.asarray(data)
            if timestamps is None:
                t = np.arange(len(data))
            else:
                t = timestamps[:len(data)]
            ax1.plot(t, data, label=label, linewidth=0.8)
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Amplitude')
        ax1.set_title('Time Domain')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        plot_idx += 1

        # 스펙트럼 플롯
        if spectrum_data:
            ax2 = fig.add_subplot(n_plots, 1, plot_idx)
            freqs, mag_db = spectrum_data
            ax2.plot(freqs, mag_db, 'b-', linewidth=0.8)
            ax2.set_xlabel('Frequency (Hz)')
            ax2.set_ylabel('Magnitude (dB)')
            ax2.set_title('Frequency Domain')
            ax2.grid(True, alpha=0.3)
            plot_idx += 1

        # 통계 텍스트
        if statistics:
            ax3 = fig.add_subplot(n_plots, 1, plot_idx)
            ax3.axis('off')

            text_content = "Statistics:\n" + "-" * 30 + "\n"
            for key, value in statistics.items():
                if isinstance(value, float):
                    text_content += f"{key}: {value:.6g}\n"
                else:
                    text_content += f"{key}: {value}\n"

            ax3.text(0.1, 0.9, text_content, transform=ax3.transAxes,
                     fontsize=10, verticalalignment='top', fontfamily='monospace',
                     bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        fig.suptitle(title, fontsize=14, fontweight='bold')
        plt.tight_layout()

        self._fig = fig

        return fig

    def show(self) -> None:
        """플롯 표시"""
        plt = self._ensure_matplotlib()
        plt.show()

    def save(self, filepath: str, **kwargs) -> None:
        """
        플롯 저장

        Args:
            filepath: 저장 경로
            **kwargs: savefig 추가 인자
        """
        if self._fig is None:
            raise ValueError("저장할 플롯이 없습니다.")

        self._fig.savefig(filepath, dpi=self.dpi, bbox_inches='tight', **kwargs)

    def close(self) -> None:
        """플롯 닫기"""
        if self._plt:
            self._plt.close('all')
        self._fig = None
        self._axes = None
