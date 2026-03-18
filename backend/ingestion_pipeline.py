from typing import List, Dict, Any, Optional
import logging
from github_ingest import GitHubIngestor, github_ingestor
from embeddings import EmbeddingModel, embedding_model
from vector_db import VectorDB, vector_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IngestionPipeline:
    
    def __init__(self):
        self.github = github_ingestor
        self.embeddings = embedding_model
        self.vector_db = vector_db
    
    def run(
        self,
        repo: str = None,
        extensions: Optional[List[str]] = None,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        logger.info("=" * 50)
        logger.info("Starting ingestion pipeline")
        logger.info(f"Repository: {repo}")
        logger.info("=" * 50)
        
        try:
            self.github.repo = repo or settings.github_repo
            logger.info(f"IngestionPipeline: Using sanitized repo: {self.github.repo}")
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
            
            logger.info("Step 2: Generating embeddings...")
            texts = [chunk["text"] for chunk in chunks]
            embeddings = self.embeddings.encode_batch(texts)
            logger.info(f"Generated {len(embeddings)} embeddings")
            
            logger.info("Step 3: Preparing vectors for storage...")
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector = {
                    "id": f"chunk_{i}",
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
        logger.info(f"Ingesting single file: {file_path}")
        
        metadata = self.github.extract_metadata(file_path, content)
        chunks = self.github.chunk_content(content)
        
        for chunk in chunks:
            chunk.update(metadata)
        
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embeddings.encode_batch(texts)
        
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
        
        self.vector_db.upsert_vectors(vectors)
        
        return {
            "status": "success",
            "chunks_created": len(chunks),
            "vectors_stored": len(vectors)
        }


ingestion_pipeline = IngestionPipeline()


def run_ingestion(
    repo: str = None,
    extensions: List[str] = None
) -> Dict[str, Any]:
    pipeline = IngestionPipeline()
    return pipeline.run(repo=repo, extensions=extensions)
