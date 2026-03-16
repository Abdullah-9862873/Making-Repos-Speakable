# =============================================================================
# AI Multimodal Tutor - Configuration Management
# =============================================================================
# Phase: 2 - Backend Core Components
# Purpose: Centralized configuration using environment variables
# Version: 2.0.0
# =============================================================================

import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    This class provides a centralized way to access configuration
    values throughout the application. All values are loaded from
    the .env file at application startup.
    """
    
    # =============================================================================
    # PINECONE VECTOR DATABASE CONFIGURATION
    # =============================================================================
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
    pinecone_environment: str = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
    pinecone_index_name: str = os.getenv("PINECONE_INDEX_NAME", "course-vectors")
    
    # =============================================================================
    # GOOGLE GEMINI LLM CONFIGURATION
    # =============================================================================
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-pro")
    
    # =============================================================================
    # GITHUB INTEGRATION CONFIGURATION (Public Repos Only)
    # =============================================================================
    # Note: Token not required for public repositories
    # Token only needed for private repos or higher rate limits
    github_repo: str = os.getenv("GITHUB_REPO", "")
    github_token: str = os.getenv("GITHUB_TOKEN", "")  # Optional: for higher rate limits
    
    # =============================================================================
    # GOOGLE CLOUD PLATFORM CONFIGURATION
    # =============================================================================
    google_cloud_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    google_cloud_region: str = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
    
    # =============================================================================
    # APPLICATION CONFIGURATION
    # =============================================================================
    backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # =============================================================================
    # RAG PIPELINE CONFIGURATION
    # =============================================================================
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    top_k_results: int = int(os.getenv("TOP_K_RESULTS", "5"))
    similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    
    # =============================================================================
    # INGESTION CONFIGURATION
    # =============================================================================
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create singleton instance
settings = Settings()


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_pinecone_config() -> bool:
    """
    Validate Pinecone configuration.
    
    Returns:
        True if configuration is valid, False otherwise.
    """
    if not settings.pinecone_api_key:
        print("WARNING: PINECONE_API_KEY not set")
        return False
    return True


def validate_github_config() -> bool:
    """
    Validate GitHub configuration.
    
    For public repositories, only the repo name is required.
    Token is optional (not needed for public repos).
    
    Returns:
        True if configuration is valid, False otherwise.
    """
    if not settings.github_repo:
        print("WARNING: GITHUB_REPO not set")
        return False
    return True


def validate_gemini_config() -> bool:
    """
    Validate Gemini API configuration.
    
    Returns:
        True if configuration is valid, False otherwise.
    """
    if not settings.gemini_api_key:
        print("WARNING: GEMINI_API_KEY not set")
        return False
    return True


def validate_all_configs() -> dict:
    """
    Validate all configuration settings.
    
    Returns:
        Dictionary with validation results for each service.
    """
    return {
        "pinecone": validate_pinecone_config(),
        "github": validate_github_config(),
        "gemini": validate_gemini_config()
    }
