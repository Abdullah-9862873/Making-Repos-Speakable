from typing import Optional
import logging
import base64
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TTSService:
    
    def __init__(
        self,
        language: str = "en",
        speed: float = 1.0
    ):
        self.language = language
        self.speed = speed
        self.gtts_available = False
        
        try:
            from gtts import gTTS
            self.gtts = gTTS
            self.gtts_available = True
            logger.info("gTTS available for TTS")
        except ImportError:
            logger.warning("gTTS not available. Run: pip install gtts")
            self.gtts = None
    
    def text_to_speech(
        self,
        text: str,
        lang: Optional[str] = None
    ) -> dict:
        lang = lang or self.language
        
        if not self.gtts_available:
            return {
                "status": "error",
                "message": "gTTS not installed. Run: pip install gtts",
                "audio_base64": None
            }
        
        try:
            tts = self.gtts(text=text, lang=lang, slow=(self.speed < 1.0))
            
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            audio_base64 = base64.b64encode(audio_buffer.read()).decode('utf-8')
            
            logger.info(f"Generated TTS audio ({len(audio_base64)} bytes)")
            
            return {
                "status": "success",
                "audio_base64": audio_base64,
                "language": lang,
                "text_length": len(text),
                "message": "Audio generated successfully"
            }
        
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "audio_base64": None
            }
    
    def text_to_speech_file(
        self,
        text: str,
        output_path: str,
        lang: Optional[str] = None
    ) -> dict:
        lang = lang or self.language
        
        if not self.gtts_available:
            return {
                "status": "error",
                "message": "gTTS not installed"
            }
        
        try:
            tts = self.gtts(text=text, lang=lang, slow=(self.speed < 1.0))
            tts.save(output_path)
            
            logger.info(f"Saved TTS audio to {output_path}")
            
            return {
                "status": "success",
                "file_path": output_path,
                "message": f"Audio saved to {output_path}"
            }
        
        except Exception as e:
            logger.error(f"TTS file generation failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def generate_preview(
        self,
        text: str,
        max_chars: int = 500
    ) -> dict:
        preview_text = text[:max_chars]
        if len(text) > max_chars:
            preview_text += "..."
        
        return self.text_to_speech(preview_text)


tts_service = TTSService()


def text_to_speech(
    text: str,
    language: str = "en"
) -> dict:
    tts = TTSService(language=language)
    return tts.text_to_speech(text)


def generate_voice_response(
    answer: str,
    language: str = "en"
) -> dict:
    tts = TTSService(language=language)
    audio_result = tts.text_to_speech(answer)
    
    return {
        "answer": answer,
        "audio": audio_result.get("audio_base64"),
        "audio_status": audio_result.get("status"),
        "language": language
    }
