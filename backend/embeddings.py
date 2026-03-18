from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
import logging
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingModel:
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.embedding_model
        self.model = None
        self.dimension = None
        
        self._load_model()
    
    def _load_model(self) -> None:
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded successfully. Dimension: {self.dimension}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )
            return embeddings
        except Exception as e:
            logger.error(f"Failed to encode texts: {e}")
            raise
    
    def encode_single(self, text: str) -> List[float]:
        embedding = self.encode(texts=[text])
        return embedding[0].tolist()
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.encode(texts=texts, show_progress=True)
        return embeddings.tolist()
    
    def get_dimension(self) -> int:
        return self.dimension
    
    def get_model_name(self) -> str:
        return self.model_name


embedding_model = EmbeddingModel()


def get_embedding(text: str) -> List[float]:
    return embedding_model.encode_single(text)


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    return embedding_model.encode_batch(texts)
