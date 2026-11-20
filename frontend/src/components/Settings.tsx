import React, { useEffect, useState } from 'react';
import {
  Check,
  CheckCircle2,
  Cpu,
  ExternalLink,
  Eye,
  EyeOff,
  GraduationCap,
  Image as ImageIcon,
  Key,
  Loader2,
  Lock,
  RefreshCw,
  Save,
  Settings2,
  ShieldCheck,
  Sliders,
  Sparkles,
  WifiOff,
} from 'lucide-react';
import { api } from '../api';
import type {
  AppSettings,
  DrawThingsStatus,
  LLMConnectionStatus,
  ProviderType,
  TaxonomyData,
} from '../types';

interface SettingsProps {
  taxonomy: TaxonomyData;
  settings: AppSettings;
  llmStatus: LLMConnectionStatus | null;
  onSettingsUpdated: (updated: AppSettings) => void;
  onStatusUpdated: (status: LLMConnectionStatus) => void;
}

export const Settings: React.FC<SettingsProps> = ({
  taxonomy,
  settings,
  llmStatus,
  onSettingsUpdated,
  onStatusUpdated,
}) => {
  const [draft, setDraft] = useState<AppSettings>(settings);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [discoveredModels, setDiscoveredModels] = useState<string[]>(llmStatus?.models || []);
  const [testResult, setTestResult] = useState<LLMConnectionStatus | null>(llmStatus);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [dtStatus, setDtStatus] = useState<DrawThingsStatus | null>(null);
  const [testingDt, setTestingDt] = useState(false);
  const [showGeminiKey, setShowGeminiKey] = useState(false);
  const [showOpenAIKey, setShowOpenAIKey] = useState(false);
  const [activeTab, setActiveTab] = useState<'student' | 'developer'>('student');

  useEffect(() => {
    api
      .getDrawThingsStatus()
      .then(setDtStatus)
      .catch(() => {});
  }, []);

  const handleTestDrawThings = async () => {
    setTestingDt(true);
    try {
      setDtStatus(await api.testDrawThings(draft.drawthings_base_url));
    } catch (err) {
      setDtStatus({
        connected: false,
        endpoint: draft.drawthings_base_url,
        grpc_detected_on_7859: false,
        message: err instanceof Error ? err.message : 'Draw Things connection test failed.',
      });
    } finally {
      setTestingDt(false);
    }
  };

  useEffect(() => {
    setDraft(settings);
  }, [settings]);

  useEffect(() => {
    if (llmStatus) {
      setTestResult(llmStatus);
      if (llmStatus.models.length > 0) setDiscoveredModels(llmStatus.models);
    }
  }, [llmStatus]);

  const currentEndpoint =
    draft.provider === 'ollama'
      ? draft.ollama_base_url
      : draft.provider === 'lmstudio'
        ? draft.lmstudio_base_url
        : draft.provider === 'gemini'
          ? 'https://generativelanguage.googleapis.com/v1beta/openai'
          : draft.provider === 'groq'
            ? 'https://api.groq.com/openai/v1'
            : draft.custom_base_url;

  const handleEndpointChange = (val: string) => {
    if (draft.provider === 'ollama') setDraft({ ...draft, ollama_base_url: val });
    else if (draft.provider === 'lmstudio') setDraft({ ...draft, lmstudio_base_url: val });
    else if (draft.provider !== 'gemini' && draft.provider !== 'groq') {
      setDraft({ ...draft, custom_base_url: val });
    }
  };

  const handleTestAndDiscover = async (overrideProvider?: ProviderType) => {
    const prov = overrideProvider || draft.provider;
    const url =
      prov === 'ollama'
        ? draft.ollama_base_url
        : prov === 'lmstudio'
          ? draft.lmstudio_base_url
          : prov === 'gemini'
            ? 'https://generativelanguage.googleapis.com/v1beta/openai'
            : prov === 'groq'
              ? 'https://api.groq.com/openai/v1'
              : draft.custom_base_url;

    const apiKey =
      prov === 'gemini'
        ? draft.gemini_api_key
        : prov === 'groq'
          ? draft.groq_api_key
          : prov === 'custom_openai'
            ? draft.custom_api_key
            : undefined;

    setTesting(true);
    try {
      const res = await api.testLLM({
        provider: prov,
        base_url: url,
        api_key: apiKey,
        model: draft.model,
      });
      setTestResult(res);
      setDiscoveredModels(res.models);
      onStatusUpdated(res);
      if (res.connected && res.models.length > 0 && !res.models.includes(draft.model)) {
        setDraft((prev) => ({ ...prev, model: res.models[0] }));
      }
    } catch (err) {
      setTestResult({
        connected: false,
        provider: prov,
        endpoint: url,
        models: [],
        selected_model: draft.model,
        message: err instanceof Error ? err.message : 'Connection test failed.',
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveMessage(null);
    try {
      const saved = await api.updateSettings(draft);
      onSettingsUpdated(saved);
      setSaveMessage('Settings saved locally to SQLite.');
      const st = await api.getLLMStatus();
      setTestResult(st);
      setDiscoveredModels(st.models);
      onStatusUpdated(st);
    } catch (err) {
      setSaveMessage(err instanceof Error ? err.message : 'Could not save settings.');
    } finally {
      setSaving(false);
    }
  };

  const toggleProfile = (pid: string) => {
    setDraft((prev) => {
      const exists = prev.active_profiles.includes(pid);
      const next = exists
        ? prev.active_profiles.length > 1
          ? prev.active_profiles.filter((x) => x !== pid)
          : prev.active_profiles
        : [...prev.active_profiles, pid];
      return { ...prev, active_profiles: next };
    });
  };

  const weightTotal =
    draft.prediction_weights.multi_year_recurrence +
    draft.prediction_weights.recency +
    draft.prediction_weights.cross_relevance +
    draft.prediction_weights.profile_relevance +
    draft.prediction_weights.practice_gaps;

  return (
    <form onSubmit={handleSave} className="space-y-8 max-w-4xl">
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-[#E4E1DA] pb-5">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#78716C]">
            Local Inference & Study Engine Configuration
          </p>
          <h1 className="font-serif-editorial text-3xl font-medium text-[#18181B] mt-1">Settings</h1>
        </div>
        <button
          type="submit"
          disabled={saving}
          className="inline-flex items-center gap-2 text-xs font-semibold px-5 py-2.5 rounded-lg bg-[#1E3A5F] text-white hover:bg-[#162C49] disabled:opacity-50 cursor-pointer"
        >
          <Save className="w-4 h-4" />
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </header>

      {saveMessage && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-xs text-emerald-900 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-700" />
          {saveMessage}
        </div>
      )}

      {/* 2-Tier Selector Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E4E1DA] pb-2">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setActiveTab('student')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'student'
                ? 'bg-[#1E3A5F] text-white shadow-xs'
                : 'bg-white text-[#57534E] hover:bg-[#F5F4F0] border border-[#E4E1DA]'
            }`}
          >
            <GraduationCap className="w-4 h-4" />
            Student Preferences
            <span
              className={`text-[10px] font-mono px-1.5 py-0.5 rounded font-medium ${
                activeTab === 'student'
                  ? 'bg-white/20 text-white'
                  : 'bg-[#FAF9F6] text-[#78716C] border border-[#E4E1DA]'
              }`}
            >
              Peers & Study
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('developer')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'developer'
                ? 'bg-[#1E3A5F] text-white shadow-xs'
                : 'bg-white text-[#57534E] hover:bg-[#F5F4F0] border border-[#E4E1DA]'
            }`}
          >
            <Settings2 className="w-4 h-4" />
            Host & Model Controls
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-200 font-medium">
              Host Only
            </span>
          </button>
        </div>

        <span className="text-xs text-[#78716C]">
          {activeTab === 'student'
            ? 'Customizing practice goals for your exam target'
            : 'Configuring backend inference endpoints'}
        </span>
      </div>

      {/* STUDENT VIEW */}
      {activeTab === 'student' && (
        <div className="space-y-6">
          {/* Status Card */}
          <div className="bg-gradient-to-br from-blue-50/50 via-white to-emerald-50/40 border border-[#D0D7DE] rounded-xl p-5 shadow-xs">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </span>
                <div>
                  <h3 className="text-sm font-semibold text-[#18181B] flex items-center gap-2">
                    AI Question Generator Ready
                    <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-medium">
                      Cloud Powered
                    </span>
                  </h3>
                  <p className="text-xs text-[#57534E] mt-0.5">
                    Model: <strong className="font-medium text-[#1E3A5F]">Google Gemini 3.5 Flash-Lite</strong> • Cloud free tier (~1.5s generation • 0 GPU needed)
                  </p>
                </div>
              </div>
              <span className="text-[11px] font-mono text-[#78716C] bg-white border border-[#E4E1DA] px-2.5 py-1 rounded-md">
                100% Free • Unlimited Practice
              </span>
            </div>
            <p className="text-[11px] text-[#78716C] mt-3 border-t border-[#E4E1DA]/60 pt-2.5">
              💡 <strong>Zero Setup Needed:</strong> Questions generate securely via the host's cloud connection. Peers do not need to install Ollama, Python, or provide any secret keys.
            </p>
          </div>

          {/* Target Preparation Profiles */}
          <section className="bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-4">
            <div>
              <div className="flex items-center gap-2">
                <GraduationCap className="w-5 h-5 text-[#1E3A5F]" />
                <h2 className="font-serif-editorial text-xl font-medium text-[#18181B]">
                  Target Preparation Profiles
                </h2>
              </div>
              <p className="text-xs text-[#78716C] mt-0.5">
                Select your target NID campuses and disciplines. This tailors the themes, design scenarios, and archetypes generated for you.
              </p>
            </div>

            <div className="space-y-3">
              {taxonomy.preparation_profiles.map((p) => {
                const active = draft.active_profiles.includes(p.id);
                return (
                  <label
                    key={p.id}
                    className={`block p-4 rounded-xl border transition-colors cursor-pointer ${
                      active ? 'border-[#1E3A5F] bg-[#F7F9FC]' : 'border-[#E4E1DA] bg-white hover:border-[#D0D7DE]'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <input
                        type="checkbox"
                        checked={active}
                        onChange={() => toggleProfile(p.id)}
                        className="mt-1 accent-[#1E3A5F] cursor-pointer"
                      />
                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-sm font-semibold text-[#18181B]">{p.name}</span>
                          <span className="font-mono-exam text-[10px] px-1.5 py-0.5 rounded bg-[#FAF9F6] border border-[#E4E1DA] text-[#78716C]">
                            {p.campus}
                          </span>
                        </div>
                        <p className="text-xs text-[#57534E] leading-relaxed">{p.note}</p>
                        <div className="flex flex-wrap gap-1.5 pt-1">
                          {p.emphasis_areas.slice(0, 6).map((area) => (
                            <span
                              key={area}
                              className="text-[11px] px-2 py-0.5 rounded bg-white border border-[#E4E1DA] text-[#44403C]"
                            >
                              {area}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </label>
                );
              })}
            </div>
          </section>

          {/* Practice & Visual Preferences */}
          <section className="bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-4">
            <h2 className="font-serif-editorial text-xl font-medium text-[#18181B]">
              Practice & Sketch Preferences
            </h2>

            <div className="divide-y divide-[#E4E1DA]">
              <div className="flex items-center justify-between py-3">
                <div className="space-y-0.5 pr-4">
                  <span className="text-xs font-semibold text-[#18181B]">
                    Google Gemini Imagen 3 Prompt Exporter
                  </span>
                  <p className="text-[11px] text-[#78716C]">
                    Adds 1-click prompt exporter buttons to questions so you can copy and open sketch references in gemini.google.com with zero GPU load.
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={draft.drawthings_enabled}
                    onChange={(e) => setDraft({ ...draft, drawthings_enabled: e.target.checked })}
                    className="accent-[#1E3A5F] w-4 h-4 cursor-pointer"
                  />
                </label>
              </div>

              <div className="flex items-center justify-between py-3">
                <div className="space-y-0.5 pr-4">
                  <span className="text-xs font-semibold text-[#18181B]">
                    Strict Exam Originality Check
                  </span>
                  <p className="text-[11px] text-[#78716C]">
                    Ensures newly generated questions never repeat scenarios or objects from your recent practice sessions.
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={draft.strict_originality_check}
                    onChange={(e) => setDraft({ ...draft, strict_originality_check: e.target.checked })}
                    className="accent-[#1E3A5F] w-4 h-4 cursor-pointer"
                  />
                </label>
              </div>
            </div>
          </section>

          {/* Switch to Developer Controls */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl bg-[#FAF9F6] border border-[#E4E1DA] text-xs text-[#78716C]">
            <span>Are you the Mac host? Need to configure API keys, local models, or inference settings?</span>
            <button
              type="button"
              onClick={() => setActiveTab('developer')}
              className="text-[#1E3A5F] font-semibold hover:underline inline-flex items-center gap-1 cursor-pointer"
            >
              Open Host Controls →
            </button>
          </div>
        </div>
      )}

      {/* DEVELOPER / HOST VIEW */}
      {activeTab === 'developer' && (
        <div className="space-y-8">
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3 text-xs text-amber-950">
            <Lock className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-amber-900">Host & Developer Controls</p>
              <p className="text-[11px] text-amber-800 mt-0.5">
                These settings configure the local backend server, cloud API credentials, and inference models. Peers practicing over the network do not need to touch anything here.
              </p>
            </div>
          </div>

          {/* 1. Local LLM Provider Configuration */}
          <section className="bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-[#1E3A5F]" />
            <h2 className="font-serif-editorial text-xl font-medium">Local LLM Provider</h2>
          </div>
          <span className="inline-flex items-center gap-1.5 text-[11px] font-medium px-2.5 py-1 rounded bg-[#FAF9F6] border border-[#E4E1DA] text-[#44403C]">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-700" />
            100% Local Proxy • No Cloud Fallback
          </span>
        </div>

        {/* Provider cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            {
              id: 'gemini' as ProviderType,
              label: 'Google Gemini (Free Cloud)',
              hint: 'gemini-3.5-flash-lite • 0 GPU Needed',
            },
            {
              id: 'groq' as ProviderType,
              label: 'Groq Cloud (Free Cloud)',
              hint: 'llama-3.3-70b • 0 GPU Needed',
            },
            {
              id: 'ollama' as ProviderType,
              label: 'Ollama (Local)',
              hint: 'Default: http://localhost:11434',
            },
            {
              id: 'lmstudio' as ProviderType,
              label: 'LM Studio (Local)',
              hint: 'Default: http://localhost:1234/v1',
            },
            {
              id: 'custom_openai' as ProviderType,
              label: 'Custom OpenAI-Compatible',
              hint: 'LocalAI, vLLM, OpenRouter, etc.',
            },
          ].map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => {
                setDraft({ ...draft, provider: p.id });
                handleTestAndDiscover(p.id);
              }}
              className={`p-3.5 rounded-lg border text-left transition-colors cursor-pointer ${
                draft.provider === p.id
                  ? 'border-[#1E3A5F] bg-[#1E3A5F]/5'
                  : 'border-[#E4E1DA] bg-white hover:bg-[#FAF9F6]'
              }`}
            >
              <div className="text-sm font-semibold text-[#18181B]">{p.label}</div>
              <div className="text-[11px] font-mono-exam text-[#78716C] mt-0.5">{p.hint}</div>
            </button>
          ))}
        </div>

        {/* Endpoint & Optional Local API Key */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-[#44403C] mb-1">Local API Endpoint</label>
            <input
              type="url"
              value={currentEndpoint}
              onChange={(e) => handleEndpointChange(e.target.value)}
              className="w-full font-mono-exam text-xs px-3 py-2 rounded-lg border border-[#D8D4CB]"
            />
            <p className="text-[11px] text-[#78716C] mt-1">
              {draft.provider === 'ollama'
                ? 'Chat endpoint: <base>/api/chat • Models: <base>/api/tags'
                : 'Chat endpoint: <base>/chat/completions • Models: <base>/models'}
            </p>
          </div>

          <div>
            <label className="block text-xs font-medium text-[#44403C] mb-1">
              Model Selection (Never Hardcoded)
            </label>
            <div className="flex gap-2">
              {discoveredModels.length > 0 ? (
                <select
                  value={discoveredModels.includes(draft.model) ? draft.model : ''}
                  onChange={(e) => setDraft({ ...draft, model: e.target.value })}
                  className="flex-1 font-mono-exam text-xs px-3 py-2 rounded-lg border border-[#D8D4CB] bg-white"
                >
                  <option value="" disabled>
                    Choose discovered model...
                  </option>
                  {discoveredModels.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  value={draft.model}
                  onChange={(e) => setDraft({ ...draft, model: e.target.value })}
                  placeholder="e.g. qwen2.5:7b or llama3.1:8b"
                  className="flex-1 font-mono-exam text-xs px-3 py-2 rounded-lg border border-[#D8D4CB]"
                />
              )}
              <button
                type="button"
                onClick={() => handleTestAndDiscover()}
                disabled={testing}
                className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-2 rounded-lg border border-[#D8D4CB] bg-[#FAF9F6] hover:bg-stone-100 cursor-pointer shrink-0"
              >
                {testing ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <RefreshCw className="w-3.5 h-3.5" />
                )}
                Test & Discover
              </button>
            </div>
            {discoveredModels.length > 0 && (
              <input
                type="text"
                value={draft.model}
                onChange={(e) => setDraft({ ...draft, model: e.target.value })}
                placeholder="Or type custom model identifier..."
                className="mt-1.5 w-full font-mono-exam text-[11px] px-2.5 py-1.5 rounded border border-[#E4E1DA] text-[#57534E]"
              />
            )}
          </div>
        </div>

        {draft.provider === 'gemini' && (
          <div className="bg-blue-50/50 border border-blue-200 rounded-lg p-3.5 space-y-2">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-semibold text-[#1E3A5F]">
                Google AI Studio API Key (100% Free • No Credit Card Required)
              </label>
              {(draft.has_gemini_key || draft.gemini_api_key) && (
                <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded-full">
                  <ShieldCheck className="w-3 h-3" /> Key securely saved on server
                </span>
              )}
            </div>
            <input
              type="password"
              value={draft.gemini_api_key || ''}
              onChange={(e) => setDraft({ ...draft, gemini_api_key: e.target.value })}
              placeholder={draft.has_gemini_key ? '•••••••• (Saved on host - enter new key to replace)' : 'Paste AIzaSy... key here'}
              className="w-full font-mono-exam text-xs px-3 py-2 rounded-lg border border-[#D8D4CB] bg-white"
            />
            <p className="text-[11px] text-[#78716C]">
              Get your free key at <a href="https://aistudio.google.com" target="_blank" rel="noreferrer" className="text-[#1E3A5F] underline font-medium">aistudio.google.com</a>. Defaults to <code className="bg-white px-1.5 py-0.5 rounded border border-blue-200 font-mono text-blue-900">gemini-3.5-flash-lite</code> (1500 free questions/day). Peers using your shared tunnel can practice without ever seeing your key.
            </p>
          </div>
        )}

        {draft.provider === 'groq' && (
          <div className="bg-orange-50/50 border border-orange-200 rounded-lg p-3.5 space-y-2">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-semibold text-orange-950">
                Groq Cloud API Key (100% Free • No Credit Card Required)
              </label>
              {(draft.has_groq_key || draft.groq_api_key) && (
                <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded-full">
                  <ShieldCheck className="w-3 h-3" /> Key securely saved on server
                </span>
              )}
            </div>
            <input
              type="password"
              value={draft.groq_api_key || ''}
              onChange={(e) => setDraft({ ...draft, groq_api_key: e.target.value })}
              placeholder={draft.has_groq_key ? '•••••••• (Saved on host - enter new key to replace)' : 'Paste gsk_... key here'}
              className="w-full font-mono-exam text-xs px-3 py-2 rounded-lg border border-[#D8D4CB] bg-white"
            />
            <p className="text-[11px] text-[#78716C]">
              Get your free key at <a href="https://console.groq.com" target="_blank" rel="noreferrer" className="text-orange-900 underline font-medium">console.groq.com</a>. Defaults to <code className="bg-white px-1.5 py-0.5 rounded border border-orange-200 font-mono text-orange-900">llama-3.3-70b-versatile</code> (14,400 free questions/day).
            </p>
          </div>
        )}

        {draft.provider === 'custom_openai' && (
          <div>
            <label className="block text-xs font-medium text-[#44403C] mb-1">
              Optional Local Bearer Token (only if your local server requires one)
            </label>
            <input
              type="password"
              value={draft.custom_api_key}
              onChange={(e) => setDraft({ ...draft, custom_api_key: e.target.value })}
              placeholder="Leave empty for standard local servers"
              className="w-full max-w-md font-mono-exam text-xs px-3 py-2 rounded-lg border border-[#D8D4CB]"
            />
          </div>
        )}

        {/* Live Connection Diagnostic Box */}
        {testResult && (
          <div
            className={`rounded-lg border p-3.5 text-xs flex items-start gap-2.5 ${
              testResult.connected
                ? 'bg-emerald-50 border-emerald-200 text-emerald-950'
                : 'bg-amber-50 border-amber-200 text-amber-950'
            }`}
          >
            {testResult.connected ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-700 shrink-0 mt-0.5" />
            ) : (
              <WifiOff className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
            )}
            <div className="space-y-0.5">
              <div className="font-semibold">
                {testResult.connected ? 'Connected' : 'Disconnected'} ({testResult.endpoint}
                {testResult.latency_ms != null ? ` • ${testResult.latency_ms}ms` : ''})
              </div>
              <p className="leading-relaxed">{testResult.message}</p>
            </div>
          </div>
        )}

        {/* Generation Parameters */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2 border-t border-[#ECEAE4]">
          <div>
            <label className="block text-xs font-medium text-[#44403C] mb-1">
              Temperature ({draft.temperature.toFixed(2)})
            </label>
            <input
              type="range"
              min={0}
              max={1.2}
              step={0.05}
              value={draft.temperature}
              onChange={(e) => setDraft({ ...draft, temperature: parseFloat(e.target.value) })}
              className="w-full accent-[#1E3A5F]"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-[#44403C] mb-1">Max Output Tokens</label>
            <input
              type="number"
              min={512}
              max={8192}
              step={128}
              value={draft.max_tokens}
              onChange={(e) => setDraft({ ...draft, max_tokens: Number(e.target.value) || 2400 })}
              className="w-full font-mono-exam text-xs px-2.5 py-1.5 rounded-lg border border-[#D8D4CB]"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-[#44403C] mb-1">JSON Retries</label>
            <input
              type="number"
              min={0}
              max={5}
              value={draft.max_retries}
              onChange={(e) => setDraft({ ...draft, max_retries: Number(e.target.value) || 0 })}
              className="w-full font-mono-exam text-xs px-2.5 py-1.5 rounded-lg border border-[#D8D4CB]"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-[#44403C] mb-1">Timeout (sec)</label>
            <input
              type="number"
              min={15}
              max={600}
              value={draft.timeout_seconds}
              onChange={(e) => setDraft({ ...draft, timeout_seconds: Number(e.target.value) || 120 })}
              className="w-full font-mono-exam text-xs px-2.5 py-1.5 rounded-lg border border-[#D8D4CB]"
            />
          </div>
        </div>

        <div className="flex flex-wrap gap-6 pt-1 text-xs">
          <label className="inline-flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={draft.enforce_json_mode}
              onChange={(e) => setDraft({ ...draft, enforce_json_mode: e.target.checked })}
              className="accent-[#1E3A5F]"
            />
            Request provider JSON format mode (auto-falls back if unsupported)
          </label>
          <label className="inline-flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={draft.strict_originality_check}
              onChange={(e) => setDraft({ ...draft, strict_originality_check: e.target.checked })}
              className="accent-[#1E3A5F]"
            />
            Enforce automatic originality & anti-duplication retry check
          </label>
        </div>
      </section>

      {/* 1b. Reference Sketch Generation Engine */}
      <section className="bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <ImageIcon className="w-5 h-5 text-[#1E3A5F]" />
            <div>
              <h2 className="font-serif-editorial text-xl font-medium">
                Reference Sketch Generation Engine
              </h2>
              <p className="text-xs text-[#78716C]">
                Choose how visual reference sheets, exploded views, and product sketches are generated after your practice attempt.
              </p>
            </div>
          </div>
          <label className="inline-flex items-center gap-2 text-xs font-medium text-[#44403C] cursor-pointer bg-[#FAF9F6] border border-[#E4E1DA] px-3 py-1.5 rounded-lg">
            <input
              type="checkbox"
              checked={draft.drawthings_enabled}
              onChange={(e) => setDraft({ ...draft, drawthings_enabled: e.target.checked })}
              className="accent-[#1E3A5F]"
            />
            Enable Post-Attempt Reference Sketches
          </label>
        </div>

        {/* Engine selector cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Option 1: Gemini Imagen 3 (Recommended) */}
          <div
            onClick={() => setDraft({ ...draft, sketch_provider: 'gemini_imagen' })}
            className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
              draft.sketch_provider === 'gemini_imagen'
                ? 'border-[#1E3A5F] bg-[#F7F9FC] shadow-xs'
                : 'border-[#E4E1DA] bg-white hover:border-[#CBD5E1]'
            }`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-semibold text-[#18181B] flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                Gemini Imagen 3
              </span>
              <span className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800">
                Recommended
              </span>
            </div>
            <p className="text-[11px] text-[#57534E] leading-relaxed">
              Industrial presentation boards with exploded views, circular detail zoom bubbles, Copic shading & crisp English labels. Zero Mac RAM.
            </p>
          </div>

          {/* Option 2: Pollinations FLUX.1 (Free Cloud) */}
          <div
            onClick={() => setDraft({ ...draft, sketch_provider: 'pollinations_flux' })}
            className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
              draft.sketch_provider === 'pollinations_flux'
                ? 'border-[#1E3A5F] bg-[#F7F9FC] shadow-xs'
                : 'border-[#E4E1DA] bg-white hover:border-[#CBD5E1]'
            }`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-semibold text-[#18181B] flex items-center gap-1.5">
                Pollinations FLUX.1
              </span>
              <span className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded bg-blue-100 text-blue-800">
                100% Free
              </span>
            </div>
            <p className="text-[11px] text-[#57534E] leading-relaxed">
              Completely free cloud generator. Zero API key or login required. Crisp geometry and marker line-art in ~10 seconds.
            </p>
          </div>

          {/* Option 3: Local Draw Things */}
          <div
            onClick={() => setDraft({ ...draft, sketch_provider: 'drawthings' })}
            className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
              draft.sketch_provider === 'drawthings'
                ? 'border-[#1E3A5F] bg-[#F7F9FC] shadow-xs'
                : 'border-[#E4E1DA] bg-white hover:border-[#CBD5E1]'
            }`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-semibold text-[#18181B] flex items-center gap-1.5">
                Draw Things (Local)
              </span>
              <span className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded bg-stone-100 text-stone-700">
                Offline
              </span>
            </div>
            <p className="text-[11px] text-[#57534E] leading-relaxed">
              Runs locally on your Mac via Draw Things HTTP API (127.0.0.1:7860). Fully private, offline SD 1.5 / SDXL.
            </p>
          </div>

          {/* Option 4: OpenAI DALL-E 3 */}
          <div
            onClick={() => setDraft({ ...draft, sketch_provider: 'openai_dalle' })}
            className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
              draft.sketch_provider === 'openai_dalle'
                ? 'border-[#1E3A5F] bg-[#F7F9FC] shadow-xs'
                : 'border-[#E4E1DA] bg-white hover:border-[#CBD5E1]'
            }`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-semibold text-[#18181B] flex items-center gap-1.5">
                OpenAI DALL-E 3
              </span>
              <span className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded bg-purple-100 text-purple-800">
                Cloud
              </span>
            </div>
            <p className="text-[11px] text-[#57534E] leading-relaxed">
              High-adherence OpenAI cloud image generation. Requires an active OpenAI API key.
            </p>
          </div>
        </div>

        {/* Engine-specific settings */}
        {draft.sketch_provider === 'gemini_imagen' && (
          <div className="bg-[#FAF9F6] border border-[#E4E1DA] rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-[#1E3A5F] flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5" />
                Google Gemini API Key
              </label>
              <a
                href="https://aistudio.google.com/app/apikey"
                target="_blank"
                rel="noreferrer"
                className="text-[11px] text-[#1E3A5F] hover:underline inline-flex items-center gap-1"
              >
                Get Free API Key from Google AI Studio
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>

            <div className="relative">
              <input
                type={showGeminiKey ? 'text' : 'password'}
                value={draft.gemini_api_key || ''}
                onChange={(e) => setDraft({ ...draft, gemini_api_key: e.target.value })}
                placeholder="Paste your Gemini API key here (AIzaSy...)"
                className="w-full font-mono-exam text-xs px-3 py-2 pr-10 rounded-lg border border-[#D8D4CB] bg-white text-[#18181B] focus:outline-none focus:border-[#1E3A5F]"
              />
              <button
                type="button"
                onClick={() => setShowGeminiKey(!showGeminiKey)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#78716C] hover:text-[#18181B] p-1 cursor-pointer"
                title={showGeminiKey ? 'Hide API Key' : 'Show API Key'}
              >
                {showGeminiKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
            </div>

            <div className="flex items-center gap-2 text-[11px] text-[#57534E]">
              <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>
                Stored securely and locally in your SQLite database on this Mac (<span className="font-mono-exam">dat_practice_lab.db</span>). Never sent to any third party other than Google's official API endpoint.
              </span>
            </div>
          </div>
        )}

        {draft.sketch_provider === 'pollinations_flux' && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 flex items-start gap-3">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <div className="space-y-1 text-xs text-emerald-950">
              <p className="font-semibold">Pollinations FLUX.1 Engine is Ready</p>
              <p className="text-[11px] leading-relaxed text-emerald-900">
                100% Free, zero signup, zero API key or credit card needed. Runs entirely in the cloud, taking 0 MB of RAM on your Mac. Generates 1024×1024 industrial sketches in ~10 seconds.
              </p>
            </div>
          </div>
        )}

        {draft.sketch_provider === 'openai_dalle' && (
          <div className="bg-[#FAF9F6] border border-[#E4E1DA] rounded-lg p-4 space-y-3">
            <label className="text-xs font-semibold text-[#1E3A5F] flex items-center gap-1.5">
              <Key className="w-3.5 h-3.5" />
              OpenAI API Key
            </label>
            <div className="relative">
              <input
                type={showOpenAIKey ? 'text' : 'password'}
                value={draft.openai_api_key || ''}
                onChange={(e) => setDraft({ ...draft, openai_api_key: e.target.value })}
                placeholder="sk-proj-..."
                className="w-full font-mono-exam text-xs px-3 py-2 pr-10 rounded-lg border border-[#D8D4CB] bg-white text-[#18181B] focus:outline-none focus:border-[#1E3A5F]"
              />
              <button
                type="button"
                onClick={() => setShowOpenAIKey(!showOpenAIKey)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#78716C] hover:text-[#18181B] p-1 cursor-pointer"
                title={showOpenAIKey ? 'Hide API Key' : 'Show API Key'}
              >
                {showOpenAIKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
            </div>
            <p className="text-[11px] text-[#57534E]">
              Stored locally on your Mac. Used for DALL-E 3 image generation requests.
            </p>
          </div>
        )}

        {draft.sketch_provider === 'drawthings' && (
          <div className="space-y-4 pt-1">
            <div className="flex flex-wrap items-end gap-3">
              <div className="flex-1 min-w-[240px]">
                <label className="block text-xs font-medium text-[#44403C] mb-1">
                  Draw Things HTTP API Endpoint
                </label>
                <input
                  type="url"
                  value={draft.drawthings_base_url}
                  onChange={(e) => setDraft({ ...draft, drawthings_base_url: e.target.value })}
                  className="w-full font-mono-exam text-xs px-3 py-2 rounded-lg border border-[#D8D4CB]"
                />
              </div>
              <button
                type="button"
                onClick={handleTestDrawThings}
                disabled={testingDt}
                className="inline-flex items-center gap-1.5 text-xs font-medium px-3.5 py-2 rounded-lg border border-[#D8D4CB] bg-[#FAF9F6] hover:bg-stone-100 cursor-pointer"
              >
                {testingDt ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <RefreshCw className="w-3.5 h-3.5" />
                )}
                Test Draw Things
              </button>
            </div>

            {dtStatus && (
              <div
                className={`rounded-lg border p-3.5 text-xs flex items-start gap-2.5 ${
                  dtStatus.connected
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-950'
                    : 'bg-amber-50 border-amber-200 text-amber-950'
                }`}
              >
                {dtStatus.connected ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-700 shrink-0 mt-0.5" />
                ) : (
                  <WifiOff className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                )}
                <div className="space-y-0.5">
                  <div className="font-semibold">
                    {dtStatus.connected ? 'Draw Things HTTP Connected' : 'Draw Things HTTP Not Reachable'} (
                    {dtStatus.endpoint}
                    {dtStatus.latency_ms != null ? ` • ${dtStatus.latency_ms}ms` : ''})
                  </div>
                  <p className="leading-relaxed">{dtStatus.message}</p>
                </div>
              </div>
            )}

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
              <div>
                <label className="block text-xs font-medium text-[#44403C] mb-1">Width (px)</label>
                <input
                  type="number"
                  min={256}
                  max={1024}
                  step={64}
                  value={draft.drawthings_width}
                  onChange={(e) => setDraft({ ...draft, drawthings_width: Number(e.target.value) || 512 })}
                  className="w-full font-mono-exam text-xs px-2.5 py-1.5 rounded-lg border border-[#D8D4CB]"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-[#44403C] mb-1">Height (px)</label>
                <input
                  type="number"
                  min={256}
                  max={1024}
                  step={64}
                  value={draft.drawthings_height}
                  onChange={(e) => setDraft({ ...draft, drawthings_height: Number(e.target.value) || 512 })}
                  className="w-full font-mono-exam text-xs px-2.5 py-1.5 rounded-lg border border-[#D8D4CB]"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-[#44403C] mb-1">
                  Steps (8 LCM / 20 std)
                </label>
                <input
                  type="number"
                  min={4}
                  max={50}
                  value={draft.drawthings_steps}
                  onChange={(e) => setDraft({ ...draft, drawthings_steps: Number(e.target.value) || 8 })}
                  className="w-full font-mono-exam text-xs px-2.5 py-1.5 rounded-lg border border-[#D8D4CB]"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-[#44403C] mb-1">
                  CFG (2.0 LCM / 7.0 std)
                </label>
                <input
                  type="number"
                  min={1}
                  max={15}
                  step={0.5}
                  value={draft.drawthings_cfg_scale}
                  onChange={(e) =>
                    setDraft({ ...draft, drawthings_cfg_scale: parseFloat(e.target.value) || 2.0 })
                  }
                  className="w-full font-mono-exam text-xs px-2.5 py-1.5 rounded-lg border border-[#D8D4CB]"
                />
              </div>
            </div>

            <label className="inline-flex items-center gap-2 text-xs text-[#44403C] cursor-pointer pt-1">
              <input
                type="checkbox"
                checked={draft.auto_unload_llm_for_sketch}
                onChange={(e) => setDraft({ ...draft, auto_unload_llm_for_sketch: e.target.checked })}
                className="accent-[#1E3A5F]"
              />
              Auto-unload Ollama model before generating a sketch (recommended on 8 GB Apple Silicon Macs)
            </label>
          </div>
        )}
      </section>

      {/* 3. Configurable Prediction Scoring Weights */}
      <section className="bg-white border border-[#E4E1DA] rounded-xl p-6 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-[#1E3A5F]" />
            <h2 className="font-serif-editorial text-xl font-medium">
              Practice-Priority Scoring Weights
            </h2>
          </div>
          <div className="flex items-center gap-3">
            <span className="font-mono-exam text-xs text-[#57534E]">
              Sum: {weightTotal.toFixed(0)}% (auto-normalised)
            </span>
            <button
              type="button"
              onClick={() =>
                setDraft({
                  ...draft,
                  prediction_weights: {
                    multi_year_recurrence: 30,
                    recency: 20,
                    cross_relevance: 20,
                    profile_relevance: 15,
                    practice_gaps: 15,
                  },
                })
              }
              className="text-xs text-[#1E3A5F] hover:underline cursor-pointer"
            >
              Reset Defaults (30/20/20/15/15)
            </button>
          </div>
        </div>

        <div className="space-y-3">
          {(
            [
              ['multi_year_recurrence', 'Multi-year recurrence (default 30%)'],
              ['recency', 'Recency across recent exam years (default 20%)'],
              ['cross_relevance', 'Cross-category & cross-programme relevance (default 20%)'],
              ['profile_relevance', 'Relevance to selected preparation profile(s) (default 15%)'],
              ['practice_gaps', "Student's under-practised & weak-area gaps (default 15%)"],
            ] as const
          ).map(([key, label]) => (
            <div key={key} className="flex items-center justify-between gap-4 text-xs">
              <span className="text-[#27272A]">{label}</span>
              <div className="flex items-center gap-3 shrink-0">
                <input
                  type="range"
                  min={0}
                  max={60}
                  step={5}
                  value={draft.prediction_weights[key]}
                  onChange={(e) =>
                    setDraft({
                      ...draft,
                      prediction_weights: {
                        ...draft.prediction_weights,
                        [key]: Number(e.target.value),
                      },
                    })
                  }
                  className="w-36 accent-[#1E3A5F]"
                />
                <span className="font-mono-exam w-10 text-right font-semibold">
                  {draft.prediction_weights[key]}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>
        </div>
      )}
    </form>
  );
};
