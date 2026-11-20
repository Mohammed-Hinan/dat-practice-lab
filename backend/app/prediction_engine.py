"""Practice-priority scoring engine and balanced/weighted category allocation."""

from __future__ import annotations

import math
import random
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from .historical_analyser import analyse_historical_bank
from .schemas import (
    AnalyticsOverviewResponse,
    AppSettings,
    CategoryPriorityItem,
    ConfidenceLevel,
    HistoricalQuestionRecord,
    PracticeAttemptRecord,
    PredictionWeights,
    ThemePriorityItem,
    WeakAreaRecord,
)
from .taxonomy import (
    CATEGORIES,
    DNERD_REFERENCE_METADATA,
    PREPARATION_PROFILES,
    RECURRING_THEMES,
)


def _normalize_weights(weights: PredictionWeights) -> Dict[str, float]:
    raw = {
        "multi_year_recurrence": max(0.0, weights.multi_year_recurrence),
        "recency": max(0.0, weights.recency),
        "cross_relevance": max(0.0, weights.cross_relevance),
        "profile_relevance": max(0.0, weights.profile_relevance),
        "practice_gaps": max(0.0, weights.practice_gaps),
    }
    total = sum(raw.values())
    if total <= 0:
        return {
            "multi_year_recurrence": 0.30,
            "recency": 0.20,
            "cross_relevance": 0.20,
            "profile_relevance": 0.15,
            "practice_gaps": 0.15,
        }
    return {k: v / total for k, v in raw.items()}


def _score_to_band(score: float) -> int:
    if score >= 78:
        return 5
    if score >= 62:
        return 4
    if score >= 45:
        return 3
    if score >= 28:
        return 2
    return 1


def _combined_profile_boosts(active_profiles: List[str]) -> Tuple[Dict[str, float], Dict[str, float]]:
    valid = [PREPARATION_PROFILES[p] for p in active_profiles if p in PREPARATION_PROFILES]
    if not valid:
        valid = [PREPARATION_PROFILES["general_nid_mdes"]]

    cat_boosts: Dict[str, float] = {}
    for cat in CATEGORIES:
        cat_boosts[cat] = sum(p["category_boosts"].get(cat, 1.0) for p in valid) / len(valid)

    theme_boosts: Dict[str, float] = {}
    for theme in RECURRING_THEMES:
        tid = theme["id"]
        theme_boosts[tid] = sum(p["theme_boosts"].get(tid, 1.0) for p in valid) / len(valid)

    return cat_boosts, theme_boosts


