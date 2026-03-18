import os
from dotenv import load_dotenv

possible_paths = [
    os.path.join(os.path.dirname(__file__), '..', '.env'),
    os.path.join(os.path.dirname(__file__), '.env'),
    os.path.join(os.getcwd(), '.env'),
]

for path in possible_paths:
    if os.path.exists(path):
        load_dotenv(path, override=True)
        print(f"Loaded env from: {path}")
        break


class Settings:
    pinecone_api_key = os.getenv("PINECONE_API_KEY", "")
    pinecone_environment = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
    pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "course-vectors")
    
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    
    github_repo = os.getenv("GITHUB_REPO", "")
    github_token = os.getenv("GITHUB_TOKEN", "")
    
    backend_host = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port = int(os.getenv("BACKEND_PORT", "8000"))
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    top_k_results = int(os.getenv("TOP_K_RESULTS", "5"))
    similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.3"))
    
    chunk_size = 500
    chunk_overlap = 50


settings = Settings()


def validate_pinecone_config() -> bool:
    if not settings.pinecone_api_key:
        print("WARNING: PINECONE_API_KEY not set")
        return False
    return True


def validate_github_config() -> bool:
    if not settings.github_repo:
        print("WARNING: GITHUB_REPO not set")
        return False
    return True


def validate_all_configs() -> dict:
    return {
        "pinecone": validate_pinecone_config(),
        "github": validate_github_config(),
    }
