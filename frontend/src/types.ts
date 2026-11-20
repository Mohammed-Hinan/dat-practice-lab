export type DifficultyLevel = 'Easy' | 'Medium' | 'Hard' | 'Random';
export type ConfidenceLevel = 'Low' | 'Medium' | 'High';
export type ProviderType = 'gemini' | 'groq' | 'ollama' | 'lmstudio' | 'custom_openai';
export type GenerationMode = 'category' | 'balanced_random' | 'likely_exam' | 'exam_simulator';
export type RandomStrategy = 'completely_balanced' | 'weighted';
export type AttemptStatus = 'completed' | 'skipped' | 'in_progress';
export type SelfDifficulty = 'Easy' | 'Medium' | 'Hard' | 'Very Hard';

export type NavSection =
  | 'dashboard'
  | 'generate'
  | 'simulator'
  | 'bank'
  | 'trends'
  | 'history'
  | 'settings';

export interface SubQuestion {
  label: string;
  instruction: string;
  marks: number;
  deliverables: string[];
}

export interface RubricItem {
  criterion: string;
  marks: number;
}

export interface TimeSplitItem {
  activity: string;
  minutes: number;
}

export interface GeneratedQuestion {
  id: string;
  title: string;
  category: string;
  programme_tags: string[];
  archetypes: string[];
  competencies: string[];
  difficulty: DifficultyLevel;
  time_minutes: number;
  total_marks: number;
  scenario: string;
  subquestions: SubQuestion[];
  constraints: string[];
  sketching_requirements: string[];
  visual_sketch_prompt?: string;
  visual_negative_prompt?: string;
  evaluation_rubric: RubricItem[];
  practice_priority: number;
  priority_reason: string;
  prediction_confidence: ConfidenceLevel;
  historical_pattern_references: string[];
  suggested_time_split: TimeSplitItem[];
  generation_mode: GenerationMode;
  exam_paper_id?: string | null;
  question_order: number;
  is_saved: boolean;
  model_used: string;
  provider_used: string;
  practice_priority_score: number;
  historical_evidence: string[];
  model_interpretation: string;
  low_confidence_warning?: string | null;
  raw_llm_response: string;
  created_at: string;
}

export interface PreparationProfile {
  id: string;
  name: string;
  campus: string;
  is_user_defined: boolean;
  note: string;
  emphasis_areas: string[];
  favoured_archetypes: string[];
  favoured_programmes: string[];
}

export interface ArchetypeSpec {
  code: string;
  name: string;
  description: string;
  prompt_patterns: string[];
  primary_categories: string[];
}

export interface RecurringTheme {
  id: string;
  label: string;
  description: string;
  keywords: string[];
  related_categories: string[];
  related_archetypes: string[];
}

export interface TaxonomyData {
  categories: string[];
  category_definitions: Record<
    string,
    {
      description: string;
      typical_formats: string[];
      expected_balance: string;
      default_archetypes: string[];
    }
  >;
  programme_tags: string[];
  archetypes: ArchetypeSpec[];
  preparation_profiles: PreparationProfile[];
  recurring_themes: RecurringTheme[];
  competencies: string[];
  dnerd_reference: {
    source_url: string;
    total_prompts_observed: number;
    default_prompt_time_minutes: number;
    website_tag_counts: Record<string, number>;
    disclaimer: string;
  };
}

export interface PredictionWeights {
  multi_year_recurrence: number;
  recency: number;
  cross_relevance: number;
  profile_relevance: number;
  practice_gaps: number;
}

export interface AppSettings {
  provider: ProviderType;
  ollama_base_url: string;
  lmstudio_base_url: string;
  custom_base_url: string;
  custom_api_key: string;
  groq_api_key?: string;
  groq_model?: string;
  gemini_text_model?: string;
  model: string;
  temperature: number;
  max_tokens: number;
  top_p: number;
  max_retries: number;
  timeout_seconds: number;
  enforce_json_mode: boolean;
  strict_originality_check: boolean;
  active_profiles: string[];
  prediction_weights: PredictionWeights;
  custom_category_weights: Record<string, number>;
  sketch_provider: 'gemini_imagen' | 'pollinations_flux' | 'drawthings' | 'openai_dalle';
  gemini_api_key: string;
  openai_api_key: string;
  has_gemini_key?: boolean;
  has_groq_key?: boolean;
  has_custom_key?: boolean;
  has_openai_key?: boolean;
  drawthings_enabled: boolean;
  drawthings_base_url: string;
  drawthings_width: number;
  drawthings_height: number;
  drawthings_steps: number;
  drawthings_cfg_scale: number;
  auto_unload_llm_for_sketch: boolean;
}

