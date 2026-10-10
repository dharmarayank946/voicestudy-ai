import React, { useState } from 'react';
import { Mic, Send, Volume2, VolumeX, Cpu, Layers, BookOpen, Sparkles, CheckCircle, RefreshCw } from 'lucide-react';
import { speechService } from '../services/speech';
import OmiStatusCard from './OmiStatusCard';

export default function StudyView() {
  const [inputVal, setInputVal] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [responseData, setResponseData] = useState(null);
  const [speakerEnabled, setSpeakerEnabled] = useState(true);
  const [conversationHistory, setConversationHistory] = useState([]);

  const sampleQueries = [
    { label: 'Science', query: 'What is photosynthesis and how does it work?' },
    { label: 'Operating Systems', query: 'Explain how Virtual Memory and Page Faults work in OS.' },
    { label: 'Software Eng', query: 'What are the SOLID design principles in software engineering?' },
    { label: 'DBMS', query: 'How does Strict Two-Phase Locking prevent cascading aborts?' },
    { label: 'Networks', query: 'Compare TCP vs UDP transport layer protocols.' },
    { label: 'Math', query: 'Explain linear algebra matrix vector multiplication.' },
  ];

  const handleSend = async (queryText = inputVal) => {
    const textToSend = queryText || inputVal;
    if (!textToSend.trim()) return;

    setIsProcessing(true);
    setResponseData(null);

    const newHistory = [...conversationHistory, { role: 'user', content: textToSend }];

    try {
      const res = await fetch('/api/study', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transcript: textToSend,
          source: 'text_fallback',
          device_id: 'browser_input',
          history: newHistory
        })
      });

      const data = await res.json();
      if (res.ok) {
        setResponseData(data);
        const assistantMessage = data.message || '';
        setConversationHistory([
          ...newHistory,
          { role: 'assistant', content: assistantMessage }
        ]);

        if (speakerEnabled && assistantMessage) {
          speechService.speak(assistantMessage);
        }
      } else {
        setResponseData({
          agent_executed: 'Error Handler',
          intent: 'ERROR',
          message: data.detail || 'Failed to process question. Please try again.',
          response_type: 'error',
          orchestration: { subject: 'General', topic: 'Error' }
        });
      }
    } catch (err) {
      console.error('Study API call failed:', err);
      setResponseData({
        agent_executed: 'Network Handler',
        intent: 'ERROR',
        message: 'Network connection issue. Please check backend connection.',
        response_type: 'error',
        orchestration: { subject: 'General', topic: 'Network' }
      });
    } finally {
      setIsProcessing(false);
      setInputVal('');
    }
  };

  const handleClearContext = () => {
    setConversationHistory([]);
    setResponseData(null);
    speechService.stopSpeaking();
  };

  // Helper to render formatted markdown nicely
  const renderFormattedText = (text) => {
    if (!text) return null;
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      const trimmed = line.trim();
      if (!trimmed) return <div key={idx} style={{ height: '0.5rem' }} />;
      
      if (trimmed.startsWith('### ')) {
        return (
          <h4 key={idx} style={{ fontSize: '1.05rem', fontWeight: '700', color: 'var(--accent-cyan)', marginTop: '1rem', marginBottom: '0.4rem' }}>
            {trimmed.replace('### ', '')}
          </h4>
        );
      }
      
      if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        const content = trimmed.replace(/^[\-\*]\s+/, '');
        return (
          <div key={idx} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.4rem', paddingLeft: '0.5rem' }}>
            <span style={{ color: 'var(--accent-emerald)', fontWeight: 'bold' }}>•</span>
            <div>{renderBoldText(content)}</div>
          </div>
        );
      }

      if (/^\d+\.\s+/.test(trimmed)) {
        const num = trimmed.match(/^(\d+\.)/)[1];
        const content = trimmed.replace(/^\d+\.\s+/, '');
        return (
          <div key={idx} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.4rem', paddingLeft: '0.5rem' }}>
            <span style={{ color: 'var(--accent-cyan)', fontWeight: '600' }}>{num}</span>
            <div>{renderBoldText(content)}</div>
          </div>
        );
      }

      return (
        <p key={idx} style={{ marginBottom: '0.6rem', lineHeight: '1.6' }}>
          {renderBoldText(trimmed)}
        </p>
      );
    });
  };

  const renderBoldText = (str) => {
    const parts = str.split(/(\?\?[^\*]+\?\?|\*\*[^\*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} style={{ color: 'var(--text-primary)', fontWeight: '700' }}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'grid', gridTemplateColumns: '1fr 300px', gap: '1.5rem' }}>
      
      {/* Main Workspace */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        
        {/* Input Card */}
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <BookOpen size={20} color="var(--accent-cyan)" />
              <h3 style={{ fontSize: '1.1rem', fontWeight: '700' }}>Study Workspace</h3>
            </div>
            
            {conversationHistory.length > 0 && (
              <button
                className="btn-secondary"
                onClick={handleClearContext}
                style={{ fontSize: '0.78rem', padding: '0.3rem 0.65rem', gap: '0.35rem' }}
                title="Start a new conversation context"
              >
                <RefreshCw size={13} /> Clear Context ({conversationHistory.length / 2 | 0} turns)
              </button>
            )}
          </div>

          <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} style={{ display: 'flex', gap: '0.75rem' }}>
            <input
              type="text"
              className="custom-input"
              placeholder='Ask any question e.g. "What is photosynthesis?" or "Explain Virtual Memory"'
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              disabled={isProcessing}
            />

            <button
              type="submit"
              className="btn-primary"
              disabled={!inputVal.trim() || isProcessing}
              style={{ whiteSpace: 'nowrap', gap: '0.4rem' }}
            >
              {isProcessing ? <Sparkles size={18} className="spin" /> : <Send size={18} />} Send
            </button>

            <button
              type="button"
              className="btn-secondary"
              onClick={() => {
                const nextState = !speakerEnabled;
                setSpeakerEnabled(nextState);
                if (!nextState) speechService.stopSpeaking();
              }}
              title={speakerEnabled ? "Mute Spoken Answer" : "Enable Spoken Answer"}
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
                <span style={{ color: 'var(--accent-cyan)', fontWeight: '600' }}>[{item.label}]</span> {item.query.slice(0, 30)}...
              </button>
            ))}
          </div>
        </div>

        {/* Agent Response Card */}
        {responseData && (
          <div className="glass-card" style={{ borderColor: 'rgba(0, 242, 254, 0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '0.85rem', borderBottom: '1px solid var(--border-subtle)', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <Cpu size={20} color="var(--accent-cyan)" />
                <div>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                    Agent Executed: <span style={{ color: 'var(--accent-cyan)' }}>{responseData.agent_executed}</span>
                  </h4>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Intent: <strong style={{ color: 'var(--accent-emerald)' }}>{responseData.intent}</strong> • Subject: <strong>{responseData.orchestration?.subject}</strong> • Topic: {responseData.orchestration?.topic}
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
            <div style={{ fontSize: '0.95rem', color: 'var(--text-primary)' }}>
              {renderFormattedText(responseData.message)}
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
              <div style={{ fontWeight: '600', color: 'var(--accent-emerald)' }}>3. AI Study Assistant</div>
              <div style={{ color: 'var(--text-muted)' }}>Executes intelligent study assistant agent</div>
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
