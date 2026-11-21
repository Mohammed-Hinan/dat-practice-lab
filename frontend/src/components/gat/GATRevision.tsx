import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  ArrowRight,
  Bookmark,
  BookmarkCheck,
  CheckCircle2,
  Clock,
  Eye,
  Filter,
  RotateCcw,
  Sparkles,
  XCircle,
} from 'lucide-react';
import type { GATQuestion, GATSection } from '../../types';
import { api, formatDuration } from '../../api';

interface GATRevisionProps {
  onPracticeQuestion: (question: GATQuestion) => void;
  onRefreshOverview?: () => void;
}

export const GATRevision: React.FC<GATRevisionProps> = ({
  onPracticeQuestion,
  onRefreshOverview,
}) => {
  const [activeTab, setActiveTab] = useState<'mistakes' | 'bookmarks'>('mistakes');
  const [questions, setQuestions] = useState<GATQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSection, setSelectedSection] = useState<string>('all');
  const [revealedExplanationId, setRevealedExplanationId] = useState<string | null>(null);

  const fetchQuestions = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (selectedSection !== 'all') params.section = selectedSection;
      if (activeTab === 'mistakes') {
        params.incorrect_only = true;
      } else {
        params.bookmarked_only = true;
      }
      const data = await api.listGATQuestions(params);
      setQuestions(data);
    } catch (err) {
      console.error('Failed to load revision questions', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuestions();
  }, [activeTab, selectedSection]);

  const handleToggleBookmark = async (q: GATQuestion) => {
    const nextState = !q.is_bookmarked;
    try {
      await api.toggleGATBookmark(q.id, nextState);
      setQuestions((prev) =>
        prev
          .map((item) => (item.id === q.id ? { ...item, is_bookmarked: nextState } : item))
          .filter((item) => (activeTab === 'bookmarks' ? nextState : true))
      );
      onRefreshOverview?.();
    } catch (err) {
      console.error('Failed to toggle bookmark', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Subtab Toggle Strip & Filter */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#E4E1DA] pb-4">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setActiveTab('mistakes')}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'mistakes'
                ? 'bg-rose-50 text-rose-900 border border-rose-200 shadow-2xs'
                : 'bg-white text-[#57534E] border border-[#D8D4CB] hover:bg-stone-50'
            }`}
          >
            <XCircle className="w-3.5 h-3.5 text-rose-600" />
            Mistake Notebook
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('bookmarks')}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'bookmarks'
                ? 'bg-[#1E3A5F]/10 text-[#1E3A5F] border border-[#1E3A5F]/30 shadow-2xs'
                : 'bg-white text-[#57534E] border border-[#D8D4CB] hover:bg-stone-50'
            }`}
          >
            <Bookmark className="w-3.5 h-3.5 text-[#1E3A5F]" />
            Bookmarked Questions
          </button>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="text-[#78716C]">Subject:</span>
          <select
            value={selectedSection}
            onChange={(e) => setSelectedSection(e.target.value)}
            className="border border-[#D8D4CB] rounded-md px-2.5 py-1 bg-white text-[#18181B] cursor-pointer"
          >
            <option value="all">All Subjects</option>
            <option value="quantitative_ability">Quantitative Ability</option>
            <option value="analytical_reasoning">Analytical Reasoning</option>
            <option value="english">English & Verbal</option>
            <option value="gk_awareness">GK & Design Awareness</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="py-20 text-center space-y-2">
          <div className="inline-block w-6 h-6 border-2 border-[#1E3A5F] border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-[#78716C]">Retrieving revision queue...</p>
        </div>
      ) : questions.length === 0 ? (
        <div className="p-12 text-center bg-white border border-[#E4E1DA] rounded-xl space-y-3">
          <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto" />
          <h4 className="font-serif-editorial text-xl font-medium text-[#18181B]">
            {activeTab === 'mistakes' ? 'No mistakes pending!' : 'No bookmarked questions yet'}
          </h4>
          <p className="text-xs text-[#78716C] max-w-sm mx-auto">
            {activeTab === 'mistakes'
              ? 'Any question answered incorrectly in Practice or Mock Tests will automatically queue here for targeted spaced revision.'
              : 'Save questions while practicing by tapping the bookmark icon to review tricky concepts later.'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {questions.map((q, idx) => {
            const isExplRevealed = revealedExplanationId === q.id;

            return (
              <article
                key={q.id}
                className="bg-white border border-[#E4E1DA] rounded-xl p-5 hover:border-[#1E3A5F]/30 transition-all space-y-3 shadow-2xs"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono-exam text-xs px-2 py-0.5 rounded bg-[#FAF9F6] border border-[#E4E1DA] text-[#57534E]">
                      {q.exam} {q.year || ''}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded bg-stone-100 text-[#57534E]">
                      {q.topic}
                    </span>
                    <span className="text-xs font-mono-exam px-2 py-0.5 rounded bg-blue-50 text-blue-700">
                      {q.question_type.replace('_', ' ')}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleToggleBookmark(q)}
                      className={`text-xs p-1.5 rounded border cursor-pointer ${
                        q.is_bookmarked
                          ? 'bg-[#1E3A5F]/10 text-[#1E3A5F] border-[#1E3A5F]/20'
                          : 'bg-white text-[#78716C] border-[#D8D4CB]'
                      }`}
                      title={q.is_bookmarked ? 'Remove bookmark' : 'Bookmark question'}
                    >
                      {q.is_bookmarked ? (
                        <BookmarkCheck className="w-3.5 h-3.5" />
                      ) : (
                        <Bookmark className="w-3.5 h-3.5" />
                      )}
                    </button>
                    <button
                      type="button"
                      onClick={() => onPracticeQuestion(q)}
                      className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-[#1E3A5F] text-white hover:bg-[#162C49] cursor-pointer"
                    >
                      <RotateCcw className="w-3 h-3" /> Retry Question
                    </button>
                  </div>
                </div>

                <p className="text-sm font-medium text-[#18181B] leading-relaxed line-clamp-3">
                  {q.question_text}
                </p>

                {q.image_url && (
                  <div className="max-w-xs bg-stone-50 p-2 rounded-lg border border-[#E4E1DA]">
                    <img
                      src={q.image_url}
                      alt="Question diagram thumbnail"
                      className="max-h-24 object-contain rounded"
                    />
                  </div>
                )}

                <div className="pt-2 border-t border-[#F2EFE9] flex items-center justify-between text-xs">
                  <span className="text-[#78716C] font-mono-exam">
                    Correct: <strong>{q.correct_answers.join(', ')}</strong>
                  </span>

                  <button
                    type="button"
                    onClick={() =>
                      setRevealedExplanationId(isExplRevealed ? null : q.id)
                    }
                    className="text-xs text-[#1E3A5F] hover:underline font-medium inline-flex items-center gap-1 cursor-pointer"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    {isExplRevealed ? 'Hide Solution' : 'View Verified Solution'}
                  </button>
                </div>

                {isExplRevealed && (
                  <div className="bg-[#FAF9F6] p-4 rounded-lg border border-[#E4E1DA] text-xs text-[#27272A] leading-relaxed whitespace-pre-line">
                    {q.explanation}
                  </div>
                )}
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
};
