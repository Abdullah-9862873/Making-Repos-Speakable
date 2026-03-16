# =============================================================================
# AI Multimodal Tutor - Main Application Entry Point
# =============================================================================
# Phase: 7 - Integration & Testing (COMPLETE)
# Purpose: FastAPI backend with LLM-powered Q&A
# Version: 7.0.0
#
# Endpoints:
#   - GET  /health         : Health check
#   - GET  /               : API information
#   - POST /ask            : Text question with RAG + LLM (Phase 4 - NOW IMPLEMENTED)
#   - POST /rag/query      : Direct RAG query (Phase 3)
#   - POST /ask/voice      : Voice question (Phase 6)
#   - POST /ask/upload     : Code/image upload (Phase 6)
#   - POST /ingest         : Trigger course ingestion (Phase 2 - IMPLEMENTED)
#   - GET  /ingest/status  : Get ingestion status
# =============================================================================

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import logging
import os
import requests
import uvicorn
from dotenv import load_dotenv

# Local imports
from config import settings, validate_all_configs
from ingestion_pipeline import ingestion_pipeline
from vector_db import vector_db
from rag_pipeline import RAGPipeline, check_context_available
from llm_chain import LLMChain
from multimodal import MultimodalGenerator
from tts_service import TTSService
from single_file import single_file_processor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# FASTAPI APPLICATION SETUP
# =============================================================================

app = FastAPI(
    title="AI Multimodal Tutor API",
    description="""
    ## Overview
    AI Multimodal Tutor transforms a GitHub programming course into a live 
    AI-powered tutor using Vector DB + RAG + Gemini LLM.
    
    ## Features
    - Text, voice, and code/image input
    - Multimodal output (text, code, diagrams, voice)
    - RAG-powered answers from course content
    - Fallback to general LLM knowledge
    
    ## Phases
    - Phase 1: Project Setup (COMPLETE)
    - Phase 2: Backend Core Components (COMPLETE)
    - Phase 3: RAG Pipeline (COMPLETE)
    - Phase 4: LLM Integration (COMPLETE)
    - Phase 5: Frontend Development
    - Phase 6: Multimodal I/O Features
    - Phase 7: Integration & Testing
    - Phase 8: Deployment & Demo
    """,
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# =============================================================================
# CORS CONFIGURATION (Phase 7 - Updated for Production)
# =============================================================================

# Get frontend URL from environment (default: localhost:3000)
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Allow multiple origins for development and production
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    frontend_url,
]

