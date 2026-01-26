"""
Unit Tests for Voice Query Processing System
Tests natural language understanding, response generation, and session management
"""

import pytest
import asyncio
import time
from typing import Dict, Any, List
import os
import sys

# Add the voice processing service to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services', 'voice-processing-service'))

from query_processor import (
    VoiceQueryProcessor,
    QueryType,
    QueryIntent,
    ResponseType,
    QueryAnalysis,
    QueryResponse,
    QueryEntity
)
from language_detector import LanguageCode
from context_manager import UserContext, ConversationContextManager

class TestVoiceQueryProcessor:
    """Test class for voice query processing functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.query_processor = VoiceQueryProcessor()
        self.context_manager = ConversationContextManager()
    
    @pytest.mark.asyncio
    async def test_greeting_query_processing(self):
        """Test greeting query processing and response generation"""
        # Test Hindi greeting
        response = await self.query_processor.process_voice_query(
            query_text="नमस्ते",
            language=LanguageCode.HINDI
        )
        
        assert response.response_type == ResponseType.GREETING_RESPONSE
        assert response.language == LanguageCode.HINDI
        assert "नमस्ते" in response.response_text or "आदाब" in response.response_text
        assert response.confidence > 0.0
        assert response.processing_time > 0.0
        assert len(response.suggested_actions) > 0
        
        # Test English greeting
        response = await self.query_processor.process_voice_query(
            query_text="hello",
            language=LanguageCode.ENGLISH
        )
        
        assert response.response_type == ResponseType.GREETING_RESPONSE
        assert response.language == LanguageCode.ENGLISH
        assert "hello" in response.response_text.lower() or "welcome" in response.response_text.lower()
    
    @pytest.mark.asyncio
    async def test_price_inquiry_processing(self):
        """Test price inquiry query processing"""
        # Test Hindi price inquiry
        response = await self.query_processor.process_voice_query(
            query_text="गेहूं का दाम क्या है?",
            language=LanguageCode.HINDI
        )
        
        assert response.response_type in [ResponseType.DIRECT_ANSWER, ResponseType.INFORMATION_PROVISION]
        assert response.language == LanguageCode.HINDI
        assert response.confidence > 0.0
        assert "गेहूं" in response.response_text or "wheat" in response.metadata.get("query_type", "")
        
        # Test English price inquiry
        response = await self.query_processor.process_voice_query(
            query_text="What is the price of rice?",
            language=LanguageCode.ENGLISH
        )
        
        assert response.response_type in [ResponseType.DIRECT_ANSWER, ResponseType.INFORMATION_PROVISION]
        assert response.language == LanguageCode.ENGLISH
        assert "rice" in response.response_text.lower() or "price" in response.response_text.lower()
    
    @pytest.mark.asyncio
    async def test_response_time_limit(self):
        """Test that responses are generated within 3-second limit"""
        start_time = time.time()
        
        response = await self.query_processor.process_voice_query(
            query_text="आज मंडी में क्या भाव है?",
            language=LanguageCode.HINDI
        )
        
        end_time = time.time()
        actual_time = end_time - start_time
        
        # Response should be generated within 3 seconds
        assert actual_time <= 3.5  # Allow small buffer for test execution
        assert response.processing_time <= 3.0  # Internal processing time should be within limit
        assert response.processing_time > 0.0
    
    @pytest.mark.asyncio
    async def test_entity_extraction(self):
        """Test entity extraction from agricultural queries"""
        processor = VoiceQueryProcessor()
        
        # Test Hindi entity extraction
        patterns = processor.agricultural_patterns[LanguageCode.HINDI]
        entities = await processor._extract_entities(
            "गेहूं का दाम 2500 रुपये क्विंटल है",
            patterns,
            LanguageCode.HINDI
        )
        
        # Should extract commodity, price keyword, number, and unit
        entity_types = [e.entity_type for e in entities]
        assert "commodity" in entity_types
        assert "price_keyword" in entity_types
        assert "number" in entity_types
        assert "quantity_unit" in entity_types
        
        # Test English entity extraction
        patterns = processor.agricultural_patterns[LanguageCode.ENGLISH]
        entities = await processor._extract_entities(
            "Rice price is 3000 rupees per quintal",
            patterns,
            LanguageCode.ENGLISH
        )
        
        entity_types = [e.entity_type for e in entities]
        assert "commodity" in entity_types
        assert "price_keyword" in entity_types
        assert "number" in entity_types
    
    @pytest.mark.asyncio
    async def test_query_classification(self):
        """Test query type and intent classification"""
        processor = VoiceQueryProcessor()
        
        # Test price inquiry classification
        analysis = await processor._analyze_query(
            "गेहूं का भाव क्या है?",
            LanguageCode.HINDI
        )
        
        assert analysis.query_type == QueryType.PRICE_INQUIRY
        assert analysis.intent == QueryIntent.INFORMATION_SEEKING
        assert analysis.language == LanguageCode.HINDI
        assert analysis.confidence > 0.0
        
        # Test greeting classification
        analysis = await processor._analyze_query(
            "नमस्ते",
            LanguageCode.HINDI
        )
        
        assert analysis.query_type == QueryType.GREETING
        assert analysis.intent == QueryIntent.SOCIAL_INTERACTION
        
        # Test crop planning classification
        analysis = await processor._analyze_query(
            "Which crop should I plant this season?",
            LanguageCode.ENGLISH
        )
        
        assert analysis.query_type == QueryType.CROP_PLANNING
        assert analysis.intent == QueryIntent.PLANNING_ASSISTANCE
    
    @pytest.mark.asyncio
    async def test_session_context_integration(self):
        """Test integration with session context management"""
        # Create session
        session_id = "test_session_123"
        user_context = UserContext(
            user_id="test_user",
            preferred_language=LanguageCode.HINDI,
            location={"region": "Punjab"},
            farmer_profile={"experience": "beginner"}
        )
        
        session = await self.context_manager.create_session(session_id, user_context)
        
        # Process query with session context
        response = await self.query_processor.process_voice_query(
            query_text="गेहूं का दाम बताओ",
            language=LanguageCode.HINDI,
            session_id=session_id,
            user_context=user_context
        )
        
        assert response.response_type in [ResponseType.DIRECT_ANSWER, ResponseType.INFORMATION_PROVISION]
        assert response.language == LanguageCode.HINDI
        
        # Check that interactions were added to session
        updated_session = await self.context_manager.get_session(session_id)
        assert updated_session is not None
        assert len(updated_session.interactions) >= 2  # Query + Response
        
        # Check interaction types
        interaction_types = [i.type.value for i in updated_session.interactions]
        assert "voice_query" in interaction_types
        assert "voice_response" in interaction_types
        
        # Cleanup
        await self.context_manager.end_session(session_id)
    
    @pytest.mark.asyncio
    async def test_multilingual_support(self):
        """Test multilingual query processing support"""
        test_queries = [
            ("नमस्ते, गेहूं का भाव क्या है?", LanguageCode.HINDI),
            ("Hello, what is wheat price?", LanguageCode.ENGLISH),
            ("নমস্কার, গমের দাম কত?", LanguageCode.BENGALI)
        ]
        
        for query_text, language in test_queries:
            response = await self.query_processor.process_voice_query(
                query_text=query_text,
                language=language
            )
            
            assert response.language == language
            assert response.response_text is not None
            assert len(response.response_text) > 0
            assert response.confidence >= 0.0
            assert response.processing_time > 0.0
    
    @pytest.mark.asyncio
    async def test_clarification_requests(self):
        """Test clarification request generation for ambiguous queries"""
        # Test ambiguous query
        response = await self.query_processor.process_voice_query(
            query_text="दाम क्या है?",  # "What is the price?" - missing commodity
            language=LanguageCode.HINDI
        )
        
        assert response.response_type == ResponseType.CLARIFICATION_REQUEST
        assert response.language == LanguageCode.HINDI
        assert "कृपया बताएं" in response.response_text or "बताएं" in response.response_text
        
        # Test very short/unclear query
        response = await self.query_processor.process_voice_query(
            query_text="क्या?",
            language=LanguageCode.HINDI
        )
        
        assert response.response_type in [ResponseType.CLARIFICATION_REQUEST, ResponseType.ERROR_RESPONSE]
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling for invalid inputs"""
        # Test empty query
        response = await self.query_processor.process_voice_query(
            query_text="",
            language=LanguageCode.HINDI
        )
        
        assert response.response_type == ResponseType.ERROR_RESPONSE
        assert response.confidence == 0.0
        
        # Test very long query (stress test)
        long_query = "गेहूं का दाम " * 100  # Very long repetitive query
        response = await self.query_processor.process_voice_query(
            query_text=long_query,
            language=LanguageCode.HINDI
        )
        
        # Should still process but may have lower confidence
        assert response.response_text is not None
        assert response.processing_time > 0.0
    
    @pytest.mark.asyncio
    async def test_suggested_actions(self):
        """Test suggested actions generation"""
        # Test greeting response
        response = await self.query_processor.process_voice_query(
            query_text="नमस्ते",
            language=LanguageCode.HINDI
        )
        
        assert len(response.suggested_actions) > 0
        assert any("price" in action.lower() or "दाम" in action for action in response.suggested_actions)
        
        # Test price inquiry response
        response = await self.query_processor.process_voice_query(
            query_text="गेहूं का दाम क्या है?",
            language=LanguageCode.HINDI
        )
        
        if response.response_type == ResponseType.DIRECT_ANSWER:
            assert len(response.suggested_actions) > 0
    
    @pytest.mark.asyncio
    async def test_confidence_scoring(self):
        """Test confidence scoring for different query types"""
        # Clear agricultural query should have high confidence
        response = await self.query_processor.process_voice_query(
            query_text="गेहूं का दाम 2500 रुपये क्विंटल है",
            language=LanguageCode.HINDI
        )
        
        assert response.confidence > 0.5  # Should be reasonably confident
        
        # Ambiguous query should have lower confidence
        response = await self.query_processor.process_voice_query(
            query_text="क्या है?",
            language=LanguageCode.HINDI
        )
        
        assert response.confidence <= 0.8  # Should be less confident
    
    @pytest.mark.asyncio
    async def test_metadata_generation(self):
        """Test metadata generation in responses"""
        response = await self.query_processor.process_voice_query(
            query_text="गेहूं का दाम क्या है?",
            language=LanguageCode.HINDI
        )
        
        assert "query_type" in response.metadata
        assert "intent" in response.metadata
        assert "entities_found" in response.metadata
        
        # Metadata should contain valid values
        assert response.metadata["query_type"] in [qt.value for qt in QueryType]
        assert response.metadata["intent"] in [qi.value for qi in QueryIntent]
        assert isinstance(response.metadata["entities_found"], int)
        assert response.metadata["entities_found"] >= 0

