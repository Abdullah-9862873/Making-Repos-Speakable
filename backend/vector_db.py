from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any, Optional
import logging
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorDB:
    
    def __init__(self):
        self.pinecone_client = Pinecone(
            api_key=settings.pinecone_api_key
        )
        
        self.index_name = settings.pinecone_index_name
        self.index = None
        
        self._connect_to_index()
    
    def _connect_to_index(self) -> None:
        existing_indexes = self.pinecone_client.list_indexes()
        index_names = [idx.name for idx in existing_indexes]
        
        if self.index_name not in index_names:
            logger.info(f"Index '{self.index_name}' not found. Creating new index...")
            self._create_index()
        else:
            logger.info(f"Connecting to existing index: {self.index_name}")
            self.index = self.pinecone_client.Index(self.index_name)
        
        self._verify_connection()
    
    def _create_index(self, dimension: int = 384) -> None:
        self.pinecone_client.create_index(
            name=self.index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        
        logger.info(f"Index '{self.index_name}' created successfully")
        
        self.index = self.pinecone_client.Index(self.index_name)
    
    def _verify_connection(self) -> bool:
        try:
            stats = self.index.describe_index_stats()
            logger.info(f"Index stats: {stats}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to index: {e}")
            return False
    
    def upsert_vectors(
        self,
        vectors: List[Dict[str, Any]],
        namespace: str = ""
    ) -> Dict[str, Any]:
        try:
            result = self.index.upsert(
                vectors=vectors,
                namespace=namespace
            )
            logger.info(f"Upserted {len(vectors)} vectors")
            return result
        except Exception as e:
            logger.error(f"Failed to upsert vectors: {e}")
            raise
    
    def query_vectors(
        self,
        query_vector: List[float],
        top_k: int = 5,
        include_metadata: bool = True,
        include_values: bool = False,
        namespace: str = "",
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        try:
            result = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=include_metadata,
                include_values=include_values,
                namespace=namespace,
                filter=filter_dict
            )
            return result
        except Exception as e:
            logger.error(f"Failed to query vectors: {e}")
            raise
    
    def delete_vectors(
        self,
        ids: List[str],
        namespace: str = ""
    ) -> Dict[str, Any]:
        try:
            result = self.index.delete(
                ids=ids,
                namespace=namespace
            )
            logger.info(f"Deleted {len(ids)} vectors")
            return result
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            raise
    
    def delete_all_vectors(self, namespace: str = "") -> None:
        try:
            self.index.delete(delete_all=True, namespace=namespace)
            logger.info("All vectors deleted from index")
        except Exception as e:
            logger.error(f"Failed to delete all vectors: {e}")
            raise
    
    def get_index_stats(self) -> Dict[str, Any]:
        try:
            stats = self.index.describe_index_stats()
            return stats.to_dict()
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            raise


vector_db = VectorDB()


def get_relevant_context(
    query_embedding: List[float],
    top_k: int = None,
    threshold: float = None
) -> List[Dict[str, Any]]:
    if top_k is None:
        top_k = settings.top_k_results
    
    if threshold is None:
        threshold = settings.similarity_threshold
    
    results = vector_db.query_vectors(
        query_vector=query_embedding,
        top_k=top_k
    )
    
    relevant_contexts = []
    for match in results.get("matches", []):
        if match["score"] >= threshold:
            relevant_contexts.append({
                "text": match["metadata"].get("text", ""),
                "source": match["metadata"].get("source", ""),
                "topic": match["metadata"].get("topic", ""),
                "score": match["score"]
            })
    
    return relevant_contexts