def compute_analytics_and_predictions(
    historical_records: List[HistoricalQuestionRecord],
    attempts: List[PracticeAttemptRecord],
    weak_areas: List[WeakAreaRecord],
    settings: AppSettings,
    override_profiles: Optional[List[str]] = None,
) -> AnalyticsOverviewResponse:
    """Build full transparent historical analytics and deterministic practice-priority scores."""
    active_profiles = override_profiles if override_profiles else settings.active_profiles
    valid_profiles = [p for p in active_profiles if p in PREPARATION_PROFILES] or ["general_nid_mdes"]
    norm_w = _normalize_weights(settings.prediction_weights)

    hist = analyse_historical_bank(historical_records)
    dataset_summary = hist["dataset_summary"]
    global_confidence: ConfidenceLevel = hist["confidence_level"]
    low_conf_warning: Optional[str] = hist["low_confidence_warning"]
    theme_stats = hist["_theme_stats"]

    total_hist = dataset_summary["total_records"]
    distinct_years_total = max(1, dataset_summary["distinct_years"])
    max_year = dataset_summary["year_range"][1] if dataset_summary["year_range"] else None
    min_year = dataset_summary["year_range"][0] if dataset_summary["year_range"] else None

    # Student attempt stats
    completed_attempts = [a for a in attempts if a.status == "completed"]
    attempt_cat_counts = Counter(a.category for a in completed_attempts)
    total_attempts = len(completed_attempts)
    avg_attempts_per_cat = total_attempts / len(CATEGORIES) if total_attempts > 0 else 0.0

    flagged_cats = {w.name.lower(): w.severity for w in weak_areas if w.area_type == "category"}
    flagged_themes = {w.name.lower(): w.severity for w in weak_areas if w.area_type == "theme"}

    cat_profile_boosts, theme_profile_boosts = _combined_profile_boosts(valid_profiles)

    # ------------------------------------------------------------------
    # Theme Practice-Priority Scoring (10 core recurring NID themes)
    # ------------------------------------------------------------------
    theme_priorities: List[ThemePriorityItem] = []

    for theme in RECURRING_THEMES:
        tid = theme["id"]
        count = int(theme_stats["counts"].get(tid, 0))
        years_seen: List[int] = theme_stats["years"].get(tid, [])
        cats_seen: List[str] = theme_stats["categories"].get(tid, [])
        progs_seen: List[str] = theme_stats["programmes"].get(tid, [])

        # 1. Multi-year recurrence (0-100)
        if total_hist == 0:
            multi_year_score = 0.0
        elif years_seen:
            year_ratio = len(years_seen) / distinct_years_total
            volume_ratio = min(1.0, count / max(3.0, total_hist * 0.25))
            multi_year_score = round((0.65 * year_ratio + 0.35 * volume_ratio) * 100.0, 1)
        else:
            # Present only in undated questions
            multi_year_score = round(min(45.0, (count / max(1.0, total_hist)) * 100.0), 1) if count > 0 else 0.0

        # 2. Recency (0-100)
        latest_year = max(years_seen) if years_seen else None
        if latest_year is not None and max_year is not None:
            span = max(1, max_year - (min_year or max_year))
            age = max_year - latest_year
            recency_score = round(max(15.0, (1.0 - (age / (span + 2.0))) * 100.0), 1)
        else:
            recency_score = 0.0

        # 3. Cross-category & cross-programme relevance (0-100)
        if count > 0:
            cat_breadth = min(1.0, len(cats_seen) / 3.0)
            prog_breadth = min(1.0, len(progs_seen) / 4.0)
            cross_score = round((0.55 * cat_breadth + 0.45 * prog_breadth) * 100.0, 1)
        else:
            cross_score = 0.0

        # 4. Preparation profile relevance (0-100)
        p_boost = theme_profile_boosts.get(tid, 1.0)
        # Map boost range [0.85 .. 1.35] -> [45 .. 95]
        profile_score = round(min(100.0, max(20.0, 55.0 + (p_boost - 1.0) * 115.0)), 1)

        # 5. Student's practice gaps (0-100)
        related_attempts = sum(attempt_cat_counts[c] for c in theme["related_categories"])
        expected_related = avg_attempts_per_cat * len(theme["related_categories"])
        if total_attempts == 0:
            gap_score = 75.0
        elif related_attempts == 0:
            gap_score = 95.0
        else:
            ratio = related_attempts / max(1.0, expected_related)
            gap_score = round(min(100.0, max(15.0, (1.25 - 0.55 * ratio) * 100.0)), 1)
        if theme["label"].lower() in flagged_themes or tid in flagged_themes:
            sev = flagged_themes.get(theme["label"].lower()) or flagged_themes.get(tid, "medium")
            gap_score = min(100.0, gap_score + (20.0 if sev == "high" else 12.0))

        # Weighted composite score
        # When historical data is completely absent, clearly note zero historical weight contribution
        composite = (
            norm_w["multi_year_recurrence"] * multi_year_score
            + norm_w["recency"] * recency_score
            + norm_w["cross_relevance"] * cross_score
            + norm_w["profile_relevance"] * profile_score
            + norm_w["practice_gaps"] * gap_score
        )
        composite = round(min(100.0, max(0.0, composite)), 1)

        # Per-theme confidence cannot exceed global confidence
        if global_confidence == "Low" or count == 0:
            item_conf: ConfidenceLevel = "Low"
        elif global_confidence == "Medium" or count < 3 or len(years_seen) < 2:
            item_conf = "Medium"
        else:
            item_conf = "High"

        # Transparent separation: Historical Evidence vs Model Interpretation
        if count == 0:
            hist_evidence = (
                "No matching questions found in your imported historical bank yet "
                f"(out of {total_hist} imported record(s))."
            )
        else:
            year_str = (
                f"across {len(years_seen)} known year(s) ({min(years_seen)}–{max(years_seen)})"
                if years_seen
                else "in records with unknown examination year"
            )
            hist_evidence = (
                f"Observed in {count} of {total_hist} imported historical question(s) {year_str}, "
                f"spanning {len(cats_seen)} category/categories and {len(progs_seen)} programme tag(s)."
            )

        profile_names = [PREPARATION_PROFILES[p]["name"] for p in valid_profiles]
        interp_parts = [
            f"Profile alignment ({profile_score:.0f}/100) for {', '.join(profile_names)}.",
            f"Practice-gap urgency ({gap_score:.0f}/100) based on {related_attempts} completed attempt(s) across related categories.",
        ]
        if total_hist < 10:
            interp_parts.append(
                "Historical evidence is limited, so this score should be treated as a study-planning heuristic rather than a trend forecast."
            )
        model_interp = " ".join(interp_parts)

        theme_priorities.append(
            ThemePriorityItem(
                theme_id=tid,
                label=theme["label"],
                description=theme["description"],
                practice_priority_score=composite,
                priority_band=_score_to_band(composite),
                confidence=item_conf,
                historical_count=count,
                distinct_years=len(years_seen),
                latest_year=latest_year,
                related_categories=theme["related_categories"],
                factor_breakdown={
                    "multi_year_recurrence": multi_year_score,
                    "recency": recency_score,
                    "cross_relevance": cross_score,
                    "profile_relevance": profile_score,
                    "practice_gaps": gap_score,
                },
                historical_evidence=hist_evidence,
                model_interpretation=model_interp,
            )
        )

    theme_priorities.sort(key=lambda t: (-t.practice_priority_score, t.label))

    # ------------------------------------------------------------------
    # Category Practice Priorities & Weighted Practice Shares
    # ------------------------------------------------------------------
    hist_cat_map = {item["category"]: item["count"] for item in hist["category_frequency"]}
    raw_weights: Dict[str, float] = {}
    cat_items_tmp: List[Dict[str, Any]] = []

    for cat in CATEGORIES:
        h_count = hist_cat_map.get(cat, 0)
        p_attempts = attempt_cat_counts.get(cat, 0)
        is_flagged = cat.lower() in flagged_cats
        is_under = (total_attempts == 0) or (p_attempts < max(1, math.floor(avg_attempts_per_cat * 0.75)))

        # Historical presence signal uses dampened log scale so one skewed tag count never dominates
        hist_signal = math.log1p(h_count) / math.log1p(max(1, total_hist)) if total_hist > 0 else 0.5
        profile_boost = cat_profile_boosts.get(cat, 1.0)
        gap_boost = 1.35 if is_under else 0.9
        if is_flagged:
            gap_boost += 0.35 if flagged_cats[cat.lower()] == "high" else 0.2
        user_mult = max(0.2, min(3.0, settings.custom_category_weights.get(cat, 1.0)))

        weight = (0.75 + 0.25 * hist_signal) * profile_boost * gap_boost * user_mult
        raw_weights[cat] = weight

        # Priority score 0-100
        score = round(min(100.0, max(15.0, 42.0 * profile_boost + 28.0 * (gap_boost / 1.5) + 20.0 * hist_signal)), 1)
        reasons = []
        if is_flagged:
            reasons.append("Manually flagged as weak area")
        if is_under:
            reasons.append(f"Under-practised ({p_attempts} completed attempt(s))")
        if profile_boost > 1.1:
            reasons.append("Emphasised by selected preparation profile(s)")
        if h_count > 0:
            reasons.append(f"Appears in {h_count} imported historical record(s)")
        if not reasons:
            reasons.append("Maintained for balanced 7-category readiness")

        cat_items_tmp.append(
            {
                "category": cat,
                "historical_count": h_count,
                "practice_attempts": p_attempts,
                "practice_priority_score": score,
                "priority_band": _score_to_band(score),
                "is_under_practised": is_under,
                "is_flagged_weak": is_flagged,
                "reason": "; ".join(reasons) + ".",
            }
        )

    total_w = sum(raw_weights.values()) or 1.0
    category_priorities: List[CategoryPriorityItem] = []
    for item in cat_items_tmp:
        cat = item["category"]
        category_priorities.append(
            CategoryPriorityItem(
                **item,
                balanced_weight=round(100.0 / len(CATEGORIES), 1),
                weighted_practice_share=round((raw_weights[cat] / total_w) * 100.0, 1),
            )
        )
    category_priorities.sort(key=lambda c: (-c.practice_priority_score, c.category))

    return AnalyticsOverviewResponse(
        dataset_summary=dataset_summary,
        confidence_level=global_confidence,
        low_confidence_warning=low_conf_warning,
        category_frequency=hist["category_frequency"],
        year_trends=hist["year_trends"],
        programme_coverage=hist["programme_coverage"],
        archetype_frequency=hist["archetype_frequency"],
        competency_frequency=hist["competency_frequency"],
        unrepresented_topics=hist["unrepresented_topics"],
        theme_priorities=theme_priorities,
        category_priorities=category_priorities,
        scoring_weights=settings.prediction_weights,
        active_profiles=valid_profiles,
        dnerd_reference_note=DNERD_REFERENCE_METADATA,
    )