export type SketchStylePreset =
  | 'product_sketch'
  | 'exploded_view'
  | 'observational_pencil'
  | 'perspective_worm_eye'
  | 'perspective_bird_eye'
  | 'storyboard_frame'
  | 'logo_symbol'
  | 'problem_ergonomic_analysis'
  | 'metamorphosis_4stage'
  | 'poster_metaphor'
  | 'character_mascot';

export interface DrawThingsStatus {
  connected: boolean;
  endpoint: string;
  active_model?: string | null;
  grpc_detected_on_7859: boolean;
  latency_ms?: number | null;
  message: string;
}

export interface VisualDeltaAnalysis {
  what_changed: string;
  why_changed: string;
  actionable_guidelines: string;
  negative_guidelines?: string;
  category?: string;
  archetype?: string;
}

export interface VisualLearningRecord {
  id: string;
  question_id?: string | null;
  question_title: string;
  category: string;
  archetype: string;
  older_prompt: string;
  older_image_url: string;
  uploaded_image_url: string;
  new_image_url: string;
  what_changed: string;
  why_changed: string;
  actionable_guidelines: string;
  negative_guidelines: string;
  created_at: string;
}

export interface DrawThingsGenerateResponse {
  image_url: string;
  filename: string;
  prompt_used: string;
  negative_prompt_used: string;
  width: number;
  height: number;
  steps: number;
  latency_ms: number;
  mode: 'txt2img' | 'img2img';
  unloaded_ollama: boolean;
  learned_analysis?: VisualDeltaAnalysis | null;
  applied_rules?: string[];
}

export interface DrawThingsEssence {
  essence_pillars: string[];
  system_prompt: string;
  style_presets: Record<
    string,
    {
      summary: string;
      positive_prefix: string;
      negative_prompt: string;
    }
  >;
}

export interface CraftSketchPromptResponse {
  visual_sketch_prompt: string;
  visual_negative_prompt: string;
  style_preset: SketchStylePreset;
  used_llm: boolean;
  system_prompt: string;
  applied_rules?: string[];
}

export interface LLMConnectionStatus {
  connected: boolean;
  provider: ProviderType;
  endpoint: string;
  models: string[];
  selected_model: string;
  latency_ms?: number | null;
  message: string;
}

export interface GenerateQuestionsRequest {
  mode: GenerationMode;
  categories: string[];
  programme_tags: string[];
  active_profiles?: string[];
  difficulty: DifficultyLevel;
  time_minutes: number;
  count: number;
  random_strategy: RandomStrategy;
  custom_category_weights?: Record<string, number>;
  focus_theme_id?: string | null;
  exclude_titles?: string[];
}

export interface GenerateQuestionsResponse {
  questions: GeneratedQuestion[];
  warnings: string[];
  distribution_summary: Record<string, number>;
}

export interface ExamPaperCreateRequest {
  title?: string;
  num_questions: number;
  total_time_minutes: number;
  difficulty: 'Easy' | 'Medium' | 'Hard' | 'Mixed' | 'Random';
  category_distribution: 'balanced' | 'profile_weighted' | 'custom';
  custom_categories: string[];
  programme_focus: string[];
  active_profiles?: string[];
  paper_strategy: 'random' | 'prediction_oriented';
  historical_relevance: 'low' | 'medium' | 'high';
}

export interface ExamPaperRecord {
  id: string;
  title: string;
  num_questions: number;
  total_time_minutes: number;
  difficulty: string;
  paper_strategy: string;
  historical_relevance: string;
  programme_focus: string[];
  status: 'not_started' | 'in_progress' | 'completed';
  elapsed_seconds: number;
  created_at: string;
  questions: GeneratedQuestion[];
  warnings: string[];
}

