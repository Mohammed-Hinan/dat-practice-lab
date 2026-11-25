import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  Award,
  BookOpen,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  Compass,
  FileText,
  HelpCircle,
  Layers,
  Loader2,
  Pause,
  PenTool,
  Play,
  Printer,
  ShieldAlert,
  Sparkles,
  Target,
  Trash2,
  Zap,
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
  // Paper configuration (defaults to authentic 5-hour CAT test preset)
  const [title, setTitle] = useState('');
  const [numQuestions, setNumQuestions] = useState(8);
  const [totalTime, setTotalTime] = useState(300);
  const [difficulty, setDifficulty] = useState<'Easy' | 'Medium' | 'Hard' | 'Mixed'>('Mixed');
  const [categoryDistribution, setCategoryDistribution] = useState<'balanced' | 'profile_weighted' | 'custom'>('balanced');
  const [customCategories, setCustomCategories] = useState<string[]>([
    'Problem identification',
    'Storyboard',
    'Drawing',
    'Creativity',
    'Composition',
    'Logos, Symbols & Signs',
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
  const [checkedSubtasks, setCheckedSubtasks] = useState<Record<string, boolean>>({});

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
        active_profiles: programmeFocus.length > 0 ? settings.active_profiles : ['general_nid_mdes'],
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
    setCheckedSubtasks({});
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

  const toggleSubtaskCheck = (subtaskId: string) => {
    setCheckedSubtasks((prev) => ({
      ...prev,
      [subtaskId]: !prev[subtaskId],
    }));
  };

  // Find featured curated official papers
  const official5hrPaper = papers.find((p) => p.id === 'cat-5hr-official-exam-001');
  const official3hrPaper = papers.find((p) => p.id === 'cat-3hr-official-exam-002');

  // ============================================================================
  // Active Mock Paper Runner View
  // ============================================================================
  if (activePaper) {
    const totalAllocated = activePaper.total_time_minutes * 60;
    const remaining = Math.max(0, totalAllocated - elapsedSeconds);
    const isOvertime = elapsedSeconds > totalAllocated;
    const currentQ = activePaper.questions[activeQIndex];
    const totalPaperMarks = activePaper.questions.reduce((sum, q) => sum + (q.total_marks || 0), 0);

    return (
      <div className="space-y-6">
        {/* Navigation Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 no-print">
          <button
            type="button"
            onClick={() => {
              setExamRunning(false);
              setActivePaper(null);
            }}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#1E3A5F] hover:underline cursor-pointer"
          >
            <ChevronLeft className="w-4 h-4" />
            Back to Exam Simulator
          </button>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => window.print()}
              className="inline-flex items-center gap-1.5 text-xs font-medium px-3.5 py-1.5 rounded-lg border border-[#D8D4CB] bg-white text-[#44403C] hover:bg-stone-50 cursor-pointer shadow-xs"
            >
              <Printer className="w-3.5 h-3.5" />
              Print Full Paper (All Questions)
            </button>
          </div>
        </div>

        {/* Sticky Exam Control Header */}
        <div className="bg-white border border-[#E4E1DA] rounded-xl p-5 shadow-xs space-y-4 no-print">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded bg-[#1E3A5F]/10 text-[#1E3A5F]">
                  Authentic CAT / DAT Format
                </span>
                <span className="text-xs text-[#78716C]">
                  {activePaper.questions.length} Questions • {totalPaperMarks} Marks Total
                </span>
              </div>
              <h1 className="font-serif-editorial text-2xl font-medium text-[#18181B] mt-1">
                {activePaper.title}
              </h1>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              {/* Countdown Clock Display */}
              <div className="px-4 py-2.5 rounded-lg bg-[#FAF9F6] border border-[#E4E1DA] flex items-center gap-2.5 shadow-xs">
                <Clock className={`w-5 h-5 ${isOvertime ? 'text-rose-600 animate-pulse' : 'text-[#1E3A5F]'}`} />
                <div className="text-right">
                  <div
                    className={`font-mono-exam text-xl font-bold tabular-nums tracking-tight ${
                      isOvertime ? 'text-rose-700' : 'text-[#18181B]'
                    }`}
                  >
                    {isOvertime
                      ? `+${formatDuration(elapsedSeconds - totalAllocated)}`
                      : formatDuration(remaining)}
                  </div>
                  <div className="text-[10px] font-medium text-[#78716C] uppercase tracking-wider">
                    {isOvertime ? 'Overtime' : `of ${activePaper.total_time_minutes}m limit`}
                  </div>
                </div>
              </div>

              {!examFinished ? (
                <>
                  <button
                    type="button"
                    onClick={handleStartOrPause}
                    className={`inline-flex items-center gap-2 text-xs font-semibold px-4 py-2.5 rounded-lg cursor-pointer transition-colors shadow-xs ${
                      examRunning
                        ? 'bg-amber-600 text-white hover:bg-amber-700'
                        : 'bg-[#1E3A5F] text-white hover:bg-[#162C49]'
                    }`}
                  >
                    {examRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    {examRunning ? 'Pause Exam' : elapsedSeconds > 0 ? 'Resume Exam' : 'Start Exam'}
                  </button>
                  <button
                    type="button"
                    onClick={handleFinishExam}
                    disabled={submittingExam}
                    className="inline-flex items-center gap-2 text-xs font-semibold px-4 py-2.5 rounded-lg border border-emerald-700 text-emerald-800 bg-emerald-50 hover:bg-emerald-100 cursor-pointer disabled:opacity-50 transition-colors shadow-xs"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    {submittingExam ? 'Saving Attempt...' : 'Finish & Reveal Rubrics'}
                  </button>
                </>
              ) : (
                <span className="inline-flex items-center gap-2 text-xs font-semibold px-4 py-2.5 rounded-lg bg-emerald-50 border border-emerald-300 text-emerald-800 shadow-xs">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  Examination Completed • Rubrics Unlocked
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

          {/* Question Stepper Strip */}
          <div className="pt-2 border-t border-[#E4E1DA]">
            <div className="flex items-center justify-between text-xs text-[#78716C] mb-2 font-medium">
              <span>Paper Questions Navigation</span>
              <span>
                Active: Question {activeQIndex + 1} of {activePaper.questions.length} (
                {currentQ?.time_minutes || 0} min suggested • {currentQ?.total_marks || 0} marks)
              </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
              {activePaper.questions.map((q, idx) => {
                const isActive = idx === activeQIndex;
                const isAllSubtasksChecked = q.subquestions.every(
                  (_, sIdx) => checkedSubtasks[`${q.id}_${sIdx}`]
                );

                return (
                  <button
                    key={q.id}
                    type="button"
                    onClick={() => setActiveQIndex(idx)}
                    className={`p-2.5 rounded-lg border text-left transition-all cursor-pointer relative ${
                      isActive
                        ? 'bg-[#1E3A5F] text-white border-[#1E3A5F] shadow-sm ring-2 ring-[#1E3A5F]/20'
                        : isAllSubtasksChecked
                          ? 'bg-emerald-50/60 text-[#18181B] border-emerald-300 hover:bg-emerald-50'
                          : 'bg-[#FAF9F6] text-[#27272A] border-[#E4E1DA] hover:bg-stone-100'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <span className="font-mono-exam text-xs font-bold">Q{idx + 1}</span>
                      <span
                        className={`text-[10px] font-mono-exam font-semibold px-1 py-0.2 rounded ${
                          isActive
                            ? 'bg-white/20 text-white'
                            : 'bg-stone-200/80 text-[#57534E]'
                        }`}
                      >
                        {q.total_marks}m
                      </span>
                    </div>
                    <div
                      className={`text-[11px] truncate font-medium ${
                        isActive ? 'text-sky-100' : 'text-[#57534E]'
                      }`}
                      title={q.title}
                    >
                      {q.title}
                    </div>
                    <div
                      className={`text-[10px] ${
                        isActive ? 'text-sky-200' : 'text-[#78716C]'
                      }`}
                    >
                      {q.time_minutes}m allocated
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Current Question Runner View with Checkable Deliverables */}
        {currentQ && (
          <div className="space-y-4 no-print">
            {/* Interactive Drawing Deliverables Checklist Bar */}
            <div className="bg-[#FAF9F6] border border-[#E4E1DA] rounded-xl p-4 shadow-xs space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#18181B] flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-[#1E3A5F]" />
                  Paper Sketch Checklist • Question {activeQIndex + 1} Deliverables ({currentQ.total_marks} Marks)
                </h3>
                <span className="text-xs text-[#78716C]">
                  Check off items as you finish sketching them on your A4 sheet
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
                {currentQ.subquestions.map((sq, sIdx) => {
                  const checkKey = `${currentQ.id}_${sIdx}`;
                  const isChecked = !!checkedSubtasks[checkKey];

                  return (
                    <button
                      key={checkKey}
                      type="button"
                      onClick={() => toggleSubtaskCheck(checkKey)}
                      className={`p-3 rounded-lg border text-left flex items-start gap-3 transition-colors cursor-pointer ${
                        isChecked
                          ? 'bg-emerald-50 border-emerald-300 text-emerald-950'
                          : 'bg-white border-[#E4E1DA] text-[#27272A] hover:bg-stone-50'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => {}} // handled by button click
                        className="mt-0.5 rounded border-stone-300 text-emerald-600 focus:ring-emerald-500 cursor-pointer"
                      />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between gap-1 mb-0.5">
                          <span className="font-mono-exam text-xs font-bold uppercase tracking-wide">
                            Part {sq.label}
                          </span>
                          <span className="font-mono-exam text-[11px] font-semibold text-[#57534E]">
                            {sq.marks} marks
                          </span>
                        </div>
                        <p
                          className={`text-xs leading-relaxed line-clamp-3 ${
                            isChecked ? 'line-through text-emerald-800/80' : 'text-[#44403C]'
                          }`}
                        >
                          {sq.instruction}
                        </p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Question Display Component */}
            <QuestionDisplay
              question={currentQ}
              questionNumber={activeQIndex + 1}
              totalInBatch={activePaper.questions.length}
              examMode
              externalRubricUnlocked={examFinished}
              externalElapsedSeconds={elapsedSeconds}
            />

            {/* Question Navigation Stepper Footer */}
            <div className="bg-white border border-[#E4E1DA] rounded-xl p-4 flex items-center justify-between gap-4">
              <button
                type="button"
                disabled={activeQIndex === 0}
                onClick={() => setActiveQIndex((i) => Math.max(0, i - 1))}
                className="inline-flex items-center gap-1.5 text-xs font-semibold px-4 py-2 rounded-lg border border-[#D8D4CB] text-[#18181B] hover:bg-stone-50 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4" />
                Previous Question (Q{activeQIndex})
              </button>

              <span className="text-xs font-medium text-[#78716C]">
                Question {activeQIndex + 1} of {activePaper.questions.length}
              </span>

              <button
                type="button"
                disabled={activeQIndex >= activePaper.questions.length - 1}
                onClick={() => setActiveQIndex((i) => Math.min(activePaper.questions.length - 1, i + 1))}
                className="inline-flex items-center gap-1.5 text-xs font-semibold px-4 py-2 rounded-lg bg-[#1E3A5F] text-white hover:bg-[#162C49] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              >
                Next Question (Q{activeQIndex + 2})
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* ==================================================================== */}
        {/* Printable Examination Paper View (Hidden on screen, Active in Print) */}
        {/* ==================================================================== */}
        <div className="hidden print:block text-black bg-white space-y-6 p-4">
          <div className="border-b-2 border-black pb-4 text-center space-y-1">
            <h1 className="text-xl font-bold uppercase tracking-wider">
              NATIONAL INSTITUTE OF DESIGN / CEED — CREATIVE ABILITY TEST (CAT)
            </h1>
            <h2 className="text-lg font-semibold">{activePaper.title}</h2>
            <div className="flex justify-between text-xs font-mono pt-2">
              <span>Total Questions: {activePaper.questions.length}</span>
              <span>Total Duration: {activePaper.total_time_minutes} Minutes ({activePaper.total_time_minutes / 60} Hours)</span>
              <span>Maximum Marks: {totalPaperMarks}</span>
            </div>
          </div>

          <div className="text-xs border border-black p-3 space-y-1 bg-stone-50">
            <p className="font-bold uppercase tracking-wider">Instructions to Candidates:</p>
            <ul className="list-disc pl-5 space-y-0.5">
              <li>Read each question carefully before beginning your drawings.</li>
              <li>Maintain clarity, proportions, perspective convergence, and functional ergonomics in all sketches.</li>
              <li>Write legible, concise English annotations and leader lines where requested.</li>
              <li>Strictly adhere to the allocated time for each question.</li>
            </ul>
          </div>

          <div className="space-y-8 divide-y divide-black pt-4">
            {activePaper.questions.map((q, idx) => (
              <div key={q.id} className="pt-6 space-y-3 page-break-inside-avoid">
                <div className="flex justify-between items-baseline border-b border-stone-400 pb-1">
                  <h3 className="text-base font-bold">
                    Question {idx + 1}: {q.title}
                  </h3>
                  <span className="font-mono font-bold text-sm">
                    [{q.total_marks} Marks • {q.time_minutes} min]
                  </span>
                </div>

                <div className="space-y-2 text-sm leading-relaxed">
                  <p>
                    <span className="font-semibold">Context / Scenario: </span>
                    {q.scenario}
                  </p>

                  <div className="space-y-2 pt-2">
                    <p className="font-semibold">Tasks & Questions:</p>
                    {q.subquestions.map((sq) => (
                      <div key={sq.label} className="pl-4 flex items-start justify-between gap-4">
                        <p>
                          <span className="font-bold">({sq.label}) </span>
                          {sq.instruction}
                        </p>
                        <span className="font-mono font-semibold shrink-0">[{sq.marks} marks]</span>
                      </div>
                    ))}
                  </div>

                  {q.constraints.length > 0 && (
                    <div className="pt-2 text-xs">
                      <span className="font-semibold">Specific Constraints: </span>
                      {q.constraints.join(' • ')}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // ============================================================================
  // Exam Simulator Dashboard View (Preloaded Papers + Custom Builder)
  // ============================================================================
  return (
    <div className="space-y-8">
      {/* Page Header */}
      <header className="border-b border-[#E4E1DA] pb-5">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#78716C]">
          Mode D — Full-Length Timed Examination
        </p>
        <h1 className="font-serif-editorial text-3xl font-medium text-[#18181B] mt-1">
          Exam Simulator
        </h1>
        <p className="text-sm text-[#57534E] mt-1 max-w-3xl">
          Experience authentic 5-hour and 3-hour NID DAT & CEED Creative Ability Tests (CAT) under official time pressure,
          with subquestion checklists, diverse creative domains, and comprehensive evaluation rubrics.
        </p>
      </header>

      {/* ==================================================================== */}
      {/* Featured Authentic Mock Papers (Instant Launch)                      */}
      {/* ==================================================================== */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold uppercase tracking-widest text-[#78716C] flex items-center gap-1.5">
            <Award className="w-4 h-4 text-amber-600" />
            Official Format Curated Mock Papers (Instant Launch)
          </h2>
          <span className="text-xs text-[#78716C]">Pre-loaded with official rubrics • No LLM generation wait</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Card 1: 5-Hour Full CAT Mock Exam */}
          <div className="bg-gradient-to-br from-white to-[#FAF9F6] border-2 border-[#1E3A5F]/30 hover:border-[#1E3A5F] rounded-xl p-5 shadow-xs transition-all space-y-4 flex flex-col justify-between">
            <div className="space-y-2.5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider bg-amber-100 text-amber-900 border border-amber-200">
                  <Sparkles className="w-3 h-3 text-amber-700" />
                  Official NID / CEED Format
                </span>
                <span className="font-mono-exam text-xs font-bold text-[#1E3A5F] px-2 py-0.5 rounded bg-[#1E3A5F]/10">
                  5 Hours • 300 Min • 100 Marks
                </span>
              </div>

              <h3 className="font-serif-editorial text-xl font-bold text-[#18181B]">
                Official NID / CEED Creative Ability Test (CAT) — 5-Hour Full Drawing Examination
              </h3>

              <p className="text-xs text-[#57534E] leading-relaxed">
                The complete 8-question drawing examination covering:
                <strong className="text-[#18181B]"> (1)</strong> Spatial Interior & Product Redesign (Elderly/Child),
                <strong className="text-[#18181B]"> (2)</strong> 3-Step Process (Mango Pickle / Shell Jewellery),
                <strong className="text-[#18181B]"> (3)</strong> Cognitive Route Map (Home to TCS iON Centre),
                <strong className="text-[#18181B]"> (4)</strong> Dynamic Sports Figures (Cricket Playground),
                <strong className="text-[#18181B]"> (5)</strong> Balcony High-Angle Perspective,
                <strong className="text-[#18181B]"> (6)</strong> 16 Colored Cubes Modular Sculpture,
                <strong className="text-[#18181B]"> (7)</strong> Public Social Scenario (Smoking Observation), and
                <strong className="text-[#18181B]"> (8)</strong> Anti-Bullying Campaign Poster with Design Rationale.
              </p>
            </div>

            <div className="pt-2 flex items-center justify-between gap-3 border-t border-[#E4E1DA]">
              <div className="flex items-center gap-2 text-xs text-[#78716C]">
                <Layers className="w-3.5 h-3.5" />
                <span>8 Full Questions</span>
                <span>•</span>
                <span>100 Marks</span>
              </div>

              {official5hrPaper ? (
                <button
                  type="button"
                  onClick={() => openPaper(official5hrPaper)}
                  className="inline-flex items-center gap-2 text-xs font-bold px-4 py-2 rounded-lg bg-[#1E3A5F] text-white hover:bg-[#162C49] transition-colors cursor-pointer shadow-xs"
                >
                  <Play className="w-3.5 h-3.5" />
                  Launch 5-Hour CAT Exam
                </button>
              ) : (
                <span className="text-xs text-[#78716C]">Loading...</span>
              )}
            </div>
          </div>

          {/* Card 2: 3-Hour NID M.Des Paper */}
          <div className="bg-gradient-to-br from-white to-[#FAF9F6] border border-[#E4E1DA] hover:border-[#1E3A5F]/60 rounded-xl p-5 shadow-xs transition-all space-y-4 flex flex-col justify-between">
            <div className="space-y-2.5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider bg-stone-100 text-stone-800 border border-stone-200">
                  <BookOpen className="w-3 h-3 text-stone-600" />
                  Standard M.Des DAT Format
                </span>
                <span className="font-mono-exam text-xs font-bold text-[#1E3A5F] px-2 py-0.5 rounded bg-[#1E3A5F]/10">
                  3 Hours • 180 Min • 100 Marks
                </span>
              </div>

              <h3 className="font-serif-editorial text-xl font-bold text-[#18181B]">
                NID M.Des Design Aptitude Test (DAT) — 3-Hour Common Creative Paper
              </h3>

              <p className="text-xs text-[#57534E] leading-relaxed">
                A focused 5-question comprehensive simulation testing:
                <strong className="text-[#18181B]"> (1)</strong> Street Vendor Produce Thela Redesign,
                <strong className="text-[#18181B]"> (2)</strong> 4-Frame Wordless Twist Storyboard (Monsoon Railway Station),
                <strong className="text-[#18181B]"> (3)</strong> First-Person Electric City Bus Interior Perspective,
                <strong className="text-[#18181B]"> (4)</strong> Dual-Metaphor Domestic Water Conservation Poster, and
                <strong className="text-[#18181B]"> (5)</strong> Tactile Upcycling Invention from Discarded Coconut Shells.
              </p>
            </div>

            <div className="pt-2 flex items-center justify-between gap-3 border-t border-[#E4E1DA]">
              <div className="flex items-center gap-2 text-xs text-[#78716C]">
                <Layers className="w-3.5 h-3.5" />
                <span>5 Full Questions</span>
                <span>•</span>
                <span>100 Marks</span>
              </div>

              {official3hrPaper ? (
                <button
                  type="button"
                  onClick={() => openPaper(official3hrPaper)}
                  className="inline-flex items-center gap-2 text-xs font-bold px-4 py-2 rounded-lg bg-[#18181B] text-white hover:bg-stone-800 transition-colors cursor-pointer shadow-xs"
                >
                  <Play className="w-3.5 h-3.5" />
                  Launch 3-Hour NID Paper
                </button>
              ) : (
                <span className="text-xs text-[#78716C]">Loading...</span>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ==================================================================== */}
      {/* Paper Configurator & Saved Papers Grid                               */}
      {/* ==================================================================== */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        {/* Custom Paper Builder Form */}
        <form
          onSubmit={handleGeneratePaper}
          className="xl:col-span-6 bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-5 shadow-xs"
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="font-serif-editorial text-xl font-medium text-[#18181B]">
                Custom Exam Generator
              </h2>
              <p className="text-xs text-[#78716C]">Generate new mock papers with targeted timing & balance</p>
            </div>
            <div className="flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={() => applyPreset(8, 300)}
                className={`text-[11px] px-2.5 py-1 rounded border font-semibold cursor-pointer transition-colors ${
                  numQuestions === 8 && totalTime === 300
                    ? 'bg-[#1E3A5F] text-white border-[#1E3A5F]'
                    : 'border-[#D8D4CB] hover:bg-[#FAF9F6] text-[#44403C]'
                }`}
              >
                5h CAT (8Q • 300m)
              </button>
              <button
                type="button"
                onClick={() => applyPreset(5, 180)}
                className={`text-[11px] px-2.5 py-1 rounded border font-semibold cursor-pointer transition-colors ${
                  numQuestions === 5 && totalTime === 180
                    ? 'bg-[#1E3A5F] text-white border-[#1E3A5F]'
                    : 'border-[#D8D4CB] hover:bg-[#FAF9F6] text-[#44403C]'
                }`}
              >
                3h NID (5Q • 180m)
              </button>
              <button
                type="button"
                onClick={() => applyPreset(4, 120)}
                className={`text-[11px] px-2.5 py-1 rounded border font-semibold cursor-pointer transition-colors ${
                  numQuestions === 4 && totalTime === 120
                    ? 'bg-[#1E3A5F] text-white border-[#1E3A5F]'
                    : 'border-[#D8D4CB] hover:bg-[#FAF9F6] text-[#44403C]'
                }`}
              >
                2h Sprint (4Q • 120m)
              </button>
              <button
                type="button"
                onClick={() => applyPreset(3, 60)}
                className={`text-[11px] px-2.5 py-1 rounded border font-semibold cursor-pointer transition-colors ${
                  numQuestions === 3 && totalTime === 60
                    ? 'bg-[#1E3A5F] text-white border-[#1E3A5F]'
                    : 'border-[#D8D4CB] hover:bg-[#FAF9F6] text-[#44403C]'
                }`}
              >
                1h Quick Drill (3Q • 60m)
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-[#44403C] mb-1">
              Custom Paper Title (optional)
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Sunday 5-Hour Full CAT Drawing Mock #2"
              className="w-full text-sm px-3.5 py-2 rounded-lg border border-[#D8D4CB] bg-white focus:outline-none focus:ring-1 focus:ring-[#1E3A5F]"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-[#44403C] mb-1">Questions (1–12)</label>
              <input
                type="number"
                min={1}
                max={12}
                value={numQuestions}
                onChange={(e) => {
                  const n = Math.max(1, Math.min(12, Number(e.target.value) || 1));
                  setNumQuestions(n);
                  setTotalTime(n * 35);
                }}
                className="w-full font-mono-exam text-sm px-3 py-2 rounded-lg border border-[#D8D4CB]"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-[#44403C] mb-1">Total Time (min)</label>
              <input
                type="number"
                min={15}
                max={360}
                step={5}
                value={totalTime}
                onChange={(e) => setTotalTime(Math.max(15, Math.min(360, Number(e.target.value) || 30)))}
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
                <option value="high">High (ground in authentic patterns)</option>
                <option value="medium">Medium</option>
                <option value="low">Low (exploratory / unexpected)</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-medium text-[#44403C]">Category Distribution</label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: 'balanced', label: 'Balanced (All 8)' },
                { id: 'profile_weighted', label: 'Profile Weighted' },
                { id: 'custom', label: 'Custom Pick' },
              ].map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setCategoryDistribution(opt.id as 'balanced' | 'profile_weighted' | 'custom')}
                  className={`py-2 px-3 rounded-lg border text-xs font-medium cursor-pointer transition-colors ${
                    categoryDistribution === opt.id
                      ? 'bg-[#1E3A5F] text-white border-[#1E3A5F]'
                      : 'bg-white text-[#44403C] border-[#D8D4CB] hover:bg-stone-50'
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
                      className={`text-xs px-2.5 py-1 rounded border cursor-pointer transition-colors ${
                        active
                          ? 'bg-[#1E3A5F]/10 border-[#1E3A5F] text-[#1E3A5F] font-semibold'
                          : 'bg-white border-[#D8D4CB] text-[#57534E] hover:bg-stone-50'
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
            <div className="max-h-28 overflow-y-auto p-2.5 rounded-lg border border-[#E4E1DA] bg-[#FAF9F6] flex flex-wrap gap-1.5">
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
                    className={`text-[11px] px-2 py-1 rounded border cursor-pointer transition-colors ${
                      active
                        ? 'bg-[#1E3A5F] text-white border-[#1E3A5F]'
                        : 'bg-white text-[#44403C] border-[#D8D4CB] hover:bg-stone-50'
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
            className="w-full inline-flex items-center justify-center gap-2 py-3 px-4 rounded-lg bg-[#1E3A5F] text-white text-sm font-semibold hover:bg-[#162C49] disabled:opacity-60 cursor-pointer shadow-xs transition-colors"
          >
            {generating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Assembling {numQuestions}-Question Mock Paper ({settings.model || 'Local LLM'})... {genElapsedSec}s
              </>
            ) : (
              <>
                <FileText className="w-4 h-4" />
                Generate New {numQuestions}-Question Mock Paper ({totalTime} min)
              </>
            )}
          </button>

          {!llmConnected && (
            <p className="text-xs text-amber-800">
              Note: Local LLM is currently offline. You can immediately launch the pre-loaded 5-Hour CAT and 3-Hour NID mock papers above without LLM connection!
            </p>
          )}
        </form>

        {/* Saved / Historical Mock Papers List */}
        <section className="xl:col-span-6 bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-4 shadow-xs">
          <div>
            <h2 className="font-serif-editorial text-xl font-medium text-[#18181B]">
              Saved & Available Mock Papers
            </h2>
            <p className="text-xs text-[#78716C] mt-0.5">
              Stored locally in SQLite. Open any paper to practice offline with countdown timer and post-exam rubrics.
            </p>
          </div>

          {loadingPapers ? (
            <div className="py-10 text-center text-xs text-[#78716C]">Loading mock papers...</div>
          ) : papers.length === 0 ? (
            <div className="py-12 text-center border border-dashed border-[#D8D4CB] rounded-lg space-y-1.5">
              <p className="text-sm text-[#57534E]">No mock papers available.</p>
              <p className="text-xs text-[#78716C]">
                Configure a paper on the left or launch one of the featured papers above.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-[#ECEAE4] max-h-[520px] overflow-y-auto pr-1">
              {papers.map((paper) => {
                const is5hr = paper.id === 'cat-5hr-official-exam-001';
                const is3hr = paper.id === 'cat-3hr-official-exam-002';

                return (
                  <div key={paper.id} className="py-3.5 flex items-start justify-between gap-4">
                    <div className="space-y-1 min-w-0">
                      <div className="flex items-center gap-2">
                        {is5hr && (
                          <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-amber-100 text-amber-800 border border-amber-200 uppercase tracking-wider">
                            Official 5-Hr CAT
                          </span>
                        )}
                        {is3hr && (
                          <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-sky-100 text-sky-800 border border-sky-200 uppercase tracking-wider">
                            3-Hr NID
                          </span>
                        )}
                        <button
                          type="button"
                          onClick={() => openPaper(paper)}
                          className="text-left text-sm font-semibold text-[#18181B] hover:text-[#1E3A5F] cursor-pointer truncate"
                        >
                          {paper.title}
                        </button>
                      </div>

                      <div className="flex flex-wrap items-center gap-2 text-xs text-[#78716C]">
                        <span className="font-mono-exam font-semibold text-[#18181B]">
                          {paper.questions.length} Questions
                        </span>
                        <span>•</span>
                        <span className="font-mono-exam font-semibold text-[#18181B]">
                          {paper.total_time_minutes} min ({Math.round((paper.total_time_minutes / 60) * 10) / 10}h)
                        </span>
                        <span>•</span>
                        <span>{paper.difficulty}</span>
                        <span>•</span>
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                            paper.status === 'completed'
                              ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                              : paper.status === 'in_progress'
                                ? 'bg-amber-50 text-amber-800 border border-amber-200'
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
                        className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-[#D8D4CB] text-[#1E3A5F] bg-white hover:bg-[#1E3A5F]/5 cursor-pointer shadow-2xs"
                      >
                        Open Paper
                      </button>
                      {!is5hr && !is3hr && (
                        <button
                          type="button"
                          onClick={() => handleDeletePaper(paper.id)}
                          className="p-1.5 rounded text-[#78716C] hover:text-rose-700 hover:bg-rose-50 cursor-pointer"
                          title="Delete paper"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </div>
  );
};
