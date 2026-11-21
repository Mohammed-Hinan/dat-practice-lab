import type {
  AnalyticsOverview,
  AppSettings,
  CraftSketchPromptResponse,
  DashboardData,
  DrawThingsEssence,
  DrawThingsGenerateResponse,
  DrawThingsStatus,
  ExamPaperCreateRequest,
  ExamPaperRecord,
  GeneratedQuestion,
  GenerateQuestionsRequest,
  GenerateQuestionsResponse,
  HistoricalQuestion,
  LLMConnectionStatus,
  ParsedQuestionDraft,
  PracticeAttempt,
  ProviderType,
  SketchStylePreset,
  TaxonomyData,
  VisualLearningRecord,
  WeakArea,
} from './types';

const rawEnvUrl = String(import.meta.env.VITE_API_BASE_URL || '').trim();
// Auto-correct any legacy typo where '-lab' was omitted from the Render subdomain
const cleanUrl =
  rawEnvUrl.includes('dat-practice-backend.onrender.com') || !rawEnvUrl
    ? 'https://dat-practice-lab.onrender.com'
    : rawEnvUrl;

export const API_BASE =
  typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') &&
  !rawEnvUrl
    ? '/api'
    : `${cleanUrl.replace(/\/$/, '')}/api`;

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
    ...options,
  });

  if (!resp.ok) {
    let message = `Request failed (${resp.status})`;
    try {
      const data = await resp.json();
      if (typeof data?.detail === 'string') {
        message = data.detail;
      } else if (Array.isArray(data?.detail)) {
        message = data.detail.map((e: { msg?: string }) => e.msg || JSON.stringify(e)).join('; ');
      }
    } catch {
      const txt = await resp.text();
      if (txt) message = txt.slice(0, 300);
    }
    throw new Error(message);
  }
  return (await resp.json()) as T;
}

