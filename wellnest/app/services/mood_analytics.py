# app/services/mood_analytics.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from math import exp, tanh
from typing import List, Optional, Tuple, Dict, Any

import numpy as np

from app.core.logger import get_logger
from app.models.mood_analytics import MoodAnalyticsResponse, MetricExplanation


logger = get_logger("mood_analytics")


@dataclass(frozen=True)
class MoodPoint:
    d: date
    x: float  # mood_score in [1, 10]


@dataclass(frozen=True)
class AnalyticsConfig:
    window_days: int = 30
    low_threshold: float = 4.0
    stability_scale: float = 2.0   # s
    trend_scale: float = 0.15      # r
    persistence_saturate_days: int = 7  # L_max
    recovery_time_scale_days: float = 3.0  # d0
    # weights for composite risk
    w_mvi: float = 1.2
    w_instability: float = 1.0     # (1 - MSI)
    w_persistence: float = 1.4
    w_downtrend: float = 1.3
    w_low_resilience: float = 0.8


# -----------------------
# Pure computation helpers
# -----------------------

def _mad(values: np.ndarray) -> float:
    if values.size == 0:
        return 0.0
    med = float(np.median(values))
    return float(np.median(np.abs(values - med)))


def mood_stability_index(points: List[MoodPoint], s: float) -> float:
    if len(points) < 2:
        return 1.0
    x = np.array([p.x for p in points], dtype=float)
    dx = np.diff(x)
    mad_dx = _mad(dx)
    return float(exp(-mad_dx / max(s, 1e-9)))


def mood_volatility_index(points: List[MoodPoint], s: float) -> float:
    if len(points) < 2:
        return 0.0
    x = np.array([p.x for p in points], dtype=float)
    dx = np.diff(x)
    sigma = float(np.std(dx, ddof=0))
    return float(1.0 - exp(-sigma / max(s, 1e-9)))


def mood_trend_score(points: List[MoodPoint], r: float) -> float:
    if len(points) < 3:
        return 0.0
    x = np.array([p.x for p in points], dtype=float)
    k = np.arange(len(points), dtype=float)
    k_mean = float(np.mean(k))
    x_mean = float(np.mean(x))
    denom = float(np.sum((k - k_mean) ** 2))
    if denom < 1e-9:
        beta = 0.0
    else:
        beta = float(np.sum((k - k_mean) * (x - x_mean)) / denom)
    return float(tanh(beta / max(r, 1e-9)))


def low_mood_persistence(points: List[MoodPoint], tau: float, lmax: int) -> Tuple[float, int]:
    if not points:
        return 0.0, 0
    longest = 0
    current = 0
    for p in points:
        if p.x <= tau:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    score = min(1.0, longest / max(lmax, 1))
    return float(score), int(longest)


def recovery_resilience_score(
    points: List[MoodPoint], tau: float, baseline: float, d0: float
) -> Tuple[Optional[float], Dict[str, Any]]:
    """
    Returns (score or None, evidence dict).
    Evidence includes median_recovery_days and num_episodes.
    """
    if len(points) < 2:
        return None, {"num_episodes": 0}

    # Identify low episodes
    episodes: List[int] = []
    for i in range(len(points)):
        if points[i].x <= tau and (i == 0 or points[i - 1].x > tau):
            episodes.append(i)

    if not episodes:
        return None, {"num_episodes": 0}

    recovery_days: List[int] = []
    for start_idx in episodes:
        start_date = points[start_idx].d
        # Find first index after start that returns to baseline
        end_idx = None
        for j in range(start_idx + 1, len(points)):
            if points[j].x >= baseline:
                end_idx = j
                break
        if end_idx is not None:
            d = (points[end_idx].d - start_date).days
            recovery_days.append(max(d, 0))

    if not recovery_days:
        # low episodes exist but no observed return-to-baseline inside window
        return 0.0, {"num_episodes": len(episodes), "median_recovery_days": None, "censored": True}

    med = float(np.median(np.array(recovery_days, dtype=float)))
    score = float(exp(-med / max(d0, 1e-9)))
    return score, {"num_episodes": len(episodes), "median_recovery_days": med, "censored": False}


def composite_risk_signal(
    mvi: float,
    msi: float,
    lmp: float,
    mts: float,
    rrs: Optional[float],
    cfg: AnalyticsConfig,
) -> float:
    rrs_star = 0.5 if rrs is None else float(rrs)
    downtrend = max(0.0, -float(mts))
    z = (
        cfg.w_mvi * float(mvi)
        + cfg.w_instability * (1.0 - float(msi))
        + cfg.w_persistence * float(lmp)
        + cfg.w_downtrend * downtrend
        + cfg.w_low_resilience * (1.0 - rrs_star)
    )
    # sigmoid
    return float(1.0 / (1.0 + exp(-z)))


def attention_level(crs: float) -> str:
    if crs < 0.4:
        return "low"
    if crs < 0.7:
        return "moderate"
    return "high"


# -----------------------
# Service (orchestrator)
# -----------------------

