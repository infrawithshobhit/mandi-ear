"""
MANDI EAR™ Voice Processing Service
Multilingual ASR/TTS and NLP processing
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel

from .language_detector import LanguageDetector, LanguageCode, LanguageDetectionResult
from .asr_engine import ASREngine, AudioBuffer, AudioFormat, TranscriptionResult
from .tts_engine import TTSEngine, VoiceProfile, VoiceGender, VoiceStyle, TTSResult
from .localization_engine import LocalizationEngine, LocalizationContext, LocalizedValue, CurrencyFormat
from .cultural_context import CulturalContextSystem, CulturalProfile, SocialContext, RegionalContext, CulturalSensitivity
from .context_manager import (
    ConversationContextManager, 
    UserContext, 
    Interaction, 
    InteractionType
)
from .query_processor import (
    VoiceQueryProcessor,
    QueryType,
    QueryIntent,
    ResponseType,
    QueryAnalysis,
    QueryResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MANDI EAR™ Voice Processing Service",
    description="Multilingual voice processing and NLP",
    version="1.0.0"
)

# Initialize core components
language_detector = LanguageDetector()
asr_engine = ASREngine()
tts_engine = TTSEngine()
localization_engine = LocalizationEngine()
cultural_context_system = CulturalContextSystem()
context_manager = ConversationContextManager()
query_processor = VoiceQueryProcessor()

# Pydantic models for API
class LanguageDetectionRequest(BaseModel):
    text: str

class TranscriptionRequest(BaseModel):
    session_id: Optional[str] = None
    language_hint: Optional[str] = None

class SessionCreateRequest(BaseModel):
    user_id: str
    preferred_language: str = "hi"
    location: Optional[Dict] = None
    farmer_profile: Optional[Dict] = None

class ContextUpdateRequest(BaseModel):
    preferred_language: Optional[str] = None
    location: Optional[Dict] = None
    farmer_profile: Optional[Dict] = None
    cultural_preferences: Optional[Dict] = None

class TTSRequest(BaseModel):
    text: str
    language: str
    voice_gender: Optional[str] = "neutral"
    voice_style: Optional[str] = "friendly"
    speed: Optional[float] = 1.0
    cultural_context: Optional[Dict] = None

class LocalizationRequest(BaseModel):
    text: str
    language: str
    region: Optional[str] = None
    localization_type: str = "currency"  # currency, units, cultural
    value: Optional[float] = None
    unit_type: Optional[str] = None
    unit_name: Optional[str] = None

class VoiceQueryRequest(BaseModel):
    query_text: str
    language: str
    session_id: Optional[str] = None
    user_context: Optional[Dict] = None

class VoiceQueryProcessRequest(BaseModel):
    query_text: str
    language: str
    session_id: str
    generate_audio_response: Optional[bool] = True
    voice_profile: Optional[Dict] = None

@app.get("/")
async def root():
    return {
        "service": "Voice Processing Service",
        "version": "1.0.0",
        "status": "operational",
        "supported_languages": len(language_detector.get_supported_languages()),
        "active_sessions": await context_manager.get_active_sessions_count()
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/detect-language")
async def detect_language(request: LanguageDetectionRequest) -> Dict:
    """Detect language from text input"""
    try:
        result = await language_detector.detect_language(request.text)
        
        return {
            "detected_language": result.language.value,
            "confidence": result.confidence,
            "is_certain": result.is_certain,
            "alternatives": [
                {"language": lang.value, "confidence": conf}
                for lang, conf in result.alternatives
            ]
        }
    except Exception as e:
        logger.error(f"Language detection failed: {e}")
        raise HTTPException(status_code=500, detail="Language detection failed")

@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    session_id: Optional[str] = None,
    language_hint: Optional[str] = None
) -> Dict:
    """Transcribe audio file to text"""
    try:
        # Read audio file
        audio_data = await file.read()
        
        # Create audio buffer
        audio_buffer = AudioBuffer(
            data=audio_data,
            sample_rate=16000,  # Default, will be adjusted in preprocessing
            channels=1,
            format=AudioFormat.WAV,
            duration=0.0  # Will be calculated
        )
        
        # Convert language hint if provided
        language = None
        if language_hint:
            try:
                language = LanguageCode(language_hint)
            except ValueError:
                logger.warning(f"Invalid language hint: {language_hint}")
        
        # Perform transcription
        result = await asr_engine.transcribe_audio(audio_buffer, language)
        
        # Add to conversation context if session provided
        if session_id and result.text:
            interaction = Interaction(
                id=str(uuid.uuid4()),
                type=InteractionType.VOICE_QUERY,
                content=result.text,
                language=result.language,
                timestamp=datetime.now(),
                confidence=result.confidence,
                metadata={
                    "processing_time": result.processing_time,
                    "audio_quality": result.audio_quality
                }
            )
            
            await context_manager.add_interaction(session_id, interaction)
        
        return {
            "text": result.text,
            "confidence": result.confidence,
            "language": result.language.value,
            "processing_time": result.processing_time,
            "audio_quality": result.audio_quality,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Audio transcription failed: {e}")
        raise HTTPException(status_code=500, detail="Audio transcription failed")

@app.post("/sessions")
async def create_session(request: SessionCreateRequest) -> Dict:
    """Create new conversation session"""
    try:
        session_id = str(uuid.uuid4())
        
        # Validate language
        try:
            preferred_language = LanguageCode(request.preferred_language)
        except ValueError:
            preferred_language = LanguageCode.HINDI
        
        # Create user context
        user_context = UserContext(
            user_id=request.user_id,
            preferred_language=preferred_language,
            location=request.location,
            farmer_profile=request.farmer_profile
        )
        
        # Create session
        session = await context_manager.create_session(session_id, user_context)
        
        return {
            "session_id": session.session_id,
            "user_id": session.user_context.user_id,
            "preferred_language": session.user_context.preferred_language.value,
            "created_at": session.created_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Session creation failed: {e}")
        raise HTTPException(status_code=500, detail="Session creation failed")

@app.get("/sessions/{session_id}")
async def get_session(session_id: str) -> Dict:
    """Get session information"""
    session = await context_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.session_id,
        "user_id": session.user_context.user_id,
        "preferred_language": session.user_context.preferred_language.value,
        "created_at": session.created_at.isoformat(),
        "last_activity": session.last_activity.isoformat(),
        "interaction_count": len(session.interactions),
        "is_active": session.is_active
    }

@app.put("/sessions/{session_id}/context")
async def update_session_context(
    session_id: str, 
    request: ContextUpdateRequest
) -> Dict:
    """Update session context"""
    updates = {}
    
    if request.preferred_language:
        updates["preferred_language"] = request.preferred_language
    if request.location:
        updates["location"] = request.location
    if request.farmer_profile:
        updates["farmer_profile"] = request.farmer_profile
    if request.cultural_preferences:
        updates["cultural_preferences"] = request.cultural_preferences
    
    success = await context_manager.update_user_context(session_id, updates)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Context updated successfully"}

@app.get("/sessions/{session_id}/history")
async def get_conversation_history(
    session_id: str, 
    limit: Optional[int] = None
) -> Dict:
    """Get conversation history"""
    interactions = await context_manager.get_conversation_history(session_id, limit)
    
    return {
        "session_id": session_id,
        "interactions": [
            {
                "id": interaction.id,
                "type": interaction.type.value,
                "content": interaction.content,
                "language": interaction.language.value,
                "timestamp": interaction.timestamp.isoformat(),
                "confidence": interaction.confidence,
                "metadata": interaction.metadata
            }
            for interaction in interactions
        ]
    }

@app.get("/sessions/{session_id}/summary")
async def get_context_summary(session_id: str) -> Dict:
    """Get contextual summary of conversation"""
    summary = await context_manager.get_context_summary(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return summary

@app.delete("/sessions/{session_id}")
async def end_session(session_id: str) -> Dict:
    """End conversation session"""
    success = await context_manager.end_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session ended successfully"}

@app.get("/languages")
async def get_supported_languages() -> Dict:
    """Get list of supported languages"""
    return {
        "supported_languages": [
            {
                "code": lang.value,
                "name": lang.name.replace("_", " ").title()
            }
            for lang in language_detector.get_supported_languages()
        ]
    }

@app.get("/stats")
async def get_service_stats() -> Dict:
    """Get service statistics"""
    session_stats = context_manager.get_session_stats()
    
    return {
        "service": "Voice Processing Service",
        "version": "1.0.0",
        "supported_languages": len(language_detector.get_supported_languages()),
        "supported_tts_languages": len(tts_engine.get_supported_languages()),
        "supported_localization_languages": len(localization_engine.get_supported_languages()),
        "session_stats": session_stats
    }

@app.post("/synthesize-speech")
async def synthesize_speech(request: TTSRequest) -> Dict:
    """Convert text to speech with cultural adaptations"""
    try:
        # Validate language
        try:
            language = LanguageCode(request.language)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported language: {request.language}")
        
        # Create voice profile
        try:
            gender = VoiceGender(request.voice_gender)
            style = VoiceStyle(request.voice_style)
        except ValueError:
            gender = VoiceGender.NEUTRAL
            style = VoiceStyle.FRIENDLY
        
        voice_profile = VoiceProfile(
            language=language,
            gender=gender,
            style=style,
            speed=request.speed,
            pitch=1.0,
            volume=1.0
        )
        
        # Synthesize speech
        result = await tts_engine.synthesize_speech(
            text=request.text,
            language=language,
            voice_profile=voice_profile,
            cultural_context=request.cultural_context
        )
        
        # Return audio data as base64 for API response
        import base64
        audio_base64 = base64.b64encode(result.audio_data).decode('utf-8')
        
        return {
            "audio_data": audio_base64,
            "duration": result.duration,
            "language": result.language.value,
            "voice_profile": {
                "gender": result.voice_profile.gender.value,
                "style": result.voice_profile.style.value,
                "speed": result.voice_profile.speed,
                "pitch": result.voice_profile.pitch,
                "volume": result.voice_profile.volume
            },
            "processing_time": result.processing_time,
            "quality_score": result.quality_score
        }
        
    except Exception as e:
        logger.error(f"Speech synthesis failed: {e}")
        raise HTTPException(status_code=500, detail="Speech synthesis failed")

@app.post("/localize")
async def localize_content(request: LocalizationRequest) -> Dict:
    """Localize content based on language and region"""
    try:
        # Validate language
        try:
            language = LanguageCode(request.language)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported language: {request.language}")
        
        # Create localization context
        context = LocalizationContext(
            language=language,
            region=request.region
        )
        
        # Perform localization based on type
        if request.localization_type == "currency" and request.value is not None:
            result = await localization_engine.localize_currency(
                amount=request.value,
                context=context
            )
        elif request.localization_type == "units" and request.value is not None and request.unit_type and request.unit_name:
            result = await localization_engine.localize_units(
                value=request.value,
                unit_type=request.unit_type,
                unit_name=request.unit_name,
                context=context
            )
        elif request.localization_type == "cultural":
            result = await localization_engine.localize_cultural_terms(
                text=request.text,
                context=context
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid localization request parameters")
        
        return {
            "original_value": result.original_value,
            "localized_text": result.localized_text,
            "language": result.language.value,
            "format_type": result.format_type,
            "confidence": result.confidence
        }
        
    except Exception as e:
        logger.error(f"Localization failed: {e}")
        raise HTTPException(status_code=500, detail="Localization failed")

@app.get("/voice-profiles/{language}")
async def get_voice_profiles(language: str) -> Dict:
    """Get available voice profiles for a language"""
    try:
        lang_code = LanguageCode(language)
        profiles = tts_engine.get_available_voices(lang_code)
        
        return {
            "language": language,
            "available_profiles": [
                {
                    "gender": profile.gender.value,
                    "style": profile.style.value,
                    "speed": profile.speed,
                    "pitch": profile.pitch,
                    "volume": profile.volume
                }
                for profile in profiles
            ]
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")
    except Exception as e:
        logger.error(f"Voice profiles retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Voice profiles retrieval failed")

@app.get("/cultural-context/{language}/{region}")
async def get_cultural_context(language: str, region: str) -> Dict:
    """Get cultural context information for language and region"""
    try:
        # Validate inputs
        lang_code = LanguageCode(language)
        region_context = RegionalContext(region)
        
        # Get regional preferences
        regional_prefs = await localization_engine.get_regional_preferences(region)
        
        return {
            "language": language,
            "region": region,
            "regional_preferences": regional_prefs,
            "supported_cultural_features": [
                "currency_localization",
                "unit_conversion",
                "cultural_term_adaptation",
                "respectful_communication",
                "festival_awareness",
                "agricultural_calendar"
            ]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        logger.error(f"Cultural context retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Cultural context retrieval failed")

@app.post("/process-voice-query")
async def process_voice_query(request: VoiceQueryRequest) -> Dict:
    """Process voice query and generate response with 3-second limit"""
    try:
        # Validate language
        try:
            language = LanguageCode(request.language)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported language: {request.language}")
        
        # Create user context if provided
        user_context = None
        if request.user_context:
            user_context = UserContext(
                user_id=request.user_context.get("user_id", "anonymous"),
                preferred_language=language,
                location=request.user_context.get("location"),
                farmer_profile=request.user_context.get("farmer_profile")
            )
        
        # Process query
        response = await query_processor.process_voice_query(
            query_text=request.query_text,
            language=language,
            session_id=request.session_id,
            user_context=user_context
        )
        
        return {
            "response_text": response.response_text,
            "response_type": response.response_type.value,
            "language": response.language.value,
            "confidence": response.confidence,
            "processing_time": response.processing_time,
            "suggested_actions": response.suggested_actions,
            "metadata": response.metadata,
            "within_time_limit": response.processing_time <= 3.0
        }
        
    except Exception as e:
        logger.error(f"Voice query processing failed: {e}")
        raise HTTPException(status_code=500, detail="Voice query processing failed")

@app.post("/process-complete-voice-interaction")
async def process_complete_voice_interaction(request: VoiceQueryProcessRequest) -> Dict:
    """Process complete voice interaction: query processing + audio response generation"""
    try:
        # Validate language
        try:
            language = LanguageCode(request.language)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported language: {request.language}")
        
        # Get session context
        session = await context_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Process text query
        query_response = await query_processor.process_voice_query(
            query_text=request.query_text,
            language=language,
            session_id=request.session_id,
            user_context=session.user_context
        )
        
        response_data = {
            "query_analysis": {
                "response_text": query_response.response_text,
                "response_type": query_response.response_type.value,
                "confidence": query_response.confidence,
                "processing_time": query_response.processing_time,
                "suggested_actions": query_response.suggested_actions,
                "metadata": query_response.metadata
            },
            "session_id": request.session_id,
            "language": language.value,
            "within_time_limit": query_response.processing_time <= 3.0
        }
        
        # Generate audio response if requested
        if request.generate_audio_response and query_response.response_text:
            # Create voice profile
            voice_profile = VoiceProfile(
                language=language,
                gender=VoiceGender.NEUTRAL,
                style=VoiceStyle.FRIENDLY,
                speed=1.0,
                pitch=1.0,
                volume=1.0
            )
            
            # Override with custom voice profile if provided
            if request.voice_profile:
                try:
                    voice_profile.gender = VoiceGender(request.voice_profile.get("gender", "neutral"))
                    voice_profile.style = VoiceStyle(request.voice_profile.get("style", "friendly"))
                    voice_profile.speed = request.voice_profile.get("speed", 1.0)
                    voice_profile.pitch = request.voice_profile.get("pitch", 1.0)
                    voice_profile.volume = request.voice_profile.get("volume", 1.0)
                except ValueError:
                    logger.warning("Invalid voice profile parameters, using defaults")
            
            # Generate audio response
            tts_result = await tts_engine.synthesize_speech(
                text=query_response.response_text,
                language=language,
                voice_profile=voice_profile
            )
            
            # Add audio data to response
            import base64
            response_data["audio_response"] = {
                "audio_data": base64.b64encode(tts_result.audio_data).decode('utf-8'),
                "duration": tts_result.duration,
                "processing_time": tts_result.processing_time,
                "quality_score": tts_result.quality_score,
                "voice_profile": {
                    "gender": tts_result.voice_profile.gender.value,
                    "style": tts_result.voice_profile.style.value,
                    "speed": tts_result.voice_profile.speed,
                    "pitch": tts_result.voice_profile.pitch,
                    "volume": tts_result.voice_profile.volume
                }
            }
            
            # Update total processing time
            total_processing_time = query_response.processing_time + tts_result.processing_time
            response_data["total_processing_time"] = total_processing_time
            response_data["within_time_limit"] = total_processing_time <= 3.0
        
        return response_data
        
    except Exception as e:
        logger.error(f"Complete voice interaction processing failed: {e}")
        raise HTTPException(status_code=500, detail="Complete voice interaction processing failed")

@app.get("/query-types")
async def get_supported_query_types() -> Dict:
    """Get supported query types and intents"""
    return {
        "supported_query_types": query_processor.get_supported_query_types(),
        "supported_languages": query_processor.get_supported_languages(),
        "query_examples": {
            "hindi": [
                "गेहूं का भाव क्या है?",
                "आज मंडी में क्या रेट है?",
                "कौन सी फसल बोनी चाहिए?"
            ],
            "english": [
                "What is the price of wheat?",
                "What are today's mandi rates?",
                "Which crop should I plant?"
            ]
        }
    }

@app.get("/sessions/{session_id}/query-context")
async def get_session_query_context(session_id: str) -> Dict:
    """Get session context summary for query processing"""
    try:
        context_summary = await query_processor.get_session_context_summary(session_id)
        return context_summary
    except Exception as e:
        logger.error(f"Session query context retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Session query context retrieval failed")

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("Voice Processing Service starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Voice Processing Service shutting down...")
    await context_manager.cleanup_all_sessions()