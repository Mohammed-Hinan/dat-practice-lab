import React, { useEffect, useRef, useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  Bookmark,
  Check,
  Clock,
  Loader2,
  RefreshCw,
  Sparkles,
  Trash2,
} from 'lucide-react';
import { api } from '../api';
import type {
  AppSettings,
  DifficultyLevel,
  GeneratedQuestion,
  GenerationMode,
  TaxonomyData,
} from '../types';
import { QuestionDisplay } from './QuestionDisplay';

interface QuestionGeneratorProps {
  taxonomy: TaxonomyData;
  settings: AppSettings;
  llmConnected: boolean;
  initialPreset?: { mode?: GenerationMode; categories?: string[]; themeId?: string | null } | null;
}

const COUNT_PRESETS = [1, 2, 3, 4, 5, 6, 8];

export const QuestionGenerator: React.FC<QuestionGeneratorProps> = ({
  taxonomy,
  settings,
  llmConnected,
  initialPreset,
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

  const seenTitlesRef = useRef<string[]>([]);

  // Saved library state
  const [savedQuestions, setSavedQuestions] = useState<GeneratedQuestion[]>([]);
  const [loadingSaved, setLoadingSaved] = useState(false);
  const [savedFilterCat, setSavedFilterCat] = useState('');
  const [viewingSaved, setViewingSaved] = useState<GeneratedQuestion | null>(null);

  const allCategoriesSelected = selectedCategories.length === taxonomy.categories.length;

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

  const resetSetTracking = () => {
    // tracking reset
  };

  const handleGenerate = async (excludeTitles: string[] = []) => {
    setError(null);
    setWarnings([]);
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
      await handleGenerate([current.title]);
      return;
    }

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
        const updatedSeen = [...seenTitlesRef.current, replacement.title].slice(-12);
        seenTitlesRef.current = updatedSeen;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not replace question.');
    } finally {
      setGenerating(false);
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
          <h1 className="font-serif-editorial text-3xl font-medium text-[#18181B]">
            Practice Studio
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


            {/* Set Stepper (for multi-question sets) */}
            {batch.length > 1 && (
              <div className="bg-white border border-[#E4E1DA] rounded-xl p-4 space-y-3 no-print">
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                  <span className="font-semibold text-[#18181B]">
                    Practice Set: Question {activeIdx + 1} of {batch.length}
                  </span>
                  <span className="text-[#57534E]">
                    Switch between questions to practise different categories.
                  </span>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  {batch.map((q, i) => {
                    const isActive = i === activeIdx;
                    return (
                      <button
                        key={q.id}
                        type="button"
                        onClick={() => setActiveIdx(i)}
                        className={`inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-colors cursor-pointer ${
                          isActive
                            ? 'bg-[#1E3A5F] text-white border-[#1E3A5F] font-semibold'
                            : 'bg-[#FAF9F6] text-[#44403C] border-[#E4E1DA] hover:bg-stone-100'
                        }`}
                      >
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


          </div>
        </div>
      )}
    </div>
  );
};
