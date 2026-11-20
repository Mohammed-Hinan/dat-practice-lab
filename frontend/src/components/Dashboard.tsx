import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Bookmark,
  Clock,
  Layers,
  Target,
  TrendingUp,
} from 'lucide-react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api, formatDuration } from '../api';
import type { DashboardData, GeneratedQuestion, GenerationMode, NavSection } from '../types';
import { QuestionDisplay } from './QuestionDisplay';

interface DashboardProps {
  onNavigate: (
    section: NavSection,
    preset?: { mode?: GenerationMode; categories?: string[]; themeId?: string | null }
  ) => void;
  llmConnected: boolean;
}

export const Dashboard: React.FC<DashboardProps> = ({ onNavigate, llmConnected }) => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeQuestion, setActiveQuestion] = useState<GeneratedQuestion | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getDashboard();
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-64 bg-stone-200 rounded" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="h-24 bg-white border border-[#E4E1DA] rounded-xl" />
          ))}
        </div>
        <div className="h-64 bg-white border border-[#E4E1DA] rounded-xl" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 bg-white border border-rose-200 rounded-xl text-sm text-rose-800">
        {error || 'Could not load dashboard metrics.'}
      </div>
    );
  }

  if (activeQuestion) {
    return (
      <div className="space-y-4">
        <button
          type="button"
          onClick={() => {
            setActiveQuestion(null);
            load();
          }}
          className="text-xs font-medium text-[#1E3A5F] hover:underline cursor-pointer"
        >
          ← Back to Dashboard
        </button>
        <QuestionDisplay
          question={activeQuestion}
          onSaveToggle={(updated) => setActiveQuestion(updated)}
          onAttemptSaved={load}
        />
      </div>
    );
  }

  const totalMinutes = Math.round(data.stats.total_practice_seconds / 60);

  return (
    <div className="space-y-8">
      {/* Header */}
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-[#E4E1DA] pb-5">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#78716C]">
            NID M.Des DAT Prelims • 2027 Preparation Studio
          </p>
          <h1 className="font-serif-editorial text-3xl font-medium text-[#18181B] mt-1">
            Practice Overview
          </h1>
        </div>
      </header>

      {/* Low Confidence / Offline Notices */}
      {!llmConnected && (
        <div className="rounded-xl border border-amber-300 bg-amber-50/70 px-5 py-3.5 flex flex-wrap items-center justify-between gap-3 text-xs text-amber-950">
          <div className="flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              AI service is currently reconnecting to the cloud. You can continue reviewing saved questions,
              historical papers, inspecting trends, and logging practice.
            </p>
          </div>
        </div>
      )}

      {/* Key Metrics */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-[#E4E1DA] rounded-xl p-5">
          <div className="flex items-center justify-between text-[#78716C] text-xs font-medium">
            <span>Questions Attempted</span>
            <Target className="w-4 h-4" />
          </div>
          <div className="font-mono-exam text-3xl font-semibold text-[#18181B] mt-2">
            {data.stats.total_attempts}
          </div>
          <p className="text-xs text-[#78716C] mt-1">
            {data.stats.completed_attempts} completed • {data.stats.skipped_attempts} skipped
          </p>
        </div>

        <div className="bg-white border border-[#E4E1DA] rounded-xl p-5">
          <div className="flex items-center justify-between text-[#78716C] text-xs font-medium">
            <span>Time Practised</span>
            <Clock className="w-4 h-4" />
          </div>
          <div className="font-mono-exam text-3xl font-semibold text-[#18181B] mt-2">
            {totalMinutes >= 60 ? `${(totalMinutes / 60).toFixed(1)}h` : `${totalMinutes}m`}
          </div>
          <p className="text-xs text-[#78716C] mt-1">
            {formatDuration(data.stats.total_practice_seconds)} total logged
          </p>
        </div>

        <div className="bg-white border border-[#E4E1DA] rounded-xl p-5">
          <div className="flex items-center justify-between text-[#78716C] text-xs font-medium">
            <span>Category Coverage</span>
            <Layers className="w-4 h-4" />
          </div>
          <div className="font-mono-exam text-3xl font-semibold text-[#18181B] mt-2">
            {data.stats.categories_covered}
            <span className="text-base font-normal text-[#78716C]">/{data.stats.total_categories}</span>
          </div>
          <p className="text-xs text-[#78716C] mt-1">
            {data.stats.exam_papers_count} mock paper(s) created
          </p>
        </div>

        <div className="bg-white border border-[#E4E1DA] rounded-xl p-5">
          <div className="flex items-center justify-between text-[#78716C] text-xs font-medium">
            <span>Local Knowledge Base</span>
            <Bookmark className="w-4 h-4" />
          </div>
          <div className="font-mono-exam text-3xl font-semibold text-[#18181B] mt-2">
            {data.stats.historical_questions_count}
          </div>
          <p className="text-xs text-[#78716C] mt-1">
            historical prompts • {data.stats.saved_questions_count} saved
          </p>
        </div>
      </section>

      {/* Category Coverage Chart + Under-Practised List */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <section className="lg:col-span-7 bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-serif-editorial text-xl font-medium text-[#18181B]">
                Category Coverage (All {data.stats.total_categories} Types)
              </h2>
              <p className="text-xs text-[#78716C] mt-0.5">
                Completed practice attempts across all {data.stats.total_categories} DAT categories including Logos, Symbols &amp; Signs.
              </p>
            </div>
            <button
              type="button"
              onClick={() => onNavigate('generate', { mode: 'balanced_random' })}
              className="text-xs font-medium text-[#1E3A5F] hover:underline cursor-pointer"
            >
              Balanced Random →
            </button>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={data.category_coverage}
                layout="vertical"
                margin={{ top: 4, right: 20, left: 10, bottom: 4 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#ECEAE4" horizontal={false} />
                <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11, fill: '#78716C' }} />
                <YAxis
                  type="category"
                  dataKey="category"
                  width={132}
                  tick={{ fontSize: 12, fill: '#27272A' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#E4E1DA',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="attempted" name="Completed Attempts" fill="#1E3A5F" radius={[0, 4, 4, 0]} barSize={16} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="lg:col-span-5 bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-serif-editorial text-xl font-medium text-[#18181B]">
                Focus & Under-Practised Areas
              </h2>
              <p className="text-xs text-[#78716C] mt-0.5">
                Categories needing attention based on practice gaps and manual flags.
              </p>
            </div>
          </div>

          <div className="divide-y divide-[#ECEAE4]">
            {data.weak_and_under_practised.map((item) => (
              <div key={item.category} className="py-3 flex items-start justify-between gap-3">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-[#18181B]">{item.category}</span>
                    {item.is_flagged_weak && (
                      <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-200">
                        Weak Flag
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-[#78716C] leading-snug">{item.reason}</p>
                </div>
                <button
                  type="button"
                  onClick={() =>
                    onNavigate('generate', { mode: 'category', categories: [item.category] })
                  }
                  className="text-xs font-medium px-2.5 py-1 rounded border border-[#D8D4CB] text-[#1E3A5F] hover:bg-[#1E3A5F]/5 shrink-0 cursor-pointer"
                >
                  Practise
                </button>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Historical Topic Trends + Recent Generated Questions */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <section className="lg:col-span-6 bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-[#1E3A5F]" />
              <h2 className="font-serif-editorial text-xl font-medium text-[#18181B]">
                Top Practice-Priority Themes
              </h2>
            </div>
            <button
              type="button"
              onClick={() => onNavigate('trends')}
              className="text-xs font-medium text-[#1E3A5F] hover:underline cursor-pointer"
            >
              Full Analysis →
            </button>
          </div>

          <div className="space-y-3">
            {data.top_themes.map((t) => (
              <div key={t.theme_id} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-[#18181B]">{t.label}</span>
                  <span className="font-mono-exam text-[#57534E]">
                    {t.practice_priority_score.toFixed(0)}/100 • {t.confidence} conf.
                  </span>
                </div>
                <div className="h-1.5 bg-stone-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[#1E3A5F]"
                    style={{ width: `${Math.min(100, t.practice_priority_score)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="lg:col-span-6 bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-serif-editorial text-xl font-medium text-[#18181B]">
              Recent Generated Questions
            </h2>
            <button
              type="button"
              onClick={() => onNavigate('generate')}
              className="text-xs font-medium text-[#1E3A5F] hover:underline cursor-pointer"
            >
              Generate New →
            </button>
          </div>

          {data.recent_questions.length === 0 ? (
            <div className="py-10 text-center space-y-2 border border-dashed border-[#D8D4CB] rounded-lg">
              <p className="text-sm text-[#57534E]">No questions generated yet.</p>
              <button
                type="button"
                onClick={() => onNavigate('generate')}
                className="text-xs font-semibold px-3.5 py-1.5 rounded-lg bg-[#1E3A5F] text-white cursor-pointer"
              >
                Generate First Question
              </button>
            </div>
          ) : (
            <div className="divide-y divide-[#ECEAE4]">
              {data.recent_questions.map((q) => (
                <button
                  key={q.id}
                  type="button"
                  onClick={() => setActiveQuestion(q)}
                  className="w-full text-left py-3 hover:bg-[#FAF9F6] px-2 -mx-2 rounded-lg transition-colors flex items-start justify-between gap-3 cursor-pointer"
                >
                  <div className="space-y-0.5 min-w-0">
                    <div className="text-sm font-medium text-[#18181B] truncate">{q.title}</div>
                    <div className="text-xs text-[#78716C]">
                      {q.category} • {q.time_minutes} min • {q.difficulty}
                    </div>
                  </div>
                  {q.is_saved && (
                    <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-[#1E3A5F]/10 text-[#1E3A5F] shrink-0">
                      Saved
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
};
