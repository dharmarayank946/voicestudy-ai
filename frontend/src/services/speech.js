export class SpeechService {
  constructor() {
    this.recognition = null;
    this.synth = typeof window !== 'undefined' ? window.speechSynthesis || null : null;
    this.isSupported = typeof window !== 'undefined' && ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);
    this.voices = [];
    this.selectedVoice = null;
    this.speechRate = 1.0;

    if (this.isSupported) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = true;
      this.recognition.lang = 'en-US';
    }

    if (this.synth) {
      this.loadVoices();
      if (this.synth.onvoiceschanged !== undefined) {
        this.synth.onvoiceschanged = () => this.loadVoices();
      }
    }
  }

  loadVoices() {
    if (!this.synth) return [];
    this.voices = this.synth.getVoices().filter(v => v.lang.startsWith('en'));
    if (!this.selectedVoice && this.voices.length > 0) {
      this.selectedVoice = this.voices.find(v => v.default || v.name.includes('Natural') || v.name.includes('Google')) || this.voices[0];
    }
    return this.voices;
  }

  getAvailableVoices() {
    if (!this.voices || this.voices.length === 0) {
      this.loadVoices();
    }
    return this.voices;
  }

  setVoice(voiceURI) {
    const found = this.voices.find(v => v.voiceURI === voiceURI || v.name === voiceURI);
    if (found) {
      this.selectedVoice = found;
    }
  }

  setRate(rate) {
    this.speechRate = Math.max(0.5, Math.min(2.0, parseFloat(rate) || 1.0));
  }

  startListening({ onResult, onError, onEnd }) {
    if (!this.recognition) {
      if (onError) onError('Web Speech API recognition is not supported in this browser. Please use text input or Chrome/Edge.');
      return;
    }

    this.recognition.onresult = (event) => {
      let finalTranscript = '';
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }
      if (onResult) {
        onResult({ final: finalTranscript, interim: interimTranscript });
      }
    };

    this.recognition.onerror = (event) => {
      console.warn('Speech recognition error:', event.error);
      if (onError) onError(event.error);
    };

    this.recognition.onend = () => {
      if (onEnd) onEnd();
    };

    try {
      this.recognition.start();
    } catch (e) {
      console.warn('Recognition start exception:', e);
    }
  }

  stopListening() {
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (e) {
        console.warn('Recognition stop exception:', e);
      }
    }
  }

  cleanMarkdownForSpeech(text) {
    if (!text) return '';
    let clean = text
      .replace(/```[\s\S]*?```/g, ' Code snippet omitted for audio playback. ')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/#{1,6}\s?/g, '')
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(/\*([^*]+)\*/g, '$1')
      .replace(/_([^_]+)_/g, '$1')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/^>\s?/gm, '')
      .replace(/^[\-\*\+]\s?/gm, '')
      .replace(/^\d+\.\s?/gm, '')
      .replace(/⚡|🤖|💡|📌|✅|❌|▶️|⏸️/g, '')
      .replace(/\n+/g, '. ');

    return clean.slice(0, 600).trim();
  }

  speak(text, onEnd) {
    if (!this.synth) return;
    this.synth.cancel();

    const cleanText = this.cleanMarkdownForSpeech(text);
    if (!cleanText) return;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = this.speechRate;
    utterance.pitch = 1.0;

    if (this.selectedVoice) {
      utterance.voice = this.selectedVoice;
    }

    if (onEnd) {
      utterance.onend = onEnd;
      utterance.onerror = onEnd;
    }

    this.synth.speak(utterance);
  }

  stopSpeaking() {
    if (this.synth) {
      this.synth.cancel();
    }
  }
}

export const speechService = new SpeechService();
