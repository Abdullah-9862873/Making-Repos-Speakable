from typing import Dict, Any, Optional


class PromptTemplates:
    
    SYSTEM_PROMPT = """You are an expert programming tutor specializing in teaching 
students through their specific course materials. You provide clear, step-by-step 
explanations with code examples drawn directly from the student's course content.

Your teaching style:
- Clear and concise explanations
- Use code examples from the course material
- Break down complex concepts into steps
- Provide practical, actionable guidance
- When possible, reference specific parts of the course"""

    SYSTEM_PROMPT_NO_CONTEXT = """You are an expert programming tutor. You provide clear, 
step-by-step explanations with code examples. Since the specific course material 
is not available, provide general but accurate programming knowledge.

Your teaching style:
- Clear and concise explanations
- Use common code examples
- Break down complex concepts into steps
- Provide practical, actionable guidance"""
    
    USER_PROMPT_WITH_CONTEXT = """Question: {question}

Course Context:
{context}

Instructions:
1. Use the course context above to answer the question
2. If the context doesn't fully answer the question, supplement with your knowledge
3. Provide code examples when relevant
4. Reference the source material when possible

Answer:"""

    USER_PROMPT_CODE_FOCUS = """Question: {question}

Course Context:
{context}

Instructions:
1. Focus on providing code examples from the course material
2. Explain the code line by line
3. If the context has related code, highlight it
4. Provide additional code if needed for clarity

Answer with code examples:"""

    USER_PROMPT_STEP_BY_STEP = """Question: {question}

Course Context:
{context}

Instructions:
1. Break down the answer into clear steps
2. Use the course material as the primary source
3. Provide code examples for each step
4. Keep explanations beginner-friendly

Step-by-step answer:"""
    
    USER_PROMPT_FALLBACK = """Question: {question}

Note: The specific course material is not available in our knowledge base. 
I'll provide a general answer based on established programming knowledge.

Instructions:
1. Provide a clear, accurate explanation
2. Use common code examples
3. Break down complex concepts into steps

Answer:"""
    
    RESPONSE_FORMAT_JSON = """Provide your answer in the following JSON format:
{{
    "answer": "Your explanation here",
    "code_example": "Optional code snippet",
    "steps": ["Step 1", "Step 2", "Step 3"],
    "sources": ["source1.md", "source2.md"]
}}"""

    RESPONSE_FORMAT_MARKDOWN = """Use markdown formatting for your response:
- Use ## for main sections
- Use ```language for code blocks
- Use bullet points for lists
- Use **bold** for emphasis"""
    
    @staticmethod
    def get_system_prompt(has_context: bool) -> str:
        return (
            PromptTemplates.SYSTEM_PROMPT 
            if has_context 
            else PromptTemplates.SYSTEM_PROMPT_NO_CONTEXT
        )
    
    @staticmethod
    def get_user_prompt(
        question: str,
        context: str,
        prompt_type: str = "default",
        has_context: bool = True
    ) -> str:
        if not has_context:
            return PromptTemplates.USER_PROMPT_FALLBACK.format(
                question=question
            )
        
        if context:
            context_section = context
        else:
            context_section = "No specific context available."
        
        prompt_map = {
            "default": PromptTemplates.USER_PROMPT_WITH_CONTEXT,
            "code": PromptTemplates.USER_PROMPT_CODE_FOCUS,
            "step_by_step": PromptTemplates.USER_PROMPT_STEP_BY_STEP
        }
        
        template = prompt_map.get(prompt_type, prompt_map["default"])
        
        return template.format(
            question=question,
            context=context_section
        )
    
    @staticmethod
    def format_response(
        answer: str,
        sources: Optional[list] = None,
        code_example: Optional[str] = None
    ) -> Dict[str, Any]:
        response = {
            "answer": answer,
            "has_code": code_example is not None,
            "code_example": code_example,
            "sources": sources or []
        }
        
        return response


class PromptBuilder:
    
    def __init__(self):
        self.system_prompt = ""
        self.user_prompt = ""
        self.context = ""
        self.question = ""
        self.prompt_type = "default"
        self.has_context = True
    
    def set_question(self, question: str) -> 'PromptBuilder':
        self.question = question
        return self
    
    def set_context(self, context: str) -> 'PromptBuilder':
        self.context = context
        self.has_context = bool(context)
        return self
    
    def set_prompt_type(self, prompt_type: str) -> 'PromptBuilder':
        self.prompt_type = prompt_type
        return self
    
    def build(self) -> Dict[str, str]:
        self.system_prompt = PromptTemplates.get_system_prompt(self.has_context)
        
        self.user_prompt = PromptTemplates.get_user_prompt(
            question=self.question,
            context=self.context,
            prompt_type=self.prompt_type,
            has_context=self.has_context
        )
        
        return {
            "system": self.system_prompt,
            "user": self.user_prompt
        }


def build_prompt(
    question: str,
    context: str = "",
    prompt_type: str = "default"
) -> Dict[str, str]:
    builder = PromptBuilder()
    builder.set_question(question)
    builder.set_context(context)
    builder.set_prompt_type(prompt_type)
    
    return builder.build()


def format_sources(sources: list) -> str:
    if not sources:
        return ""
    
    unique_sources = list(set(sources))
    
    return "Sources: " + ", ".join(unique_sources)
