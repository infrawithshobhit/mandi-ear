"""
Conversation Analysis and Entity Extraction for MANDI EAR™
Handles NLP pipeline for commodity, price, quantity extraction and intent classification
"""

import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger()

class Intent(Enum):
    BUYING = "buying"
    SELLING = "selling"
    INQUIRY = "inquiry"
    UNKNOWN = "unknown"

class CommodityType(Enum):
    WHEAT = "wheat"
    RICE = "rice"
    CORN = "corn"
    BARLEY = "barley"
    ONION = "onion"
    POTATO = "potato"
    TOMATO = "tomato"
    COTTON = "cotton"
    SUGARCANE = "sugarcane"
    UNKNOWN = "unknown"

@dataclass
class ExtractedEntity:
    """Represents an extracted entity from conversation"""
    entity_type: str
    value: str
    confidence: float
    start_pos: int
    end_pos: int

@dataclass
class PriceEntity:
    """Represents extracted price information"""
    amount: float
    currency: str
    unit: str
    confidence: float

@dataclass
class QuantityEntity:
    """Represents extracted quantity information"""
    amount: float
    unit: str
    confidence: float

@dataclass
class LocationEntity:
    """Represents extracted location information"""
    name: str
    type: str  # mandi, district, state
    confidence: float

@dataclass
class ConversationAnalysis:
    """Complete analysis of a conversation segment"""
    text: str
    intent: Intent
    intent_confidence: float
    commodity: Optional[CommodityType]
    commodity_confidence: float
    price: Optional[PriceEntity]
    quantity: Optional[QuantityEntity]
    location: Optional[LocationEntity]
    entities: List[ExtractedEntity]
    overall_confidence: float

