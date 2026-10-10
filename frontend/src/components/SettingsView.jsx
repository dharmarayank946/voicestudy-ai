import React, { useState, useEffect } from 'react';
import { Settings, ShieldCheck, Database, Radio, Cpu, Key, Save, CheckCircle2, Sliders } from 'lucide-react';

export default function SettingsView({ healthData }) {
  const qdrant = healthData?.vector_memory || {};
  const voice = healthData?.voice || {};
  const agents = healthData?.agents || {};

  const [defaultNumQuestions, setDefaultNumQuestions] = useState(5);
  const [defaultDifficulty, setDefaultDifficulty] = useState('medium');
  const [enableVoiceTts, setEnableVoiceTts] = useState(true);
  const [saveNotice, setSaveNotice] = useState(null);

  useEffect(() => {
    const savedCount = localStorage.getItem('voicestudy_pref_num_q');
    const savedDiff = localStorage.getItem('voicestudy_pref_diff');
    const savedTts = localStorage.getItem('voicestudy_pref_tts');

    if (savedCount) setDefaultNumQuestions(Number(savedCount));
    if (savedDiff) setDefaultDifficulty(savedDiff);
    if (savedTts !== null) setEnableVoiceTts(savedTts === 'true');
  }, []);

  const handleSavePreferences = (e) => {
    e.preventDefault();
    localStorage.setItem('voicestudy_pref_num_q', defaultNumQuestions.toString());
    localStorage.setItem('voicestudy_pref_diff', defaultDifficulty);
    localStorage.setItem('voicestudy_pref_tts', enableVoiceTts.toString());

    setSaveNotice('Settings saved successfully!');
    setTimeout(() => setSaveNotice(null), 3500);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '900px', margin: '0 auto' }}>
      <div>
        <h3 style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Settings size={24} color="var(--accent-cyan)" /> VoiceStudy AI Settings & Status
        </h3>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          System health connectivity, vector database stats, and user preferences
        </p>
      </div>

      {/* Save Confirmation Notice */}
      {saveNotice && (
        <div style={{
          background: 'rgba(16, 185, 129, 0.15)',
          border: '1px solid rgba(16, 185, 129, 0.4)',
          borderRadius: '10px',
          padding: '0.75rem 1rem',
          color: 'var(--accent-emerald)',
          fontSize: '0.85rem',
          fontWeight: '600',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          <CheckCircle2 size={18} />
          {saveNotice}
        </div>
      )}

      {/* Integration Status Cards */}
      <div className="glass-card">
        <h4 style={{ fontSize: '1.1rem', fontWeight: '700', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <ShieldCheck size={20} color="var(--accent-emerald)" /> System Health & Connectivity
        </h4>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
          <div style={{ padding: '1rem', background: 'rgba(10, 16, 26, 0.7)', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <Database size={18} color="var(--accent-cyan)" />
              <strong style={{ fontSize: '0.9rem' }}>Qdrant Vector DB</strong>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Status: <span style={{ color: 'var(--accent-emerald)', fontWeight: '600' }}>{qdrant.status || 'Connected'}</span><br />
              Mode: <span style={{ color: 'var(--text-primary)' }}>{qdrant.storage_path || './qdrant_data'}</span><br />
              Total Vectors: <span style={{ color: 'var(--accent-cyan)' }}>{qdrant.total_memories || 0}</span>
            </div>
          </div>

          <div style={{ padding: '1rem', background: 'rgba(10, 16, 26, 0.7)', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <Cpu size={18} color="var(--accent-purple)" />
              <strong style={{ fontSize: '0.9rem' }}>Lyzr Agent Pipeline</strong>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Orchestrator: <span style={{ color: 'var(--accent-emerald)' }}>Active</span><br />
              Memory Agent: <span style={{ color: 'var(--accent-emerald)' }}>Active</span><br />
              Quiz Agent: <span style={{ color: 'var(--accent-emerald)' }}>Active</span>
            </div>
          </div>

          <div style={{ padding: '1rem', background: 'rgba(10, 16, 26, 0.7)', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <Radio size={18} color="var(--accent-emerald)" />
              <strong style={{ fontSize: '0.9rem' }}>Omi Voice Adapter</strong>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              SDK Configured: <span style={{ color: voice.omi_sdk_configured ? 'var(--accent-emerald)' : 'var(--accent-amber)' }}>
                {voice.omi_sdk_configured ? 'Yes' : 'Adapter Interface Active'}
              </span><br />
              Web Speech Fallback: <span style={{ color: 'var(--accent-emerald)' }}>Active</span>
            </div>
          </div>
        </div>
      </div>

      {/* User Preferences Form */}
      <div className="glass-card">
        <h4 style={{ fontSize: '1.1rem', fontWeight: '700', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Sliders size={18} color="var(--accent-cyan)" /> Application Preferences
        </h4>

        <form onSubmit={handleSavePreferences} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>Default Quiz Question Count</label>
              <select
                className="custom-input"
                value={defaultNumQuestions}
                onChange={(e) => setDefaultNumQuestions(Number(e.target.value))}
              >
                <option value={3}>3 Questions</option>
                <option value={5}>5 Questions</option>
                <option value={10}>10 Questions</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>Default Difficulty</label>
              <select
                className="custom-input"
                value={defaultDifficulty}
                onChange={(e) => setDefaultDifficulty(e.target.value)}
              >
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <input
              type="checkbox"
              id="ttsToggle"
              checked={enableVoiceTts}
              onChange={(e) => setEnableVoiceTts(e.target.checked)}
              style={{ width: '18px', height: '18px', cursor: 'pointer' }}
            />
            <label htmlFor="ttsToggle" style={{ fontSize: '0.88rem', color: 'var(--text-primary)', cursor: 'pointer' }}>
              Enable Voice Speech Synthesis (Text-to-Speech playback for responses)
            </label>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
            <button type="submit" className="btn-primary" style={{ gap: '0.5rem' }}>
              <Save size={16} /> Save Settings
            </button>
          </div>
        </form>
      </div>

      {/* Environment Variable Keys Reference */}
      <div className="glass-card">
        <h4 style={{ fontSize: '1.1rem', fontWeight: '700', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Key size={18} color="var(--accent-amber)" /> Environment Variables (.env)
        </h4>
        <p style={{ fontSize: '0.83rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          Configure API keys in your root <code>.env</code> file:
        </p>

        <pre style={{
          background: 'rgba(10, 16, 26, 0.95)',
          padding: '1.25rem',
          borderRadius: '12px',
          border: '1px solid var(--border-subtle)',
          fontSize: '0.82rem',
          color: 'var(--accent-cyan)',
          lineHeight: '1.7',
          overflowX: 'auto'
        }}>
{`# Lyzr Agent API Key
LYZR_API_KEY=your_lyzr_api_key_here

# LLM Provider Key (OpenAI / Groq)
LLM_API_KEY=your_openai_or_groq_api_key_here
LLM_MODEL=gpt-4o-mini

# Qdrant Vector DB Configuration
QDRANT_URL=:memory:
QDRANT_API_KEY=your_qdrant_cloud_key_if_used

# Omi Voice Integration
OMI_API_KEY=your_omi_api_key_here
OMI_WEBHOOK_SECRET=your_omi_webhook_secret_here`}
        </pre>
      </div>
    </div>
  );
}