# ---------------------------------------------------------------------------
# Category & Slot Allocation Algorithms (Modes A, B, C, D)
# ---------------------------------------------------------------------------


def allocate_categories_mode_a(selected_categories: List[str], count: int) -> List[str]:
    """Mode A — Category Practice.

    Guarantees balanced coverage across selected categories; when all 7 (or N) categories
    are selected and count >= N, every selected category appears at least once.
    Never skews toward Design aptitude.
    """
    valid = [c for c in selected_categories if c in CATEGORIES]
    if not valid:
        valid = list(CATEGORIES)

    # Deduplicate preserving order
    unique_cats = list(dict.fromkeys(valid))
    shuffled = list(unique_cats)
    random.shuffle(shuffled)

    result: List[str] = []
    if count >= len(shuffled):
        # Guarantee at least one per selected category
        result.extend(shuffled)
        remaining = count - len(shuffled)
        pool = list(shuffled)
        idx = 0
        while remaining > 0:
            if idx % len(pool) == 0:
                random.shuffle(pool)
            result.append(pool[idx % len(pool)])
            idx += 1
            remaining -= 1
    else:
        result = shuffled[:count]

    random.shuffle(result)
    return result


def allocate_categories_mode_b(
    count: int,
    strategy: str,
    category_priorities: List[CategoryPriorityItem],
    custom_weights: Optional[Dict[str, float]] = None,
) -> List[str]:
    """Mode B — Balanced Random Practice (completely balanced vs weighted)."""
    if strategy == "completely_balanced":
        # Stratified uniform sampling so small batches never repeat before covering distinct categories
        result: List[str] = []
        while len(result) < count:
            bag = list(CATEGORIES)
            random.shuffle(bag)
            take = min(len(bag), count - len(result))
            result.extend(bag[:take])
        return result

    # Weighted practice: uses prediction-engine weighted shares (or user overrides), capped against extreme skew
    weights_map: Dict[str, float] = {}
    share_lookup = {cp.category: cp.weighted_practice_share for cp in category_priorities}
    for cat in CATEGORIES:
        base = share_lookup.get(cat, 100.0 / len(CATEGORIES))
        if custom_weights and cat in custom_weights:
            base = max(0.1, float(custom_weights[cat]))
        weights_map[cat] = max(0.1, base)

    cats = list(CATEGORIES)
    weights = [weights_map[c] for c in cats]
    if count <= len(cats):
        # Weighted sampling without replacement for maximum diversity
        chosen: List[str] = []
        pool_c = list(cats)
        pool_w = list(weights)
        for _ in range(count):
            pick = random.choices(pool_c, weights=pool_w, k=1)[0]
            idx = pool_c.index(pick)
            chosen.append(pick)
            pool_c.pop(idx)
            pool_w.pop(idx)
        return chosen
    return random.choices(cats, weights=weights, k=count)


