"""NID M.Des DAT Question Generation Prompt Engine (Modes A, B, C, and D)."""

from __future__ import annotations

import json
import random
import re
import uuid
from typing import Dict, List, Optional, Tuple

from .database import Database, utc_now_iso
from .drawthings_service import (
    build_fallback_visual_prompts,
    default_negative_for_category,
    sanitize_subject_for_diffusion,
)
from .nid_sketch_knowledge import CATEGORY_SKETCH_KNOWLEDGE
from .historical_analyser import classify_question_text
from .llm_service import LLMService
from .prediction_engine import (
    allocate_categories_mode_a,
    allocate_categories_mode_b,
    allocate_slots_mode_c,
    compute_analytics_and_predictions,
)
from .schemas import (
    AnalyticsOverviewResponse,
    AppSettings,
    ExamPaperCreateRequest,
    ExamPaperRecord,
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    GeneratedQuestionPayload,
    HistoricalQuestionRecord,
    StoredGeneratedQuestion,
    ThemePriorityItem,
)
from .taxonomy import (
    ARCHETYPES,
    CATEGORIES,
    CATEGORY_DEFINITIONS,
    PREPARATION_PROFILES,
    PROGRAMME_TAGS,
)


DANGLING_ENDINGS = {
    "on", "with", "without", "to", "for", "and", "or", "in", "by", "that", "which",
    "at", "from", "as", "into", "onto", "upon", "about", "against", "between",
    "among", "through", "during", "before", "after", "above", "below", "under",
    "behind", "beyond", "such", "due", "compromising", "without compromising",
    "a", "an", "the", "of", "be", "is", "are", "was", "were", "have", "has", "having", "should",
}


def sanitize_complete_sentence(text: str) -> str:
    """Trim dangling prepositions, trailing articles, and incomplete ending clauses to guarantee complete, grammatical sentences."""
    cleaned = text.strip()
    if not cleaned:
        return cleaned
    had_question = bool(re.search(r"\?\s*(?:(?:Key insights & analysis|Design concept drawing|Deliverables?)\s*:\s*\[\.+\]|[.!?\s])*$", cleaned, re.IGNORECASE))
    # Strip prompt leakage like ': [...]' or '[...]'
    cleaned = re.sub(r"\s*(?:Key insights & analysis|Design concept drawing|Deliverables?)\s*:\s*\[\.+\]\s*\.?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*:\s*\[\.+\]\s*\.?", "", cleaned)
    cleaned = re.sub(r"\s*\[\.+\]\s*\.?", "", cleaned)
    # Strip trailing broken clauses like 'The scene should be a' or 'without compromising on'
    cleaned = re.sub(
        r"\s+(?:the\s+scene\s+should\s+be(?:\s+a|\s+an)?|scene\s+should\s+be(?:\s+a|\s+an)?|the\s+scene\s+is(?:\s+a|\s+an)?|without\s+compromising\s+on|compromising\s+on|such\s+as|due\s+to|without\s+compromising)\s*[.,;:!?-]*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    words = cleaned.rstrip(".,;:!?-").split()
    while words and words[-1].lower() in DANGLING_ENDINGS:
        words.pop()
    if not words:
        return text.strip()
    res = " ".join(words)
    if not res.endswith((".", "!", "?")):
        # If the final clause begins with an interrogative word, end with '?'
        last_sentence_match = re.search(r"(?:^|[.!?]\s+)(?:what|how|why|where|when|which|can|could|would|should|do|does|is|are)\b", res, re.IGNORECASE)
        if had_question or last_sentence_match:
            res += "?"
        else:
            res += "."
    return res


SYSTEM_PROMPT = """You write authentic NID M.Des DAT Prelims examination questions modeled directly on real past NID papers.
Voice & style:
- Write in crisp, direct, plain-English second-person ("You are...", "Imagine...", "Picture someone...", "Pick one...").
- Real NID questions are deceptively simple, concrete, playful or observant—NEVER use corporate/academic jargon ("stakeholder optimization", "holistic ergonomic framework") and NEVER mention NID campus names (like Gandhinagar or Haryana) inside a question.
- STRICT SINGLE-FOCUS RULE: Every question must focus on ONE single coherent challenge or product. NEVER blend multiple conflicting tasks together (e.g. NEVER mix product ergonomics with fantasy characters, never ask for "5 usability issues" when designing a visual metaphor or animal illustration, and never mash unrelated objects together). Subquestion A and Subquestion B must address the exact same subject.
- STRICT TASK-CONTEXT COHERENCE: Subquestion A and Subquestion B must directly serve the exact challenge established in the scenario. If the scenario asks to design a physical product, container, or tool, Subquestions MUST evaluate that physical product (e.g., pain points, ergonomic features, 3D perspective drawing, exploded view, user interaction in context). NEVER switch disciplines or ask for a promotional poster, advertising flyer, or marketing pitch when the scenario is designing a physical product!
- COMPLETE GRAMMATICAL SENTENCES: Every constraint, scenario, and instruction MUST be a complete, grammatically sound sentence ending with a period. NEVER end mid-phrase or with dangling words like "without compromising on", "such as", or "due to".
- Ground every prompt in a vivid, ordinary Indian or universal situation with clever constraints (e.g., carrying awkward items without spilling, two unexpected visual elements in a poster, what changes in 2047 vs what stays the same, turning factory surplus into products, 4-frame wordless action).
- Also write `visual_sketch_prompt`: a concrete 18-32 word purely visual description of ONE cohesive drawn solution/scene/symbol answering this question (exact objects, perspective angle, human posture/gesture, everyday Indian props). NEVER write "examination sheet", "annotations", "labels", "table", "20 minutes", "realistic", or drawing-tool names (our 2D line-art renderer applies the hand-drawn sketch style automatically).
- Return ONLY one compact valid JSON object matching the 6 requested keys. Never copy supplied historical examples."""


from .topic_synthesizer import (
    NID_BLUEPRINTS,
    pick_nid_blueprint_and_topic as _pick_nid_blueprint_and_topic,
)


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z]{3,}", text.lower())
    stop = {
        "the", "and", "for", "with", "that", "this", "from", "your", "design",
        "question", "sketch", "draw", "using", "into", "about", "their", "them",
        "what", "how", "one", "two", "three", "five", "user", "users", "create",
        "explain", "propose", "based", "given", "show", "make", "should", "must",
    }
    return {w for w in words if w not in stop}


