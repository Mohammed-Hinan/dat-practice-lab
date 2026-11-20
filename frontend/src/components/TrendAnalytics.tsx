import React, { useEffect, useState } from 'react';
import { AlertTriangle, ArrowRight, Info, Layers, Sliders } from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { api } from '../api';
import type { AnalyticsOverview, GenerationMode, NavSection } from '../types';

interface TrendAnalyticsProps {
  onNavigate: (
    section: NavSection,
    preset?: { mode?: GenerationMode; categories?: string[]; themeId?: string | null }
  ) => void;
}

export const TrendAnalytics: React.FC<TrendAnalyticsProps> = ({ onNavigate }) => {
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        setData(await api.getAnalyticsOverview());
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load trend analytics.');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-8 w-72 bg-stone-200 rounded" />
        <div className="h-56 bg-white border border-[#E4E1DA] rounded-xl" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 bg-white border border-rose-200 rounded-xl text-sm text-rose-800">
        {error || 'Could not compute analytics.'}
      </div>
    );
  }

  const confBadge =
    data.confidence_level === 'High'
      ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
      : data.confidence_level === 'Medium'
        ? 'bg-sky-50 text-sky-900 border-sky-200'
        : 'bg-amber-50 text-amber-900 border-amber-200';

  const w = data.scoring_weights;

  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-[#E4E1DA] pb-5">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#78716C]">
            Transparent Historical Evidence & Practice-Priority Model
          </p>
          <h1 className="font-serif-editorial text-3xl font-medium text-[#18181B] mt-1">
            Trends & Practice Priority
          </h1>
          <p className="text-sm text-[#57534E] mt-1 max-w-2xl">
            Practice-priority scores guide study focus using historical recurrence, recency, cross-programme
            relevance, your preparation profiles, and practice gaps. They are not exam appearance guarantees.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className={`text-xs font-semibold px-3 py-1.5 rounded-lg border ${confBadge}`}>
            Dataset Confidence: {data.confidence_level}
          </span>
        </div>
      </header>



      {/* Evidence Transparency Strip */}
      <section className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        <div className="bg-white border border-[#E4E1DA] rounded-xl p-4">
          <div className="text-[11px] uppercase tracking-wider text-[#78716C]">Historical Records</div>
          <div className="font-mono-exam text-2xl font-semibold mt-1">
            {data.dataset_summary.total_records}
          </div>
        </div>
        <div className="bg-white border border-[#E4E1DA] rounded-xl p-4">
          <div className="text-[11px] uppercase tracking-wider text-[#78716C]">Dated Records</div>
          <div className="font-mono-exam text-2xl font-semibold mt-1">
            {data.dataset_summary.records_with_known_year}
          </div>
        </div>
        <div className="bg-white border border-[#E4E1DA] rounded-xl p-4">
          <div className="text-[11px] uppercase tracking-wider text-[#78716C]">Unknown Year</div>
          <div className="font-mono-exam text-2xl font-semibold mt-1">
            {data.dataset_summary.unknown_year_records}
          </div>
        </div>
        <div className="bg-white border border-[#E4E1DA] rounded-xl p-4">
          <div className="text-[11px] uppercase tracking-wider text-[#78716C]">Distinct Years</div>
          <div className="font-mono-exam text-2xl font-semibold mt-1">
            {data.dataset_summary.distinct_years}
          </div>
        </div>
        <div className="bg-white border border-[#E4E1DA] rounded-xl p-4">
          <div className="text-[11px] uppercase tracking-wider text-[#78716C]">Year Span</div>
          <div className="font-mono-exam text-xl font-semibold mt-1">
            {data.dataset_summary.year_range
              ? `${data.dataset_summary.year_range[0]}–${data.dataset_summary.year_range[1]}`
              : '—'}
          </div>
        </div>
      </section>

      {/* Scoring Formula Summary */}
      <section className="bg-[#FAF9F6] border border-[#E4E1DA] rounded-xl p-4 flex flex-wrap items-center justify-between gap-3 text-xs text-[#44403C]">
        <div className="flex items-center gap-2 font-medium text-[#18181B]">
          <Info className="w-4 h-4 text-[#1E3A5F]" />
          Active Practice-Priority Weights:
        </div>
        <div className="flex flex-wrap gap-2 font-mono-exam">
          <span className="px-2 py-0.5 rounded bg-white border border-[#E4E1DA]">
            Multi-year {w.multi_year_recurrence}%
          </span>
          <span className="px-2 py-0.5 rounded bg-white border border-[#E4E1DA]">
            Recency {w.recency}%
          </span>
          <span className="px-2 py-0.5 rounded bg-white border border-[#E4E1DA]">
            Cross-relevance {w.cross_relevance}%
          </span>
          <span className="px-2 py-0.5 rounded bg-white border border-[#E4E1DA]">
            Profile fit {w.profile_relevance}%
          </span>
          <span className="px-2 py-0.5 rounded bg-white border border-[#E4E1DA]">
            Practice gaps {w.practice_gaps}%
          </span>
        </div>
      </section>

      {/* Theme Priorities: Evidence vs Interpretation */}
      <section className="space-y-4">
        <div>
          <h2 className="font-serif-editorial text-2xl font-medium text-[#18181B]">
            Recurring Themes & Practice Priority
          </h2>
          <p className="text-xs text-[#78716C] mt-0.5">
            Each theme clearly separates observed historical evidence from profile-adjusted coaching
            interpretation.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {data.theme_priorities.map((t) => (
            <div key={t.theme_id} className="bg-white border border-[#E4E1DA] rounded-xl p-5 space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-serif-editorial text-lg font-medium text-[#18181B]">{t.label}</h3>
                  <p className="text-xs text-[#78716C] mt-0.5">{t.description}</p>
                </div>
                <div className="text-right shrink-0">
                  <div className="font-mono-exam text-lg font-semibold text-[#1E3A5F]">
                    {t.practice_priority_score.toFixed(0)}/100
                  </div>
                  <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-stone-100 text-stone-700">
                    Band {t.priority_band}/5 • {t.confidence}
                  </span>
                </div>
              </div>

              {/* Factor breakdown bars */}
              <div className="grid grid-cols-5 gap-1.5 pt-1 text-[10px] font-mono-exam text-[#57534E]">
                {[
                  ['Recurrence', t.factor_breakdown.multi_year_recurrence],
                  ['Recency', t.factor_breakdown.recency],
                  ['Cross', t.factor_breakdown.cross_relevance],
                  ['Profile', t.factor_breakdown.profile_relevance],
                  ['Gaps', t.factor_breakdown.practice_gaps],
                ].map(([label, val]) => (
                  <div key={label as string} className="bg-[#FAF9F6] border border-[#ECEAE4] rounded p-1.5">
                    <div className="truncate">{label}</div>
                    <div className="font-semibold text-[#18181B]">{Number(val).toFixed(0)}</div>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs pt-1">
                <div className="p-2.5 rounded-lg bg-[#FAF9F6] border border-[#ECEAE4]">
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-[#57534E] mb-1">
                    Historical Evidence
                  </div>
                  <p className="text-[#27272A] leading-snug">{t.historical_evidence}</p>
                </div>
                <div className="p-2.5 rounded-lg bg-[#F7F9FC] border border-[#1E3A5F]/15">
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-[#1E3A5F] mb-1">
                    Model Interpretation
                  </div>
                  <p className="text-[#27272A] leading-snug">{t.model_interpretation}</p>
                </div>
              </div>

              <div className="flex items-center justify-between pt-1">
                <div className="flex flex-wrap gap-1">
                  {t.related_categories.map((c) => (
                    <span
                      key={c}
                      className="text-[11px] px-2 py-0.5 rounded bg-stone-100 text-stone-700"
                    >
                      {c}
                    </span>
                  ))}
                </div>
                <button
                  type="button"
                  onClick={() =>
                    onNavigate('generate', {
                      mode: 'likely_exam',
                      categories: t.related_categories.slice(0, 1),
                      themeId: t.theme_id,
                    })
                  }
                  className="inline-flex items-center gap-1 text-xs font-medium text-[#1E3A5F] hover:underline cursor-pointer"
                >
                  Practise Theme
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Meaningful Charts: Category Frequency & Year Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-4">
          <div>
            <h2 className="font-serif-editorial text-xl font-medium">
              Historical Bank Category Distribution
            </h2>
            <p className="text-xs text-[#78716C] mt-0.5">
              Count of imported historical questions per category ({data.dataset_summary.total_records}{' '}
              total).
            </p>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={data.category_frequency}
                layout="vertical"
                margin={{ top: 4, right: 20, left: 10, bottom: 4 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#ECEAE4" horizontal={false} />
                <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11, fill: '#78716C' }} />
                <YAxis type="category" dataKey="category" width={132} tick={{ fontSize: 12, fill: '#27272A' }} />
                <Tooltip />
                <Bar dataKey="count" name="Historical Prompts" fill="#1E3A5F" radius={[0, 4, 4, 0]} barSize={16} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-4">
          <div>
            <h2 className="font-serif-editorial text-xl font-medium">Year-Wise Record Volume</h2>
            <p className="text-xs text-[#78716C] mt-0.5">
              Distribution of imported prompts across known examination years (plus Unknown year).
            </p>
          </div>
          {data.year_trends.length === 0 ? (
            <div className="h-64 flex items-center justify-center border border-dashed border-[#D8D4CB] rounded-lg text-xs text-[#78716C]">
              Import historical questions to populate year-wise trends.
            </div>
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.year_trends} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ECEAE4" vertical={false} />
                  <XAxis dataKey="year" tick={{ fontSize: 11, fill: '#57534E' }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#78716C' }} />
                  <Tooltip />
                  <Bar dataKey="total" name="Questions" fill="#475569" radius={[4, 4, 0, 0]} barSize={28} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </section>
      </div>

      {/* Category Practice Balance + Unrepresented Topics */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <section className="lg:col-span-7 bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-[#1E3A5F]" />
            <h2 className="font-serif-editorial text-xl font-medium">
              Category Practice Balance & Weighted Share
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-[#FAF9F6] text-left uppercase tracking-wider text-[#57534E]">
                <tr>
                  <th className="px-3 py-2.5">Category</th>
                  <th className="px-3 py-2.5 text-right">Bank</th>
                  <th className="px-3 py-2.5 text-right">Attempted</th>
                  <th className="px-3 py-2.5 text-right">Balanced</th>
                  <th className="px-3 py-2.5 text-right">Weighted</th>
                  <th className="px-3 py-2.5 text-right">Priority</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#ECEAE4]">
                {data.category_priorities.map((c) => (
                  <tr key={c.category}>
                    <td className="px-3 py-2.5 font-medium text-[#18181B]">
                      {c.category}
                      {c.is_under_practised && (
                        <span className="ml-1.5 text-[10px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
                          Low practice
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2.5 text-right font-mono-exam">{c.historical_count}</td>
                    <td className="px-3 py-2.5 text-right font-mono-exam">{c.practice_attempts}</td>
                    <td className="px-3 py-2.5 text-right font-mono-exam text-[#78716C]">
                      {c.balanced_weight}%
                    </td>
                    <td className="px-3 py-2.5 text-right font-mono-exam text-[#1E3A5F] font-medium">
                      {c.weighted_practice_share}%
                    </td>
                    <td className="px-3 py-2.5 text-right font-mono-exam font-semibold">
                      {c.practice_priority_score.toFixed(0)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="lg:col-span-5 bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-4">
          <h2 className="font-serif-editorial text-xl font-medium">
            Topics Missing From Your Bank ({data.unrepresented_topics.length})
          </h2>
          {data.unrepresented_topics.length === 0 ? (
            <p className="text-xs text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-lg p-3">
              All 7 categories and 10 recurring themes are represented in your imported historical dataset.
            </p>
          ) : (
            <div className="max-h-64 overflow-y-auto divide-y divide-[#ECEAE4] text-xs">
              {data.unrepresented_topics.map((u, idx) => (
                <div key={idx} className="py-2.5">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-stone-100 text-stone-700">
                      {u.type}
                    </span>
                    <span className="font-medium text-[#18181B]">{u.name}</span>
                  </div>
                  <p className="text-[#78716C] mt-0.5">{u.detail}</p>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      {/* Reference Taxonomy Context (Dnerd Studio disclaimer) */}
      <section className="bg-[#FAF9F6] border border-[#E4E1DA] rounded-xl p-5 space-y-2 text-xs text-[#57534E]">
        <div className="font-semibold text-[#18181B]">
          Reference Collection Note ({data.dnerd_reference_note.total_prompts_observed} Observed Prompts •{' '}
          {data.dnerd_reference_note.default_prompt_time_minutes}-min default)
        </div>
        <p className="leading-relaxed">{data.dnerd_reference_note.disclaimer}</p>
        <div className="flex flex-wrap gap-2 pt-1 font-mono-exam text-[11px]">
          {Object.entries(data.dnerd_reference_note.website_tag_counts).map(([k, v]) => (
            <span key={k} className="px-2 py-0.5 rounded bg-white border border-[#E4E1DA]">
              {k}: {v}
            </span>
          ))}
        </div>
      </section>
    </div>
  );
};
