import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  Bookmark,
  BookmarkCheck,
  Check,
  CheckCircle2,
  Clock,
  Delete,
  Eye,
  Filter,
  Flag,
  HelpCircle,
  Maximize2,
  RefreshCw,
  RotateCcw,
  Sparkles,
  X,
  XCircle,
  ZoomIn,
} from 'lucide-react';
import type { GATAttemptResult, GATQuestion, GATQuestionType, GATSection } from '../../types';
import { api, formatDuration } from '../../api';

interface GATPracticeProps {
  initialSection?: GATSection;
  onRefreshOverview?: () => void;
}

export const GATPractice: React.FC<GATPracticeProps> = ({
  initialSection,
  onRefreshOverview,
}) => {
  const [questions, setQuestions] = useState<GATQuestion[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);

  // Filters
  const [selectedSection, setSelectedSection] = useState<string>(initialSection || 'all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all');

  // User input & session state
  const [userSelectedOptions, setUserSelectedOptions] = useState<string[]>([]);
  const [numericalInput, setNumericalInput] = useState<string>('');
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [attemptResult, setAttemptResult] = useState<GATAttemptResult | null>(null);
  const [bookmarked, setBookmarked] = useState(false);
  const [markedForReview, setMarkedForReview] = useState(false);
  const [zoomedImage, setZoomedImage] = useState<string | null>(null);

  // Timer
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // Fetch questions
  const loadQuestions = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (selectedSection !== 'all') params.section = selectedSection;
      if (selectedType !== 'all') params.question_type = selectedType;
      if (selectedDifficulty !== 'all') params.difficulty = selectedDifficulty;

      const data = await api.listGATQuestions(params);
      setQuestions(data);
      setCurrentIndex(0);
      resetQuestionState(data[0]);
    } catch (err) {
      console.error('Failed to load GAT questions', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQuestions();
  }, [selectedSection, selectedType, selectedDifficulty]);

  const currentQ = questions[currentIndex] || null;

  const resetQuestionState = (q?: GATQuestion) => {
    setUserSelectedOptions([]);
    setNumericalInput('');
    setSubmitted(false);
    setAttemptResult(null);
    setElapsedSeconds(0);
    setMarkedForReview(false);
    if (q) {
      setBookmarked(q.is_bookmarked);
    }
  };

  // Timer tick
  useEffect(() => {
    if (submitted) return;
    const interval = window.setInterval(() => {
      setElapsedSeconds((s) => s + 1);
    }, 1000);
    return () => window.clearInterval(interval);
  }, [submitted, currentIndex]);

  // Keyboard navigation & shortcuts (1-4 / A-D / Enter)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) {
        if (e.key === 'Enter' && !submitted) {
          handleSubmit();
        }
        return;
      }

      if (!currentQ) return;

      const keyUpper = e.key.toUpperCase();
      const numMap: Record<string, string> = { '1': 'A', '2': 'B', '3': 'C', '4': 'D' };
      const optionLetter = ['A', 'B', 'C', 'D'].includes(keyUpper)
        ? keyUpper
        : numMap[e.key];

      if (optionLetter && !submitted && currentQ.question_type !== 'numerical') {
        e.preventDefault();
        handleOptionClick(optionLetter);
      } else if (e.key === 'Enter' && !submitted) {
        e.preventDefault();
        handleSubmit();
      } else if (e.key === 'ArrowRight' && submitted) {
        e.preventDefault();
        handleNext();
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        handlePrevious();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentQ, userSelectedOptions, numericalInput, submitted]);

  const handleOptionClick = (letter: string) => {
    if (submitted || !currentQ) return;
    if (currentQ.question_type === 'multiple_choice') {
      setUserSelectedOptions([letter]);
    } else if (currentQ.question_type === 'multiple_select') {
      setUserSelectedOptions((prev) =>
        prev.includes(letter) ? prev.filter((item) => item !== letter) : [...prev, letter]
      );
    }
  };

  const handleKeypadPress = (val: string) => {
    if (submitted) return;
    if (val === 'clear') {
      setNumericalInput('');
    } else if (val === 'backspace') {
      setNumericalInput((prev) => prev.slice(0, -1));
    } else if (val === '.') {
      if (!numericalInput.includes('.')) {
        setNumericalInput((prev) => prev + '.');
      }
    } else if (val === '-') {
      if (numericalInput === '') {
        setNumericalInput('-');
      }
    } else {
      setNumericalInput((prev) => prev + val);
    }
  };

  const handleSubmit = async () => {
    if (!currentQ || submitted || submitting) return;

    const answersToSend =
      currentQ.question_type === 'numerical'
        ? [numericalInput.trim()]
        : userSelectedOptions;

    if (answersToSend.length === 0 || (currentQ.question_type === 'numerical' && !answersToSend[0])) {
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.recordGATAttempt(currentQ.id, {
        question_id: currentQ.id,
        user_answers: answersToSend,
        time_spent_seconds: elapsedSeconds,
        mode: 'practice',
      });
      setAttemptResult(res);
      setSubmitted(true);
      onRefreshOverview?.();
    } catch (err) {
      console.error('Failed to submit GAT attempt', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleBookmark = async () => {
    if (!currentQ) return;
    const nextState = !bookmarked;
    setBookmarked(nextState);
    try {
      await api.toggleGATBookmark(currentQ.id, nextState);
      onRefreshOverview?.();
    } catch {
      setBookmarked(!nextState);
    }
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      const nextIdx = currentIndex + 1;
      setCurrentIndex(nextIdx);
      resetQuestionState(questions[nextIdx]);
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      const prevIdx = currentIndex - 1;
      setCurrentIndex(prevIdx);
      resetQuestionState(questions[prevIdx]);
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center space-y-3">
        <div className="inline-block w-6 h-6 border-2 border-[#1E3A5F] border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-[#78716C]">Loading authentic Roughworks questions...</p>
      </div>
    );
  }

  if (questions.length === 0) {
    return (
      <div className="bg-white border border-[#E4E1DA] rounded-xl p-12 text-center space-y-4">
        <AlertCircle className="w-8 h-8 text-[#78716C] mx-auto" />
        <div className="space-y-1">
          <h3 className="font-serif-editorial text-xl font-medium text-[#18181B]">
            No questions match current filters
          </h3>
          <p className="text-sm text-[#78716C]">
            Try broadening your subject or difficulty criteria.
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            setSelectedSection('all');
            setSelectedType('all');
            setSelectedDifficulty('all');
          }}
          className="text-xs font-semibold px-4 py-2 rounded-lg bg-[#1E3A5F] text-white hover:bg-[#162C49] cursor-pointer"
        >
          Reset Filters
        </button>
      </div>
    );
  }

  const optionLetters = ['A', 'B', 'C', 'D'];

  return (
    <div className="space-y-6">
      {/* Filters Strip */}
      <div className="bg-white border border-[#E4E1DA] rounded-xl p-3.5 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-semibold text-[#57534E] flex items-center gap-1">
            <Filter className="w-3.5 h-3.5 text-[#1E3A5F]" />
            Subject:
          </span>
          <select
            value={selectedSection}
            onChange={(e) => setSelectedSection(e.target.value)}
            className="border border-[#D8D4CB] rounded-md px-2.5 py-1 bg-white text-[#18181B] cursor-pointer focus:outline-none"
          >
            <option value="all">All Subjects</option>
            <option value="quantitative_ability">Quantitative Ability</option>
            <option value="analytical_reasoning">Analytical Reasoning</option>
            <option value="english">English & Verbal</option>
            <option value="gk_awareness">GK & Design Awareness</option>
          </select>

          <span className="font-semibold text-[#57534E] ml-2">Type:</span>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="border border-[#D8D4CB] rounded-md px-2.5 py-1 bg-white text-[#18181B] cursor-pointer focus:outline-none"
          >
            <option value="all">All Types</option>
            <option value="multiple_choice">MCQ (Single)</option>
            <option value="multiple_select">MSQ (Multiple)</option>
            <option value="numerical">NAT (Numerical)</option>
          </select>

          <span className="font-semibold text-[#57534E] ml-2">Difficulty:</span>
          <select
            value={selectedDifficulty}
            onChange={(e) => setSelectedDifficulty(e.target.value)}
            className="border border-[#D8D4CB] rounded-md px-2.5 py-1 bg-white text-[#18181B] cursor-pointer focus:outline-none"
          >
            <option value="all">All Difficulties</option>
            <option value="Easy">Easy</option>
            <option value="Medium">Medium</option>
            <option value="Hard">Hard</option>
          </select>
        </div>

        <div className="flex items-center gap-2 text-[#78716C] font-mono-exam text-xs">
          <span>
            Question <strong>{currentIndex + 1}</strong> of {questions.length}
          </span>
        </div>
      </div>

      {/* Main Practice Question Card */}
      {currentQ && (
        <article className="bg-white border border-[#E4E1DA] rounded-xl shadow-xs overflow-hidden">
          {/* Card Header Strip */}
          <div className="border-b border-[#E4E1DA] bg-[#FAF9F6] px-6 py-3.5 flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono-exam text-xs font-semibold px-2.5 py-1 rounded bg-[#1E3A5F] text-white">
                Q{currentIndex + 1}
              </span>
              <span className="text-xs font-medium px-2.5 py-1 rounded border border-[#D8D4CB] bg-white text-[#18181B]">
                {currentQ.exam} {currentQ.year || ''}
              </span>
              <span className="text-xs px-2.5 py-1 rounded bg-stone-100 text-[#57534E] border border-stone-200">
                {currentQ.topic}
              </span>
              <span
                className={`text-xs px-2 py-0.5 rounded font-mono-exam ${
                  currentQ.question_type === 'numerical'
                    ? 'bg-purple-50 text-purple-700 border border-purple-200'
                    : currentQ.question_type === 'multiple_select'
                      ? 'bg-amber-50 text-amber-700 border border-amber-200'
                      : 'bg-blue-50 text-blue-700 border border-blue-200'
                }`}
              >
                {currentQ.question_type === 'numerical'
                  ? 'NAT (Numerical)'
                  : currentQ.question_type === 'multiple_select'
                    ? 'MSQ (Multiple Select)'
                    : 'MCQ (Single)'}
              </span>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 text-xs text-[#57534E] font-mono-exam">
                <Clock className="w-3.5 h-3.5 text-[#1E3A5F]" />
                <span>{formatDuration(elapsedSeconds)}</span>
              </div>

              <button
                type="button"
                onClick={() => setMarkedForReview((m) => !m)}
                className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded border transition-colors cursor-pointer ${
                  markedForReview
                    ? 'bg-amber-50 border-amber-300 text-amber-800'
                    : 'bg-white border-[#D8D4CB] text-[#57534E] hover:bg-stone-50'
                }`}
                title="Mark for review"
              >
                <Flag className="w-3 h-3" />
                <span>Review</span>
              </button>

              <button
                type="button"
                onClick={handleToggleBookmark}
                className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded border transition-colors cursor-pointer ${
                  bookmarked
                    ? 'bg-[#1E3A5F]/10 border-[#1E3A5F]/30 text-[#1E3A5F]'
                    : 'bg-white border-[#D8D4CB] text-[#57534E] hover:bg-stone-50'
                }`}
                title="Save question"
              >
                {bookmarked ? (
                  <BookmarkCheck className="w-3.5 h-3.5 text-[#1E3A5F]" />
                ) : (
                  <Bookmark className="w-3.5 h-3.5" />
                )}
                <span>{bookmarked ? 'Saved' : 'Save'}</span>
              </button>
            </div>
          </div>

          {/* Question Body */}
          <div className="p-6 sm:p-8 space-y-6">
            <div className="space-y-4">
              <p className="text-[16px] sm:text-[17px] leading-relaxed text-[#18181B] font-medium whitespace-pre-line">
                {currentQ.question_text}
              </p>

              {/* Diagram / Problem Image if present */}
              {currentQ.image_url && (
                <div className="relative group max-w-xl mx-auto my-4 border border-[#E4E1DA] rounded-xl overflow-hidden bg-[#FAF9F6] p-2 text-center">
                  <img
                    src={currentQ.image_url}
                    alt="Question Diagram"
                    className="max-h-72 w-auto mx-auto object-contain rounded"
                  />
                  <button
                    type="button"
                    onClick={() => setZoomedImage(currentQ.image_url || null)}
                    className="absolute top-3 right-3 p-1.5 rounded-lg bg-black/60 text-white hover:bg-black/80 backdrop-blur-xs transition-opacity cursor-pointer opacity-80 group-hover:opacity-100"
                    title="Click to zoom image"
                  >
                    <ZoomIn className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>

            {/* Answer Interface */}
            <div className="pt-2">
              {currentQ.question_type === 'numerical' ? (
                /* NAT Virtual Keypad + Input */
                <div className="space-y-4 max-w-sm mx-auto">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold uppercase tracking-wider text-[#78716C]">
                      Enter Numerical Value:
                    </label>
                    <input
                      type="text"
                      value={numericalInput}
                      onChange={(e) => !submitted && setNumericalInput(e.target.value)}
                      disabled={submitted}
                      placeholder="e.g. 7, 0.25, 36"
                      className="w-full px-4 py-2.5 text-lg font-mono-exam font-bold tracking-wider text-center border-2 border-[#1E3A5F] rounded-xl bg-white focus:outline-none"
                    />
                  </div>

                  {!submitted && (
                    <div className="grid grid-cols-3 gap-2 bg-[#FAF9F6] p-3 rounded-xl border border-[#E4E1DA]">
                      {['7', '8', '9', '4', '5', '6', '1', '2', '3', '-', '0', '.'].map((key) => (
                        <button
                          key={key}
                          type="button"
                          onClick={() => handleKeypadPress(key)}
                          className="h-11 rounded-lg bg-white border border-[#D8D4CB] hover:bg-stone-50 active:bg-stone-100 font-mono-exam font-semibold text-base text-[#18181B] shadow-2xs transition-colors cursor-pointer"
                        >
                          {key}
                        </button>
                      ))}
                      <button
                        type="button"
                        onClick={() => handleKeypadPress('clear')}
                        className="col-span-1 h-10 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold hover:bg-rose-100 cursor-pointer"
                      >
                        Clear
                      </button>
                      <button
                        type="button"
                        onClick={() => handleKeypadPress('backspace')}
                        className="col-span-2 h-10 rounded-lg bg-stone-100 border border-stone-300 text-[#44403C] text-xs font-semibold hover:bg-stone-200 flex items-center justify-center gap-1 cursor-pointer"
                      >
                        <Delete className="w-4 h-4" /> Backspace
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                /* MCQ / MSQ Options */
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between text-xs text-[#78716C] pb-1">
                    <span>
                      {currentQ.question_type === 'multiple_select'
                        ? 'Select ALL correct options (MSQ)'
                        : 'Select ONE correct option (MCQ)'}
                    </span>
                    <span className="hidden sm:inline">Use keys 1-4 or A-D</span>
                  </div>

                  {currentQ.options.map((optText, optIdx) => {
                    const letter = optionLetters[optIdx];
                    const isSelected = userSelectedOptions.includes(letter);
                    const isCorrectAnswer =
                      submitted && (attemptResult?.correct_answers || currentQ.correct_answers).includes(letter);
                    const isUserMistake = submitted && isSelected && !isCorrectAnswer;

                    let optStyle =
                      'border-[#D8D4CB] bg-white hover:border-[#1E3A5F] hover:bg-stone-50/50 text-[#18181B]';

                    if (submitted) {
                      if (isCorrectAnswer) {
                        optStyle =
                          'border-emerald-500 bg-emerald-50/80 text-emerald-900 font-medium ring-1 ring-emerald-500';
                      } else if (isUserMistake) {
                        optStyle = 'border-rose-400 bg-rose-50 text-rose-900 ring-1 ring-rose-400';
                      } else {
                        optStyle = 'border-[#E4E1DA] bg-stone-50/50 text-[#78716C] opacity-70';
                      }
                    } else if (isSelected) {
                      optStyle =
                        'border-[#1E3A5F] bg-[#1E3A5F]/5 text-[#1E3A5F] font-medium ring-1 ring-[#1E3A5F]';
                    }

                    return (
                      <button
                        key={letter}
                        type="button"
                        onClick={() => handleOptionClick(letter)}
                        disabled={submitted}
                        className={`w-full p-4 rounded-xl border text-left flex items-start gap-3 transition-all cursor-pointer ${optStyle}`}
                      >
                        <span
                          className={`w-6 h-6 rounded-md font-mono-exam text-xs font-semibold flex items-center justify-center shrink-0 mt-0.5 border ${
                            submitted && isCorrectAnswer
                              ? 'bg-emerald-600 text-white border-emerald-600'
                              : submitted && isUserMistake
                                ? 'bg-rose-600 text-white border-rose-600'
                                : isSelected
                                  ? 'bg-[#1E3A5F] text-white border-[#1E3A5F]'
                                  : 'bg-[#FAF9F6] border-[#D8D4CB] text-[#57534E]'
                          }`}
                        >
                          {letter}
                        </span>

                        <span className="text-sm sm:text-[15px] leading-relaxed flex-1">
                          {optText}
                        </span>

                        {submitted && isCorrectAnswer && (
                          <span className="shrink-0 flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">
                            <Check className="w-3.5 h-3.5" /> Correct
                          </span>
                        )}
                        {submitted && isUserMistake && (
                          <span className="shrink-0 flex items-center gap-1 text-xs font-semibold text-rose-700 bg-rose-100 px-2 py-0.5 rounded">
                            <X className="w-3.5 h-3.5" /> Your pick
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Submit / Action Bar */}
            <div className="pt-4 border-t border-[#E4E1DA] flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handlePrevious}
                  disabled={currentIndex === 0}
                  className="inline-flex items-center gap-1 text-xs font-medium px-3 py-2 rounded-lg border border-[#D8D4CB] bg-white text-[#44403C] hover:bg-stone-50 disabled:opacity-40 cursor-pointer"
                >
                  <ArrowLeft className="w-3.5 h-3.5" /> Previous
                </button>

                <button
                  type="button"
                  onClick={handleNext}
                  disabled={currentIndex === questions.length - 1}
                  className="inline-flex items-center gap-1 text-xs font-medium px-3 py-2 rounded-lg border border-[#D8D4CB] bg-white text-[#44403C] hover:bg-stone-50 disabled:opacity-40 cursor-pointer"
                >
                  Skip Question
                </button>
              </div>

              <div className="flex items-center gap-3">
                {!submitted ? (
                  <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={
                      submitting ||
                      (currentQ.question_type === 'numerical'
                        ? !numericalInput.trim()
                        : userSelectedOptions.length === 0)
                    }
                    className="inline-flex items-center gap-2 text-sm font-semibold px-6 py-2.5 rounded-xl bg-[#1E3A5F] text-white hover:bg-[#162C49] disabled:opacity-40 transition-all shadow-sm cursor-pointer"
                  >
                    {submitting ? 'Checking...' : 'Check Answer (Enter)'}
                  </button>
                ) : (
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => resetQuestionState(currentQ)}
                      className="inline-flex items-center gap-1.5 text-xs font-medium px-3.5 py-2 rounded-lg border border-[#D8D4CB] bg-white text-[#44403C] hover:bg-stone-50 cursor-pointer"
                    >
                      <RotateCcw className="w-3.5 h-3.5" /> Retry
                    </button>

                    {currentIndex < questions.length - 1 && (
                      <button
                        type="button"
                        onClick={handleNext}
                        className="inline-flex items-center gap-2 text-sm font-semibold px-5 py-2 rounded-xl bg-[#1E3A5F] text-white hover:bg-[#162C49] transition-all shadow-sm cursor-pointer"
                      >
                        Next Question <ArrowRight className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Verified Step-by-Step Explanation Drawer */}
            {submitted && attemptResult && (
              <div
                className={`p-6 rounded-xl border space-y-3.5 transition-all ${
                  attemptResult.is_correct
                    ? 'bg-emerald-50/70 border-emerald-200 text-emerald-950'
                    : 'bg-stone-50 border-[#D8D4CB] text-[#18181B]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {attemptResult.is_correct ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    ) : (
                      <XCircle className="w-5 h-5 text-rose-600" />
                    )}
                    <h4 className="font-semibold text-base">
                      {attemptResult.is_correct ? 'Correct! Nicely reasoned.' : 'Incorrect'}
                    </h4>
                  </div>

                  <span className="font-mono-exam text-xs font-semibold px-2.5 py-1 rounded bg-white border border-[#D8D4CB]">
                    Correct Answer: {attemptResult.correct_answers.join(', ')}
                  </span>
                </div>

                <div className="border-t border-[#E4E1DA] pt-3 space-y-2">
                  <h5 className="text-xs font-semibold uppercase tracking-wider text-[#57534E]">
                    Detailed Solution & Reasoning:
                  </h5>
                  <div className="text-sm leading-relaxed whitespace-pre-line text-[#27272A] bg-white p-4 rounded-lg border border-[#E4E1DA] font-sans">
                    {attemptResult.explanation}
                  </div>
                </div>
              </div>
            )}
          </div>
        </article>
      )}

      {/* Image Zoom Modal */}
      {zoomedImage && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
          onClick={() => setZoomedImage(null)}
        >
          <div
            className="relative max-w-4xl max-h-[90vh] bg-white rounded-xl p-2 overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              onClick={() => setZoomedImage(null)}
              className="absolute top-3 right-3 p-1 rounded-full bg-stone-100 hover:bg-stone-200 text-[#18181B] cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
            <img src={zoomedImage} alt="Zoomed Diagram" className="w-full h-auto rounded" />
          </div>
        </div>
      )}
    </div>
  );
};
