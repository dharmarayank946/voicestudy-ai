import React, { useState, useEffect } from 'react';
import { Mic, MicOff, Send, Sparkles, Volume2, VolumeX, AlertCircle } from 'lucide-react';
import { speechService } from '../services/speech';

export default function VoiceOrb({ onProcessInput, isProcessing, responseData }) {
  const [orbState, setOrbState] = useState('idle'); // idle, listening, processing, responding
  const [textInput, setTextInput] = useState('');
  const [transcriptText, setTranscriptText] = useState('');
  const [speakerEnabled, setSpeakerEnabled] = useState(true);
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
          setErrorMsg(`Voice recognition error: ${err}`);
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
    if (!text || !text.trim()) return;
    
    setErrorMsg(null);
    onProcessInput(text.trim(), 'web_speech');
    setTextInput('');
    setTranscriptText('');
  };

  const promptSuggestions = [
    "Remember that I studied DBMS concurrency control today.",
    "What did I study about concurrency control?",
    "Explain what I studied yesterday.",
    "Give me five revision questions from my recent study.",
    "What topics have I studied recently?",
    "Compare what I learned about TCP and UDP."
  ];

  return (
    <div className="orb-container">
      {/* Dynamic Title */}
      <h2 style={{ fontSize: '1.6rem', fontWeight: '700', color: 'var(--text-primary)', textAlign: 'center', marginBottom: '0.25rem' }}>
        How can I help you study?
      </h2>
      <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', textAlign: 'center', marginBottom: '1.5rem' }}>
        Speak naturally or select a prompt below
      </p>

      {/* Voice Orb Area */}
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

      {/* State Text Label */}
      <div style={{ textAlign: 'center', marginBottom: '1.5rem', minHeight: '36px' }}>
        <p style={{ 
          fontSize: '0.95rem', 
          fontWeight: '600', 
          color: orbState === 'listening' ? 'var(--accent-cyan)' :
                 orbState === 'processing' ? 'var(--accent-purple)' :
                 orbState === 'remembering' ? 'var(--accent-emerald)' :
                 orbState === 'thinking' ? 'var(--accent-amber)' :
                 orbState === 'responding' ? 'var(--accent-emerald)' :
                 orbState === 'error' ? 'var(--accent-rose)' : 'var(--text-secondary)'
        }}>
          {orbState === 'listening' && (transcriptText || 'Listening... Speak your study note or question')}
          {orbState === 'processing' && 'Processing... Classifying Intent'}
          {orbState === 'remembering' && 'Remembering... Storing to Qdrant Persistent Vector Memory'}
          {orbState === 'thinking' && 'Thinking... Lyzr Agents Reasoning over Retrieved Memory'}
          {orbState === 'responding' && 'Responding... VoiceStudy AI Output Ready'}
          {orbState === 'error' && (errorMsg || 'Error Encountered')}
          {orbState === 'idle' && 'Ready | Tap Orb to Speak or send via Omi Webhook'}
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

      {/* Text Input Fallback Bar */}
      <div style={{ display: 'flex', gap: '0.75rem', width: '100%', maxWidth: '640px', marginBottom: '2rem' }}>
        <input
          type="text"
          className="custom-input"
          placeholder='Or type e.g., "Remember that I studied DBMS concurrency control today"'
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
          title={speakerEnabled ? "Mute Voice Response" : "Enable Voice Response"}
          style={{ padding: '0.75rem' }}
        >
          {speakerEnabled ? <Volume2 size={18} color="var(--accent-emerald)" /> : <VolumeX size={18} color="var(--text-muted)" />}
        </button>
      </div>

      {/* Sample Prompt Chips */}
      <div style={{ width: '100%', maxWidth: '780px' }}>
        <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: '600', marginBottom: '0.75rem', textAlign: 'center' }}>
          Try these voice examples
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
              💬 "{prompt}"
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