class MoodAnalyticsService:
    def __init__(self, mood_repo, cfg: Optional[AnalyticsConfig] = None):
        """
        mood_repo must expose:
          - async get_moods(user_id: str, start: date, end: date) -> List[dict]
            dict contains: {"date": date|datetime|str, "mood_score": int|float}
        """
        self.mood_repo = mood_repo
        self.cfg = cfg or AnalyticsConfig()

    async def compute(self, user_id: str) -> MoodAnalyticsResponse:
        end = date.today()
        start = end - timedelta(days=self.cfg.window_days - 1)

        rows = await self.mood_repo.get_moods(user_id=user_id, start=start, end=end)

        points = self._to_points(rows)
        points.sort(key=lambda p: p.d)

        n = len(points)
        window_len = self.cfg.window_days
        coverage = (n / window_len) if window_len > 0 else 0.0

        if n == 0:
            # Brutal truth: no data means no analytics. Return safe defaults.
            return MoodAnalyticsResponse(
                user_id=user_id,
                window_start=start,
                window_end=end,
                n_observations=0,
                coverage_ratio=0.0,
                mood_stability_index=1.0,
                mood_volatility_index=0.0,
                mood_trend_score=0.0,
                low_mood_persistence=0.0,
                recovery_resilience_score=None,
                composite_risk_signal=0.0,
                attention_level="low",
                safe_summary="Not enough mood entries in the selected window to compute meaningful analytics.",
                explanations=[
                    MetricExplanation(
                        name="data_sufficiency",
                        value=None,
                        interpretation="No observations available in the time window.",
                        evidence={"window_days": window_len},
                    )
                ],
            )

        baseline = float(np.median(np.array([p.x for p in points], dtype=float)))

        msi = mood_stability_index(points, self.cfg.stability_scale)
        mvi = mood_volatility_index(points, self.cfg.stability_scale)
        mts = mood_trend_score(points, self.cfg.trend_scale)
        lmp, longest_run = low_mood_persistence(points, self.cfg.low_threshold, self.cfg.persistence_saturate_days)
        rrs, rrs_evidence = recovery_resilience_score(points, self.cfg.low_threshold, baseline, self.cfg.recovery_time_scale_days)

        crs = composite_risk_signal(mvi=mvi, msi=msi, lmp=lmp, mts=mts, rrs=rrs, cfg=self.cfg)
        level = attention_level(crs)

        summary = self._safe_summary(level=level, mts=mts, lmp=lmp, rrs=rrs, coverage=coverage)

        logger.info(
            "mood_analytics_computed",
            user_id=user_id,
            n_observations=n,
            coverage_ratio=coverage,
            msi=msi,
            mvi=mvi,
            mts=mts,
            lmp=lmp,
            rrs=rrs,
            crs=crs,
            attention_level=level,
        )

        explanations = [
            MetricExplanation(
                name="mood_stability_index",
                value=msi,
                interpretation="Higher means more consistent day-to-day mood changes (robust to outliers).",
                evidence={"scale_s": self.cfg.stability_scale},
            ),
            MetricExplanation(
                name="mood_volatility_index",
                value=mvi,
                interpretation="Higher means larger day-to-day swings in mood score.",
                evidence={"scale_s": self.cfg.stability_scale},
            ),
            MetricExplanation(
                name="mood_trend_score",
                value=mts,
                interpretation="Positive indicates improving direction over the window; negative indicates declining direction.",
                evidence={"trend_scale_r": self.cfg.trend_scale},
            ),
            MetricExplanation(
                name="low_mood_persistence",
                value=lmp,
                interpretation="Higher means more consecutive low-mood days (duration-focused, not diagnosis).",
                evidence={"threshold_tau": self.cfg.low_threshold, "longest_run_days": longest_run},
            ),
            MetricExplanation(
                name="recovery_resilience_score",
                value=rrs,
                interpretation="Higher means faster return to baseline after low episodes; may be unavailable if no low episodes occurred.",
                evidence={"baseline_median": baseline, **rrs_evidence},
            ),
            MetricExplanation(
                name="composite_risk_signal",
                value=crs,
                interpretation="A conservative attention flag combining variability, persistence, and downward direction (not a medical statement).",
                evidence={
                    "weights": {
                        "w_mvi": self.cfg.w_mvi,
                        "w_instability": self.cfg.w_instability,
                        "w_persistence": self.cfg.w_persistence,
                        "w_downtrend": self.cfg.w_downtrend,
                        "w_low_resilience": self.cfg.w_low_resilience,
                    }
                },
            ),
        ]

        return MoodAnalyticsResponse(
            user_id=user_id,
            window_start=start,
            window_end=end,
            n_observations=n,
            coverage_ratio=float(min(max(coverage, 0.0), 1.0)),
            mood_stability_index=msi,
            mood_volatility_index=mvi,
            mood_trend_score=mts,
            low_mood_persistence=lmp,
            recovery_resilience_score=rrs,
            composite_risk_signal=crs,
            attention_level=level,
            safe_summary=summary,
            explanations=explanations,
        )

    def _to_points(self, rows: List[dict]) -> List[MoodPoint]:
        points: List[MoodPoint] = []
        for r in rows:
            raw_d = r.get("date")
            if isinstance(raw_d, datetime):
                d = raw_d.date()
            elif isinstance(raw_d, date):
                d = raw_d
            elif isinstance(raw_d, str):
                d = date.fromisoformat(raw_d[:10])
            else:
                continue
            x = float(r.get("mood_score"))
            x = min(10.0, max(1.0, x))  # clamp
            points.append(MoodPoint(d=d, x=x))
        return points

    def _safe_summary(self, level: str, mts: float, lmp: float, rrs: Optional[float], coverage: float) -> str:
        direction = "stable" if abs(mts) < 0.15 else ("improving" if mts > 0 else "declining")
        persistence_note = "with some sustained low-mood days" if lmp >= 0.5 else "without prolonged low-mood runs"
        resilience_note = "Recovery patterns look limited in this window." if (rrs is not None and rrs < 0.4) else "Recovery patterns look present in this window."
        if rrs is None:
            resilience_note = "Recovery score is not applicable because no low-mood episodes were detected in this window."

        return (
            f"Over the selected window, your mood pattern looks {direction} {persistence_note}. "
            f"{resilience_note} Data coverage in this window is {coverage:.0%}. "
            f"Attention level: {level} (this is an analytics signal, not a diagnosis)."
        )