class TestVoiceQueryProcessorIntegration:
    """Integration tests for voice query processor"""
    
    @pytest.mark.asyncio
    async def test_complete_conversation_flow(self):
        """Test complete conversation flow with multiple interactions"""
        processor = VoiceQueryProcessor()
        context_manager = ConversationContextManager()
        
        # Create session
        session_id = "integration_test_session"
        user_context = UserContext(
            user_id="integration_test_user",
            preferred_language=LanguageCode.HINDI,
            location={"region": "Haryana"},
            farmer_profile={"crops": ["wheat", "rice"]}
        )
        
        session = await context_manager.create_session(session_id, user_context)
        
        # Conversation flow
        conversation_steps = [
            ("नमस्ते", ResponseType.GREETING_RESPONSE),
            ("गेहूं का दाम क्या है?", ResponseType.DIRECT_ANSWER),
            ("धन्यवाद", ResponseType.GREETING_RESPONSE)
        ]
        
        for query_text, expected_response_type in conversation_steps:
            response = await processor.process_voice_query(
                query_text=query_text,
                language=LanguageCode.HINDI,
                session_id=session_id,
                user_context=user_context
            )
            
            # Validate response
            assert response.response_type in [expected_response_type, ResponseType.INFORMATION_PROVISION, ResponseType.CLARIFICATION_REQUEST]
            assert response.language == LanguageCode.HINDI
            assert response.processing_time <= 3.0
            assert response.processing_time > 0.0
        
        # Check final session state
        final_session = await context_manager.get_session(session_id)
        assert final_session is not None
        assert len(final_session.interactions) >= 6  # 3 queries + 3 responses
        
        # Cleanup
        await context_manager.end_session(session_id)

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])