class ConversationAnalyzer:
    """
    Analyzes conversations to extract market intelligence
    Implements NLP pipeline for commodity, price, quantity extraction and intent classification
    """
    
    def __init__(self):
        """Initialize the conversation analyzer"""
        self.commodity_patterns = self._build_commodity_patterns()
        self.price_patterns = self._build_price_patterns()
        self.quantity_patterns = self._build_quantity_patterns()
        self.location_patterns = self._build_location_patterns()
        self.intent_patterns = self._build_intent_patterns()
        
        logger.info("ConversationAnalyzer initialized")
    
    def _build_commodity_patterns(self) -> Dict[CommodityType, List[str]]:
        """Build regex patterns for commodity detection"""
        return {
            CommodityType.WHEAT: [
                r'\b(?:wheat|गेहूं|गहूं|ಗೋಧಿ|గోధుమ|கோதுமை)\b',
                r'\b(?:gehun|godhuma|kothumai)\b'
            ],
            CommodityType.RICE: [
                r'\b(?:rice|चावल|ಅಕ್ಕಿ|బియ్యం|அரிசி)\b',
                r'\b(?:chawal|akki|biyyam|arisi)\b'
            ],
            CommodityType.CORN: [
                r'\b(?:corn|maize|मक्का|ಜೋಳ|మొక్కజొన్న|சோளம்)\b',
                r'\b(?:makka|jola|mokkajonnu|cholam)\b'
            ],
            CommodityType.ONION: [
                r'\b(?:onion|प्याज|ಈರುಳ್ಳಿ|ఉల్లిపాయ|வெங்காயம்)\b',
                r'\b(?:pyaj|eerulli|ullipaya|vengayam)\b'
            ],
            CommodityType.POTATO: [
                r'\b(?:potato|आलू|ಆಲೂಗಡ್ಡೆ|బంగాళాదుంప|உருளைக்கிழங்கு)\b',
                r'\b(?:aloo|alugadde|bangaladumpa|urulaikizhangu)\b'
            ],
            CommodityType.TOMATO: [
                r'\b(?:tomato|टमाटर|ಟೊಮೇಟೊ|టమాట|தக்காளி)\b',
                r'\b(?:tamatar|tometo|tamata|thakkali)\b'
            ],
            CommodityType.COTTON: [
                r'\b(?:cotton|कपास|ಹತ್ತಿ|పత్తి|பருத்தி)\b',
                r'\b(?:kapas|hatti|patti|parutti)\b'
            ],
            CommodityType.SUGARCANE: [
                r'\b(?:sugarcane|गन्ना|ಕಬ್ಬು|చెరకు|கரும்பு)\b',
                r'\b(?:ganna|kabbu|cheraku|karumbu)\b'
            ]
        }
    
    def _build_price_patterns(self) -> List[str]:
        """Build regex patterns for price detection"""
        return [
            r'₹\s*(\d+(?:,\d+)*(?:\.\d+)?)',  # ₹1000, ₹1,000.50
            r'(?:rs|rupees?|रुपये?|रूपए)\s*(\d+(?:,\d+)*(?:\.\d+)?)',  # Rs 1000, rupees 1000
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:rs|rupees?|रुपये?|रूपए)',  # 1000 rs
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:per|प्रति|ಪ್ರತಿ|ప్రతి|ஒன்றுக்கு)',  # 1000 per
            r'(?:price|rate|दाम|भाव|ಬೆಲೆ|ధర|விலை)\s*(?:is|है|ಇದೆ|ఉంది|உள்ளது)?\s*₹?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:taka|टका|ಟಕಾ|టాకా|டாகா)'  # Regional currency terms
        ]
    
    def _build_quantity_patterns(self) -> List[str]:
        """Build regex patterns for quantity detection"""
        return [
            r'(\d+(?:\.\d+)?)\s*(?:kg|kilogram|किलो|ಕಿಲೋ|కిలో|கிலோ)',
            r'(\d+(?:\.\d+)?)\s*(?:quintal|क्विंटल|ಕ್ವಿಂಟಲ್|క్వింటల్|குவிண்டல்)',
            r'(\d+(?:\.\d+)?)\s*(?:ton|tonne|टन|ಟನ್|టన్|டன்)',
            r'(\d+(?:\.\d+)?)\s*(?:bag|bags|बोरी|बोरे|ಚೀಲ|సంచి|பை)',
            r'(\d+(?:\.\d+)?)\s*(?:sack|sacks|बोरा|ಚೀಲ|సంచి|சாக்)',
            r'(\d+(?:\.\d+)?)\s*(?:maund|मन|ಮಣ|మణ|மணம்)',
            r'(\d+(?:\.\d+)?)\s*(?:acre|एकड़|ಎಕರೆ|ఎకరం|ஏக்கர்)'
        ]
    
    def _build_location_patterns(self) -> List[str]:
        """Build regex patterns for location detection"""
        return [
            r'(?:mandi|market|मंडी|ಮಂಡಿ|మండి|மண்டி)\s+([A-Za-z\u0900-\u097F\u0C80-\u0CFF\u0C00-\u0C7F\u0B80-\u0BFF]+)',
            r'([A-Za-z\u0900-\u097F\u0C80-\u0CFF\u0C00-\u0C7F\u0B80-\u0BFF]+)\s+(?:mandi|market|मंडी|ಮಂಡಿ|మండి|மண்டி)',
            r'(?:district|जिला|ಜಿಲ್ಲೆ|జిల్లా|மாவட்டம்)\s+([A-Za-z\u0900-\u097F\u0C80-\u0CFF\u0C00-\u0C7F\u0B80-\u0BFF]+)',
            r'([A-Za-z\u0900-\u097F\u0C80-\u0CFF\u0C00-\u0C7F\u0B80-\u0BFF]+)\s+(?:district|जिला|ಜಿಲ್ಲೆ|జిల్లా|மாவட்டம்)'
        ]
    
    def _build_intent_patterns(self) -> Dict[Intent, List[str]]:
        """Build regex patterns for intent classification"""
        return {
            Intent.BUYING: [
                r'\b(?:buy|buying|purchase|खरीद|ಖರೀದಿ|కొనుగోలు|வாங்க)\b',
                r'\b(?:need|want|चाहिए|ಬೇಕು|కావాలి|வேண்டும்)\b',
                r'\b(?:looking for|ढूंढ|ಹುಡುಕು|వెతుకు|தேடு)\b'
            ],
            Intent.SELLING: [
                r'\b(?:sell|selling|sale|बेच|ಮಾರಾಟ|అమ್మకం|விற்பனை)\b',
                r'\b(?:available|उपलब्ध|ಲಭ್ಯ|అందుబాటు|கிடைக்கும்)\b',
                r'\b(?:have|got|है|ಇದೆ|ఉంది|உள்ளது)\b.*(?:for sale|बेचने|ಮಾರಾಟಕ್ಕೆ|అమ్మకానికి|விற்பனைக்கு)'
            ],
            Intent.INQUIRY: [
                r'\b(?:price|rate|cost|दाम|भाव|ಬೆಲೆ|ధర|விலை)\b.*(?:\?|कैसा|ಹೇಗೆ|ఎలా|எப்படி)',
                r'\b(?:what|क्या|ಏನು|ఏమి|என்ன)\b.*(?:price|rate|दाम|भाव|ಬೆಲೆ|ధర|விலை)',
                r'\b(?:how much|कितना|ಎಷ್ಟು|ఎంత|எவ்வளவு)\b'
            ]
        }
    
    def extract_commodity(self, text: str) -> Tuple[Optional[CommodityType], float]:
        """Extract commodity information from text"""
        text_lower = text.lower()
        best_match = None
        best_confidence = 0.0
        
        for commodity, patterns in self.commodity_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE | re.UNICODE)
                if matches:
                    # Calculate confidence based on pattern specificity and match count
                    confidence = min(0.9, 0.6 + len(matches) * 0.1)
                    if confidence > best_confidence:
                        best_match = commodity
                        best_confidence = confidence
        
        return best_match, best_confidence
    
    def extract_price(self, text: str) -> Optional[PriceEntity]:
        """Extract price information from text"""
        for pattern in self.price_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.UNICODE)
            for match in matches:
                try:
                    # Extract numeric value
                    price_str = match.group(1) if match.groups() else match.group(0)
                    price_str = re.sub(r'[^\d.]', '', price_str)  # Remove non-numeric chars
                    
                    if price_str:
                        amount = float(price_str)
                        
                        # Determine unit context
                        context = text[max(0, match.start()-20):match.end()+20].lower()
                        unit = "per_unit"
                        
                        if any(word in context for word in ["kg", "kilogram", "किलो"]):
                            unit = "per_kg"
                        elif any(word in context for word in ["quintal", "क्विंटल"]):
                            unit = "per_quintal"
                        elif any(word in context for word in ["ton", "टन"]):
                            unit = "per_ton"
                        elif any(word in context for word in ["bag", "बोरी"]):
                            unit = "per_bag"
                        
                        # Calculate confidence based on pattern match and context
                        confidence = 0.8 if "₹" in match.group(0) else 0.7
                        
                        return PriceEntity(
                            amount=amount,
                            currency="INR",
                            unit=unit,
                            confidence=confidence
                        )
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def extract_quantity(self, text: str) -> Optional[QuantityEntity]:
        """Extract quantity information from text"""
        for pattern in self.quantity_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.UNICODE)
            for match in matches:
                try:
                    amount_str = match.group(1)
                    amount = float(amount_str)
                    
                    # Determine unit from the match
                    full_match = match.group(0).lower()
                    unit = "units"
                    
                    if any(word in full_match for word in ["kg", "kilogram", "किलो"]):
                        unit = "kg"
                    elif any(word in full_match for word in ["quintal", "क्विंटल"]):
                        unit = "quintal"
                    elif any(word in full_match for word in ["ton", "टन"]):
                        unit = "ton"
                    elif any(word in full_match for word in ["bag", "बोरी"]):
                        unit = "bags"
                    elif any(word in full_match for word in ["sack", "बोरा"]):
                        unit = "sacks"
                    elif any(word in full_match for word in ["maund", "मन"]):
                        unit = "maund"
                    elif any(word in full_match for word in ["acre", "एकड़"]):
                        unit = "acres"
                    
                    return QuantityEntity(
                        amount=amount,
                        unit=unit,
                        confidence=0.8
                    )
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def extract_location(self, text: str) -> Optional[LocationEntity]:
        """Extract location information from text"""
        for pattern in self.location_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.UNICODE)
            for match in matches:
                try:
                    location_name = match.group(1).strip()
                    
                    # Determine location type from context
                    full_match = match.group(0).lower()
                    location_type = "unknown"
                    
                    if any(word in full_match for word in ["mandi", "market", "मंडी"]):
                        location_type = "mandi"
                    elif any(word in full_match for word in ["district", "जिला"]):
                        location_type = "district"
                    
                    return LocationEntity(
                        name=location_name,
                        type=location_type,
                        confidence=0.7
                    )
                except IndexError:
                    continue
        
        return None
    
    def classify_intent(self, text: str) -> Tuple[Intent, float]:
        """Classify the intent of the conversation"""
        text_lower = text.lower()
        intent_scores = {intent: 0.0 for intent in Intent}
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE | re.UNICODE)
                if matches:
                    # Score based on number of matches and pattern specificity
                    score = len(matches) * 0.3
                    intent_scores[intent] += score
        
        # Find the intent with highest score
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        
        if best_intent[1] > 0:
            confidence = min(0.9, best_intent[1])
            return best_intent[0], confidence
        else:
            return Intent.UNKNOWN, 0.1
    
    def extract_all_entities(self, text: str) -> List[ExtractedEntity]:
        """Extract all entities from text"""
        entities = []
        
        # Extract commodity entities
        commodity, commodity_conf = self.extract_commodity(text)
        if commodity and commodity != CommodityType.UNKNOWN:
            entities.append(ExtractedEntity(
                entity_type="commodity",
                value=commodity.value,
                confidence=commodity_conf,
                start_pos=0,  # Simplified - would need more complex logic for exact positions
                end_pos=len(text)
            ))
        
        # Extract price entities
        price = self.extract_price(text)
        if price:
            entities.append(ExtractedEntity(
                entity_type="price",
                value=f"{price.amount} {price.currency} {price.unit}",
                confidence=price.confidence,
                start_pos=0,
                end_pos=len(text)
            ))
        
        # Extract quantity entities
        quantity = self.extract_quantity(text)
        if quantity:
            entities.append(ExtractedEntity(
                entity_type="quantity",
                value=f"{quantity.amount} {quantity.unit}",
                confidence=quantity.confidence,
                start_pos=0,
                end_pos=len(text)
            ))
        
        # Extract location entities
        location = self.extract_location(text)
        if location:
            entities.append(ExtractedEntity(
                entity_type="location",
                value=f"{location.name} ({location.type})",
                confidence=location.confidence,
                start_pos=0,
                end_pos=len(text)
            ))
        
        return entities
    
    def analyze_conversation(self, text: str) -> ConversationAnalysis:
        """
        Complete conversation analysis pipeline
        
        Args:
            text: Input conversation text
            
        Returns:
            ConversationAnalysis with all extracted information
        """
        try:
            logger.debug("Starting conversation analysis", text_length=len(text))
            
            # Extract all components
            commodity, commodity_confidence = self.extract_commodity(text)
            price = self.extract_price(text)
            quantity = self.extract_quantity(text)
            location = self.extract_location(text)
            intent, intent_confidence = self.classify_intent(text)
            entities = self.extract_all_entities(text)
            
            # Calculate overall confidence
            confidence_scores = [intent_confidence, commodity_confidence]
            if price:
                confidence_scores.append(price.confidence)
            if quantity:
                confidence_scores.append(quantity.confidence)
            if location:
                confidence_scores.append(location.confidence)
            
            overall_confidence = np.mean(confidence_scores) if confidence_scores else 0.1
            
            analysis = ConversationAnalysis(
                text=text,
                intent=intent,
                intent_confidence=intent_confidence,
                commodity=commodity,
                commodity_confidence=commodity_confidence,
                price=price,
                quantity=quantity,
                location=location,
                entities=entities,
                overall_confidence=overall_confidence
            )
            
            logger.info("Conversation analysis completed", 
                       intent=intent.value,
                       commodity=commodity.value if commodity else None,
                       entities_count=len(entities),
                       overall_confidence=overall_confidence)
            
            return analysis
            
        except Exception as e:
            logger.error("Conversation analysis failed", error=str(e))
            # Return minimal analysis on error
            return ConversationAnalysis(
                text=text,
                intent=Intent.UNKNOWN,
                intent_confidence=0.0,
                commodity=None,
                commodity_confidence=0.0,
                price=None,
                quantity=None,
                location=None,
                entities=[],
                overall_confidence=0.0
            )