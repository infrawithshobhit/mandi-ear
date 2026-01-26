"""
Buyer Intent Detector for Negotiation Intelligence Service
Analyzes buyer behavior and negotiation patterns
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from models import BuyerIntent, UrgencyLevel

logger = logging.getLogger(__name__)

class BuyerIntentDetector:
    """Detects buyer intent from conversation data and behavior patterns"""
    
    def __init__(self):
        self.urgency_keywords = {
            'high': ['urgent', 'immediately', 'today', 'now', 'asap', 'quick', 'fast', 'hurry'],
            'medium': ['soon', 'this week', 'few days', 'tomorrow', 'next'],
            'low': ['sometime', 'eventually', 'when possible', 'no rush', 'flexible']
        }
        
        self.price_sensitivity_keywords = {
            'high': ['cheap', 'lowest price', 'discount', 'bargain', 'budget', 'cost-effective'],
            'medium': ['reasonable', 'fair price', 'market rate', 'competitive'],
            'low': ['premium', 'quality', 'best', 'top grade', 'willing to pay']
        }
        
        self.quality_focus_keywords = {
            'high': ['quality', 'grade', 'premium', 'best', 'top', 'excellent', 'superior'],
            'medium': ['good', 'standard', 'decent', 'acceptable'],
            'low': ['any', 'basic', 'minimum', 'whatever available']
        }
        
        self.negotiation_style_keywords = {
            'aggressive': ['final offer', 'take it or leave it', 'non-negotiable', 'firm', 'fixed'],
            'collaborative': ['work together', 'mutual benefit', 'partnership', 'long-term'],
            'passive': ['whatever you think', 'up to you', 'flexible', 'open to suggestions']
        }
    
    async def detect_buyer_intent(self, conversation_data: str) -> BuyerIntent:
        """
        Detect buyer intent from conversation data
        
        Args:
            conversation_data: Raw conversation text or structured data
            
        Returns:
            BuyerIntent: Detected buyer intent with confidence scores
        """
        try:
            # Parse conversation data
            conversation_text = self._extract_text(conversation_data)
            
            # Detect urgency level
            urgency = self._detect_urgency(conversation_text)
            
            # Detect price sensitivity
            price_sensitivity = self._detect_price_sensitivity(conversation_text)
            
            # Detect quality focus
            quality_focus = self._detect_quality_focus(conversation_text)
            
            # Extract volume requirement
            volume_requirement = self._extract_volume_requirement(conversation_text)
            
            # Detect negotiation style
            negotiation_style = self._detect_negotiation_style(conversation_text)
            
            # Detect budget constraints
            budget_constraint = self._detect_budget_constraint(conversation_text)
            
            # Count alternative sources mentioned
            alternative_sources = self._count_alternative_sources(conversation_text)
            
            # Assess relationship value
            relationship_value = self._assess_relationship_value(conversation_text)
            
            # Check if repeat buyer
            repeat_buyer = self._check_repeat_buyer(conversation_text)
            
            # Assess payment terms flexibility
            payment_flexibility = self._assess_payment_flexibility(conversation_text)
            
            # Calculate overall confidence
            confidence = self._calculate_confidence(conversation_text)
            
            return BuyerIntent(
                urgency=urgency,
                price_sensitivity=price_sensitivity,
                quality_focus=quality_focus,
                volume_requirement=volume_requirement,
                negotiation_style=negotiation_style,
                budget_constraint=budget_constraint,
                alternative_sources=alternative_sources,
                relationship_value=relationship_value,
                repeat_buyer=repeat_buyer,
                payment_terms_flexibility=payment_flexibility,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Buyer intent detection failed: {str(e)}")
            # Return default intent
            return BuyerIntent(
                urgency=UrgencyLevel.MEDIUM,
                price_sensitivity=0.5,
                quality_focus=0.5,
                volume_requirement=100.0,
                negotiation_style="collaborative",
                alternative_sources=1,
                relationship_value=0.5,
                repeat_buyer=False,
                payment_terms_flexibility=0.5,
                confidence=0.3
            )
    
    def _extract_text(self, conversation_data: str) -> str:
        """Extract text from conversation data"""
        try:
            # Try to parse as JSON first
            data = json.loads(conversation_data)
            if isinstance(data, dict):
                return data.get('text', '') or data.get('transcription', '') or str(data)
            elif isinstance(data, list):
                return ' '.join([str(item) for item in data])
            else:
                return str(data)
        except json.JSONDecodeError:
            # Treat as plain text
            return conversation_data.lower()
    
    def _detect_urgency(self, text: str) -> UrgencyLevel:
        """Detect urgency level from conversation text"""
        text_lower = text.lower()
        
        # Count urgency indicators
        high_count = sum(1 for keyword in self.urgency_keywords['high'] if keyword in text_lower)
        medium_count = sum(1 for keyword in self.urgency_keywords['medium'] if keyword in text_lower)
        low_count = sum(1 for keyword in self.urgency_keywords['low'] if keyword in text_lower)
        
        # Determine urgency level
        if high_count > medium_count and high_count > low_count:
            return UrgencyLevel.HIGH
        elif low_count > medium_count and low_count > high_count:
            return UrgencyLevel.LOW
        else:
            return UrgencyLevel.MEDIUM
    
    def _detect_price_sensitivity(self, text: str) -> float:
        """Detect price sensitivity (0.0 = low sensitivity, 1.0 = high sensitivity)"""
        text_lower = text.lower()
        
        high_count = sum(1 for keyword in self.price_sensitivity_keywords['high'] if keyword in text_lower)
        medium_count = sum(1 for keyword in self.price_sensitivity_keywords['medium'] if keyword in text_lower)
        low_count = sum(1 for keyword in self.price_sensitivity_keywords['low'] if keyword in text_lower)
        
        total_count = high_count + medium_count + low_count
        
        if total_count == 0:
            return 0.5  # Default medium sensitivity
        
        # Calculate weighted score
        score = (high_count * 1.0 + medium_count * 0.5 + low_count * 0.0) / total_count
        return score
    
    def _detect_quality_focus(self, text: str) -> float:
        """Detect quality focus (0.0 = low focus, 1.0 = high focus)"""
        text_lower = text.lower()
        
        high_count = sum(1 for keyword in self.quality_focus_keywords['high'] if keyword in text_lower)
        medium_count = sum(1 for keyword in self.quality_focus_keywords['medium'] if keyword in text_lower)
        low_count = sum(1 for keyword in self.quality_focus_keywords['low'] if keyword in text_lower)
        
        total_count = high_count + medium_count + low_count
        
        if total_count == 0:
            return 0.5  # Default medium focus
        
        # Calculate weighted score
        score = (high_count * 1.0 + medium_count * 0.5 + low_count * 0.0) / total_count
        return score
    
    def _extract_volume_requirement(self, text: str) -> float:
        """Extract volume requirement from text"""
        # Look for quantity patterns
        quantity_patterns = [
            r'(\d+)\s*(quintal|kg|ton|tonnes?)',
            r'(\d+)\s*(bags?|sacks?)',
            r'(\d+)\s*(units?|pieces?)'
        ]
        
        quantities = []
        for pattern in quantity_patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                try:
                    quantity = float(match[0])
                    unit = match[1]
                    
                    # Convert to standard unit (quintals)
                    if 'kg' in unit:
                        quantity = quantity / 100
                    elif 'ton' in unit:
                        quantity = quantity * 10
                    elif 'bag' in unit or 'sack' in unit:
                        quantity = quantity * 0.5  # Assume 50kg bags
                    
                    quantities.append(quantity)
                except ValueError:
                    continue
        
        if quantities:
            return max(quantities)  # Return the largest quantity mentioned
        
        return 100.0  # Default volume
    
    def _detect_negotiation_style(self, text: str) -> str:
        """Detect negotiation style from conversation"""
        text_lower = text.lower()
        
        aggressive_count = sum(1 for keyword in self.negotiation_style_keywords['aggressive'] if keyword in text_lower)
        collaborative_count = sum(1 for keyword in self.negotiation_style_keywords['collaborative'] if keyword in text_lower)
        passive_count = sum(1 for keyword in self.negotiation_style_keywords['passive'] if keyword in text_lower)
        
        # Determine style based on highest count
        if aggressive_count > collaborative_count and aggressive_count > passive_count:
            return "aggressive"
        elif passive_count > collaborative_count and passive_count > aggressive_count:
            return "passive"
        else:
            return "collaborative"
    
    def _detect_budget_constraint(self, text: str) -> Optional[float]:
        """Detect budget constraints from conversation"""
        # Look for budget patterns
        budget_patterns = [
            r'budget.*?(\d+)',
            r'maximum.*?(\d+)',
            r'can.*?pay.*?(\d+)',
            r'afford.*?(\d+)'
        ]
        
        for pattern in budget_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                try:
                    return float(matches[0])
                except ValueError:
                    continue
        
        return None
    
    def _count_alternative_sources(self, text: str) -> int:
        """Count alternative sources mentioned"""
        alternative_indicators = [
            'other seller', 'another farmer', 'different supplier',
            'elsewhere', 'other option', 'alternative'
        ]
        
        count = sum(1 for indicator in alternative_indicators if indicator in text.lower())
        return max(count, 1)  # At least 1 alternative assumed
    
    def _assess_relationship_value(self, text: str) -> float:
        """Assess the value of long-term relationship"""
        relationship_indicators = [
            'long-term', 'partnership', 'regular buyer', 'trusted',
            'relationship', 'future business', 'ongoing'
        ]
        
        count = sum(1 for indicator in relationship_indicators if indicator in text.lower())
        
        # Convert count to score (0.0 to 1.0)
        return min(count * 0.3, 1.0)
    
    def _check_repeat_buyer(self, text: str) -> bool:
        """Check if buyer is a repeat customer"""
        repeat_indicators = [
            'again', 'regular', 'usual', 'as before',
            'same as last time', 'repeat order'
        ]
        
        return any(indicator in text.lower() for indicator in repeat_indicators)
    
    def _assess_payment_flexibility(self, text: str) -> float:
        """Assess payment terms flexibility"""
        flexible_indicators = [
            'flexible payment', 'installment', 'credit', 'advance',
            'partial payment', 'payment terms'
        ]
        
        rigid_indicators = [
            'cash only', 'immediate payment', 'upfront',
            'no credit', 'cash on delivery'
        ]
        
        flexible_count = sum(1 for indicator in flexible_indicators if indicator in text.lower())
        rigid_count = sum(1 for indicator in rigid_indicators if indicator in text.lower())
        
        if rigid_count > flexible_count:
            return 0.2  # Low flexibility
        elif flexible_count > 0:
            return 0.8  # High flexibility
        else:
            return 0.5  # Medium flexibility
    
    def _calculate_confidence(self, text: str) -> float:
        """Calculate overall confidence in intent detection"""
        # Factors that increase confidence
        confidence_factors = [
            len(text) > 50,  # Sufficient text length
            any(keyword in text.lower() for keyword in 
                self.urgency_keywords['high'] + self.urgency_keywords['medium'] + self.urgency_keywords['low']),
            any(keyword in text.lower() for keyword in 
                self.price_sensitivity_keywords['high'] + self.price_sensitivity_keywords['medium'] + self.price_sensitivity_keywords['low']),
            re.search(r'\d+', text) is not None,  # Contains numbers
            len(text.split()) > 10  # Sufficient word count
        ]
        
        confidence = sum(confidence_factors) / len(confidence_factors)
        return max(0.3, confidence)  # Minimum 30% confidence