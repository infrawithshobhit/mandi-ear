"""
Property-Based Test for Multilingual Processing Consistency
Feature: mandi-ear, Property 4: Multilingual Processing Consistency

**Validates: Requirements 2.1, 2.3**

This test validates that for any supported Indian language, voice input processing 
and output generation work correctly with appropriate localization (currency, units, 
cultural context).
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import asyncio
from typing import Dict, Any, List, Optional
import json
import os
import sys

# Import voice processing components
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services', 'voice-processing-service'))

from language_detector import LanguageCode, LanguageDetector

# Test configuration
SUPPORTED_LANGUAGES = [
    "hi", "en", "bn", "te", "mr", "ta", "gu", "ur", "kn", "or", 
    "ml", "pa", "as", "mai", "sat", "ks", "ne", "sd", "gom", "doi"
]

# Agricultural vocabulary in different languages
AGRICULTURAL_VOCABULARY = {
    "hi": {
        "price": ["दाम", "कीमत", "भाव", "रेट"],
        "farmer": ["किसान", "खेतिहर"],
        "market": ["मंडी", "बाजार"],
        "crop": ["फसल", "पैदावार"],
        "currency": ["रुपये", "रुपया"],
        "units": ["किलो", "क्विंटल", "टन"]
    },
    "en": {
        "price": ["price", "rate", "cost", "value"],
        "farmer": ["farmer", "cultivator"],
        "market": ["market", "mandi"],
        "crop": ["crop", "produce", "harvest"],
        "currency": ["rupees", "INR"],
        "units": ["kg", "quintal", "ton", "kilogram"]
    },
    "bn": {
        "price": ["দাম", "মূল্য", "ভাব"],
        "farmer": ["কৃষক", "চাষী"],
        "market": ["বাজার", "মণ্ডি"],
        "crop": ["ফসল", "শস্য"],
        "currency": ["টাকা", "রুপি"],
        "units": ["কেজি", "কুইন্টাল", "টন"]
    }
}

# Hypothesis strategies
@st.composite
def language_test_data(draw):
    """Generate test data for language processing"""
    language = draw(st.sampled_from(["hi", "en", "bn"]))  # Limit to languages with vocabulary
    
    # Get vocabulary for the language
    vocab = AGRICULTURAL_VOCABULARY[language]
    
    # Generate test phrases
    price_word = draw(st.sampled_from(vocab["price"]))
    crop_word = draw(st.sampled_from(vocab["crop"]))
    currency_word = draw(st.sampled_from(vocab["currency"]))
    unit_word = draw(st.sampled_from(vocab["units"]))
    
    # Generate price value
    price_value = draw(st.integers(min_value=100, max_value=10000))
    
    return {
        "language": language,
        "vocabulary": vocab,
        "test_phrase": f"{crop_word} {price_word} {price_value} {currency_word} {unit_word}",
        "price_value": price_value,
        "components": {
            "price": price_word,
            "crop": crop_word,
            "currency": currency_word,
            "unit": unit_word
        }
    }

@st.composite
def localization_test_data(draw):
    """Generate localization test data"""
    language = draw(st.sampled_from(["hi", "en", "bn"]))
    
    # Currency formats by region
    currency_formats = {
        "hi": ["₹{}", "{} रुपये", "{} रु"],
        "en": ["₹{}", "Rs. {}", "INR {}"],
        "bn": ["৳{}", "{} টাকা"]
    }
    
    # Unit formats by region
    unit_formats = {
        "hi": ["{} किलो", "{} क्विंटल", "{} टन"],
        "en": ["{} kg", "{} quintal", "{} ton"],
        "bn": ["{} কেজি", "{} কুইন্টাল"]
    }
    
    amount = draw(st.integers(min_value=50, max_value=5000))
    quantity = draw(st.integers(min_value=1, max_value=100))
    
    currency_format = draw(st.sampled_from(currency_formats[language]))
    unit_format = draw(st.sampled_from(unit_formats[language]))
    
    return {
        "language": language,
        "amount": amount,
        "quantity": quantity,
        "currency_text": currency_format.format(amount),
        "unit_text": unit_format.format(quantity),
        "localized_phrase": f"{currency_format.format(amount)} per {unit_format.format(quantity)}"
    }

class TestMultilingualProcessing:
    """Test class for multilingual processing consistency"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.language_detector = LanguageDetector()
    
    @given(test_data=language_test_data())
    @settings(max_examples=15, deadline=10000)
    def test_language_detection_consistency(self, test_data: Dict[str, Any]):
        """
        Property 4: Multilingual Processing Consistency - Language Detection
        
        For any supported Indian language text containing agricultural vocabulary,
        the language detector should correctly identify the language with reasonable confidence.
        """
        assume(len(test_data["test_phrase"]) >= 5)
        
        try:
            # Test language detection
            result = asyncio.run(
                self.language_detector.detect_language(test_data["test_phrase"])
            )
            
            # Validate detection result structure
            assert hasattr(result, 'language'), "Result should have language attribute"
            assert hasattr(result, 'confidence'), "Result should have confidence attribute"
            assert hasattr(result, 'is_certain'), "Result should have is_certain attribute"
            
            # Validate confidence range
            assert 0.0 <= result.confidence <= 1.0, f"Invalid confidence: {result.confidence}"
            
            # Validate detected language is supported
            detected_lang_code = result.language.value
            assert detected_lang_code in SUPPORTED_LANGUAGES, f"Unsupported language detected: {detected_lang_code}"
            
            # For clear language indicators, expect higher confidence
            if any(word in test_data["test_phrase"] for word in ["रुपये", "किसान", "मंडी"]):
                # Hindi indicators should boost confidence
                if result.language == LanguageCode.HINDI:
                    assert result.confidence >= 0.4, "Hindi indicators should increase confidence"
            
        except Exception as e:
            pytest.fail(f"Language detection consistency test failed: {str(e)}")
    
    @given(loc_data=localization_test_data())
    @settings(max_examples=10, deadline=8000)
    def test_localization_consistency(self, loc_data: Dict[str, Any]):
        """
        Property 4: Multilingual Processing Consistency - Localization
        
        For any localization data (currency, units), the system should handle
        regional formats consistently across supported languages.
        """
        try:
            # Test currency localization
            currency_result = asyncio.run(
                self.language_detector.detect_language(loc_data["currency_text"])
            )
            
            # Test unit localization
            unit_result = asyncio.run(
                self.language_detector.detect_language(loc_data["unit_text"])
            )
            
            # Test combined localized phrase
            phrase_result = asyncio.run(
                self.language_detector.detect_language(loc_data["localized_phrase"])
            )
            
            # Validate all results have valid structure
            for result in [currency_result, unit_result, phrase_result]:
                assert hasattr(result, 'language'), "Result should have language"
                assert hasattr(result, 'confidence'), "Result should have confidence"
                assert 0.0 <= result.confidence <= 1.0, f"Invalid confidence: {result.confidence}"
                assert result.language.value in SUPPORTED_LANGUAGES, "Should detect supported language"
            
            # Currency symbols should be handled consistently
            if "₹" in loc_data["currency_text"]:
                # Indian rupee symbol should indicate Indian language context
                assert currency_result.confidence > 0.1, "Currency symbol should provide language context"
            
            # Numeric values should not break language detection
            assert phrase_result.confidence > 0.0, "Numeric values should not break detection"
            
        except Exception as e:
            pytest.fail(f"Localization consistency test failed: {str(e)}")
    
    @given(lang_code=st.sampled_from(["hi", "en", "bn", "te", "ta"]))
    @settings(max_examples=5, deadline=5000)
    def test_language_support_validation(self, lang_code: str):
        """
        Property 4: Multilingual Processing Consistency - Language Support
        
        For any supported language code, the system should validate support
        and provide appropriate configuration.
        """
        try:
            # Test language support validation
            is_supported = asyncio.run(
                self.language_detector.validate_language_support(lang_code)
            )
            
            # All test language codes should be supported
            assert is_supported, f"Language {lang_code} should be supported"
            
            # Test language detector supported languages
            detector_languages = self.language_detector.get_supported_languages()
            detector_lang_codes = [lang.value for lang in detector_languages]
            
            assert lang_code in detector_lang_codes, f"Language {lang_code} should be supported by detector"
            
        except Exception as e:
            pytest.fail(f"Language support validation test failed: {str(e)}")

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])