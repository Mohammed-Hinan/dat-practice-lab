import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Clock,
  FileText,
  Loader2,
  Pause,
  Play,
  Printer,
  Trash2,
} from 'lucide-react';
import { api, formatDuration } from '../api';
import type { AppSettings, ExamPaperRecord, TaxonomyData } from '../types';
import { QuestionDisplay } from './QuestionDisplay';

interface ExamSimulatorProps {
  taxonomy: TaxonomyData;
  settings: AppSettings;
  llmConnected: boolean;
}

export const ExamSimulator: React.FC<ExamSimulatorProps> = ({
  taxonomy,
  settings,
  llmConnected,
}) => {
  // Paper configuration (default 20 min per question)
  const [title, setTitle] = useState('');
  const [numQuestions, setNumQuestions] = useState(3);
  const [totalTime, setTotalTime] = useState(60);
  const [difficulty, setDifficulty] = useState<'Easy' | 'Medium' | 'Hard' | 'Mixed'>('Mixed');
  const [categoryDistribution, setCategoryDistribution] = useState<'balanced' | 'profile_weighted' | 'custom'>('balanced');
  const [customCategories, setCustomCategories] = useState<string[]>([
    'Problem identification',
    'Product sketch',
    'Storyboard',
  ]);
  const [programmeFocus, setProgrammeFocus] = useState<string[]>([]);
  const [paperStrategy, setPaperStrategy] = useState<'random' | 'prediction_oriented'>('prediction_oriented');
  const [historicalRelevance, setHistoricalRelevance] = useState<'low' | 'medium' | 'high'>('high');

  const [generating, setGenerating] = useState(false);
  const [genElapsedSec, setGenElapsedSec] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!generating) {
      setGenElapsedSec(0);
      return;
    }
    const id = window.setInterval(() => setGenElapsedSec((s) => s + 1), 1000);
    return () => window.clearInterval(id);
  }, [generating]);
  const [papers, setPapers] = useState<ExamPaperRecord[]>([]);
  const [loadingPapers, setLoadingPapers] = useState(true);

  // Active exam runner state
  const [activePaper, setActivePaper] = useState<ExamPaperRecord | null>(null);
  const [activeQIndex, setActiveQIndex] = useState(0);
  const [examRunning, setExamRunning] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [examFinished, setExamFinished] = useState(false);
  const [submittingExam, setSubmittingExam] = useState(false);

  const loadPapers = async () => {
    setLoadingPapers(true);
    try {
      const list = await api.listExamPapers();
      setPapers(list);
    } catch {
      // ignore
    } finally {
      setLoadingPapers(false);
    }
  };

  useEffect(() => {
    loadPapers();
  }, []);

  useEffect(() => {
    if (!examRunning || !activePaper) return;
    const id = window.setInterval(() => {
      setElapsedSeconds((s) => s + 1);
    }, 1000);
    return () => window.clearInterval(id);
  }, [examRunning, activePaper]);

  const applyPreset = (qCount: number, mins: number) => {
    setNumQuestions(qCount);
    setTotalTime(mins);
  };

  const toggleCustomCat = (cat: string) => {
    setCustomCategories((prev) =>
      prev.includes(cat) ? (prev.length > 1 ? prev.filter((c) => c !== cat) : prev) : [...prev, cat]
    );
  };

  const handleGeneratePaper = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    setError(null);
    try {
      const paper = await api.generateExamPaper({
        title: title.trim() || undefined,
        num_questions: numQuestions,
        total_time_minutes: totalTime,
        difficulty,
        category_distribution: categoryDistribution,
        custom_categories: categoryDistribution === 'custom' ? customCategories : [],
        programme_focus: programmeFocus,
        active_profiles: settings.active_profiles,
        paper_strategy: paperStrategy,
        historical_relevance: historicalRelevance,
      });
      await loadPapers();
      openPaper(paper);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate mock examination paper.');
    } finally {
      setGenerating(false);
    }
  };

  const openPaper = (paper: ExamPaperRecord) => {
    setActivePaper(paper);
    setActiveQIndex(0);
    setElapsedSeconds(paper.elapsed_seconds || 0);
    setExamRunning(false);
    setExamFinished(paper.status === 'completed');
  };

  const handleStartOrPause = async () => {
    if (!activePaper) return;
    const nextRunning = !examRunning;
    setExamRunning(nextRunning);
    try {
      const updated = await api.updateExamPaperState(activePaper.id, {
        status: 'in_progress',
        elapsed_seconds: elapsedSeconds,
      });
      setActivePaper(updated);
    } catch {
      // non-fatal
    }
  };

  const handleFinishExam = async () => {
    if (!activePaper) return;
    setExamRunning(false);
    setSubmittingExam(true);
    try {
      const updated = await api.updateExamPaperState(activePaper.id, {
        status: 'completed',
        elapsed_seconds: elapsedSeconds,
      });
      setActivePaper(updated);
      setExamFinished(true);
      // Record attempts for all questions in this paper
      const perQuestionSeconds = Math.round(elapsedSeconds / Math.max(1, activePaper.questions.length));
      for (const q of activePaper.questions) {
        await api.createAttempt({
          question_id: q.id,
          question_title: q.title,
          category: q.category,
          programme_tags: q.programme_tags,
          exam_paper_id: activePaper.id,
          time_allocated_minutes: q.time_minutes,
          time_spent_seconds: perQuestionSeconds,
          self_difficulty: 'Medium',
          status: 'completed',
          notes: `Completed as part of mock paper: ${activePaper.title}`,
          rubric_revealed: true,
        });
      }
      await loadPapers();
    } finally {
      setSubmittingExam(false);
    }
  };

  const handleDeletePaper = async (id: string) => {
    await api.deleteExamPaper(id);
    if (activePaper?.id === id) setActivePaper(null);
    loadPapers();
  };

  // Active Mock Paper Runner View
  if (activePaper) {
    const totalAllocated = activePaper.total_time_minutes * 60;
    const remaining = Math.max(0, totalAllocated - elapsedSeconds);
    const isOvertime = elapsedSeconds > totalAllocated;
    const currentQ = activePaper.questions[activeQIndex];

    return (
      <div className="space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3 no-print">
          <button
            type="button"
            onClick={() => {
              setExamRunning(false);
              setActivePaper(null);
            }}
            className="text-xs font-medium text-[#1E3A5F] hover:underline cursor-pointer"
          >
            ← Back to Exam Simulator
          </button>

          <button
            type="button"
            onClick={() => window.print()}
            className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-[#D8D4CB] bg-white text-[#44403C] hover:bg-stone-50 cursor-pointer"
          >
            <Printer className="w-3.5 h-3.5" />
            Print Paper
          </button>
        </div>

        {/* Sticky Exam Control Header */}
        <div className="bg-white border border-[#E4E1DA] rounded-xl p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-widest text-[#78716C]">
                Mock Examination Paper • {activePaper.paper_strategy.replace('_', ' ')}
              </p>
              <h1 className="font-serif-editorial text-2xl font-medium text-[#18181B]">
                {activePaper.title}
              </h1>
            </div>

            <div className="flex flex-wrap items-center gap-3 no-print">
              <div className="px-3.5 py-2 rounded-lg bg-[#FAF9F6] border border-[#E4E1DA] flex items-center gap-2">
                <Clock className={`w-4 h-4 ${isOvertime ? 'text-rose-600' : 'text-[#1E3A5F]'}`} />
                <span
                  className={`font-mono-exam text-lg font-semibold tabular-nums ${
                    isOvertime ? 'text-rose-700' : 'text-[#18181B]'
                  }`}
                >
                  {isOvertime
                    ? `+${formatDuration(elapsedSeconds - totalAllocated)}`
                    : formatDuration(remaining)}
                </span>
                <span className="text-xs text-[#78716C]">/ {activePaper.total_time_minutes}m</span>
              </div>

              {!examFinished ? (
                <>
                  <button
                    type="button"
                    onClick={handleStartOrPause}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold px-4 py-2.5 rounded-lg bg-[#1E3A5F] text-white hover:bg-[#162C49] cursor-pointer"
                  >
                    {examRunning ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                    {examRunning ? 'Pause Exam' : elapsedSeconds > 0 ? 'Resume Exam' : 'Start Exam'}
                  </button>
                  <button
                    type="button"
                    onClick={handleFinishExam}
                    disabled={submittingExam}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold px-4 py-2.5 rounded-lg border border-emerald-700 text-emerald-800 bg-emerald-50 hover:bg-emerald-100 cursor-pointer disabled:opacity-50"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    {submittingExam ? 'Saving...' : 'Finish & Unlock Rubrics'}
                  </button>
                </>
              ) : (
                <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Completed • Rubrics Unlocked
                </span>
              )}
            </div>
          </div>

          {activePaper.warnings.length > 0 && (
            <div className="rounded-lg bg-amber-50 border border-amber-200 px-3.5 py-2.5 text-xs text-amber-950 flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
              <span>{activePaper.warnings.join(' ')}</span>
            </div>
          )}

          {/* Question Stepper */}
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-[#E4E1DA] no-print">
            {activePaper.questions.map((q, idx) => (
              <button
                key={q.id}
                type="button"
                onClick={() => setActiveQIndex(idx)}
                className={`px-3 py-2 rounded-lg border text-left transition-colors cursor-pointer ${
                  idx === activeQIndex
                    ? 'bg-[#1E3A5F] text-white border-[#1E3A5F]'
                    : 'bg-[#FAF9F6] text-[#27272A] border-[#E4E1DA] hover:bg-stone-100'
                }`}
              >
                <div className="font-mono-exam text-xs font-semibold">
                  Q{idx + 1} • {q.time_minutes}m
                </div>
                <div
                  className={`text-[11px] ${
                    idx === activeQIndex ? 'text-sky-100' : 'text-[#78716C]'
                  }`}
                >
                  {q.category}
                </div>
              </button>
            ))}
          </div>
        </div>

        {currentQ && (
          <QuestionDisplay
            question={currentQ}
            questionNumber={activeQIndex + 1}
            totalInBatch={activePaper.questions.length}
            examMode
            externalRubricUnlocked={examFinished}
            externalElapsedSeconds={elapsedSeconds}
          />
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <header className="border-b border-[#E4E1DA] pb-5">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#78716C]">
          Mode D — Timed Mock Examination
        </p>
        <h1 className="font-serif-editorial text-3xl font-medium text-[#18181B] mt-1">
          Exam Simulator
        </h1>
        <p className="text-sm text-[#57534E] mt-1 max-w-2xl">
          Assemble complete NID M.Des DAT Prelims papers with distinct skill demands across every question,
          configurable total timing, and post-submission evaluation rubrics.
        </p>
      </header>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        {/* Paper Builder Form */}
        <form
          onSubmit={handleGeneratePaper}
          className="xl:col-span-6 bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-5"
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="font-serif-editorial text-xl font-medium">Configure Practice Paper</h2>
            <div className="flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={() => applyPreset(1, 20)}
                className="text-[11px] px-2.5 py-1 rounded border border-[#D8D4CB] hover:bg-[#FAF9F6] cursor-pointer"
              >
                1Q • 20m
              </button>
              <button
                type="button"
                onClick={() => applyPreset(3, 60)}
                className="text-[11px] px-2.5 py-1 rounded border border-[#D8D4CB] hover:bg-[#FAF9F6] cursor-pointer"
              >
                3Q • 60m
              </button>
              <button
                type="button"
                onClick={() => applyPreset(5, 100)}
                className="text-[11px] px-2.5 py-1 rounded border border-[#D8D4CB] hover:bg-[#FAF9F6] cursor-pointer"
              >
                5Q • 100m
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-[#44403C] mb-1">
              Paper Title (optional)
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Sunday Full-Length DAT Prelims Mock #1"
              className="w-full text-sm px-3 py-2 rounded-lg border border-[#D8D4CB] bg-white"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-[#44403C] mb-1">Questions</label>
              <input
                type="number"
                min={1}
                max={10}
                value={numQuestions}
                onChange={(e) => {
                  const n = Math.max(1, Math.min(10, Number(e.target.value) || 1));
                  setNumQuestions(n);
                  setTotalTime(n * 20);
                }}
                className="w-full font-mono-exam text-sm px-3 py-2 rounded-lg border border-[#D8D4CB]"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-[#44403C] mb-1">Total Time (min)</label>
              <input
                type="number"
                min={15}
                max={300}
                step={5}
                value={totalTime}
                onChange={(e) => setTotalTime(Math.max(15, Math.min(300, Number(e.target.value) || 30)))}
                className="w-full font-mono-exam text-sm px-3 py-2 rounded-lg border border-[#D8D4CB]"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-[#44403C] mb-1">Difficulty</label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value as 'Easy' | 'Medium' | 'Hard' | 'Mixed')}
                className="w-full text-sm px-3 py-2 rounded-lg border border-[#D8D4CB] bg-white"
              >
                <option value="Mixed">Mixed (Exam-like)</option>
                <option value="Easy">Easy</option>
                <option value="Medium">Medium</option>
                <option value="Hard">Hard</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-[#44403C] mb-1">Paper Strategy</label>
              <select
                value={paperStrategy}
                onChange={(e) => setPaperStrategy(e.target.value as 'random' | 'prediction_oriented')}
                className="w-full text-sm px-3 py-2 rounded-lg border border-[#D8D4CB] bg-white"
              >
                <option value="prediction_oriented">Prediction & Priority Oriented</option>
                <option value="random">Completely Random & Diverse</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-[#44403C] mb-1">Historical Relevance</label>
              <select
                value={historicalRelevance}
                onChange={(e) => setHistoricalRelevance(e.target.value as 'low' | 'medium' | 'high')}
                className="w-full text-sm px-3 py-2 rounded-lg border border-[#D8D4CB] bg-white"
              >
                <option value="high">High (ground in imported patterns)</option>
                <option value="medium">Medium</option>
                <option value="low">Low (exploratory / unexpected)</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-medium text-[#44403C]">Category Distribution</label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: 'balanced', label: 'Balanced' },
                { id: 'profile_weighted', label: 'Profile Weighted' },
                { id: 'custom', label: 'Custom Pick' },
              ].map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setCategoryDistribution(opt.id as 'balanced' | 'profile_weighted' | 'custom')}
                  className={`py-2 px-3 rounded-lg border text-xs font-medium cursor-pointer ${
                    categoryDistribution === opt.id
                      ? 'bg-[#1E3A5F] text-white border-[#1E3A5F]'
                      : 'bg-white text-[#44403C] border-[#D8D4CB]'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            {categoryDistribution === 'custom' && (
              <div className="flex flex-wrap gap-1.5 pt-1">
                {taxonomy.categories.map((c) => {
                  const active = customCategories.includes(c);
                  return (
                    <button
                      key={c}
                      type="button"
                      onClick={() => toggleCustomCat(c)}
                      className={`text-xs px-2.5 py-1 rounded border cursor-pointer ${
                        active
                          ? 'bg-[#1E3A5F]/10 border-[#1E3A5F] text-[#1E3A5F] font-medium'
                          : 'bg-white border-[#D8D4CB] text-[#57534E]'
                      }`}
                    >
                      {c}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-[#44403C]">
              Programme Focus (optional)
            </label>
            <div className="max-h-32 overflow-y-auto p-2.5 rounded-lg border border-[#E4E1DA] bg-[#FAF9F6] flex flex-wrap gap-1.5">
              {taxonomy.programme_tags.map((p) => {
                const active = programmeFocus.includes(p);
                return (
                  <button
                    key={p}
                    type="button"
                    onClick={() =>
                      setProgrammeFocus((prev) =>
                        prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]
                      )
                    }
                    className={`text-[11px] px-2 py-1 rounded border cursor-pointer ${
                      active
                        ? 'bg-[#1E3A5F] text-white border-[#1E3A5F]'
                        : 'bg-white text-[#44403C] border-[#D8D4CB]'
                    }`}
                  >
                    {p}
                  </button>
                );
              })}
            </div>
          </div>

          {error && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-3.5 py-3 text-xs text-rose-900 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-rose-700 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={generating}
            className="w-full inline-flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-[#1E3A5F] text-white text-sm font-semibold hover:bg-[#162C49] disabled:opacity-60 cursor-pointer"
          >
            {generating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Assembling {numQuestions}-Question Paper ({settings.model || 'Local LLM'})... {genElapsedSec}s
              </>
            ) : (
              <>
                <FileText className="w-4 h-4" />
                Generate Mock Exam Paper
              </>
            )}
          </button>

          {!llmConnected && (
            <p className="text-xs text-amber-800">
              Local LLM is currently offline. Connect Ollama or LM Studio to generate new papers; existing
              papers on the right can still be opened and practised offline.
            </p>
          )}
        </form>

        {/* Saved / Past Mock Papers List */}
        <section className="xl:col-span-6 bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-4">
          <div>
            <h2 className="font-serif-editorial text-xl font-medium">Saved Mock Papers</h2>
            <p className="text-xs text-[#78716C] mt-0.5">
              Stored locally in SQLite. Open any paper to run a timed simulation offline.
            </p>
          </div>

          {loadingPapers ? (
            <div className="py-10 text-center text-xs text-[#78716C]">Loading papers...</div>
          ) : papers.length === 0 ? (
            <div className="py-12 text-center border border-dashed border-[#D8D4CB] rounded-lg space-y-1.5">
              <p className="text-sm text-[#57534E]">No mock papers generated yet.</p>
              <p className="text-xs text-[#78716C]">
                Configure a 30-minute single prompt or 90–150 minute mock paper on the left.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-[#ECEAE4]">
              {papers.map((paper) => (
                <div key={paper.id} className="py-4 flex items-start justify-between gap-4">
                  <div className="space-y-1 min-w-0">
                    <button
                      type="button"
                      onClick={() => openPaper(paper)}
                      className="text-left text-sm font-semibold text-[#18181B] hover:text-[#1E3A5F] cursor-pointer"
                    >
                      {paper.title}
                    </button>
                    <div className="flex flex-wrap items-center gap-2 text-xs text-[#78716C]">
                      <span className="font-mono-exam">{paper.questions.length} Qs</span>
                      <span>•</span>
                      <span className="font-mono-exam">{paper.total_time_minutes} min</span>
                      <span>•</span>
                      <span>{paper.difficulty}</span>
                      <span>•</span>
                      <span
                        className={`px-1.5 py-0.5 rounded text-[11px] font-medium ${
                          paper.status === 'completed'
                            ? 'bg-emerald-50 text-emerald-800'
                            : paper.status === 'in_progress'
                              ? 'bg-amber-50 text-amber-800'
                              : 'bg-stone-100 text-stone-700'
                        }`}
                      >
                        {paper.status.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      type="button"
                      onClick={() => openPaper(paper)}
                      className="text-xs font-medium px-3 py-1.5 rounded-lg border border-[#D8D4CB] text-[#1E3A5F] hover:bg-[#1E3A5F]/5 cursor-pointer"
                    >
                      Open
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDeletePaper(paper.id)}
                      className="p-1.5 rounded text-[#78716C] hover:text-rose-700 hover:bg-rose-50 cursor-pointer"
                      title="Delete paper"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
};
