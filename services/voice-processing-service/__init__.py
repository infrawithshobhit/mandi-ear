"""
MANDI EAR™ Voice Processing Service Package
"""

from .language_detector import LanguageDetector, LanguageCode, LanguageDetectionResult
from .asr_engine import ASREngine, AudioBuffer, AudioFormat, TranscriptionResult
from .tts_engine import TTSEngine, VoiceProfile, VoiceGender, VoiceStyle, TTSResult
from .localization_engine import LocalizationEngine, LocalizationContext, LocalizedValue, CurrencyFormat
from .cultural_context import CulturalContextSystem, CulturalProfile, SocialContext, RegionalContext, CulturalSensitivity
from .context_manager import (
    ConversationContextManager,
    UserContext,
    Interaction,
    InteractionType,
    ConversationSession
)

__version__ = "1.0.0"
__all__ = [
    "LanguageDetector",
    "LanguageCode", 
    "LanguageDetectionResult",
    "ASREngine",
    "AudioBuffer",
    "AudioFormat",
    "TranscriptionResult",
    "TTSEngine",
    "VoiceProfile",
    "VoiceGender",
    "VoiceStyle",
    "TTSResult",
    "LocalizationEngine",
    "LocalizationContext",
    "LocalizedValue",
    "CurrencyFormat",
    "CulturalContextSystem",
    "CulturalProfile",
    "SocialContext",
    "RegionalContext",
    "CulturalSensitivity",
    "ConversationContextManager",
    "UserContext",
    "Interaction",
    "InteractionType",
    "ConversationSession"
]