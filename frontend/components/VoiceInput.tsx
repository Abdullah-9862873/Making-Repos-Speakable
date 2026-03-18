import React, { useState, useRef, useEffect } from 'react';
import styles from '../styles/VoiceInput.module.css';

interface VoiceInputProps {
  onVoiceInput: (transcript: string) => void;
  disabled?: boolean;
}

const VoiceInput: React.FC<VoiceInputProps> = ({ onVoiceInput, disabled = false }) => {
  const [isListening, setIsListening] = useState<boolean>(false);
  const [transcript, setTranscript] = useState<string>('');
  const [error, setError] = useState<string>('');
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      setError('Voice input is not supported in this browser');
      return;
    }

    recognitionRef.current = new SpeechRecognition();
    recognitionRef.current.continuous = false;
    recognitionRef.current.interimResults = true;
    recognitionRef.current.lang = 'en-US';

    recognitionRef.current.onresult = (event: any) => {
      const current = event.resultIndex;
      const result = event.results[current];
      const transcriptText = result[0].transcript;
      
      setTranscript(transcriptText);
      
      if (result.isFinal) {
        onVoiceInput(transcriptText);
        setTranscript('');
      }
    };

    recognitionRef.current.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      setError(`Error: ${event.error}`);
      setIsListening(false);
    };

    recognitionRef.current.onend = () => {
      setIsListening(false);
    };

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [onVoiceInput]);

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    } else {
      setError('');
      try {
        recognitionRef.current?.start();
        setIsListening(true);
      } catch (err) {
        console.error('Failed to start recognition:', err);
        setError('Failed to start voice recognition');
      }
    }
  };

  return (
    <div className={styles.container}>
      <button
        className={`${styles.voiceButton} ${isListening ? styles.listening : ''}`}
        onClick={toggleListening}
        disabled={disabled || !recognitionRef.current}
        title={isListening ? 'Stop recording' : 'Start voice input'}
      >
        <span className={styles.micIcon}>
          {isListening ? '🔴' : '🎤'}
        </span>
        {isListening ? 'Stop' : 'Voice'}
      </button>
      {error && <div className={styles.error}>{error}</div>}
      {transcript && (
        <div className={styles.transcript}>
          &quot;{transcript}&quot;
        </div>
      )}
    </div>
  );
};

export default VoiceInput;
