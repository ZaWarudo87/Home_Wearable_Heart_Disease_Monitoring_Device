import numpy as np
from collections import deque

from pan_tompkins_plus_plus.algos.pan_tompkins_plus_plus import (
    Pan_Tompkins_Plus_Plus as RpeakDetection,
)


class AFCVDetector:

    def __init__(
        self,
        fs_hz: float = 160.0,
        window_beats: int = 100,  # number of RR intervals in the window
        cv_rr_ref: float = 0.24,
        rcv_percent: float = 35.0,
        hr_max: float = 200.0,
        voting_windows: int = 5,
        voting_min_positive: int | None = None,
        min_new_rr_for_update: int = 10,
    ):

        self.fs_hz = int(round(fs_hz))
        
        self.window_beats = int(window_beats)
       
        self.cv_rr_ref = float(cv_rr_ref)
        
        self.rcv_percent = float(rcv_percent)
        
        self.hr_max = float(hr_max)
        
        self.voting_windows = int(voting_windows)
       
        self.min_new_rr_for_update = max(1, int(min_new_rr_for_update))
        
        if voting_min_positive is None:
            self.voting_min_positive = self.voting_windows // 2 + 1
        else:
            self.voting_min_positive = int(voting_min_positive)

        # R-peak detector used to derive RR intervals.
        self._det = RpeakDetection()
        # save RR intervals for the current window; updated incrementally with each chunk.
        self._rr_intervals: list[float] = []
        # save result for voting
        self._af_history: deque[bool] = deque(maxlen=self.voting_windows)
        # save count of new RR intervals since last evaluation to control update frequency.
        self._new_rr_since_eval = 0
        
        # Last output returned by update(); preserved when current chunk is insufficient.
        self._last_result = {
            "af_detected": False,
            "af_raw": False,
            "cv_rr": None,
            "beats_used": 0,
            "vote_positive": 0,
            "vote_total": 0,
        }

    def reset(self) -> None:
        # Clear internal state so detection restarts cleanly.
        self._rr_intervals.clear()
        self._af_history.clear()
        self._new_rr_since_eval = 0
        self._last_result = {
            "af_detected": False,
            "af_raw": False,
            "cv_rr": None,
            "beats_used": 0,
            "vote_positive": 0,
            "vote_total": 0,
        }

    def _within_range(self, value: float, ref: float) -> bool:
        # Check if value is within +/- Rcv% of reference CV.
        if not np.isfinite(value) or not np.isfinite(ref):
            return False
        low = ref * (1.0 - self.rcv_percent / 100.0)
        high = ref * (1.0 + self.rcv_percent / 100.0)
        return low <= value <= high

    def _compute_cv_rr(self, rr: np.ndarray) -> float:
        # CV_RR = std(RR)/mean(RR)
        rr = np.asarray(rr, dtype=float)
        if rr.size < 2:
            return np.nan
        mean_rr = float(np.mean(rr))
        if mean_rr <= 0:
            return np.nan
        return float(np.std(rr, ddof=0) / mean_rr)

    def _apply_refractory(self, peaks: np.ndarray) -> np.ndarray:
        # Enforce minimum spacing between adjacent R-peaks to suppress over-detections.
        peaks = np.asarray(peaks, dtype=int)
        if peaks.size == 0:
            return peaks
        min_rr_sec = 60.0 / max(self.hr_max, 1e-9)
        refractory = int(round(min_rr_sec * self.fs_hz))
        keep = [int(peaks[0])]
        for k in range(1, len(peaks)):
            if int(peaks[k]) - keep[-1] >= refractory:
                keep.append(int(peaks[k]))
        return np.asarray(keep, dtype=int)

    def update(self, ecg: np.ndarray) -> dict:
        # Feed one ECG chunk and return the latest AF decision payload.
        ecg = np.asarray(ecg, dtype=float)

        # 1) Detect and clean R peaks.
        peaks = np.asarray(self._det.rpeak_detection(ecg, self.fs_hz), dtype=int)
        peaks = self._apply_refractory(peaks)

        # 2) Convert peaks to RR intervals (seconds), then basic physiological filtering.
        if peaks.size >= 2:
            rr = np.diff(peaks) / float(self.fs_hz)
            # Keep only a high-end guard for extreme gaps/outliers.
            rr = rr[rr < 3.0]
            if rr.size:
                self._rr_intervals.extend(rr.tolist())
                self._new_rr_since_eval += int(rr.size)

        # 3) Keep a fixed-size rolling window (no unbounded memory growth).
        cap = self.window_beats
        if len(self._rr_intervals) > cap:
            self._rr_intervals = self._rr_intervals[-cap:]

        # 4) Evaluate only when window is full and enough fresh RR arrived.
        should_eval = (
            len(self._rr_intervals) >= self.window_beats
            and (
                self._last_result["cv_rr"] is None
                or self._new_rr_since_eval >= self.min_new_rr_for_update
            )
        )
        if should_eval:
            rr_window = np.asarray(self._rr_intervals[-self.window_beats :], dtype=float)
            cv_rr = self._compute_cv_rr(rr_window)

            # 5) CV test: AF when CV_RR falls inside reference tolerance band.
            af_rr = self._within_range(cv_rr, self.cv_rr_ref)
            af_raw = bool(af_rr)
            self._af_history.append(af_raw)
            vote_positive = int(sum(self._af_history))
            vote_total = len(self._af_history)
            # Use a stricter persistence rule: AF is reported only when
            # the recent window is full and every raw decision is positive.
            af_voted = (
                vote_total == self.voting_windows
                and vote_positive == self.voting_windows
            )

            self._last_result = {
                "af_detected": bool(af_voted),
                "af_raw": af_raw,
                "cv_rr": float(cv_rr) if np.isfinite(cv_rr) else None,
                "beats_used": int(self.window_beats),
                "vote_positive": vote_positive,
                "vote_total": vote_total,
            }
            self._new_rr_since_eval = 0

        return self._last_result
