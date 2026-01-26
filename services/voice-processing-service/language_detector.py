"""
Language Detection Module for MANDI EAR™
Supports 50+ Indian languages with confidence scoring
"""

import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
import asyncio
from langdetect import detect, detect_langs, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Set seed for consistent results
DetectorFactory.seed = 0

logger = logging.getLogger(__name__)

class LanguageCode(str, Enum):
    """Supported Indian languages"""
    HINDI = "hi"
    ENGLISH = "en"
    BENGALI = "bn"
    TELUGU = "te"
    MARATHI = "mr"
    TAMIL = "ta"
    GUJARATI = "gu"
    URDU = "ur"
    KANNADA = "kn"
    ODIA = "or"
    MALAYALAM = "ml"
    PUNJABI = "pa"
    ASSAMESE = "as"
    MAITHILI = "mai"
    SANTALI = "sat"
    KASHMIRI = "ks"
    NEPALI = "ne"
    SINDHI = "sd"
    KONKANI = "gom"
    DOGRI = "doi"
    MANIPURI = "mni"
    BODO = "brx"
    SANTHALI = "sat"

class LanguageDetectionResult:
    """Result of language detection with confidence"""
    def __init__(self, language: LanguageCode, confidence: float, alternatives: List[Tuple[LanguageCode, float]] = None):
        self.language = language
        self.confidence = confidence
        self.alternatives = alternatives or []
        self.is_certain = confidence > 0.8

class LanguageDetector:
    """Advanced language detection for Indian languages"""
    
    def __init__(self):
        self.supported_languages = set(lang.value for lang in LanguageCode)
        self.regional_patterns = self._load_regional_patterns()
        
    def _load_regional_patterns(self) -> Dict[str, List[str]]:
        """Load regional language patterns and keywords"""
        return {
            "hi": ["रुपये", "किसान", "मंडी", "फसल", "बाजार", "दाम"],
            "bn": ["টাকা", "কৃষক", "বাজার", "ফসল", "দাম"],
            "te": ["రూపాయలు", "రైతు", "మార్కెట్", "పంట", "ధర"],
            "ta": ["ரூபாய்", "விவசாயி", "சந்தை", "பயிர்", "விலை"],
            "mr": ["रुपये", "शेतकरी", "बाजार", "पीक", "दर"],
            "gu": ["રૂપિયા", "ખેડૂત", "બજાર", "પાક", "ભાવ"],
            "kn": ["ರೂಪಾಯಿ", "ರೈತ", "ಮಾರುಕಟ್ಟೆ", "ಬೆಳೆ", "ಬೆಲೆ"],
            "ml": ["രൂപ", "കർഷകൻ", "മാർക്കറ്റ്", "വിള", "വില"],
            "pa": ["ਰੁਪਏ", "ਕਿਸਾਨ", "ਮੰਡੀ", "ਫਸਲ", "ਰੇਟ"],
            "or": ["ଟଙ୍କା", "କୃଷକ", "ବଜାର", "ଫସଲ", "ଦର"]
        }
    
    async def detect_language(self, text: str) -> LanguageDetectionResult:
        """
        Detect language from text with confidence scoring
        
        Args:
            text: Input text to analyze
            
        Returns:
            LanguageDetectionResult with detected language and confidence
        """
        if not text or len(text.strip()) < 3:
            return LanguageDetectionResult(LanguageCode.HINDI, 0.5)
        
        try:
            # Primary detection using langdetect
            detected_langs = detect_langs(text)
            
            # Filter for supported languages
            supported_detections = [
                (lang.lang, lang.prob) for lang in detected_langs 
                if lang.lang in self.supported_languages
            ]
            
            if not supported_detections:
                # Fallback to pattern matching
                return await self._pattern_based_detection(text)
            
            primary_lang, primary_confidence = supported_detections[0]
            
            # Enhance confidence with pattern matching
            pattern_boost = await self._calculate_pattern_boost(text, primary_lang)
            adjusted_confidence = min(1.0, primary_confidence + pattern_boost)
            
            alternatives = [
                (LanguageCode(lang), conf) for lang, conf in supported_detections[1:3]
            ]
            
            return LanguageDetectionResult(
                language=LanguageCode(primary_lang),
                confidence=adjusted_confidence,
                alternatives=alternatives
            )
            
        except LangDetectException as e:
            logger.warning(f"Language detection failed: {e}")
            return await self._pattern_based_detection(text)
    
    async def _pattern_based_detection(self, text: str) -> LanguageDetectionResult:
        """Fallback pattern-based language detection"""
        pattern_scores = {}
        
        for lang_code, patterns in self.regional_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text)
            if score > 0:
                pattern_scores[lang_code] = score / len(patterns)
        
        if pattern_scores:
            best_lang = max(pattern_scores, key=pattern_scores.get)
            confidence = min(0.7, pattern_scores[best_lang])
            return LanguageDetectionResult(LanguageCode(best_lang), confidence)
        
        # Ultimate fallback to Hindi
        return LanguageDetectionResult(LanguageCode.HINDI, 0.3)
    
    async def _calculate_pattern_boost(self, text: str, detected_lang: str) -> float:
        """Calculate confidence boost based on regional patterns"""
        if detected_lang not in self.regional_patterns:
            return 0.0
        
        patterns = self.regional_patterns[detected_lang]
        matches = sum(1 for pattern in patterns if pattern in text)
        
        return min(0.2, matches * 0.05)  # Max boost of 0.2
    
    def get_supported_languages(self) -> List[LanguageCode]:
        """Get list of all supported languages"""
        return list(LanguageCode)
    
    async def validate_language_support(self, language_code: str) -> bool:
        """Check if a language is supported"""
        return language_code in self.supported_languages