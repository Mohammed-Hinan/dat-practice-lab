import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  Download,
  Edit3,
  FileUp,
  Plus,
  Search,
  Trash2,
  Upload,
  X,
} from 'lucide-react';
import { api } from '../api';
import type { HistoricalQuestion, ParsedQuestionDraft, TaxonomyData } from '../types';

interface QuestionBankProps {
  taxonomy: TaxonomyData;
}

const SAMPLE_CSV_TEMPLATE = `title,prompt_text,year,category,programme_tags,marks,time_minutes,source,notes
Example Public Queue Audit,"Observe a crowded public hospital outpatient waiting area during peak morning hours. Identify five distinct challenges faced by patients, caregivers, and staff. Prioritise one problem and propose an annotated intervention.",2024,Problem identification,"Universal Design; Strategic Design Management",20,30,"Personal Archive","Replace with your own verified past-paper prompts"
Example Five-Frame Visual Story,"Illustrate a five-frame wordless storyboard showing an unexpected interaction between a street bookseller and a curious child during sudden monsoon rain.",,Storyboard,"Animation Film Design; Film & Video Communication",,30,"Memory Recall","Year and marks left blank because unknown"`;

export const QuestionBank: React.FC<QuestionBankProps> = ({ taxonomy }) => {
  const [tab, setTab] = useState<'browse' | 'manual' | 'import'>('browse');
  const [records, setRecords] = useState<HistoricalQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterCat, setFilterCat] = useState('');

  // Manual add / edit state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [mTitle, setMTitle] = useState('');
  const [mPrompt, setMPrompt] = useState('');
  const [mYear, setMYear] = useState('');
  const [mCategory, setMCategory] = useState('Design aptitude');
  const [mProgrammes, setMProgrammes] = useState<string[]>([]);
  const [mMarks, setMMarks] = useState('');
  const [mTime, setMTime] = useState('');
  const [mSource, setMSource] = useState('');
  const [mNotes, setMNotes] = useState('');
  const [savingManual, setSavingManual] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  // Bulk / CSV / JSON Import state
  const [importFormat, setImportFormat] = useState<'text' | 'csv' | 'json'>('text');
  const [importContent, setImportContent] = useState('');
  const [importSource, setImportSource] = useState('');
  const [parsing, setParsing] = useState(false);
  const [parseErrors, setParseErrors] = useState<string[]>([]);
  const [drafts, setDrafts] = useState<ParsedQuestionDraft[]>([]);
  const [committing, setCommitting] = useState(false);

  const loadRecords = async () => {
    setLoading(true);
    try {
      const list = await api.listHistorical({
        category: filterCat || undefined,
        search: search.trim() || undefined,
      });
      setRecords(list);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRecords();
  }, [filterCat]);

  const resetManualForm = () => {
    setEditingId(null);
    setMTitle('');
    setMPrompt('');
    setMYear('');
    setMCategory('Design aptitude');
    setMProgrammes([]);
    setMMarks('');
    setMTime('');
    setMSource('');
    setMNotes('');
  };

  const startEdit = (rec: HistoricalQuestion) => {
    setEditingId(rec.id);
    setMTitle(rec.title || '');
    setMPrompt(rec.prompt_text);
    setMYear(rec.year != null ? String(rec.year) : '');
    setMCategory(rec.category);
    setMProgrammes(rec.programme_tags || []);
    setMMarks(rec.marks != null ? String(rec.marks) : '');
    setMTime(rec.time_minutes != null ? String(rec.time_minutes) : '');
    setMSource(rec.source || '');
    setMNotes(rec.notes || '');
    setTab('manual');
  };

  const handleSaveManual = async (e: React.FormEvent) => {
    e.preventDefault();
    if (mPrompt.trim().length < 10) {
      setFeedback('Prompt text must be at least 10 characters.');
      return;
    }
    setSavingManual(true);
    setFeedback(null);
    try {
      const payload = {
        title: mTitle.trim() || null,
        prompt_text: mPrompt.trim(),
        year: mYear.trim() ? parseInt(mYear.trim(), 10) : null,
        category: mCategory,
        programme_tags: mProgrammes,
        marks: mMarks.trim() ? parseInt(mMarks.trim(), 10) : null,
        time_minutes: mTime.trim() ? parseInt(mTime.trim(), 10) : null,
        source: mSource.trim() || null,
        notes: mNotes.trim() || null,
      };
      if (editingId) {
        await api.updateHistorical(editingId, payload);
        setFeedback('Historical question updated.');
      } else {
        await api.createHistorical(payload);
        setFeedback('Historical question added to local SQLite bank.');
      }
      resetManualForm();
      await loadRecords();
      setTab('browse');
    } catch (err) {
      setFeedback(err instanceof Error ? err.message : 'Save failed.');
    } finally {
      setSavingManual(false);
    }
  };

  const handleDelete = async (id: string) => {
    await api.deleteHistorical(id);
    loadRecords();
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.name.endsWith('.csv')) setImportFormat('csv');
    else if (file.name.endsWith('.json')) setImportFormat('json');
    else setImportFormat('text');

    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        setImportContent(reader.result);
      }
    };
    reader.readAsText(file);
  };

  const handleParseBulk = async () => {
    if (!importContent.trim()) return;
    setParsing(true);
    setParseErrors([]);
    try {
      const res = await api.parseHistoricalBulk({
        format: importFormat,
        content: importContent,
        default_source: importSource.trim() || undefined,
      });
      setDrafts(res.drafts);
      setParseErrors(res.errors);
    } catch (err) {
      setParseErrors([err instanceof Error ? err.message : 'Failed to parse import content.']);
    } finally {
      setParsing(false);
    }
  };

  const handleCommitDrafts = async () => {
    if (drafts.length === 0) return;
    setCommitting(true);
    try {
      const saved = await api.importHistoricalDrafts(drafts);
      setDrafts([]);
      setImportContent('');
      setFeedback(`Imported ${saved.length} historical question(s) into SQLite.`);
      await loadRecords();
      setTab('browse');
    } catch (err) {
      setParseErrors([err instanceof Error ? err.message : 'Failed to save imported questions.']);
    } finally {
      setCommitting(false);
    }
  };

  const downloadCsvTemplate = () => {
    const blob = new Blob([SAMPLE_CSV_TEMPLATE], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'dat_historical_import_template.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-[#E4E1DA] pb-5">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#78716C]">
            Evidence-Grounded Reference Repository
          </p>
          <h1 className="font-serif-editorial text-3xl font-medium text-[#18181B] mt-1">
            Historical Question Bank
          </h1>
          <p className="text-sm text-[#57534E] mt-1 max-w-2xl">
            Import your own NID M.Des past questions via manual entry, bulk text, CSV, or JSON. Unknown
            years, marks, and sources are preserved honestly as “Unknown”.
          </p>
        </div>

        <div className="inline-flex rounded-lg border border-[#D8D4CB] bg-white p-1">
          {[
            { id: 'browse', label: `Bank (${records.length})` },
            { id: 'manual', label: editingId ? 'Edit Question' : 'Manual Entry' },
            { id: 'import', label: 'Bulk / CSV / JSON Import' },
          ].map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id as 'browse' | 'manual' | 'import')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors cursor-pointer ${
                tab === t.id ? 'bg-[#1E3A5F] text-white' : 'text-[#57534E] hover:text-[#18181B]'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </header>

      {feedback && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-xs text-emerald-900 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-700" />
            {feedback}
          </span>
          <button type="button" onClick={() => setFeedback(null)} className="cursor-pointer">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* BROWSE TAB */}
      {tab === 'browse' && (
        <div className="space-y-4">
          <div className="bg-white border border-[#E4E1DA] rounded-xl p-4 flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2 flex-1">
              <div className="relative flex-1 min-w-[200px] max-w-sm">
                <Search className="w-4 h-4 text-[#78716C] absolute left-3 top-2.5" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && loadRecords()}
                  placeholder="Search prompts or sources..."
                  className="w-full pl-9 pr-3 py-1.5 text-sm rounded-lg border border-[#D8D4CB]"
                />
              </div>
              <select
                value={filterCat}
                onChange={(e) => setFilterCat(e.target.value)}
                className="text-xs px-3 py-2 rounded-lg border border-[#D8D4CB] bg-white"
              >
                <option value="">All 7 categories</option>
                {taxonomy.categories.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={loadRecords}
                className="text-xs font-medium px-3 py-2 rounded-lg border border-[#D8D4CB] hover:bg-stone-50 cursor-pointer"
              >
                Filter
              </button>
            </div>

            <div className="flex items-center gap-2">
              <a
                href="/api/historical/export?format=csv"
                className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-[#D8D4CB] bg-white text-[#44403C] hover:bg-stone-50"
              >
                <Download className="w-3.5 h-3.5" />
                Export CSV
              </a>
              <button
                type="button"
                onClick={() => {
                  resetManualForm();
                  setTab('manual');
                }}
                className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-[#1E3A5F] text-white hover:bg-[#162C49] cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                Add Question
              </button>
            </div>
          </div>

          {loading ? (
            <div className="bg-white border border-[#E4E1DA] rounded-xl p-10 text-center text-xs text-[#78716C]">
              Loading historical question bank...
            </div>
          ) : records.length === 0 ? (
            <div className="bg-white border border-[#E4E1DA] rounded-xl p-10 text-center space-y-3">
              <h2 className="font-serif-editorial text-xl font-medium text-[#18181B]">
                Your Historical Question Bank is Empty
              </h2>
              <p className="text-sm text-[#57534E] max-w-lg mx-auto leading-relaxed">
                DAT Practice Lab never fabricates past NID exam dates or prompts. Add verified past-paper
                questions manually or import a CSV / JSON / text file to unlock evidence-backed trend
                analytics.
              </p>
              <div className="flex flex-wrap justify-center gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setTab('import')}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold px-4 py-2 rounded-lg bg-[#1E3A5F] text-white cursor-pointer"
                >
                  <Upload className="w-3.5 h-3.5" />
                  Import CSV / JSON / Text
                </button>
                <button
                  type="button"
                  onClick={() => setTab('manual')}
                  className="inline-flex items-center gap-1.5 text-xs font-medium px-4 py-2 rounded-lg border border-[#D8D4CB] bg-white text-[#18181B] cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Enter Manually
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-white border border-[#E4E1DA] rounded-xl divide-y divide-[#ECEAE4]">
              {records.map((rec) => (
                <div key={rec.id} className="p-5 flex items-start justify-between gap-4">
                  <div className="space-y-2 min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2 text-xs">
                      <span className="font-mono-exam font-semibold px-2 py-0.5 rounded bg-[#FAF9F6] border border-[#E4E1DA] text-[#18181B]">
                        {rec.year ?? 'Year: Unknown'}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-[#1E3A5F]/10 text-[#1E3A5F] font-medium">
                        {rec.category}
                      </span>
                      <span className="text-[#78716C]">
                        Marks: {rec.marks != null ? rec.marks : 'Unknown'}
                      </span>
                      <span className="text-[#78716C]">•</span>
                      <span className="text-[#78716C]">
                        Source: {rec.source || 'Unknown'}
                      </span>
                    </div>

                    {rec.title && (
                      <div className="font-serif-editorial text-lg font-medium text-[#18181B]">
                        {rec.title}
                      </div>
                    )}

                    <p className="text-sm text-[#27272A] leading-relaxed whitespace-pre-line">
                      {rec.prompt_text}
                    </p>

                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {rec.programme_tags.map((p) => (
                        <span
                          key={p}
                          className="text-[11px] px-2 py-0.5 rounded bg-[#F2F0EA] text-[#44403C]"
                        >
                          {p}
                        </span>
                      ))}
                      {rec.archetypes.map((a) => (
                        <span
                          key={a}
                          className="text-[11px] px-2 py-0.5 rounded border border-[#E4E1DA] text-[#57534E]"
                        >
                          {a}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center gap-1 shrink-0">
                    <button
                      type="button"
                      onClick={() => startEdit(rec)}
                      className="p-1.5 rounded text-[#57534E] hover:text-[#1E3A5F] hover:bg-stone-100 cursor-pointer"
                      title="Edit"
                    >
                      <Edit3 className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(rec.id)}
                      className="p-1.5 rounded text-[#57534E] hover:text-rose-700 hover:bg-rose-50 cursor-pointer"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* MANUAL ENTRY / EDIT TAB */}
      {tab === 'manual' && (
        <form
          onSubmit={handleSaveManual}
          className="bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-4 max-w-3xl"
        >
          <h2 className="font-serif-editorial text-xl font-medium">
            {editingId ? 'Edit Historical Question' : 'Add Historical Question Manually'}
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-[#44403C] mb-1">
                Short Title (optional)
              </label>
              <input
                type="text"
                value={mTitle}
                onChange={(e) => setMTitle(e.target.value)}
                placeholder="Auto-derived from prompt if blank"
                className="w-full text-sm px-3 py-2 rounded-lg border border-[#D8D4CB]"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-[#44403C] mb-1">Category</label>
              <select
                value={mCategory}
                onChange={(e) => setMCategory(e.target.value)}
                className="w-full text-sm px-3 py-2 rounded-lg border border-[#D8D4CB] bg-white"
              >
                {taxonomy.categories.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-[#44403C] mb-1">
              Question Prompt Text *
            </label>
            <textarea
              rows={5}
              required
              value={mPrompt}
              onChange={(e) => setMPrompt(e.target.value)}
              placeholder="Paste the exact historical prompt text..."
              className="w-full text-sm px-3 py-2 rounded-lg border border-[#D8D4CB]"
            />
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div>
              <label className="block text-xs font-medium text-[#44403C] mb-1">
                Year (blank = Unknown)
              </label>
              <input
                type="number"
                min={1980}
                max={2030}
                value={mYear}
                onChange={(e) => setMYear(e.target.value)}
                placeholder="Unknown"
                className="w-full font-mono-exam text-sm px-3 py-2 rounded-lg border border-[#D8D4CB]"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-[#44403C] mb-1">
                Marks (blank = Unknown)
              </label>
              <input
                type="number"
                min={1}
                max={200}
                value={mMarks}
                onChange={(e) => setMMarks(e.target.value)}
                placeholder="Unknown"
                className="w-full font-mono-exam text-sm px-3 py-2 rounded-lg border border-[#D8D4CB]"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-[#44403C] mb-1">Time (min)</label>
              <input
                type="number"
                min={5}
                max={240}
                value={mTime}
                onChange={(e) => setMTime(e.target.value)}
                placeholder="e.g. 30"
                className="w-full font-mono-exam text-sm px-3 py-2 rounded-lg border border-[#D8D4CB]"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-[#44403C] mb-1">Source</label>
              <input
                type="text"
                value={mSource}
                onChange={(e) => setMSource(e.target.value)}
                placeholder="e.g. NID 2024 Paper"
                className="w-full text-sm px-3 py-2 rounded-lg border border-[#D8D4CB]"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-[#44403C] mb-1.5">
              Programme Tags (separate from Question Category)
            </label>
            <div className="max-h-36 overflow-y-auto p-2.5 rounded-lg border border-[#E4E1DA] bg-[#FAF9F6] flex flex-wrap gap-1.5">
              {taxonomy.programme_tags.map((p) => {
                const active = mProgrammes.includes(p);
                return (
                  <button
                    key={p}
                    type="button"
                    onClick={() =>
                      setMProgrammes((prev) =>
                        prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]
                      )
                    }
                    className={`text-[11px] px-2 py-1 rounded border cursor-pointer ${
                      active
                        ? 'bg-[#1E3A5F] text-white border-[#1E3A5F]'
                        : 'bg-white text-[#44403C] border-[#D8D4CB]'
                    }`}
                  >
                    {p}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-[#44403C] mb-1">Notes (optional)</label>
            <input
              type="text"
              value={mNotes}
              onChange={(e) => setMNotes(e.target.value)}
              placeholder="Any exam paper notes or memory-recall caveats"
              className="w-full text-sm px-3 py-2 rounded-lg border border-[#D8D4CB]"
            />
          </div>

          <div className="flex items-center gap-2 pt-2">
            <button
              type="submit"
              disabled={savingManual}
              className="text-xs font-semibold px-4 py-2 rounded-lg bg-[#1E3A5F] text-white hover:bg-[#162C49] cursor-pointer"
            >
              {savingManual ? 'Saving...' : editingId ? 'Save Changes' : 'Add to Question Bank'}
            </button>
            <button
              type="button"
              onClick={() => {
                resetManualForm();
                setTab('browse');
              }}
              className="text-xs px-4 py-2 rounded-lg border border-[#D8D4CB] text-[#57534E] cursor-pointer"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* BULK / CSV / JSON IMPORT TAB WITH REVIEW STEP */}
      {tab === 'import' && (
        <div className="space-y-5">
          <div className="bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="font-serif-editorial text-xl font-medium">
                  Import & Review Historical Questions
                </h2>
                <p className="text-xs text-[#78716C] mt-0.5">
                  Auto-assigned categories and metadata are shown for review before saving to SQLite.
                </p>
              </div>
              <button
                type="button"
                onClick={downloadCsvTemplate}
                className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-[#D8D4CB] text-[#1E3A5F] hover:bg-[#FAF9F6] cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                Download CSV Template
              </button>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="inline-flex rounded-lg border border-[#D8D4CB] p-1 bg-[#FAF9F6]">
                {(['text', 'csv', 'json'] as const).map((fmt) => (
                  <button
                    key={fmt}
                    type="button"
                    onClick={() => setImportFormat(fmt)}
                    className={`px-3 py-1 text-xs font-medium uppercase rounded cursor-pointer ${
                      importFormat === fmt ? 'bg-[#1E3A5F] text-white' : 'text-[#57534E]'
                    }`}
                  >
                    {fmt}
                  </button>
                ))}
              </div>

              <label className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-[#D8D4CB] bg-white hover:bg-stone-50 cursor-pointer">
                <FileUp className="w-3.5 h-3.5 text-[#1E3A5F]" />
                Load File (.txt, .csv, .json)
                <input
                  type="file"
                  accept=".txt,.csv,.json"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>

              <input
                type="text"
                value={importSource}
                onChange={(e) => setImportSource(e.target.value)}
                placeholder="Default source label (optional)"
                className="text-xs px-3 py-1.5 rounded-lg border border-[#D8D4CB] min-w-[210px]"
              />
            </div>

            <textarea
              rows={8}
              value={importContent}
              onChange={(e) => setImportContent(e.target.value)}
              placeholder={
                importFormat === 'text'
                  ? 'Paste questions separated by blank lines or ---\nOptional tags: [2024] [Category: Storyboard] [Marks: 20]'
                  : importFormat === 'csv'
                    ? 'title,prompt_text,year,category,programme_tags,marks,time_minutes,source\n...'
                    : '[{"prompt_text": "...", "year": 2024, "category": "Problem identification", "programme_tags": ["Universal Design"]}]'
              }
              className="w-full font-mono-exam text-xs px-3.5 py-3 rounded-lg border border-[#D8D4CB] bg-[#FCFBF9]"
            />

            {parseErrors.length > 0 && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900 space-y-1">
                {parseErrors.map((e, i) => (
                  <div key={i}>• {e}</div>
                ))}
              </div>
            )}

            <button
              type="button"
              onClick={handleParseBulk}
              disabled={parsing || !importContent.trim()}
              className="inline-flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-lg bg-[#1E3A5F] text-white hover:bg-[#162C49] disabled:opacity-50 cursor-pointer"
            >
              <Upload className="w-3.5 h-3.5" />
              {parsing ? 'Parsing...' : 'Parse & Review Assignments'}
            </button>
          </div>

          {/* Review Table before Saving */}
          {drafts.length > 0 && (
            <div className="bg-white border border-[#1E3A5F]/30 rounded-xl p-6 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="font-serif-editorial text-lg font-medium text-[#18181B]">
                    Review {drafts.length} Parsed Question(s) Before Saving
                  </h3>
                  <p className="text-xs text-[#57534E]">
                    Verify auto-assigned categories and metadata. Blank years/marks remain “Unknown”.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleCommitDrafts}
                  disabled={committing}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold px-4 py-2 rounded-lg bg-emerald-700 text-white hover:bg-emerald-800 cursor-pointer"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  {committing ? 'Saving...' : `Confirm & Import ${drafts.length} Question(s)`}
                </button>
              </div>

              <div className="divide-y divide-[#ECEAE4]">
                {drafts.map((d, idx) => (
                  <div key={idx} className="py-4 space-y-2.5">
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm text-[#18181B] leading-relaxed flex-1">{d.prompt_text}</p>
                      <button
                        type="button"
                        onClick={() => setDrafts((prev) => prev.filter((_, i) => i !== idx))}
                        className="p-1 text-[#78716C] hover:text-rose-700 cursor-pointer"
                        title="Remove from import"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                    <div className="flex flex-wrap items-center gap-2 text-xs">
                      <select
                        value={d.category}
                        onChange={(e) => {
                          const next = [...drafts];
                          next[idx] = { ...d, category: e.target.value, auto_assigned_category: false };
                          setDrafts(next);
                        }}
                        className="px-2.5 py-1 rounded border border-[#D8D4CB] bg-white font-medium"
                      >
                        {taxonomy.categories.map((c) => (
                          <option key={c} value={c}>
                            {c}
                          </option>
                        ))}
                      </select>
                      <input
                        type="number"
                        placeholder="Year (Unknown)"
                        value={d.year ?? ''}
                        onChange={(e) => {
                          const next = [...drafts];
                          next[idx] = {
                            ...d,
                            year: e.target.value ? parseInt(e.target.value, 10) : null,
                          };
                          setDrafts(next);
                        }}
                        className="w-32 font-mono-exam px-2.5 py-1 rounded border border-[#D8D4CB]"
                      />
                      <span className="text-[11px] text-[#78716C]">{d.confidence_note}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