def _jaccard_similarity(a: str, b: str) -> float:
    ta = _tokenize(a)
    tb = _tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _pick_archetypes_for_slot(
    category: str,
    active_profiles: List[str],
    theme: Optional[ThemePriorityItem],
    avoid_archetypes: Optional[List[str]] = None,
) -> List[str]:
    cat_def = CATEGORY_DEFINITIONS.get(category, {})
    primary = list(cat_def.get("default_archetypes", []))
    candidates: List[str] = []

    if primary:
        candidates.append(primary[0])

    # Add complementary archetype from theme or preparation profile
    profile_favs: List[str] = []
    for pid in active_profiles:
        if pid in PREPARATION_PROFILES:
            profile_favs.extend(PREPARATION_PROFILES[pid]["favoured_archetypes"])

    secondary_pool: List[str] = []
    if theme:
        for arch in ARCHETYPES:
            if any(c in arch["primary_categories"] for c in theme.related_categories):
                secondary_pool.append(arch["name"])
    secondary_pool.extend(profile_favs)
    secondary_pool.extend(primary[1:])

    avoid = set(avoid_archetypes or [])
    for candidate in secondary_pool:
        if candidate not in candidates and candidate not in avoid:
            candidates.append(candidate)
            if len(candidates) >= 2:
                break

    if len(candidates) < 2:
        for arch in ARCHETYPES:
            if arch["name"] not in candidates:
                candidates.append(arch["name"])
                if len(candidates) >= 2:
                    break
    return candidates[:2]


def _summarize_historical_evidence(
    historical_records: List[HistoricalQuestionRecord],
    category: str,
    theme: Optional[ThemePriorityItem],
) -> Tuple[str, List[str]]:
    """Build transparent historical evidence bullets for UI without leaking raw nouns into small-LLM prompts."""
    if not historical_records:
        return (
            "HISTORICAL BANK: 0 imported records. Do NOT invent past exam years or counts.",
            ["No historical NID M.Des questions imported in the local question bank yet."],
        )

    relevant = [r for r in historical_records if r.category == category]
    if theme:
        themed = [r for r in historical_records if theme.theme_id in r.themes]
        pool = list({r.id: r for r in (themed + relevant)}.values())
    else:
        pool = relevant if len(relevant) >= 3 else list({r.id: r for r in (relevant + historical_records[:40])}.values())

    # Prioritize recent 2024–2026 examination records to ground in latest NID style
    pool = sorted(pool, key=lambda r: (r.year or 2000), reverse=True)
    sample = pool[:4] if pool else []
    evidence_bullets: List[str] = []
    for rec in sample:
        yr = str(rec.year) if rec.year is not None else "Unknown"
        snippet = rec.prompt_text.replace("\n", " ")[:90]
        evidence_bullets.append(f"[{yr} • {rec.category}] {rec.title or snippet}")

    # Deliberately omit raw topic nouns from the LLM prompt so small models never parrot old topics
    prompt_note = (
        f"Style benchmark ({len(historical_records)} past papers): direct, concrete, surprising—stay strictly anchored to the Fresh Everyday Subject Seed below."
    )
    return prompt_note, evidence_bullets[:4]