export interface HistoricalQuestion {
  id: string;
  title?: string | null;
  prompt_text: string;
  year?: number | null;
  category: string;
  programme_tags: string[];
  archetypes: string[];
  competencies: string[];
  themes: string[];
  marks?: number | null;
  time_minutes?: number | null;
  source?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ParsedQuestionDraft {
  title?: string | null;
  prompt_text: string;
  year?: number | null;
  category: string;
  programme_tags: string[];
  archetypes: string[];
  competencies: string[];
  themes: string[];
  marks?: number | null;
  time_minutes?: number | null;
  source?: string | null;
  notes?: string | null;
  auto_assigned_category: boolean;
  confidence_note: string;
}

export interface PracticeAttempt {
  id: string;
  question_id?: string | null;
  question_title: string;
  category: string;
  programme_tags: string[];
  exam_paper_id?: string | null;
  time_allocated_minutes: number;
  time_spent_seconds: number;
  self_difficulty?: SelfDifficulty | null;
  status: AttemptStatus;
  notes: string;
  rubric_revealed: boolean;
  attempted_at: string;
}

export interface WeakArea {
  id: string;
  area_type: 'category' | 'competency' | 'theme' | 'programme';
  name: string;
  severity: 'low' | 'medium' | 'high';
  notes: string;
  created_at: string;
}

export interface ThemePriorityItem {
  theme_id: string;
  label: string;
  description: string;
  practice_priority_score: number;
  priority_band: number;
  confidence: ConfidenceLevel;
  historical_count: number;
  distinct_years: number;
  latest_year?: number | null;
  related_categories: string[];
  factor_breakdown: Record<string, number>;
  historical_evidence: string;
  model_interpretation: string;
}

export interface CategoryPriorityItem {
  category: string;
  historical_count: number;
  practice_attempts: number;
  practice_priority_score: number;
  priority_band: number;
  balanced_weight: number;
  weighted_practice_share: number;
  is_under_practised: boolean;
  is_flagged_weak: boolean;
  reason: string;
}

export interface AnalyticsOverview {
  dataset_summary: {
    total_records: number;
    records_with_known_year: number;
    unknown_year_records: number;
    unknown_marks_records: number;
    unknown_source_records: number;
    distinct_years: number;
    year_range: [number, number] | null;
  };
  confidence_level: ConfidenceLevel;
  low_confidence_warning?: string | null;
  category_frequency: { category: string; count: number; percentage: number }[];
  year_trends: Record<string, string | number>[];
  programme_coverage: { programme: string; count: number; percentage: number }[];
  archetype_frequency: { code: string; archetype: string; count: number }[];
  competency_frequency: { competency: string; count: number }[];
  unrepresented_topics: { type: string; name: string; detail: string }[];
  theme_priorities: ThemePriorityItem[];
  category_priorities: CategoryPriorityItem[];
  scoring_weights: PredictionWeights;
  active_profiles: string[];
  dnerd_reference_note: TaxonomyData['dnerd_reference'];
}

export interface DashboardData {
  stats: {
    total_attempts: number;
    completed_attempts: number;
    skipped_attempts: number;
    total_practice_seconds: number;
    saved_questions_count: number;
    historical_questions_count: number;
    exam_papers_count: number;
    categories_covered: number;
    total_categories: number;
  };
  category_coverage: {
    category: string;
    attempted: number;
    historical_count: number;
    priority_score: number;
    is_under_practised: boolean;
    is_flagged_weak: boolean;
  }[];
  weak_and_under_practised: CategoryPriorityItem[];
  manual_weak_areas: WeakArea[];
  recent_questions: GeneratedQuestion[];
  top_themes: ThemePriorityItem[];
  confidence_level: ConfidenceLevel;
  low_confidence_warning?: string | null;
  active_profiles: PreparationProfile[];
  recommended_session: {
    category: string;
    theme_id?: string | null;
    theme_label: string;
    suggested_mode: GenerationMode;
    suggested_time_minutes: number;
    reason: string;
  };
}
