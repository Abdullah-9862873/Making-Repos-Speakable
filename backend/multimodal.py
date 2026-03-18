from typing import Dict, Any, Optional, List
import re
import logging
from config import settings
from llm_chain import LLMChain

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultimodalGenerator:
    
    def __init__(self):
        self.llm = LLMChain()
    
    def extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        code_blocks = []
        
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for language, code in matches:
            code_blocks.append({
                "language": language or "text",
                "code": code.strip()
            })
        
        return code_blocks
    
    def format_code_response(self, code: str, language: str = "python") -> str:
        return f"```{language}\n{code}\n```"
    
    def generate_diagram_prompt(self, topic: str, context: str = "") -> str:
        prompt = f"""Create a clear diagram description for explaining: {topic}

Context: {context}

Provide:
1. A brief description of what the diagram should show
2. Key elements to include
3. Labels and annotations

Keep it simple and educational."""
        return prompt
    
    def extract_structured_response(self, text: str) -> Dict[str, Any]:
        result = {
            "text": text,
            "has_code": False,
            "code_blocks": [],
            "steps": [],
            "explanation": text
        }
        
        code_blocks = self.extract_code_blocks(text)
        if code_blocks:
            result["has_code"] = True
            result["code_blocks"] = code_blocks
        
        step_pattern = r'(\d+)\.\s+(.+?)(?=\n\d+\.|$)'
        steps = re.findall(step_pattern, text, re.DOTALL)
        if steps:
            result["steps"] = [step[1].strip() for step in steps]
        
        return result
    
    def generate_full_response(
        self,
        question: str,
        answer: str,
        sources: List[str] = None,
        include_diagram: bool = False
    ) -> Dict[str, Any]:
        structured = self.extract_structured_response(answer)
        
        response = {
            "question": question,
            "answer": answer,
            "explanation": structured.get("explanation", ""),
            "has_code": structured.get("has_code", False),
            "code_blocks": structured.get("code_blocks", []),
            "steps": structured.get("steps", []),
            "sources": sources or [],
            "has_diagram": include_diagram,
            "diagram_prompt": None
        }
        
        if include_diagram:
            response["diagram_prompt"] = self.generate_diagram_prompt(
                topic=question,
                context=answer[:500]
            )
        
        return response
    
    def generate_code_focused(
        self,
        question: str,
        context: str = ""
    ) -> Dict[str, Any]:
        result = self.llm.generate_answer(
            question=question,
            context=context,
            has_context=bool(context),
            prompt_type="code"
        )
        
        answer = result.get("answer", "")
        code_blocks = self.extract_code_blocks(answer)
        
        return {
            "question": question,
            "answer": answer,
            "has_code": bool(code_blocks),
            "code_blocks": code_blocks,
            "status": result.get("status", "error")
        }
    
    def generate_step_by_step(
        self,
        question: str,
        context: str = ""
    ) -> Dict[str, Any]:
        result = self.llm.generate_answer(
            question=question,
            context=context,
            has_context=bool(context),
            prompt_type="step_by_step"
        )
        
        answer = result.get("answer", "")
        
        step_pattern = r'(\d+)\.\s+(.+?)(?=\n\d+\.|$)'
        steps = re.findall(step_pattern, answer, re.DOTALL)
        
        return {
            "question": question,
            "answer": answer,
            "steps": [step[1].strip() for step in steps],
            "status": result.get("status", "error")
        }


multimodal_generator = MultimodalGenerator()


def generate_response(
    question: str,
    answer: str,
    sources: List[str] = None
) -> Dict[str, Any]:
    generator = MultimodalGenerator()
    return generator.generate_full_response(question, answer, sources)


def extract_code(text: str) -> List[Dict[str, str]]:
    generator = MultimodalGenerator()
    return generator.extract_code_blocks(text)
