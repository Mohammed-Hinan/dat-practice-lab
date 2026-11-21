import React from 'react';
import {
  ArrowRight,
  Award,
  BookOpen,
  CheckCircle2,
  Clock,
  Compass,
  FileText,
  Flame,
  HelpCircle,
  Layers,
  RotateCcw,
  Sparkles,
  TrendingUp,
  XCircle,
} from 'lucide-react';
import type { GATOverview as GATOverviewData, GATSection, GATSubTab } from '../../types';
import { formatDuration } from '../../api';

interface GATOverviewProps {
  overview: GATOverviewData | null;
  loading: boolean;
  onNavigateTab: (tab: GATSubTab, sectionFilter?: GATSection) => void;
  onStartPractice: (section?: GATSection) => void;
}

export const GATOverview: React.FC<GATOverviewProps> = ({
  overview,
  loading,
  onNavigateTab,
  onStartPractice,
}) => {
  if (loading || !overview) {
    return (
      <div className="py-16 text-center space-y-3">
        <div className="inline-block w-6 h-6 border-2 border-[#1E3A5F] border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-[#78716C]">Loading GAT preparation dashboard...</p>
      </div>
    );
  }

  const {
    total_questions,
    total_attempted,
    accuracy_percentage,
    bookmarked_count,
    incorrect_count,
    sections_progress,
    weak_topics,
    recent_activity,
    recommended_practice,
  } = overview;

  return (
    <div className="space-y-8">
      {/* Hero Recommended Action Card */}
      <section className="bg-gradient-to-br from-[#1E3A5F] to-[#142842] text-white rounded-2xl p-6 sm:p-8 shadow-sm border border-[#1E3A5F]/20 relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-white/5 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/10 text-white/90 text-xs font-medium border border-white/15">
              <Sparkles className="w-3.5 h-3.5 text-amber-300" />
              <span>Recommended Daily Practice</span>
            </div>
            <h2 className="font-serif-editorial text-2xl sm:text-3xl font-medium tracking-tight">
              {recommended_practice.title}
            </h2>
            <p className="text-white/80 text-sm leading-relaxed">
              {recommended_practice.description}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <button
              type="button"
              onClick={() => onStartPractice(recommended_practice.section as GATSection)}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white text-[#1E3A5F] font-semibold text-sm hover:bg-stone-50 active:scale-[0.99] transition-all shadow-sm cursor-pointer"
            >
              Start 5-Q Sprint
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => onNavigateTab('mock_tests')}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/15 text-white font-medium text-sm border border-white/20 transition-all cursor-pointer"
            >
              <Clock className="w-4 h-4 text-white/70" />
              Timed Mock Test
            </button>
          </div>
        </div>
      </section>

      {/* Core Preparation Metric Tiles */}
      <section className="grid grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4">
        <div className="bg-white border border-[#E4E1DA] rounded-xl p-4 sm:p-5 space-y-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#78716C] flex items-center gap-1">
            <Layers className="w-3.5 h-3.5 text-[#1E3A5F]" />
            Question Bank
          </span>
          <div className="font-mono-exam text-2xl font-bold text-[#18181B]">{total_questions}</div>
          <p className="text-xs text-[#78716C]">From UCEED, NIFT, CEED</p>
        </div>

        <div className="bg-white border border-[#E4E1DA] rounded-xl p-4 sm:p-5 space-y-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#78716C] flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            Attempted
          </span>
          <div className="font-mono-exam text-2xl font-bold text-[#18181B]">
            {total_attempted}{' '}
            <span className="text-xs font-normal text-[#78716C]">
              ({Math.round((total_attempted / Math.max(1, total_questions)) * 100)}%)
            </span>
          </div>
          <p className="text-xs text-[#78716C]">Coverage of total bank</p>
        </div>

        <div className="bg-white border border-[#E4E1DA] rounded-xl p-4 sm:p-5 space-y-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#78716C] flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5 text-blue-600" />
            Accuracy
          </span>
          <div className="font-mono-exam text-2xl font-bold text-[#18181B]">{accuracy_percentage}%</div>
          <p className="text-xs text-[#78716C]">Overall first-attempt rate</p>
        </div>

        <div className="bg-white border border-[#E4E1DA] rounded-xl p-4 sm:p-5 space-y-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#78716C] flex items-center gap-1">
            <XCircle className="w-3.5 h-3.5 text-rose-600" />
            Mistake Notebook
          </span>
          <div className="font-mono-exam text-2xl font-bold text-rose-700">{incorrect_count}</div>
          <button
            type="button"
            onClick={() => onNavigateTab('revision')}
            className="text-xs text-rose-600 hover:text-rose-800 font-medium underline inline-flex items-center gap-0.5 cursor-pointer"
          >
            Review mistakes &rarr;
          </button>
        </div>

        <div className="bg-white border border-[#E4E1DA] rounded-xl p-4 sm:p-5 space-y-1 col-span-2 lg:col-span-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#78716C] flex items-center gap-1">
            <Award className="w-3.5 h-3.5 text-amber-600" />
            Bookmarks
          </span>
          <div className="font-mono-exam text-2xl font-bold text-[#18181B]">{bookmarked_count}</div>
          <button
            type="button"
            onClick={() => onNavigateTab('revision')}
            className="text-xs text-[#1E3A5F] hover:underline font-medium cursor-pointer"
          >
            Open saved questions &rarr;
          </button>
        </div>
      </section>

      {/* 4 Core GAT Subjects */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-serif-editorial text-xl font-medium text-[#18181B]">
              Subject Syllabus & Progress
            </h3>
            <p className="text-xs text-[#78716C]">
              Targeted preparation across the 4 core design entrance GAT disciplines
            </p>
          </div>
          <button
            type="button"
            onClick={() => onNavigateTab('learn')}
            className="text-xs font-semibold text-[#1E3A5F] hover:underline inline-flex items-center gap-1 cursor-pointer"
          >
            View Full Curriculum <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sections_progress.map((sec) => {
            const pct = Math.round((sec.attempted_questions / Math.max(1, sec.total_questions)) * 100);
            return (
              <div
                key={sec.section}
                className="bg-white border border-[#E4E1DA] rounded-xl p-5 hover:border-[#1E3A5F]/40 transition-colors space-y-4 shadow-2xs"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h4 className="font-semibold text-base text-[#18181B]">{sec.title}</h4>
                    <p className="text-xs text-[#78716C] mt-0.5">{sec.description}</p>
                  </div>
                  <span className="font-mono-exam text-xs px-2 py-0.5 rounded bg-[#FAF9F6] border border-[#E4E1DA] text-[#57534E]">
                    {sec.total_questions} Qs
                  </span>
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs text-[#57534E]">
                    <span>
                      Progress: <strong>{sec.attempted_questions}</strong> / {sec.total_questions}
                    </span>
                    <span className="font-mono-exam font-medium">{pct}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-stone-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#1E3A5F] rounded-full transition-all duration-300"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>

                <div className="pt-2 border-t border-[#F2EFE9] flex items-center justify-between">
                  <div className="text-xs text-[#78716C]">
                    Accuracy:{' '}
                    <span className="font-mono-exam font-semibold text-[#18181B]">
                      {sec.accuracy_percentage}%
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => onNavigateTab('learn', sec.section)}
                      className="text-xs text-[#57534E] hover:text-[#18181B] font-medium px-2.5 py-1 rounded border border-[#E4E1DA] hover:bg-stone-50 cursor-pointer"
                    >
                      Concepts
                    </button>
                    <button
                      type="button"
                      onClick={() => onStartPractice(sec.section)}
                      className="text-xs font-semibold text-white px-3 py-1 rounded bg-[#1E3A5F] hover:bg-[#162C49] cursor-pointer"
                    >
                      Practice &rarr;
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Weak Areas Banner if present */}
      {weak_topics.length > 0 && (
        <section className="bg-rose-50/60 border border-rose-200/80 rounded-xl p-5 space-y-3">
          <div className="flex items-center gap-2 text-rose-800">
            <Flame className="w-4 h-4 text-rose-600" />
            <h4 className="font-semibold text-sm">Priority Revision Needed: Weak Topics</h4>
          </div>
          <p className="text-xs text-rose-700 leading-relaxed">
            These topics currently have less than 70% accuracy on first attempt. Focus short drills here to raise your percentile.
          </p>
          <div className="flex flex-wrap gap-2 pt-1">
            {weak_topics.map((w, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => onStartPractice(w.section as GATSection)}
                className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-white border border-rose-200 text-rose-900 hover:bg-rose-100/50 cursor-pointer shadow-2xs"
              >
                <span>{w.topic}</span>
                <span className="font-mono-exam text-[11px] text-rose-600 font-semibold">
                  ({w.accuracy}%)
                </span>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Recent Attempts Trail */}
      {recent_activity.length > 0 && (
        <section className="bg-white border border-[#E4E1DA] rounded-xl p-5 sm:p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-serif-editorial text-lg font-medium text-[#18181B]">
              Recent Practice Attempts
            </h4>
            <span className="text-xs text-[#78716C]">{recent_activity.length} recent sessions</span>
          </div>

          <div className="divide-y divide-[#F2EFE9]">
            {recent_activity.map((act) => (
              <div key={act.id} className="py-3 flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  {act.is_correct ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
                  ) : (
                    <XCircle className="w-4 h-4 text-rose-600 mt-0.5 shrink-0" />
                  )}
                  <div className="space-y-0.5">
                    <p className="text-sm font-medium text-[#18181B] line-clamp-1">
                      {act.question_text}
                    </p>
                    <div className="flex flex-wrap items-center gap-2 text-xs text-[#78716C]">
                      <span className="px-1.5 py-0.5 rounded bg-stone-100 text-[#57534E]">
                        {act.topic}
                      </span>
                      <span>·</span>
                      <span className="font-mono-exam">{formatDuration(act.time_spent_seconds)}</span>
                    </div>
                  </div>
                </div>

                <span
                  className={`font-mono-exam text-xs px-2 py-0.5 rounded font-medium shrink-0 ${
                    act.is_correct
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : 'bg-rose-50 text-rose-700 border border-rose-200'
                  }`}
                >
                  {act.is_correct ? 'Correct' : 'Incorrect'}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};
