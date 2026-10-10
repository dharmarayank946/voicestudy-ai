import React, { useState } from 'react';
import { Send, Sparkles, Brain, Cpu, CheckCircle2, MessageSquare, HelpCircle, Layers } from 'lucide-react';
import OmiStatusCard from './OmiStatusCard';

export default function StudyView({ onProcessInput, isProcessing, responseData }) {
  const [inputVal, setInputVal] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputVal.trim()) return;
    onProcessInput(inputVal.trim(), 'text_fallback');
    setInputVal('');
  };

  const sampleQueries = [
    { label: 'Save Note', query: 'Remember that I studied DBMS concurrency control today.' },
    { label: 'Ask Memory', query: 'What did I study about concurrency control?' },
    { label: 'Explain Topic', query: 'Explain what I studied yesterday.' },
    { label: 'Generate Quiz', query: 'Give me five revision questions from my recent study.' },
    { label: 'Compare Concepts', query: 'Compare what I learned about TCP and UDP.' }
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '1.5rem' }}>
      {/* Main Agent Interaction Panel */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* Input Box */}
        <div className="glass-card">
          <h3 style={{ fontSize: '1.1rem', fontWeight: '700', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sparkles size={18} color="var(--accent-cyan)" /> Agent Study Workspace
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
            Type or speak your study statement. Lyzr Orchestrator will route it to Memory, Assistant, or Quiz Agent.
          </p>

          <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.75rem' }}>
            <input
              type="text"
              className="custom-input"
              placeholder="e.g. Remember that I studied DBMS 2PL protocol today..."
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
            />
            <button className="btn-primary" type="submit" disabled={isProcessing || !inputVal.trim()}>
              <Send size={18} /> {isProcessing ? 'Agent Thinking...' : 'Process'}
            </button>
          </form>

          {/* Preset Buttons */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '1rem' }}>
            {sampleQueries.map((item, i) => (
              <button
                key={i}
                className="btn-secondary"
                onClick={() => onProcessInput(item.query, 'text_fallback')}
                style={{ fontSize: '0.78rem', padding: '0.35rem 0.75rem' }}
              >
                <span style={{ color: 'var(--accent-cyan)' }}>[{item.label}]</span> {item.query.slice(0, 32)}...
              </button>
            ))}
          </div>
        </div>

        {/* Agent Response Visualization */}
        {responseData && (
          <div className="glass-card" style={{ borderColor: 'rgba(0, 242, 254, 0.3)' }}>
            {/* Header metadata */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '1rem', borderBottom: '1px solid var(--border-subtle)', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <Cpu size={20} color="var(--accent-cyan)" />
                <div>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                    Agent Executed: <span style={{ color: 'var(--accent-cyan)' }}>{responseData.agent_executed}</span>
                  </h4>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Intent: <strong style={{ color: 'var(--accent-emerald)' }}>{responseData.intent}</strong> • Subject: {responseData.orchestration?.subject}
                  </span>
                </div>
              </div>
              <span className="badge badge-cyan">{responseData.response_type}</span>
            </div>

            {/* Agent Message Content */}
            <div style={{ fontSize: '0.95rem', lineHeight: '1.6', color: 'var(--text-primary)', whiteSpace: 'pre-line' }}>
              {responseData.message}
            </div>

            {/* If Quiz questions present */}
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

      {/* Sidebar Info: Orchestration Flow & Omi Status */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <OmiStatusCard />

        <div className="glass-card">
          <h4 style={{ fontSize: '0.95rem', fontWeight: '700', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Layers size={16} color="var(--accent-cyan)" /> Agent Orchestration Pipeline
          </h4>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', fontSize: '0.82rem' }}>
            <div style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '10px', borderLeft: '3px solid var(--accent-cyan)' }}>
              <div style={{ fontWeight: '600', color: 'var(--accent-cyan)' }}>1. Omi Wearable / Voice Input</div>
              <div style={{ color: 'var(--text-muted)' }}>Raw webhook transcript & overview received</div>
            </div>

            <div style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '10px', borderLeft: '3px solid var(--accent-purple)' }}>
              <div style={{ fontWeight: '600', color: 'var(--accent-purple)' }}>2. FastAPI Webhook Server</div>
              <div style={{ color: 'var(--text-muted)' }}>Defensive payload parsing & background processing</div>
            </div>

            <div style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '10px', borderLeft: '3px solid var(--accent-emerald)' }}>
              <div style={{ fontWeight: '600', color: 'var(--accent-emerald)' }}>3. Qdrant Vector Memory</div>
              <div style={{ color: 'var(--text-muted)' }}>Indexed by Omi UID & semantic vector embeddings</div>
            </div>

            <div style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '10px', borderLeft: '3px solid var(--accent-amber)' }}>
              <div style={{ fontWeight: '600', color: 'var(--accent-amber)' }}>4. Lyzr Agent Reasoning</div>
              <div style={{ color: 'var(--text-muted)' }}>Retrieves memory & answers student questions</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
