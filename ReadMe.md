# 🤖 AI Multimodal Tutor

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-00a859?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb?logo=react)](https://react.dev)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?logo=next.js)](https://nextjs.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**An AI-powered tutor that transforms any GitHub programming course into an interactive learning assistant**

</div>

---

## 📚 Overview

AI Multimodal Tutor is a hackathon project that transforms a GitHub programming course into a live AI-powered tutor. Students can ask questions via **text**, **voice**, or **upload code/screenshots**, and the AI instantly retrieves explanations directly from the course content using **Vector Database + RAG + Gemini LLM**.

### Key Features

- 🔗 **GitHub Repo Input** - Enter any public repo URL to learn from it
- ✅ **Public/Private Validation** - Automatically checks if repo is public
- 🗣️ **Voice Input** - Speak your questions directly
- 📝 **Text Input** - Type detailed questions
- 📎 **Single File Upload** - Upload specific file to ask about it only
- 💬 **Smart Responses** - AI-generated answers grounded in course material
- 🎨 **Code Highlighting** - Beautiful syntax-highlighted code examples
- 🔊 **Voice Output** - Listen to answers via Text-to-Speech
- 📖 **Source Tracking** - See which course materials were used

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11+, FastAPI, Uvicorn |
| **Vector Database** | Pinecone |
| **LLM** | Google Gemini Pro |
| **Embeddings** | Sentence-Transformers (all-MiniLM-L6-v2) |
| **Frontend** | React 18, Next.js 14, TypeScript |
| **Voice** | Web Speech API, gTTS |
| **Deployment** | Docker, Google Cloud Run |

---

## 🚀 How It Works

### Mode 1: GitHub Repository (Main Feature)

```
1. Enter GitHub Repo URL (e.g., microsoft/vscode)
2. Validate: Public or Private?
   - If Private → Show error "Please enter a public repository"
   - If Public → Enable "Ingest This Repo" button
3. Click "Ingest This Repo"
4. Files fetched, chunked, embedded, stored in Pinecone
5. Ask questions via text or voice
6. Get AI answers grounded in YOUR repo content!
```

### Mode 2: Single File (Optional)

```
1. Upload a single file (e.g., main.py)
2. Ask questions about ONLY that file
3. Get answers specific to that file!
```

---

## 📁 Project Structure

```
ai-tutor-hackathon/
├── backend/                      # FastAPI backend
│   ├── main.py                 # Application entry point
│   ├── config.py               # Configuration management
│   ├── vector_db.py            # Pinecone operations
│   ├── embeddings.py           # Sentence-transformer embeddings
│   ├── github_ingest.py        # GitHub content fetching
│   ├── ingestion_pipeline.py   # Complete ingestion workflow
│   ├── rag_pipeline.py          # RAG retrieval pipeline
│   ├── prompt_templates.py      # LLM prompt templates
│   ├── llm_chain.py            # Gemini LLM integration
│   ├── multimodal.py            # Multimodal output generator
│   ├── tts_service.py          # Text-to-Speech service
│   └── requirements.txt        # Python dependencies
│
├── frontend/                     # Next.js frontend
│   ├── components/
│   │   ├── QuestionInput.tsx   # Text question input
│   │   ├── ResponseDisplay.tsx # AI response display
│   │   ├── VoiceInput.tsx      # Voice recording
│   │   └── FileUpload.tsx      # File upload
│   ├── lib/
│   │   └── api.ts             # API service layer
│   ├── pages/
│   │   ├── _app.tsx           # App wrapper
│   │   └── index.tsx          # Main page
│   ├── styles/                  # CSS modules
│   ├── package.json
│   └── tsconfig.json
│
├── docker/
│   ├── Dockerfile              # Backend container
│   └── .dockerignore
│
├── .env                         # Environment variables
├── .env.example                # Environment template
├── README.md                   # This file
└── RUNNING.md                  # Running instructions
```

---

## 📋 Phases Implementation

### ✅ Phase 1: Project Setup & Infrastructure

| Attribute | Details |
|-----------|---------|
| **Aim** | Set up project structure, virtual environment, Docker, and environment variables |
| **Technologies** | Python 3.11, Docker, pip |
| **Language** | Python (backend), JSON (config) |
| **Files Created** | `backend/requirements.txt`, `docker/Dockerfile`, `.env.example` |

**Testing Phase 1:**
```bash
# Verify Python environment
python --version

# Check installed packages
pip list
```

---

### ✅ Phase 2: Backend Core Components

| Attribute | Details |
|-----------|---------|
| **Aim** | Implement Vector DB connection, GitHub ingestion, and embedding generation |
| **Technologies** | Pinecone, Sentence-Transformers, GitHub API |
| **Language** | Python |
| **Files Created** | `config.py`, `vector_db.py`, `embeddings.py`, `github_ingest.py`, `ingestion_pipeline.py` |

**API Endpoints:**
- `POST /validate-repo` - Validate GitHub repo (public/private) - **NEW**
- `POST /ingest` - Ingest GitHub repository
- `GET /ingest/status` - Get ingestion status
- `POST /ingest/single` - Ingest single file - **NEW**

**Testing Phase 2:**
```bash
# Start backend
cd backend && uvicorn main:app --reload

# Validate a repository
curl -X POST "http://localhost:8000/validate-repo" \
  -H "Content-Type: application/json" \
  -d '{"repo": "microsoft/vscode"}'

# Ingest a public repository
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{"repo": "microsoft/vscode", "extensions": [".md", ".py"]}'

# Check status
curl http://localhost:8000/ingest/status
```

---

### ✅ Phase 3: RAG Pipeline

| Attribute | Details |
|-----------|---------|
| **Aim** | Implement retrieval-augmented generation pipeline with similarity search |
| **Technologies** | Pinecone, Custom RAG implementation |
| **Language** | Python |
| **Files Created** | `rag_pipeline.py`, `prompt_templates.py` |

**Features:**
- Query preprocessing
- Vector similarity search
- Metadata filtering
- Context assembly

**Testing Phase 3:**
```bash
# Test RAG query (raw context)
curl -X POST "http://localhost:8000/rag/query?query=What%20is%20merge%20sort&top_k=3"
```

---

### ✅ Phase 4: LLM Integration

| Attribute | Details |
|-----------|---------|
| **Aim** | Integrate Gemini LLM for generating course-grounded answers |
| **Technologies** | Google Gemini Pro, google-generativeai |
| **Language** | Python |
| **Files Created** | `llm_chain.py`, `multimodal.py`, `tts_service.py` |

**Features:**
- RAG + LLM answer generation
- Code block extraction
- Source tracking
- Voice output (TTS)

**Testing Phase 4:**
```bash
# Ask a question
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is merge sort?", "top_k": 5}'
```

---

### ✅ Phase 5: Frontend Development

| Attribute | Details |
|-----------|---------|
| **Aim** | Build responsive React/Next.js UI with all input/output methods |
| **Technologies** | React 18, Next.js 14, TypeScript, CSS Modules |
| **Language** | TypeScript, CSS |
| **Files Created** | `components/*`, `pages/*`, `styles/*`, `lib/api.ts` |

**Features:**
- Clean modern UI
- Question input with keyboard shortcuts
- Voice input button
- File upload for code/screenshots
- Response display with syntax highlighting
- Connection status indicator

**Testing Phase 5:**
```bash
# Start frontend
cd frontend
npm install
npm run dev

# Open http://localhost:3000
```

---

### ⏳ Phase 6: Multimodal I/O Features

| Attribute | Details |
|-----------|---------|
| **Aim** | Complete voice I/O, diagram display, and advanced file handling |
| **Technologies** | Web Speech API, gTTS |
| **Language** | TypeScript, JavaScript |

**Features (In Progress):**
- Enhanced voice input
- Voice output playback
- Image/diagram display
- Advanced file uploads

---

### ⏳ Phase 7: Integration & Testing

| Attribute | Details |
|-----------|---------|
| **Aim** | Connect frontend to backend and perform end-to-end testing |
| **Technologies** | All integrated |
| **Language** | Full stack |

---

### ⏳ Phase 8: Deployment & Demo

| Attribute | Details |
|-----------|---------|
| **Aim** | Deploy to Google Cloud Run and prepare demo |
| **Technologies** | Docker, Google Cloud Run, GCP |
| **Language** | Shell, YAML |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Pinecone API Key
- Gemini API Key

### 1. Clone & Setup

```bash
git clone <your-repo-url>
cd ai-tutor-hackathon
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```env
PINECONE_API_KEY=your_pinecone_key
GEMINI_API_KEY=your_gemini_key
GITHUB_REPO=owner/repository-name
```

Get keys:
- **Pinecone**: https://app.pinecone.io/
- **Gemini**: https://aistudio.google.com/app/apikey

### 3. Run Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install gtts

# Run server
uvicorn main:app --reload
```

Backend runs at: http://localhost:8000

### 4. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:3000

### 5. Use the App

1. Open http://localhost:3000
2. Click **"📥 Ingest Course"** to load a GitHub repo
3. Ask questions using text or voice!

---

## 📖 API Documentation

Once the backend is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/` | API information |
| POST | `/validate-repo` | Validate GitHub repo (public/private) |
| POST | `/ingest` | Ingest GitHub repository to vector DB |
| POST | `/ingest/single` | Ingest single uploaded file |
| GET | `/ingest/status` | Get ingestion status |
| POST | `/ask` | Ask question (uses repo content) |
| POST | `/ask/single` | Ask about single file only |
| POST | `/rag/query` | Direct RAG query |
| POST | `/ask/voice` | Voice question (Phase 6) |

---

## 🧪 Testing Commands

```bash
# Health check
curl http://localhost:8000/health

# Validate repository
curl -X POST "http://localhost:8000/validate-repo" \
  -H "Content-Type: application/json" \
  -d '{"repo": "microsoft/vscode"}'

# Ingest repository
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{"repo": "microsoft/vscode", "extensions": [".md", ".py"]}'

# Ask question
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is merge sort?"}'

# RAG query only
curl -X POST "http://localhost:8000/rag/query?query=What+is+merge+sort"
```

---

## 📝 License

MIT License - feel free to use this project for learning or hackathons!

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com) - Modern Python web framework
- [Pinecone](https://pinecone.io) - Vector database
- [Google Gemini](https://gemini.google.com) - AI language model
- [Sentence-Transformers](https://sbert.net) - Embedding models
- [Next.js](https://nextjs.org) - React framework

---

<div align="center">

**Built with ❤️ for the Gemini Live Agent Hackathon**

</div>
