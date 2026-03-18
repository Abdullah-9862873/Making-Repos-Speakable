import React, { useEffect, useRef } from 'react';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import styles from '../styles/ResponseDisplay.module.css';

interface CodeBlock {
  language: string;
  code: string;
}

interface ResponseDisplayProps {
  question: string;
  answer: string;
  sources: string[];
  hasCode: boolean;
  codeBlocks: CodeBlock[];
  voiceAudio?: string | null;
  isLoading: boolean;
}

const ResponseDisplay: React.FC<ResponseDisplayProps> = ({
  question,
  answer,
  sources,
  hasCode,
  codeBlocks,
  voiceAudio,
  isLoading,
}) => {
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    if (voiceAudio && audioRef.current) {
      const audioUrl = `data:audio/mp3;base64,${voiceAudio}`;
      audioRef.current.src = audioUrl;
    }
  }, [voiceAudio]);

  const playVoice = () => {
    if (audioRef.current) {
      audioRef.current.play();
    }
  };

  if (isLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>
          <div className={styles.spinner}></div>
          <span>Thinking...</span>
        </div>
      </div>
    );
  }

  if (!question && !answer) {
    return (
      <div className={styles.container}>
        <div className={styles.empty}>
          <h2>Making Repos Speakable</h2>
          <p>Ask a question to get started!</p>
          <p className={styles.hint}>
            Enter a GitHub repo URL, ingest it, and ask anything about the codebase.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.questionSection}>
        <div className={styles.label}>Question</div>
        <div className={styles.question}>{question}</div>
      </div>
      <div className={styles.answerSection}>
        <div className={styles.label}>Answer</div>
        {voiceAudio && (
          <button className={styles.voiceButton} onClick={playVoice}>
            <span className={styles.voiceIcon}>🔊</span>
            Play Voice
          </button>
        )}
        <audio ref={audioRef} className={styles.hiddenAudio} controls />
        <div className={styles.answer}>
          {answer.split('```').map((part, index) => {
            if (index % 2 === 0) {
              return (
                <p key={index} className={styles.answerText}>
                  {part}
                </p>
              );
            }
            return null;
          })}
        </div>
        {hasCode && codeBlocks.length > 0 && (
          <div className={styles.codeSection}>
            <div className={styles.label}>Code Examples</div>
            {codeBlocks.map((block, index) => (
              <div key={index} className={styles.codeBlock}>
                <SyntaxHighlighter
                  language={block.language || 'text'}
                  style={atomDark}
                  showLineNumbers
                >
                  {block.code}
                </SyntaxHighlighter>
              </div>
            ))}
          </div>
        )}
        {sources.length > 0 && (
          <div className={styles.sourcesSection}>
            <div className={styles.label}>Sources</div>
            <div className={styles.sources}>
              {sources.map((source, index) => (
                <span key={index} className={styles.source}>
                  {source}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResponseDisplay;
