import React, { useEffect, useState } from 'react';
import {
  Archive,
  ClipboardList,
  Compass,
  History,
  LayoutDashboard,
  Menu,
  Settings as SettingsIcon,
  Sparkles,
  TrendingUp,
  X,
} from 'lucide-react';
import { api } from './api';
import { Dashboard } from './components/Dashboard';
import { ExamSimulator } from './components/ExamSimulator';
import { PracticeHistory } from './components/PracticeHistory';
import { QuestionBank } from './components/QuestionBank';
import { QuestionGenerator } from './components/QuestionGenerator';
import { Settings } from './components/Settings';
import { TrendAnalytics } from './components/TrendAnalytics';
import type {
  AppSettings,
  GenerationMode,
  LLMConnectionStatus,
  NavSection,
  TaxonomyData,
} from './types';

const NAV_ITEMS: { id: NavSection; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'generate', label: 'Generate Questions', icon: Sparkles },
  { id: 'simulator', label: 'Exam Simulator', icon: ClipboardList },
  { id: 'bank', label: 'Question Bank', icon: Archive },
  { id: 'trends', label: 'Trends & Predictions', icon: TrendingUp },
  { id: 'history', label: 'Practice History', icon: History },
];

export default function App() {
  const [section, setSection] = useState<NavSection>('dashboard');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const [taxonomy, setTaxonomy] = useState<TaxonomyData | null>(null);
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [llmStatus, setLlmStatus] = useState<LLMConnectionStatus | null>(null);
  const [bootError, setBootError] = useState<string | null>(null);

  const [genPreset, setGenPreset] = useState<{
    mode?: GenerationMode;
    categories?: string[];
    themeId?: string | null;
  } | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [tax, cfg] = await Promise.all([api.getTaxonomy(), api.getSettings()]);
        setTaxonomy(tax);
        setSettings(cfg);
      } catch (err) {
        setBootError(
          err instanceof Error
            ? err.message
            : 'Unable to reach DAT Practice Lab backend API at http://127.0.0.1:8000.'
        );
        return;
      }

      try {
        const st = await api.getLLMStatus();
        setLlmStatus(st);
      } catch {
        setLlmStatus({
          connected: false,
          provider: 'ollama',
          endpoint: 'http://localhost:11434',
          models: [],
          selected_model: '',
          message: 'Local LLM status check failed.',
        });
      }
    })();

    // Periodically verify LLM connection so status auto-recovers after model load/unload
    const timer = setInterval(async () => {
      try {
        const st = await api.getLLMStatus();
        setLlmStatus(st);
      } catch {
        // Keep prior state quietly
      }
    }, 12000);

    return () => clearInterval(timer);
  }, []);

  const handleNavigate = (
    target: NavSection,
    preset?: { mode?: GenerationMode; categories?: string[]; themeId?: string | null }
  ) => {
    if (preset) {
      setGenPreset(preset);
    }
    setSection(target);
    setMobileMenuOpen(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (bootError) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6 bg-[#F7F6F2]">
        <div className="max-w-md w-full bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-3">
          <h1 className="font-serif-editorial text-2xl font-medium text-[#18181B]">
            Backend Not Reachable
          </h1>
          <p className="text-sm text-[#57534E] leading-relaxed">{bootError}</p>
          <p className="text-xs font-mono-exam bg-[#FAF9F6] border border-[#E4E1DA] rounded p-3 text-[#27272A]">
            cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000
          </p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="text-xs font-semibold px-4 py-2 rounded-lg bg-[#1E3A5F] text-white cursor-pointer"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  if (!taxonomy || !settings) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F7F6F2]">
        <div className="text-center space-y-2">
          <div className="font-serif-editorial text-2xl text-[#18181B]">DAT Practice Lab</div>
          <p className="text-xs text-[#78716C]">Loading local studio...</p>
        </div>
      </div>
    );
  }

  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* Brand */}
      <div className="px-5 py-5 border-b border-[#E4E1DA]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#1E3A5F] text-white flex items-center justify-center">
            <Compass className="w-4 h-4" />
          </div>
          <div>
            <div className="font-serif-editorial text-lg font-semibold leading-tight text-[#18181B]">
              DAT Practice Lab
            </div>
            <div className="text-[10px] font-mono-exam uppercase tracking-wider text-[#78716C]">
              NID M.Des Exam Studio
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto" aria-label="Primary Navigation">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = section === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => handleNavigate(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors cursor-pointer ${
                active
                  ? 'bg-[#1E3A5F] text-white font-medium'
                  : 'text-[#44403C] hover:bg-[#EFECE5] hover:text-[#18181B]'
              }`}
            >
              <Icon className={`w-4 h-4 ${active ? 'text-white' : 'text-[#78716C]'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Cloud Engine Status Footer */}
      <div className="p-3 border-t border-[#E4E1DA]">
        <div className="w-full p-2.5 rounded-lg bg-[#FAF9F6] border border-[#E4E1DA] space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="font-medium text-[#18181B]">
              {llmStatus?.provider === 'gemini'
                ? 'Google Gemini Cloud'
                : llmStatus?.provider === 'groq'
                  ? 'Groq Cloud'
                  : 'AI Study Engine'}
            </span>
            <span className="inline-flex items-center gap-1.5 text-[11px]">
              <span
                className={`w-2 h-2 rounded-full ${
                  llmStatus?.connected ? 'bg-emerald-600' : 'bg-amber-500'
                }`}
              />
              <span className={llmStatus?.connected ? 'text-emerald-800' : 'text-amber-800'}>
                {llmStatus?.connected ? 'Online' : 'Offline'}
              </span>
            </span>
          </div>
          <div className="font-mono-exam text-[10px] text-[#78716C] flex items-center justify-between">
            <span className="truncate">{llmStatus?.selected_model || 'Cloud Ready'}</span>
            {typeof window !== 'undefined' &&
              (window.location.hostname === 'localhost' ||
                window.location.hostname === '127.0.0.1') && (
                <button
                  type="button"
                  onClick={() => handleNavigate('settings')}
                  title="Host Configuration"
                  className="text-[#78716C] hover:text-[#18181B] p-0.5 rounded cursor-pointer"
                >
                  <SettingsIcon className="w-3.5 h-3.5" />
                </button>
              )}
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex bg-[#F7F6F2] text-[#18181B]">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:block w-64 shrink-0 bg-white border-r border-[#E4E1DA] sticky top-0 h-screen">
        {sidebarContent}
      </aside>

      {/* Mobile Topbar + Drawer */}
      <div className="lg:hidden fixed top-0 inset-x-0 z-30 h-14 bg-white border-b border-[#E4E1DA] px-4 flex items-center justify-between no-print">
        <div className="flex items-center gap-2">
          <Compass className="w-4 h-4 text-[#1E3A5F]" />
          <span className="font-serif-editorial text-lg font-semibold">DAT Practice Lab</span>
        </div>
        <button
          type="button"
          onClick={() => setMobileMenuOpen((v) => !v)}
          className="p-2 rounded-lg border border-[#E4E1DA] text-[#18181B]"
          aria-label="Toggle navigation"
        >
          {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
        </button>
      </div>

      {mobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 z-40 flex">
          <div className="w-64 bg-white border-r border-[#E4E1DA] h-full shadow-xl">
            {sidebarContent}
          </div>
          <button
            type="button"
            aria-label="Close navigation"
            className="flex-1 bg-black/30"
            onClick={() => setMobileMenuOpen(false)}
          />
        </div>
      )}

      {/* Main Content Canvas */}
      <main className="flex-1 min-w-0 pt-16 lg:pt-0">
        <div className="max-w-6xl mx-auto px-4 sm:px-8 py-6 sm:py-8">
          {section === 'dashboard' && (
            <Dashboard onNavigate={handleNavigate} llmConnected={Boolean(llmStatus?.connected)} />
          )}
          {section === 'generate' && (
            <QuestionGenerator
              taxonomy={taxonomy}
              settings={settings}
              llmConnected={Boolean(llmStatus?.connected)}
              initialPreset={genPreset}
              onGoToSettings={() => handleNavigate('settings')}
            />
          )}
          {section === 'simulator' && (
            <ExamSimulator
              taxonomy={taxonomy}
              settings={settings}
              llmConnected={Boolean(llmStatus?.connected)}
            />
          )}
          {section === 'bank' && <QuestionBank taxonomy={taxonomy} />}
          {section === 'trends' && <TrendAnalytics onNavigate={handleNavigate} />}
          {section === 'history' && <PracticeHistory taxonomy={taxonomy} />}
          {section === 'settings' && (
            <Settings
              taxonomy={taxonomy}
              settings={settings}
              llmStatus={llmStatus}
              onSettingsUpdated={setSettings}
              onStatusUpdated={setLlmStatus}
            />
          )}
        </div>
      </main>
    </div>
  );
}
