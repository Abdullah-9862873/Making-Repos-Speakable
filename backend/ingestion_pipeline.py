# =============================================================================
# AI Multimodal Tutor - Ingestion Pipeline
# =============================================================================
# Phase: 2 - Backend Core Components
# Purpose: Combine GitHub fetch, chunking, embedding, and Vector DB storage
# Version: 2.0.0
# =============================================================================

from typing import List, Dict, Any, Optional
import logging
from github_ingest import GitHubIngestor, github_ingestor
from embeddings import EmbeddingModel, embedding_model
from vector_db import VectorDB, vector_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Complete Ingestion Pipeline.
    
    This class orchestrates the entire ingestion process:
    1. Fetch content from GitHub repository
    2. Chunk content into smaller pieces
    3. Generate embeddings for each chunk
    4. Store in Pinecone Vector DB
    
    Attributes:
        github: GitHubIngestor instance
        embeddings: EmbeddingModel instance
        vector_db: VectorDB instance
    """
    
    def __init__(self):
        """
        Initialize the ingestion pipeline with all components.
        """
        self.github = github_ingestor
        self.embeddings = embedding_model
        self.vector_db = vector_db
    
    def run(
        self,
        repo: str = None,
        extensions: Optional[List[str]] = None,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Run the complete ingestion pipeline.
        
        Args:
            repo: GitHub repository in format "owner/repo"
            extensions: File extensions to include
            batch_size: Number of vectors to upsert at once
        
        Returns:
            Dictionary with ingestion results
        
        Example:
            >>> pipeline = IngestionPipeline()
            >>> result = pipeline.run(
            ...     repo="username/dsa-course",
            ...     extensions=[".md", ".py"]
            ... )
            >>> print(result)
            {
                "status": "success",
                "files_processed": 10,
                "chunks_created": 150,
                "vectors_stored": 150
            }
        """
        logger.info("=" * 50)
        logger.info("Starting ingestion pipeline")
        logger.info(f"Repository: {repo}")
        logger.info("=" * 50)
        
        try:
            # Set repo for github ingestor
            self.github.repo = repo or settings.github_repo
            logger.info(f"Using repo: {self.github.repo}")
            # Step 1: Fetch and chunk repository content
            logger.info("Step 1: Fetching repository content...")
            chunks = self.github.fetch_and_chunk_repo(extensions=extensions)
            logger.info(f"Created {len(chunks)} chunks from repository")
            
            if not chunks:
                return {
                    "status": "warning",
                    "message": "No content found to ingest",
                    "chunks_created": 0,
                    "vectors_stored": 0
                }
            
            # Step 2: Generate embeddings
            logger.info("Step 2: Generating embeddings...")
            texts = [chunk["text"] for chunk in chunks]
            embeddings = self.embeddings.encode_batch(texts)
            logger.info(f"Generated {len(embeddings)} embeddings")
            
            # Step 3: Prepare vectors for Pinecone
            logger.info("Step 3: Preparing vectors for storage...")
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector = {
                    "id": f"chunk_{i}",
                    "values": embedding,
                    "metadata": {
                        "text": chunk["text"][:5000],  # Limit text size for metadata
                        "source": chunk.get("source", ""),
                        "topic": chunk.get("topic", ""),
                        "file_type": chunk.get("file_type", ""),
                        "language": chunk.get("language", ""),
                        "index": chunk.get("index", 0)
                    }
                }
                vectors.append(vector)
            
            # Step 4: Upsert vectors to Pinecone in batches
            logger.info("Step 4: Storing vectors in Pinecone...")
            total_stored = 0
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.vector_db.upsert_vectors(batch)
                total_stored += len(batch)
                logger.info(f"Upserted batch {i//batch_size + 1}: {len(batch)} vectors")
            
            logger.info("=" * 50)
            logger.info("Ingestion pipeline completed successfully!")
            logger.info("=" * 50)
            
            return {
                "status": "success",
                "chunks_created": len(chunks),
                "vectors_stored": total_stored,
                "dimension": self.embeddings.get_dimension()
            }
        
        except Exception as e:
            logger.error(f"Ingestion pipeline failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "chunks_created": 0,
                "vectors_stored": 0
            }
    
    def run_single_file(
        self,
        file_path: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Ingest a single file's content.
        
        Args:
            file_path: Path to the file
            content: Content of the file
        
        Returns:
            Dictionary with ingestion results
        """
        logger.info(f"Ingesting single file: {file_path}")
        
        # Extract metadata
        metadata = self.github.extract_metadata(file_path, content)
        
        # Chunk content
        chunks = self.github.chunk_content(content)
        
        # Add metadata to each chunk
        for chunk in chunks:
            chunk.update(metadata)
        
        # Generate embeddings
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embeddings.encode_batch(texts)
        
        # Prepare vectors
        vectors = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector = {
                "id": f"{file_path}_{i}",
                "values": embedding,
                "metadata": {
                    "text": chunk["text"][:5000],
                    "source": chunk.get("source", ""),
                    "topic": chunk.get("topic", ""),
                    "file_type": chunk.get("file_type", ""),
                    "language": chunk.get("language", ""),
                    "index": chunk.get("index", 0)
                }
            }
            vectors.append(vector)
        
        # Upsert to Pinecone
        self.vector_db.upsert_vectors(vectors)
        
        return {
            "status": "success",
            "chunks_created": len(chunks),
            "vectors_stored": len(vectors)
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

ingestion_pipeline = IngestionPipeline()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def run_ingestion(
    repo: str = None,
    extensions: List[str] = None
) -> Dict[str, Any]:
    """
    Run the complete ingestion pipeline.
    
    Convenience function.
    
    Args:
        repo: GitHub repository
        extensions: File extensions to include
    
    Returns:
        Dictionary with ingestion results
    """
    pipeline = IngestionPipeline()
    return pipeline.run(repo=repo, extensions=extensions)
