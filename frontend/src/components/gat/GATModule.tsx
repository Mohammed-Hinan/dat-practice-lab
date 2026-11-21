import React, { useEffect, useState } from 'react';
import {
  BarChart2,
  BookOpen,
  CheckCircle2,
  Clock,
  Compass,
  FileCheck2,
  Layers,
  LayoutDashboard,
  PenTool,
  RotateCcw,
  Sparkles,
} from 'lucide-react';
import type { GATOverview as GATOverviewType, GATQuestion, GATSection, GATSubTab } from '../../types';
import { api } from '../../api';

import { GATOverview } from './GATOverview';
import { GATPractice } from './GATPractice';
import { GATLearn } from './GATLearn';
import { GATGkBoard } from './GATGkBoard';
import { GATRevision } from './GATRevision';
import { GATMockTests } from './GATMockTests';
import { GATPerformance } from './GATPerformance';

interface GATModuleProps {
  initialSubTab?: GATSubTab;
}

export const GATModule: React.FC<GATModuleProps> = ({ initialSubTab = 'overview' }) => {
  const [activeTab, setActiveTab] = useState<GATSubTab>(initialSubTab);
  const [activeSectionFilter, setActiveSectionFilter] = useState<GATSection | undefined>();
  const [overview, setOverview] = useState<GATOverviewType | null>(null);
  const [loadingOverview, setLoadingOverview] = useState(true);

  const fetchOverview = async () => {
    try {
      const data = await api.getGATOverview();
      setOverview(data);
    } catch (err) {
      console.error('Failed to fetch GAT overview', err);
    } finally {
      setLoadingOverview(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  const handleNavigateTab = (tab: GATSubTab, sectionFilter?: GATSection) => {
    setActiveSectionFilter(sectionFilter);
    setActiveTab(tab);
  };

  const handleStartPractice = (section?: GATSection) => {
    setActiveSectionFilter(section);
    setActiveTab('practice');
  };

  const tabs: { key: GATSubTab; label: string; icon: React.ReactNode }[] = [
    { key: 'overview', label: 'Overview', icon: <LayoutDashboard className="w-3.5 h-3.5" /> },
    { key: 'learn', label: 'Learn', icon: <BookOpen className="w-3.5 h-3.5" /> },
    { key: 'practice', label: 'Practice', icon: <PenTool className="w-3.5 h-3.5" /> },
    { key: 'gk', label: 'GK & Awareness', icon: <Sparkles className="w-3.5 h-3.5" /> },
    { key: 'revision', label: 'Revision', icon: <RotateCcw className="w-3.5 h-3.5" /> },
    { key: 'mock_tests', label: 'Mock Tests', icon: <Clock className="w-3.5 h-3.5" /> },
    { key: 'performance', label: 'Performance', icon: <BarChart2 className="w-3.5 h-3.5" /> },
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-[#E4E1DA] pb-5">
        <div>
          <h1 className="font-serif-editorial text-3xl font-medium text-[#18181B]">
            GAT Preparation Lab
          </h1>
          <p className="text-xs text-[#78716C] mt-1">
            General Ability Test preparation for NIFT M.Des, UCEED, and CEED Part A — populated exclusively from authentic Roughworks questions.
          </p>
        </div>

        {/* Sub-tab Navigation Pills */}
        <nav className="flex flex-wrap items-center gap-1.5 bg-[#FAF9F6] p-1 rounded-xl border border-[#E4E1DA]">
          {tabs.map((t) => {
            const isActive = activeTab === t.key;
            return (
              <button
                key={t.key}
                type="button"
                onClick={() => {
                  setActiveTab(t.key);
                }}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                  isActive
                    ? 'bg-white text-[#1E3A5F] font-semibold border border-[#D8D4CB] shadow-2xs'
                    : 'text-[#57534E] hover:text-[#18181B] hover:bg-stone-100/60'
                }`}
              >
                {t.icon}
                <span>{t.label}</span>
              </button>
            );
          })}
        </nav>
      </header>

      {/* Sub-view Content Router */}
      <main>
        {activeTab === 'overview' && (
          <GATOverview
            overview={overview}
            loading={loadingOverview}
            onNavigateTab={handleNavigateTab}
            onStartPractice={handleStartPractice}
          />
        )}

        {activeTab === 'learn' && (
          <GATLearn
            initialSection={activeSectionFilter}
            onStartPracticeTopic={(sec, _topic) => {
              setActiveSectionFilter(sec);
              setActiveTab('practice');
            }}
          />
        )}

        {activeTab === 'practice' && (
          <GATPractice
            initialSection={activeSectionFilter}
            onRefreshOverview={fetchOverview}
          />
        )}

        {activeTab === 'gk' && (
          <GATGkBoard
            onPracticeQuestion={(_qid) => {
              setActiveTab('practice');
            }}
          />
        )}

        {activeTab === 'revision' && (
          <GATRevision
            onPracticeQuestion={(_q: GATQuestion) => {
              setActiveTab('practice');
            }}
            onRefreshOverview={fetchOverview}
          />
        )}

        {activeTab === 'mock_tests' && (
          <GATMockTests onRefreshOverview={fetchOverview} />
        )}

        {activeTab === 'performance' && (
          <GATPerformance
            overview={overview}
            loading={loadingOverview}
            onStartPractice={handleStartPractice}
          />
        )}
      </main>
    </div>
  );
};