export const api = {
  getTaxonomy: () => request<TaxonomyData>('/taxonomy'),
  getDashboard: () => request<DashboardData>('/dashboard'),
  getSettings: () => request<AppSettings>('/settings'),
  updateSettings: (settings: AppSettings) =>
    request<AppSettings>('/settings', { method: 'PUT', body: JSON.stringify(settings) }),

  getLLMStatus: () => request<LLMConnectionStatus>('/llm/status'),
  testLLM: (payload: {
    provider?: ProviderType;
    base_url?: string;
    api_key?: string;
    model?: string;
  }) => request<LLMConnectionStatus>('/llm/test', { method: 'POST', body: JSON.stringify(payload) }),

  getDrawThingsStatus: () => request<DrawThingsStatus>('/drawthings/status'),
  getDrawThingsEssence: () => request<DrawThingsEssence>('/drawthings/essence'),
  craftSketchPrompt: (payload: {
    title: string;
    scenario: string;
    category: string;
    subquestions?: string[];
    constraints?: string[];
    sketching_requirements?: string[];
    time_minutes?: number;
    style_preset: SketchStylePreset;
  }) =>
    request<CraftSketchPromptResponse>('/drawthings/craft-prompt', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  testDrawThings: (base_url?: string) =>
    request<DrawThingsStatus>('/drawthings/test', {
      method: 'POST',
      body: JSON.stringify({ base_url }),
    }),
  generateReferenceSketch: (payload: {
    question_id?: string;
    question_title?: string;
    category?: string;
    prompt: string;
    negative_prompt?: string;
    style_preset: SketchStylePreset;
    width?: number;
    height?: number;
    steps?: number;
    cfg_scale?: number;
    seed?: number;
    init_image_base64?: string | null;
    denoising_strength?: number;
    older_image_url?: string;
    older_prompt?: string;
  }) =>
    request<DrawThingsGenerateResponse>('/drawthings/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  listLearnedRules: (category?: string) => {
    const q = category ? `?category=${encodeURIComponent(category)}` : '';
    return request<VisualLearningRecord[]>(`/drawthings/learned-rules${q}`);
  },
  deleteLearnedRule: (ruleId: string) =>
    request<{ deleted: boolean }>(`/drawthings/learned-rules/${ruleId}`, { method: 'DELETE' }),

  generateQuestions: (payload: GenerateQuestionsRequest, signal?: AbortSignal) =>
    request<GenerateQuestionsResponse>('/questions/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
      signal,
    }),
  listGeneratedQuestions: (params?: { saved_only?: boolean; category?: string; limit?: number }) => {
    const sp = new URLSearchParams();
    if (params?.saved_only) sp.set('saved_only', 'true');
    if (params?.category) sp.set('category', params.category);
    if (params?.limit) sp.set('limit', String(params.limit));
    const q = sp.toString();
    return request<GeneratedQuestion[]>(`/questions${q ? `?${q}` : ''}`);
  },
  toggleSaveQuestion: (id: string, saved: boolean) =>
    request<GeneratedQuestion>(`/questions/${id}/save`, {
      method: 'PATCH',
      body: JSON.stringify({ saved }),
    }),
  deleteGeneratedQuestion: (id: string) =>
    request<{ deleted: boolean }>(`/questions/${id}`, { method: 'DELETE' }),

  generateExamPaper: (payload: ExamPaperCreateRequest) =>
    request<ExamPaperRecord>('/exams/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  listExamPapers: () => request<ExamPaperRecord[]>('/exams'),
  updateExamPaperState: (id: string, patch: { status?: string; elapsed_seconds?: number }) =>
    request<ExamPaperRecord>(`/exams/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    }),
  deleteExamPaper: (id: string) =>
    request<{ deleted: boolean }>(`/exams/${id}`, { method: 'DELETE' }),

  listHistorical: (params?: { category?: string; programme?: string; year?: string; search?: string }) => {
    const sp = new URLSearchParams();
    if (params?.category) sp.set('category', params.category);
    if (params?.programme) sp.set('programme', params.programme);
    if (params?.year) sp.set('year', params.year);
    if (params?.search) sp.set('search', params.search);
    const q = sp.toString();
    return request<HistoricalQuestion[]>(`/historical${q ? `?${q}` : ''}`);
  },
  createHistorical: (payload: Partial<HistoricalQuestion> & { prompt_text: string }) =>
    request<HistoricalQuestion>('/historical', { method: 'POST', body: JSON.stringify(payload) }),
  updateHistorical: (id: string, patch: Partial<HistoricalQuestion>) =>
    request<HistoricalQuestion>(`/historical/${id}`, { method: 'PUT', body: JSON.stringify(patch) }),
  deleteHistorical: (id: string) =>
    request<{ deleted: boolean }>(`/historical/${id}`, { method: 'DELETE' }),
  parseHistoricalBulk: (payload: { format: 'text' | 'csv' | 'json'; content: string; default_source?: string }) =>
    request<{ drafts: ParsedQuestionDraft[]; errors: string[] }>('/historical/parse', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  importHistoricalDrafts: (questions: ParsedQuestionDraft[]) =>
    request<HistoricalQuestion[]>('/historical/import', {
      method: 'POST',
      body: JSON.stringify({ questions }),
    }),

  getAnalyticsOverview: () => request<AnalyticsOverview>('/analytics/overview'),

  listAttempts: (params?: { category?: string; status?: string }) => {
    const sp = new URLSearchParams();
    if (params?.category) sp.set('category', params.category);
    if (params?.status) sp.set('status', params.status);
    const q = sp.toString();
    return request<PracticeAttempt[]>(`/attempts${q ? `?${q}` : ''}`);
  },
  createAttempt: (payload: Omit<PracticeAttempt, 'id' | 'attempted_at'>) =>
    request<PracticeAttempt>('/attempts', { method: 'POST', body: JSON.stringify(payload) }),
  updateAttempt: (
    id: string,
    patch: Partial<Pick<PracticeAttempt, 'time_spent_seconds' | 'self_difficulty' | 'status' | 'notes' | 'rubric_revealed'>>
  ) => request<PracticeAttempt>(`/attempts/${id}`, { method: 'PATCH', body: JSON.stringify(patch) }),
  deleteAttempt: (id: string) =>
    request<{ deleted: boolean }>(`/attempts/${id}`, { method: 'DELETE' }),

  listWeakAreas: () => request<WeakArea[]>('/weak-areas'),
  createWeakArea: (payload: Omit<WeakArea, 'id' | 'created_at'>) =>
    request<WeakArea>('/weak-areas', { method: 'POST', body: JSON.stringify(payload) }),
  deleteWeakArea: (id: string) =>
    request<{ deleted: boolean }>(`/weak-areas/${id}`, { method: 'DELETE' }),

  pingPresence: (clientId?: string) =>
    request<{
      live_count: number;
      real_connected: number;
      cohort: string;
      active_cities: string[];
      timestamp: number;
    }>('/presence/ping', {
      method: 'POST',
      body: JSON.stringify({ client_id: clientId }),
    }),
  getPresence: () =>
    request<{
      live_count: number;
      real_connected: number;
      cohort: string;
      active_cities: string[];
      timestamp: number;
    }>('/presence'),
};

export function formatDuration(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds));
  const hrs = Math.floor(s / 3600);
  const mins = Math.floor((s % 3600) / 60);
  const secs = s % 60;
  if (hrs > 0) {
    return `${hrs}h ${String(mins).padStart(2, '0')}m`;
  }
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}
