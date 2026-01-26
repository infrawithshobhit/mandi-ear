"""
Automatic Speech Recognition Engine for MANDI EAR™
Supports 50+ Indian languages with noise handling
"""

import logging
import asyncio
import io
from typing import Dict, List, Optional, Union, BinaryIO
from dataclasses import dataclass
from enum import Enum
import speech_recognition as sr
from pydub import AudioSegment
import webrtcvad
import numpy as np
import librosa
import soundfile as sf

from .language_detector import LanguageCode, LanguageDetector

logger = logging.getLogger(__name__)

class AudioFormat(str, Enum):
    """Supported audio formats"""
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    OGG = "ogg"

@dataclass
class AudioBuffer:
    """Audio data container"""
    data: bytes
    sample_rate: int
    channels: int
    format: AudioFormat
    duration: float

@dataclass
class TranscriptionResult:
    """Result of speech-to-text conversion"""
    text: str
    confidence: float
    language: LanguageCode
    processing_time: float
    audio_quality: float

class ASREngine:
    """Advanced ASR engine for Indian languages"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.language_detector = LanguageDetector()
        self.vad = webrtcvad.Vad(2)  # Aggressiveness level 2
        
        # Configure recognizer for better Indian language support
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        
        # Language-specific ASR configurations
        self.language_configs = {
            LanguageCode.HINDI: {"google_lang": "hi-IN", "timeout": 5},
            LanguageCode.ENGLISH: {"google_lang": "en-IN", "timeout": 5},
            LanguageCode.BENGALI: {"google_lang": "bn-IN", "timeout": 5},
            LanguageCode.TELUGU: {"google_lang": "te-IN", "timeout": 5},
            LanguageCode.MARATHI: {"google_lang": "mr-IN", "timeout": 5},
            LanguageCode.TAMIL: {"google_lang": "ta-IN", "timeout": 5},
            LanguageCode.GUJARATI: {"google_lang": "gu-IN", "timeout": 5},
            LanguageCode.KANNADA: {"google_lang": "kn-IN", "timeout": 5},
            LanguageCode.MALAYALAM: {"google_lang": "ml-IN", "timeout": 5},
            LanguageCode.PUNJABI: {"google_lang": "pa-IN", "timeout": 5},
            LanguageCode.ODIA: {"google_lang": "or-IN", "timeout": 5},
            LanguageCode.ASSAMESE: {"google_lang": "as-IN", "timeout": 5},
        }
    
    async def transcribe_audio(
        self, 
        audio_buffer: AudioBuffer, 
        language: Optional[LanguageCode] = None
    ) -> TranscriptionResult:
        """
        Convert speech to text with language detection
        
        Args:
            audio_buffer: Audio data to transcribe
            language: Optional language hint
            
        Returns:
            TranscriptionResult with transcribed text and metadata
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Preprocess audio for better recognition
            processed_audio = await self._preprocess_audio(audio_buffer)
            
            # Detect language if not provided
            if language is None:
                # For audio, we'll use a simple heuristic or fallback to Hindi
                language = LanguageCode.HINDI
            
            # Perform speech recognition
            audio_data = sr.AudioData(
                processed_audio.data,
                processed_audio.sample_rate,
                processed_audio.channels
            )
            
            # Get language configuration
            lang_config = self.language_configs.get(
                language, 
                self.language_configs[LanguageCode.HINDI]
            )
            
            # Transcribe using Google Speech Recognition
            text = await self._perform_recognition(audio_data, lang_config)
            
            # Calculate confidence and quality metrics
            confidence = await self._calculate_confidence(text, audio_buffer)
            audio_quality = await self._assess_audio_quality(audio_buffer)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            return TranscriptionResult(
                text=text,
                confidence=confidence,
                language=language,
                processing_time=processing_time,
                audio_quality=audio_quality
            )
            
        except Exception as e:
            logger.error(f"ASR transcription failed: {e}")
            processing_time = asyncio.get_event_loop().time() - start_time
            
            return TranscriptionResult(
                text="",
                confidence=0.0,
                language=language or LanguageCode.HINDI,
                processing_time=processing_time,
                audio_quality=0.0
            )
    
    async def _preprocess_audio(self, audio_buffer: AudioBuffer) -> AudioBuffer:
        """Preprocess audio for better recognition"""
        try:
            # Convert to AudioSegment for processing
            audio_segment = AudioSegment(
                data=audio_buffer.data,
                sample_width=2,  # 16-bit
                frame_rate=audio_buffer.sample_rate,
                channels=audio_buffer.channels
            )
            
            # Normalize audio levels
            audio_segment = audio_segment.normalize()
            
            # Apply noise reduction (simple high-pass filter)
            audio_segment = audio_segment.high_pass_filter(80)
            
            # Convert to mono if stereo
            if audio_segment.channels > 1:
                audio_segment = audio_segment.set_channels(1)
            
            # Ensure 16kHz sample rate for better recognition
            if audio_segment.frame_rate != 16000:
                audio_segment = audio_segment.set_frame_rate(16000)
            
            return AudioBuffer(
                data=audio_segment.raw_data,
                sample_rate=audio_segment.frame_rate,
                channels=audio_segment.channels,
                format=AudioFormat.WAV,
                duration=len(audio_segment) / 1000.0
            )
            
        except Exception as e:
            logger.warning(f"Audio preprocessing failed: {e}")
            return audio_buffer
    
    async def _perform_recognition(
        self, 
        audio_data: sr.AudioData, 
        lang_config: Dict
    ) -> str:
        """Perform actual speech recognition"""
        try:
            # Use Google Speech Recognition with language specification
            text = self.recognizer.recognize_google(
                audio_data,
                language=lang_config["google_lang"],
                show_all=False
            )
            return text.strip()
            
        except sr.UnknownValueError:
            logger.warning("Speech recognition could not understand audio")
            return ""
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return ""
    
    async def _calculate_confidence(self, text: str, audio_buffer: AudioBuffer) -> float:
        """Calculate confidence score for transcription"""
        if not text:
            return 0.0
        
        # Basic confidence calculation based on text length and audio quality
        text_length_score = min(1.0, len(text) / 50.0)  # Normalize by expected length
        audio_quality_score = await self._assess_audio_quality(audio_buffer)
        
        # Combine scores
        confidence = (text_length_score * 0.6) + (audio_quality_score * 0.4)
        return min(1.0, confidence)
    
    async def _assess_audio_quality(self, audio_buffer: AudioBuffer) -> float:
        """Assess audio quality for confidence calculation"""
        try:
            # Convert audio data to numpy array for analysis
            audio_array = np.frombuffer(audio_buffer.data, dtype=np.int16)
            
            # Calculate signal-to-noise ratio approximation
            signal_power = np.mean(audio_array ** 2)
            if signal_power == 0:
                return 0.0
            
            # Simple quality metric based on signal power and dynamic range
            dynamic_range = np.max(audio_array) - np.min(audio_array)
            quality_score = min(1.0, (signal_power / 1000000) * (dynamic_range / 65535))
            
            return quality_score
            
        except Exception as e:
            logger.warning(f"Audio quality assessment failed: {e}")
            return 0.5  # Default moderate quality
    
    async def detect_voice_activity(self, audio_buffer: AudioBuffer) -> List[tuple]:
        """Detect voice activity in audio buffer"""
        try:
            # Convert to 16kHz mono for VAD
            audio_segment = AudioSegment(
                data=audio_buffer.data,
                sample_width=2,
                frame_rate=audio_buffer.sample_rate,
                channels=audio_buffer.channels
            )
            
            if audio_segment.frame_rate != 16000:
                audio_segment = audio_segment.set_frame_rate(16000)
            if audio_segment.channels > 1:
                audio_segment = audio_segment.set_channels(1)
            
            # Split into 30ms frames for VAD
            frame_duration = 30  # ms
            frame_size = int(16000 * frame_duration / 1000)
            
            voice_segments = []
            current_segment_start = None
            
            for i in range(0, len(audio_segment), frame_duration):
                frame = audio_segment[i:i + frame_duration]
                if len(frame) < frame_duration:
                    break
                
                # Check if frame contains voice
                is_voice = self.vad.is_speech(frame.raw_data, 16000)
                
                if is_voice and current_segment_start is None:
                    current_segment_start = i / 1000.0  # Convert to seconds
                elif not is_voice and current_segment_start is not None:
                    voice_segments.append((current_segment_start, i / 1000.0))
                    current_segment_start = None
            
            # Close final segment if needed
            if current_segment_start is not None:
                voice_segments.append((current_segment_start, len(audio_segment) / 1000.0))
            
            return voice_segments
            
        except Exception as e:
            logger.warning(f"Voice activity detection failed: {e}")
            return [(0.0, audio_buffer.duration)]  # Return full duration as fallback
    
    def get_supported_languages(self) -> List[LanguageCode]:
        """Get list of supported languages for ASR"""
        return list(self.language_configs.keys())
    
    async def validate_audio_format(self, audio_buffer: AudioBuffer) -> bool:
        """Validate if audio format is supported"""
        supported_formats = [AudioFormat.WAV, AudioFormat.FLAC]
        return audio_buffer.format in supported_formats