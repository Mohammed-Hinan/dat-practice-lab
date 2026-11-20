"""Transparent historical question analyser and import classification helper."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

from .schemas import ConfidenceLevel, HistoricalQuestionRecord
from .taxonomy import (
    ARCHETYPES,
    CATEGORIES,
    PROGRAMME_TAGS,
    RECURRING_THEMES,
    STANDARD_COMPETENCIES,
)


CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Storyboard": [
        "storyboard", "frames", "panels", "frame", "comic", "sequential", "visual story",
        "without dialogue", "narrative sequence", "4 frames", "5 frames", "6 frames",
    ],
    "Product sketch": [
        "product", "redesign", "sketch a product", "orthographic", "perspective sketch",
        "ergonomic", "mechanism", "foldable", "appliance", "furniture", "tool", "device",
        "handle", "bottle", "chair", "lamp", "backpack", "bag", "utensil",
    ],
    "Problem identification": [
        "identify", "problems", "pain points", "list five problems", "list 5 problems",
        "issues faced", "stakeholders", "prioritise", "prioritize", "challenges faced",
        "analyse the situation", "analyze the situation",
    ],
    "Composition": [
        "poster", "composition", "layout", "book cover", "magazine cover", "visual metaphor",
        "arrange", "geometric shapes", "banner", "campaign", "infographic", "graphic",
    ],
    "Logos, Symbols & Signs": [
        "logo", "symbol", "symbols", "sign", "signs", "signage", "icon", "icons",
        "pictogram", "emblem", "wayfinding", "tagline", "monogram", "badge", "brand mark",
    ],
    "Drawing": [
        "draw", "observational", "perspective", "proportion", "eye level", "bird's eye",
        "ant's eye", "human figure", "hand holding", "light and shadow", "sketch the scene",
        "cutaway", "exploded view", "step-by-step drawing",
    ],
    "Creativity": [
        "unusual", "combine", "alternate uses", "lateral", "imagine if", "reimagine",
        "proverb", "metaphor", "unrelated objects", "creative uses", "what if",
        "unconventional", "inventive",
    ],
    "Design aptitude": [
        "service", "system", "experience", "community", "future", "sustainable",
        "material", "kiosk", "app", "interface", "intervention", "inclusive",
    ],
}

PROGRAMME_KEYWORDS: Dict[str, List[str]] = {
    "Product Design": ["product", "tool", "device", "appliance", "ergonomic", "utensil", "everyday object"],
    "Furniture & Interior Design": ["furniture", "chair", "table", "desk", "interior", "room", "seating", "space"],
    "Ceramic & Glass Design": ["ceramic", "clay", "terracotta", "pottery", "glass", "kiln", "vessel"],
    "Toy & Game Design": ["toy", "board game", "play", "children", "puzzle", "playful"],
    "Transportation & Automobile Design": ["vehicle", "bus", "train", "metro", "bicycle", "auto", "rickshaw", "commute", "mobility", "helmet"],
    "Universal Design": ["accessibility", "accessible", "elderly", "disability", "blind", "wheelchair", "inclusive", "low-literacy"],
    "Graphic Design": ["poster", "logo", "typography", "signage", "symbol", "branding", "book cover", "editorial"],
    "Animation Film Design": ["storyboard", "character", "animation", "frames", "visual story", "expression"],
    "Film & Video Communication": ["film", "camera", "scene", "shot", "documentary", "cinema", "dialogue"],
    "Photography Design": ["photograph", "framing", "light", "shadow", "perspective", "viewpoint"],
    "Exhibition Design": ["exhibition", "museum", "pavilion", "installation", "gallery", "display"],
    "Textile Design": ["textile", "fabric", "weave", "loom", "dye", "handloom", "cloth"],
    "Apparel Design": ["garment", "clothing", "wearable", "uniform", "apparel", "raincoat", "footwear"],
    "Lifestyle Accessory Design": ["bag", "backpack", "watch", "luggage", "wallet", "accessory", "eyewear"],
    "Interaction Design": ["app", "interface", "kiosk", "screen", "interactive", "touchpoint", "digital", "ux"],
    "Information Design": ["infographic", "wayfinding", "map", "diagram", "data", "instruction", "timetable"],
    "New Media Design": ["ar", "vr", "sensor", "installation", "smart", "ai", "new media", "projection"],
    "Digital Game Design": ["video game", "level", "mechanic", "player", "digital game", "avatar"],
    "Strategic Design Management": ["stakeholder", "system", "policy", "service", "strategy", "community", "civic", "circular", "public"],
    "Design for Retail Experience": ["retail", "shop", "store", "market", "vendor", "stall", "packaging", "checkout"],
}


def detect_themes(text: str) -> List[str]:
    lower = text.lower()
    matched: List[str] = []
    for theme in RECURRING_THEMES:
        if any(kw in lower for kw in theme["keywords"]):
            matched.append(theme["id"])
    return matched


def detect_archetypes(text: str, category: Optional[str] = None) -> List[str]:
    lower = text.lower()
    scores: Dict[str, int] = {}
    archetype_keywords = {
        "Problem identification": ["identify", "problem", "pain point", "stakeholder", "issue", "prioritise", "prioritize", "challenge"],
        "Product innovation": ["product", "redesign", "invent", "modify", "combine", "device", "tool", "ergonomic", "mechanism", "foldable"],
        "Human-centred design": ["elderly", "child", "children", "disability", "blind", "commuter", "worker", "vendor", "student", "user", "inclusive"],
        "Visual communication": ["poster", "symbol", "sign", "signage", "graphic", "campaign", "infographic", "branding", "metaphor", "logo"],
        "Storytelling and storyboard": ["storyboard", "frame", "frames", "panel", "story", "narrative", "character", "sequence", "comic"],
        "Drawing and observation": ["draw", "proportion", "perspective", "eye level", "posture", "hand", "object drawing", "sketch the scene", "observe"],
        "Materials and sustainability": ["material", "bamboo", "clay", "plastic", "sustainable", "recycle", "reuse", "circular", "waste", "craft", "eco"],
        "Future and systems thinking": ["future", "2030", "2040", "2050", "system", "infrastructure", "city", "community", "autonomous", "climate", "technology"],
        "Interaction and service design": ["interface", "kiosk", "app", "service", "journey", "touchpoint", "interactive", "onboarding", "booking"],
        "Creative and lateral thinking": ["unusual", "unrelated", "lateral", "imagine if", "what if", "reverse", "metaphor", "creative uses", "word"],
    }
    for name, kws in archetype_keywords.items():
        hits = sum(1 for kw in kws if kw in lower)
        if hits > 0:
            scores[name] = hits
    ordered = [name for name, _ in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)][:3]
    if not ordered and category:
        for arch in ARCHETYPES:
            if category in arch["primary_categories"]:
                ordered.append(arch["name"])
                if len(ordered) >= 2:
                    break
    return ordered


def classify_question_text(prompt_text: str, explicit_category: Optional[str] = None) -> Dict[str, Any]:
    """Heuristically suggest category, archetypes, programmes, themes, and competencies for review."""
    lower = prompt_text.lower()

    if explicit_category and explicit_category in CATEGORIES:
        category = explicit_category
        auto_assigned = False
        confidence_note = "Category supplied directly in import data."
    else:
        cat_scores: Dict[str, int] = {}
        for cat, kws in CATEGORY_KEYWORDS.items():
            hits = sum(1 for kw in kws if kw in lower)
            if hits:
                cat_scores[cat] = hits
        if cat_scores:
            # Prefer specific categories over broad 'Design aptitude' on ties
            ranked = sorted(
                cat_scores.items(),
                key=lambda kv: (kv[1], 0 if kv[0] == "Design aptitude" else 1),
                reverse=True,
            )
            category = ranked[0][0]
            confidence_note = f"Auto-suggested '{category}' based on keyword cues; review before saving."
        else:
            category = "Design aptitude"
            confidence_note = "Defaulted to 'Design aptitude' (no strong category-specific cue detected); review before saving."
        auto_assigned = True

    programmes: List[str] = []
    for prog, kws in PROGRAMME_KEYWORDS.items():
        if any(kw in lower for kw in kws):
            programmes.append(prog)
    programmes = programmes[:4]

    themes = detect_themes(prompt_text)
    archetypes = detect_archetypes(prompt_text, category=category)

    comp_map = {
        "Observation": ["observe", "everyday", "scene", "detail", "draw", "identify"],
        "Empathy": ["elderly", "child", "disabled", "blind", "worker", "vendor", "patient", "commuter"],
        "Problem framing": ["problem", "prioritise", "prioritize", "stakeholder", "issue", "root cause"],
        "Divergent thinking": ["unusual", "creative", "combine", "ideas", "alternative", "reimagine"],
        "Systems thinking": ["system", "infrastructure", "city", "public", "community", "service", "future"],
        "Visual communication": ["poster", "symbol", "sign", "graphic", "infographic", "metaphor", "visual"],
        "Proportion & perspective": ["proportion", "perspective", "scale", "eye level", "orthographic", "draw"],
        "Ergonomic reasoning": ["ergonomic", "hand", "posture", "handle", "comfort", "portable", "wearable"],
        "Material intelligence": ["material", "bamboo", "clay", "plastic", "fabric", "metal", "wood", "craft"],
        "Sequential storytelling": ["storyboard", "frame", "panel", "story", "sequence", "narrative"],
        "Stakeholder analysis": ["stakeholder", "vendor", "commuter", "hospital", "queue", "community"],
        "Sustainability reasoning": ["sustainable", "recycle", "reuse", "waste", "circular", "eco", "repair"],
        "Constraint navigation": ["constraint", "without", "only using", "limit", "budget", "no text"],
        "Service & interaction logic": ["kiosk", "app", "interface", "service", "journey", "touchpoint"],
    }
    competencies = [c for c, kws in comp_map.items() if any(kw in lower for kw in kws)][:5]
    if not competencies:
        competencies = ["Observation", "Problem framing"]

    return {
        "category": category,
        "auto_assigned_category": auto_assigned,
        "confidence_note": confidence_note,
        "programme_tags": programmes,
        "archetypes": archetypes,
        "themes": themes,
        "competencies": competencies,
    }


def evaluate_dataset_confidence(records: List[HistoricalQuestionRecord]) -> Tuple[ConfidenceLevel, Optional[str]]:
    """Honest, transparent data sufficiency assessment."""
    total = len(records)
    dated = [r for r in records if r.year is not None]
    distinct_years = len({r.year for r in dated})

    if total == 0:
        return (
            "Low",
            "No historical NID M.Des questions are imported yet. Practice-priority scores currently rely "
            "only on your selected preparation profiles and practice gaps.",
        )
    if total < 5:
        return (
            "Medium",
            f"Dataset has {total} question(s). Importing additional past papers will refine trends.",
        )
    return ("High", None)


def analyse_historical_bank(records: List[HistoricalQuestionRecord]) -> Dict[str, Any]:
    """Compute transparent analytics across all imported historical questions."""
    total = len(records)
    dated_records = [r for r in records if r.year is not None]
    years = sorted({r.year for r in dated_records if r.year is not None})
    unknown_year_count = total - len(dated_records)
    unknown_marks_count = sum(1 for r in records if r.marks is None)
    unknown_source_count = sum(1 for r in records if not r.source)

    confidence, warning = evaluate_dataset_confidence(records)

    cat_counter: Counter[str] = Counter()
    prog_counter: Counter[str] = Counter()
    arch_counter: Counter[str] = Counter()
    comp_counter: Counter[str] = Counter()
    theme_counter: Counter[str] = Counter()
    theme_years: Dict[str, set[int]] = defaultdict(set)
    theme_categories: Dict[str, set[str]] = defaultdict(set)
    theme_programmes: Dict[str, set[str]] = defaultdict(set)
    year_cat_counts: Dict[str, Counter[str]] = defaultdict(Counter)

    for rec in records:
        cat_counter[rec.category] += 1
        year_key = str(rec.year) if rec.year is not None else "Unknown"
        year_cat_counts[year_key][rec.category] += 1

        for p in rec.programme_tags:
            prog_counter[p] += 1

        # Enrich on the fly if record has empty archetypes/themes/competencies
        inferred_themes = rec.themes if rec.themes else detect_themes(rec.prompt_text)
        inferred_archetypes = rec.archetypes if rec.archetypes else detect_archetypes(rec.prompt_text, rec.category)
        inferred_comps = rec.competencies if rec.competencies else []

        for a in inferred_archetypes:
            arch_counter[a] += 1
        for c in inferred_comps:
            comp_counter[c] += 1
        for t_id in inferred_themes:
            theme_counter[t_id] += 1
            if rec.year is not None:
                theme_years[t_id].add(rec.year)
            theme_categories[t_id].add(rec.category)
            for p in rec.programme_tags:
                theme_programmes[t_id].add(p)

    category_frequency = [
        {
            "category": cat,
            "count": cat_counter[cat],
            "percentage": round((cat_counter[cat] / total) * 100, 1) if total > 0 else 0.0,
        }
        for cat in CATEGORIES
    ]

    year_trends = []
    for y in years:
        yk = str(y)
        entry: Dict[str, Any] = {"year": yk, "total": sum(year_cat_counts[yk].values())}
        for cat in CATEGORIES:
            entry[cat] = year_cat_counts[yk][cat]
        year_trends.append(entry)
    if unknown_year_count > 0:
        entry = {"year": "Unknown", "total": unknown_year_count}
        for cat in CATEGORIES:
            entry[cat] = year_cat_counts["Unknown"][cat]
        year_trends.append(entry)

    programme_coverage = [
        {
            "programme": prog,
            "count": prog_counter[prog],
            "percentage": round((prog_counter[prog] / total) * 100, 1) if total > 0 else 0.0,
        }
        for prog in PROGRAMME_TAGS
    ]
    programme_coverage.sort(key=lambda x: (-x["count"], x["programme"]))

    archetype_frequency = [
        {
            "code": a["code"],
            "archetype": a["name"],
            "count": arch_counter[a["name"]],
        }
        for a in ARCHETYPES
    ]
    archetype_frequency.sort(key=lambda x: (-x["count"], x["code"]))

    competency_frequency = [
        {"competency": comp, "count": comp_counter[comp]}
        for comp in STANDARD_COMPETENCIES
    ]
    # Also include any custom competencies added by user
    for comp, cnt in comp_counter.items():
        if comp not in STANDARD_COMPETENCIES:
            competency_frequency.append({"competency": comp, "count": cnt})
    competency_frequency.sort(key=lambda x: (-x["count"], x["competency"]))

    unrepresented_topics: List[Dict[str, Any]] = []
    for theme in RECURRING_THEMES:
        if theme_counter[theme["id"]] == 0:
            unrepresented_topics.append(
                {
                    "type": "theme",
                    "name": theme["label"],
                    "detail": theme["description"],
                }
            )
    for cat in CATEGORIES:
        if cat_counter[cat] == 0:
            unrepresented_topics.append(
                {
                    "type": "category",
                    "name": cat,
                    "detail": "No historical records currently tagged under this category.",
                }
            )

    return {
        "dataset_summary": {
            "total_records": total,
            "records_with_known_year": len(dated_records),
            "unknown_year_records": unknown_year_count,
            "unknown_marks_records": unknown_marks_count,
            "unknown_source_records": unknown_source_count,
            "distinct_years": len(years),
            "year_range": [years[0], years[-1]] if years else None,
        },
        "confidence_level": confidence,
        "low_confidence_warning": warning,
        "category_frequency": category_frequency,
        "year_trends": year_trends,
        "programme_coverage": programme_coverage,
        "archetype_frequency": archetype_frequency,
        "competency_frequency": competency_frequency,
        "unrepresented_topics": unrepresented_topics,
        "_theme_stats": {
            "counts": dict(theme_counter),
            "years": {k: sorted(v) for k, v in theme_years.items()},
            "categories": {k: sorted(v) for k, v in theme_categories.items()},
            "programmes": {k: sorted(v) for k, v in theme_programmes.items()},
        },
    }
