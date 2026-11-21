import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  Award,
  CheckCircle2,
  Clock,
  Delete,
  Eye,
  Flag,
  Play,
  RotateCcw,
  Sparkles,
  TrendingUp,
  X,
  XCircle,
} from 'lucide-react';
import type { GATMockTest, GATQuestion, GATSection } from '../../types';
import { api, formatDuration } from '../../api';

interface GATMockTestsProps {
  onRefreshOverview?: () => void;
}

export const GATMockTests: React.FC<GATMockTestsProps> = ({ onRefreshOverview }) => {
  const [tests, setTests] = useState<GATMockTest[]>([]);
  const [activeTest, setActiveTest] = useState<GATMockTest | null>(null);
  const [activeQuestionIndex, setActiveQuestionIndex] = useState(0);
  const [loading, setLoading] = useState(true);

  // In-test runtime state
  const [testTimeRemaining, setTestTimeRemaining] = useState(0);
  const [userAnswers, setUserAnswers] = useState<Record<string, string[]>>({});
  const [markedForReview, setMarkedForReview] = useState<Record<string, boolean>>({});
  const [submittedResult, setSubmittedResult] = useState<GATMockTest | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // New Test Creator Form state
  const [newTitle, setNewTitle] = useState('NIFT M.Des GAT Full Sectional Sprint');
  const [newExam, setNewExam] = useState('NIFT M.Des GAT');
  const [newTimeMinutes, setNewTimeMinutes] = useState(25);
  const [newNumQuestions, setNewNumQuestions] = useState(15);
  const [newSectionFilter, setNewSectionFilter] = useState<string>('');

  const fetchTests = async () => {
    setLoading(true);
    try {
      const data = await api.listGATMockTests();
      setTests(data);
    } catch (err) {
      console.error('Failed to list GAT mock tests', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTests();
  }, []);

  // Timer countdown during active test
  useEffect(() => {
    if (!activeTest || submittedResult) return;
    if (testTimeRemaining <= 0) {
      handleFinalSubmit();
      return;
    }

    const interval = window.setInterval(() => {
      setTestTimeRemaining((prev) => Math.max(0, prev - 1));
    }, 1000);

    return () => window.clearInterval(interval);
  }, [activeTest, testTimeRemaining, submittedResult]);

  const handleStartNewTest = async () => {
    setLoading(true);
    try {
      const created = await api.createGATMockTest({
        title: newTitle,
        exam: newExam,
        time_limit_minutes: newTimeMinutes,
        num_questions: newNumQuestions,
        section_filter: newSectionFilter || undefined,
      });
      setActiveTest(created);
      setTestTimeRemaining(created.time_limit_minutes * 60);
      setUserAnswers({});
      setMarkedForReview({});
      setActiveQuestionIndex(0);
      setSubmittedResult(null);
    } catch (err) {
      console.error('Failed to start mock test', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOptionToggle = (questionId: string, optLetter: string, isMsq: boolean) => {
    setUserAnswers((prev) => {
      const current = prev[questionId] || [];
      if (isMsq) {
        return {
          ...prev,
          [questionId]: current.includes(optLetter)
            ? current.filter((l) => l !== optLetter)
            : [...current, optLetter],
        };
      }
      return {
        ...prev,
        [questionId]: [optLetter],
      };
    });
  };

  const handleNatKeypad = (questionId: string, char: string) => {
    setUserAnswers((prev) => {
      const currentVal = (prev[questionId] || [''])[0] || '';
      if (char === 'clear') {
        return { ...prev, [questionId]: [''] };
      } else if (char === 'backspace') {
        return { ...prev, [questionId]: [currentVal.slice(0, -1)] };
      } else if (char === '.') {
        if (!currentVal.includes('.')) {
          return { ...prev, [questionId]: [currentVal + '.'] };
        }
      } else {
        return { ...prev, [questionId]: [currentVal + char] };
      }
      return prev;
    });
  };

  const handleFinalSubmit = async () => {
    if (!activeTest || submitting) return;
    setSubmitting(true);
    try {
      const completed = await api.submitGATMockTest(activeTest.id, userAnswers);
      setSubmittedResult(completed);
      fetchTests();
      onRefreshOverview?.();
    } catch (err) {
      console.error('Failed to submit mock test', err);
    } finally {
      setSubmitting(false);
    }
  };

  const currentQuestions = activeTest?.questions || [];
  const currentQ = currentQuestions[activeQuestionIndex];

  // --------------------------------------------------------------------------
  // Render: Test Score & Detailed Analysis Report
  // --------------------------------------------------------------------------
  if (submittedResult) {
    const questionsList = submittedResult.questions || [];
    let correctCount = 0;
    let incorrectCount = 0;
    let unattemptedCount = 0;

    questionsList.forEach((q) => {
      const ans = submittedResult.user_responses[q.id] || [];
      if (ans.length === 0 || (q.question_type === 'numerical' && !ans[0])) {
        unattemptedCount += 1;
      } else {
        const uClean = ans.map((a) => a.trim().toUpperCase());
        const cClean = q.correct_answers.map((a) => a.trim().toUpperCase());
        const isCor =
          q.question_type === 'numerical'
            ? Math.abs(parseFloat(uClean[0]) - parseFloat(cClean[0])) < 0.01
            : JSON.stringify(uClean.sort()) === JSON.stringify(cClean.sort());
        if (isCor) correctCount += 1;
        else incorrectCount += 1;
      }
    });

    const accuracy =
      correctCount + incorrectCount > 0
        ? Math.round((correctCount / (correctCount + incorrectCount)) * 100)
        : 0;

    return (
      <div className="space-y-8 max-w-4xl mx-auto">
        {/* Score Summary Banner */}
        <section className="bg-white border border-[#E4E1DA] rounded-2xl p-6 sm:p-8 space-y-6 shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#F2EFE9] pb-6">
            <div>
              <div className="text-xs font-semibold uppercase tracking-wider text-[#78716C]">
                Examination Result
              </div>
              <h2 className="font-serif-editorial text-2xl sm:text-3xl font-medium text-[#18181B] mt-0.5">
                {submittedResult.title}
              </h2>
            </div>

            <button
              type="button"
              onClick={() => {
                setSubmittedResult(null);
                setActiveTest(null);
              }}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#1E3A5F] text-white text-xs font-semibold hover:bg-[#162C49] cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Back to Tests Dashboard
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
            <div className="bg-[#FAF9F6] border border-[#E4E1DA] p-4 rounded-xl">
              <span className="text-[11px] font-semibold uppercase text-[#78716C]">Final Score</span>
              <div className="font-mono-exam text-3xl font-bold text-[#1E3A5F] mt-1">
                {submittedResult.score}{' '}
                <span className="text-sm font-normal text-[#78716C]">/ {submittedResult.total_marks}</span>
              </div>
            </div>

            <div className="bg-emerald-50/60 border border-emerald-200 p-4 rounded-xl">
              <span className="text-[11px] font-semibold uppercase text-emerald-800">Correct</span>
              <div className="font-mono-exam text-3xl font-bold text-emerald-700 mt-1">
                {correctCount}
              </div>
            </div>

            <div className="bg-rose-50/60 border border-rose-200 p-4 rounded-xl">
              <span className="text-[11px] font-semibold uppercase text-rose-800">Incorrect</span>
              <div className="font-mono-exam text-3xl font-bold text-rose-700 mt-1">
                {incorrectCount}
              </div>
            </div>

            <div className="bg-stone-50 border border-stone-200 p-4 rounded-xl">
              <span className="text-[11px] font-semibold uppercase text-[#57534E]">Accuracy</span>
              <div className="font-mono-exam text-3xl font-bold text-[#18181B] mt-1">
                {accuracy}%
              </div>
            </div>
          </div>
        </section>

        {/* Question Solutions List */}
        <section className="space-y-4">
          <h3 className="font-serif-editorial text-xl font-medium text-[#18181B]">
            Detailed Solution & Paper Analysis
          </h3>

          <div className="space-y-4">
            {questionsList.map((q, idx) => {
              const uAns = submittedResult.user_responses[q.id] || [];
              const hasAttempted = uAns.length > 0 && (q.question_type !== 'numerical' || !!uAns[0]);
              const isCor =
                hasAttempted &&
                (q.question_type === 'numerical'
                  ? Math.abs(parseFloat(uAns[0]) - parseFloat(q.correct_answers[0])) < 0.01
                  : JSON.stringify(uAns.map((a) => a.toUpperCase()).sort()) ===
                    JSON.stringify(q.correct_answers.map((a) => a.toUpperCase()).sort()));

              return (
                <div
                  key={q.id}
                  className="bg-white border border-[#E4E1DA] rounded-xl p-5 space-y-3"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono-exam font-semibold text-[#57534E]">
                      Question {idx + 1} ({q.topic})
                    </span>
                    <span
                      className={`font-mono-exam font-semibold px-2 py-0.5 rounded ${
                        !hasAttempted
                          ? 'bg-stone-100 text-[#57534E]'
                          : isCor
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-rose-100 text-rose-800'
                      }`}
                    >
                      {!hasAttempted ? 'Unattempted' : isCor ? 'Correct (+1.0)' : 'Incorrect (-0.25)'}
                    </span>
                  </div>

                  <p className="text-sm font-medium text-[#18181B] whitespace-pre-line">
                    {q.question_text}
                  </p>

                  {q.image_url && (
                    <img
                      src={q.image_url}
                      alt="Question diagram"
                      className="max-h-40 rounded object-contain border border-[#E4E1DA]"
                    />
                  )}

                  <div className="text-xs space-y-1 bg-[#FAF9F6] p-3 rounded-lg border border-[#E4E1DA]">
                    <div>
                      <strong>Your Answer:</strong>{' '}
                      <span className="font-mono-exam font-bold">
                        {uAns.join(', ') || 'None (skipped)'}
                      </span>
                    </div>
                    <div>
                      <strong>Correct Answer:</strong>{' '}
                      <span className="font-mono-exam font-bold text-emerald-700">
                        {q.correct_answers.join(', ')}
                      </span>
                    </div>
                    <div className="pt-2 text-[#44403C] whitespace-pre-line border-t border-stone-200 mt-2">
                      <strong>Solution:</strong> {q.explanation}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>
    );
  }

  // --------------------------------------------------------------------------
  // Render: Active Mock Test Simulator
  // --------------------------------------------------------------------------
  if (activeTest && currentQ) {
    const isOvertime = testTimeRemaining <= 0;
    const isWarning = testTimeRemaining < 300; // under 5 minutes

    const currentSelected = userAnswers[currentQ.id] || [];
    const isMsq = currentQ.question_type === 'multiple_select';
    const isNat = currentQ.question_type === 'numerical';
    const isRev = markedForReview[currentQ.id] || false;

    return (
      <div className="space-y-6 max-w-5xl mx-auto">
        {/* Test Simulator Top Bar */}
        <div className="bg-[#1E3A5F] text-white rounded-xl px-6 py-4 flex flex-wrap items-center justify-between gap-4 shadow-sm">
          <div>
            <h2 className="font-semibold text-base tracking-tight">{activeTest.title}</h2>
            <div className="text-xs text-white/70">Official GAT Exam Simulator</div>
          </div>

          <div className="flex items-center gap-4">
            <div
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-mono-exam text-base font-bold tabular-nums ${
                isWarning ? 'bg-rose-500 text-white animate-pulse' : 'bg-white/10 text-white'
              }`}
            >
              <Clock className="w-4 h-4" />
              <span>{formatDuration(testTimeRemaining)}</span>
            </div>

            <button
              type="button"
              onClick={handleFinalSubmit}
              disabled={submitting}
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold transition-colors cursor-pointer"
            >
              {submitting ? 'Submitting...' : 'Submit Test'}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Question Display Column */}
          <div className="lg:col-span-3 space-y-6">
            <article className="bg-white border border-[#E4E1DA] rounded-xl p-6 sm:p-8 space-y-6 shadow-xs">
              <div className="flex items-center justify-between border-b border-[#F2EFE9] pb-4">
                <div className="flex items-center gap-2">
                  <span className="font-mono-exam text-xs font-bold px-2.5 py-1 rounded bg-[#1E3A5F] text-white">
                    Question {activeQuestionIndex + 1} / {currentQuestions.length}
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded bg-stone-100 text-[#57534E]">
                    {currentQ.topic}
                  </span>
                  <span className="text-xs font-mono-exam px-2 py-0.5 rounded bg-blue-50 text-blue-700">
                    {currentQ.question_type.replace('_', ' ')}
                  </span>
                </div>

                <button
                  type="button"
                  onClick={() =>
                    setMarkedForReview((prev) => ({ ...prev, [currentQ.id]: !isRev }))
                  }
                  className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded border cursor-pointer ${
                    isRev
                      ? 'bg-purple-50 text-purple-800 border-purple-300 font-medium'
                      : 'bg-white text-[#57534E] border-[#D8D4CB]'
                  }`}
                >
                  <Flag className="w-3.5 h-3.5" />
                  {isRev ? 'Marked for Review' : 'Mark for Review'}
                </button>
              </div>

              {/* Question Text & Diagram */}
              <div className="space-y-4">
                <p className="text-base sm:text-[17px] text-[#18181B] font-medium leading-relaxed whitespace-pre-line">
                  {currentQ.question_text}
                </p>

                {currentQ.image_url && (
                  <div className="text-center p-3 bg-stone-50 border border-[#E4E1DA] rounded-xl">
                    <img
                      src={currentQ.image_url}
                      alt="Question diagram"
                      className="max-h-64 mx-auto object-contain rounded"
                    />
                  </div>
                )}
              </div>

              {/* Input: NAT or MCQ */}
              <div className="pt-2">
                {isNat ? (
                  <div className="space-y-3 max-w-xs mx-auto">
                    <input
                      type="text"
                      value={currentSelected[0] || ''}
                      onChange={(e) =>
                        setUserAnswers((p) => ({ ...p, [currentQ.id]: [e.target.value] }))
                      }
                      placeholder="Enter number"
                      className="w-full text-center font-mono-exam text-xl font-bold py-2 border-2 border-[#1E3A5F] rounded-lg"
                    />
                    <div className="grid grid-cols-3 gap-1.5">
                      {['7', '8', '9', '4', '5', '6', '1', '2', '3', '-', '0', '.'].map((k) => (
                        <button
                          key={k}
                          type="button"
                          onClick={() => handleNatKeypad(currentQ.id, k)}
                          className="h-9 rounded bg-[#FAF9F6] border border-[#D8D4CB] font-mono-exam font-semibold text-sm hover:bg-stone-100 cursor-pointer"
                        >
                          {k}
                        </button>
                      ))}
                      <button
                        type="button"
                        onClick={() => handleNatKeypad(currentQ.id, 'clear')}
                        className="col-span-1 h-8 rounded bg-rose-50 text-rose-700 text-xs font-semibold cursor-pointer"
                      >
                        Clear
                      </button>
                      <button
                        type="button"
                        onClick={() => handleNatKeypad(currentQ.id, 'backspace')}
                        className="col-span-2 h-8 rounded bg-stone-100 text-[#44403C] text-xs font-semibold flex items-center justify-center gap-1 cursor-pointer"
                      >
                        <Delete className="w-3.5 h-3.5" /> Backspace
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2.5">
                    {currentQ.options.map((opt, oIdx) => {
                      const letter = ['A', 'B', 'C', 'D'][oIdx];
                      const isSel = currentSelected.includes(letter);
                      return (
                        <button
                          key={letter}
                          type="button"
                          onClick={() => handleOptionToggle(currentQ.id, letter, isMsq)}
                          className={`w-full p-4 rounded-xl border text-left flex items-start gap-3 transition-colors cursor-pointer ${
                            isSel
                              ? 'bg-[#1E3A5F]/10 border-[#1E3A5F] text-[#1E3A5F] font-medium'
                              : 'bg-white border-[#D8D4CB] text-[#18181B] hover:bg-stone-50'
                          }`}
                        >
                          <span
                            className={`w-6 h-6 rounded font-mono-exam text-xs font-bold flex items-center justify-center shrink-0 border ${
                              isSel
                                ? 'bg-[#1E3A5F] text-white border-[#1E3A5F]'
                                : 'bg-stone-50 border-stone-300 text-[#57534E]'
                            }`}
                          >
                            {letter}
                          </span>
                          <span className="text-sm leading-relaxed">{opt}</span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Navigation Bar */}
              <div className="pt-4 border-t border-[#F2EFE9] flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => setActiveQuestionIndex((i) => Math.max(0, i - 1))}
                  disabled={activeQuestionIndex === 0}
                  className="inline-flex items-center gap-1 text-xs font-medium px-3 py-2 rounded-lg border border-[#D8D4CB] hover:bg-stone-50 disabled:opacity-40 cursor-pointer"
                >
                  <ArrowLeft className="w-3.5 h-3.5" /> Previous
                </button>

                <button
                  type="button"
                  onClick={() =>
                    setActiveQuestionIndex((i) => Math.min(currentQuestions.length - 1, i + 1))
                  }
                  disabled={activeQuestionIndex === currentQuestions.length - 1}
                  className="inline-flex items-center gap-1 text-xs font-semibold px-4 py-2 rounded-lg bg-[#1E3A5F] text-white hover:bg-[#162C49] disabled:opacity-40 cursor-pointer"
                >
                  Next <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </article>
          </div>

          {/* Question Palette Sidebar */}
          <div className="space-y-4">
            <div className="bg-white border border-[#E4E1DA] rounded-xl p-5 space-y-4 shadow-2xs">
              <h4 className="font-semibold text-xs uppercase tracking-wider text-[#78716C]">
                Question Palette
              </h4>

              <div className="grid grid-cols-5 gap-2">
                {currentQuestions.map((q, idx) => {
                  const ans = userAnswers[q.id] || [];
                  const isAnswered = ans.length > 0 && (q.question_type !== 'numerical' || !!ans[0]);
                  const isCurrent = idx === activeQuestionIndex;
                  const isMarked = markedForReview[q.id];

                  let btnStyle = 'bg-stone-100 text-[#57534E] border-stone-200';
                  if (isCurrent) {
                    btnStyle = 'ring-2 ring-[#1E3A5F] border-transparent font-bold';
                  }
                  if (isAnswered) {
                    btnStyle += ' bg-emerald-600 text-white border-emerald-600';
                  }
                  if (isMarked) {
                    btnStyle += ' bg-purple-600 text-white border-purple-600';
                  }

                  return (
                    <button
                      key={q.id}
                      type="button"
                      onClick={() => setActiveQuestionIndex(idx)}
                      className={`h-9 rounded-lg font-mono-exam text-xs flex items-center justify-center border transition-all cursor-pointer ${btnStyle}`}
                    >
                      {idx + 1}
                    </button>
                  );
                })}
              </div>

              {/* Palette Legend */}
              <div className="pt-3 border-t border-[#F2EFE9] space-y-2 text-[11px] text-[#57534E]">
                <div className="flex items-center gap-2">
                  <div className="w-3.5 h-3.5 rounded bg-emerald-600 shrink-0" />
                  <span>Answered</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3.5 h-3.5 rounded bg-purple-600 shrink-0" />
                  <span>Marked for Review</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3.5 h-3.5 rounded bg-stone-100 border border-stone-300 shrink-0" />
                  <span>Not Answered</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // --------------------------------------------------------------------------
  // Render: Mock Tests Dashboard & Creation Launcher
  // --------------------------------------------------------------------------
  return (
    <div className="space-y-8">
      {/* Test Generator Banner */}
      <section className="bg-white border border-[#E4E1DA] rounded-2xl p-6 sm:p-8 space-y-5 shadow-xs">
        <div>
          <h3 className="font-serif-editorial text-2xl font-medium text-[#18181B]">
            Configure Timed Mock Test
          </h3>
          <p className="text-xs text-[#78716C] mt-1">
            Simulate real exam conditions with strict countdown, question palette, and negative marking.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-[#57534E]">Exam Blueprint:</label>
            <select
              value={newExam}
              onChange={(e) => setNewExam(e.target.value)}
              className="w-full border border-[#D8D4CB] rounded-lg px-3 py-2 text-xs bg-white text-[#18181B]"
            >
              <option value="NIFT M.Des GAT">NIFT M.Des GAT (2025/2026)</option>
              <option value="UCEED Part A">UCEED Part A Practice</option>
              <option value="CEED Part A">CEED Part A General</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-[#57534E]">Section Focus:</label>
            <select
              value={newSectionFilter}
              onChange={(e) => setNewSectionFilter(e.target.value)}
              className="w-full border border-[#D8D4CB] rounded-lg px-3 py-2 text-xs bg-white text-[#18181B]"
            >
              <option value="">Full Mixed Paper (All 4 Subjects)</option>
              <option value="quantitative_ability">Quantitative Ability Only</option>
              <option value="analytical_reasoning">Analytical Reasoning Only</option>
              <option value="english">English & Verbal Only</option>
              <option value="gk_awareness">GK & Design Awareness Only</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-[#57534E]">Questions Count:</label>
            <select
              value={newNumQuestions}
              onChange={(e) => setNewNumQuestions(Number(e.target.value))}
              className="w-full border border-[#D8D4CB] rounded-lg px-3 py-2 text-xs bg-white text-[#18181B]"
            >
              <option value={10}>10 Questions (Quick)</option>
              <option value={15}>15 Questions (Standard)</option>
              <option value={20}>20 Questions (Full Bank)</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-[#57534E]">Time Limit:</label>
            <select
              value={newTimeMinutes}
              onChange={(e) => setNewTimeMinutes(Number(e.target.value))}
              className="w-full border border-[#D8D4CB] rounded-lg px-3 py-2 text-xs bg-white text-[#18181B]"
            >
              <option value={15}>15 Minutes</option>
              <option value={25}>25 Minutes</option>
              <option value={45}>45 Minutes</option>
              <option value={60}>60 Minutes</option>
            </select>
          </div>
        </div>

        <div className="pt-2 flex justify-end">
          <button
            type="button"
            onClick={handleStartNewTest}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-[#1E3A5F] text-white text-xs font-semibold hover:bg-[#162C49] cursor-pointer shadow-xs transition-all"
          >
            <Play className="w-4 h-4 fill-current" />
            Launch Mock Test Simulator
          </button>
        </div>
      </section>

      {/* Previously Taken Mock Tests */}
      {tests.length > 0 && (
        <section className="bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-4 shadow-2xs">
          <h4 className="font-serif-editorial text-lg font-medium text-[#18181B]">
            Mock Test History
          </h4>

          <div className="divide-y divide-[#F2EFE9]">
            {tests.map((t) => (
              <div key={t.id} className="py-3.5 flex items-center justify-between gap-4">
                <div>
                  <h5 className="font-semibold text-sm text-[#18181B]">{t.title}</h5>
                  <div className="flex items-center gap-2 text-xs text-[#78716C] mt-0.5">
                    <span>{t.exam}</span>
                    <span>•</span>
                    <span className="font-mono-exam">{t.question_ids.length} Questions</span>
                    <span>•</span>
                    <span>{t.time_limit_minutes} min</span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <span className="font-mono-exam text-sm font-bold text-[#1E3A5F]">
                      Score: {t.score} / {t.total_marks}
                    </span>
                    <div className="text-[11px] text-[#78716C]">
                      {t.status === 'completed' ? 'Submitted' : 'Incomplete'}
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => {
                      setSubmittedResult(t);
                    }}
                    className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-[#D8D4CB] hover:bg-stone-50 cursor-pointer"
                  >
                    View Breakdown
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};