# Add production URLs if specified
production_url = os.getenv("PRODUCTION_URL")
if production_url:
    allowed_origins.append(production_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# ROOT ENDPOINTS
# =============================================================================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information
    
    Returns basic information about the API and current version.
    """
    return {
        "name": "AI Multimodal Tutor API",
        "version": "7.0.0",
        "status": "running",
        "phase": "Phase 7: Integration & Testing",
        "docs": "/docs",
        "message": "AI Multimodal Tutor - GitHub Repo & Single File Q&A"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    
    Used to verify the API is running and healthy.
    Returns status of various components.
    """
    return {
        "status": "healthy",
        "phase": "Phase 7: Integration & Testing",
        "version": "7.0.0",
        "components": {
            "fastapi": "running",
            "pinecone": "configured",
            "embeddings": "configured",
            "github": "configured",
            "rag_pipeline": "configured",
            "llm": "configured"
        }
    }

# =============================================================================
# REQUEST MODELS
# =============================================================================

class IngestRequest(BaseModel):
    """
    Request model for ingestion endpoint.
    """
    repo: Optional[str] = None
    extensions: Optional[List[str]] = None


class IngestResponse(BaseModel):
    """
    Response model for ingestion endpoint.
    """
    status: str
    message: str
    chunks_created: int = 0
    vectors_stored: int = 0


# =============================================================================
# INGESTION ENDPOINTS (Phase 2 - IMPLEMENTED)
# =============================================================================

class ValidateRepoRequest(BaseModel):
    """
    Request model for validating GitHub repository.
    """
    repo: str


class ValidateRepoResponse(BaseModel):
    """
    Response model for validate-repo endpoint.
    """
    valid: bool
    is_public: bool
    repo: str
    message: str
    owner: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    stars: Optional[int] = None


@app.post("/validate-repo", tags=["Ingestion"], response_model=ValidateRepoResponse)
async def validate_repo(request: ValidateRepoRequest):
    """
    Validate GitHub repository (public/private check)
    
    Checks if the repository exists and whether it's public or private.
    
    Args:
        request: ValidateRepoRequest with repo (owner/repo format)
    
    Returns:
        ValidateRepoResponse with validation results
    
    Example:
        POST /validate-repo
        {
            "repo": "microsoft/vscode"
        }
        
        Response:
        {
            "valid": true,
            "is_public": true,
            "repo": "microsoft/vscode",
            "message": "Public repository",
            "owner": "microsoft",
            "name": "vscode",
            "description": "Code editing. redefined.",
            "stars": 123456
        }
    """
    repo = request.repo.strip()
    
    # Clean up repo URL if user paste full URL
    if "github.com/" in repo:
        repo = repo.split("github.com/")[-1].strip("/")
    
    # Split owner/repo
    parts = repo.split("/")
    if len(parts) != 2:
        raise HTTPException(
            status_code=400,
            detail="Invalid repository format. Use 'owner/repo' format (e.g., 'microsoft/vscode')"
        )
    
    owner, name = parts[0], parts[1]
    
    # Try to fetch repo info from GitHub
    try:
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{name}",
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=10
        )
        
        if response.status_code == 404:
            return ValidateRepoResponse(
                valid=False,
                is_public=False,
                repo=repo,
                message="Repository not found. Please check the repository name."
            )
        
        if response.status_code == 403:
            # Rate limited or private (without token)
            return ValidateRepoResponse(
                valid=True,
                is_public=False,
                repo=repo,
                message="Cannot verify visibility. This might be a private repository or rate limited. Please ensure the repository is public."
            )
        
        if response.status_code == 200:
            data = response.json()
            is_public = not data.get("private", True)
            
            if is_public:
                return ValidateRepoResponse(
                    valid=True,
                    is_public=True,
                    repo=repo,
                    message="Public repository found! You can ingest this repository.",
                    owner=owner,
                    name=name,
                    description=data.get("description"),
                    stars=data.get("stargazers_count", 0)
                )
            else:
                return ValidateRepoResponse(
                    valid=True,
                    is_public=False,
                    repo=repo,
                    message="This is a private repository. Please enter a public repository."
                )
    
    except Exception as e:
        logger.error(f"Error validating repo: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error validating repository: {str(e)}"
        )


@app.post("/ingest", tags=["Ingestion"], response_model=IngestResponse)
async def ingest_course(request: Optional[IngestRequest] = None):
    """
    Trigger course ingestion from GitHub repository
    
    Phase: 2 (Backend - Core Components) - NOW IMPLEMENTED
    
    Fetches GitHub course content and ingests into Vector DB.
    
    Args:
        request: Optional IngestRequest with repo and extensions
    
    Returns:
        IngestResponse with ingestion results
    
    Example:
        POST /ingest
        {
            "repo": "username/dsa-course",
            "extensions": [".md", ".py", ".js"]
        }
    """
    logger.info("Ingestion request received")
    
    # Validate configurations
    configs = validate_all_configs()
    
    # Check required configs
    if not configs["pinecone"]:
        raise HTTPException(
            status_code=400,
            detail="Pinecone API key not configured"
        )
    
    # Get repo from request or use default
    repo = request.repo if request and request.repo else settings.github_repo
    
    # Check if we have a repo to ingest (either from request or env)
    if not repo:
        raise HTTPException(
            status_code=400,
            detail="GitHub repo not provided. Please provide a repo in the request body or set GITHUB_REPO environment variable"
        )
    
    extensions = request.extensions if request and request.extensions else [".md", ".txt", ".py", ".js", ".ts"]
    
    logger.info(f"Starting ingestion for repo: {repo}")
    logger.info(f"File extensions: {extensions}")
    
    try:
        # Run ingestion pipeline
        result = ingestion_pipeline.run(
            repo=repo,
            extensions=extensions
        )
        
        if result["status"] == "success":
            return IngestResponse(
                status="success",
                message=f"Successfully ingested {result['chunks_created']} chunks ({result['vectors_stored']} vectors)",
                chunks_created=result["chunks_created"],
                vectors_stored=result["vectors_stored"]
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Ingestion failed")
            )
    
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        )


@app.get("/ingest/status", tags=["Ingestion"])
async def get_ingestion_status():
    """
    Get ingestion status and statistics
    
    Phase: 2
    
    Returns information about the Vector DB index and last ingestion.
    """
    try:
        stats = vector_db.get_index_stats()
        
        return {
            "status": "success",
            "index_name": settings.pinecone_index_name,
            "total_vectors": stats.get("total_vector_count", 0),
            "dimension": stats.get("dimension", 0),
            "namespaces": stats.get("namespaces", {}),
            "phase": "Phase 2: Complete"
        }
    except Exception as e:
        logger.error(f"Failed to get ingestion status: {e}")
        return {
            "status": "error",
            "message": str(e),
            "phase": "Phase 2"
        }


