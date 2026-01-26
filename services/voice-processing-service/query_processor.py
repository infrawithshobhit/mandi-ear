"""
Voice Query Processing System for MANDI EAR™
Natural language understanding for agricultural queries with response generation
"""

import logging
import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import re
from datetime import datetime

from language_detector import LanguageCode
from context_manager import ConversationContextManager, UserContext, Interaction, InteractionType

logger = logging.getLogger(__name__)

class QueryType(str, Enum):
    """Types of agricultural queries"""
    PRICE_INQUIRY = "price_inquiry"
    MARKET_COMPARISON = "market_comparison"
    CROP_PLANNING = "crop_planning"
    WEATHER_QUERY = "weather_query"
    MSP_INQUIRY = "msp_inquiry"
    NEGOTIATION_HELP = "negotiation_help"
    GENERAL_INFO = "general_info"
    GREETING = "greeting"
    UNKNOWN = "unknown"

class QueryIntent(str, Enum):
    """Intent classification for queries"""
    INFORMATION_SEEKING = "information_seeking"
    TRANSACTION_SUPPORT = "transaction_support"
    PLANNING_ASSISTANCE = "planning_assistance"
    COMPARISON_REQUEST = "comparison_request"
    HELP_REQUEST = "help_request"
    SOCIAL_INTERACTION = "social_interaction"

class ResponseType(str, Enum):
    """Types of responses"""
    DIRECT_ANSWER = "direct_answer"
    CLARIFICATION_REQUEST = "clarification_request"
    INFORMATION_PROVISION = "information_provision"
    ACTION_SUGGESTION = "action_suggestion"
    GREETING_RESPONSE = "greeting_response"
    ERROR_RESPONSE = "error_response"

@dataclass
class QueryEntity:
    """Extracted entity from query"""
    entity_type: str  # commodity, location, price, quantity, etc.
    value: str
    confidence: float
    start_pos: int = 0
    end_pos: int = 0

