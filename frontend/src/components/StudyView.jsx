import React, { useState } from 'react';
import { Send, Sparkles, Cpu, Layers, Volume2, VolumeX, Trash2, CheckCircle, AlertTriangle, ShieldCheck } from 'lucide-react';
import OmiStatusCard from './OmiStatusCard';
import { speechService } from '../services/speech';

export default function StudyView({ onProcessInput, isProcessing, responseData }) {
  const [inputVal, setInputVal] = useState('');
  const [conversationHistory, setConversationHistory] = useState([]);
  const [speakerEnabled, setSpeakerEnabled] = useState(true);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputVal.trim() || isProcessing) return;
    
    const query = inputVal.trim();
    setInputVal('');

    const newHistory = [...conversationHistory, { role: 'user', content: query }];
    setConversationHistory(newHistory);

    const result = await onProcessInput(query, 'text_fallback', { history: newHistory });
    if (result && result.message) {
      setConversationHistory(prev => [...prev, { role: 'assistant', content: result.message }]);
      if (speakerEnabled) {
        speechService.speak(result.message);
      }
    }
  };

  const handleClearHistory = () => {
    setConversationHistory([]);
    speechService.stopSpeaking();
  };

  const sampleQueries = [
    { label: 'OS Paging', query: 'Explain how Virtual Memory and Page Faults work in Operating Systems.' },
    { label: 'SOLID Design', query: 'What are the SOLID principles in Software Engineering?' },
    { label: 'Networks TCP', query: 'Compare TCP and UDP transport layer protocols.' },
    { label: 'DBMS 2PL', query: 'Explain how Two-Phase Locking ensures concurrency control in DBMS.' },
    { label: 'Python Async', query: 'How does Python GIL affect asyncio and multiprocessing?' },
    { label: 'Calculus', query: 'Explain the role of gradient descent in machine learning mathematics.' }
  ];

  const providerStatus = responseData?.ai_provider;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '1.5rem' }}>
      {/* Main Agent Interaction Panel */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        
        {/* AI Provider Status Banner */}
        <div className="glass-card" style={{
          padding: '0.85rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          justify: 'space-between',
          borderColor: providerStatus?.is_real_ai ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)',
          background: providerStatus?.is_real_ai ? 'rgba(16, 185, 129, 0.08)' : 'rgba(245, 158, 11, 0.08)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            {providerStatus?.is_real_ai ? (
              <ShieldCheck size={20} color="var(--accent-emerald)" />
            ) : (
              <AlertTriangle size={20} color="var(--accent-amber)" />
            )}
            <div>
              <div style={{ fontSize: '0.88rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                Provider: {providerStatus?.provider_name || 'Offline Engine Fallback'}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                {providerStatus?.notice || 'Intelligent AI answers ready across all CS & General subjects.'}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {conversationHistory.length > 0 && (
              <button 
                className="btn-secondary" 
                onClick={handleClearHistory}
                style={{ fontSize: '0.8rem', padding: '0.4rem 0.75rem', gap: '0.35rem' }}
                title="Clear current conversation context"
              >
                <Trash2 size={14} color="var(--accent-rose)" /> Clear Context
              </button>
            )}
          </div>
        </div>

        {/* Input Box */}
        <div className="glass-card">
          <h3 style={{ fontSize: '1.1rem', fontWeight: '700', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sparkles size={18} color="var(--accent-cyan)" /> AI Tutor Study Workspace
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
            Ask questions about Software Engineering, OS, DBMS, Networks, Mathematics, Programming, or general topics.
          </p>

          <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.75rem' }}>
            <input
              type="text"
              className="custom-input"
              placeholder="Ask any study question e.g., Explain Virtual Memory in Operating Systems..."
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
            />
            <button className="btn-primary" type="submit" disabled={isProcessing || !inputVal.trim()}>
              <Send size={18} /> {isProcessing ? 'Thinking...' : 'Ask AI'}
            </button>
            <button
              className="btn-secondary"
              type="button"
              onClick={() => {
                setSpeakerEnabled(!speakerEnabled);
                if (speakerEnabled) speechService.stopSpeaking();
              }}
              title={speakerEnabled ? "Mute Spoken Answers" : "Enable Spoken Answers"}
              style={{ padding: '0.75rem' }}
            >
              {speakerEnabled ? <Volume2 size={18} color="var(--accent-emerald)" /> : <VolumeX size={18} color="var(--text-muted)" />}
            </button>
          </form>

          {/* Subject Preset Chips */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '1rem' }}>
            {sampleQueries.map((item, i) => (
              <button
                key={i}
                className="btn-secondary"
                onClick={() => setInputVal(item.query)}
                style={{ fontSize: '0.78rem', padding: '0.35rem 0.75rem' }}
              >
                <span style={{ color: 'var(--accent-cyan)', fontWeight: '600' }}>[{item.label}]</span> {item.query.slice(0, 32)}...
              </button>
            ))}
          </div>
        </div>

        {/* Agent Response Visualization */}
        {responseData && (
          <div className="glass-card" style={{ borderColor: 'rgba(0, 242, 254, 0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '1rem', borderBottom: '1px solid var(--border-subtle)', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <Cpu size={20} color="var(--accent-cyan)" />
                <div>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                    Agent Executed: <span style={{ color: 'var(--accent-cyan)' }}>{responseData.agent_executed}</span>
                  </h4>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Intent: <strong style={{ color: 'var(--accent-emerald)' }}>{responseData.intent}</strong>   Subject: <strong>{responseData.orchestration?.subject}</strong>   Topic: {responseData.orchestration?.topic}
                  </span>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span className="badge badge-cyan">{responseData.response_type}</span>
                <button
                  className="btn-secondary"
                  onClick={() => speechService.speak(responseData.message)}
                  style={{ padding: '0.35rem 0.6rem', fontSize: '0.78rem' }}
                  title="Replay Spoken Answer"
                >
                  <Volume2 size={14} color="var(--accent-cyan)" /> Speak
                </button>
              </div>
            </div>

            {/* Response Message */}
            <div style={{ fontSize: '0.95rem', lineHeight: '1.6', color: 'var(--text-primary)', whiteSpace: 'pre-line' }}>
              {responseData.message}
            </div>

            {/* Quiz view if generated */}
            {responseData.response_type === 'quiz' && responseData.data?.questions && (
              <div style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <h5 style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--accent-purple)' }}>Generated Revision Questions:</h5>
                {responseData.data.questions.map((q, qIdx) => (
                  <div key={qIdx} className="glass-card" style={{ background: 'rgba(10, 16, 26, 0.7)', padding: '1rem' }}>
                    <p style={{ fontWeight: '600', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                      Q{qIdx + 1}. {q.question}
                    </p>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                      {q.options?.map((opt, optIdx) => (
                        <div 
                          key={optIdx} 
                          style={{
                            padding: '0.5rem 0.75rem',
                            borderRadius: '8px',
                            background: optIdx === q.correct_answer ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                            border: optIdx === q.correct_answer ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid var(--border-subtle)',
                            fontSize: '0.82rem',
                            color: optIdx === q.correct_answer ? 'var(--accent-emerald)' : 'var(--text-secondary)'
                          }}
                        >
                          {String.fromCharCode(65 + optIdx)}. {opt} {optIdx === q.correct_answer && ' (Correct)'}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Sidebar Info */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <OmiStatusCard />

        <div className="glass-card">
          <h4 style={{ fontSize: '0.95rem', fontWeight: '700', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Layers size={16} color="var(--accent-cyan)" /> Conversational AI Pipeline
          </h4>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', fontSize: '0.82rem' }}>
            <div style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '10px', borderLeft: '3px solid var(--accent-cyan)' }}>
              <div style={{ fontWeight: '600', color: 'var(--accent-cyan)' }}>1. Real-time Transcript</div>
              <div style={{ color: 'var(--text-muted)' }}>Captures spoken words directly without altering query</div>
            </div>

            <div style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '10px', borderLeft: '3px solid var(--accent-purple)' }}>
              <div style={{ fontWeight: '600', color: 'var(--accent-purple)' }}>2. Orchestrator Reasoning</div>
              <div style={{ color: 'var(--text-muted)' }}>Identifies subject, topic & intent with history context</div>
            </div>

            <div style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '10px', borderLeft: '3px solid var(--accent-emerald)' }}>
              <div style={{ fontWeight: '600', color: 'var(--accent-emerald)' }}>3. AI Provider Completion</div>
              <div style={{ color: 'var(--text-muted)' }}>Executes Lyzr/OpenAI model or structured offline engine</div>
            </div>

            <div style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '10px', borderLeft: '3px solid var(--accent-amber)' }}>
              <div style={{ fontWeight: '600', color: 'var(--accent-amber)' }}>4. Natural Speech Synthesis</div>
              <div style={{ color: 'var(--text-muted)' }}>Clean text-to-speech with stop & voice controls</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
