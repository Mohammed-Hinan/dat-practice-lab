"""Pydantic schemas for DAT Practice Lab API and LLM validation."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

from .taxonomy import ARCHETYPE_NAMES, CATEGORIES, PREPARATION_PROFILES, PROGRAMME_TAGS


DifficultyLevel = Literal["Easy", "Medium", "Hard", "Random"]
ConfidenceLevel = Literal["Low", "Medium", "High"]
ProviderType = Literal["gemini", "groq", "ollama", "lmstudio", "custom_openai"]
GenerationMode = Literal["category", "balanced_random", "likely_exam", "exam_simulator"]
RandomStrategy = Literal["completely_balanced", "weighted"]
AttemptStatus = Literal["completed", "skipped", "in_progress"]
SelfDifficulty = Literal["Easy", "Medium", "Hard", "Very Hard"]


# ---------------------------------------------------------------------------
# LLM Structured Question Schema (Section 8)
# ---------------------------------------------------------------------------


class SubQuestion(BaseModel):
    label: str = Field(default="A", min_length=1, max_length=16)
    instruction: str = Field(..., min_length=10)
    marks: int = Field(default=10, ge=1, le=100)
    deliverables: List[str] = Field(default_factory=list)


class RubricItem(BaseModel):
    criterion: str = Field(..., min_length=2)
    marks: int = Field(default=5, ge=1, le=100)


class TimeSplitItem(BaseModel):
    activity: str = Field(..., min_length=2)
    minutes: int = Field(default=5, ge=1, le=240)


class GeneratedQuestionPayload(BaseModel):
    """Strict schema validated against every local LLM question response."""

    title: str = Field(..., min_length=5, max_length=180)
    category: str
    programme_tags: List[str] = Field(default_factory=list)
    archetypes: List[str] = Field(default_factory=list)
    competencies: List[str] = Field(default_factory=list)
    difficulty: DifficultyLevel = "Medium"
    time_minutes: int = Field(default=30, ge=5, le=240)
    total_marks: int = Field(default=20, ge=5, le=200)
    scenario: str = Field(..., min_length=25)
    subquestions: List[SubQuestion] = Field(..., min_length=1)
    constraints: List[str] = Field(default_factory=list)
    sketching_requirements: List[str] = Field(default_factory=list)
    visual_sketch_prompt: str = Field(default="", max_length=1200)
    visual_negative_prompt: str = Field(default="", max_length=800)
    evaluation_rubric: List[RubricItem] = Field(..., min_length=2)
    practice_priority: int = Field(default=3, ge=1, le=5)
    priority_reason: str = Field(..., min_length=10)
    prediction_confidence: ConfidenceLevel = "Low"
    historical_pattern_references: List[str] = Field(default_factory=list)
    suggested_time_split: List[TimeSplitItem] = Field(..., min_length=2)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        lookup = {c.lower(): c for c in CATEGORIES}
        key = v.strip().lower()
        if key not in lookup:
            raise ValueError(f"category must be one of {CATEGORIES}, got '{v}'")
        return lookup[key]

    @field_validator("programme_tags")
    @classmethod
    def normalize_programme_tags(cls, tags: List[str]) -> List[str]:
        lookup = {p.lower(): p for p in PROGRAMME_TAGS}
        cleaned: List[str] = []
        for t in tags:
            k = t.strip().lower()
            if k in lookup and lookup[k] not in cleaned:
                cleaned.append(lookup[k])
        return cleaned or ["Product Design"]

    @field_validator("archetypes")
    @classmethod
    def normalize_archetypes(cls, items: List[str]) -> List[str]:
        lookup = {a.lower(): a for a in ARCHETYPE_NAMES}
        cleaned: List[str] = []
        for item in items:
            k = item.strip().lower()
            if k in lookup and lookup[k] not in cleaned:
                cleaned.append(lookup[k])
        return cleaned

    @field_validator("competencies")
    @classmethod
    def ensure_competencies(cls, items: List[str]) -> List[str]:
        cleaned = [x.strip() for x in items if x and x.strip()]
        if not cleaned:
            raise ValueError("competencies must contain at least one competency")
        return cleaned[:8]

    @model_validator(mode="after")
    def validate_marks_consistency(self) -> "GeneratedQuestionPayload":
        # Allow minor LLM arithmetic drift by aligning total_marks to subquestions sum if reasonable
        sub_sum = sum(sq.marks for sq in self.subquestions)
        if sub_sum > 0 and sub_sum != self.total_marks:
            self.total_marks = sub_sum
        rubric_sum = sum(r.marks for r in self.evaluation_rubric)
        if rubric_sum != self.total_marks and rubric_sum > 0 and len(self.evaluation_rubric) > 0:
            # Proportionally scale rubric marks to sum to total_marks
            scaled = [max(1, round(r.marks * self.total_marks / rubric_sum)) for r in self.evaluation_rubric]
            diff = self.total_marks - sum(scaled)
            scaled[0] = max(1, scaled[0] + diff)
            for r, m in zip(self.evaluation_rubric, scaled):
                r.marks = m
        return self


class StoredGeneratedQuestion(GeneratedQuestionPayload):
    id: str
    generation_mode: GenerationMode
    exam_paper_id: Optional[str] = None
    question_order: int = 1
    is_saved: bool = False
    model_used: str = ""
    provider_used: str = ""
    practice_priority_score: float = 0.0
    historical_evidence: List[str] = Field(default_factory=list)
    model_interpretation: str = ""
    low_confidence_warning: Optional[str] = None
    raw_llm_response: str = ""
    created_at: str


# ---------------------------------------------------------------------------
# Settings & Local LLM Configuration
# ---------------------------------------------------------------------------


class PredictionWeights(BaseModel):
    multi_year_recurrence: float = Field(default=30.0, ge=0, le=100)
    recency: float = Field(default=20.0, ge=0, le=100)
    cross_relevance: float = Field(default=20.0, ge=0, le=100)
    profile_relevance: float = Field(default=15.0, ge=0, le=100)
    practice_gaps: float = Field(default=15.0, ge=0, le=100)


class AppSettings(BaseModel):
    provider: ProviderType = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    lmstudio_base_url: str = "http://localhost:1234/v1"
    custom_base_url: str = "http://localhost:8000/v1"
    custom_api_key: str = ""
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    gemini_text_model: str = "gemini-3.5-flash-lite"
    model: str = ""
    temperature: float = Field(default=0.75, ge=0.0, le=1.5)
    max_tokens: int = Field(default=2400, ge=512, le=8192)
    top_p: float = Field(default=0.92, ge=0.1, le=1.0)
    max_retries: int = Field(default=2, ge=0, le=5)
    timeout_seconds: int = Field(default=240, ge=15, le=600)
    enforce_json_mode: bool = True
    strict_originality_check: bool = True
    active_profiles: List[str] = Field(
        default_factory=lambda: [
            "general_nid_mdes",
        ]
    )
    prediction_weights: PredictionWeights = Field(default_factory=PredictionWeights)
    custom_category_weights: Dict[str, float] = Field(
        default_factory=lambda: {cat: 1.0 for cat in CATEGORIES}
    )
    # Sketch Reference Provider & Cloud Generation settings
    sketch_provider: Literal["gemini_imagen", "pollinations_flux", "drawthings", "openai_dalle"] = "gemini_imagen"
    gemini_api_key: str = ""
    openai_api_key: str = ""
    # Key presence status flags (safe to expose publicly to clients/peers without revealing raw secret keys)
    has_gemini_key: bool = False
    has_groq_key: bool = False
    has_custom_key: bool = False
    has_openai_key: bool = False
    # Local Draw Things Sketch Reference settings (8 GB M1 friendly defaults — tuned for DreamShaper XL Turbo 8-bit)
    drawthings_enabled: bool = True
    drawthings_base_url: str = "http://127.0.0.1:7860"
    drawthings_width: int = Field(default=640, ge=256, le=1024)
    drawthings_height: int = Field(default=640, ge=256, le=1024)
    drawthings_steps: int = Field(default=6, ge=4, le=50)
    drawthings_cfg_scale: float = Field(default=2.8, ge=1.0, le=15.0)
    auto_unload_llm_for_sketch: bool = True

    @field_validator("active_profiles")
    @classmethod
    def validate_profiles(cls, profiles: List[str]) -> List[str]:
        valid = [p for p in profiles if p in PREPARATION_PROFILES]
        return valid or ["general_nid_mdes"]


class DrawThingsStatus(BaseModel):
    connected: bool
    endpoint: str
    active_model: Optional[str] = None
    grpc_detected_on_7859: bool = False
    latency_ms: Optional[int] = None
    message: str


SketchStylePreset = Literal[
    "product_sketch",
    "exploded_view",
    "observational_pencil",
    "perspective_worm_eye",
    "perspective_bird_eye",
    "storyboard_frame",
    "logo_symbol",
    "problem_ergonomic_analysis",
    "metamorphosis_4stage",
    "poster_metaphor",
    "character_mascot",
]


class VisualDeltaAnalysis(BaseModel):
    what_changed: str
    why_changed: str
    actionable_guidelines: str
    negative_guidelines: str = ""
    category: str = ""
    archetype: str = ""


class VisualLearningRecord(BaseModel):
    id: str
    question_id: Optional[str] = None
    question_title: str
    category: str
    archetype: str = ""
    older_prompt: str = ""
    older_image_url: str = ""
    uploaded_image_url: str = ""
    new_image_url: str = ""
    what_changed: str
    why_changed: str
    actionable_guidelines: str
    negative_guidelines: str = ""
    created_at: str


class VisualLearningCreate(BaseModel):
    question_id: Optional[str] = None
    question_title: str
    category: str
    archetype: str = ""
    older_prompt: str = ""
    older_image_url: str = ""
    uploaded_image_url: str = ""
    new_image_url: str = ""
    what_changed: str
    why_changed: str
    actionable_guidelines: str
    negative_guidelines: str = ""


class DrawThingsGenerateRequest(BaseModel):
    question_id: Optional[str] = None
    question_title: Optional[str] = None
    category: Optional[str] = None
    prompt: str = Field(..., min_length=5, max_length=2000)
    negative_prompt: Optional[str] = Field(default=None, max_length=1500)
    style_preset: SketchStylePreset = "product_sketch"
    width: Optional[int] = Field(default=None, ge=256, le=1024)
    height: Optional[int] = Field(default=None, ge=256, le=1024)
    steps: Optional[int] = Field(default=None, ge=4, le=50)
    cfg_scale: Optional[float] = Field(default=None, ge=1.0, le=15.0)
    seed: int = Field(default=-1, ge=-1)
    init_image_base64: Optional[str] = None
    denoising_strength: float = Field(default=0.58, ge=0.15, le=0.95)
    older_image_url: Optional[str] = None
    older_prompt: Optional[str] = None


class DrawThingsGenerateResponse(BaseModel):
    image_url: str
    filename: str
    prompt_used: str
    negative_prompt_used: str
    width: int
    height: int
    steps: int
    latency_ms: int
    mode: Literal["txt2img", "img2img"]
    unloaded_ollama: bool = False
    learned_analysis: Optional[VisualDeltaAnalysis] = None
    applied_rules: List[str] = Field(default_factory=list)


class CraftSketchPromptRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=240)
    scenario: str = Field(..., min_length=5, max_length=1800)
    category: str = "Product sketch"
    subquestions: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    sketching_requirements: List[str] = Field(default_factory=list)
    time_minutes: int = Field(default=20, ge=5, le=180)
    style_preset: SketchStylePreset = "product_sketch"


class CraftSketchPromptResponse(BaseModel):
    visual_sketch_prompt: str
    visual_negative_prompt: str
    style_preset: SketchStylePreset
    used_llm: bool = False
    system_prompt: str
    applied_rules: List[str] = Field(default_factory=list)


class DrawThingsEssenceResponse(BaseModel):
    essence_pillars: List[str]
    system_prompt: str
    style_presets: Dict[str, Dict[str, str]]


class LLMTestRequest(BaseModel):
    provider: Optional[ProviderType] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None


class LLMConnectionStatus(BaseModel):
    connected: bool
    provider: ProviderType
    endpoint: str
    models: List[str] = Field(default_factory=list)
    selected_model: str = ""
    latency_ms: Optional[int] = None
    message: str


# ---------------------------------------------------------------------------
# Generation Requests & Exam Simulator
# ---------------------------------------------------------------------------


class GenerateQuestionsRequest(BaseModel):
    mode: GenerationMode = "balanced_random"
    categories: List[str] = Field(default_factory=list)
    programme_tags: List[str] = Field(default_factory=list)
    active_profiles: Optional[List[str]] = None
    difficulty: Literal["Easy", "Medium", "Hard", "Random", "Mixed"] = "Medium"
    time_minutes: int = Field(default=20, ge=5, le=180)
    count: int = Field(default=1, ge=1, le=10)
    random_strategy: RandomStrategy = "completely_balanced"
    custom_category_weights: Optional[Dict[str, float]] = None
    focus_theme_id: Optional[str] = None
    exclude_titles: List[str] = Field(default_factory=list)


class GenerateQuestionsResponse(BaseModel):
    questions: List[StoredGeneratedQuestion]
    warnings: List[str] = Field(default_factory=list)
    distribution_summary: Dict[str, int] = Field(default_factory=dict)


class ExamPaperCreateRequest(BaseModel):
    title: Optional[str] = None
    num_questions: int = Field(default=3, ge=1, le=10)
    total_time_minutes: int = Field(default=90, ge=15, le=300)
    difficulty: Literal["Easy", "Medium", "Hard", "Mixed", "Random"] = "Mixed"
    category_distribution: Literal["balanced", "profile_weighted", "custom"] = "balanced"
    custom_categories: List[str] = Field(default_factory=list)
    programme_focus: List[str] = Field(default_factory=list)
    active_profiles: Optional[List[str]] = None
    paper_strategy: Literal["random", "prediction_oriented"] = "prediction_oriented"
    historical_relevance: Literal["low", "medium", "high"] = "high"


class ExamPaperRecord(BaseModel):
    id: str
    title: str
    num_questions: int
    total_time_minutes: int
    difficulty: str
    paper_strategy: str
    historical_relevance: str
    programme_focus: List[str] = Field(default_factory=list)
    status: Literal["not_started", "in_progress", "completed"] = "not_started"
    elapsed_seconds: int = 0
    created_at: str
    questions: List[StoredGeneratedQuestion] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Historical Question Bank
# ---------------------------------------------------------------------------


class HistoricalQuestionBase(BaseModel):
    prompt_text: str = Field(..., min_length=10)
    title: Optional[str] = None
    year: Optional[int] = Field(default=None, ge=1980, le=2030)
    category: str = "Design aptitude"
    programme_tags: List[str] = Field(default_factory=list)
    archetypes: List[str] = Field(default_factory=list)
    competencies: List[str] = Field(default_factory=list)
    themes: List[str] = Field(default_factory=list)
    marks: Optional[int] = Field(default=None, ge=1, le=200)
    time_minutes: Optional[int] = Field(default=None, ge=5, le=240)
    source: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("category")
    @classmethod
    def check_category(cls, v: str) -> str:
        lookup = {c.lower(): c for c in CATEGORIES}
        key = v.strip().lower()
        return lookup.get(key, "Design aptitude")


class HistoricalQuestionCreate(HistoricalQuestionBase):
    pass


class HistoricalQuestionUpdate(BaseModel):
    prompt_text: Optional[str] = Field(default=None, min_length=10)
    title: Optional[str] = None
    year: Optional[int] = Field(default=None, ge=1980, le=2030)
    category: Optional[str] = None
    programme_tags: Optional[List[str]] = None
    archetypes: Optional[List[str]] = None
    competencies: Optional[List[str]] = None
    themes: Optional[List[str]] = None
    marks: Optional[int] = Field(default=None, ge=1, le=200)
    time_minutes: Optional[int] = Field(default=None, ge=5, le=240)
    source: Optional[str] = None
    notes: Optional[str] = None


class HistoricalQuestionRecord(HistoricalQuestionBase):
    id: str
    created_at: str
    updated_at: str


class BulkParseRequest(BaseModel):
    format: Literal["text", "csv", "json"]
    content: str
    default_source: Optional[str] = None


class ParsedQuestionDraft(HistoricalQuestionBase):
    auto_assigned_category: bool = True
    confidence_note: str = ""


class BulkParseResponse(BaseModel):
    drafts: List[ParsedQuestionDraft]
    errors: List[str] = Field(default_factory=list)


class BulkImportCommitRequest(BaseModel):
    questions: List[HistoricalQuestionCreate]


# ---------------------------------------------------------------------------
# Practice History & Weak Areas
# ---------------------------------------------------------------------------


class PracticeAttemptCreate(BaseModel):
    question_id: Optional[str] = None
    question_title: str = Field(..., min_length=2)
    category: str
    programme_tags: List[str] = Field(default_factory=list)
    exam_paper_id: Optional[str] = None
    time_allocated_minutes: int = Field(default=30, ge=1, le=300)
    time_spent_seconds: int = Field(default=0, ge=0)
    self_difficulty: Optional[SelfDifficulty] = None
    status: AttemptStatus = "completed"
    notes: str = ""
    rubric_revealed: bool = False


class PracticeAttemptUpdate(BaseModel):
    time_spent_seconds: Optional[int] = Field(default=None, ge=0)
    self_difficulty: Optional[SelfDifficulty] = None
    status: Optional[AttemptStatus] = None
    notes: Optional[str] = None
    rubric_revealed: Optional[bool] = None


class PracticeAttemptRecord(PracticeAttemptCreate):
    id: str
    attempted_at: str


class WeakAreaCreate(BaseModel):
    area_type: Literal["category", "competency", "theme", "programme"]
    name: str = Field(..., min_length=2)
    severity: Literal["low", "medium", "high"] = "medium"
    notes: str = ""


class WeakAreaRecord(WeakAreaCreate):
    id: str
    created_at: str


# ---------------------------------------------------------------------------
# Analytics & Predictions
# ---------------------------------------------------------------------------


class ThemePriorityItem(BaseModel):
    theme_id: str
    label: str
    description: str
    practice_priority_score: float
    priority_band: int  # 1-5
    confidence: ConfidenceLevel
    historical_count: int
    distinct_years: int
    latest_year: Optional[int] = None
    related_categories: List[str]
    factor_breakdown: Dict[str, float]
    historical_evidence: str
    model_interpretation: str


class CategoryPriorityItem(BaseModel):
    category: str
    historical_count: int
    practice_attempts: int
    practice_priority_score: float
    priority_band: int
    balanced_weight: float
    weighted_practice_share: float
    is_under_practised: bool
    is_flagged_weak: bool
    reason: str


class AnalyticsOverviewResponse(BaseModel):
    dataset_summary: Dict[str, Any]
    confidence_level: ConfidenceLevel
    low_confidence_warning: Optional[str] = None
    category_frequency: List[Dict[str, Any]]
    year_trends: List[Dict[str, Any]]
    programme_coverage: List[Dict[str, Any]]
    archetype_frequency: List[Dict[str, Any]]
    competency_frequency: List[Dict[str, Any]]
    unrepresented_topics: List[Dict[str, Any]]
    theme_priorities: List[ThemePriorityItem]
    category_priorities: List[CategoryPriorityItem]
    scoring_weights: PredictionWeights
    active_profiles: List[str]
    dnerd_reference_note: Dict[str, Any]


# ==============================================================================
# GAT (General Ability Test) Schemas
# ==============================================================================

GATSection = Literal["quantitative_ability", "analytical_reasoning", "english", "gk_awareness"]
GATQuestionType = Literal["multiple_choice", "multiple_select", "numerical"]
GATDifficulty = Literal["Easy", "Medium", "Hard"]


class GATQuestionRecord(BaseModel):
    id: str
    exam: str
    programme: str = "Common"
    section: str
    topic: str
    difficulty: str = "Medium"
    question_type: str = "multiple_choice"
    source_type: str = "previous_year"
    source_reference: Optional[str] = None
    year: Optional[int] = None
    question_text: str
    image_url: Optional[str] = None
    options: List[str] = Field(default_factory=list)
    correct_answers: List[str] = Field(default_factory=list)
    explanation: str = ""
    verified: bool = True
    created_at: str
    is_bookmarked: bool = False
    attempt_status: Optional[str] = None
    user_previous_answer: Optional[List[str]] = None


class GATQuestionCreate(BaseModel):
    id: Optional[str] = None
    exam: str
    programme: str = "Common"
    section: str
    topic: str
    difficulty: str = "Medium"
    question_type: str = "multiple_choice"
    source_type: str = "previous_year"
    source_reference: Optional[str] = None
    year: Optional[int] = None
    question_text: str
    image_url: Optional[str] = None
    options: List[str] = Field(default_factory=list)
    correct_answers: List[str] = Field(default_factory=list)
    explanation: str = ""
    verified: bool = True


class GATAttemptCreate(BaseModel):
    question_id: str
    user_answers: List[str]
    time_spent_seconds: int = 0
    mode: str = "practice"
    test_id: Optional[str] = None


class GATAttemptResult(BaseModel):
    is_correct: bool
    correct_answers: List[str]
    explanation: str
    time_spent_seconds: int


class GATLearningTopicRecord(BaseModel):
    id: str
    section: str
    topic: str
    title: str
    summary: str
    concept_markdown: str
    key_formulas_or_facts: List[str] = Field(default_factory=list)
    worked_examples: List[Dict[str, Any]] = Field(default_factory=list)
    total_questions: int = 0
    attempted_questions: int = 0
    mastery_percentage: float = 0.0


class GATVisualGKRecord(BaseModel):
    id: str
    subcategory: str
    title: str
    image_url: str
    description: str
    key_facts: List[str] = Field(default_factory=list)
    related_quiz_question_id: Optional[str] = None


class GATDailyCurrentAffairRecord(BaseModel):
    id: str
    date: str
    headline: str
    summary: str
    source_reference: str
    key_takeaways: List[str] = Field(default_factory=list)
    related_quiz_question_id: Optional[str] = None


class GATMockTestCreate(BaseModel):
    title: str
    exam: str = "NIFT M.Des GAT"
    time_limit_minutes: int = 60
    section_filter: Optional[str] = None
    num_questions: int = 30


class GATMockTestRecord(BaseModel):
    id: str
    title: str
    exam: str
    time_limit_minutes: int
    question_ids: List[str]
    user_responses: Dict[str, List[str]] = Field(default_factory=dict)
    score: float = 0.0
    total_marks: float = 0.0
    status: str = "not_started"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: str
    questions: Optional[List[GATQuestionRecord]] = None


class GATOverviewResponse(BaseModel):
    total_questions: int
    total_attempted: int
    total_correct: int
    accuracy_percentage: float
    bookmarked_count: int
    incorrect_count: int
    sections_progress: List[Dict[str, Any]]
    weak_topics: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    recommended_practice: Dict[str, Any]
