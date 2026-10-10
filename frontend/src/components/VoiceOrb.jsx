import React, { useState, useEffect } from 'react';
import { Mic, Volume2, Sparkles, Send, AlertCircle, VolumeX, Square, Lightbulb } from 'lucide-react';
import { speechService } from '../services/speech';

export default function VoiceOrb({ onTranscriptSubmit }) {
  const [orbState, setOrbState] = useState('idle'); // 'idle' | 'listening' | 'processing' | 'responding' | 'error'
  const [transcriptText, setTranscriptText] = useState('');
  const [textInput, setTextInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [speechRate, setSpeechRate] = useState(1.0);
  const [speakerEnabled, setSpeakerEnabled] = useState(true);

  const promptSuggestions = [
    "What is photosynthesis and how does it work?",
    "Explain how Virtual Memory and Page Faults work in Operating Systems.",
    "What are the SOLID principles in Software Engineering?",
    "Compare TCP vs UDP transport layer protocols.",
    "How does Two-Phase Locking ensure concurrency control in DBMS?",
    "What is the difference between processes and threads?",
    "How does Python GIL affect asyncio and multiprocessing?"
  ];

  useEffect(() => {
    return () => {
      speechService.stopListening();
      speechService.stopSpeaking();
    };
  }, []);

  const toggleListening = () => {
    if (orbState === 'listening') {
      stopListening();
    } else {
      startListening();
    }
  };

  const startListening = () => {
    setErrorMsg(null);
    setTranscriptText('');
    setOrbState('listening');

    speechService.startListening({
      onResult: ({ final, interim }) => {
        const currentText = final || interim;
        setTranscriptText(currentText);
        if (final) {
          handleSend(final, 'web_speech');
        }
      },
      onError: (err) => {
        console.warn('Voice Orb recognition error:', err);
        setErrorMsg('Microphone input unavailable. You can type your question in the text box below.');
        setOrbState('idle');
      },
      onEnd: () => {
        if (orbState === 'listening') {
          if (!transcriptText) {
            setOrbState('idle');
          }
        }
      }
    });
  };

  const stopListening = () => {
    speechService.stopListening();
    if (transcriptText.trim()) {
      handleSend(transcriptText, 'web_speech');
    } else {
      setOrbState('idle');
    }
  };

  const handleSend = async (queryToSend = textInput, source = 'text_fallback') => {
    const text = queryToSend.trim();
    if (!text || isProcessing) return;

    setIsProcessing(true);
    setErrorMsg(null);
    setOrbState('processing');

    try {
      if (onTranscriptSubmit) {
        const responseData = await onTranscriptSubmit(text, source);
        setOrbState('responding');
        
        const spokenMessage = responseData?.message || responseData?.answer || '';
        if (speakerEnabled && spokenMessage) {
          speechService.speak(spokenMessage, () => {
            setOrbState('idle');
          });
        } else {
          setOrbState('idle');
        }
      } else {
        const res = await fetch('/api/study', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            transcript: text,
            source: source,
            device_id: 'voice_orb'
          })
        });

        const data = await res.json();
        if (res.ok) {
          setOrbState('responding');
          const spokenMessage = data.message || '';
          if (speakerEnabled && spokenMessage) {
            speechService.speak(spokenMessage, () => {
              setOrbState('idle');
            });
          } else {
            setOrbState('idle');
          }
        } else {
          setErrorMsg(data.detail || 'Error processing voice study request.');
          setOrbState('error');
        }
      }
    } catch (err) {
      console.error('Voice Orb submission error:', err);
      setErrorMsg('Failed to process request. Please try typing your question.');
      setOrbState('error');
    } finally {
      setIsProcessing(false);
      setTextInput('');
    }
  };

  const handleRateChange = (newRate) => {
    setSpeechRate(newRate);
    speechService.setRate(newRate);
  };

  const handleStopSpeech = () => {
    speechService.stopSpeaking();
    setOrbState('idle');
  };

  return (
    <div className="voice-orb-container glass-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '2.5rem 1.5rem', margin: '0 auto 2rem', maxWidth: '850px' }}>
      
      {/* Orb Header */}
      <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: '700', marginBottom: '0.25rem', background: 'var(--gradient-cyan-emerald)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          Interactive Voice Orb
        </h2>
        <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
          Tap the Orb or type a question to learn across any subject
        </p>
      </div>

      {/* Voice Orb Interactive Element */}
      <div className="voice-orb-wrapper" onClick={toggleListening}>
        <div className={`orb-ring orb-ring-1`} />
        <div className={`orb-ring orb-ring-2`} />
        <div className={`orb-ring orb-ring-3`} />

        <div className={`voice-orb ${orbState}`}>
          {orbState === 'listening' ? (
            <div className="waveform-bars">
              <div className="waveform-bar" />
              <div className="waveform-bar" />
              <div className="waveform-bar" />
              <div className="waveform-bar" />
              <div className="waveform-bar" />
            </div>
          ) : orbState === 'processing' ? (
            <Sparkles size={42} color="#00F2FE" />
          ) : orbState === 'responding' ? (
            <Volume2 size={42} color="#10B981" />
          ) : (
            <Mic size={42} color="#FFFFFF" />
          )}
        </div>
      </div>

      {/* Real-time Spoken Transcript Display */}
      <div style={{ textAlign: 'center', marginBottom: '1.5rem', minHeight: '36px', maxWidth: '600px' }}>
        <p style={{ 
          fontSize: '0.95rem', 
          fontWeight: '600', 
          color: orbState === 'listening' ? 'var(--accent-cyan)' :
                 orbState === 'processing' ? 'var(--accent-purple)' :
                 orbState === 'responding' ? 'var(--accent-emerald)' :
                 orbState === 'error' ? 'var(--accent-rose)' : 'var(--text-secondary)'
        }}>
          {orbState === 'listening' && (transcriptText ? `Transcript: "${transcriptText}"` : 'Listening... Speak your study question')}
          {orbState === 'processing' && 'AI Thinking... Analyzing Question'}
          {orbState === 'responding' && 'Voice AI Responding... Spoken Answer Active'}
          {orbState === 'error' && (errorMsg || 'Error Encountered')}
          {orbState === 'idle' && 'Ready | Tap Orb to Speak or Type Query Below'}
        </p>
      </div>

      {/* Error Banner */}
      {errorMsg && (
        <div style={{
          background: 'rgba(244, 63, 94, 0.15)',
          border: '1px solid rgba(244, 63, 94, 0.3)',
          borderRadius: '10px',
          padding: '0.6rem 1rem',
          marginBottom: '1rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          fontSize: '0.85rem',
          color: 'var(--accent-rose)'
        }}>
          <AlertCircle size={16} />
          {errorMsg}
        </div>
      )}

      {/* Controls Bar: Voice Speed & Mute / Stop */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
          <span>Speed:</span>
          {[0.8, 1.0, 1.2, 1.5].map((rate) => (
            <button
              key={rate}
              onClick={() => handleRateChange(rate)}
              style={{
                padding: '0.2rem 0.5rem',
                fontSize: '0.78rem',
                borderRadius: '6px',
                border: speechRate === rate ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                background: speechRate === rate ? 'rgba(0, 242, 254, 0.15)' : 'transparent',
                color: speechRate === rate ? 'var(--accent-cyan)' : 'var(--text-muted)',
                cursor: 'pointer'
              }}
            >
              {rate}x
            </button>
          ))}
        </div>

        {orbState === 'responding' && (
          <button
            className="btn-secondary"
            onClick={handleStopSpeech}
            style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem', gap: '0.35rem', color: 'var(--accent-rose)' }}
          >
            <Square size={14} /> Stop Speaking
          </button>
        )}
      </div>

      {/* Text Input Fallback Bar */}
      <div style={{ display: 'flex', gap: '0.75rem', width: '100%', maxWidth: '640px', marginBottom: '2rem' }}>
        <input
          type="text"
          className="custom-input"
          placeholder='Type any question e.g. "What is photosynthesis?"'
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        />

        <button 
          className="btn-primary" 
          onClick={() => handleSend()}
          disabled={!textInput.trim() || isProcessing}
          style={{ whiteSpace: 'nowrap', gap: '0.4rem' }}
        >
          <Send size={18} /> Send
        </button>

        <button
          className="btn-secondary"
          onClick={() => {
            const next = !speakerEnabled;
            setSpeakerEnabled(next);
            if (!next) speechService.stopSpeaking();
          }}
          title={speakerEnabled ? "Mute Voice Output" : "Enable Voice Output"}
          style={{ padding: '0.75rem' }}
        >
          {speakerEnabled ? <Volume2 size={18} color="var(--accent-emerald)" /> : <VolumeX size={18} color="var(--text-muted)" />}
        </button>
      </div>

      {/* Sample Prompt Chips */}
      <div style={{ width: '100%', maxWidth: '780px' }}>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', letterSpacing: '0.03em', fontWeight: '600', marginBottom: '0.75rem', textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem' }}>
          <Lightbulb size={15} color="var(--accent-amber)" /> Try asking a study question:
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', justifyContent: 'center' }}>
          {promptSuggestions.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(prompt)}
              className="glass-card glass-card-interactive"
              style={{
                padding: '0.45rem 0.85rem',
                fontSize: '0.82rem',
                color: 'var(--text-secondary)',
                borderRadius: '20px',
                border: '1px solid var(--border-subtle)',
                background: 'rgba(15, 22, 35, 0.6)'
              }}
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
