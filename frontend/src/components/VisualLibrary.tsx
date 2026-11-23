import React, { useEffect, useState } from 'react';
import {
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  Compass,
  Eye,
  EyeOff,
  Flame,
  Layers,
  Maximize2,
  Play,
  RotateCcw,
  Search,
  Sparkles,
  Target,
  Trophy,
  X,
  Zap,
} from 'lucide-react';
import { api, formatDuration } from '../api';
import type {
  CuratedSheet,
  DailyWorkoutItem,
  GenerationMode,
  NavSection,
  VisualLibraryCatalogue,
  VisualLibraryCategory,
  VisualLibraryItem,
} from '../types';

interface VisualLibraryProps {
  onNavigateToStudio?: (
    section: NavSection,
    preset?: { mode?: GenerationMode; categories?: string[]; themeId?: string | null }
  ) => void;
}

export const VisualLibrary: React.FC<VisualLibraryProps> = ({ onNavigateToStudio }) => {
  const [catalogue, setCatalogue] = useState<VisualLibraryCatalogue | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedCatId, setSelectedCatId] = useState<string>('human_figures');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [filterLevel, setFilterLevel] = useState<'all' | 'unpracticed' | 'level1' | 'level2' | 'level3'>('all');

  // Modal states
  const [activeSheetModal, setActiveSheetModal] = useState<CuratedSheet | null>(null);
  const [drillSubject, setDrillSubject] = useState<{ item: VisualLibraryItem; categoryId: string } | null>(null);
  const [drillTimerSeconds, setDrillTimerSeconds] = useState<number>(120);
  const [drillTimerRunning, setDrillTimerRunning] = useState<boolean>(false);
  const [drillPeekVisible, setDrillPeekVisible] = useState<boolean>(false);
  const [drillNotes, setDrillNotes] = useState<string>('');

  // Daily Workout state
  const [workoutModalOpen, setWorkoutModalOpen] = useState(false);
  const [dailyWorkout, setDailyWorkout] = useState<DailyWorkoutItem[] | null>(null);
  const [workoutLoading, setWorkoutLoading] = useState(false);

  const loadCatalogue = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getVisualLibraryCatalogue();
      setCatalogue(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load visual library catalogue.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCatalogue();
  }, []);

  // Timer interval for 2-min drill
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null;
    if (drillTimerRunning && drillTimerSeconds > 0) {
      interval = setInterval(() => {
        setDrillTimerSeconds((prev) => {
          if (prev <= 1) {
            setDrillTimerRunning(false);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [drillTimerRunning, drillTimerSeconds]);

  const handleToggleLevel = async (
    item: VisualLibraryItem,
    categoryId: string,
    level: 1 | 2 | 3
  ) => {
    const currentProg = item.user_progress || {
      subject_name: item.name,
      category_id: categoryId,
      level_1_studied: false,
      level_2_reproduced: false,
      level_3_adapted: false,
      drill_time_seconds: 0,
      notes: '',
    };

    const patch: {
      subject_name: string;
      category_id: string;
      level_1_studied?: boolean;
      level_2_reproduced?: boolean;
      level_3_adapted?: boolean;
    } = {
      subject_name: item.name,
      category_id: categoryId,
    };

    if (level === 1) patch.level_1_studied = !currentProg.level_1_studied;
    if (level === 2) patch.level_2_reproduced = !currentProg.level_2_reproduced;
    if (level === 3) patch.level_3_adapted = !currentProg.level_3_adapted;

    // Optimistically update local catalogue
    if (catalogue) {
      const updatedCategories = catalogue.categories.map((cat) => {
        if (cat.id !== categoryId) return cat;
        const updatedSubgroups = cat.subgroups.map((sub) => ({
          ...sub,
          items: sub.items.map((it) => {
            if (it.name !== item.name) return it;
            return {
              ...it,
              user_progress: {
                ...currentProg,
                ...(patch.level_1_studied !== undefined ? { level_1_studied: patch.level_1_studied } : {}),
                ...(patch.level_2_reproduced !== undefined ? { level_2_reproduced: patch.level_2_reproduced } : {}),
                ...(patch.level_3_adapted !== undefined ? { level_3_adapted: patch.level_3_adapted } : {}),
              },
            };
          }),
        }));
        return { ...cat, subgroups: updatedSubgroups };
      });
      setCatalogue({ ...catalogue, categories: updatedCategories });
    }

    try {
      await api.updateVisualLibraryProgress(patch);
      // Reload stats in background
      const fresh = await api.getVisualLibraryCatalogue();
      setCatalogue(fresh);
    } catch (err) {
      console.error('Failed to persist progress:', err);
    }
  };

  const startMemoryDrill = (item: VisualLibraryItem, categoryId: string) => {
    setDrillSubject({ item, categoryId });
    setDrillTimerSeconds(120);
    setDrillTimerRunning(true);
    setDrillPeekVisible(false);
    setDrillNotes(item.user_progress?.notes || '');
  };

  const completeMemoryDrill = async () => {
    if (!drillSubject) return;
    const timeSpent = 120 - drillTimerSeconds;
    await api.updateVisualLibraryProgress({
      subject_name: drillSubject.item.name,
      category_id: drillSubject.categoryId,
      level_1_studied: true,
      level_2_reproduced: true,
      drill_time_seconds: timeSpent,
      notes: drillNotes,
    });
    setDrillTimerRunning(false);
    setDrillSubject(null);
    loadCatalogue();
  };

  const openDailyWorkout = async () => {
    setWorkoutLoading(true);
    setWorkoutModalOpen(true);
    try {
      const workout = await api.getVisualLibraryDailyWorkout();
      setDailyWorkout(workout);
    } catch (err) {
      console.error('Failed to load workout:', err);
    } finally {
      setWorkoutLoading(false);
    }
  };

  if (loading && !catalogue) {
    return (
      <div className="space-y-6 animate-pulse max-w-7xl mx-auto py-8">
        <div className="h-10 w-72 bg-stone-200 rounded-lg" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 bg-white border border-[#E4E1DA] rounded-xl" />
          ))}
        </div>
        <div className="h-96 bg-white border border-[#E4E1DA] rounded-xl" />
      </div>
    );
  }

  if (error || !catalogue) {
    return (
      <div className="p-8 bg-red-50 border border-red-200 rounded-xl max-w-4xl mx-auto my-8 text-center space-y-4">
        <h3 className="text-lg font-bold text-red-900">Visual Library Error</h3>
        <p className="text-sm text-red-700">{error || 'Unable to load syllabus.'}</p>
        <button
          onClick={loadCatalogue}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium text-sm transition"
        >
          Retry
        </button>
      </div>
    );
  }

  const activeCategory: VisualLibraryCategory =
    catalogue.categories.find((c) => c.id === selectedCatId) || catalogue.categories[0];

  const globalStats = catalogue.global_stats;

  // Filter items
  const query = searchQuery.trim().toLowerCase();
  const filteredSubgroups = activeCategory.subgroups
    .map((sub) => {
      const matchingItems = sub.items.filter((item) => {
        const matchesQuery =
          !query ||
          item.name.toLowerCase().includes(query) ||
          item.primitives.toLowerCase().includes(query) ||
          item.proportions.toLowerCase().includes(query) ||
          item.level_3_mashup.toLowerCase().includes(query);

        if (!matchesQuery) return false;

        const prog = item.user_progress;
        if (filterLevel === 'unpracticed') return !prog?.level_2_reproduced;
        if (filterLevel === 'level1') return prog?.level_1_studied;
        if (filterLevel === 'level2') return prog?.level_2_reproduced;
        if (filterLevel === 'level3') return prog?.level_3_adapted;
        return true;
      });
      return { ...sub, items: matchingItems };
    })
    .filter((sub) => sub.items.length > 0);

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      {/* Top Banner / Hero */}
      <div className="bg-white border border-[#E4E1DA] rounded-2xl p-6 lg:p-8 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-amber-50 text-amber-800 border border-amber-200 rounded-full text-xs font-semibold uppercase tracking-wider">
              <Zap className="w-3.5 h-3.5 text-amber-600" />
              NID DAT Mental Pinterest Board
            </div>
            <h1 className="text-2xl lg:text-3xl font-serif font-bold text-stone-900 tracking-tight">
              Visual Library & 2-Minute Memory Drills
            </h1>
            <p className="text-stone-600 text-sm leading-relaxed">
              Build a reusable mental library of ~285 visual building blocks across 13 core categories.
              Master the transition from <strong>Recognition</strong> to <strong>2-minute memory reproduction</strong>,
              and finally to <strong>unfamiliar examination adaptation</strong>.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={openDailyWorkout}
              className="flex items-center gap-2.5 px-5 py-3 bg-stone-900 text-white rounded-xl hover:bg-stone-800 font-medium text-sm shadow-sm transition active:scale-[0.98]"
            >
              <Flame className="w-4 h-4 text-amber-400" />
              <span>Daily 15-Min Workout</span>
            </button>
          </div>
        </div>

        {/* Global Progress Strip */}
        <div className="mt-8 pt-6 border-t border-[#E4E1DA] grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 bg-[#FAF9F5] border border-[#E4E1DA] rounded-xl space-y-1">
            <div className="text-xs text-stone-500 font-medium">Total Visual Targets</div>
            <div className="text-2xl font-bold font-serif text-stone-900">
              {globalStats.total_subjects}{' '}
              <span className="text-xs font-sans text-stone-400 font-normal">in 13 categories</span>
            </div>
            <div className="text-[11px] text-stone-500">100% Curated Reference Atlas</div>
          </div>

          <div className="p-4 bg-blue-50/50 border border-blue-100 rounded-xl space-y-1">
            <div className="text-xs text-blue-700 font-medium flex items-center justify-between">
              <span>Level 1: Studied</span>
              <span className="text-[10px] bg-blue-100 px-1.5 py-0.5 rounded text-blue-800 font-bold">Recognition</span>
            </div>
            <div className="text-2xl font-bold font-serif text-blue-900">
              {globalStats.studied_recognition}{' '}
              <span className="text-xs font-sans text-blue-600 font-normal">
                ({Math.round((globalStats.studied_recognition / Math.max(1, globalStats.total_subjects)) * 100)}%)
              </span>
            </div>
            <div className="text-[11px] text-blue-600">Studied geometry & proportions</div>
          </div>

          <div className="p-4 bg-emerald-50/50 border border-emerald-100 rounded-xl space-y-1">
            <div className="text-xs text-emerald-700 font-medium flex items-center justify-between">
              <span>Level 2: Memory Sketches</span>
              <span className="text-[10px] bg-emerald-100 px-1.5 py-0.5 rounded text-emerald-800 font-bold">Reproduction</span>
            </div>
            <div className="text-2xl font-bold font-serif text-emerald-900">
              {globalStats.reproduced_memory}{' '}
              <span className="text-xs font-sans text-emerald-600 font-normal">
                ({Math.round((globalStats.reproduced_memory / Math.max(1, globalStats.total_subjects)) * 100)}%)
              </span>
            </div>
            <div className="text-[11px] text-emerald-600">Passed 2-minute memory test</div>
          </div>

          <div className="p-4 bg-amber-50/50 border border-amber-100 rounded-xl space-y-1">
            <div className="text-xs text-amber-700 font-medium flex items-center justify-between">
              <span>Level 3: Exam Adapted</span>
              <span className="text-[10px] bg-amber-100 px-1.5 py-0.5 rounded text-amber-800 font-bold">Adaptation</span>
            </div>
            <div className="text-2xl font-bold font-serif text-amber-900">
              {globalStats.adapted_exam}{' '}
              <span className="text-xs font-sans text-amber-600 font-normal">
                ({Math.round((globalStats.adapted_exam / Math.max(1, globalStats.total_subjects)) * 100)}%)
              </span>
            </div>
            <div className="text-[11px] text-amber-600">Applied in DAT scenario</div>
          </div>
        </div>
      </div>

      {/* Main Grid: Category Selector Sidebar + Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: 13 Categories Selector */}
        <div className="lg:col-span-4 bg-white border border-[#E4E1DA] rounded-2xl p-4 space-y-2 shadow-sm">
          <div className="px-2 py-1.5 flex items-center justify-between">
            <span className="text-xs font-semibold text-stone-500 uppercase tracking-wider">
              13 Major Categories
            </span>
            <span className="text-xs text-stone-400 font-medium">Priority Order</span>
          </div>

          <div className="space-y-1.5 max-h-[750px] overflow-y-auto pr-1">
            {catalogue.categories.map((cat, idx) => {
              const isSelected = cat.id === selectedCatId;
              const completedCount = cat.stats?.l2_count || 0;
              const totalCat = cat.stats?.total_items || cat.target_count;
              const mastery = cat.stats?.mastery_percent || 0;

              return (
                <button
                  key={cat.id}
                  onClick={() => {
                    setSelectedCatId(cat.id);
                    setSearchQuery('');
                  }}
                  className={`w-full text-left p-3 rounded-xl border transition flex items-center justify-between ${
                    isSelected
                      ? 'bg-stone-900 text-white border-stone-900 shadow-sm'
                      : 'bg-white hover:bg-[#FAF9F5] text-stone-800 border-[#E4E1DA]'
                  }`}
                >
                  <div className="space-y-1 min-w-0 pr-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                          isSelected ? 'bg-white/20 text-white' : 'bg-stone-100 text-stone-600'
                        }`}
                      >
                        {idx + 1}
                      </span>
                      <span className="text-sm font-semibold truncate">{cat.name}</span>
                    </div>

                    <div className="flex items-center gap-2 text-xs">
                      <span className={isSelected ? 'text-stone-300' : 'text-stone-500'}>
                        {completedCount}/{totalCat} mastered
                      </span>
                      <span className={isSelected ? 'text-stone-400' : 'text-stone-300'}>•</span>
                      <span
                        className={`text-[11px] font-medium ${
                          isSelected
                            ? 'text-amber-300'
                            : cat.priority_level <= 4
                            ? 'text-amber-700 font-semibold'
                            : 'text-stone-500'
                        }`}
                      >
                        {cat.priority}
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col items-end gap-1 flex-shrink-0">
                    <span
                      className={`text-xs font-bold ${
                        isSelected ? 'text-amber-300' : mastery > 50 ? 'text-emerald-600' : 'text-stone-500'
                      }`}
                    >
                      {mastery}%
                    </span>
                    <div className="w-12 h-1.5 bg-stone-200/50 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          isSelected ? 'bg-amber-400' : 'bg-emerald-500'
                        }`}
                        style={{ width: `${Math.min(100, mastery)}%` }}
                      />
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Column: Selected Category Details, Curated Atlas & Subject Items */}
        <div className="lg:col-span-8 space-y-6">
          {/* Category Header Card */}
          <div className="bg-white border border-[#E4E1DA] rounded-2xl p-6 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 text-xs font-semibold text-amber-800 bg-amber-50 border border-amber-200 w-fit px-2.5 py-0.5 rounded-full mb-1.5">
                  <span>{activeCategory.priority} ({activeCategory.priority_percent}%)</span>
                  <span>•</span>
                  <span>Target: {activeCategory.target_count} Subjects</span>
                </div>
                <h2 className="text-2xl font-serif font-bold text-stone-900">{activeCategory.name}</h2>
                <p className="text-stone-600 text-sm mt-1">{activeCategory.tagline}</p>
              </div>

              <div className="text-right sm:border-l sm:border-[#E4E1DA] sm:pl-6 space-y-0.5 flex-shrink-0">
                <div className="text-xs text-stone-400 font-medium">Category Mastery</div>
                <div className="text-2xl font-bold font-serif text-stone-900">
                  {activeCategory.stats?.mastery_percent || 0}%
                </div>
                <div className="text-[11px] text-emerald-600 font-medium">
                  {activeCategory.stats?.l2_count || 0} of {activeCategory.stats?.total_items || 0} Memory Ready
                </div>
              </div>
            </div>

            <p className="text-xs text-stone-500 bg-[#FAF9F5] p-3.5 rounded-xl border border-[#E4E1DA] leading-relaxed">
              <strong className="text-stone-800 font-medium">DAT Strategy:</strong> {activeCategory.intro}
            </p>

            {/* Curated Visual Atlas (3 Reference Sheets) */}
            <div className="pt-2">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Eye className="w-4 h-4 text-stone-600" />
                  <span className="text-xs font-bold uppercase tracking-wider text-stone-700">
                    Curated Visual Atlas (3 Local Reference Sheets)
                  </span>
                </div>
                <span className="text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  ✓ Hosted Locally • 100% Offline Ready
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {activeCategory.curated_sheets.map((sheet, idx) => (
                  <div
                    key={idx}
                    onClick={() => setActiveSheetModal(sheet)}
                    className="group relative cursor-pointer overflow-hidden rounded-xl border border-[#E4E1DA] bg-stone-100 hover:border-stone-400 transition shadow-sm"
                  >
                    <div className="aspect-[4/3] w-full overflow-hidden bg-stone-200">
                      <img
                        src={sheet.local_path}
                        alt={sheet.caption}
                        className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                        loading="lazy"
                      />
                    </div>
                    <div className="p-2.5 bg-white space-y-0.5">
                      <div className="text-xs font-semibold text-stone-800 truncate">
                        Sheet {sheet.index}: {sheet.caption || 'Reference Guide'}
                      </div>
                      <div className="flex items-center justify-between text-[10px] text-stone-400">
                        <span>Click to view full size</span>
                        <Maximize2 className="w-3 h-3 text-stone-400 group-hover:text-stone-800 transition" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Search & Filter Controls */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-4 rounded-xl border border-[#E4E1DA] shadow-sm">
            <div className="relative w-full sm:w-72">
              <Search className="w-4 h-4 text-stone-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search subject, geometry, scenario..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-xs bg-[#FAF9F5] border border-[#E4E1DA] rounded-lg focus:outline-none focus:ring-1 focus:ring-stone-800"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-600"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0 text-xs">
              <span className="text-stone-400 text-[11px] font-medium mr-1 flex-shrink-0">Filter:</span>
              {(['all', 'unpracticed', 'level1', 'level2', 'level3'] as const).map((lvl) => (
                <button
                  key={lvl}
                  onClick={() => setFilterLevel(lvl)}
                  className={`px-2.5 py-1.5 rounded-lg font-medium transition flex-shrink-0 ${
                    filterLevel === lvl
                      ? 'bg-stone-900 text-white'
                      : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
                  }`}
                >
                  {lvl === 'all' && 'All Subjects'}
                  {lvl === 'unpracticed' && 'Unpracticed'}
                  {lvl === 'level1' && 'L1 Studied'}
                  {lvl === 'level2' && 'L2 Memory'}
                  {lvl === 'level3' && 'L3 Adapted'}
                </button>
              ))}
            </div>
          </div>

          {/* Subgroups & Subject Cards */}
          <div className="space-y-6">
            {filteredSubgroups.length === 0 ? (
              <div className="p-12 text-center bg-white border border-[#E4E1DA] rounded-2xl text-stone-500 space-y-2">
                <Search className="w-8 h-8 mx-auto text-stone-300" />
                <p className="font-medium text-sm">No subjects found matching your filter.</p>
                <button
                  onClick={() => {
                    setSearchQuery('');
                    setFilterLevel('all');
                  }}
                  className="text-xs text-stone-800 underline font-semibold"
                >
                  Reset filters
                </button>
              </div>
            ) : (
              filteredSubgroups.map((subgroup, gIdx) => (
                <div key={gIdx} className="space-y-3">
                  <div className="flex items-center justify-between px-1">
                    <h3 className="text-sm font-bold text-stone-800 uppercase tracking-wide">
                      {subgroup.group_name}
                    </h3>
                    <span className="text-xs text-stone-400 font-medium">
                      {subgroup.items.length} subjects
                    </span>
                  </div>

                  <div className="grid grid-cols-1 gap-3">
                    {subgroup.items.map((item, iIdx) => {
                      const prog = item.user_progress || {
                        subject_name: item.name,
                        category_id: activeCategory.id,
                        level_1_studied: false,
                        level_2_reproduced: false,
                        level_3_adapted: false,
                        drill_time_seconds: 0,
                        notes: '',
                      };

                      return (
                        <div
                          key={iIdx}
                          className="bg-white border border-[#E4E1DA] hover:border-stone-300 rounded-xl p-4 transition shadow-sm space-y-3"
                        >
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                            <div>
                              <h4 className="text-base font-semibold text-stone-900">{item.name}</h4>
                            </div>

                            {/* 3-Level Mastery Badges / Toggles */}
                            <div className="flex items-center gap-1.5 flex-wrap">
                              {/* Level 1 Toggle */}
                              <button
                                onClick={() => handleToggleLevel(item, activeCategory.id, 1)}
                                title="Level 1: Studied recognition & proportions"
                                className={`px-2.5 py-1 rounded-lg text-xs font-medium border flex items-center gap-1.5 transition ${
                                  prog.level_1_studied
                                    ? 'bg-blue-50 text-blue-800 border-blue-200 font-semibold'
                                    : 'bg-stone-50 text-stone-400 border-stone-200 hover:text-stone-700'
                                }`}
                              >
                                <span className={`w-2 h-2 rounded-full ${prog.level_1_studied ? 'bg-blue-600' : 'bg-stone-300'}`} />
                                L1 Recognition
                              </button>

                              {/* Level 2 Toggle */}
                              <button
                                onClick={() => handleToggleLevel(item, activeCategory.id, 2)}
                                title="Level 2: 2-minute memory reproduction passed"
                                className={`px-2.5 py-1 rounded-lg text-xs font-medium border flex items-center gap-1.5 transition ${
                                  prog.level_2_reproduced
                                    ? 'bg-emerald-50 text-emerald-800 border-emerald-200 font-semibold'
                                    : 'bg-stone-50 text-stone-400 border-stone-200 hover:text-stone-700'
                                }`}
                              >
                                <span className={`w-2 h-2 rounded-full ${prog.level_2_reproduced ? 'bg-emerald-600' : 'bg-stone-300'}`} />
                                L2 Memory (2m)
                              </button>

                              {/* Level 3 Toggle */}
                              <button
                                onClick={() => handleToggleLevel(item, activeCategory.id, 3)}
                                title="Level 3: Adapted to an examination problem"
                                className={`px-2.5 py-1 rounded-lg text-xs font-medium border flex items-center gap-1.5 transition ${
                                  prog.level_3_adapted
                                    ? 'bg-amber-50 text-amber-800 border-amber-200 font-semibold'
                                    : 'bg-stone-50 text-stone-400 border-stone-200 hover:text-stone-700'
                                }`}
                              >
                                <span className={`w-2 h-2 rounded-full ${prog.level_3_adapted ? 'bg-amber-600' : 'bg-stone-300'}`} />
                                L3 Exam Adapted
                              </button>

                              {/* Memory Drill Trigger */}
                              <button
                                onClick={() => startMemoryDrill(item, activeCategory.id)}
                                className="px-3 py-1 bg-stone-900 text-white rounded-lg text-xs font-medium hover:bg-stone-800 flex items-center gap-1.5 transition active:scale-95 shadow-sm"
                              >
                                <Play className="w-3 h-3 fill-current text-amber-400" />
                                <span>2m Drill</span>
                              </button>
                            </div>
                          </div>

                          {/* Breakdown Grid: Primitives & Proportions */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs bg-[#FAF9F5] p-3 rounded-lg border border-[#E4E1DA]">
                            <div>
                              <span className="font-semibold text-stone-700 block mb-0.5">
                                Geometric Primitives:
                              </span>
                              <span className="text-stone-600 leading-relaxed">{item.primitives}</span>
                            </div>
                            <div>
                              <span className="font-semibold text-stone-700 block mb-0.5">
                                Proportions & Alignment:
                              </span>
                              <span className="text-stone-600 leading-relaxed">{item.proportions}</span>
                            </div>
                          </div>

                          {/* Level 3 Exam Adaptation Mashup Prompt */}
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 bg-amber-50/60 border border-amber-200/80 rounded-lg text-xs">
                            <div className="space-y-0.5">
                              <span className="font-bold text-amber-900 uppercase tracking-wide text-[10px] block">
                                Level 3 Exam Mashup Challenge:
                              </span>
                              <p className="text-amber-950 font-serif italic text-sm">
                                "{item.level_3_mashup}"
                              </p>
                            </div>

                            {onNavigateToStudio && (
                              <button
                                onClick={() =>
                                  onNavigateToStudio('generate', {
                                    mode: 'category',
                                    categories: [
                                      activeCategory.id === 'human_figures' || activeCategory.id === 'hands_and_interactions'
                                        ? 'Problem identification'
                                        : activeCategory.id === 'mechanisms_and_components' || activeCategory.id === 'everyday_objects'
                                        ? 'Product sketch'
                                        : activeCategory.id === 'symbols_and_signage'
                                        ? 'Logos, Symbols & Signs'
                                        : 'Drawing',
                                    ],
                                  })
                                }
                                className="flex-shrink-0 self-start sm:self-center px-3 py-1.5 bg-amber-600 text-white hover:bg-amber-700 font-medium rounded-md shadow-xs transition text-[11px]"
                              >
                                Practice in Studio →
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* MODAL 1: Full Size Curated Reference Sheet Modal */}
      {activeSheetModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="relative max-w-4xl w-full max-h-[92vh] bg-white rounded-2xl overflow-hidden shadow-2xl flex flex-col">
            <div className="p-4 border-b border-stone-200 flex items-center justify-between bg-stone-50">
              <div className="space-y-0.5">
                <h3 className="font-serif font-bold text-stone-900 text-lg">
                  {activeSheetModal.caption || `Curated Reference Sheet ${activeSheetModal.index}`}
                </h3>
                <p className="text-xs text-stone-500">
                  From NID DAT Curated Atlas • Local file: {activeSheetModal.filename}
                </p>
              </div>
              <button
                onClick={() => setActiveSheetModal(null)}
                className="p-1.5 text-stone-400 hover:text-stone-700 hover:bg-stone-200 rounded-lg transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-auto p-4 flex items-center justify-center bg-stone-900">
              <img
                src={activeSheetModal.local_path}
                alt={activeSheetModal.caption}
                className="max-h-[75vh] w-auto object-contain rounded-lg shadow-md"
              />
            </div>

            <div className="p-4 bg-stone-50 border-t border-stone-200 flex items-center justify-between text-xs text-stone-600">
              <span>Study construction lines, negative space, and anatomical proportions.</span>
              <button
                onClick={() => setActiveSheetModal(null)}
                className="px-4 py-2 bg-stone-900 text-white rounded-lg font-medium hover:bg-stone-800 transition"
              >
                Close Reference
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 2: Interactive 2-Minute Memory Sketch Flashcard Timer */}
      {drillSubject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-sm animate-fade-in">
          <div className="relative max-w-xl w-full bg-white rounded-2xl overflow-hidden shadow-2xl p-6 sm:p-8 space-y-6">
            <div className="flex items-center justify-between border-b border-stone-200 pb-4">
              <div className="space-y-1">
                <span className="text-[11px] font-bold uppercase tracking-wider text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                  Level 2 Memory Drill (2 Minutes)
                </span>
                <h3 className="text-xl font-serif font-bold text-stone-900">
                  {drillSubject.item.name}
                </h3>
              </div>
              <button
                onClick={() => {
                  setDrillTimerRunning(false);
                  setDrillSubject(null);
                }}
                className="p-1.5 text-stone-400 hover:text-stone-700 rounded-lg transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Giant Timer Display */}
            <div className="text-center py-4 bg-[#FAF9F5] border border-[#E4E1DA] rounded-2xl space-y-2">
              <div className="text-xs text-stone-500 font-medium">Time Remaining</div>
              <div
                className={`text-6xl font-mono font-bold tracking-tight ${
                  drillTimerSeconds <= 15 ? 'text-red-600 animate-pulse' : 'text-stone-900'
                }`}
              >
                {formatDuration(drillTimerSeconds)}
              </div>
              <div className="flex items-center justify-center gap-2 pt-2">
                <button
                  onClick={() => setDrillTimerRunning(!drillTimerRunning)}
                  className={`px-4 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                    drillTimerRunning
                      ? 'bg-stone-200 text-stone-700 hover:bg-stone-300'
                      : 'bg-emerald-600 text-white hover:bg-emerald-700'
                  }`}
                >
                  {drillTimerRunning ? 'Pause' : 'Resume Timer'}
                </button>
                <button
                  onClick={() => {
                    setDrillTimerSeconds(120);
                    setDrillTimerRunning(true);
                  }}
                  className="px-3 py-1.5 bg-stone-100 text-stone-600 hover:bg-stone-200 rounded-lg text-xs font-medium flex items-center gap-1"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  Reset
                </button>
              </div>
            </div>

            {/* Drill Instructions & Peek Reference Toggle */}
            <div className="space-y-3">
              <div className="p-3 bg-stone-50 border border-stone-200 rounded-xl space-y-1 text-xs">
                <span className="font-semibold text-stone-700 block">Geometric Rule:</span>
                <p className="text-stone-600">{drillSubject.item.primitives}</p>
              </div>

              {/* Peek Reference Button */}
              <div className="flex items-center justify-between text-xs">
                <span className="text-stone-500">Stuck on the form?</span>
                <button
                  onClick={() => setDrillPeekVisible(!drillPeekVisible)}
                  className="flex items-center gap-1.5 text-stone-700 hover:text-stone-900 font-medium underline"
                >
                  {drillPeekVisible ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  {drillPeekVisible ? 'Hide Reference' : 'Peek 5-Second Reference'}
                </button>
              </div>

              {drillPeekVisible && (
                <div className="p-3 bg-stone-100 border border-stone-300 rounded-xl animate-fade-in flex items-center justify-center">
                  <div className="text-center space-y-2">
                    <p className="text-[11px] text-stone-600 font-serif italic">
                      "Keep construction ellipses clean and line of action continuous."
                    </p>
                    <div className="flex gap-2 justify-center">
                      {activeCategory.curated_sheets.map((sheet, i) => (
                        <img
                          key={i}
                          src={sheet.local_path}
                          alt="peek"
                          className="h-24 w-auto rounded border border-stone-300 object-cover shadow-xs"
                        />
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Reflection Notes Input */}
              <div className="space-y-1">
                <label className="text-xs font-medium text-stone-600">Drill Notes / Self-Critique:</label>
                <input
                  type="text"
                  placeholder="e.g. Struggled with foreshortening on arm; line of action tilted"
                  value={drillNotes}
                  onChange={(e) => setDrillNotes(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-white border border-[#E4E1DA] rounded-lg focus:outline-none focus:ring-1 focus:ring-stone-800"
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-end gap-3 pt-4 border-t border-stone-200">
              <button
                onClick={() => {
                  setDrillTimerRunning(false);
                  setDrillSubject(null);
                }}
                className="px-4 py-2 text-stone-600 hover:text-stone-800 text-xs font-medium transition"
              >
                Cancel
              </button>
              <button
                onClick={completeMemoryDrill}
                className="px-5 py-2.5 bg-emerald-600 text-white rounded-xl text-xs font-semibold hover:bg-emerald-700 flex items-center gap-1.5 shadow-sm transition active:scale-95"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Mark as 2-Minute Memory Mastered</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 3: Daily 15-Minute Workout Modal */}
      {workoutModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="relative max-w-2xl w-full bg-white rounded-2xl overflow-hidden shadow-2xl p-6 sm:p-8 space-y-6 max-h-[92vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-stone-200 pb-4">
              <div className="space-y-1">
                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-amber-50 text-amber-800 border border-amber-200 rounded-full text-xs font-semibold">
                  <Flame className="w-3.5 h-3.5 text-amber-600" />
                  Today's 15-Minute Workout
                </div>
                <h3 className="text-xl font-serif font-bold text-stone-900">
                  3 Focused Daily Drills
                </h3>
              </div>
              <button
                onClick={() => setWorkoutModalOpen(false)}
                className="p-1.5 text-stone-400 hover:text-stone-700 rounded-lg transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-stone-600 leading-relaxed">
              Spend exactly 5 minutes per item: 1 minute studying the breakdown, 2 minutes sketching from memory,
              and 2 minutes reviewing against the reference sheet.
            </p>

            {workoutLoading || !dailyWorkout ? (
              <div className="space-y-3 py-8 text-center">
                <Clock className="w-8 h-8 mx-auto text-amber-500 animate-spin" />
                <p className="text-xs text-stone-500">Selecting 3 unpracticed subjects across tiers...</p>
              </div>
            ) : (
              <div className="space-y-4">
                {dailyWorkout.map((w, i) => (
                  <div
                    key={i}
                    className="p-4 bg-[#FAF9F5] border border-[#E4E1DA] rounded-xl space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-stone-900 text-white text-[10px] font-bold flex items-center justify-center">
                          {i + 1}
                        </span>
                        <div>
                          <span className="text-[11px] font-semibold text-stone-400 block">
                            {w.category_name}
                          </span>
                          <h4 className="text-sm font-bold text-stone-900">{w.subject.name}</h4>
                        </div>
                      </div>

                      <button
                        onClick={() => {
                          setWorkoutModalOpen(false);
                          startMemoryDrill(w.subject, w.category_id);
                        }}
                        className="px-3 py-1.5 bg-stone-900 text-white rounded-lg text-xs font-medium hover:bg-stone-800 flex items-center gap-1.5 shadow-sm transition"
                      >
                        <Play className="w-3 h-3 fill-current text-amber-400" />
                        Start Drill
                      </button>
                    </div>

                    <div className="text-xs text-stone-600 space-y-1">
                      <p>
                        <strong>Geometric rule:</strong> {w.subject.primitives}
                      </p>
                      <p className="text-[11px] text-amber-900 italic font-serif bg-amber-50 p-2 rounded border border-amber-200/60">
                        Level 3 Exam Mashup: "{w.subject.level_3_mashup}"
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="flex justify-end pt-4 border-t border-stone-200">
              <button
                onClick={() => setWorkoutModalOpen(false)}
                className="px-5 py-2 bg-stone-900 text-white rounded-xl text-xs font-semibold hover:bg-stone-800 transition"
              >
                Close Workout
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
