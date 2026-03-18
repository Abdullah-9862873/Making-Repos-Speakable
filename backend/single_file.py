from typing import Dict, Any, Optional
import logging
import os
import re
from embeddings import embedding_model
from vector_db import vector_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SingleFileProcessor:
    
    def __init__(self):
        self.embeddings = embedding_model
        self.vector_db = vector_db
        self.namespace = "single-file"
    
    def process_file(
        self,
        file_content: str,
        file_name: str,
        file_extension: str
    ) -> Dict[str, Any]:
        logger.info(f"Processing single file: {file_name}")
        
        try:
            chunks = self._chunk_content(file_content, file_name)
            
            texts = [chunk["text"] for chunk in chunks]
            embeddings = self.embeddings.encode_batch(texts)
            
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector = {
                    "id": f"single_{file_name}_{i}",
                    "values": embedding,
                    "metadata": {
                        "text": chunk["text"][:5000],
                        "source": file_name,
                        "topic": file_name,
                        "file_type": file_extension,
                        "language": self._detect_language(file_extension),
                        "index": i,
                        "type": "single-file"
                    }
                }
                vectors.append(vector)
            
            self.vector_db.upsert_vectors(vectors, namespace=self.namespace)
            
            logger.info(f"Processed {len(vectors)} chunks from {file_name}")
            
            return {
                "status": "success",
                "file_name": file_name,
                "chunks_created": len(chunks),
                "vectors_stored": len(vectors)
            }
        
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _chunk_content(self, content: str, file_name: str) -> list:
        import re
        
        chunks = []
        chunk_size = 2000
        chunk_overlap = 200
        
        paragraphs = re.split(r"\n\n+", content)
        
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            if len(current_chunk) + len(paragraph) + 2 > chunk_size:
                if current_chunk:
                    chunks.append({"text": current_chunk.strip()})
                
                if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                    current_chunk = current_chunk[-chunk_overlap:] + "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        if current_chunk:
            chunks.append({"text": current_chunk.strip()})
        
        for i, chunk in enumerate(chunks):
            chunk["index"] = i
        
        return chunks
    
    def _detect_language(self, extension: str) -> str:
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
            ".txt": "text",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".xml": "xml",
            ".sql": "sql"
        }
        
        return ext_map.get(extension.lower(), "text")
    
    def query_single_file(
        self,
        question: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        query_embedding = self.embeddings.encode_single(question)
        
        results = self.vector_db.query_vectors(
            query_vector=query_embedding,
            top_k=top_k,
            namespace=self.namespace
        )
        
        contexts = []
        for match in results.get("matches", []):
            contexts.append({
                "text": match["metadata"].get("text", ""),
                "source": match["metadata"].get("source", ""),
                "score": match.get("score", 0)
            })
        
        return {
            "question": question,
            "contexts": contexts,
            "context_text": "\n\n".join([ctx["text"] for ctx in contexts]),
            "has_context": len(contexts) > 0,
            "num_results": len(contexts)
        }
    
    def clear_single_file(self) -> Dict[str, Any]:
        try:
            self.vector_db.delete_all_vectors(namespace=self.namespace)
            return {"status": "success", "message": "Single file content cleared"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


single_file_processor = SingleFileProcessor()


def process_single_file(
    file_content: str,
    file_name: str
) -> Dict[str, Any]:
    import os
    _, ext = os.path.splitext(file_name)
    processor = SingleFileProcessor()
    return processor.process_file(file_content, file_name, ext)


def query_file(question: str, top_k: int = 5) -> Dict[str, Any]:
    processor = SingleFileProcessor()
    return processor.query_single_file(question, top_k)
