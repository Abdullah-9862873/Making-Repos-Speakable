// =============================================================================
// AI Multimodal Tutor - Main Page
// =============================================================================
// Phase: 5 - Frontend Development (UPDATED)
// Purpose: Main application page with GitHub repo validation
// Version: 5.1.0
// =============================================================================

import { useState, useEffect } from 'react';
import Head from 'next/head';
import QuestionInput from '../components/QuestionInput';
import ResponseDisplay from '../components/ResponseDisplay';
import VoiceInput from '../components/VoiceInput';
import FileUpload from '../components/FileUpload';
import apiService, { AskResponse, HealthResponse } from '@/lib/api';
import styles from '../styles/Home.module.css';

type Mode = 'repo' | 'single-file';

interface ValidateResponse {
  valid: boolean;
  is_public: boolean;
  repo: string;
  message: string;
  owner?: string;
  name?: string;
  description?: string;
  stars?: number;
}

export default function Home() {
  // State
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string>('');
  const [ingestStatus, setIngestStatus] = useState<any>(null);
  
  // New state for GitHub repo validation
  const [repoUrl, setRepoUrl] = useState<string>('');
  const [validateStatus, setValidateStatus] = useState<ValidateResponse | null>(null);
  const [isValidating, setIsValidating] = useState<boolean>(false);
  const [mode, setMode] = useState<Mode>('repo');
  const [ingestedRepo, setIngestedRepo] = useState<string>('');
  
  // Single file state
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isFileUploaded, setIsFileUploaded] = useState<boolean>(false);

  // Check API connection on mount
  useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = async () => {
    try {
      const healthData = await apiService.getHealth();
      setHealth(healthData);
      setIsConnected(true);
      
      // Check ingest status
      try {
        const status = await apiService.getIngestStatus();
        setIngestStatus(status);
      } catch (err) {
        console.log('No content ingested yet');
      }
    } catch (err) {
      setIsConnected(false);
      setError('Cannot connect to backend. Make sure the server is running.');
    }
  };

  const handleValidateRepo = async () => {
    if (!repoUrl.trim()) {
      setError('Please enter a GitHub repository URL');
      return;
    }

    setIsValidating(true);
    setError('');
    setValidateStatus(null);

    try {
      const result = await apiService.validateRepo(repoUrl);
      setValidateStatus(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to validate repository');
    } finally {
      setIsValidating(false);
    }
  };

  const handleIngest = async () => {
    if (!validateStatus?.is_public) {
      setError('Please validate a public repository first');
      return;
    }

    setIsLoading(true);
    setError('');
    
    try {
      const result = await apiService.ingestCourse(repoUrl, ['.md', '.py', '.js', '.ts', '.txt', '.java', '.cpp', '.go', '.rs']);
      alert(`Ingestion complete: ${result.message}`);
      // Refresh status
      const status = await apiService.getIngestStatus();
      setIngestStatus(status);
      setIngestedRepo(repoUrl);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to ingest course');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAskQuestion = async (question: string) => {
    if (mode === 'repo' && !ingestStatus?.total_vectors) {
      setError('Please ingest a GitHub repository first');
      return;
    }
    
    if (mode === 'single-file' && !isFileUploaded) {
      setError('Please upload a file first');
      return;
    }

    setIsLoading(true);
    setError('');
    
    try {
      let result;
      
      if (mode === 'single-file') {
        // Ask about single file
        result = await apiService.askSingleFile(question);
      } else {
        // Ask about repo
        result = await apiService.askQuestion({
          question,
          top_k: 5,
          threshold: 0.7,
          prompt_type: 'default',
        });
      }
      
      setResponse(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to get answer');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVoiceInput = (transcript: string) => {
    handleAskQuestion(transcript);
  };

  const handleFileSelect = async (file: File) => {
    console.log('File selected:', file.name);
    setUploadedFile(file);
    setIsLoading(true);
    setError('');
    
    try {
      // Upload and ingest the file
      const result = await apiService.ingestSingleFile(file);
      console.log('File ingested:', result);
      setIsFileUploaded(true);
      alert(`File "${file.name}" uploaded successfully! Now you can ask questions about it.`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload file');
    } finally {
      setIsLoading(false);
    }
  };

  const switchMode = (newMode: Mode) => {
    setMode(newMode);
    setResponse(null);
    setError('');
    if (newMode === 'single-file') {
      setUploadedFile(null);
      setIsFileUploaded(false);
    }
  };

  return (
    <div className={styles.container}>
      <Head>
        <title>AI Multimodal Tutor</title>
        <meta name="description" content="Ask questions about your GitHub course" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.title}>AI Multimodal Tutor</h1>
          <p className={styles.subtitle}>
            Your personal programming tutor powered by AI
          </p>
        </div>
        
        {/* Status Badge */}
        <div className={styles.status}>
          <span className={`${styles.statusDot} ${isConnected ? styles.connected : styles.disconnected}`} />
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </header>

      {/* Main Content */}
      <main className={styles.main}>
        {/* Error Message */}
        {error && (
          <div className={styles.error}>
            {error}
            <button onClick={() => setError('')} className={styles.errorClose}>
              ✕
            </button>
          </div>
        )}

        {/* Mode Switcher */}
        <div className={styles.modeSwitcher}>
          <button 
            className={`${styles.modeButton} ${mode === 'repo' ? styles.modeActive : ''}`}
            onClick={() => switchMode('repo')}
          >
            🔗 GitHub Repo
          </button>
          <button 
            className={`${styles.modeButton} ${mode === 'single-file' ? styles.modeActive : ''}`}
            onClick={() => switchMode('single-file')}
          >
            📄 Single File
          </button>
        </div>

        {/* GitHub Repo Mode */}
        {mode === 'repo' && (
          <div className={styles.repoSection}>
            <div className={styles.repoInputGroup}>
              <label className={styles.repoLabel}>
                Enter GitHub Repository URL:
              </label>
              <div className={styles.repoInputRow}>
                <input
                  type="text"
                  className={styles.repoInput}
                  placeholder="e.g., microsoft/vscode or https://github.com/microsoft/vscode"
                  value={repoUrl}
                  onChange={(e) => {
                    setRepoUrl(e.target.value);
                    setValidateStatus(null);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleValidateRepo();
                    }
                  }}
                />
                <button 
                  className={styles.validateButton}
                  onClick={handleValidateRepo}
                  disabled={isValidating || !repoUrl.trim()}
                >
                  {isValidating ? '...' : '✓ Check'}
                </button>
              </div>
            </div>

            {/* Validation Status */}
            {validateStatus && (
              <div className={`${styles.validationStatus} ${validateStatus.is_public ? styles.validPublic : styles.validPrivate}`}>
                {validateStatus.is_public ? (
                  <>
                    <span className={styles.validIcon}>✅</span>
                    <span>
                      <strong>{validateStatus.repo}</strong> - Public Repository
                      {validateStatus.description && <span className={styles.repoDesc}>: {validateStatus.description}</span>}
                    </span>
                  </>
                ) : (
                  <>
                    <span className={styles.invalidIcon}>❌</span>
                    <span>{validateStatus.message}</span>
                  </>
                )}
              </div>
            )}

            {/* Ingest Button */}
            {validateStatus?.is_public && (
              <button 
                className={styles.ingestButton}
                onClick={handleIngest}
                disabled={isLoading || !isConnected}
              >
                {isLoading ? '⏳ Ingesting...' : '📥 Ingest This Repository'}
              </button>
            )}

            {/* Ingested Info */}
            {ingestedRepo && ingestStatus?.total_vectors > 0 && (
              <div className={styles.ingestedInfo}>
                ✅ <strong>{ingestedRepo}</strong> has been ingested! 
                ({ingestStatus.total_vectors} vectors)
              </div>
            )}
          </div>
        )}

        {/* Single File Mode */}
        {mode === 'single-file' && (
          <div className={styles.singleFileSection}>
            {!isFileUploaded ? (
              <>
                <div className={styles.fileUploadNote}>
                  📄 Upload a single file to ask questions about it specifically.
                  This is useful when you want to understand a particular file in detail.
                </div>
                <FileUpload
                  onFileSelect={handleFileSelect}
                  disabled={!isConnected || isLoading}
                />
              </>
            ) : (
              <div className={styles.fileUploadedInfo}>
                ✅ <strong>{uploadedFile?.name}</strong> is uploaded and ready!
                <br />
                <small>You can now ask questions about this file.</small>
              </div>
            )}
          </div>
        )}

        {/* Info Bar */}
        <div className={styles.infoBar}>
          <div className={styles.infoItem}>
            <span className={styles.infoLabel}>Mode:</span>
            <span className={styles.infoValue}>
              {mode === 'repo' ? 'GitHub Repo' : 'Single File'}
            </span>
          </div>
          <div className={styles.infoItem}>
            <span className={styles.infoLabel}>Vectors:</span>
            <span className={styles.infoValue}>
              {ingestStatus?.total_vectors || 0}
            </span>
          </div>
          <div className={styles.infoItem}>
            <span className={styles.infoLabel}>Phase:</span>
            <span className={styles.infoValue}>
              {health?.phase || 'Loading...'}
            </span>
          </div>
        </div>

        {/* Response Display */}
        <ResponseDisplay
          question={response?.question || ''}
          answer={response?.answer || ''}
          sources={response?.sources || []}
          hasCode={response?.has_code || false}
          codeBlocks={response?.code_blocks || []}
          voiceAudio={response?.voice_audio}
          isLoading={isLoading}
        />

        {/* Input Section */}
        <div className={styles.inputSection}>
          <QuestionInput
            onSubmit={handleAskQuestion}
            isLoading={isLoading}
            disabled={!isConnected}
          />
          
          <div className={styles.inputTools}>
            <VoiceInput
              onVoiceInput={handleVoiceInput}
              disabled={!isConnected}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className={styles.footer}>
        <p>
          Powered by Gemini LLM + Pinecone Vector DB
        </p>
      </footer>
    </div>
  );
}