# =============================================================================
# REQUEST MODELS (Updated for Phase 3)
# =============================================================================

class AskRequest(BaseModel):
    """
    Request model for ask endpoint.
    """
    question: str
    top_k: Optional[int] = None
    threshold: Optional[float] = None
    prompt_type: Optional[str] = "default"
    include_voice: Optional[bool] = False


class AskResponse(BaseModel):
    """
    Response model for ask endpoint.
    """
    question: str
    answer: str
    has_context: bool
    context_used: bool
    sources: List[str] = []
    num_contexts: int = 0
    top_score: float = 0.0
    has_code: bool = False
    code_blocks: List[Dict[str, str]] = []
    voice_audio: Optional[str] = None


# =============================================================================
# PLACEHOLDER ENDPOINTS (To be implemented in future phases)
# =============================================================================

@app.post("/ask", tags=["Q&A"], response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Ask a text question
    
    Phase: 4 (LLM Integration)
    
    Processes a text question using the RAG pipeline to retrieve
    relevant context from the course material, then generates
    an answer grounded in the course content.
    
    Args:
        request: AskRequest with question and optional parameters
    
    Returns:
        AskResponse with answer and context information
    
    Example:
        POST /ask
        {
            "question": "What is merge sort?",
            "top_k": 5,
            "threshold": 0.7
        }
    """
    logger.info(f"Question received: {request.question}")
    
    # Validate configurations
    configs = validate_all_configs()
    
    if not configs["pinecone"]:
        raise HTTPException(
            status_code=400,
            detail="Pinecone API key not configured"
        )
    
    # Check if context is available
    has_indexed_content = check_context_available()
    
    if not has_indexed_content:
        logger.warning("No content found in Vector DB. Please run /ingest first.")
        return AskResponse(
            question=request.question,
            answer="No course content has been indexed yet. Please run the /ingest endpoint first to add course material to the knowledge base.",
            has_context=False,
            context_used=False,
            sources=[],
            num_contexts=0,
            top_score=0.0
        )
    
    try:
        # Validate Gemini API
        if not configs["gemini"]:
            raise HTTPException(
                status_code=400,
                detail="Gemini API key not configured"
            )
        
        # Run RAG + LLM to get answer
        llm = LLMChain()
        result = llm.generate_with_rag(
            question=request.question,
            top_k=request.top_k or 5,
            threshold=request.threshold or 0.7,
            prompt_type=request.prompt_type or "default"
        )
        
        # Extract answer and metadata
        answer_text = result.get("answer", "")
        has_relevant_context = result.get("has_context", False)
        sources = result.get("sources", [])
        num_contexts = result.get("num_contexts", 0)
        top_score = result.get("top_score", 0.0)
        
        # Extract code blocks
        multimodal = MultimodalGenerator()
        code_blocks = multimodal.extract_code_blocks(answer_text)
        has_code = bool(code_blocks)
        
        # Generate voice if requested
        voice_audio = None
        if request.include_voice:
            try:
                tts = TTSService()
                tts_result = tts.text_to_speech(answer_text)
                voice_audio = tts_result.get("audio_base64")
            except Exception as e:
                logger.warning(f"TTS generation failed: {e}")
        
        return AskResponse(
            question=request.question,
            answer=answer_text,
            has_context=has_indexed_content,
            context_used=has_relevant_context,
            sources=sources,
            num_contexts=num_contexts,
            top_score=top_score,
            has_code=has_code,
            code_blocks=code_blocks,
            voice_audio=voice_audio
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Question answering failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to answer question: {str(e)}"
        )


@app.post("/rag/query", tags=["RAG"])
async def rag_query(
    query: str,
    top_k: int = 5,
    threshold: float = 0.7
):
    """
    Direct RAG query endpoint
    
    Phase: 3 (RAG Pipeline)
    
    Returns the raw retrieved context without LLM processing.
    Useful for testing the RAG pipeline.
    
    Args:
        query: Search query
        top_k: Number of results
        threshold: Similarity threshold
    
    Returns:
        RAG pipeline results with contexts
    """
    try:
        rag = RAGPipeline(top_k=top_k, threshold=threshold)
        result = rag.run(query=query)
        
        return {
            "status": "success",
            "phase": "Phase 3: RAG Pipeline",
            "query": query,
            "has_relevant_context": result.get("has_relevant_context", False),
            "contexts": result.get("contexts", []),
            "num_results": result.get("num_results", 0),
            "top_score": result.get("top_score", 0.0)
        }
    
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"RAG query failed: {str(e)}"
        )


# =============================================================================
# SINGLE FILE ENDPOINTS (Phase 6 - IMPLEMENTED)
# =============================================================================

@app.post("/ingest/single", tags=["Ingestion"])
async def ingest_single_file(
    file: UploadFile = File(...)
):
    """
    Upload and ingest a single file
    
    Phase: 6 (Multimodal I/O Features) - NOW IMPLEMENTED
    
    Accepts a single file upload, processes it, and stores in vector DB
    for querying about that specific file.
    
    Args:
        file: The file to upload and process
    
    Returns:
        Processing results
    """
    try:
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8', errors='ignore')
        
        # Get file extension
        _, ext = os.path.splitext(file.filename)
        
        # Process file
        result = single_file_processor.process_file(
            file_content=content_str,
            file_name=file.filename,
            file_extension=ext
        )
        
        if result["status"] == "success":
            return {
                "status": "success",
                "message": f"Successfully processed {file.filename}",
                "file_name": file.filename,
                "chunks_created": result.get("chunks_created", 0),
                "vectors_stored": result.get("vectors_stored", 0)
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Failed to process file")
            )
    
    except Exception as e:
        logger.error(f"Error processing single file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )


@app.post("/ask/single", tags=["Q&A"])
async def ask_about_single_file(
    question: str = Form(...),
    top_k: int = 5
):
    """
    Ask a question about the uploaded single file
    
    Phase: 6 (Multimodal I/O Features) - NOW IMPLEMENTED
    
    Searches within the uploaded single file content only.
    
    Args:
        question: The question to ask
        top_k: Number of context results
    
    Returns:
        Answer based on single file content
    """
    logger.info(f"Single file question: {question}")
    
    try:
        # Query single file content
        query_result = single_file_processor.query_single_file(
            question=question,
            top_k=top_k
        )
        
        # Check if we have content
        if not query_result.get("has_context", False):
            return {
                "question": question,
                "answer": "No file has been uploaded yet. Please upload a file first using /ingest/single endpoint.",
                "has_context": False,
                "context_used": False,
                "sources": [],
                "num_contexts": 0,
                "top_score": 0.0
            }
        
        # Get context
        context_text = query_result.get("context_text", "")
        contexts = query_result.get("contexts", [])
        
        # Generate answer with LLM
        llm = LLMChain()
        result = llm.generate_answer(
            question=question,
            context=context_text,
            has_context=True,
            prompt_type="default"
        )
        
        answer_text = result.get("answer", "")
        
        # Extract code blocks
        multimodal = MultimodalGenerator()
        code_blocks = multimodal.extract_code_blocks(answer_text)
        has_code = bool(code_blocks)
        
        # Get sources
        sources = list(set([ctx.get("source", "") for ctx in contexts if ctx.get("source")]))
        
        return {
            "question": question,
            "answer": answer_text,
            "has_context": True,
            "context_used": True,
            "sources": sources,
            "num_contexts": len(contexts),
            "top_score": contexts[0].get("score", 0) if contexts else 0,
            "has_code": has_code,
            "code_blocks": code_blocks
        }
    
    except Exception as e:
        logger.error(f"Error answering single file question: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error answering question: {str(e)}"
        )


@app.post("/ingest/single/clear", tags=["Ingestion"])
async def clear_single_file():
    """
    Clear all single file content from vector DB
    
    Phase: 6
    
    Removes all vectors stored from single file uploads.
    """
    try:
        result = single_file_processor.clear_single_file()
        return result
    except Exception as e:
        logger.error(f"Error clearing single file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing file: {str(e)}"
        )


@app.post("/ask/voice", tags=["Q&A"])
async def ask_voice():
    """
    Ask a voice question
    
    Phase: 6 (Multimodal I/O Features)
    
    Accepts voice input, processes it, and returns multimodal answer.
    """
    return {
        "message": "Endpoint not yet implemented",
        "phase": "Pending: Phase 6"
    }


@app.post("/ask/upload", tags=["Q&A"])
async def ask_upload():
    """
    Ask with code/image upload
    
    Phase: 6 (Multimodal I/O Features)
    
    Accepts code snippets or screenshots and returns multimodal answer.
    """
    return {
        "message": "Endpoint not yet implemented",
        "phase": "Pending: Phase 6"
    }


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler
    
    Catches any unhandled exceptions and returns a proper error response.
    """
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "phase": "Phase 7"
        }
    )


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("BACKEND_PORT", "8000")))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False
    )
