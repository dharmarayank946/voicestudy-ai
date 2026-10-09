export class SpeechService {
  constructor() {
    this.recognition = null;
    this.synth = window.speechSynthesis || null;
    this.isSupported = 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window;
    
    if (this.isSupported) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = true;
      this.recognition.lang = 'en-US';
    }
  }

  startListening({ onResult, onError, onEnd }) {
    if (!this.recognition) {
      onError('Web Speech API is not supported in this browser. Please use text input or Chrome/Edge.');
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
      onResult({ final: finalTranscript, interim: interimTranscript });
    };

    this.recognition.onerror = (event) => {
      console.warn('Speech recognition error:', event.error);
      onError(event.error);
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

  speak(text, onEnd) {
    if (!this.synth) return;
    this.synth.cancel(); // Stop any ongoing speech
    
    // Clean markdown text for TTS playback
    const cleanText = text.replace(/[*#_`~]/g, '').slice(0, 300);
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    
    if (onEnd) {
      utterance.onend = onEnd;
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
