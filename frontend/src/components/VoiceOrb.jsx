import React, { useState, useEffect } from 'react';
import { Mic, MicOff, Send, Sparkles, Volume2, VolumeX, AlertCircle, Square } from 'lucide-react';
import { speechService } from '../services/speech';

export default function VoiceOrb({ onProcessInput, isProcessing, responseData }) {
  const [orbState, setOrbState] = useState('idle'); // idle, listening, processing, responding
  const [textInput, setTextInput] = useState('');
  const [transcriptText, setTranscriptText] = useState('');
  const [speakerEnabled, setSpeakerEnabled] = useState(true);
  const [speechRate, setSpeechRate] = useState(1.0);
  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    if (isProcessing) {
      setOrbState('processing');
    } else if (responseData) {
      setOrbState('responding');
      if (speakerEnabled && responseData.message) {
        speechService.speak(responseData.message, () => setOrbState('idle'));
      } else {
        const timer = setTimeout(() => setOrbState('idle'), 4000);
        return () => clearTimeout(timer);
      }
    } else {
      setOrbState('idle');
    }
  }, [isProcessing, responseData]);

  const toggleListening = () => {
    if (orbState === 'listening') {
      speechService.stopListening();
      setOrbState('idle');
    } else {
      setErrorMsg(null);
      setTranscriptText('');
      setOrbState('listening');

      speechService.startListening({
        onResult: ({ final, interim }) => {
          if (final) {
            setTranscriptText(final);
            setTextInput(final);
            handleSend(final);
          } else {
            setTranscriptText(interim);
          }
        },
        onError: (err) => {
          setErrorMsg(`Voice recognition note: ${err}`);
          setOrbState('idle');
        },
        onEnd: () => {
          if (orbState === 'listening') {
            setOrbState('idle');
          }
        }
      });
    }
  };

  const handleSend = (textToSend) => {
    const text = textToSend || textInput;
    if (!text || !text.trim()) {
      setErrorMsg("Please speak clearly into the microphone or type a query before sending.");
      return;
    }
    
    setErrorMsg(null);
    onProcessInput(text.trim(), 'web_speech');
    setTextInput('');
    setTranscriptText('');
  };

  const handleStopSpeech = () => {
    speechService.stopSpeaking();
    setOrbState('idle');
  };

  const handleRateChange = (rate) => {
    setSpeechRate(rate);
    speechService.setRate(rate);
  };

  const promptSuggestions = [
    "Explain how Virtual Memory and Page Faults work in Operating Systems.",
    "What are the SOLID principles in Software Engineering?",
    "Compare TCP vs UDP transport layer protocols.",
    "How does Two-Phase Locking ensure concurrency control in DBMS?",
    "What is the difference between processes and threads?",
    "How does Python GIL affect asyncio and multiprocessing?"
  ];

  return (
    <div className="orb-container">
      {/* Dynamic Title */}
      <h2 style={{ fontSize: '1.6rem', fontWeight: '700', color: 'var(--text-primary)', textAlign: 'center', marginBottom: '0.25rem' }}>
        VoiceStudy AI Tutor
      </h2>
      <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', textAlign: 'center', marginBottom: '1.5rem' }}>
        Speak naturally about any subject or select a prompt below
      </p>

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
          {orbState === 'processing' && 'AI Thinking... Classifying Intent & Subject'}
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
          placeholder='Type any question e.g. "Explain SOLID principles in Software Engineering"'
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        />

        <button 
          className="btn-primary" 
          onClick={() => handleSend()}
          disabled={!textInput.trim() || isProcessing}
          style={{ whiteSpace: 'nowrap' }}
        >
          <Send size={18} /> Send
        </button>

        <button
          className="btn-secondary"
          onClick={() => {
            setSpeakerEnabled(!speakerEnabled);
            if (speakerEnabled) speechService.stopSpeaking();
          }}
          title={speakerEnabled ? "Mute Voice Output" : "Enable Voice Output"}
          style={{ padding: '0.75rem' }}
        >
          {speakerEnabled ? <Volume2 size={18} color="var(--accent-emerald)" /> : <VolumeX size={18} color="var(--text-muted)" />}
        </button>
      </div>

      {/* Sample Prompt Chips */}
      <div style={{ width: '100%', maxWidth: '780px' }}>
        <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: '600', marginBottom: '0.75rem', textAlign: 'center' }}>
          Multidisciplinary Sample Questions
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
              💡 "{prompt}"
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
