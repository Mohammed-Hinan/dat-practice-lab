import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Bookmark,
  BookmarkCheck,
  Check,
  Clock,
  Copy,
  ExternalLink,
  Eye,
  Image as ImageIcon,
  Lock,
  Pause,
  PenTool,
  Play,
  RefreshCw,
  RotateCcw,
  ShieldAlert,
  Sparkles,
} from 'lucide-react';
import { api, formatDuration } from '../api';
import type { GeneratedQuestion } from '../types';

interface QuestionDisplayProps {
  question: GeneratedQuestion;
  questionNumber?: number;
  totalInBatch?: number;
  onSaveToggle?: (updated: GeneratedQuestion) => void;
  onAttemptSaved?: (questionId: string) => void;
  onRegenerate?: () => void;
  regenerating?: boolean;
  initialAttempted?: boolean;
  examMode?: boolean;
  externalRubricUnlocked?: boolean;
  externalElapsedSeconds?: number;
}

export const QuestionDisplay: React.FC<QuestionDisplayProps> = ({
  question,
  questionNumber = 1,
  totalInBatch,
  onSaveToggle,
  onRegenerate,
  regenerating = false,
  examMode = false,
  externalRubricUnlocked = false,
  externalElapsedSeconds,
}) => {
  const allocatedSeconds = question.time_minutes * 60;
  const [practiceStarted, setPracticeStarted] = useState(false);
  const [timerRunning, setTimerRunning] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [isSaved, setIsSaved] = useState(question.is_saved);
  const [savingBookmark, setSavingBookmark] = useState(false);
  const [rubricRevealed, setRubricRevealed] = useState(false);

  // Reset per-question session state when question changes
  useEffect(() => {
    setPracticeStarted(false);
    setTimerRunning(false);
    setElapsedSeconds(0);
    setIsSaved(question.is_saved);
    setRubricRevealed(false);
  }, [question.id]);

  useEffect(() => {
    if (!timerRunning || examMode) return;
    const interval = window.setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);
    return () => window.clearInterval(interval);
  }, [timerRunning, examMode]);

  const effectiveElapsed = examMode && externalElapsedSeconds !== undefined ? externalElapsedSeconds : elapsedSeconds;
  const remainingSeconds = Math.max(0, allocatedSeconds - effectiveElapsed);
  const isOvertime = effectiveElapsed > allocatedSeconds;
  const progressPct = Math.min(100, (effectiveElapsed / Math.max(1, allocatedSeconds)) * 100);

  const canRevealRubric = !examMode || externalRubricUnlocked;

  const handleStartPractice = () => {
    setPracticeStarted(true);
    setTimerRunning(true);
  };

  const handleToggleBookmark = async () => {
    setSavingBookmark(true);
    try {
      const updated = await api.toggleSaveQuestion(question.id, !isSaved);
      setIsSaved(updated.is_saved);
      onSaveToggle?.(updated);
    } catch {
      // handled quietly
    } finally {
      setSavingBookmark(false);
    }
  };

  const [copiedGeminiPrompt, setCopiedGeminiPrompt] = useState(false);

  const handleCopyGeminiPrompt = () => {
    const lines = [
      'Act as a master NID / CEED industrial designer and technical illustrator.',
      'Generate an authentic design examination presentation sheet on clean off-white paper for the following question:',
      '',
      `"${question.title}"`,
      `Context & Scenario: ${question.scenario}`,
      '',
      'Deliverables & Examination Tasks:',
      ...question.subquestions.map((sq) => `- ${sq.label}) ${sq.instruction} (${sq.marks} marks)`),
      '',
      'Constraints:',
      ...question.constraints.map((c) => `- ${c}`),
      '',
      'Drawing & Visual Presentation Requirements on the Sheet:',
      '- Centered hero 3/4 isometric perspective view of the practical intervention/solution',
      '- Exploded isometric assembly drawing showing materials, parts, and joinery mechanisms',
      '- Circular detail zoom bubbles with leader lines explaining key functional features',
      '- Expressive human figure/hand vignette showing the solution in actual use',
      '- Neat hand-lettered English technical callouts and leader lines pointing to mechanisms',
      '- Medium: Confident black fineliner ink outlines, Copic warm-grey marker shading, clean white negative space',
      '- Exclusions: No photorealism, no 3D CGI, no glossy commercial photo, no messy dark background.',
    ];
    navigator.clipboard.writeText(lines.join('\n'));
    setCopiedGeminiPrompt(true);
    setTimeout(() => setCopiedGeminiPrompt(false), 3500);
  };

  const difficultyBadgeStyle =
    question.difficulty === 'Hard'
      ? 'bg-rose-50 text-rose-800 border-rose-200'
      : question.difficulty === 'Easy'
        ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
        : 'bg-stone-100 text-stone-800 border-stone-200';

  return (
    <article className="bg-white border border-[#E4E1DA] rounded-xl shadow-[0_1px_2px_rgba(0,0,0,0.03)] overflow-hidden">
      {/* Examination Paper Header Strip */}
      <div className="border-b border-[#E4E1DA] bg-[#FAF9F6] px-6 py-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono-exam text-xs font-semibold uppercase tracking-wider px-2.5 py-1 rounded bg-[#1E3A5F] text-white">
            Q{questionNumber}
            {totalInBatch ? ` / ${totalInBatch}` : ''}
          </span>
          <span className="text-xs font-medium px-2.5 py-1 rounded border border-[#D8D4CB] bg-white text-[#18181B]">
            {question.category}
          </span>
          <span className={`text-xs font-medium px-2.5 py-1 rounded border ${difficultyBadgeStyle}`}>
            {question.difficulty}
          </span>
          <span className="font-mono-exam text-xs px-2.5 py-1 rounded border border-[#E4E1DA] bg-white text-[#57534E]">
            {question.time_minutes} min
          </span>
          <span className="font-mono-exam text-xs px-2.5 py-1 rounded border border-[#E4E1DA] bg-white text-[#57534E]">
            {question.total_marks} marks
          </span>
        </div>

        <div className="flex items-center gap-2 no-print">
          <button
            type="button"
            onClick={handleToggleBookmark}
            disabled={savingBookmark}
            className={`inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border transition-colors cursor-pointer ${
              isSaved
                ? 'bg-[#1E3A5F]/10 border-[#1E3A5F]/30 text-[#1E3A5F]'
                : 'bg-white border-[#D8D4CB] text-[#44403C] hover:bg-stone-50'
            }`}
          >
            {isSaved ? <BookmarkCheck className="w-3.5 h-3.5" /> : <Bookmark className="w-3.5 h-3.5" />}
            {isSaved ? 'Saved' : 'Save Question'}
          </button>
        </div>
      </div>

      {/* Standalone Question Timer Bar (hidden in Exam Mode where paper-level timer runs) */}
      {!examMode && (
        <div className="border-b border-[#E4E1DA] bg-white px-6 py-3 flex flex-wrap items-center justify-between gap-4 no-print">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Clock className={`w-4 h-4 ${isOvertime ? 'text-rose-600' : 'text-[#1E3A5F]'}`} />
              <span
                className={`font-mono-exam text-lg font-semibold tabular-nums ${
                  isOvertime ? 'text-rose-700' : 'text-[#18181B]'
                }`}
              >
                {isOvertime ? `+${formatDuration(effectiveElapsed - allocatedSeconds)}` : formatDuration(remainingSeconds)}
              </span>
              <span className="text-xs text-[#78716C]">
                {isOvertime ? 'over allocated time' : `remaining (elapsed ${formatDuration(effectiveElapsed)})`}
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {!practiceStarted ? (
              <button
                type="button"
                onClick={handleStartPractice}
                className="inline-flex items-center gap-1.5 text-xs font-semibold px-3.5 py-1.5 rounded-lg bg-[#1E3A5F] text-white hover:bg-[#162C49] transition-colors cursor-pointer"
              >
                <Play className="w-3.5 h-3.5" />
                Start Practice
              </button>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => setTimerRunning((r) => !r)}
                  className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-[#D8D4CB] bg-white text-[#18181B] hover:bg-stone-50 cursor-pointer"
                >
                  {timerRunning ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                  {timerRunning ? 'Pause Timer' : 'Resume Timer'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setTimerRunning(false);
                    setElapsedSeconds(0);
                  }}
                  className="inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1.5 rounded-lg border border-[#E4E1DA] text-[#57534E] hover:bg-stone-50 cursor-pointer"
                  title="Reset timer"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  Reset
                </button>
              </>
            )}


            {onRegenerate && (
              <button
                type="button"
                onClick={onRegenerate}
                disabled={regenerating}
                className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-[#D8D4CB] bg-white text-[#44403C] hover:bg-stone-50 disabled:opacity-50 cursor-pointer shadow-xs transition-colors"
                title="Generate another question for this category"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${regenerating ? 'animate-spin' : ''}`} />
                {regenerating ? 'Generating...' : 'Different Question'}
              </button>
            )}
          </div>

          {/* Subtle linear progress indicator */}
          <div className="w-full h-1 bg-stone-100 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${isOvertime ? 'bg-rose-500' : 'bg-[#1E3A5F]'}`}
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      )}


      {/* Main Examination Prompt Body */}
      <div className="px-6 sm:px-8 py-6 space-y-6">
        {/* Title */}
        <div>
          <h2 className="font-serif-editorial text-2xl sm:text-[26px] font-medium text-[#18181B] leading-snug">
            {question.title}
          </h2>
        </div>

        {/* Scenario */}
        <section className="space-y-2">
          <h3 className="text-[11px] font-semibold uppercase tracking-widest text-[#78716C]">
            Context & Scenario
          </h3>
          <p className="text-[15px] leading-relaxed text-[#27272A] whitespace-pre-line">
            {question.scenario}
          </p>
        </section>

        {/* Subquestions / Tasks */}
        <section className="space-y-3">
          <h3 className="text-[11px] font-semibold uppercase tracking-widest text-[#78716C]">
            Examination Tasks
          </h3>
          <div className="divide-y divide-[#E4E1DA] border border-[#E4E1DA] rounded-lg bg-[#FCFBF9]">
            {question.subquestions.map((sq, idx) => (
              <div key={`${sq.label}-${idx}`} className="p-4 space-y-2">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <span className="font-mono-exam text-xs font-semibold w-6 h-6 rounded bg-[#18181B] text-white flex items-center justify-center shrink-0 mt-0.5">
                      {sq.label}
                    </span>
                    <p className="text-sm text-[#18181B] leading-relaxed">{sq.instruction}</p>
                  </div>
                  <span className="font-mono-exam text-xs font-medium text-[#57534E] shrink-0">
                    [{sq.marks} marks]
                  </span>
                </div>
                {sq.deliverables.length > 0 && (
                  <div className="pl-9 flex flex-wrap items-center gap-1.5 pt-1">
                    <span className="text-[11px] uppercase tracking-wider text-[#78716C] mr-1">
                      Deliverables:
                    </span>
                    {sq.deliverables.map((d, di) => (
                      <span
                        key={di}
                        className="text-xs px-2 py-0.5 rounded bg-white border border-[#E4E1DA] text-[#44403C]"
                      >
                        {d}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Constraints & Drawing Requirements side by side */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border border-[#E4E1DA] rounded-lg p-4 bg-white space-y-2">
            <h3 className="text-[11px] font-semibold uppercase tracking-widest text-[#78716C] flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-[#1E3A5F]" />
              Constraints
            </h3>
            {question.constraints.length > 0 ? (
              <ul className="list-disc pl-4 space-y-1 text-sm text-[#27272A]">
                {question.constraints.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-[#78716C] italic">No additional rigid constraints specified.</p>
            )}
          </div>

          <div className="border border-[#E4E1DA] rounded-lg p-4 bg-white space-y-2">
            <h3 className="text-[11px] font-semibold uppercase tracking-widest text-[#78716C] flex items-center gap-1.5">
              <PenTool className="w-3.5 h-3.5 text-[#1E3A5F]" />
              Drawing & Visual Communication
            </h3>
            {question.sketching_requirements.length > 0 ? (
              <ul className="list-disc pl-4 space-y-1 text-sm text-[#27272A]">
                {question.sketching_requirements.map((req, i) => (
                  <li key={i}>{req}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-[#78716C] italic">
                Written reasoning primary; annotated schematic diagrams optional.
              </p>
            )}
          </div>
        </div>

        {/* Evaluation Rubric */}
        <section className="border-t border-[#E4E1DA] pt-4 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-[11px] font-semibold uppercase tracking-widest text-[#78716C] flex items-center gap-1.5">
              {canRevealRubric ? <Sparkles className="w-3.5 h-3.5 text-[#1E3A5F]" /> : <Lock className="w-3.5 h-3.5" />}
              Evaluation Rubric ({question.total_marks} Marks)
            </h3>

            {canRevealRubric ? (
              <button
                type="button"
                onClick={() => setRubricRevealed((v) => !v)}
                className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-[#1E3A5F]/30 text-[#1E3A5F] bg-[#1E3A5F]/5 hover:bg-[#1E3A5F]/10 cursor-pointer"
              >
                <Eye className="w-3.5 h-3.5" />
                {rubricRevealed ? 'Hide Evaluation Criteria' : 'Reveal Evaluation Criteria'}
              </button>
            ) : (
              <span className="text-xs text-[#78716C]">
                Evaluation criteria unlock when the examination paper is submitted.
              </span>
            )}
          </div>

          {canRevealRubric && rubricRevealed && (
            <div className="border border-[#E4E1DA] rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-[#FAF9F6] text-left text-xs uppercase tracking-wider text-[#57534E]">
                  <tr>
                    <th className="px-4 py-2.5 font-semibold">Evaluation Criterion</th>
                    <th className="px-4 py-2.5 font-semibold text-right w-28">Weight</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E4E1DA]">
                  {question.evaluation_rubric.map((r, i) => (
                    <tr key={i} className="bg-white">
                      <td className="px-4 py-2.5 text-[#18181B]">{r.criterion}</td>
                      <td className="px-4 py-2.5 text-right font-mono-exam text-[#44403C]">{r.marks} marks</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* Visual Reference (Draw Things) — Generated on Submit or on Command */}
        <section className="border-t border-[#E4E1DA] pt-4 space-y-3 no-print">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-[11px] font-semibold uppercase tracking-widest text-[#78716C] flex items-center gap-1.5">
              <ImageIcon className="w-3.5 h-3.5 text-[#1E3A5F]" />
              Visual Reference Solution (Google Gemini)
            </h3>

            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={handleCopyGeminiPrompt}
                className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg border border-[#1E3A5F]/30 bg-[#F7F9FC] text-[#1E3A5F] hover:bg-[#EEF2F8] cursor-pointer shadow-xs transition-colors"
                title="Copy formatted NID Master Prompt to paste into free Google Gemini (gemini.google.com)"
              >
                {copiedGeminiPrompt ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                    <span className="text-emerald-700 font-semibold">✓ Copied for Google Gemini!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5 text-[#1E3A5F]" />
                    <span>Copy Prompt for Google Gemini</span>
                  </>
                )}
              </button>

              <a
                href="https://gemini.google.com/app"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-[11px] font-medium text-[#1E3A5F] px-2.5 py-1.5 rounded-lg border border-[#D8D4CB] bg-white hover:bg-stone-50 cursor-pointer"
                title="Open Google Gemini in a new browser tab"
              >
                Open Gemini
                <ExternalLink className="w-3 h-3 text-[#78716C]" />
              </a>


            </div>
          </div>

          <div className="p-4 bg-[#FAF9F6] border border-[#E4E1DA] rounded-lg space-y-2 text-xs text-[#57534E]">
            <p className="leading-relaxed">
              <strong>Master Visual Prompt:</strong> Click <em>&ldquo;Copy Prompt for Google Gemini&rdquo;</em> and paste it into{' '}
              <a href="https://gemini.google.com/app" target="_blank" rel="noreferrer" className="text-[#1E3A5F] font-semibold underline">
                gemini.google.com
              </a>{' '}
              to generate an authentic design presentation sheet with 2-point perspective, exploded mechanism assembly, and annotations.
            </p>
            {question.visual_sketch_prompt && (
              <div className="bg-white border border-[#E4E1DA] rounded p-2.5 font-mono-exam text-[11px] text-[#27272A] leading-normal">
                {question.visual_sketch_prompt}
              </div>
            )}
          </div>





        </section>


      </div>
    </article>
  );
};
