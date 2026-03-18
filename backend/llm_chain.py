import requests
import time
from typing import Dict, Any, Optional, List
import logging
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

GROQ_MODELS = {
    "llama-3.1-8b-instant": "Llama 3.1 8B (Fastest, Recommended)",
    "llama-3.2-1b-preview": "Llama 3.2 1B (Very Fast)",
    "llama-3.2-3b-preview": "Llama 3.2 3B (Balanced)",
    "mixtral-8x7b-32768": "Mixtral 8x7B (High Quality)",
}


class LLMChain:
    def __init__(self, model_name: str = None):
        self.api_key = settings.groq_api_key
        self.model_name = model_name or settings.groq_model
        self._test_connection()
    
    def _test_connection(self) -> None:
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                logger.info(f"Connected to Groq API successfully")
            else:
                logger.warning(f"Groq API returned status: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to connect to Groq API: {e}")
    
    def _build_prompt(self, question: str, context: str = "", prompt_type: str = "default") -> str:
        if context:
            prompt = f"""Context from the codebase:
{context}

Question: {question}

Based on the context above, answer the question. If the context contains relevant information, provide a detailed answer citing specific parts. If the context doesn't contain enough information, say so."""
        else:
            prompt = f"""Question: {question}

Answer the question based on your knowledge. Provide a clear and helpful response."""
        
        return prompt
    
    def _call_groq_api(self, prompt: str, max_retries: int = 3) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 512,
            "temperature": 0.7,
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    GROQ_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        generated_text = result["choices"][0]["message"]["content"]
                        return {"status": "success", "data": generated_text}
                    else:
                        return {"status": "success", "data": str(result)}
                
                elif response.status_code == 429:
                    logger.warning("Rate limited by Groq API, waiting 30s...")
                    time.sleep(30)
                    continue
                
                elif response.status_code == 503:
                    logger.warning("Groq API service unavailable, waiting 10s...")
                    time.sleep(10)
                    continue
                
                else:
                    logger.error(f"Groq API error: {response.status_code} - {response.text}")
                    return {
                        "status": "error",
                        "error": f"API error {response.status_code}: {response.text}"
                    }
            
            except requests.exceptions.Timeout:
                logger.warning(f"Request timed out (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                return {"status": "error", "error": "Request timed out"}
            
            except Exception as e:
                logger.error(f"Error calling Groq API: {e}")
                return {"status": "error", "error": str(e)}
        
        return {"status": "error", "error": "Max retries exceeded"}
    
    def generate_answer(
        self,
        question: str,
        context: str = "",
        has_context: bool = True,
        prompt_type: str = "default",
        temperature: float = 0.7,
        max_tokens: int = 512
    ) -> Dict[str, Any]:
        logger.info(f"Generating answer for question: {question[:50]}...")
        prompt = self._build_prompt(question, context, prompt_type)
        result = self._call_groq_api(prompt)
        
        if result["status"] == "success":
            answer_text = str(result["data"])
            logger.info(f"Answer generated successfully ({len(answer_text)} chars)")
            
            return {
                "answer": answer_text.strip(),
                "has_context": has_context,
                "context_used": bool(context),
                "model": self.model_name,
                "status": "success"
            }
        else:
            logger.error(f"Failed to generate answer: {result.get('error', 'Unknown error')}")
            return {
                "answer": f"I apologize, but I encountered an error while generating the answer: {result.get('error', 'Unknown error')}",
                "has_context": has_context,
                "context_used": bool(context),
                "model": self.model_name,
                "status": "error",
                "error": result.get("error", "Unknown error")
            }
    
    def generate_with_rag(
        self,
        question: str,
        top_k: int = None,
        threshold: float = None,
        prompt_type: str = "default"
    ) -> Dict[str, Any]:
        from rag_pipeline import RAGPipeline
        
        rag = RAGPipeline(top_k=top_k, threshold=threshold)
        rag_result = rag.run(query=question)
        
        context = rag_result.get("context_text", "")
        has_relevant_context = rag_result.get("has_relevant_context", False)
        contexts = rag_result.get("contexts", [])
        
        answer_result = self.generate_answer(
            question=question,
            context=context,
            has_context=has_relevant_context,
            prompt_type=prompt_type
        )
        
        sources = list(set([ctx.get("source", "") for ctx in contexts if ctx.get("source")]))
        
        return {
            "question": question,
            "answer": answer_result.get("answer", ""),
            "has_context": has_relevant_context,
            "context_used": bool(context),
            "sources": sources,
            "num_contexts": len(contexts),
            "top_score": rag_result.get("top_score", 0.0),
            "model": self.model_name,
            "status": answer_result.get("status", "error")
        }
    
    def generate_followup(
        self,
        question: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        context_parts = []
        
        if conversation_history:
            for msg in conversation_history[-5:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                context_parts.append(f"{role}: {content}")
        
        context_parts.append(f"user: {question}")
        full_prompt = "\n\n".join(context_parts)
        result = self._call_groq_api(full_prompt)
        
        if result["status"] == "success":
            answer_text = str(result["data"])
            return {
                "answer": answer_text.strip(),
                "status": "success"
            }
        else:
            return {
                "answer": f"Error: {result.get('error', 'Unknown error')}",
                "status": "error"
            }


llm_chain = LLMChain()


def generate_answer(question: str, context: str = "", has_context: bool = True) -> Dict[str, Any]:
    chain = LLMChain()
    return chain.generate_answer(question=question, context=context, has_context=has_context)


def ask_with_rag(question: str, top_k: int = None, threshold: float = None) -> Dict[str, Any]:
    chain = LLMChain()
    return chain.generate_with_rag(question=question, top_k=top_k, threshold=threshold)
