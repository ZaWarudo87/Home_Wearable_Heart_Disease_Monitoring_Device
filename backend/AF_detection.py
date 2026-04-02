import numpy as np

from pan_tompkins_plus_plus.algos.pan_tompkins_plus_plus import (
    Pan_Tompkins_Plus_Plus as RpeakDetection,
)


class AFRdRDetector:
    def __init__(
        self,
        fs_hz: float = 160.0,
        window_beats: int = 128,
        grid_ms: float = 25.0,
        nec_threshold: int = 65,
        hr_max: float = 200.0,
        min_new_rr_for_update: int = 10,
    ):
        self.fs_hz = int(round(fs_hz))
        self.window_beats = int(window_beats)
        self.grid_ms = float(grid_ms)
        self.nec_threshold = int(nec_threshold)
        self.hr_max = float(hr_max)
        self.min_new_rr_for_update = max(1, int(min_new_rr_for_update))

        self._det = RpeakDetection()
        self._rr_intervals: list[float] = []
        self._new_rr_since_eval = 0
        self._last_result = {
            "af_detected": False,
            "nec": None,
            "beats_used": 0,
            "threshold": self.nec_threshold,
        }

    def reset(self) -> None:
        self._rr_intervals.clear()
        self._new_rr_since_eval = 0
        self._last_result = {
            "af_detected": False,
            "nec": None,
            "beats_used": 0,
            "threshold": self.nec_threshold,
        }

    def _apply_refractory(self, peaks: np.ndarray) -> np.ndarray:
        peaks = np.asarray(peaks, dtype=int)
        if peaks.size == 0:
            return peaks

        min_rr_sec = 60.0 / max(self.hr_max, 1e-9)
        refractory = int(round(min_rr_sec * self.fs_hz))
        keep = [int(peaks[0])]
        for index in range(1, len(peaks)):
            if int(peaks[index]) - keep[-1] >= refractory:
                keep.append(int(peaks[index]))
        return np.asarray(keep, dtype=int)

    def _compute_nec(self, rr_sec: np.ndarray) -> int | None:
        rr_ms = np.asarray(rr_sec, dtype=float) * 1000.0
        if rr_ms.size < 2:
            return None

        drr_ms = np.diff(rr_ms)
        rr_points_ms = rr_ms[1:]
        rr_bins = np.floor(rr_points_ms / self.grid_ms).astype(np.int64)
        drr_bins = np.floor(drr_ms / self.grid_ms).astype(np.int64)
        cells = np.column_stack((rr_bins, drr_bins))
        return int(np.unique(cells, axis=0).shape[0])

    def update(self, ecg: np.ndarray) -> dict:
        ecg = np.asarray(ecg, dtype=float)

        peaks = np.asarray(self._det.rpeak_detection(ecg, self.fs_hz), dtype=int)
        peaks = self._apply_refractory(peaks)

        if peaks.size >= 2:
            rr = np.diff(peaks) / float(self.fs_hz)
            rr = rr[(rr >= 0.3) & (rr < 3.0)]
            if rr.size:
                self._rr_intervals.extend(rr.tolist())
                self._new_rr_since_eval += int(rr.size)

        if len(self._rr_intervals) > self.window_beats:
            self._rr_intervals = self._rr_intervals[-self.window_beats :]

        should_eval = (
            len(self._rr_intervals) >= self.window_beats
            and (
                self._last_result["beats_used"] == 0
                or self._new_rr_since_eval >= self.min_new_rr_for_update
            )
        )

        if should_eval:
            rr_window = np.asarray(self._rr_intervals[-self.window_beats :], dtype=float)
            nec = self._compute_nec(rr_window)
            af_detected = bool(nec is not None and nec > self.nec_threshold)

            self._last_result = {
                "af_detected": af_detected,
                "nec": nec,
                "beats_used": int(self.window_beats),
                "threshold": self.nec_threshold,
            }
            self._new_rr_since_eval = 0

        return self._last_result
