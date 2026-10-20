import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Square, 
  RefreshCw, 
  AlertCircle, 
  AlertTriangle,
  BookOpen, 
  Volume2, 
  VolumeX, 
  Cpu, 
  Layers, 
  Sparkles, 
  CheckCircle2,
  Monitor,
  MonitorOff
} from 'lucide-react';
import { speechService } from '../services/speech';
import { processStudyRequest } from '../services/api';
import OmiStatusCard from './OmiStatusCard';

export default function StudyView() {
  const [inputVal, setInputVal] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  // States: 'idle' | 'loading' | 'speaking' | 'stopped' | 'error'
  const [studyState, setStudyState] = useState('idle');
  const [responseData, setResponseData] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [lastFailedQuery, setLastFailedQuery] = useState('');
  const [lastExecutedQuery, setLastExecutedQuery] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('All');
  const [speakerEnabled, setSpeakerEnabled] = useState(true);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [isSharing, setIsSharing] = useState(false);
  
  const abortControllerRef = useRef(null);
  const mediaStreamRef = useRef(null);

  const subjects = ['All', 'DBMS', 'Networks', 'Operating Systems', 'Python', 'Science'];

  const sampleQueries = [
    { label: 'Science', query: 'What is photosynthesis?' },
    { label: 'Physics', query: "Explain Newton's first law of motion and inertia." },
    { label: 'Networks', query: 'Compare TCP vs UDP transport layer protocols.' },
    { label: 'DBMS', query: 'How does Strict Two-Phase Locking prevent cascading aborts?' },
    { label: 'Python', query: 'Explain Python functions, variable scope, and return values.' },
    { label: 'Software Eng', query: 'What are the SOLID design principles in software engineering?' },
    { label: 'Meeting Intel', query: 'Summarize our project meeting and extract all action items, owners, and deadlines.' },
  ];

  // Clean up on component unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      speechService.stopSpeaking();
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach(t => { try { t.stop(); } catch (e) {} });
        mediaStreamRef.current = null;
      }
    };
  }, []);

  const handleStartSharing = async () => {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
        alert("Screen / display sharing is not supported in this browser. Please use Chrome, Edge, or Firefox.");
        return;
      }
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: true
      });
      mediaStreamRef.current = stream;
      setIsSharing(true);

      const tracks = stream.getTracks();
      tracks.forEach(track => {
        track.onended = () => {
          handleStopSharing();
        };
      });
    } catch (err) {
      if (err.name !== 'NotAllowedError') {
        console.error('Screen sharing error:', err);
      }
    }
  };

  const handleStopSharing = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => {
        try { track.stop(); } catch (e) {}
      });
      mediaStreamRef.current = null;
    }
    setIsSharing(false);
  };

  const handleStartExplaining = async (queryText = inputVal) => {
    const textToSend = (queryText || inputVal).trim();
    if (!textToSend || isProcessing) return;

    // Abort any ongoing request before starting a new one
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    speechService.stopSpeaking();
    setIsSpeaking(false);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    setIsProcessing(true);
    setStudyState('loading');
    setErrorMessage(null);
    setResponseData(null);
    setLastExecutedQuery(textToSend);

    const newHistory = [...conversationHistory, { role: 'user', content: textToSend }];

    try {
      const subjectParam = selectedSubject !== 'All' ? selectedSubject : null;
      const data = await processStudyRequest(textToSend, 'text_fallback', subjectParam, null, controller.signal);

      // Handle backend returning structured error (e.g. Lyzr API error)
      if (data.response_type === 'error' || data.intent === 'ERROR') {
        const rawErr = data.message || data.data?.error || 'Lyzr AI Agent encountered an issue.';
        setLastFailedQuery(textToSend);
        setErrorMessage(rawErr);
        setResponseData(data);
        setStudyState('error');
        // Do NOT play audio of error messages
      } else {
        setResponseData(data);
        setLastFailedQuery('');
        const assistantMessage = data.message || '';
        setConversationHistory([
          ...newHistory,
          { role: 'assistant', content: assistantMessage }
        ]);

        if (speakerEnabled && assistantMessage) {
          setStudyState('speaking');
          setIsSpeaking(true);
          speechService.speak(
            assistantMessage,
            () => {
              setIsSpeaking(false);
              setStudyState('idle');
            },
            () => {
              setIsSpeaking(true);
              setStudyState('speaking');
            }
          );
        } else {
          setStudyState('idle');
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        setStudyState('stopped');
      } else {
        console.error('Study API call failed:', err);
        setLastFailedQuery(textToSend);
        setErrorMessage(err.message || 'Network connection issue. Please check backend connection.');
        setStudyState('error');
        setResponseData({
          agent_executed: 'Network Handler',
          intent: 'ERROR',
          message: err.message || 'Network connection issue. Please check backend connection.',
          response_type: 'error',
          orchestration: { subject: selectedSubject, topic: 'Network Communication' }
        });
      }
    } finally {
      setIsProcessing(false);
      abortControllerRef.current = null;
    }
  };

  const handleStopExplaining = () => {
    // 1. Abort in-flight network request if active
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    // 2. Stop speech synthesis if speaking
    speechService.stopSpeaking();
    setIsSpeaking(false);
    setIsProcessing(false);
    setStudyState('stopped');
  };

  const handleRetry = () => {
    const queryToRetry = lastFailedQuery || lastExecutedQuery || inputVal;
    if (queryToRetry) {
      handleStartExplaining(queryToRetry);
    }
  };

  const handleClearContext = () => {
    handleStopExplaining();
    setConversationHistory([]);
    setResponseData(null);
    setErrorMessage(null);
    setLastFailedQuery('');
    setStudyState('idle');
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
              {studyState === 'loading' && (
                <span className="badge badge-cyan" style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.72rem' }}>
                  <Sparkles size={12} className="spin" /> Generating...
                </span>
              )}
              {studyState === 'speaking' && (
                <span className="badge badge-emerald" style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.72rem' }}>
                  <Volume2 size={12} /> Speaking
                </span>
              )}
              {studyState === 'stopped' && (
                <span className="badge" style={{ background: 'rgba(255,255,255,0.08)', color: 'var(--text-muted)', fontSize: '0.72rem' }}>
                  Stopped
                </span>
              )}
              {isSharing && (
                <span className="badge badge-rose" style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.72rem', animation: 'pulse 2s infinite' }}>
                  <Monitor size={12} /> Sharing Screen
                </span>
              )}
            </div>
            
            {conversationHistory.length > 0 && (
              <button
                className="btn-secondary"
                onClick={handleClearContext}
                style={{ fontSize: '0.78rem', padding: '0.3rem 0.65rem', gap: '0.35rem' }}
                title="Start a new conversation context"
              >
                <RefreshCw size={13} /> Clear Context ({Math.floor(conversationHistory.length / 2)} turns)
              </button>
            )}
          </div>

          <form onSubmit={(e) => { e.preventDefault(); handleStartExplaining(); }} style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <input
              type="text"
              className="custom-input"
              placeholder='Type an educational question e.g. "What is photosynthesis?" or "Explain Newton&#39;s first law"'
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              disabled={isProcessing}
              style={{ flex: '1 1 280px' }}
            />

            {/* Start Explaining Button */}
            <button
              type="submit"
              className="btn-primary"
              disabled={!inputVal.trim() || isProcessing}
              style={{ whiteSpace: 'nowrap', gap: '0.4rem', padding: '0.7rem 1.1rem' }}
              title="Start an AI explanation session"
            >
              {isProcessing ? (
                <>
                  <Sparkles size={17} className="spin" /> Explaining...
                </>
              ) : (
                <>
                  <Play size={16} fill="currentColor" /> Start Explaining
                </>
              )}
            </button>

            {/* Stop Explaining Button — Active during loading or speaking */}
            {(isProcessing || isSpeaking || studyState === 'loading' || studyState === 'speaking') && (
              <button
                type="button"
                className="btn-secondary"
                onClick={handleStopExplaining}
                style={{
                  whiteSpace: 'nowrap',
                  gap: '0.4rem',
                  color: 'var(--accent-rose)',
                  borderColor: 'rgba(244, 63, 94, 0.4)',
                  background: 'rgba(244, 63, 94, 0.1)',
                  padding: '0.7rem 1rem',
                  cursor: 'pointer'
                }}
                title="Stop current explanation and cancel speech"
              >
                <Square size={15} fill="currentColor" /> Stop Explaining
              </button>
            )}

            {/* Stop Sharing / Share Screen Control */}
            {isSharing ? (
              <button
                type="button"
                id="stop-sharing-btn"
                className="btn-secondary"
                onClick={handleStopSharing}
                style={{
                  whiteSpace: 'nowrap',
                  gap: '0.4rem',
                  color: 'var(--accent-rose)',
                  borderColor: 'rgba(244, 63, 94, 0.4)',
                  background: 'rgba(244, 63, 94, 0.12)',
                  padding: '0.7rem 1rem',
                  cursor: 'pointer'
                }}
                title="Stop active screen sharing and release media stream"
              >
                <MonitorOff size={16} /> Stop Sharing
              </button>
            ) : (
              <button
                type="button"
                id="start-sharing-btn"
                className="btn-secondary"
                onClick={handleStartSharing}
                style={{
                  whiteSpace: 'nowrap',
                  gap: '0.4rem',
                  padding: '0.7rem 0.95rem',
                  cursor: 'pointer'
                }}
                title="Share screen or study notes with VoiceStudy AI"
              >
                <Monitor size={16} /> Share Screen
              </button>
            )}

            {/* Voice Mute / Unmute Control */}
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

          {/* Subject Filter Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.85rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Focus Subject:</span>
            {subjects.map((sub) => (
              <button
                key={sub}
                type="button"
                onClick={() => setSelectedSubject(sub)}
                style={{
                  padding: '0.25rem 0.65rem',
                  borderRadius: '16px',
                  border: selectedSubject === sub ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                  background: selectedSubject === sub ? 'rgba(0, 242, 254, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                  color: selectedSubject === sub ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                  fontWeight: '600',
                  fontSize: '0.74rem',
                  cursor: 'pointer'
                }}
              >
                {sub}
              </button>
            ))}
          </div>

          {/* Subject Preset Chips */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.75rem' }}>
            {sampleQueries.map((item, i) => (
              <button
                key={i}
                className="btn-secondary"
                onClick={() => {
                  setInputVal(item.query);
                  handleStartExplaining(item.query);
                }}
                style={{ fontSize: '0.78rem', padding: '0.35rem 0.75rem' }}
              >
                <span style={{ color: 'var(--accent-cyan)', fontWeight: '600' }}>[{item.label}]</span> {item.query.length > 32 ? item.query.slice(0, 32) + '...' : item.query}
              </button>
            ))}
          </div>
        </div>

        {/* Loading Feedback Card */}
        {studyState === 'loading' && (
          <div className="glass-card" style={{ borderColor: 'rgba(0, 242, 254, 0.3)', padding: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{ padding: '0.75rem', borderRadius: '12px', background: 'rgba(0, 242, 254, 0.1)' }}>
                <Sparkles size={24} color="var(--accent-cyan)" className="spin" />
              </div>
              <div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                  AI Study Assistant is generating an explanation...
                </h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Question: "{lastExecutedQuery}"
                </p>
              </div>
            </div>
            <button
              className="btn-secondary"
              onClick={handleStopExplaining}
              style={{ color: 'var(--accent-rose)', borderColor: 'rgba(244, 63, 94, 0.3)', gap: '0.35rem', fontSize: '0.82rem' }}
            >
              <Square size={14} fill="currentColor" /> Stop
            </button>
          </div>
        )}

        {/* Stopped Notification Banner */}
        {studyState === 'stopped' && !isProcessing && (
          <div style={{
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '12px',
            padding: '0.85rem 1.25rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.85rem',
            color: 'var(--text-muted)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Square size={15} color="var(--text-muted)" />
              <span>Explanation session was stopped.</span>
            </div>
            {lastExecutedQuery && (
              <button
                className="btn-secondary"
                onClick={() => handleStartExplaining(lastExecutedQuery)}
                style={{ fontSize: '0.78rem', padding: '0.3rem 0.65rem', gap: '0.35rem' }}
              >
                <Play size={13} fill="currentColor" /> Resume
              </button>
            )}
          </div>
        )}

        {/* Friendly Error State Card with Functional Retry Button */}
        {studyState === 'error' && (
          <div className="glass-card" style={{ borderColor: 'rgba(244, 63, 94, 0.4)', background: 'rgba(244, 63, 94, 0.05)', padding: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', flex: '1 1 260px' }}>
                <div style={{ padding: '0.5rem', borderRadius: '8px', background: 'rgba(244, 63, 94, 0.15)', marginTop: '0.1rem' }}>
                  <AlertCircle size={22} color="var(--accent-rose)" />
                </div>
                <div>
                  <h4 style={{ fontSize: '0.98rem', fontWeight: '700', color: 'var(--accent-rose)', marginBottom: '0.35rem' }}>
                    AI Service Notice
                  </h4>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5', marginBottom: '0.5rem' }}>
                    {errorMessage || 'The AI agent could not complete this request at this moment.'}
                  </p>
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    Your question "{lastFailedQuery || lastExecutedQuery}" has been preserved. You can retry with the button below.
                  </p>
                </div>
              </div>

              {/* Functional Retry Button */}
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <button
                  type="button"
                  className="btn-primary"
                  onClick={handleRetry}
                  disabled={isProcessing}
                  style={{
                    gap: '0.4rem',
                    fontSize: '0.85rem',
                    padding: '0.55rem 1rem',
                    background: 'var(--gradient-cyan-emerald)'
                  }}
                  title="Retry the failed request"
                >
                  <RefreshCw size={15} /> Retry
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Agent Response Card */}
        {responseData && responseData.response_type !== 'error' && (
          <div className="glass-card" style={{ borderColor: 'rgba(0, 242, 254, 0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '0.85rem', borderBottom: '1px solid var(--border-subtle)', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
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
                
                {isSpeaking ? (
                  <button
                    className="btn-secondary"
                    onClick={handleStopExplaining}
                    style={{ padding: '0.35rem 0.65rem', fontSize: '0.78rem', color: 'var(--accent-rose)', gap: '0.3rem' }}
                    title="Stop Spoken Answer"
                  >
                    <Square size={13} fill="currentColor" /> Stop Speaking
                  </button>
                ) : (
                  <button
                    className="btn-secondary"
                    onClick={() => {
                      setIsSpeaking(true);
                      setStudyState('speaking');
                      speechService.speak(
                        responseData.message,
                        () => {
                          setIsSpeaking(false);
                          setStudyState('idle');
                        },
                        () => {
                          setIsSpeaking(true);
                          setStudyState('speaking');
                        }
                      );
                    }}
                    style={{ padding: '0.35rem 0.6rem', fontSize: '0.78rem', gap: '0.3rem' }}
                    title="Play Spoken Answer"
                  >
                    <Volume2 size={14} color="var(--accent-cyan)" /> Speak
                  </button>
                )}
              </div>
            </div>

            {/* Response Message */}
            <div style={{ fontSize: '0.95rem', color: 'var(--text-primary)' }}>
              {renderFormattedText(responseData.message)}
            </div>

            {/* Display Retrieved Study Memories if present */}
            {responseData.retrieved_memories && responseData.retrieved_memories.length > 0 && (
              <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid var(--border-subtle)' }}>
                <h5 style={{ fontSize: '0.85rem', fontWeight: '700', color: 'var(--accent-cyan)', marginBottom: '0.6rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <BookOpen size={14} /> Retrieved Notebook Memories ({responseData.retrieved_memories.length})
                </h5>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {responseData.retrieved_memories.map((m, idx) => (
                    <div key={idx} style={{ padding: '0.6rem 0.85rem', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '8px', borderLeft: '3px solid var(--accent-emerald)', fontSize: '0.82rem' }}>
                      <span style={{ fontWeight: '600', color: 'var(--accent-emerald)' }}>[{m.subject || 'General'} - {m.topic || 'Note'}]</span>: {m.text}
                    </div>
                  ))}
                </div>
              </div>
            )}

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
              <div style={{ fontWeight: '600', color: 'var(--accent-cyan)' }}>1. Start Explaining</div>
              <div style={{ color: 'var(--text-muted)' }}>Captures student educational question with full context</div>
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
              <div style={{ fontWeight: '600', color: 'var(--accent-amber)' }}>4. Voice & Control Management</div>
              <div style={{ color: 'var(--text-muted)' }}>Clean stop, retry after errors, and speech synthesis</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