@dataclass
class QueryAnalysis:
    """Analysis result of user query"""
    query_type: QueryType
    intent: QueryIntent
    entities: List[QueryEntity]
    confidence: float
    language: LanguageCode
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class QueryResponse:
    """Response to user query"""
    response_text: str
    response_type: ResponseType
    language: LanguageCode
    confidence: float
    processing_time: float
    suggested_actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class VoiceQueryProcessor:
    """Advanced voice query processing system for agricultural queries"""
    
    def __init__(self, context_manager: Optional[ConversationContextManager] = None):
        self.context_manager = context_manager or ConversationContextManager()
        self.response_timeout = 3.0  # 3-second response limit
        
        # Agricultural vocabulary and patterns
        self.agricultural_patterns = self._initialize_agricultural_patterns()
        self.response_templates = self._initialize_response_templates()
        
    def _initialize_agricultural_patterns(self) -> Dict[LanguageCode, Dict[str, Any]]:
        """Initialize agricultural vocabulary and patterns for different languages"""
        return {
            LanguageCode.HINDI: {
                "commodities": {
                    "गेहूं": "wheat", "चावल": "rice", "कपास": "cotton", 
                    "गन्ना": "sugarcane", "मक्का": "maize", "जौ": "barley",
                    "दाल": "pulses", "सरसों": "mustard", "आलू": "potato",
                    "प्याज": "onion", "टमाटर": "tomato"
                },
                "price_keywords": ["दाम", "कीमत", "भाव", "रेट", "मूल्य"],
                "location_keywords": ["मंडी", "बाजार", "शहर", "गांव", "जिला"],
                "quantity_keywords": ["किलो", "क्विंटल", "टन", "बोरी", "थैला"],
                "transaction_keywords": ["बेचना", "खरीदना", "बिक्री", "खरीद"],
                "greeting_patterns": ["नमस्ते", "नमस्कार", "आदाब", "सलाम"],
                "question_patterns": ["क्या", "कैसे", "कब", "कहां", "कितना", "कौन"]
            },
            LanguageCode.ENGLISH: {
                "commodities": {
                    "wheat": "wheat", "rice": "rice", "cotton": "cotton",
                    "sugarcane": "sugarcane", "maize": "maize", "barley": "barley",
                    "pulses": "pulses", "mustard": "mustard", "potato": "potato",
                    "onion": "onion", "tomato": "tomato"
                },
                "price_keywords": ["price", "rate", "cost", "value", "amount"],
                "location_keywords": ["mandi", "market", "city", "village", "district"],
                "quantity_keywords": ["kg", "kilogram", "quintal", "ton", "bag"],
                "transaction_keywords": ["sell", "buy", "selling", "buying", "trade"],
                "greeting_patterns": ["hello", "hi", "namaste", "good morning", "good evening"],
                "question_patterns": ["what", "how", "when", "where", "how much", "which"]
            },
            LanguageCode.BENGALI: {
                "commodities": {
                    "গম": "wheat", "চাল": "rice", "তুলা": "cotton",
                    "আখ": "sugarcane", "ভুট্টা": "maize", "যব": "barley",
                    "ডাল": "pulses", "সরিষা": "mustard", "আলু": "potato"
                },
                "price_keywords": ["দাম", "মূল্য", "ভাব", "রেট"],
                "location_keywords": ["মণ্ডি", "বাজার", "শহর", "গ্রাম"],
                "quantity_keywords": ["কেজি", "কুইন্টাল", "টন", "বস্তা"],
                "transaction_keywords": ["বিক্রি", "কিনতে", "বেচা", "কেনা"],
                "greeting_patterns": ["নমস্কার", "আদাব", "প্রণাম"],
                "question_patterns": ["কি", "কিভাবে", "কখন", "কোথায়", "কত"]
            }
        }
    
    def _initialize_response_templates(self) -> Dict[LanguageCode, Dict[str, List[str]]]:
        """Initialize response templates for different languages"""
        return {
            LanguageCode.HINDI: {
                "greeting": [
                    "नमस्ते! मैं आपकी कृषि संबंधी जानकारी में मदद कर सकता हूं।",
                    "आदाब! मंडी की कीमतों और फसल की जानकारी के लिए पूछें।"
                ],
                "price_response": [
                    "{commodity} का आज का भाव {price} रुपये प्रति {unit} है।",
                    "{location} मंडी में {commodity} की कीमत {price} रुपये {unit} है।"
                ],
                "clarification": [
                    "कृपया बताएं कि आप किस फसल के बारे में जानना चाहते हैं?",
                    "आप किस मंडी की कीमत जानना चाहते हैं?"
                ],
                "error": [
                    "माफ करें, मैं आपकी बात समझ नहीं पाया। कृपया फिर से कहें।",
                    "क्षमा करें, कोई तकनीकी समस्या है। कृपया दोबारा कोशिश करें।"
                ]
            },
            LanguageCode.ENGLISH: {
                "greeting": [
                    "Hello! I can help you with agricultural information and market prices.",
                    "Welcome! Ask me about crop prices, market information, or farming guidance."
                ],
                "price_response": [
                    "Today's price for {commodity} is ₹{price} per {unit}.",
                    "In {location} mandi, {commodity} is trading at ₹{price} per {unit}."
                ],
                "clarification": [
                    "Please specify which crop you want to know about?",
                    "Which market or location are you interested in?"
                ],
                "error": [
                    "Sorry, I didn't understand. Please try again.",
                    "I apologize, there seems to be a technical issue. Please retry."
                ]
            },
            LanguageCode.BENGALI: {
                "greeting": [
                    "নমস্কার! আমি কৃষি তথ্য এবং বাজার দামে সাহায্য করতে পারি।",
                    "স্বাগতম! ফসলের দাম এবং বাজারের তথ্য জানতে চাইলে জিজ্ঞাসা করুন।"
                ],
                "price_response": [
                    "{commodity} এর আজকের দাম {price} টাকা প্রতি {unit}।",
                    "{location} মণ্ডিতে {commodity} এর দাম {price} টাকা {unit}।"
                ],
                "clarification": [
                    "দয়া করে বলুন কোন ফসল সম্পর্কে জানতে চান?",
                    "কোন বাজার বা এলাকার দাম জানতে চান?"
                ],
                "error": [
                    "দুঃখিত, আমি বুঝতে পারিনি। আবার চেষ্টা করুন।",
                    "ক্ষমা করবেন, কিছু সমস্যা হয়েছে। আবার চেষ্টা করুন।"
                ]
            }
        }
    
    async def process_voice_query(
        self,
        query_text: str,
        language: LanguageCode,
        session_id: Optional[str] = None,
        user_context: Optional[UserContext] = None
    ) -> QueryResponse:
        """
        Process voice query and generate response within 3-second limit
        
        Args:
            query_text: Transcribed query text
            language: Detected language
            session_id: Optional session ID for context
            user_context: Optional user context
            
        Returns:
            QueryResponse with generated response
        """
        start_time = time.time()
        
        try:
            # Analyze query
            analysis = await self._analyze_query(query_text, language)
            
            # Get session context if available
            session_context = None
            if session_id:
                session_context = await self.context_manager.get_session(session_id)
            
            # Generate response based on analysis
            response = await self._generate_response(
                analysis, 
                session_context, 
                user_context
            )
            
            # Add interaction to session if available
            if session_id and session_context:
                # Add user query
                user_interaction = Interaction(
                    id=f"query_{int(time.time())}",
                    type=InteractionType.VOICE_QUERY,
                    content=query_text,
                    language=language,
                    timestamp=datetime.now(),
                    confidence=analysis.confidence
                )
                await self.context_manager.add_interaction(session_id, user_interaction)
                
                # Add system response
                response_interaction = Interaction(
                    id=f"response_{int(time.time())}",
                    type=InteractionType.VOICE_RESPONSE,
                    content=response.response_text,
                    language=response.language,
                    timestamp=datetime.now(),
                    confidence=response.confidence
                )
                await self.context_manager.add_interaction(session_id, response_interaction)
            
            processing_time = time.time() - start_time
            response.processing_time = processing_time
            
            # Ensure response time is within limit
            if processing_time > self.response_timeout:
                logger.warning(f"Response time exceeded limit: {processing_time:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"Voice query processing failed: {e}")
            processing_time = time.time() - start_time
            
            # Return error response
            return QueryResponse(
                response_text=self._get_error_response(language),
                response_type=ResponseType.ERROR_RESPONSE,
                language=language,
                confidence=0.0,
                processing_time=processing_time
            )
    
    async def _analyze_query(self, query_text: str, language: LanguageCode) -> QueryAnalysis:
        """Analyze query to extract intent and entities"""
        start_time = time.time()
        
        # Get language patterns
        patterns = self.agricultural_patterns.get(language, self.agricultural_patterns[LanguageCode.ENGLISH])
        
        # Extract entities
        entities = await self._extract_entities(query_text, patterns, language)
        
        # Classify query type and intent
        query_type = await self._classify_query_type(query_text, entities, patterns)
        intent = await self._classify_intent(query_type, entities)
        
        # Calculate confidence based on entity extraction and pattern matching
        confidence = await self._calculate_analysis_confidence(query_text, entities, patterns)
        
        processing_time = time.time() - start_time
        
        return QueryAnalysis(
            query_type=query_type,
            intent=intent,
            entities=entities,
            confidence=confidence,
            language=language,
            processing_time=processing_time,
            metadata={
                "original_query": query_text,
                "pattern_matches": len(entities)
            }
        )
    
    async def _extract_entities(
        self, 
        query_text: str, 
        patterns: Dict[str, Any], 
        language: LanguageCode
    ) -> List[QueryEntity]:
        """Extract entities from query text"""
        entities = []
        query_lower = query_text.lower()
        
        # Extract commodities
        for commodity_name, commodity_code in patterns.get("commodities", {}).items():
            if commodity_name.lower() in query_lower:
                start_pos = query_lower.find(commodity_name.lower())
                entities.append(QueryEntity(
                    entity_type="commodity",
                    value=commodity_code,
                    confidence=0.9,
                    start_pos=start_pos,
                    end_pos=start_pos + len(commodity_name)
                ))
        
        # Extract price-related keywords
        for price_keyword in patterns.get("price_keywords", []):
            if price_keyword.lower() in query_lower:
                start_pos = query_lower.find(price_keyword.lower())
                entities.append(QueryEntity(
                    entity_type="price_keyword",
                    value=price_keyword,
                    confidence=0.8,
                    start_pos=start_pos,
                    end_pos=start_pos + len(price_keyword)
                ))
        
        # Extract locations
        for location_keyword in patterns.get("location_keywords", []):
            if location_keyword.lower() in query_lower:
                start_pos = query_lower.find(location_keyword.lower())
                entities.append(QueryEntity(
                    entity_type="location",
                    value=location_keyword,
                    confidence=0.7,
                    start_pos=start_pos,
                    end_pos=start_pos + len(location_keyword)
                ))
        
        # Extract quantities and units
        for quantity_keyword in patterns.get("quantity_keywords", []):
            if quantity_keyword.lower() in query_lower:
                start_pos = query_lower.find(quantity_keyword.lower())
                entities.append(QueryEntity(
                    entity_type="quantity_unit",
                    value=quantity_keyword,
                    confidence=0.8,
                    start_pos=start_pos,
                    end_pos=start_pos + len(quantity_keyword)
                ))
        
        # Extract numeric values (prices, quantities)
        import re
        number_pattern = r'\d+(?:\.\d+)?'
        for match in re.finditer(number_pattern, query_text):
            entities.append(QueryEntity(
                entity_type="number",
                value=match.group(),
                confidence=0.9,
                start_pos=match.start(),
                end_pos=match.end()
            ))
        
        return entities
    
    async def _classify_query_type(
        self, 
        query_text: str, 
        entities: List[QueryEntity], 
        patterns: Dict[str, Any]
    ) -> QueryType:
        """Classify the type of query"""
        query_lower = query_text.lower()
        
        # Check for greeting patterns
        for greeting in patterns.get("greeting_patterns", []):
            if greeting.lower() in query_lower:
                return QueryType.GREETING
        
        # Check for price-related queries
        price_entities = [e for e in entities if e.entity_type == "price_keyword"]
        commodity_entities = [e for e in entities if e.entity_type == "commodity"]
        
        if price_entities and commodity_entities:
            return QueryType.PRICE_INQUIRY
        elif price_entities:
            return QueryType.PRICE_INQUIRY
        
        # Check for market comparison keywords
        comparison_keywords = ["compare", "comparison", "better", "best", "तुलना", "बेहतर"]
        if any(keyword in query_lower for keyword in comparison_keywords):
            return QueryType.MARKET_COMPARISON
        
        # Check for planning-related keywords
        planning_keywords = ["plan", "planning", "crop", "season", "योजना", "फसल", "मौसम"]
        if any(keyword in query_lower for keyword in planning_keywords):
            return QueryType.CROP_PLANNING
        
        # Check for weather keywords
        weather_keywords = ["weather", "rain", "temperature", "मौसम", "बारिश", "तापमान"]
        if any(keyword in query_lower for keyword in weather_keywords):
            return QueryType.WEATHER_QUERY
        
        # Check for MSP keywords
        msp_keywords = ["msp", "minimum support price", "government price", "न्यूनतम समर्थन मूल्य"]
        if any(keyword in query_lower for keyword in msp_keywords):
            return QueryType.MSP_INQUIRY
        
        # Check for negotiation help
        negotiation_keywords = ["negotiate", "bargain", "deal", "बातचीत", "सौदा"]
        if any(keyword in query_lower for keyword in negotiation_keywords):
            return QueryType.NEGOTIATION_HELP
        
        # Check for question patterns
        question_patterns = patterns.get("question_patterns", [])
        if any(pattern in query_lower for pattern in question_patterns):
            return QueryType.GENERAL_INFO
        
        return QueryType.UNKNOWN
    
    async def _classify_intent(self, query_type: QueryType, entities: List[QueryEntity]) -> QueryIntent:
        """Classify user intent based on query type and entities"""
        if query_type == QueryType.GREETING:
            return QueryIntent.SOCIAL_INTERACTION
        elif query_type in [QueryType.PRICE_INQUIRY, QueryType.MSP_INQUIRY]:
            return QueryIntent.INFORMATION_SEEKING
        elif query_type == QueryType.MARKET_COMPARISON:
            return QueryIntent.COMPARISON_REQUEST
        elif query_type == QueryType.CROP_PLANNING:
            return QueryIntent.PLANNING_ASSISTANCE
        elif query_type == QueryType.NEGOTIATION_HELP:
            return QueryIntent.TRANSACTION_SUPPORT
        elif query_type in [QueryType.WEATHER_QUERY, QueryType.GENERAL_INFO]:
            return QueryIntent.INFORMATION_SEEKING
        else:
            return QueryIntent.HELP_REQUEST
    
    async def _calculate_analysis_confidence(
        self, 
        query_text: str, 
        entities: List[QueryEntity], 
        patterns: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for query analysis"""
        if not query_text.strip():
            return 0.0
        
        # Base confidence from entity extraction
        entity_confidence = sum(e.confidence for e in entities) / max(len(entities), 1)
        
        # Boost confidence for clear agricultural vocabulary
        agricultural_terms = 0
        total_terms = len(query_text.split())
        
        for pattern_list in patterns.values():
            if isinstance(pattern_list, dict):
                agricultural_terms += sum(1 for term in pattern_list.keys() 
                                        if term.lower() in query_text.lower())
            elif isinstance(pattern_list, list):
                agricultural_terms += sum(1 for term in pattern_list 
                                        if term.lower() in query_text.lower())
        
        vocabulary_confidence = min(1.0, agricultural_terms / max(total_terms, 1))
        
        # Combine confidences
        final_confidence = (entity_confidence * 0.6) + (vocabulary_confidence * 0.4)
        
        return min(1.0, final_confidence)
    
    async def _generate_response(
        self,
        analysis: QueryAnalysis,
        session_context: Optional[Any] = None,
        user_context: Optional[UserContext] = None
    ) -> QueryResponse:
        """Generate appropriate response based on query analysis"""
        start_time = time.time()
        
        templates = self.response_templates.get(
            analysis.language, 
            self.response_templates[LanguageCode.ENGLISH]
        )
        
        response_text = ""
        response_type = ResponseType.DIRECT_ANSWER
        suggested_actions = []
        
        if analysis.query_type == QueryType.GREETING:
            response_text = templates["greeting"][0]
            response_type = ResponseType.GREETING_RESPONSE
            suggested_actions = ["Ask about crop prices", "Get market information"]
            
        elif analysis.query_type == QueryType.PRICE_INQUIRY:
            # Extract commodity and location from entities
            commodity = None
            location = None
            
            for entity in analysis.entities:
                if entity.entity_type == "commodity":
                    commodity = entity.value
                elif entity.entity_type == "location":
                    location = entity.value
            
            if commodity:
                # Simulate price data (in real system, this would fetch from price service)
                mock_price = 2500  # Mock price
                mock_unit = "quintal"
                
                if location:
                    response_text = templates["price_response"][1].format(
                        commodity=commodity.title(),
                        location=location,
                        price=mock_price,
                        unit=mock_unit
                    )
                else:
                    response_text = templates["price_response"][0].format(
                        commodity=commodity.title(),
                        price=mock_price,
                        unit=mock_unit
                    )
                
                suggested_actions = ["Compare with other markets", "Check MSP rates"]
            else:
                response_text = templates["clarification"][0]
                response_type = ResponseType.CLARIFICATION_REQUEST
                
        elif analysis.query_type == QueryType.MARKET_COMPARISON:
            response_text = "मैं विभिन्न मंडियों की कीमतों की तुलना कर सकता हूं। कृपया बताएं कि आप किस फसल की तुलना करना चाहते हैं?"
            response_type = ResponseType.CLARIFICATION_REQUEST
            suggested_actions = ["Specify crop for comparison"]
            
        elif analysis.query_type == QueryType.CROP_PLANNING:
            response_text = "फसल योजना के लिए मैं मौसम, मिट्टी और बाजार की मांग के आधार पर सुझाव दे सकता हूं। आप किस क्षेत्र के लिए योजना बनाना चाहते हैं?"
            response_type = ResponseType.CLARIFICATION_REQUEST
            suggested_actions = ["Provide location for planning"]
            
        elif analysis.query_type == QueryType.UNKNOWN:
            response_text = templates["clarification"][0]
            response_type = ResponseType.CLARIFICATION_REQUEST
            suggested_actions = ["Ask about prices", "Get market info", "Crop planning help"]
            
        else:
            response_text = templates["error"][0]
            response_type = ResponseType.ERROR_RESPONSE
        
        processing_time = time.time() - start_time
        
        return QueryResponse(
            response_text=response_text,
            response_type=response_type,
            language=analysis.language,
            confidence=analysis.confidence,
            processing_time=processing_time,
            suggested_actions=suggested_actions,
            metadata={
                "query_type": analysis.query_type.value,
                "intent": analysis.intent.value,
                "entities_found": len(analysis.entities)
            }
        )
    
    def _get_error_response(self, language: LanguageCode) -> str:
        """Get error response in appropriate language"""
        templates = self.response_templates.get(
            language, 
            self.response_templates[LanguageCode.ENGLISH]
        )
        return templates["error"][0]
    
    async def get_session_context_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of session context for query processing"""
        return await self.context_manager.get_context_summary(session_id)
    
    async def update_session_context(
        self, 
        session_id: str, 
        context_updates: Dict[str, Any]
    ) -> bool:
        """Update session context"""
        return await self.context_manager.update_user_context(session_id, context_updates)
    
    def get_supported_query_types(self) -> List[str]:
        """Get list of supported query types"""
        return [query_type.value for query_type in QueryType]
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages for query processing"""
        return [lang.value for lang in self.agricultural_patterns.keys()]