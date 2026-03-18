from typing import List, Dict, Any, Optional, Union
import logging
from vector_db import vector_db
from embeddings import embedding_model
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGPipeline:
    
    def __init__(
        self,
        top_k: int = None,
        threshold: float = None
    ):
        self.vector_db = vector_db
        self.embeddings = embedding_model
        self.top_k = top_k or settings.top_k_results
        self.threshold = threshold or settings.similarity_threshold
    
    def preprocess_query(self, query: str) -> str:
        query = query.strip()
        query = query.lower()
        return query
    
    def generate_query_embedding(self, query: str) -> List[float]:
        logger.info(f"Generating embedding for query: {query[:50]}...")
        embedding = self.embeddings.encode_single(query)
        return embedding
    
    def search_vector_db(
        self,
        query_embedding: List[float],
        top_k: int = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        top_k = top_k or self.top_k
        
        logger.info(f"Searching Vector DB with top_k={top_k}")
        
        results = self.vector_db.query_vectors(
            query_vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter_dict=filters
        )
        
        return results.get("matches", [])
    
    def filter_by_threshold(
        self,
        results: List[Dict[str, Any]],
        threshold: float = None
    ) -> List[Dict[str, Any]]:
        threshold = threshold or self.threshold
        
        filtered = [
            result for result in results
            if result.get("score", 0) >= threshold
        ]
        
        if len(filtered) == 0 and len(results) > 0:
            filtered = results[:3]
        
        logger.info(f"Filtered {len(results)} results to {len(filtered)} by threshold {threshold}")
        
        return filtered
    
    def extract_contexts(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        contexts = []
        
        for result in results:
            context = {
                "text": result.get("metadata", {}).get("text", ""),
                "source": result.get("metadata", {}).get("source", ""),
                "topic": result.get("metadata", {}).get("topic", ""),
                "file_type": result.get("metadata", {}).get("file_type", ""),
                "language": result.get("metadata", {}).get("language", ""),
                "score": result.get("score", 0)
            }
            contexts.append(context)
        
        return contexts
    
    def assemble_context_text(
        self,
        contexts: List[Dict[str, Any]],
        include_sources: bool = True
    ) -> str:
        if not contexts:
            return ""
        
        context_parts = []
        
        for i, ctx in enumerate(contexts, 1):
            text = ctx.get("text", "")
            context_parts.append(f"[Context {i}]\n{text}")
            
            if include_sources:
                source = ctx.get("source", "")
                if source:
                    context_parts[-1] += f"\nSource: {source}"
        
        return "\n\n".join(context_parts)
    
    def run(
        self,
        query: str,
        top_k: int = None,
        threshold: float = None,
        filters: Optional[Dict[str, Any]] = None,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        logger.info("=" * 50)
        logger.info(f"RAG Pipeline - Query: {query[:50]}...")
        logger.info("=" * 50)
        
        try:
            processed_query = self.preprocess_query(query)
            
            query_embedding = self.generate_query_embedding(processed_query)
            
            search_results = self.search_vector_db(
                query_embedding,
                top_k=top_k,
                filters=filters
            )
            
            filtered_results = self.filter_by_threshold(
                search_results,
                threshold=threshold
            )
            
            contexts = self.extract_contexts(filtered_results)
            
            context_text = self.assemble_context_text(contexts, include_sources)
            
            has_relevant_context = len(contexts) > 0
            
            logger.info(f"RAG Pipeline - Found {len(contexts)} relevant contexts")
            logger.info("=" * 50)
            
            return {
                "query": query,
                "processed_query": processed_query,
                "has_relevant_context": has_relevant_context,
                "contexts": contexts,
                "context_text": context_text,
                "num_results": len(contexts),
                "top_score": contexts[0].get("score", 0) if contexts else 0,
                "status": "success"
            }
        
        except Exception as e:
            logger.error(f"RAG Pipeline failed: {e}")
            return {
                "query": query,
                "has_relevant_context": False,
                "contexts": [],
                "context_text": "",
                "num_results": 0,
                "top_score": 0,
                "status": "error",
                "error": str(e)
            }


def retrieve_context(
    query: str,
    top_k: int = None,
    threshold: float = None
) -> Dict[str, Any]:
    pipeline = RAGPipeline(top_k=top_k, threshold=threshold)
    return pipeline.run(query=query)


def check_context_available() -> bool:
    try:
        stats = vector_db.get_index_stats()
        total_vectors = stats.get("total_vector_count", 0)
        logger.info(f"check_context_available: Found {total_vectors} vectors in index")
        return total_vectors > 0
    except Exception as e:
        logger.error(f"check_context_available failed: {e}")
        return False


def get_context_count() -> int:
    try:
        stats = vector_db.get_index_stats()
        return stats.get("total_vector_count", 0)
    except Exception:
        return 0
