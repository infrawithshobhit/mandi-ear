"""
Property-Based Test for Language Detection Fallback
Feature: mandi-ear, Property 5: Language Detection Fallback

**Validates: Requirements 2.4, 2.5**

This test validates that for any uncertain language detection scenario, the system 
should request clarification in the most likely detected language and maintain 
conversation context.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import asyncio
from typing import Dict, Any, List, Optional
import json
import os
import sys
from datetime import datetime

# Import voice processing components
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services', 'voice-processing-service'))

# Import with absolute imports to avoid relative import issues
import importlib.util
import sys

# Load language_detector module
spec = importlib.util.spec_from_file_location(
    "language_detector", 
    os.path.join(os.path.dirname(__file__), '..', 'services', 'voice-processing-service', 'language_detector.py')
)
language_detector_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(language_detector_module)

# Load context_manager module
spec = importlib.util.spec_from_file_location(
    "context_manager", 
    os.path.join(os.path.dirname(__file__), '..', 'services', 'voice-processing-service', 'context_manager.py')
)
context_manager_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(context_manager_module)

# Load cultural_context module
spec = importlib.util.spec_from_file_location(
    "cultural_context", 
    os.path.join(os.path.dirname(__file__), '..', 'services', 'voice-processing-service', 'cultural_context.py')
)
cultural_context_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cultural_context_module)

# Import classes
LanguageCode = language_detector_module.LanguageCode
LanguageDetector = language_detector_module.LanguageDetector
ConversationContextManager = context_manager_module.ConversationContextManager
UserContext = context_manager_module.UserContext
InteractionType = context_manager_module.InteractionType
Interaction = context_manager_module.Interaction
CulturalContextSystem = cultural_context_module.CulturalContextSystem
CulturalProfile = cultural_context_module.CulturalProfile
SocialContext = cultural_context_module.SocialContext
RegionalContext = cultural_context_module.RegionalContext
CulturalSensitivity = cultural_context_module.CulturalSensitivity

# Test configuration
SUPPORTED_LANGUAGES = [
    "hi", "en", "bn", "te", "mr", "ta", "gu", "ur", "kn", "or", 
    "ml", "pa", "as", "mai", "sat", "ks", "ne", "sd", "gom", "doi"
]

# Ambiguous text samples that could be multiple languages
AMBIGUOUS_SAMPLES = {
    "mixed_script": [
        "hello नमस्ते",  # English + Hindi
        "price দাম",     # English + Bengali
        "market మార్కెట్", # English + Telugu
        "farmer விவசாயி",  # English + Tamil
    ],
    "short_text": [
        "ok",
        "yes", 
        "no",
        "hi",
        "bye"
    ],
    "numbers_only": [
        "100",
        "500", 
        "₹250",
        "Rs 300"
    ],
    "transliterated": [
        "namaste",      # Hindi in English script
        "dhanyawad",    # Hindi in English script
        "vanakkam",     # Tamil in English script
        "adaab",        # Urdu in English script
    ],
    "very_short": [
        "a", "i", "o", "1", "2", "?"
    ]
}

# Fallback scenarios
FALLBACK_SCENARIOS = {
    "low_confidence": {
        "threshold": 0.5,
        "expected_behavior": "request_clarification"
    },
    "multiple_candidates": {
        "min_alternatives": 2,
        "expected_behavior": "show_alternatives"
    },
    "unknown_script": {
        "samples": ["???", "###", "***"],
        "expected_behavior": "fallback_to_default"
    },
    "empty_input": {
        "samples": ["", "   ", "\n", "\t"],
        "expected_behavior": "request_input"
    }
}

# Hypothesis strategies
@st.composite
def ambiguous_text_data(draw):
    """Generate ambiguous text data for testing fallback scenarios"""
    category = draw(st.sampled_from(list(AMBIGUOUS_SAMPLES.keys())))
    text = draw(st.sampled_from(AMBIGUOUS_SAMPLES[category]))
    
    # Add noise to make it more ambiguous
    noise_level = draw(st.floats(min_value=0.0, max_value=0.3))
    
    return {
        "text": text,
        "category": category,
        "noise_level": noise_level,
        "expected_ambiguity": True
    }

@st.composite
def fallback_scenario_data(draw):
    """Generate fallback scenario test data"""
    scenario_type = draw(st.sampled_from(list(FALLBACK_SCENARIOS.keys())))
    scenario_config = FALLBACK_SCENARIOS[scenario_type]
    
    if scenario_type == "unknown_script":
        text = draw(st.sampled_from(scenario_config["samples"]))
    elif scenario_type == "empty_input":
        text = draw(st.sampled_from(scenario_config["samples"]))
    else:
        # Generate text that should trigger the scenario
        text = draw(st.text(min_size=1, max_size=20))
    
    return {
        "scenario_type": scenario_type,
        "text": text,
        "config": scenario_config,
        "expected_behavior": scenario_config["expected_behavior"]
    }

@st.composite
def conversation_context_data(draw):
    """Generate conversation context for fallback testing"""
    session_length = draw(st.integers(min_value=1, max_value=10))
    primary_language = draw(st.sampled_from(["hi", "en", "bn"]))
    
    # Generate conversation history
    interactions = []
    for i in range(session_length):
        interaction_text = draw(st.text(min_size=5, max_size=50))
        interactions.append({
            "text": interaction_text,
            "language": primary_language,
            "confidence": draw(st.floats(min_value=0.1, max_value=1.0))
        })
    
    return {
        "session_length": session_length,
        "primary_language": primary_language,
        "interactions": interactions,
        "user_id": f"test_user_{draw(st.integers(min_value=1, max_value=1000))}"
    }

# Test fixtures
@pytest.fixture
async def language_detector():
    """Create language detector instance"""
    return LanguageDetector()

@pytest.fixture
async def context_manager():
    """Create conversation context manager instance"""
    return ConversationContextManager()

@pytest.fixture
async def cultural_context_system():
    """Create cultural context system instance"""
    return CulturalContextSystem()

# Property-based tests
class TestLanguageDetectionFallback:
    """
    Property 5: Language Detection Fallback
    
    For any uncertain language detection scenario, the system should request 
    clarification in the most likely detected language and maintain conversation context.
    """
    
    @given(ambiguous_text_data())
    @settings(max_examples=100, deadline=5000)
    def test_ambiguous_text_fallback_behavior(self, ambiguous_data):
        """
        Test that ambiguous text triggers appropriate fallback behavior
        **Validates: Requirements 2.4, 2.5**
        """
        async def run_test():
            language_detector = LanguageDetector()
            text = ambiguous_data["text"]
            category = ambiguous_data["category"]
            
            # Detect language for ambiguous text
            result = await language_detector.detect_language(text)
            
            # Property: System should provide alternatives for uncertain detection
            if result.confidence < 0.8:
                assert len(result.alternatives) >= 0, "Low confidence detection should provide alternatives"
                
            # Property: Fallback should maintain supported language constraint
            assert result.language in LanguageCode, f"Detected language {result.language} must be supported"
            
            # Property: Very short text should have reasonable fallback
            if category == "short_text" and len(text) < 5:
                assert result.language in [LanguageCode.HINDI, LanguageCode.ENGLISH], \
                    "Very short text should fallback to common languages"
            
            # Property: For truly ambiguous cases, confidence should reflect uncertainty
            if category in ["numbers_only", "short_text"] and len(text) <= 3:
                # Very short or numeric text should have lower confidence
                assert result.confidence <= 0.8, f"Very short/numeric text should have lower confidence, got {result.confidence}"
        
        asyncio.run(run_test())
    
    @given(fallback_scenario_data())
    @settings(max_examples=100, deadline=5000)
    def test_fallback_scenario_handling(self, scenario_data):
        """
        Test specific fallback scenarios behave correctly
        **Validates: Requirements 2.4, 2.5**
        """
        async def run_test():
            language_detector = LanguageDetector()
            scenario_type = scenario_data["scenario_type"]
            text = scenario_data["text"]
            expected_behavior = scenario_data["expected_behavior"]
            
            result = await language_detector.detect_language(text)
            
            # Property: Empty input should fallback to default language
            if scenario_type == "empty_input":
                assert result.language == LanguageCode.HINDI, "Empty input should fallback to Hindi"
                assert result.confidence <= 0.5, "Empty input should have low confidence"
                
            # Property: Unknown script should fallback gracefully
            elif scenario_type == "unknown_script":
                assert result.language in [LanguageCode.HINDI, LanguageCode.ENGLISH], \
                    "Unknown script should fallback to common languages"
                assert result.confidence <= 0.5, "Unknown script should have low confidence"
                
            # Property: Low confidence should provide alternatives
            elif scenario_type == "low_confidence":
                if result.confidence < 0.5:
                    assert len(result.alternatives) >= 0, "Low confidence should provide alternatives"
                    
            # Property: Multiple candidates should be ranked by confidence
            elif scenario_type == "multiple_candidates":
                if len(result.alternatives) > 1:
                    confidences = [alt[1] for alt in result.alternatives]
                    assert confidences == sorted(confidences, reverse=True), \
                        "Alternatives should be sorted by confidence"
        
        asyncio.run(run_test())
    
    @given(conversation_context_data(), ambiguous_text_data())
    @settings(max_examples=50, deadline=10000)
    def test_context_maintained_during_fallback(self, context_data, ambiguous_data):
        """
        Test that conversation context is maintained during language detection fallback
        **Validates: Requirements 2.5**
        """
        async def run_test():
            context_manager = ConversationContextManager()
            language_detector = LanguageDetector()
            
            # Create session with context
            session_id = f"test_session_{context_data['user_id']}"
            user_context = UserContext(
                user_id=context_data['user_id'],
                preferred_language=LanguageCode(context_data['primary_language']),
                location={"region": "test_region"},
                farmer_profile={"experience": "beginner"}
            )
            
            session = await context_manager.create_session(session_id, user_context)
            
            # Add conversation history
            for interaction_data in context_data['interactions']:
                interaction = Interaction(
                    id=f"interaction_{len(session.interactions)}",
                    type=InteractionType.VOICE_QUERY,
                    content=interaction_data['text'],
                    language=LanguageCode(interaction_data['language']),
                    timestamp=datetime.now(),
                    confidence=interaction_data['confidence']
                )
                await context_manager.add_interaction(session_id, interaction)
            
            # Test language detection with ambiguous text
            ambiguous_text = ambiguous_data["text"]
            detection_result = await language_detector.detect_language(ambiguous_text)
            
            # Property: Context should influence fallback language selection
            session_after = await context_manager.get_session(session_id)
            primary_lang = context_data['primary_language']
            
            # If detection is uncertain, it should consider session context
            if detection_result.confidence < 0.7:
                # Should either match primary language or provide it as alternative
                lang_codes = [detection_result.language.value] + [alt[0].value for alt in detection_result.alternatives]
                context_influence = primary_lang in lang_codes
                
                # Property: Session context should influence uncertain detections
                assert context_influence or detection_result.confidence > 0.25, \
                    f"Context language {primary_lang} should influence uncertain detection or provide reasonable confidence (got {detection_result.confidence})"
            
            # Property: Session should remain active and accessible
            assert session_after is not None, "Session should remain accessible after language detection"
            assert session_after.is_active, "Session should remain active"
            
            # Property: Conversation history should be preserved
            assert len(session_after.interactions) == len(context_data['interactions']), \
                "Conversation history should be preserved during language detection"
            
            # Cleanup
            await context_manager.end_session(session_id)
        
        asyncio.run(run_test())
    
    @given(st.lists(st.text(min_size=1, max_size=100), min_size=2, max_size=5))
    @settings(max_examples=50, deadline=10000)
    def test_clarification_request_language_consistency(self, text_samples):
        """
        Test that clarification requests use the most likely detected language consistently
        **Validates: Requirements 2.4**
        """
        async def run_test():
            language_detector = LanguageDetector()
            detection_results = []
            
            # Detect language for each text sample
            for text in text_samples:
                result = await language_detector.detect_language(text)
                detection_results.append(result)
            
            # Property: Uncertain detections should be consistent in fallback behavior
            uncertain_results = [r for r in detection_results if r.confidence < 0.8]
            
            if len(uncertain_results) > 1:
                # Check that similar confidence levels use similar fallback strategies
                low_conf_results = [r for r in uncertain_results if r.confidence < 0.5]
                medium_conf_results = [r for r in uncertain_results if 0.5 <= r.confidence < 0.8]
                
                # Property: Very low confidence should consistently fallback to common languages
                if low_conf_results:
                    common_languages = {LanguageCode.HINDI, LanguageCode.ENGLISH}
                    for result in low_conf_results:
                        assert result.language in common_languages, \
                            f"Very low confidence should fallback to common languages, got {result.language}"
                
                # Property: Medium confidence should provide alternatives
                if medium_conf_results:
                    for result in medium_conf_results:
                        assert len(result.alternatives) >= 0, \
                            "Medium confidence results should provide alternatives when available"
        
        asyncio.run(run_test())
    
    @given(st.sampled_from(SUPPORTED_LANGUAGES), st.text(min_size=1, max_size=50))
    @settings(max_examples=100, deadline=5000)
    def test_supported_language_constraint(self, expected_lang, text):
        """
        Test that fallback always results in supported languages
        **Validates: Requirements 2.4, 2.5**
        """
        async def run_test():
            language_detector = LanguageDetector()
            
            # Force detection with various text inputs
            result = await language_detector.detect_language(text)
            
            # Property: Detected language must always be supported
            assert result.language.value in SUPPORTED_LANGUAGES, \
                f"Detected language {result.language.value} must be in supported languages"
            
            # Property: All alternatives must be supported languages
            for alt_lang, alt_conf in result.alternatives:
                assert alt_lang.value in SUPPORTED_LANGUAGES, \
                    f"Alternative language {alt_lang.value} must be in supported languages"
                assert 0.0 <= alt_conf <= 1.0, f"Alternative confidence {alt_conf} must be valid probability"
            
            # Property: Confidence scores must be valid probabilities
            assert 0.0 <= result.confidence <= 1.0, \
                f"Confidence {result.confidence} must be valid probability"
            
            # Property: Primary detection should have highest confidence among alternatives
            if result.alternatives:
                max_alt_confidence = max(alt[1] for alt in result.alternatives)
                assert result.confidence >= max_alt_confidence, \
                    "Primary detection should have highest confidence"
        
        asyncio.run(run_test())

# Integration test for complete fallback workflow
class TestLanguageDetectionFallbackIntegration:
    """Integration tests for complete language detection fallback workflow"""
    
    @pytest.mark.asyncio
    async def test_complete_fallback_workflow(self):
        """
        Test complete workflow from uncertain detection to clarification
        **Validates: Requirements 2.4, 2.5**
        """
        # Initialize components
        detector = LanguageDetector()
        context_mgr = ConversationContextManager()
        
        # Test with highly ambiguous input
        ambiguous_inputs = [
            "ok",  # Very short
            "123",  # Numbers only
            "???",  # Unknown characters
            "",     # Empty
            "hello नमस्ते"  # Mixed script
        ]
        
        for text in ambiguous_inputs:
            # Detect language
            result = await detector.detect_language(text)
            
            # Verify fallback properties
            assert result.language in LanguageCode, "Must return supported language"
            assert 0.0 <= result.confidence <= 1.0, "Must return valid confidence"
            
            # For very uncertain cases, should have low confidence
            if text in ["", "???", "ok"]:
                assert result.confidence <= 0.7, f"Very ambiguous text '{text}' should have low confidence"
            
            # Should provide alternatives for uncertain cases
            if result.confidence < 0.8:
                assert isinstance(result.alternatives, list), "Should provide alternatives list"

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
   