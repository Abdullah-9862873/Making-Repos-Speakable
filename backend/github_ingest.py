# =============================================================================
# AI Multimodal Tutor - GitHub Repository Ingestion
# =============================================================================
# Phase: 2 - Backend Core Components
# Purpose: Fetch content from GitHub repo and prepare for vectorization
# Version: 2.0.0 (Updated to use ZIP download to avoid rate limits)
# =============================================================================

import requests
import re
import io
import zipfile
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitHubIngestor:
    """
    GitHub Repository Content Ingestor.
    
    This class handles fetching content from a GitHub repository
    and preparing it for vector database ingestion.
    
    Features:
    - Fetch README and documentation from public repos
    - Parse code files
    - Extract metadata
    - Split content into chunks
    
    Note:
        This ingestor is designed for PUBLIC repositories only.
        No authentication token is required for public repos.
    
    Attributes:
        repo: GitHub repository in format "owner/repo"
    """
    
    def __init__(self, repo: str = None):
        """
        Initialize the GitHub ingestor.
        
        Args:
            repo: GitHub repository in format "owner/repo"
                  (uses config default if None)
        """
        self.repo = repo or settings.github_repo
        self.github_token = settings.github_token
        self.base_url = "https://api.github.com"
        
        # Set up headers for API requests
        # Token increases rate limit from 60 to 5000 requests/hour
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"
    
    def _make_request(self, endpoint: str) -> Dict[str, Any]:
        """
        Make a request to the GitHub API.
        
        Args:
            endpoint: API endpoint (e.g., "/repos/owner/repo/contents")
        
        Returns:
            JSON response as dictionary
        
        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_repo_info(self) -> Dict[str, Any]:
        """
        Get repository information.
        
        Returns:
            Dictionary with repository metadata
        """
        endpoint = f"/repos/{self.repo}"
        return self._make_request(endpoint)
    
    def get_file_content(self, file_path: str) -> str:
        """
        Get content of a file from the repository.
        
        Args:
            file_path: Path to the file (e.g., "README.md")
        
        Returns:
            File content as string
        """
        endpoint = f"/repos/{self.repo}/contents/{file_path}"
        data = self._make_request(endpoint)
        
        # Content is base64 encoded
        import base64
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content
    
    def list_files(self, path: str = "") -> List[Dict[str, Any]]:
        """
        List all files in a directory.
        
        Args:
            path: Directory path (empty for root)
        
        Returns:
            List of file/directory metadata
        """
        endpoint = f"/repos/{self.repo}/contents/{path}"
        return self._make_request(endpoint)
    
    def get_all_files(
        self,
        path: str = "",
        extensions: Optional[List[str]] = None
    ) -> List[str]:
        """
        Recursively get all file paths in the repository.
        
        Args:
            path: Starting path (empty for root)
            extensions: Filter by file extensions (e.g., [".md", ".py"])
        
        Returns:
            List of file paths
        
        Example:
            >>> files = ingestor.get_all_files(extensions=[".md", ".py", ".js"])
        """
        files = []
        
        try:
            contents = self.list_files(path)
            
            for item in contents:
                if item["type"] == "dir":
                    # Recursively process subdirectories
                    sub_files = self.get_all_files(
                        item["path"],
                        extensions=extensions
                    )
                    files.extend(sub_files)
                else:
                    # Check if file matches extensions
                    if extensions is None:
                        files.append(item["path"])
                    else:
                        file_ext = Path(item["name"]).suffix
                        if file_ext in extensions:
                            files.append(item["path"])
        
        except requests.HTTPError as e:
            logger.warning(f"Could not access path '{path}': {e}")
        
        return files
    
    def extract_metadata(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Extract metadata from file content.
        
        Args:
            file_path: Path to the file
            content: File content
        
        Returns:
            Dictionary with extracted metadata
        """
        metadata = {
            "source": file_path,
            "file_type": Path(file_path).suffix,
            "topic": self._extract_topic(content, file_path),
            "language": self._detect_language(file_path)
        }
        
        return metadata
    
    def _extract_topic(self, content: str, file_path: str) -> str:
        """
        Extract topic from content or filename.
        
        Args:
            content: File content
            file_path: Path to the file
        
        Returns:
            Topic string
        """
        # Try to extract title from markdown
        lines = content.split("\n")
        for line in lines:
            # Check for heading
            if line.startswith("# "):
                return line[2:].strip()
        
        # Fall back to filename
        return Path(file_path).stem.replace("-", " ").replace("_", " ").title()
    
    def _detect_language(self, file_path: str) -> str:
        """
        Detect programming language from file extension.
        
        Args:
            file_path: Path to the file
        
        Returns:
            Language string
        """
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".md": "markdown",
            ".txt": "text"
        }
        
        ext = Path(file_path).suffix
        return ext_map.get(ext, "unknown")
    
    def chunk_content(
        self,
        content: str,
        chunk_size: int = None,
        chunk_overlap: int = None
    ) -> List[Dict[str, Any]]:
        """
        Split content into chunks for vectorization.
        
        This method splits content by:
        1. Markdown headers (##, ###)
        2. Paragraphs
        3. Code blocks
        
        Args:
            content: Text content to chunk
            chunk_size: Maximum chunk size in characters
            chunk_overlap: Overlap between chunks
        
        Returns:
            List of chunk dictionaries with text and metadata
        """
        chunk_size = chunk_size or settings.chunk_size
        chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        chunks = []
        
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r"\n\n+", content)
        
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Check if adding this paragraph exceeds chunk size
            if len(current_chunk) + len(paragraph) + 2 > chunk_size:
                # Save current chunk if not empty
                if current_chunk:
                    chunks.append({"text": current_chunk.strip()})
                
                # Start new chunk with overlap
                if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                    current_chunk = current_chunk[-chunk_overlap:] + "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # Add to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add final chunk
        if current_chunk:
            chunks.append({"text": current_chunk.strip()})
        
        # Add chunk index to metadata
        for i, chunk in enumerate(chunks):
            chunk["index"] = i
        
        return chunks
    
    def fetch_and_chunk_repo(
        self,
        extensions: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch entire repository via ZIP download and return chunked content.
        
        This method downloads the repo as a ZIP archive instead of using
        the GitHub API to avoid rate limiting (60 requests/hour for unauthenticated).
        
        Args:
            extensions: Filter by file extensions
        
        Returns:
            List of all chunks with metadata
        """
        logger.info(f"Fetching repository via ZIP: {self.repo}")
        
        # Default extensions to fetch
        if extensions is None:
            extensions = [".md", ".txt", ".py", ".js", ".ts", ".java"]
        
        all_chunks = []
        
        # Try main branch first, then master
        branches = ["main", "master"]
        
        for branch in branches:
            zip_url = f"https://github.com/{self.repo}/archive/refs/heads/{branch}.zip"
            logger.info(f"Trying branch: {branch}")
            response = requests.get(zip_url, stream=True, timeout=60, allow_redirects=True)
            
            if response.status_code == 200:
                logger.info(f"Successfully downloaded ZIP from {branch} branch")
                break
            else:
                logger.warning(f"Branch {branch} returned status {response.status_code}")
        else:
            raise Exception(f"Could not download repository {self.repo} - no valid branch found")
        
        # Limit download size (50MB max)
        max_size = 50 * 1024 * 1024
        content = b""
        downloaded = 0
        
        for chunk in response.iter_content(chunk_size=8192):
            downloaded += len(chunk)
            if downloaded > max_size:
                raise Exception(f"Repository too large (>50MB). Try a smaller repo.")
            content += chunk
        
        # Process ZIP file in memory
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                logger.info(f"ZIP contains {len(z.infolist())} items")
                
                for file_info in z.infolist():
                    if file_info.is_dir():
                        continue
                    
                    file_path = file_info.filename
                    
                    # Skip files not matching extensions
                    if extensions:
                        file_name = file_path.split("/")[-1] if "/" in file_path else file_path
                        file_ext = Path(file_name).suffix
                        if file_ext not in extensions:
                            continue
                    
                    try:
                        # Skip files larger than 1MB
                        if file_info.file_size > 1024 * 1024:
                            logger.info(f"Skipping large file: {file_path} ({file_info.file_size} bytes)")
                            continue
                        
                        with z.open(file_info) as f:
                            content = f.read().decode('utf-8', errors='ignore')
                        
                        if not content.strip():
                            continue
                        
                        logger.info(f"Processing: {file_path}")
                        
                        metadata = self.extract_metadata(file_path, content)
                        chunks = self.chunk_content(content)
                        
                        for chunk in chunks:
                            chunk.update(metadata)
                        
                        all_chunks.extend(chunks)
                        
                    except Exception as e:
                        logger.warning(f"Skipping {file_path}: {e}")
                        continue
        
        except zipfile.BadZipFile:
            raise Exception(f"Invalid ZIP file for repository {self.repo}")
        
        logger.info(f"Total chunks generated: {len(all_chunks)}")
        return all_chunks


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

github_ingestor = GitHubIngestor()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def ingest_github_repo(
    repo: str = None,
    extensions: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch and chunk a GitHub repository.
    
    Convenience function that uses the singleton github_ingestor.
    
    Args:
        repo: GitHub repository in format "owner/repo"
        extensions: File extensions to include
    
    Returns:
        List of all chunks with metadata
    """
    ingestor = GitHubIngestor(repo=repo)
    return ingestor.fetch_and_chunk_repo(extensions=extensions)
