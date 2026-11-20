import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Bookmark,
  Check,
  CheckCircle2,
  Clock,
  Image as ImageIcon,
  Loader2,
  RefreshCw,
  Sparkles,
  Trash2,
  Zap,
} from 'lucide-react';
import { api } from '../api';
import type {
  AppSettings,
  DifficultyLevel,
  DrawThingsGenerateResponse,
  GeneratedQuestion,
  GenerationMode,
  TaxonomyData,
} from '../types';
import {
  defaultSketchStyleForCategory,
  defaultVisualPromptForQuestion,
  QuestionDisplay,
} from './QuestionDisplay';

interface QuestionGeneratorProps {
  taxonomy: TaxonomyData;
  settings: AppSettings;
  llmConnected: boolean;
  initialPreset?: { mode?: GenerationMode; categories?: string[]; themeId?: string | null } | null;
  onGoToSettings: () => void;
}

const COUNT_PRESETS = [1, 2, 3, 4, 5, 6, 8];

export const QuestionGenerator: React.FC<QuestionGeneratorProps> = ({
  taxonomy,
  settings,
  llmConnected,
  initialPreset,
  onGoToSettings,
}) => {
  const [activeTab, setActiveTab] = useState<'generate' | 'saved'>('generate');

  // Common-paper equal practice settings (all 8 categories equal by default, 20 min per question)
  const [selectedCategories, setSelectedCategories] = useState<string[]>(
    initialPreset?.categories && initialPreset.categories.length > 0
      ? initialPreset.categories
      : [...taxonomy.categories]
  );
  const [difficulty, setDifficulty] = useState<DifficultyLevel>('Medium');
  const [timeMinutes, setTimeMinutes] = useState<number>(20);
  const [count, setCount] = useState<number>(3);

  // Active set state
  const [generating, setGenerating] = useState(false);
  const [genElapsedSec, setGenElapsedSec] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [batch, setBatch] = useState<GeneratedQuestion[]>([]);
  const [activeIdx, setActiveIdx] = useState(0);
  const [attemptedIds, setAttemptedIds] = useState<string[]>([]);

  // Post-set automatic Draw Things reference sketches for every question in the set
  const [setSketches, setSetSketches] = useState<Record<string, DrawThingsGenerateResponse>>({});
  const [renderingSetSketches, setRenderingSetSketches] = useState(false);
  const [sketchProgress, setSketchProgress] = useState<{ current: number; total: number } | null>(null);
  const [setSketchError, setSetSketchError] = useState<string | null>(null);
  const sketchesTriggeredForSetRef = useRef<string>('');

  // Background pre-generation buffer (for 1-question sets: 0s wait for next question!)
  const [prefetchedNext, setPrefetchedNext] = useState<GeneratedQuestion | null>(null);
  const [prefetchStatus, setPrefetchStatus] = useState<'idle' | 'preparing' | 'ready'>('idle');
  const prefetchAbortRef = useRef<AbortController | null>(null);
  const prefetchPromiseRef = useRef<Promise<GeneratedQuestion | null> | null>(null);
  const prefetchTimeoutRef = useRef<number | null>(null);
  const prefetchKeyRef = useRef<string>('');
  const seenTitlesRef = useRef<string[]>([]);

  // Saved library state
  const [savedQuestions, setSavedQuestions] = useState<GeneratedQuestion[]>([]);
  const [loadingSaved, setLoadingSaved] = useState(false);
  const [savedFilterCat, setSavedFilterCat] = useState('');
  const [viewingSaved, setViewingSaved] = useState<GeneratedQuestion | null>(null);

  const allCategoriesSelected = selectedCategories.length === taxonomy.categories.length;

  const configKey = useMemo(
    () =>
      JSON.stringify({
        categories: [...selectedCategories].sort(),
        difficulty,
        timeMinutes,
        count,
      }),
    [selectedCategories, difficulty, timeMinutes, count]
  );

  const batchSignature = useMemo(() => batch.map((q) => q.id).join('|'), [batch]);
  const allQuestionsAttempted =
    batch.length > 0 && batch.every((q) => attemptedIds.includes(q.id));

  const cancelPrefetch = () => {
    if (prefetchTimeoutRef.current) {
      window.clearTimeout(prefetchTimeoutRef.current);
      prefetchTimeoutRef.current = null;
    }
    if (prefetchAbortRef.current) {
      prefetchAbortRef.current.abort();
      prefetchAbortRef.current = null;
    }
    prefetchPromiseRef.current = null;
    prefetchKeyRef.current = '';
    setPrefetchedNext(null);
    setPrefetchStatus('idle');
  };

  useEffect(() => {
    if (prefetchKeyRef.current && prefetchKeyRef.current !== configKey) {
      cancelPrefetch();
    }
  }, [configKey]);

  useEffect(() => {
    return () => {
      cancelPrefetch();
    };
  }, []);

  useEffect(() => {
    if (!generating) {
      setGenElapsedSec(0);
      return;
    }
    const id = window.setInterval(() => setGenElapsedSec((s) => s + 1), 1000);
    return () => window.clearInterval(id);
  }, [generating]);

  useEffect(() => {
    if (initialPreset?.categories && initialPreset.categories.length > 0) {
      setSelectedCategories(initialPreset.categories);
    }
  }, [initialPreset]);

  // Automatically render Draw Things visual reference sketches for EVERY question once ALL in the set are attempted!
  const renderAllSketchesForBatch = async (questionsToRender: GeneratedQuestion[]) => {
    if (questionsToRender.length === 0) return;
    // Cancel any background LLM prefetch first so Draw Things has clean 8 GB M1 unified memory
    cancelPrefetch();
    setRenderingSetSketches(true);
    setSetSketchError(null);
    setSketchProgress({ current: 0, total: questionsToRender.length });

    for (let i = 0; i < questionsToRender.length; i++) {
      const q = questionsToRender[i];
      setSketchProgress({ current: i + 1, total: questionsToRender.length });
      try {
        const res = await api.generateReferenceSketch({
          question_id: q.id,
          prompt: defaultVisualPromptForQuestion(q),
          negative_prompt: q.visual_negative_prompt || undefined,
          style_preset: defaultSketchStyleForCategory(q.category, `${q.title} ${q.scenario}`),
        });
        setSetSketches((prev) => ({ ...prev, [q.id]: res }));
      } catch (err) {
        setSetSketchError(
          err instanceof Error
            ? err.message
            : 'Draw Things could not render reference sketches. Check Draw Things HTTP server (port 7860).'
        );
        break;
      }
    }

    setRenderingSetSketches(false);
    setSketchProgress(null);
  };

  useEffect(() => {
    // Post-set Draw Things auto-rendering disabled (cloud Gemini generation active)
  }, [allQuestionsAttempted, batchSignature]);

  const loadSaved = async () => {
    setLoadingSaved(true);
    try {
      const list = await api.listGeneratedQuestions({
        saved_only: true,
        category: savedFilterCat || undefined,
      });
      setSavedQuestions(list);
    } catch {
      // keep existing
    } finally {
      setLoadingSaved(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'saved') {
      loadSaved();
    }
  }, [activeTab, savedFilterCat]);

  const toggleCategory = (cat: string) => {
    setSelectedCategories((prev) =>
      prev.includes(cat) ? (prev.length > 1 ? prev.filter((c) => c !== cat) : prev) : [...prev, cat]
    );
  };

  const selectAllEqual = () => {
    setSelectedCategories([...taxonomy.categories]);
  };

  const buildPayload = (overrideCount: number, excludeTitles: string[]) => {
    const isAllEqual = selectedCategories.length === taxonomy.categories.length;
    return {
      // Common-paper equal practice across all 8 categories (never skewed by Dnerd tag counts or campus profiles)
      mode: (isAllEqual ? 'balanced_random' : 'category') as GenerationMode,
      categories: isAllEqual ? [] : selectedCategories,
      programme_tags: [],
      active_profiles: ['general_nid_mdes'],
      difficulty,
      time_minutes: timeMinutes,
      count: overrideCount,
      random_strategy: 'completely_balanced' as const,
      exclude_titles: excludeTitles,
    };
  };

  const startBackgroundPrefetch = (excludeTitles: string[], keyForRun: string) => {
    if (!llmConnected || count !== 1) return;
    if (prefetchTimeoutRef.current) {
      window.clearTimeout(prefetchTimeoutRef.current);
      prefetchTimeoutRef.current = null;
    }

    // 2.5s debounce so user has time to read question or regenerate before background prefetch starts
    prefetchTimeoutRef.current = window.setTimeout(() => {
      prefetchTimeoutRef.current = null;
      if (!llmConnected || count !== 1) return;

      const controller = new AbortController();
      prefetchAbortRef.current = controller;
      prefetchKeyRef.current = keyForRun;
      setPrefetchedNext(null);
      setPrefetchStatus('preparing');

      const promise = api
        .generateQuestions(buildPayload(1, excludeTitles.slice(-12)), controller.signal)
        .then((res) => {
          if (controller.signal.aborted || prefetchKeyRef.current !== keyForRun) return null;
          const nextQ = res.questions[0] || null;
          if (nextQ) {
            setPrefetchedNext(nextQ);
            setPrefetchStatus('ready');
          } else {
            setPrefetchStatus('idle');
          }
          return nextQ;
        })
        .catch(() => {
          if (!controller.signal.aborted && prefetchKeyRef.current === keyForRun) {
            setPrefetchStatus('idle');
          }
          return null;
        })
        .finally(() => {
          if (prefetchAbortRef.current === controller) {
            prefetchAbortRef.current = null;
            prefetchPromiseRef.current = null;
          }
        });

      prefetchPromiseRef.current = promise;
    }, 2500);
  };

  const resetSetTracking = () => {
    setAttemptedIds([]);
    setSetSketches({});
    setSetSketchError(null);
    sketchesTriggeredForSetRef.current = '';
  };

  const handleGenerate = async (excludeTitles: string[] = []) => {
    setError(null);
    setWarnings([]);

    // 1. Instant swap if background prefetch is already ready!
    if (count === 1 && prefetchedNext && prefetchKeyRef.current === configKey) {
      const nextQ = prefetchedNext;
      setPrefetchedNext(null);
      setPrefetchStatus('idle');
      resetSetTracking();
      setBatch([nextQ]);
      setActiveIdx(0);
      const updatedSeen = [...seenTitlesRef.current, nextQ.title].slice(-12);
      seenTitlesRef.current = updatedSeen;
      startBackgroundPrefetch(updatedSeen, configKey);
      return;
    }

    // 2. Reuse in-flight matching background prefetch if one is currently preparing
    if (count === 1 && prefetchPromiseRef.current && prefetchKeyRef.current === configKey) {
      setGenerating(true);
      try {
        const awaited = await prefetchPromiseRef.current;
        if (awaited) {
          setPrefetchedNext(null);
          setPrefetchStatus('idle');
          resetSetTracking();
          setBatch([awaited]);
          setActiveIdx(0);
          const updatedSeen = [...seenTitlesRef.current, awaited.title].slice(-12);
          seenTitlesRef.current = updatedSeen;
          startBackgroundPrefetch(updatedSeen, configKey);
          return;
        }
      } catch {
        // Fall through to fresh direct generation below
      } finally {
        setGenerating(false);
      }
    }

    // 3. Fresh direct generation
    cancelPrefetch();
    setGenerating(true);
    try {
      const mergedExcludes = [...seenTitlesRef.current, ...excludeTitles].slice(-12);
      const res = await api.generateQuestions(buildPayload(count, mergedExcludes));
      resetSetTracking();
      setBatch(res.questions);
      setWarnings(res.warnings);
      setActiveIdx(0);
      const newTitles = res.questions.map((q) => q.title);
      const updatedSeen = [...seenTitlesRef.current, ...newTitles].slice(-12);
      seenTitlesRef.current = updatedSeen;

      // Start quiet background prefetch for the next question if in 1-question practice mode
      if (count === 1 && res.questions.length === 1) {
        startBackgroundPrefetch(updatedSeen, configKey);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Question generation failed.');
    } finally {
      setGenerating(false);
    }
  };

  const handleRegenerateSingle = async () => {
    const current = batch[activeIdx];
    if (!current) return;

    if (batch.length === 1 && count === 1) {
      cancelPrefetch();
      await handleGenerate([current.title]);
      return;
    }

    cancelPrefetch();
    setGenerating(true);
    setError(null);
    try {
      const res = await api.generateQuestions({
        mode: 'category',
        categories: [current.category],
        programme_tags: [],
        active_profiles: ['general_nid_mdes'],
        difficulty,
        time_minutes: timeMinutes,
        count: 1,
        random_strategy: 'completely_balanced',
        exclude_titles: [...seenTitlesRef.current, ...batch.map((q) => q.title)].slice(-12),
      });
      if (res.questions.length > 0) {
        const replacement = res.questions[0];
        const next = [...batch];
        next[activeIdx] = replacement;
        setBatch(next);
        setAttemptedIds((prev) => prev.filter((id) => id !== current.id));
        const updatedSeen = [...seenTitlesRef.current, replacement.title].slice(-12);
        seenTitlesRef.current = updatedSeen;
        if (count === 1) {
          startBackgroundPrefetch(updatedSeen, configKey);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not replace question.');
    } finally {
      setGenerating(false);
    }
  };

  const handleQuestionAttempted = (questionId: string) => {
    setAttemptedIds((prev) => (prev.includes(questionId) ? prev : [...prev, questionId]));
  };

  const handleRegenerateOneSketch = async (q: GeneratedQuestion) => {
    setSetSketchError(null);
    setRenderingSetSketches(true);
    try {
      const res = await api.generateReferenceSketch({
        question_id: q.id,
        prompt: defaultVisualPromptForQuestion(q),
        negative_prompt: q.visual_negative_prompt || undefined,
        style_preset: defaultSketchStyleForCategory(q.category, `${q.title} ${q.scenario}`),
      });
      setSetSketches((prev) => ({ ...prev, [q.id]: res }));
    } catch (err) {
      setSetSketchError(err instanceof Error ? err.message : 'Could not regenerate sketch.');
    } finally {
      setRenderingSetSketches(false);
    }
  };

  const handleDeleteSaved = async (id: string) => {
    await api.deleteGeneratedQuestion(id);
    if (viewingSaved?.id === id) setViewingSaved(null);
    loadSaved();
  };

  const activeQuestion = batch[activeIdx] || null;
  const totalSetMinutes = count * timeMinutes;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-[#E4E1DA] pb-5">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#78716C]">
            Common-Paper Equal Practice • 2025–2027 NID M.Des DAT Prelims
          </p>
          <h1 className="font-serif-editorial text-3xl font-medium text-[#18181B] mt-1">
            Generate Practice Set
          </h1>
        </div>

        <div className="inline-flex rounded-lg border border-[#D8D4CB] bg-white p-1">
          <button
            type="button"
            onClick={() => setActiveTab('generate')}
            className={`px-3.5 py-1.5 text-xs font-medium rounded-md transition-colors cursor-pointer ${
              activeTab === 'generate' ? 'bg-[#1E3A5F] text-white' : 'text-[#57534E] hover:text-[#18181B]'
            }`}
          >
            Practice Set
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('saved')}
            className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium rounded-md transition-colors cursor-pointer ${
              activeTab === 'saved' ? 'bg-[#1E3A5F] text-white' : 'text-[#57534E] hover:text-[#18181B]'
            }`}
          >
            <Bookmark className="w-3.5 h-3.5" />
            Saved Library
          </button>
        </div>
      </header>

      {activeTab === 'saved' ? (
        <div className="space-y-4">
          {viewingSaved ? (
            <div className="space-y-4">
              <button
                type="button"
                onClick={() => {
                  setViewingSaved(null);
                  loadSaved();
                }}
                className="text-xs font-medium text-[#1E3A5F] hover:underline cursor-pointer"
              >
                ← Back to Saved Questions
              </button>
              <QuestionDisplay
                question={viewingSaved}
                onSaveToggle={(u) => {
                  setViewingSaved(u);
                  loadSaved();
                }}
              />
            </div>
          ) : (
            <div className="bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="font-serif-editorial text-xl font-medium">Saved Practice Prompts</h2>
                  <p className="text-xs text-[#78716C]">
                    Available anytime, even when your local LLM server is offline.
                  </p>
                </div>
                <select
                  value={savedFilterCat}
                  onChange={(e) => setSavedFilterCat(e.target.value)}
                  className="text-xs px-3 py-1.5 rounded-lg border border-[#D8D4CB] bg-white"
                >
                  <option value="">All {taxonomy.categories.length} categories</option>
                  {taxonomy.categories.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              {loadingSaved ? (
                <div className="py-10 text-center text-xs text-[#78716C]">Loading saved questions...</div>
              ) : savedQuestions.length === 0 ? (
                <div className="py-12 text-center border border-dashed border-[#D8D4CB] rounded-lg space-y-2">
                  <p className="text-sm text-[#57534E]">No saved questions yet.</p>
                  <p className="text-xs text-[#78716C]">
                    Generate a practice set and click “Save Question” to build your offline practice deck.
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-[#ECEAE4]">
                  {savedQuestions.map((q) => (
                    <div key={q.id} className="py-3.5 flex items-start justify-between gap-4">
                      <button
                        type="button"
                        onClick={() => setViewingSaved(q)}
                        className="text-left space-y-1 flex-1 min-w-0 cursor-pointer group"
                      >
                        <div className="text-sm font-medium text-[#18181B] group-hover:text-[#1E3A5F]">
                          {q.title}
                        </div>
                        <div className="flex flex-wrap items-center gap-2 text-xs text-[#78716C]">
                          <span className="px-2 py-0.5 rounded bg-stone-100 text-stone-700">{q.category}</span>
                          <span>{q.difficulty}</span>
                          <span>{q.time_minutes} min</span>
                          <span>{q.total_marks} marks</span>
                        </div>
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteSaved(q.id)}
                        className="p-1.5 rounded text-[#78716C] hover:text-rose-700 hover:bg-rose-50 cursor-pointer"
                        title="Delete saved question"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-6">
          {/* Top Common-Paper Configuration Panel */}
          <div className="bg-white border border-[#E4E1DA] rounded-xl p-5 sm:p-6 space-y-5 shadow-xs">
            {/* Row 1: Question Count | Timer | Difficulty */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-5 items-end">
              {/* Question Count Selector */}
              <div className="md:col-span-6 lg:col-span-7 space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-[11px] font-semibold uppercase tracking-widest text-[#78716C]">
                    Number of Questions
                  </label>
                  <span className="font-mono-exam text-xs text-[#57534E]">
                    {count} × {timeMinutes}m = {totalSetMinutes}m
                  </span>
                </div>
                <div className="flex flex-wrap items-center gap-1.5">
                  {COUNT_PRESETS.map((n) => (
                    <button
                      key={n}
                      type="button"
                      onClick={() => setCount(n)}
                      className={`font-mono-exam text-xs px-3 py-1.5 rounded-lg border transition-colors cursor-pointer ${
                        count === n
                          ? 'bg-[#1E3A5F] text-white border-[#1E3A5F] font-semibold'
                          : 'bg-white text-[#44403C] border-[#D8D4CB] hover:bg-stone-50'
                      }`}
                    >
                      {n}
                    </button>
                  ))}
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={count}
                    onChange={(e) => setCount(Math.max(1, Math.min(10, Number(e.target.value) || 1)))}
                    aria-label="Custom question count"
                    className="w-16 font-mono-exam text-xs px-2.5 py-1.5 rounded-lg border border-[#D8D4CB] bg-white text-center"
                  />
                </div>
              </div>

              {/* Per-Question Timer */}
              <div className="md:col-span-3 lg:col-span-2.5">
                <label className="block text-[11px] font-semibold uppercase tracking-wider text-[#78716C] mb-1">
                  Timer / Question (min)
                </label>
                <div className="relative">
                  <Clock className="w-3.5 h-3.5 text-[#78716C] absolute left-2.5 top-2.5" />
                  <input
                    type="number"
                    min={5}
                    max={120}
                    step={5}
                    value={timeMinutes}
                    onChange={(e) =>
                      setTimeMinutes(Math.max(5, Math.min(120, Number(e.target.value) || 20)))
                    }
                    className="w-full font-mono-exam text-xs pl-8 pr-2.5 py-2 rounded-lg border border-[#D8D4CB] bg-white"
                  />
                </div>
              </div>

              {/* Difficulty */}
              <div className="md:col-span-3 lg:col-span-2.5">
                <label className="block text-[11px] font-semibold uppercase tracking-wider text-[#78716C] mb-1">
                  Difficulty Level
                </label>
                <select
                  value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value as DifficultyLevel)}
                  className="w-full text-xs px-2.5 py-2 rounded-lg border border-[#D8D4CB] bg-white font-medium"
                >
                  <option value="Random">🎲 Random (Any Level)</option>
                  <option value="Easy">Easy (Direct Observation)</option>
                  <option value="Medium">Medium (Balanced Practice)</option>
                  <option value="Hard">Hard (Strict Constraints)</option>
                </select>
              </div>
            </div>

            {/* Row 2: Category Pool (All 8 Equal by default) */}
            <div className="space-y-2 border-t border-[#E4E1DA] pt-4">
              <div className="flex items-center justify-between">
                <label className="text-[11px] font-semibold uppercase tracking-widest text-[#78716C]">
                  Categories ({allCategoriesSelected ? `All ${taxonomy.categories.length} Equal` : `${selectedCategories.length} selected`})
                </label>
                {!allCategoriesSelected && (
                  <button
                    type="button"
                    onClick={selectAllEqual}
                    className="text-[11px] font-medium text-[#1E3A5F] hover:underline cursor-pointer"
                  >
                    Reset to All {taxonomy.categories.length} Equal
                  </button>
                )}
              </div>
              <div className="flex flex-wrap gap-1.5">
                {taxonomy.categories.map((cat) => {
                  const selected = selectedCategories.includes(cat);
                  return (
                    <button
                      key={cat}
                      type="button"
                      onClick={() => toggleCategory(cat)}
                      className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border transition-colors cursor-pointer ${
                        selected
                          ? 'bg-[#1E3A5F] text-white border-[#1E3A5F] font-medium'
                          : 'bg-white text-[#44403C] border-[#D8D4CB] hover:bg-stone-50'
                      }`}
                    >
                      {selected && <Check className="w-3 h-3" />}
                      {cat}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Row 3: Action Bar & Offline Notice */}
            <div className="flex flex-wrap items-center justify-between gap-4 border-t border-[#E4E1DA] pt-4">
              <button
                type="button"
                onClick={() => handleGenerate()}
                disabled={generating}
                className="w-full sm:w-auto min-w-[280px] inline-flex items-center justify-center gap-2 py-2.5 px-6 rounded-lg bg-[#1E3A5F] text-white text-sm font-semibold hover:bg-[#162C49] disabled:opacity-60 transition-colors cursor-pointer shadow-xs"
              >
                {generating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Drafting {count === 1 ? 'Question' : `${count} Questions`} ({settings.model || 'Local LLM'})… {genElapsedSec}s
                  </>
                ) : count === 1 && prefetchedNext && prefetchKeyRef.current === configKey ? (
                  <>
                    <Zap className="w-4 h-4" />
                    Next Question (Instant)
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    Generate {count === 1 ? '1 Question' : `${count}-Question Set`} ({timeMinutes}m each)
                  </>
                )}
              </button>

              {!llmConnected && (
                <div className="text-xs text-amber-900 bg-amber-50 border border-amber-200 rounded-lg px-3.5 py-2 flex items-center gap-2">
                  <p>AI service is currently reconnecting...</p>
                </div>
              )}
            </div>
          </div>

          {/* Below: Generated Question Display & Practice Area */}
          <div className="space-y-4">
            {error && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 px-5 py-4 flex items-start gap-3 text-sm text-rose-900">
                <AlertCircle className="w-5 h-5 text-rose-700 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <div className="font-semibold">Generation could not complete</div>
                  <p className="text-xs leading-relaxed">{error}</p>
                </div>
              </div>
            )}

            {warnings.length > 0 && (
              <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 space-y-1 text-xs text-amber-950">
                {warnings.map((w, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                    <span>{w}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Background Pre-Generation Status (when count === 1) */}
            {activeQuestion && count === 1 && prefetchStatus !== 'idle' && (
              <div className="bg-white border border-[#E4E1DA] rounded-xl px-4 py-2.5 flex flex-wrap items-center justify-between gap-2 text-xs no-print">
                {prefetchStatus === 'preparing' ? (
                  <div className="flex items-center gap-2 text-[#57534E]">
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-[#1E3A5F]" />
                    <span>Pre-generating your next question in the background while you practise…</span>
                  </div>
                ) : (
                  <>
                    <div className="flex items-center gap-2 text-emerald-900 font-medium">
                      <span className="w-2 h-2 rounded-full bg-emerald-600" />
                      <span>Next question is ready in background (0s wait)</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleGenerate()}
                      className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1 rounded-lg bg-[#1E3A5F] text-white hover:bg-[#162C49] transition-colors cursor-pointer"
                    >
                      Next Question
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </>
                )}
              </div>
            )}

            {/* Set Stepper + Attempt Progress Bar (for multi-question sets) */}
            {batch.length > 1 && (
              <div className="bg-white border border-[#E4E1DA] rounded-xl p-4 space-y-3 no-print">
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                  <span className="font-semibold text-[#18181B]">
                    Practice Set Progress: {attemptedIds.length} / {batch.length} attempted
                  </span>
                  <span className="text-[#57534E]">
                    {allQuestionsAttempted
                      ? 'All questions attempted!'
                      : 'Generate sketches on command anytime, or submit attempts to auto-generate.'}
                  </span>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  {batch.map((q, i) => {
                    const done = attemptedIds.includes(q.id);
                    const isActive = i === activeIdx;
                    return (
                      <button
                        key={q.id}
                        type="button"
                        onClick={() => setActiveIdx(i)}
                        className={`inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-colors cursor-pointer ${
                          isActive
                            ? 'bg-[#1E3A5F] text-white border-[#1E3A5F]'
                            : done
                              ? 'bg-emerald-50 text-emerald-900 border-emerald-200 hover:bg-emerald-100'
                              : 'bg-[#FAF9F6] text-[#44403C] border-[#E4E1DA] hover:bg-stone-100'
                        }`}
                      >
                        {done && <CheckCircle2 className="w-3.5 h-3.5" />}
                        <span>
                          Q{i + 1}: {q.category}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Active Question Card */}
            {activeQuestion ? (
              <QuestionDisplay
                question={activeQuestion}
                questionNumber={activeIdx + 1}
                totalInBatch={batch.length}
                initialAttempted={attemptedIds.includes(activeQuestion.id)}
                autoSketch={setSketches[activeQuestion.id] || null}
                onSketchGenerated={(qId, sketch) =>
                  setSetSketches((prev) => ({ ...prev, [qId]: sketch }))
                }
                onAttemptSaved={handleQuestionAttempted}
                onRegenerate={handleRegenerateSingle}
                regenerating={generating}
                onSaveToggle={(updated) => {
                  const next = [...batch];
                  next[activeIdx] = updated;
                  setBatch(next);
                }}
              />
            ) : (
              <div className="bg-white border border-[#E4E1DA] rounded-xl p-10 text-center space-y-4">
                <div className="w-12 h-12 rounded-full bg-[#FAF9F6] border border-[#E4E1DA] flex items-center justify-center mx-auto text-[#1E3A5F]">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div className="max-w-md mx-auto space-y-1.5">
                  <h2 className="font-serif-editorial text-2xl font-medium text-[#18181B]">
                    Ready to Practise
                  </h2>
                  <p className="text-sm text-[#57534E] leading-relaxed">
                    Configure your practice session above and click Generate to begin your timed NID M.Des examination practice session.
                  </p>
                </div>
              </div>
            )}

            {/* Automatic Full-Set Visual Reference Gallery (appears once ALL questions in the set are attempted!) */}
            {allQuestionsAttempted && batch.length > 0 && (
              <section className="bg-white border border-[#1E3A5F]/25 rounded-xl p-6 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-widest text-[#1E3A5F]">
                      <ImageIcon className="w-3.5 h-3.5" />
                      Set Complete • Local Draw Things Visual Reference Gallery
                    </div>
                    <h2 className="font-serif-editorial text-2xl font-medium text-[#18181B] mt-0.5">
                      Reference Sketches for All {batch.length} Question{batch.length > 1 ? 's' : ''}
                    </h2>
                  </div>

                  <button
                    type="button"
                    onClick={() => renderAllSketchesForBatch(batch)}
                    disabled={renderingSetSketches}
                    className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-[#D8D4CB] bg-[#FAF9F6] text-[#18181B] hover:bg-stone-100 disabled:opacity-50 cursor-pointer"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${renderingSetSketches ? 'animate-spin' : ''}`} />
                    {renderingSetSketches ? 'Rendering…' : 'Regenerate All Sketches'}
                  </button>
                </div>

                {renderingSetSketches && sketchProgress && (
                  <div className="rounded-lg bg-[#F7F9FC] border border-[#1E3A5F]/20 px-4 py-3 flex items-center gap-2.5 text-xs text-[#1E3A5F]">
                    <Loader2 className="w-4 h-4 animate-spin shrink-0" />
                    <span>
                      Generating local reference sketch {sketchProgress.current} of {sketchProgress.total} via
                      Draw Things…
                    </span>
                  </div>
                )}

                {setSketchError && (
                  <div className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-xs text-amber-950">
                    {setSketchError}
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {batch.map((q, idx) => {
                    const sk = setSketches[q.id];
                    return (
                      <div
                        key={q.id}
                        className="border border-[#E4E1DA] rounded-xl overflow-hidden bg-[#FAF9F6] flex flex-col"
                      >
                        <div className="px-4 py-2.5 bg-white border-b border-[#E4E1DA] flex items-center justify-between gap-2">
                          <div className="min-w-0">
                            <span className="font-mono-exam text-[11px] font-semibold text-[#1E3A5F] mr-1.5">
                              Q{idx + 1}
                            </span>
                            <span className="text-xs font-semibold text-[#18181B] truncate">
                              {q.title}
                            </span>
                            <span className="block text-[11px] text-[#78716C]">{q.category}</span>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleRegenerateOneSketch(q)}
                            disabled={renderingSetSketches}
                            className="text-[11px] px-2 py-1 rounded border border-[#D8D4CB] bg-white text-[#44403C] hover:bg-stone-50 cursor-pointer shrink-0"
                            title="Regenerate sketch"
                          >
                            Retry
                          </button>
                        </div>

                        <div className="p-3 flex-1 flex items-center justify-center min-h-[220px] bg-white">
                          {sk ? (
                            <img
                              src={sk.image_url}
                              alt={`Reference sketch for ${q.title}`}
                              className="w-full max-h-72 object-contain rounded"
                            />
                          ) : renderingSetSketches ? (
                            <div className="text-xs text-[#78716C] flex items-center gap-2">
                              <Loader2 className="w-4 h-4 animate-spin text-[#1E3A5F]" />
                              Waiting in local Draw Things queue…
                            </div>
                          ) : (
                            <div className="text-xs text-[#78716C] text-center">
                              No sketch generated yet. Click Retry to render via Draw Things.
                            </div>
                          )}
                        </div>

                        {sk && (
                          <div className="px-3.5 py-2 border-t border-[#E4E1DA] text-[11px] font-mono-exam text-[#78716C] flex items-center justify-between">
                            <span>
                              {sk.width}×{sk.height} • {sk.steps} steps
                            </span>
                            <span>{(sk.latency_ms / 1000).toFixed(1)}s</span>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </section>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
