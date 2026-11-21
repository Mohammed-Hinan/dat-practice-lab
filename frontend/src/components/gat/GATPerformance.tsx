import React from 'react';
import {
  Award,
  BarChart3,
  CheckCircle2,
  Clock,
  Compass,
  Flame,
  Layers,
  Sparkles,
  TrendingUp,
  XCircle,
} from 'lucide-react';
import type { GATOverview, GATSection } from '../../types';
import { formatDuration } from '../../api';

interface GATPerformanceProps {
  overview: GATOverview | null;
  loading: boolean;
  onStartPractice: (section?: GATSection) => void;
}

export const GATPerformance: React.FC<GATPerformanceProps> = ({
  overview,
  loading,
  onStartPractice,
}) => {
  if (loading || !overview) {
    return (
      <div className="py-20 text-center space-y-2">
        <div className="inline-block w-6 h-6 border-2 border-[#1E3A5F] border-t-transparent rounded-full animate-spin" />
        <p className="text-xs text-[#78716C]">Loading performance analytics...</p>
      </div>
    );
  }

  const {
    total_questions,
    total_attempted,
    total_correct,
    accuracy_percentage,
    sections_progress,
    weak_topics,
    recent_activity,
  } = overview;

  // Calculate average time per attempted question from recent activity
  const avgTimeSeconds =
    recent_activity.length > 0
      ? Math.round(
          recent_activity.reduce((acc, curr) => acc + curr.time_spent_seconds, 0) /
            recent_activity.length
        )
      : 45;

  return (
    <div className="space-y-8">
      {/* Top Level Metric Dashboard */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-[#E4E1DA] rounded-xl p-5 space-y-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-[#78716C]">
            Coverage Rate
          </span>
          <div className="font-mono-exam text-2xl font-bold text-[#18181B]">
            {Math.round((total_attempted / Math.max(1, total_questions)) * 100)}%
          </div>
          <p className="text-[11px] text-[#78716C]">
            {total_attempted} of {total_questions} questions solved
          </p>
        </div>

        <div className="bg-white border border-[#E4E1DA] rounded-xl p-5 space-y-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-[#78716C]">
            GAT Accuracy
          </span>
          <div className="font-mono-exam text-2xl font-bold text-[#1E3A5F]">
            {accuracy_percentage}%
          </div>
          <p className="text-[11px] text-[#78716C]">
            {total_correct} correct first-attempts
          </p>
        </div>

        <div className="bg-white border border-[#E4E1DA] rounded-xl p-5 space-y-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-[#78716C]">
            Avg Speed per Question
          </span>
          <div className="font-mono-exam text-2xl font-bold text-[#18181B]">
            {formatDuration(avgTimeSeconds)}
          </div>
          <p className="text-[11px] text-[#78716C]">Exam target: &le; 60s per MCQ</p>
        </div>

        <div className="bg-white border border-[#E4E1DA] rounded-xl p-5 space-y-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-[#78716C]">
            Preparation Health
          </span>
          <div className="font-mono-exam text-2xl font-bold text-emerald-700">
            {accuracy_percentage >= 75 ? 'Strong' : accuracy_percentage >= 50 ? 'Moderate' : 'Developing'}
          </div>
          <p className="text-[11px] text-[#78716C]">Based on UCEED/NIFT calibration</p>
        </div>
      </section>

      {/* Subject-wise Competency Breakdown */}
      <section className="bg-white border border-[#E4E1DA] rounded-2xl p-6 sm:p-8 space-y-6 shadow-xs">
        <div>
          <h3 className="font-serif-editorial text-xl font-medium text-[#18181B]">
            Subject-wise Accuracy & Mastery
          </h3>
          <p className="text-xs text-[#78716C]">
            Evaluate your readiness in each specific GAT discipline
          </p>
        </div>

        <div className="space-y-5">
          {sections_progress.map((sec) => (
            <div key={sec.section} className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-[#18181B]">{sec.title}</span>
                <div className="flex items-center gap-3">
                  <span className="text-[#78716C]">
                    Solved: {sec.attempted_questions} / {sec.total_questions}
                  </span>
                  <span className="font-mono-exam font-bold text-[#1E3A5F]">
                    {sec.accuracy_percentage}% Accuracy
                  </span>
                </div>
              </div>

              <div className="w-full h-2.5 bg-stone-100 rounded-full overflow-hidden flex">
                <div
                  className={`h-full transition-all duration-500 ${
                    sec.accuracy_percentage >= 70
                      ? 'bg-emerald-600'
                      : sec.accuracy_percentage >= 40
                        ? 'bg-[#1E3A5F]'
                        : 'bg-amber-600'
                  }`}
                  style={{ width: `${sec.accuracy_percentage}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Actionable Strategy Recommendations */}
      <section className="bg-stone-50 border border-[#E4E1DA] rounded-2xl p-6 sm:p-8 space-y-4">
        <h3 className="font-serif-editorial text-xl font-medium text-[#18181B] flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-amber-600" />
          Recommended Exam Strategy
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs leading-relaxed text-[#44403C]">
          <div className="bg-white p-4 rounded-xl border border-[#E4E1DA] space-y-1">
            <strong className="text-[#18181B] block text-sm">Target NAT Questions First</strong>
            <p>
              Numerical Answer Type (NAT) questions carry zero negative marking in UCEED and CEED. Attempt every NAT question before moving to tricky MSQ questions.
            </p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-[#E4E1DA] space-y-1">
            <strong className="text-[#18181B] block text-sm">Beware Partial MSQ Traps</strong>
            <p>
              In Multiple Select Questions (MSQ), all correct options must be selected to earn marks. If uncertain about an option, check for extreme wording or spatial violations.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};