def _build_category_rubric(category: str, total_marks: int) -> List[Dict[str, object]]:
    """Build category-specific NID M.Des evaluation criteria summing exactly to total_marks."""
    q = max(1, total_marks // 4)
    rem = total_marks - 3 * q
    rubrics = {
        "Storyboard": [
            ("Narrative clarity & emotional arc", q),
            ("Sequential continuity & pacing", q),
            ("Framing, camera angles & visual expression", q),
            ("Originality & constraint adherence", rem),
        ],
        "Product sketch": [
            ("Ergonomic & user-context understanding", q),
            ("Functional & material feasibility", q),
            ("Perspective clarity, proportion & callouts", q),
            ("Originality & constraint sensitivity", rem),
        ],
        "Drawing": [
            ("Observational accuracy & proportion", q),
            ("Perspective, depth & spatial scale", q),
            ("Line quality, light/shadow & posture", q),
            ("Storytelling detail & composition", rem),
        ],
        "Composition": [
            ("Visual metaphor & conceptual strength", q),
            ("Hierarchy, balance & figure-ground clarity", q),
            ("Immediate communicative impact", q),
            ("Craft & constraint discipline", rem),
        ],
        "Logos, Symbols & Signs": [
            ("Clarity & instant recognisability at a glance", q),
            ("Visual simplicity, scalability & form consistency", q),
            ("Cultural / universal communicative fit", q),
            ("Concept originality & practical application", rem),
        ],
        "Problem identification": [
            ("Depth of observation & stakeholder empathy", q),
            ("Prioritisation logic & problem framing", q),
            ("Practicality & constraint sensitivity", q),
            ("Clarity of annotated visual communication", rem),
        ],
        "Creativity": [
            ("Divergent originality & lateral leaps", q),
            ("Plausibility within given constraints", q),
            ("Concept variety & visual clarity", q),
            ("Concise conceptual articulation", rem),
        ],
    }
    items = rubrics.get(
        category,
        [
            ("Observation & contextual empathy", q),
            ("Systems & design-thinking depth", q),
            ("Practicality & constraint navigation", q),
            ("Visual & written communication clarity", rem),
        ],
    )
    return [{"criterion": c, "marks": m} for c, m in items]


def _build_category_time_split(category: str, time_minutes: int) -> List[Dict[str, object]]:
    """Build realistic, category-tailored time-split guidance summing exactly to time_minutes."""
    t1 = max(2, round(time_minutes * 0.14))
    t2 = max(3, round(time_minutes * 0.20))
    t3 = max(5, round(time_minutes * 0.50))
    t4 = max(2, time_minutes - (t1 + t2 + t3))
    labels = {
        "Storyboard": ("Plan narrative beats", "Thumbnail frame angles", "Draw final frame sequence", "Check visual continuity"),
        "Product sketch": ("Analyse user & constraints", "Explore form thumbnails", "Draw annotated 3D sketch", "Add callouts & material notes"),
        "Drawing": ("Establish proportion & eye level", "Block perspective & figures", "Develop tonal detail & scale", "Refine line weight & clarity"),
        "Composition": ("Interpret theme & metaphor", "Explore 2–3 thumbnail layouts", "Execute final framed visual", "Polish contrast & rationale"),
        "Logos, Symbols & Signs": ("Define visual cues & meaning", "Sketch 3–4 thumbnail symbols", "Draw clean final marks/signs", "Check legibility & notes"),
        "Problem identification": ("Observe stakeholders & context", "List & prioritise core issues", "Sketch practical intervention", "Verify constraints & labels"),
        "Creativity": ("Reframe prompt & constraints", "Brainstorm divergent angles", "Sketch & annotate best concepts", "Sharpen conceptual clarity"),
    }
    a1, a2, a3, a4 = labels.get(
        category,
        ("Understand scenario & constraints", "Explore & shortlist ideas", "Develop written/visual response", "Annotate & refine"),
    )
    return [
        {"activity": a1, "minutes": t1},
        {"activity": a2, "minutes": t2},
        {"activity": a3, "minutes": t3},
        {"activity": a4, "minutes": t4},
    ]


def build_generation_prompt(
    category: str,
    archetypes: List[str],
    programme_tags: List[str],
    active_profiles: List[str],
    difficulty: str,
    time_minutes: int,
    analytics: AnalyticsOverviewResponse,
    historical_records: List[HistoricalQuestionRecord],
    recent_titles_and_scenarios: List[str],
    theme: Optional[ThemePriorityItem] = None,
    modality_hint: Optional[Tuple[str, str]] = None,
    avoid_repetition_note: Optional[str] = None,
) -> Tuple[str, List[str], Dict[str, object]]:
    hist_block, evidence_bullets = _summarize_historical_evidence(historical_records, category, theme)

    recent_titles = [item.split(":")[0][:45] for item in recent_titles_and_scenarios[:5]]
    recent_line = ", ".join(recent_titles) if recent_titles else "None"

    if modality_hint:
        chosen_blueprint, context_seed = modality_hint
    else:
        chosen_blueprint, context_seed = _pick_nid_blueprint_and_topic(
            category, active_profiles, historical_fingerprints=recent_titles_and_scenarios
        )
    default_marks = 20 if time_minutes <= 35 else (30 if time_minutes <= 60 else 40)
    half_marks = default_marks // 2
    rem_marks = default_marks - half_marks

    extra_warning = f"\nRETRY NOTE: {avoid_repetition_note}" if avoid_repetition_note else ""

    cat_kb = CATEGORY_SKETCH_KNOWLEDGE.get(
        category, CATEGORY_SKETCH_KNOWLEDGE["Design aptitude"]
    )
    camera_angle_cue = str(cat_kb["camera_angles"][0]) if cat_kb.get("camera_angles") else "clear 3/4 perspective"

    category_sketch_expectations = {
        "Logos, Symbols & Signs": (
            'e.g. "Render flat 2D graphic silhouettes inside neat square frame tiles", "Use high-contrast negative space with zero 3D perspective or shading"',
            "flat 2D graphic mark or neat 2x2 grid of four square pictogram tiles with solid black silhouettes and negative space — NEVER 3D perspective, NEVER containers or physical products"
        ),
        "Product sketch": (
            'e.g. "Show hero 3/4 perspective with exploded/mechanism circular zoom bubble and human hand for scale", "Include straight leader lines for material notes"',
            "hero 3/4 perspective view with circular mechanism zoom bubble and ergonomic human hand vignette"
        ),
        "Storyboard": (
            'e.g. "Draw a 4-panel 2x2 sequence: wide establishing shot, medium action, close-up hands/reaction, resolution", "Keep character outfit consistent"',
            "4-panel sequence (Panel 1 wide shot, Panel 2 medium action, Panel 3 close-up hands/interaction, Panel 4 resolution)"
        ),
        "Drawing": (
            'e.g. "Use dramatic 1st-person POV or extreme foreground overlap with visible construction lines and accurate proportions"',
            "dramatic 1st-person POV or extreme foreground overlap with clear vanishing lines and human scale"
        ),
        "Problem identification": (
            'e.g. "Draw a clear situational scene showing user struggle in real context", "Sketch practical functional intervention fixing the root cause"',
            "eye-level situational scene showing human struggle in everyday Indian context and physical cause"
        ),
        "Composition": (
            'e.g. "Establish strong visual flow, generous clean white negative space, and clear focal hierarchy"',
            "striking visual metaphor with flowing curves and generous clean white paper"
        ),
        "Creativity": (
            'e.g. "Synthesize two unexpected metaphors into one striking cohesive drawing"',
            "lateral visual hybrid of two distinct objects with bold clean contours on white paper"
        ),
        "Design aptitude": (
            'e.g. "Show user in context with practical ergonomic intervention and functional details"',
            "practical design solution in active everyday Indian context with ergonomic details"
        ),
    }

    sketch_req_example, visual_angle_guideline = category_sketch_expectations.get(
        category,
        (
            'e.g. "Include a clear annotated freehand sketch showing user interaction and context"',
            camera_angle_cue,
        ),
    )

    cat_deliverables_hint = {
        "Product sketch": 'Subquestion A: "5 user pain points", Subquestion B: "Annotated 3/4 perspective sketch"',
        "Problem identification": 'Subquestion A: "5 usability/safety problems", Subquestion B: "Annotated fix sketch"',
        "Storyboard": 'Subquestion A: "Brief narrative outline", Subquestion B: "4-frame sequential drawing"',
        "Logos, Symbols & Signs": 'Subquestion A: "Set of 4 pictogram marks", Subquestion B: "Visual rationale notes"',
        "Creativity": 'Subquestion A: "Design rationale & 3 features", Subquestion B: "Annotated concept sketch"',
        "Composition": 'Subquestion A: "Visual hierarchy notes", Subquestion B: "Framed poster sketch"',
        "Drawing": 'Subquestion A: "3 proportional object studies", Subquestion B: "Human interaction sketch"',
        "Design aptitude": 'Subquestion A: "Key insights & analysis", Subquestion B: "Design concept drawing"',
    }.get(category, 'Subquestion A: "Structured observations", Subquestion B: "Annotated concept sketch"')

    diff_cues = {
        "Easy": "Direct, accessible everyday observation or straightforward functional redesign with 1 user group.",
        "Medium": "Balanced everyday scenario requiring keen empathy, realistic functional ergonomics, and 1-2 practical constraints.",
        "Hard": "Demanding design challenge with stringent real-world constraints (e.g. extreme climate, multiple conflicting user needs, zero-electricity, or tight physical space limits).",
    }
    diff_guideline = diff_cues.get(difficulty, diff_cues["Medium"])

    user_prompt = f"""Write ONE original, exam-ready NID M.Des / CEED Part B question as compact JSON.
Required Category (exact string): {category}
Focus Topic (stay 100% anchored to this ONE single subject): {context_seed}
Blueprint: {chosen_blueprint}
Time: {time_minutes} min | Marks: {default_marks} (Subquestion A: {half_marks} marks, Subquestion B: {rem_marks} marks) | Target Difficulty: {difficulty} ({diff_guideline})
Avoid repeating these recent titles: {recent_line}{extra_warning}

CRITICAL ANTI-HALLUCINATION RULES:
- SINGLE COHESIVE SUBJECT ONLY: Pick ONE single everyday object, situation, or user challenge. NEVER blend multiple unrelated objects or domains together (e.g. do NOT mix animals with furniture, or cartoon characters with ergonomics).
- Subquestion A and Subquestion B MUST address the exact same subject. Never switch topics mid-question.
- COHERENT DELIVERABLE DISCIPLINE: If the scenario asks to design a physical product, wearable, container, or equipment, Subquestion B MUST require drawing the product (e.g. 3/4 perspective, exploded view, or in-use scene). NEVER ask to sketch a poster, logo, or advertising graphic for a physical product challenge. Posters are strictly reserved for Composition / Awareness campaigns.
- Deliverables must match this category ({cat_deliverables_hint}). Never put "usability issues" on character/creative questions!
- COMPLETE SENTENCES: Every constraint and instruction MUST be a complete, grammatically sound sentence ending with a period. NEVER end mid-phrase or with dangling words like "without compromising on", "such as", or "due to".

Strict field rules:
- `title`: crisp 3-6 word exam title matching this ONE topic.
- `scenario`: 2-3 vivid plain-English sentences setting up the real Indian everyday context, user, and challenge.
- `subquestions`: exactly 2 items (label "A" with {half_marks} marks, label "B" with {rem_marks} marks). Follow the Blueprint closely.
- `constraints`: 1-2 realistic constraints strictly belonging to THIS topic (never invent unrelated objects, always complete sentences).
- `sketching_requirements`: 1-2 concrete drawing expectations for THIS question ({sketch_req_example}).
- `visual_sketch_prompt`: 18-30 plain visual words describing ONLY what should be drawn for THIS exact topic ({visual_angle_guideline}) — concrete objects, human posture/hands, everyday props. Never include "examination sheet", "annotations", "labels", "realistic", or "20 minutes".
- Never mention marks rules, prompt instructions, or NID campus names."""

    cat_prio = next((c for c in analytics.category_priorities if c.category == category), None)
    priority_band = theme.priority_band if theme else (cat_prio.priority_band if cat_prio else 3)
    priority_reason = (
        theme.model_interpretation
        if theme
        else (cat_prio.reason if cat_prio else "Balanced NID M.Des DAT Prelims readiness.")
    )
    hist_refs = (
        []
        if analytics.dataset_summary["total_records"] == 0
        else evidence_bullets[:3]
    )

    hydration_defaults: Dict[str, object] = {
        "category": category,
        "programme_tags": programme_tags[:3] if programme_tags else ["Product Design"],
        "archetypes": archetypes,
        "competencies": ["Observation", "Empathy", "Problem framing", "Visual communication"],
        "difficulty": difficulty,
        "time_minutes": time_minutes,
        "total_marks": default_marks,
        "practice_priority": priority_band,
        "priority_reason": priority_reason,
        "prediction_confidence": theme.confidence if theme else analytics.confidence_level,
        "historical_pattern_references": hist_refs,
        "suggested_time_split": _build_category_time_split(category, time_minutes),
        "evaluation_rubric": _build_category_rubric(category, default_marks),
    }

    return user_prompt, evidence_bullets, hydration_defaults


class QuestionGenerator:
    """Orchestrates Modes A, B, C, and D question generation via the local LLM."""

    def __init__(self, db: Database, llm_service: LLMService) -> None:
        self.db = db
        self.llm = llm_service

    def _collect_recent_fingerprints(self, extra_exclude: List[str]) -> List[str]:
        recent_gen = self.db.list_generated_questions(limit=25)
        recent_attempts = self.db.list_practice_attempts(limit=25)
        items: List[str] = []
        seen: set[str] = set()
        for q in recent_gen:
            key = q.title.strip().lower()
            if key not in seen:
                seen.add(key)
                items.append(f"{q.title}: {q.scenario[:110]}")
        for a in recent_attempts:
            key = a.question_title.strip().lower()
            if key not in seen:
                seen.add(key)
                items.append(a.question_title)
        for ex in extra_exclude:
            if ex.strip():
                items.append(ex.strip())
        return items

    def _check_duplication(
        self,
        candidate: GeneratedQuestionPayload,
        recent_gen: List[StoredGeneratedQuestion],
        historical: List[HistoricalQuestionRecord],
    ) -> Optional[str]:
        cand_blob = f"{candidate.title} {candidate.scenario}"
        for existing in recent_gen[:60]:
            sim = _jaccard_similarity(cand_blob, f"{existing.title} {existing.scenario}")
            if sim >= 0.48 or candidate.title.strip().lower() == existing.title.strip().lower():
                return f"Too similar (overlap {sim:.2f}) to previously generated question '{existing.title}'."
            title_sim = _jaccard_similarity(candidate.title, existing.title)
            if title_sim >= 0.60:
                return f"Title too similar (overlap {title_sim:.2f}) to previously generated question '{existing.title}'."
        for h in historical[:120]:
            sim = _jaccard_similarity(cand_blob, f"{h.title or ''} {h.prompt_text}")
            if sim >= 0.52:
                return f"Too similar (overlap {sim:.2f}) to historical question '{h.title or h.prompt_text[:60]}'."
        return None

    async def _generate_single(
        self,
        settings: AppSettings,
        category: str,
        programme_tags: List[str],
        active_profiles: List[str],
        difficulty: str,
        time_minutes: int,
        mode: str,
        analytics: AnalyticsOverviewResponse,
        historical_records: List[HistoricalQuestionRecord],
        recent_gen: List[StoredGeneratedQuestion],
        recent_fingerprints: List[str],
        theme: Optional[ThemePriorityItem] = None,
        modality_hint: Optional[Tuple[str, str]] = None,
        avoid_archetypes: Optional[List[str]] = None,
        exam_paper_id: Optional[str] = None,
        question_order: int = 1,
    ) -> StoredGeneratedQuestion:
        archetypes = _pick_archetypes_for_slot(
            category=category,
            active_profiles=active_profiles,
            theme=theme,
            avoid_archetypes=avoid_archetypes,
        )
        user_prompt, evidence_bullets, hydration_defaults = build_generation_prompt(
            category=category,
            archetypes=archetypes,
            programme_tags=programme_tags,
            active_profiles=active_profiles,
            difficulty=difficulty,
            time_minutes=time_minutes,
            analytics=analytics,
            historical_records=historical_records,
            recent_titles_and_scenarios=recent_fingerprints,
            theme=theme,
            modality_hint=modality_hint,
        )

        payload, raw_response, model_used = await self.llm.generate_structured_question(
            settings=settings,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            expected_category=category,
            expected_time_minutes=time_minutes,
            expected_difficulty=difficulty,
            hydration_defaults=hydration_defaults,
        )

        # Originality check with one automatic regeneration attempt if too close to prior questions
        if settings.strict_originality_check:
            dup_reason = self._check_duplication(payload, recent_gen, historical_records)
            if dup_reason:
                retry_prompt, _, retry_defaults = build_generation_prompt(
                    category=category,
                    archetypes=archetypes,
                    programme_tags=programme_tags,
                    active_profiles=active_profiles,
                    difficulty=difficulty,
                    time_minutes=time_minutes,
                    analytics=analytics,
                    historical_records=historical_records,
                    recent_titles_and_scenarios=recent_fingerprints + [f"{payload.title}: {payload.scenario[:100]}"],
                    theme=theme,
                    modality_hint=modality_hint,
                    avoid_repetition_note=(
                        f"Your previous draft was rejected because: {dup_reason} "
                        "Invent a completely different setting, user group, object, and problem angle."
                    ),
                )
                payload, raw_response, model_used = await self.llm.generate_structured_question(
                    settings=settings,
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=retry_prompt,
                    expected_category=category,
                    expected_time_minutes=time_minutes,
                    expected_difficulty=difficulty,
                    hydration_defaults=retry_defaults,
                )

        # Clean any small-model placeholder echoes in deliverables, instructions, and constraints
        payload.scenario = sanitize_complete_sentence(payload.scenario)
        for sq in payload.subquestions:
            sq.instruction = sanitize_complete_sentence(sq.instruction)
            cleaned_deliv = []
            for d in sq.deliverables:
                flat = sanitize_complete_sentence(re.sub(r"\s+", " ", d).strip()).rstrip(".")
                if len(flat) > 3 and not any(bad in flat.lower() for bad in ("noun-phrase", "noun phrase", "short concrete output", "placeholder")):
                    if len(flat) > 40:
                        flat = flat[:38].rsplit(" ", 1)[0]
                    cleaned_deliv.append(flat)
            if payload.category in ("Creativity", "Composition", "Storyboard", "Logos, Symbols & Signs"):
                cleaned_deliv = [
                    d for d in cleaned_deliv
                    if not any(bad in d.lower() for bad in ("usability", "ergonomic issue", "pain point"))
                ]
            sq.deliverables = cleaned_deliv or (["Design rationale"] if sq.label == "A" else ["Annotated sketch"])

        # Safeguard against cross-discipline deliverable contamination (e.g. asking for a poster on a physical product)
        physical_keywords = (
            "container", "bottle", "backpack", "tiffin", "lunchbox", "lamp", "stool",
            "device", "tool", "chair", "desk", "carrier", "harness", "peeler", "kettle",
            "cutter", "packaging", "dispenser", "gear", "hardware"
        )
        is_physical_problem = (
            any(w in payload.scenario.lower() or w in payload.title.lower() for w in physical_keywords)
            or payload.category in ("Product sketch",)
        )
        for sq in payload.subquestions:
            if is_physical_problem and any(bad in sq.instruction.lower() for bad in ("promotional poster", "poster", "advertising campaign")):
                sq.instruction = "Present your redesigned concept in clean 3/4 perspective showing the product in active use on-site, with circular detail callouts for key mechanisms and material notes."
                sq.deliverables = ["Annotated 3/4 perspective sketch", "Ergonomic & mechanism callouts"]

        # Guarantee complete, grammatically sound constraints (no dangling prepositions/cut-offs)
        cleaned_constraints: List[str] = []
        for c in payload.constraints:
            sanitized = sanitize_complete_sentence(c)
            if len(sanitized) > 10:
                cleaned_constraints.append(sanitized)
        payload.constraints = cleaned_constraints or ["Maintain functional clarity and realistic user proportions."]

        bad_sketch_markers = (
            "specific drawing or visual output",
            "4-step sequential narrative for one consistent",
            "communicate a practical, buildable 3d product",
            "placeholder",
        )
        cleaned_sketch_reqs = []
        for sr in payload.sketching_requirements:
            if not any(b in sr.lower() for b in bad_sketch_markers):
                sanitized_sr = sanitize_complete_sentence(sr)
                if len(sanitized_sr) > 10:
                    cleaned_sketch_reqs.append(sanitized_sr)
        if not cleaned_sketch_reqs:
            cleaned_sketch_reqs = [
                {
                    "Product sketch": "Draw a clear 3/4 perspective sketch showing working features, materials, and human scale.",
                    "Storyboard": "Use 4 neat rectangular frames with varied camera angles and consistent character appearance.",
                    "Logos, Symbols & Signs": "Render clean, high-contrast monochrome geometric marks legible at small sizes.",
                    "Drawing": "Use accurate perspective, clear foreground-background line weight, and believable proportions.",
                    "Composition": "Establish a strong focal point, clean visual hierarchy, and uncluttered negative space.",
                }.get(payload.category, "Include a clear annotated freehand sketch showing user interaction and context.")
            ]
        payload.sketching_requirements = cleaned_sketch_reqs

        # Ensure every question passes through our strict diffusion visual firewall
        raw_vsp = sanitize_subject_for_diffusion(payload.visual_sketch_prompt or "")
        meta_leak_markers = (
            "showing the specific visual solution",
            "compact foldable lunch carrier with snap-lock lid",
            "18-32",
            "45-75",
            "concrete visual",
            "visual_sketch_prompt",
            "subquestion",
            "placeholder",
        )
        fb_pos, fb_neg = build_fallback_visual_prompts(
            title=payload.title,
            scenario=payload.scenario,
            category=payload.category,
            time_minutes=payload.time_minutes,
            subquestions=[sq.instruction for sq in payload.subquestions],
            constraints=payload.constraints,
            sketching_requirements=payload.sketching_requirements,
        )
        if len(raw_vsp) < 20 or any(m in raw_vsp.lower() for m in meta_leak_markers):
            payload.visual_sketch_prompt = fb_pos
        else:
            payload.visual_sketch_prompt = raw_vsp
        if not payload.visual_negative_prompt or len(payload.visual_negative_prompt.strip()) < 20:
            payload.visual_negative_prompt = default_negative_for_category(payload.category) or fb_neg

        # Enrich programme_tags & competencies dynamically from the actual generated scenario text
        full_text_blob = " ".join(
            [payload.title, payload.scenario] + [sq.instruction for sq in payload.subquestions]
        )
        inferred = classify_question_text(full_text_blob, explicit_category=payload.category)
        canonical_programmes = {
            "Product sketch": ["Product Design", "Furniture & Interior Design"],
            "Storyboard": ["Animation Film Design", "Film & Video Communication"],
            "Composition": ["Graphic Design", "Communication Design"],
            "Logos, Symbols & Signs": ["Graphic Design", "Information Design"],
            "Creativity": ["New Media Design", "Design for Retail Experience"],
            "Drawing": ["Design Drawing", "Visual Communication"],
            "Problem identification": ["Universal Design", "Design for Sustainability"],
            "Design aptitude": ["Strategic Design Management", "Product Design"],
        }.get(payload.category, ["Product Design"])
        if not programme_tags:
            valid_inferred = [p for p in inferred.get("programme_tags", []) if p in canonical_programmes]
            payload.programme_tags = valid_inferred[:2] or canonical_programmes[:2]
        if inferred["competencies"]:
            merged_comps = list(dict.fromkeys(inferred["competencies"] + payload.competencies))
            payload.competencies = merged_comps[:5]

        # Anchor priority score & confidence strictly to deterministic analytics (no hallucinated confidence)
        cat_prio = next((c for c in analytics.category_priorities if c.category == payload.category), None)
        if theme:
            priority_score = theme.practice_priority_score
            priority_band = theme.priority_band
            confidence = theme.confidence
            hist_evidence = [theme.historical_evidence] + evidence_bullets[:3]
            model_interp = theme.model_interpretation
        elif cat_prio:
            priority_score = cat_prio.practice_priority_score
            priority_band = cat_prio.priority_band
            confidence = analytics.confidence_level
            hist_evidence = evidence_bullets[:4]
            model_interp = cat_prio.reason
        else:
            priority_score = 50.0
            priority_band = 3
            confidence = analytics.confidence_level
            hist_evidence = evidence_bullets[:4]
            model_interp = payload.priority_reason

        # Enforce strict honesty when dataset is empty
        if analytics.dataset_summary["total_records"] == 0:
            payload.prediction_confidence = "Low"
            payload.historical_pattern_references = []
        else:
            payload.prediction_confidence = confidence
        payload.practice_priority = priority_band

        stored = StoredGeneratedQuestion(
            **payload.model_dump(),
            id=str(uuid.uuid4()),
            generation_mode=mode,  # type: ignore[arg-type]
            exam_paper_id=exam_paper_id,
            question_order=question_order,
            is_saved=False,
            model_used=model_used,
            provider_used=settings.provider,
            practice_priority_score=priority_score,
            historical_evidence=hist_evidence,
            model_interpretation=model_interp,
            low_confidence_warning=analytics.low_confidence_warning,
            raw_llm_response=raw_response,
            created_at=utc_now_iso(),
        )
        self.db.save_generated_question(stored)
        recent_gen.insert(0, stored)
        recent_fingerprints.insert(0, f"{stored.title}: {stored.scenario[:110]}")
        return stored

    async def generate_questions(self, req: GenerateQuestionsRequest) -> GenerateQuestionsResponse:
        settings = self.db.get_settings()
        # When no optional programme focus is picked, strictly lock to the authentic 2026 NID M.Des Common Paper model ("general_nid_mdes")
        if not req.programme_focus:
            active_profiles = ["general_nid_mdes"]
        else:
            active_profiles = req.active_profiles if req.active_profiles else settings.active_profiles
        historical_records = self.db.list_historical_questions()
        attempts = self.db.list_practice_attempts(limit=300)
        weak_areas = self.db.list_weak_areas()
        recent_gen = self.db.list_generated_questions(limit=40)
        recent_fingerprints = self._collect_recent_fingerprints(req.exclude_titles)

        analytics = compute_analytics_and_predictions(
            historical_records=historical_records,
            attempts=attempts,
            weak_areas=weak_areas,
            settings=settings,
            override_profiles=active_profiles,
        )

        warnings: List[str] = []
        if analytics.low_confidence_warning and req.mode == "likely_exam":
            warnings.append(analytics.low_confidence_warning)

        # Build generation slots depending on Mode A, B, or C
        slots: List[Tuple[str, Optional[ThemePriorityItem]]] = []

        if req.mode == "category":
            selected = [c for c in req.categories if c in CATEGORIES] or list(CATEGORIES)
            count = req.count
            # Requirement: When all categories are selected, generate at least one per category
            if len(set(selected)) == len(CATEGORIES) and count < len(CATEGORIES):
                count = len(CATEGORIES)
                warnings.append(
                    "All 7 categories were selected; adjusted batch size to 7 so every category gets at least one question."
                )
            allocated = allocate_categories_mode_a(selected, count)
            slots = [(cat, None) for cat in allocated]

        elif req.mode == "balanced_random":
            allocated = allocate_categories_mode_b(
                count=req.count,
                strategy=req.random_strategy,
                category_priorities=analytics.category_priorities,
                custom_weights=req.custom_category_weights,
            )
            slots = [(cat, None) for cat in allocated]

        elif req.mode == "likely_exam":
            paired = allocate_slots_mode_c(
                count=req.count,
                analytics=analytics,
                preferred_categories=req.categories if req.categories else None,
                focus_theme_id=req.focus_theme_id,
            )
            slots = [(cat, theme) for cat, theme in paired]
        else:
            allocated = allocate_categories_mode_b(req.count, "completely_balanced", analytics.category_priorities)
            slots = [(cat, None) for cat in allocated]

        generated: List[StoredGeneratedQuestion] = []
        used_archetypes: List[str] = []
        distribution: Dict[str, int] = {}

        for idx, (cat, theme) in enumerate(slots, start=1):
            modality = _pick_nid_blueprint_and_topic(
                cat, active_profiles, slot_idx=idx - 1, historical_fingerprints=recent_fingerprints
            )
            target_diff = req.difficulty
            if target_diff in ("Random", "Mixed"):
                target_diff = random.choice(["Easy", "Medium", "Hard"])
            q = await self._generate_single(
                settings=settings,
                category=cat,
                programme_tags=req.programme_tags,
                active_profiles=active_profiles,
                difficulty=target_diff,
                time_minutes=req.time_minutes,
                mode=req.mode,
                analytics=analytics,
                historical_records=historical_records,
                recent_gen=recent_gen,
                recent_fingerprints=recent_fingerprints,
                theme=theme,
                modality_hint=modality,
                avoid_archetypes=used_archetypes[-3:] if len(slots) > 1 else None,
                question_order=idx,
            )
            generated.append(q)
            used_archetypes.extend(q.archetypes)
            distribution[q.category] = distribution.get(q.category, 0) + 1

        return GenerateQuestionsResponse(
            questions=generated,
            warnings=warnings,
            distribution_summary=distribution,
        )

    async def generate_exam_paper(self, req: ExamPaperCreateRequest) -> ExamPaperRecord:
        """Mode D — Exam Simulator: generates a multi-question mock paper with diverse skills."""
        settings = self.db.get_settings()
        # When no optional programme focus is picked, strictly lock to the authentic 2026 NID M.Des Common Paper model ("general_nid_mdes")
        if not req.programme_focus:
            active_profiles = ["general_nid_mdes"]
        else:
            active_profiles = req.active_profiles if req.active_profiles else settings.active_profiles
        historical_records = self.db.list_historical_questions()
        attempts = self.db.list_practice_attempts(limit=300)
        weak_areas = self.db.list_weak_areas()
        recent_gen = self.db.list_generated_questions(limit=40)
        recent_fingerprints = self._collect_recent_fingerprints([])

        analytics = compute_analytics_and_predictions(
            historical_records=historical_records,
            attempts=attempts,
            weak_areas=weak_areas,
            settings=settings,
            override_profiles=active_profiles,
        )

        warnings: List[str] = []
        if analytics.low_confidence_warning and req.paper_strategy == "prediction_oriented":
            warnings.append(analytics.low_confidence_warning)

        # Determine categories and optional themes across paper
        if req.category_distribution == "custom" and req.custom_categories:
            cats = allocate_categories_mode_a(req.custom_categories, req.num_questions)
            slots: List[Tuple[str, Optional[ThemePriorityItem]]] = []
            for i, cat in enumerate(cats):
                theme = (
                    analytics.theme_priorities[i % len(analytics.theme_priorities)]
                    if req.paper_strategy == "prediction_oriented" and req.historical_relevance != "low"
                    else None
                )
                slots.append((cat, theme))
        elif req.paper_strategy == "prediction_oriented":
            preferred = None
            if req.category_distribution == "balanced":
                cats = allocate_categories_mode_b(req.num_questions, "completely_balanced", analytics.category_priorities)
                slots = [
                    (cat, analytics.theme_priorities[i % len(analytics.theme_priorities)])
                    for i, cat in enumerate(cats)
                ]
            else:
                slots = allocate_slots_mode_c(req.num_questions, analytics, preferred_categories=preferred)
        else:
            strategy = "weighted" if req.category_distribution == "profile_weighted" else "completely_balanced"
            cats = allocate_categories_mode_b(req.num_questions, strategy, analytics.category_priorities)
            slots = [(cat, None) for cat in cats]

        # Compute realistic per-question time splits summing exactly to total_time_minutes
        base_time = max(10, req.total_time_minutes // req.num_questions)
        per_q_times = [base_time] * req.num_questions
        remainder = req.total_time_minutes - sum(per_q_times)
        for i in range(abs(remainder)):
            idx = i % req.num_questions
            per_q_times[idx] += 1 if remainder > 0 else -1

        # Difficulty mix for "Mixed" or "Random"
        if req.difficulty in ("Mixed", "Random"):
            cycle = ["Medium", "Medium", "Hard", "Easy", "Hard"]
            difficulties = [cycle[i % len(cycle)] for i in range(req.num_questions)]
            random.shuffle(difficulties)
        else:
            difficulties = [req.difficulty] * req.num_questions

        paper_id = str(uuid.uuid4())
        paper_title = (
            req.title.strip()
            if req.title and req.title.strip()
            else f"NID M.Des DAT Prelims Mock Paper ({req.num_questions}Q • {req.total_time_minutes} min)"
        )

        paper = ExamPaperRecord(
            id=paper_id,
            title=paper_title,
            num_questions=req.num_questions,
            total_time_minutes=req.total_time_minutes,
            difficulty=req.difficulty,
            paper_strategy=req.paper_strategy,
            historical_relevance=req.historical_relevance,
            programme_focus=req.programme_focus,
            status="not_started",
            elapsed_seconds=0,
            created_at=utc_now_iso(),
            questions=[],
            warnings=warnings,
        )
        self.db.create_exam_paper(paper)

        used_archetypes: List[str] = []
        generated_questions: List[StoredGeneratedQuestion] = []

        try:
            for idx, (cat, theme) in enumerate(slots, start=1):
                modality = _pick_nid_blueprint_and_topic(
                    cat, active_profiles, slot_idx=idx - 1, historical_fingerprints=recent_fingerprints
                )
                q = await self._generate_single(
                    settings=settings,
                    category=cat,
                    programme_tags=req.programme_focus,
                    active_profiles=active_profiles,
                    difficulty=difficulties[idx - 1],
                    time_minutes=per_q_times[idx - 1],
                    mode="exam_simulator",
                    analytics=analytics,
                    historical_records=historical_records,
                    recent_gen=recent_gen,
                    recent_fingerprints=recent_fingerprints,
                    theme=theme,
                    modality_hint=modality,
                    avoid_archetypes=used_archetypes[-4:],
                    exam_paper_id=paper_id,
                    question_order=idx,
                )
                generated_questions.append(q)
                used_archetypes.extend(q.archetypes)
        except Exception:
            # Clean up empty/incomplete paper shell if generation fails mid-way
            if not generated_questions:
                self.db.delete_exam_paper(paper_id)
            raise

        paper.questions = generated_questions
        return paper
