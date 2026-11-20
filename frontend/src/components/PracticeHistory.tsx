import React, { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle2, Clock, Flag, Plus, Trash2 } from 'lucide-react';
import { api, formatDuration } from '../api';
import type { AttemptStatus, PracticeAttempt, SelfDifficulty, TaxonomyData, WeakArea } from '../types';

interface PracticeHistoryProps {
  taxonomy: TaxonomyData;
}

export const PracticeHistory: React.FC<PracticeHistoryProps> = ({ taxonomy }) => {
  const [attempts, setAttempts] = useState<PracticeAttempt[]>([]);
  const [weakAreas, setWeakAreas] = useState<WeakArea[]>([]);
  const [loading, setLoading] = useState(true);

  const [filterCat, setFilterCat] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  // Manual weak area flag form
  const [waType, setWaType] = useState<'category' | 'competency' | 'theme' | 'programme'>('category');
  const [waName, setWaName] = useState(taxonomy.categories[0]);
  const [waSeverity, setWaSeverity] = useState<'low' | 'medium' | 'high'>('high');
  const [waNotes, setWaNotes] = useState('');
  const [addingWa, setAddingWa] = useState(false);

  // Manual offline attempt form
  const [showManualLog, setShowManualLog] = useState(false);
  const [mTitle, setMTitle] = useState('');
  const [mCat, setMCat] = useState(taxonomy.categories[0]);
  const [mProg, setMProg] = useState(taxonomy.programme_tags[0]);
  const [mMins, setMMins] = useState(30);
  const [mDiff, setMDiff] = useState<SelfDifficulty>('Medium');
  const [mStatus, setMStatus] = useState<AttemptStatus>('completed');
  const [mNotes, setMNotes] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const [att, wa] = await Promise.all([
        api.listAttempts({
          category: filterCat || undefined,
          status: filterStatus || undefined,
        }),
        api.listWeakAreas(),
      ]);
      setAttempts(att);
      setWeakAreas(wa);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [filterCat, filterStatus]);

  const optionsForWaType = () => {
    if (waType === 'category') return taxonomy.categories;
    if (waType === 'competency') return taxonomy.competencies;
    if (waType === 'theme') return taxonomy.recurring_themes.map((t) => t.label);
    return taxonomy.programme_tags;
  };

  const handleWaTypeChange = (next: 'category' | 'competency' | 'theme' | 'programme') => {
    setWaType(next);
    if (next === 'category') setWaName(taxonomy.categories[0]);
    else if (next === 'competency') setWaName(taxonomy.competencies[0]);
    else if (next === 'theme') setWaName(taxonomy.recurring_themes[0].label);
    else setWaName(taxonomy.programme_tags[0]);
  };

  const handleAddWeakArea = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddingWa(true);
    try {
      await api.createWeakArea({
        area_type: waType,
        name: waName,
        severity: waSeverity,
        notes: waNotes.trim(),
      });
      setWaNotes('');
      await load();
    } finally {
      setAddingWa(false);
    }
  };

  const handleDeleteWeakArea = async (id: string) => {
    await api.deleteWeakArea(id);
    load();
  };

  const handleCreateManualAttempt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mTitle.trim()) return;
    await api.createAttempt({
      question_id: null,
      question_title: mTitle.trim(),
      category: mCat,
      programme_tags: mProg ? [mProg] : [],
      exam_paper_id: null,
      time_allocated_minutes: 30,
      time_spent_seconds: Math.max(60, mMins * 60),
      self_difficulty: mDiff,
      status: mStatus,
      notes: mNotes.trim(),
      rubric_revealed: true,
    });
    setMTitle('');
    setMNotes('');
    setShowManualLog(false);
    load();
  };

  const handleDeleteAttempt = async (id: string) => {
    await api.deleteAttempt(id);
    load();
  };

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-[#E4E1DA] pb-5">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#78716C]">
            Persistent Local Practice Ledger
          </p>
          <h1 className="font-serif-editorial text-3xl font-medium text-[#18181B] mt-1">
            Practice History & Weak Areas
          </h1>
          <p className="text-sm text-[#57534E] mt-1">
            Review every attempted prompt, time spent, self-assessed difficulty, and flag weak areas
            manually to steer future practice priority.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setShowManualLog((s) => !s)}
          className="inline-flex items-center gap-1.5 text-xs font-semibold px-3.5 py-2 rounded-lg bg-[#1E3A5F] text-white hover:bg-[#162C49] cursor-pointer"
        >
          <Plus className="w-3.5 h-3.5" />
          Log Offline Attempt
        </button>
      </header>

      {showManualLog && (
        <form
          onSubmit={handleCreateManualAttempt}
          className="bg-white border border-[#1E3A5F]/30 rounded-xl p-5 space-y-3"
        >
          <h3 className="text-sm font-semibold text-[#1E3A5F]">Log Pen-and-Paper Practice Attempt</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <input
              type="text"
              required
              value={mTitle}
              onChange={(e) => setMTitle(e.target.value)}
              placeholder="Question title / topic"
              className="sm:col-span-2 text-sm px-3 py-1.5 rounded-lg border border-[#D8D4CB]"
            />
            <select
              value={mCat}
              onChange={(e) => setMCat(e.target.value)}
              className="text-sm px-3 py-1.5 rounded-lg border border-[#D8D4CB] bg-white"
            >
              {taxonomy.categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
            <select
              value={mProg}
              onChange={(e) => setMProg(e.target.value)}
              className="text-sm px-3 py-1.5 rounded-lg border border-[#D8D4CB] bg-white"
            >
              {taxonomy.programme_tags.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <input
              type="number"
              min={1}
              max={240}
              value={mMins}
              onChange={(e) => setMMins(Number(e.target.value) || 30)}
              placeholder="Minutes spent"
              className="font-mono-exam text-sm px-3 py-1.5 rounded-lg border border-[#D8D4CB]"
            />
            <select
              value={mDiff}
              onChange={(e) => setMDiff(e.target.value as SelfDifficulty)}
              className="text-sm px-3 py-1.5 rounded-lg border border-[#D8D4CB] bg-white"
            >
              <option value="Easy">Easy</option>
              <option value="Medium">Medium</option>
              <option value="Hard">Hard</option>
              <option value="Very Hard">Very Hard</option>
            </select>
            <select
              value={mStatus}
              onChange={(e) => setMStatus(e.target.value as AttemptStatus)}
              className="text-sm px-3 py-1.5 rounded-lg border border-[#D8D4CB] bg-white"
            >
              <option value="completed">Completed</option>
              <option value="skipped">Skipped</option>
              <option value="in_progress">In Progress</option>
            </select>
            <input
              type="text"
              value={mNotes}
              onChange={(e) => setMNotes(e.target.value)}
              placeholder="Reflection note..."
              className="text-sm px-3 py-1.5 rounded-lg border border-[#D8D4CB]"
            />
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowManualLog(false)}
              className="text-xs px-3 py-1.5 rounded-lg border border-[#D8D4CB] text-[#57534E] cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="text-xs font-semibold px-4 py-1.5 rounded-lg bg-[#1E3A5F] text-white cursor-pointer"
            >
              Save Attempt
            </button>
          </div>
        </form>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        {/* Practice Attempt History Table */}
        <section className="xl:col-span-8 bg-white border border-[#E4E1DA] rounded-xl overflow-hidden">
          <div className="p-4 border-b border-[#E4E1DA] flex flex-wrap items-center justify-between gap-3">
            <h2 className="font-serif-editorial text-xl font-medium">
              Logged Attempts ({attempts.length})
            </h2>
            <div className="flex items-center gap-2">
              <select
                value={filterCat}
                onChange={(e) => setFilterCat(e.target.value)}
                className="text-xs px-2.5 py-1.5 rounded-lg border border-[#D8D4CB] bg-white"
              >
                <option value="">All Categories</option>
                {taxonomy.categories.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="text-xs px-2.5 py-1.5 rounded-lg border border-[#D8D4CB] bg-white"
              >
                <option value="">All Statuses</option>
                <option value="completed">Completed</option>
                <option value="skipped">Skipped</option>
                <option value="in_progress">In Progress</option>
              </select>
            </div>
          </div>

          {loading ? (
            <div className="p-10 text-center text-xs text-[#78716C]">Loading practice history...</div>
          ) : attempts.length === 0 ? (
            <div className="p-12 text-center space-y-1.5">
              <p className="text-sm text-[#57534E]">No practice attempts logged yet.</p>
              <p className="text-xs text-[#78716C]">
                Complete a generated prompt or mock exam, or log an offline sketch session above.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-[#ECEAE4]">
              {attempts.map((a) => (
                <div key={a.id} className="p-4 flex items-start justify-between gap-4">
                  <div className="space-y-1.5 min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-semibold text-[#18181B]">{a.question_title}</span>
                      <span
                        className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded ${
                          a.status === 'completed'
                            ? 'bg-emerald-50 text-emerald-800'
                            : a.status === 'skipped'
                              ? 'bg-rose-50 text-rose-800'
                              : 'bg-amber-50 text-amber-800'
                        }`}
                      >
                        {a.status === 'completed' ? (
                          <CheckCircle2 className="w-3 h-3" />
                        ) : (
                          <AlertCircle className="w-3 h-3" />
                        )}
                        {a.status}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 text-xs text-[#78716C]">
                      <span className="px-2 py-0.5 rounded bg-[#FAF9F6] border border-[#E4E1DA] text-[#44403C]">
                        {a.category}
                      </span>
                      {a.programme_tags.slice(0, 2).map((p) => (
                        <span key={p} className="px-2 py-0.5 rounded bg-stone-100 text-stone-700">
                          {p}
                        </span>
                      ))}
                      <span className="inline-flex items-center gap-1 font-mono-exam">
                        <Clock className="w-3 h-3" />
                        {formatDuration(a.time_spent_seconds)} / {a.time_allocated_minutes}m
                      </span>
                      {a.self_difficulty && <span>• Felt: {a.self_difficulty}</span>}
                      <span>• {new Date(a.attempted_at).toLocaleDateString()}</span>
                    </div>

                    {a.notes && <p className="text-xs text-[#57534E] italic">“{a.notes}”</p>}
                  </div>

                  <button
                    type="button"
                    onClick={() => handleDeleteAttempt(a.id)}
                    className="p-1.5 rounded text-[#78716C] hover:text-rose-700 hover:bg-rose-50 cursor-pointer shrink-0"
                    title="Delete attempt"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Manual Weak Areas Identification Panel */}
        <section className="xl:col-span-4 bg-white border border-[#E4E1DA] rounded-xl p-5 space-y-5">
          <div>
            <div className="flex items-center gap-2">
              <Flag className="w-4 h-4 text-rose-700" />
              <h2 className="font-serif-editorial text-xl font-medium">My Weak Areas</h2>
            </div>
            <p className="text-xs text-[#78716C] mt-1">
              Manually flag categories, competencies, or themes you struggle with. Flagged areas receive
              higher practice-gap priority automatically.
            </p>
          </div>

          <form onSubmit={handleAddWeakArea} className="space-y-3 border-b border-[#E4E1DA] pb-5">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-[11px] font-semibold uppercase text-[#78716C] mb-1">
                  Area Type
                </label>
                <select
                  value={waType}
                  onChange={(e) =>
                    handleWaTypeChange(e.target.value as 'category' | 'competency' | 'theme' | 'programme')
                  }
                  className="w-full text-xs px-2.5 py-2 rounded-lg border border-[#D8D4CB] bg-white"
                >
                  <option value="category">Category</option>
                  <option value="competency">Competency</option>
                  <option value="theme">Theme</option>
                  <option value="programme">Programme</option>
                </select>
              </div>
              <div>
                <label className="block text-[11px] font-semibold uppercase text-[#78716C] mb-1">
                  Severity
                </label>
                <select
                  value={waSeverity}
                  onChange={(e) => setWaSeverity(e.target.value as 'low' | 'medium' | 'high')}
                  className="w-full text-xs px-2.5 py-2 rounded-lg border border-[#D8D4CB] bg-white"
                >
                  <option value="high">High priority</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold uppercase text-[#78716C] mb-1">
                Specific Area
              </label>
              <select
                value={waName}
                onChange={(e) => setWaName(e.target.value)}
                className="w-full text-xs px-2.5 py-2 rounded-lg border border-[#D8D4CB] bg-white"
              >
                {optionsForWaType().map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            </div>

            <input
              type="text"
              value={waNotes}
              onChange={(e) => setWaNotes(e.target.value)}
              placeholder="Note (e.g., struggle with 3-point perspective in 30m)"
              className="w-full text-xs px-3 py-2 rounded-lg border border-[#D8D4CB]"
            />

            <button
              type="submit"
              disabled={addingWa}
              className="w-full text-xs font-semibold py-2 rounded-lg bg-[#18181B] text-white hover:bg-[#27272A] cursor-pointer"
            >
              {addingWa ? 'Flagging...' : 'Flag Weak Area'}
            </button>
          </form>

          <div className="space-y-2">
            {weakAreas.length === 0 ? (
              <p className="text-xs text-[#78716C] italic">No manual weak areas flagged yet.</p>
            ) : (
              weakAreas.map((w) => (
                <div
                  key={w.id}
                  className="p-3 rounded-lg border border-[#ECEAE4] bg-[#FAF9F6] flex items-start justify-between gap-2"
                >
                  <div className="space-y-0.5 text-xs">
                    <div className="flex items-center gap-1.5">
                      <span className="font-semibold text-[#18181B]">{w.name}</span>
                      <span
                        className={`text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded ${
                          w.severity === 'high'
                            ? 'bg-rose-100 text-rose-800'
                            : w.severity === 'medium'
                              ? 'bg-amber-100 text-amber-900'
                              : 'bg-stone-200 text-stone-700'
                        }`}
                      >
                        {w.severity}
                      </span>
                    </div>
                    <div className="text-[11px] text-[#78716C] uppercase">{w.area_type}</div>
                    {w.notes && <p className="text-[#44403C]">{w.notes}</p>}
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDeleteWeakArea(w.id)}
                    className="p-1 text-[#78716C] hover:text-rose-700 cursor-pointer"
                    title="Remove flag"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
};
