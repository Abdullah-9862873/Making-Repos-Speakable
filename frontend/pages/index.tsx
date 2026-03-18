import { useState, useEffect } from 'react';
import Head from 'next/head';
import QuestionInput from '../components/QuestionInput';
import ResponseDisplay from '../components/ResponseDisplay';
import VoiceInput from '../components/VoiceInput';
import FileUpload from '../components/FileUpload';
import ConfirmModal from '../components/ConfirmModal';
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
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string>('');
  const [ingestStatus, setIngestStatus] = useState<any>(null);
  const [successMessage, setSuccessMessage] = useState<{title: string; message: string} | null>(null);
  const [repoUrl, setRepoUrl] = useState<string>('');
  const [validateStatus, setValidateStatus] = useState<ValidateResponse | null>(null);
  const [isValidating, setIsValidating] = useState<boolean>(false);
  const [mode, setMode] = useState<Mode>('repo');
  const [ingestedRepo, setIngestedRepo] = useState<string>('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isFileUploaded, setIsFileUploaded] = useState<boolean>(false);
  const [showClearModal, setShowClearModal] = useState<boolean>(false);

  useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = async () => {
    try {
      const healthData = await apiService.getHealth();
      setHealth(healthData);
      setIsConnected(true);
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
      setSuccessMessage(null);
      return;
    }
    setIsLoading(true);
    setError('');
    setSuccessMessage(null);
    try {
      console.log('Starting ingestion for:', repoUrl);
      const result = await apiService.ingestCourse(repoUrl, ['.md', '.py', '.js', '.ts', '.txt', '.java', '.cpp', '.go', '.rs']);
      console.log('Ingestion result:', result);
      setSuccessMessage({
        title: 'GitHub Repo Successfully Ingested!',
        message: result.message || `Successfully ingested ${result.chunks_created || result.vectors_stored} chunks`
      });
      const status = await apiService.getIngestStatus();
      setIngestStatus(status);
      setIngestedRepo(repoUrl);
    } catch (err: any) {
      console.error('Ingestion error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to ingest course');
      setSuccessMessage(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearAndIngest = async () => {
    if (!validateStatus?.is_public) {
      setError('Please validate a public repository first');
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      if (ingestStatus?.total_vectors > 0) {
        await apiService.clearIngestion();
      }
      const result = await apiService.ingestCourse(repoUrl, ['.md', '.py', '.js', '.ts', '.txt', '.java', '.cpp', '.go', '.rs']);
      setSuccessMessage({
        title: 'GitHub Repo Successfully Replaced!',
        message: `Cleared previous data and ingested new repository. ${result.message}`
      });
      const status = await apiService.getIngestStatus();
      setIngestStatus(status);
      setIngestedRepo(repoUrl);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to replace repository');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearData = async () => {
    setShowClearModal(true);
  };

  const confirmClearData = async () => {
    setShowClearModal(false);
    setIsLoading(true);
    setError('');
    setSuccessMessage(null);
    try {
      await apiService.clearIngestion();
    } catch (err: any) {
      console.log('Clear operation attempted');
    } finally {
      setIngestStatus({ total_vectors: 0 });
      setIngestedRepo('');
      setResponse(null);
      setUploadedFile(null);
      setIsFileUploaded(false);
      setValidateStatus(null);
      setRepoUrl('');
      setIsLoading(false);
      setSuccessMessage({
        title: 'Data Cleared!',
        message: 'All data has been cleared successfully'
      });
    }
  };

  const handleAskQuestion = async (question: string) => {
    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      let result;
      if (mode === 'single-file') {
        result = await apiService.askSingleFile(question);
      } else {
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
      const result = await apiService.ingestSingleFile(file);
      console.log('File ingested:', result);
      setIsFileUploaded(true);
      setSuccessMessage({
        title: 'File Uploaded Successfully!',
        message: `"${file.name}" is ready. You can now ask questions about it.`
      });
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
        <title>Making Repos Speakable</title>
        <meta name="description" content="Give life to your repositories. Ask anything about any codebase." />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.title}>Making Repos Speakable</h1>
          <p className={styles.subtitle}>
            Give life to your repositories. Ask anything about any codebase.
          </p>
        </div>
        <div className={styles.status}>
          <span className={`${styles.statusDot} ${isConnected ? styles.connected : styles.disconnected}`} />
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </header>
      <main className={styles.main}>
        {error && error.trim() && (
          <div className={styles.error}>
            {error}
            <button onClick={() => setError('')} className={styles.errorClose}>
              ✕
            </button>
          </div>
        )}
        {successMessage && (
          <div className={styles.successPopup}>
            <div className={styles.successContent}>
              <div className={styles.successIcon}>✅</div>
              <div className={styles.successText}>
                <div className={styles.successTitle}>{successMessage.title}</div>
                <div className={styles.successMessage}>{successMessage.message}</div>
              </div>
              <button onClick={() => setSuccessMessage(null)} className={styles.successClose}>
                ✕
              </button>
            </div>
          </div>
        )}
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
            {validateStatus && (
              <div className={`${styles.validationStatus} ${validateStatus.is_public ? styles.validPublic : styles.validPrivate}`}>
                {validateStatus.is_public ? (
                  <>
                    <span className={styles.validIcon}>✅ OK</span>
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
            {validateStatus?.is_public && (
              <div className={styles.ingestButtonGroup}>
                <button
                  className={styles.ingestButton}
                  onClick={handleIngest}
                  disabled={isLoading || !isConnected}
                >
                  {isLoading ? '⏳ Ingesting...' : '📥 Ingest This Repository'}
                </button>
                {ingestStatus?.total_vectors > 0 && (
                  <button
                    className={styles.clearButton}
                    onClick={handleClearAndIngest}
                    disabled={isLoading || !isConnected}
                    title="Clear previous data and ingest new repository"
                  >
                    {isLoading ? '⏳...' : '🗑️ Clear & Ingest New'}
                  </button>
                )}
              </div>
            )}
            {ingestedRepo && ingestStatus?.total_vectors > 0 && (
              <div className={styles.ingestedInfo}>
                <div className={styles.successHeader}>
                  <span className={styles.successIcon}>✅</span>
                  <strong>GitHub Repo Successfully Ingested!</strong>
                </div>
                <div className={styles.successDetails}>
                  <div className={styles.successItem}>
                    <span className={styles.successLabel}>Repository:</span>
                    <span className={styles.successValue}>{ingestedRepo}</span>
                  </div>
                  <div className={styles.successItem}>
                    <span className={styles.successLabel}>Vectors Stored:</span>
                    <span className={styles.successValue}>{ingestStatus.total_vectors}</span>
                  </div>
                  <div className={styles.successItem}>
                    <span className={styles.successLabel}>Status:</span>
                    <span className={styles.successValue}>Ready to answer questions!</span>
                  </div>
                </div>
                <button
                  className={styles.clearDataButton}
                  onClick={handleClearData}
                  disabled={isLoading}
                >
                  🗑️ Clear All Data
                </button>
              </div>
            )}
          </div>
        )}
        {mode === 'single-file' && (
          <div className={styles.singleFileSection}>
            {!isFileUploaded ? (
              <>
                <div className={styles.fileUploadNote}>
                  📄 Upload a single file to ask questions about it specifically.
                  This is useful when you want to understand a particular file in detail.
                </div>
                <div className={styles.supportedFormats}>
                  <strong>Supported formats:</strong> .py, .java, .md, .txt, .js, .ts, .cpp, .c, .go, .rs, .rb, .php, .swift, .kt, .sql, .sh, .json, .yaml, .xml, .html, .css, and all other file formats
                </div>
                <FileUpload
                  onFileSelect={handleFileSelect}
                  disabled={!isConnected || isLoading}
                />
              </>
            ) : (
              <div className={styles.fileUploadedInfo}>
                <div className={styles.fileSuccessHeader}>
                  <span className={styles.fileSuccessIcon}>✅</span>
                  <strong>File Uploaded Successfully!</strong>
                </div>
                <div className={styles.fileNameDisplay}>
                  📄 <strong>{uploadedFile?.name}</strong>
                </div>
                <p className={styles.fileReadyText}>You can now ask questions about this file.</p>
              </div>
            )}
          </div>
        )}
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
          {ingestStatus?.total_vectors > 0 && (
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>Data:</span>
              <span className={styles.infoValue}>
                {ingestStatus.total_vectors} vectors
              </span>
              <button
                className={styles.clearDataSmallButton}
                onClick={handleClearData}
                disabled={isLoading}
                title="Clear all data from vector database"
              >
                🗑️ Clear
              </button>
            </div>
          )}
        </div>
        <ResponseDisplay
          question={response?.question || ''}
          answer={response?.answer || ''}
          sources={response?.sources || []}
          hasCode={response?.has_code || false}
          codeBlocks={response?.code_blocks || []}
          voiceAudio={response?.voice_audio}
          isLoading={isLoading}
        />
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
      <footer className={styles.footer}>
        <p>
          Powered by Groq LLM + Pinecone Vector DB
        </p>
      </footer>
      <ConfirmModal
        isOpen={showClearModal}
        title="Clear All Data?"
        message="Are you sure you want to clear all data? This will remove all ingested repositories and uploaded files. This action cannot be undone."
        confirmText="Clear All"
        cancelText="Cancel"
        icon="🗑️"
        onConfirm={confirmClearData}
        onCancel={() => setShowClearModal(false)}
      />
    </div>
  );
}
