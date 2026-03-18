import requests
import re
import io
import zipfile
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubIngestor:
    
    def __init__(self, repo: str = None):
        self._repo = ""
        self.repo = repo or settings.github_repo
        self.github_token = settings.github_token
        self.base_url = "https://api.github.com"
        
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"
    
    @property
    def repo(self) -> str:
        return self._repo
    
    @repo.setter
    def repo(self, value: str):
        if not value:
            self._repo = ""
            return
            
        cleaned = value.strip().rstrip("/")
        if "github.com/" in cleaned:
            cleaned = cleaned.split("github.com/")[-1]
        if cleaned.endswith(".git"):
            cleaned = cleaned[:-4]
            
        parts = cleaned.split("/")
        if len(parts) >= 2:
            self._repo = f"{parts[-2]}/{parts[-1]}"
        else:
            self._repo = cleaned
        
        logger.info(f"GitHubIngestor: Initialized with repo '{self._repo}' (original: '{value}')")

    def get_repo_info(self) -> Dict[str, Any]:
        if not self.repo:
            raise ValueError("No repository specified")
            
        url = f"{self.base_url}/repos/{self.repo}"
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        return response.json()

    def chunk_content(self, content: str, chunk_size: int = None, chunk_overlap: int = None) -> List[Dict[str, Any]]:
        chunk_size = chunk_size or getattr(settings, "chunk_size", 500)
        chunk_overlap = chunk_overlap or getattr(settings, "chunk_overlap", 50)
        
        chunks = []
        paragraphs = re.split(r"\n\n+", content)
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para: continue
            
            if len(current_chunk) + len(para) + 2 > chunk_size:
                if current_chunk:
                    chunks.append({"text": current_chunk.strip()})
                current_chunk = para
            else:
                current_chunk = f"{current_chunk}\n\n{para}" if current_chunk else para
                
        if current_chunk:
            chunks.append({"text": current_chunk.strip()})
            
        for i, chunk in enumerate(chunks):
            chunk["index"] = i
        return chunks

    def extract_metadata(self, file_path: str, content: str) -> Dict[str, Any]:
        return {
            "source": file_path,
            "file_type": Path(file_path).suffix,
            "language": self._detect_language(file_path)
        }

    def _detect_language(self, file_path: str) -> str:
        ext_map = {".py": "python", ".js": "javascript", ".ts": "typescript", ".java": "java", ".md": "markdown"}
        return ext_map.get(Path(file_path).suffix, "text")

    def fetch_and_chunk_repo(self, extensions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        if not self.repo:
            raise ValueError("No repository specified for ingestion")

        branch = "main"
        try:
            info = self.get_repo_info()
            branch = info.get("default_branch", "main")
        except Exception as e:
            logger.warning(f"Branch detection failed for {self.repo}, using fallback 'main': {e}")

        zip_url = f"https://github.com/{self.repo}/archive/refs/heads/{branch}.zip"
        logger.info(f"Downloading ZIP: {zip_url}")
        
        resp = requests.get(zip_url, timeout=60)
        if resp.status_code != 200 and branch == "main":
            logger.info("Main branch ZIP failed, trying master...")
            zip_url = f"https://github.com/{self.repo}/archive/refs/heads/master.zip"
            resp = requests.get(zip_url, timeout=60)

        if resp.status_code != 200:
            raise Exception(f"Failed to download repository {self.repo} (HTTP {resp.status_code}). URL: {zip_url}")

        all_chunks = []
        with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
            for info in z.infolist():
                if info.is_dir() or info.file_size > 1024 * 1024:
                    continue
                
                if extensions and not any(info.filename.endswith(ext) for ext in extensions):
                    continue
                    
                try:
                    with z.open(info) as f:
                        text = f.read().decode('utf-8', errors='ignore')
                    
                    if not text.strip(): continue
                    
                    metadata = self.extract_metadata(info.filename, text)
                    chunks = self.chunk_content(text)
                    for chunk in chunks:
                        chunk.update(metadata)
                    all_chunks.extend(chunks)
                except Exception as e:
                    logger.warning(f"Error processing {info.filename}: {e}")
                    
        return all_chunks

github_ingestor = GitHubIngestor()

def ingest_github_repo(repo: str = None, extensions: List[str] = None):
    ingestor = GitHubIngestor(repo=repo)
    return ingestor.fetch_and_chunk_repo(extensions=extensions)
