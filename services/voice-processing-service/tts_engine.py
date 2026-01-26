"""
Text-to-Speech Engine for MANDI EAR™
Supports regional Indian languages with cultural context
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import io

from .language_detector import LanguageCode

logger = logging.getLogger(__name__)

class VoiceGender(str, Enum):
    """Voice gender options"""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"

class VoiceStyle(str, Enum):
    """Voice style options"""
    FORMAL = "formal"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"

@dataclass
class VoiceProfile:
    """Voice profile configuration"""
    language: LanguageCode
    gender: VoiceGender
    style: VoiceStyle
    speed: float = 1.0  # 0.5 to 2.0
    pitch: float = 1.0  # 0.5 to 2.0
    volume: float = 1.0  # 0.0 to 1.0

@dataclass
class TTSResult:
    """Result of text-to-speech conversion"""
    audio_data: bytes
    duration: float
    language: LanguageCode
    voice_profile: VoiceProfile
    processing_time: float
    quality_score: float

class TTSEngine:
    """Advanced TTS engine for Indian languages"""
    
    def __init__(self):
        self.supported_voices = self._initialize_voice_profiles()
        self.cultural_adaptations = self._load_cultural_adaptations()
        
    def _initialize_voice_profiles(self) -> Dict[LanguageCode, List[VoiceProfile]]:
        """Initialize available voice profiles for each language"""
        voices = {}
        
        # Define voice profiles for major Indian languages
        language_configs = [
            (LanguageCode.HINDI, "Hindi"),
            (LanguageCode.ENGLISH, "English (Indian)"),
            (LanguageCode.BENGALI, "Bengali"),
            (LanguageCode.TELUGU, "Telugu"),
            (LanguageCode.MARATHI, "Marathi"),
            (LanguageCode.TAMIL, "Tamil"),
            (LanguageCode.GUJARATI, "Gujarati"),
            (LanguageCode.KANNADA, "Kannada"),
            (LanguageCode.MALAYALAM, "Malayalam"),
            (LanguageCode.PUNJABI, "Punjabi"),
            (LanguageCode.ODIA, "Odia"),
        ]
        
        for lang_code, lang_name in language_configs:
            voices[lang_code] = [
                VoiceProfile(
                    language=lang_code,
                    gender=VoiceGender.MALE,
                    style=VoiceStyle.FORMAL,
                    speed=1.0,
                    pitch=1.0,
                    volume=1.0
                ),
                VoiceProfile(
                    language=lang_code,
                    gender=VoiceGender.FEMALE,
                    style=VoiceStyle.FRIENDLY,
                    speed=1.0,
                    pitch=1.1,
                    volume=1.0
                ),
                VoiceProfile(
                    language=lang_code,
                    gender=VoiceGender.MALE,
                    style=VoiceStyle.CASUAL,
                    speed=1.1,
                    pitch=0.9,
                    volume=1.0
                )
            ]
        
        return voices
    
    def _load_cultural_adaptations(self) -> Dict[LanguageCode, Dict[str, Any]]:
        """Load cultural adaptations for different languages"""
        return {
            LanguageCode.HINDI: {
                "honorifics": ["जी", "साहब", "मैडम", "भाई साहब"],
                "greetings": ["नमस्ते", "नमस्कार", "आदाब"],
                "respectful_terms": ["आप", "आपका", "आपकी"],
                "pause_after_honorifics": 0.3,
                "emphasis_words": ["महत्वपूर्ण", "जरूरी", "ध्यान"]
            },
            LanguageCode.ENGLISH: {
                "honorifics": ["sir", "madam", "ji"],
                "greetings": ["hello", "good morning", "good evening", "namaste"],
                "respectful_terms": ["you", "your", "please"],
                "pause_after_honorifics": 0.2,
                "emphasis_words": ["important", "urgent", "attention"]
            },
            LanguageCode.BENGALI: {
                "honorifics": ["দাদা", "দিদি", "বাবু", "মশাই"],
                "greetings": ["নমস্কার", "আদাব", "প্রণাম"],
                "respectful_terms": ["আপনি", "আপনার"],
                "pause_after_honorifics": 0.3,
                "emphasis_words": ["গুরুত্বপূর্ণ", "জরুরি", "মনোযোগ"]
            },
            LanguageCode.TELUGU: {
                "honorifics": ["గారు", "అన్న", "అక్క"],
                "greetings": ["నమస్కారం", "వందనాలు"],
                "respectful_terms": ["మీరు", "మీ", "దయచేసి"],
                "pause_after_honorifics": 0.3,
                "emphasis_words": ["ముఖ్యమైన", "అత్యవసరం", "దృష్టి"]
            },
            LanguageCode.TAMIL: {
                "honorifics": ["ஐயா", "அம்மா", "அண்ணா", "அக்கா"],
                "greetings": ["வணக்கம்", "நமஸ்காரம்"],
                "respectful_terms": ["நீங்கள்", "உங்கள்", "தயவுசெய்து"],
                "pause_after_honorifics": 0.3,
                "emphasis_words": ["முக்கியமான", "அவசரம்", "கவனம்"]
            }
        }
    
    async def synthesize_speech(
        self,
        text: str,
        language: LanguageCode,
        voice_profile: Optional[VoiceProfile] = None,
        cultural_context: Optional[Dict[str, Any]] = None
    ) -> TTSResult:
        """
        Convert text to speech with cultural adaptations
        
        Args:
            text: Text to convert to speech
            language: Target language
            voice_profile: Optional voice configuration
            cultural_context: Optional cultural context for adaptation
            
        Returns:
            TTSResult with audio data and metadata
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Select voice profile
            if voice_profile is None:
                voice_profile = await self._select_default_voice(language, cultural_context)
            
            # Apply cultural adaptations
            adapted_text = await self._apply_cultural_adaptations(
                text, language, cultural_context
            )
            
            # Generate speech audio
            audio_data = await self._generate_audio(adapted_text, voice_profile)
            
            # Calculate metrics
            processing_time = asyncio.get_event_loop().time() - start_time
            duration = await self._calculate_audio_duration(audio_data)
            quality_score = await self._assess_audio_quality(audio_data, adapted_text)
            
            return TTSResult(
                audio_data=audio_data,
                duration=duration,
                language=language,
                voice_profile=voice_profile,
                processing_time=processing_time,
                quality_score=quality_score
            )
            
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            processing_time = asyncio.get_event_loop().time() - start_time
            
            # Return empty result on failure
            return TTSResult(
                audio_data=b"",
                duration=0.0,
                language=language,
                voice_profile=voice_profile or VoiceProfile(
                    language=language,
                    gender=VoiceGender.NEUTRAL,
                    style=VoiceStyle.FORMAL
                ),
                processing_time=processing_time,
                quality_score=0.0
            )
    
    async def _select_default_voice(
        self,
        language: LanguageCode,
        cultural_context: Optional[Dict[str, Any]] = None
    ) -> VoiceProfile:
        """Select appropriate default voice based on context"""
        available_voices = self.supported_voices.get(language, [])
        
        if not available_voices:
            # Fallback to Hindi if language not supported
            available_voices = self.supported_voices.get(LanguageCode.HINDI, [])
            if not available_voices:
                # Ultimate fallback
                return VoiceProfile(
                    language=LanguageCode.HINDI,
                    gender=VoiceGender.NEUTRAL,
                    style=VoiceStyle.FORMAL
                )
        
        # Select based on cultural context
        if cultural_context:
            # Prefer formal voice for business contexts
            if cultural_context.get("context_type") == "business":
                formal_voices = [v for v in available_voices if v.style == VoiceStyle.FORMAL]
                if formal_voices:
                    return formal_voices[0]
            
            # Prefer friendly voice for casual contexts
            elif cultural_context.get("context_type") == "casual":
                friendly_voices = [v for v in available_voices if v.style == VoiceStyle.FRIENDLY]
                if friendly_voices:
                    return friendly_voices[0]
        
        # Default to first available voice
        return available_voices[0]
    
    async def _apply_cultural_adaptations(
        self,
        text: str,
        language: LanguageCode,
        cultural_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Apply cultural adaptations to text"""
        adaptations = self.cultural_adaptations.get(language, {})
        if not adaptations:
            return text
        
        adapted_text = text
        
        # Add pauses after honorifics
        honorifics = adaptations.get("honorifics", [])
        for honorific in honorifics:
            if honorific in adapted_text:
                # Add SSML pause markup (simplified representation)
                adapted_text = adapted_text.replace(
                    honorific,
                    f"{honorific}<pause:{adaptations.get('pause_after_honorifics', 0.2)}s>"
                )
        
        # Emphasize important words
        emphasis_words = adaptations.get("emphasis_words", [])
        for word in emphasis_words:
            if word in adapted_text:
                adapted_text = adapted_text.replace(
                    word,
                    f"<emphasis>{word}</emphasis>"
                )
        
        # Add cultural greetings if context suggests
        if cultural_context and cultural_context.get("add_greeting"):
            greetings = adaptations.get("greetings", [])
            if greetings:
                greeting = greetings[0]  # Use first greeting
                adapted_text = f"{greeting}. {adapted_text}"
        
        return adapted_text
    
    async def _generate_audio(self, text: str, voice_profile: VoiceProfile) -> bytes:
        """Generate audio from text using voice profile"""
        # This is a simplified implementation
        # In a real system, this would interface with actual TTS engines
        # like Google Cloud TTS, Azure Cognitive Services, or local engines
        
        try:
            # Simulate audio generation
            # In reality, this would call external TTS APIs or local engines
            
            # Calculate approximate audio length based on text
            words = len(text.split())
            estimated_duration = words * 0.5  # ~0.5 seconds per word
            
            # Generate placeholder audio data (silence)
            sample_rate = 22050
            samples = int(estimated_duration * sample_rate)
            
            # Create simple audio header (WAV format)
            import struct
            
            # WAV header
            header = struct.pack('<4sI4s4sIHHIIHH4sI',
                               b'RIFF',
                               36 + samples * 2,
                               b'WAVE',
                               b'fmt ',
                               16,  # PCM format chunk size
                               1,   # PCM format
                               1,   # Mono
                               sample_rate,
                               sample_rate * 2,  # Byte rate
                               2,   # Block align
                               16,  # Bits per sample
                               b'data',
                               samples * 2)
            
            # Generate simple tone based on voice characteristics
            import math
            base_freq = 200 if voice_profile.gender == VoiceGender.MALE else 300
            base_freq *= voice_profile.pitch
            
            audio_samples = []
            for i in range(samples):
                # Generate simple sine wave with some variation
                t = i / sample_rate
                amplitude = int(16000 * voice_profile.volume * 0.1)  # Low volume
                sample = int(amplitude * math.sin(2 * math.pi * base_freq * t))
                audio_samples.append(sample)
            
            # Pack audio data
            audio_data = struct.pack('<' + 'h' * len(audio_samples), *audio_samples)
            
            return header + audio_data
            
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            # Return minimal WAV file with silence
            return b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
    
    async def _calculate_audio_duration(self, audio_data: bytes) -> float:
        """Calculate duration of audio data"""
        if len(audio_data) < 44:  # Minimum WAV header size
            return 0.0
        
        try:
            # Extract sample rate and data size from WAV header
            import struct
            
            # Read WAV header
            sample_rate = struct.unpack('<I', audio_data[24:28])[0]
            data_size = struct.unpack('<I', audio_data[40:44])[0]
            
            # Calculate duration
            bytes_per_sample = 2  # 16-bit audio
            duration = data_size / (sample_rate * bytes_per_sample)
            
            return duration
            
        except Exception as e:
            logger.warning(f"Duration calculation failed: {e}")
            return 0.0
    
    async def _assess_audio_quality(self, audio_data: bytes, text: str) -> float:
        """Assess quality of generated audio"""
        try:
            # Simple quality assessment based on data size and text length
            if len(audio_data) < 44:
                return 0.0
            
            words = len(text.split())
            if words == 0:
                return 0.0
            
            # Quality based on audio data size relative to text length
            data_per_word = len(audio_data) / words
            
            # Normalize quality score (arbitrary thresholds)
            if data_per_word > 1000:
                return min(1.0, data_per_word / 5000)
            else:
                return data_per_word / 1000
                
        except Exception as e:
            logger.warning(f"Quality assessment failed: {e}")
            return 0.5  # Default moderate quality
    
    def get_supported_languages(self) -> List[LanguageCode]:
        """Get list of supported languages"""
        return list(self.supported_voices.keys())
    
    def get_available_voices(self, language: LanguageCode) -> List[VoiceProfile]:
        """Get available voice profiles for a language"""
        return self.supported_voices.get(language, [])
    
    async def validate_voice_profile(self, voice_profile: VoiceProfile) -> bool:
        """Validate if voice profile is supported"""
        available_voices = self.get_available_voices(voice_profile.language)
        
        # Check if similar voice profile exists
        for voice in available_voices:
            if (voice.language == voice_profile.language and
                voice.gender == voice_profile.gender and
                voice.style == voice_profile.style):
                return True
        
        return False
    
    async def customize_voice_profile(
        self,
        base_profile: VoiceProfile,
        speed: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None
    ) -> VoiceProfile:
        """Customize voice profile parameters"""
        customized = VoiceProfile(
            language=base_profile.language,
            gender=base_profile.gender,
            style=base_profile.style,
            speed=speed if speed is not None else base_profile.speed,
            pitch=pitch if pitch is not None else base_profile.pitch,
            volume=volume if volume is not None else base_profile.volume
        )
        
        # Validate parameter ranges
        customized.speed = max(0.5, min(2.0, customized.speed))
        customized.pitch = max(0.5, min(2.0, customized.pitch))
        customized.volume = max(0.0, min(1.0, customized.volume))
        
        return customized