def allocate_slots_mode_c(
    count: int,
    analytics: AnalyticsOverviewResponse,
    preferred_categories: Optional[List[str]] = None,
    focus_theme_id: Optional[str] = None,
) -> List[Tuple[str, ThemePriorityItem]]:
    """Mode C — Likely Exam Practice: pair high-priority themes with diverse categories."""
    themes = analytics.theme_priorities
    if focus_theme_id:
        matched = [t for t in themes if t.theme_id == focus_theme_id]
        top_themes = matched if matched else themes[:5]
    else:
        top_themes = themes[: max(5, count)]

    valid_cats = [c for c in (preferred_categories or []) if c in CATEGORIES]
    used_pairs: set[Tuple[str, str]] = set()
    used_cats: List[str] = []
    slots: List[Tuple[str, ThemePriorityItem]] = []

    for i in range(count):
        theme = top_themes[i % len(top_themes)]
        candidate_cats = valid_cats if valid_cats else theme.related_categories
        # Prefer a category not already used in this batch for diversity
        fresh_cats = [c for c in candidate_cats if c not in used_cats]
        if fresh_cats:
            cat = fresh_cats[0]
        else:
            fallback_fresh = [c for c in CATEGORIES if c not in used_cats]
            cat = fallback_fresh[0] if (not valid_cats and fallback_fresh) else candidate_cats[i % len(candidate_cats)]

        if (cat, theme.theme_id) in used_pairs and len(themes) > 1:
            for alt in themes:
                if (cat, alt.theme_id) not in used_pairs:
                    theme = alt
                    break
        used_pairs.add((cat, theme.theme_id))
        used_cats.append(cat)
        slots.append((cat, theme))

    return slots
