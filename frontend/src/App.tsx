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
import { api, API_BASE } from './api';
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
  const [bootingMessage, setBootingMessage] = useState<string>('Loading exam studio...');

  const [genPreset, setGenPreset] = useState<{
    mode?: GenerationMode;
    categories?: string[];
    themeId?: string | null;
  } | null>(null);

  const initStudio = async (retriesLeft = 3) => {
    try {
      setBootError(null);
      if (retriesLeft < 3) {
        setBootingMessage(`Waking backend server (attempt ${4 - retriesLeft}/3)...`);
      }
      const [tax, cfg] = await Promise.all([api.getTaxonomy(), api.getSettings()]);
      setTaxonomy(tax);
      setSettings(cfg);
    } catch (err) {
      if (retriesLeft > 1) {
        setBootingMessage(`Waiting for backend to wake up (attempt ${4 - retriesLeft}/3)...`);
        await new Promise((r) => setTimeout(r, 2500));
        return initStudio(retriesLeft - 1);
      }
      setBootError(
        err instanceof Error
          ? err.message
          : 'Unable to connect to DAT Practice Lab backend.'
      );
      return;
    }

    try {
      const st = await api.getLLMStatus();
      setLlmStatus(st);
    } catch {
      setLlmStatus({
        connected: false,
        provider: 'gemini',
        endpoint: '',
        models: [],
        selected_model: '',
        message: 'LLM status check unavailable.',
      });
    }
  };

  useEffect(() => {
    initStudio(3);

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
    const isCloudHost = typeof window !== 'undefined' && 
      window.location.hostname !== 'localhost' && 
      window.location.hostname !== '127.0.0.1';
    const isMixedContent = typeof window !== 'undefined' && 
      window.location.protocol === 'https:' && 
      API_BASE.startsWith('http://');
    const isMissingCloudEnv = isCloudHost && API_BASE === '/api';

    return (
      <div className="min-h-screen flex items-center justify-center p-6 bg-[#F7F6F2]">
        <div className="max-w-lg w-full bg-white border border-[#E4E1DA] rounded-xl p-6 sm:p-8 space-y-4 shadow-sm">
          <div className="flex items-center gap-3 border-b border-[#E4E1DA] pb-4">
            <div className="w-10 h-10 rounded-lg bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-700 font-semibold text-lg">
              !
            </div>
            <div>
              <h1 className="font-serif-editorial text-xl sm:text-2xl font-semibold text-[#18181B]">
                Backend Not Reachable
              </h1>
              <p className="text-xs text-[#78716C] font-mono-exam mt-0.5">
                Target endpoint: {API_BASE.startsWith('http') ? API_BASE : `${typeof window !== 'undefined' ? window.location.origin : ''}${API_BASE}`}
              </p>
            </div>
          </div>

          <div className="rounded-lg bg-rose-50/70 border border-rose-200 p-3.5 text-xs text-rose-900 leading-relaxed font-mono-exam">
            Error: {bootError}
          </div>

          {isMixedContent ? (
            <div className="space-y-2 text-xs text-[#44403C] bg-amber-50 border border-amber-200 rounded-lg p-3.5">
              <p className="font-semibold text-amber-900">⚠️ Browser Security Block (Mixed Content):</p>
              <p>Your web app is loaded securely over <strong>HTTPS</strong>, but your API endpoint is configured with insecure <code>http://</code>. Web browsers automatically block this.</p>
              <p className="font-mono-exam text-[11px] bg-white/70 p-2 rounded border border-amber-200">
                Change your <code>VITE_API_BASE_URL</code> environment variable to use <code>https://</code>.
              </p>
            </div>
          ) : isMissingCloudEnv ? (
            <div className="space-y-2 text-xs text-[#44403C] bg-sky-50 border border-sky-200 rounded-lg p-3.5">
              <p className="font-semibold text-sky-950">🌐 Missing Backend Cloud URL on Vercel:</p>
              <p>Your frontend is deployed to the cloud, but doesn't know where your backend lives yet.</p>
              <ol className="list-decimal list-inside space-y-1 font-sans text-sky-900 pl-1">
                <li>Copy your <strong>Render Web Service URL</strong> (e.g. <code>https://dat-practice-lab-backend.onrender.com</code>).</li>
                <li>Go to <strong>Vercel &rarr; Your Project &rarr; Settings &rarr; Environment Variables</strong>.</li>
                <li>Add variable: <code>VITE_API_BASE_URL</code> with your Render URL.</li>
                <li>Click <strong>Redeploy</strong> in Vercel.</li>
              </ol>
            </div>
          ) : (
            <div className="space-y-2 text-xs text-[#44403C] bg-[#FAF9F6] border border-[#E4E1DA] rounded-lg p-3.5">
              <p className="font-semibold text-[#18181B]">💡 How to resolve:</p>
              {isCloudHost ? (
                <p className="leading-relaxed">
                  If your backend is hosted on Render (free tier), it may take <strong>30–50 seconds</strong> to wake up from idle on the first request.
                </p>
              ) : (
                <>
                  <p>Ensure your local backend server is running in terminal:</p>
                  <pre className="font-mono-exam text-[11px] bg-white p-2.5 rounded border border-[#E4E1DA] text-[#27272A] overflow-x-auto">
                    cd backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
                  </pre>
                </>
              )}
            </div>
          )}

          <div className="pt-2 flex items-center justify-between">
            <button
              type="button"
              onClick={() => initStudio(3)}
              className="text-xs font-semibold px-4 py-2.5 rounded-lg bg-[#1E3A5F] text-white hover:bg-[#162C49] cursor-pointer transition-colors shadow-sm"
            >
              Retry Connection
            </button>
            <span className="text-[11px] text-[#78716C]">
              {bootingMessage}
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (!taxonomy || !settings) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F7F6F2]">
        <div className="text-center space-y-3">
          <div className="font-serif-editorial text-2xl text-[#18181B]">DAT Practice Lab</div>
          <div className="inline-flex items-center gap-2 text-xs text-[#78716C] bg-white px-3 py-1.5 rounded-full border border-[#E4E1DA] shadow-xs">
            <span className="w-2 h-2 rounded-full bg-[#1E3A5F] animate-pulse" />
            <span>{bootingMessage}</span>
          </div>
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
