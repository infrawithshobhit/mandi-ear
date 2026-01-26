"""
Cultural Context Awareness System for MANDI EAR™
Handles cultural nuances, social contexts, and regional variations
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, date
import calendar
import os
import sys

# Add the current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from language_detector import LanguageCode
except ImportError:
    # Fallback for when running tests
    class LanguageCode(str, Enum):
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

logger = logging.getLogger(__name__)

class SocialContext(str, Enum):
    """Social context types"""
    FORMAL_BUSINESS = "formal_business"
    INFORMAL_MARKET = "informal_market"
    FAMILY_DISCUSSION = "family_discussion"
    COMMUNITY_MEETING = "community_meeting"
    GOVERNMENT_INTERACTION = "government_interaction"

class RegionalContext(str, Enum):
    """Regional context types"""
    NORTH_INDIA = "north_india"
    SOUTH_INDIA = "south_india"
    EAST_INDIA = "east_india"
    WEST_INDIA = "west_india"
    CENTRAL_INDIA = "central_india"
    NORTHEAST_INDIA = "northeast_india"

class CulturalSensitivity(str, Enum):
    """Cultural sensitivity levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class CulturalProfile:
    """Cultural profile for user context"""
    language: LanguageCode
    region: RegionalContext
    social_context: SocialContext
    sensitivity_level: CulturalSensitivity
    religious_context: Optional[str] = None
    caste_considerations: bool = False
    gender_context: Optional[str] = None
    age_group: Optional[str] = None

@dataclass
class CulturalAdaptation:
    """Cultural adaptation result"""
    original_text: str
    adapted_text: str
    adaptations_applied: List[str]
    confidence: float
    cultural_notes: List[str]

class CulturalContextSystem:
    """Advanced cultural context awareness system"""
    
    def __init__(self):
        self.regional_patterns = self._initialize_regional_patterns()
        self.social_hierarchies = self._initialize_social_hierarchies()
        self.festival_calendar = self._initialize_festival_calendar()
        self.agricultural_calendar = self._initialize_agricultural_calendar()
        self.respectful_communication = self._initialize_respectful_communication()
        self.taboo_topics = self._initialize_taboo_topics()
        self.regional_dialects = self._initialize_regional_dialects()
    
    def _initialize_regional_patterns(self) -> Dict[RegionalContext, Dict[str, Any]]:
        """Initialize regional cultural patterns"""
        return {
            RegionalContext.NORTH_INDIA: {
                "languages": [LanguageCode.HINDI, LanguageCode.PUNJABI, LanguageCode.URDU],
                "greeting_style": "formal_respectful",
                "business_approach": "relationship_first",
                "negotiation_style": "direct_but_respectful",
                "time_orientation": "flexible",
                "hierarchy_importance": "high",
                "family_involvement": "high",
                "seasonal_priorities": ["rabi", "kharif"],
                "major_crops": ["wheat", "rice", "sugarcane", "cotton"],
                "traditional_units": ["quintal", "maund", "bigha"],
                "cultural_values": ["respect_for_elders", "joint_family", "hospitality"]
            },
            RegionalContext.SOUTH_INDIA: {
                "languages": [LanguageCode.TELUGU, LanguageCode.TAMIL, LanguageCode.KANNADA, LanguageCode.MALAYALAM],
                "greeting_style": "traditional_formal",
                "business_approach": "education_valued",
                "negotiation_style": "analytical_detailed",
                "time_orientation": "punctual",
                "hierarchy_importance": "medium",
                "family_involvement": "high",
                "seasonal_priorities": ["kharif", "rabi"],
                "major_crops": ["rice", "cotton", "groundnut", "coconut"],
                "traditional_units": ["kg", "acre"],
                "cultural_values": ["education", "tradition", "temple_culture"]
            },
            RegionalContext.EAST_INDIA: {
                "languages": [LanguageCode.BENGALI, LanguageCode.ODIA, LanguageCode.ASSAMESE],
                "greeting_style": "warm_personal",
                "business_approach": "intellectual_discussion",
                "negotiation_style": "consensus_building",
                "time_orientation": "relaxed",
                "hierarchy_importance": "medium",
                "family_involvement": "very_high",
                "seasonal_priorities": ["kharif", "boro"],
                "major_crops": ["rice", "jute", "tea", "fish"],
                "traditional_units": ["kg", "bigha", "katha"],
                "cultural_values": ["art_culture", "intellectual_discourse", "fish_rice_culture"]
            },
            RegionalContext.WEST_INDIA: {
                "languages": [LanguageCode.GUJARATI, LanguageCode.MARATHI],
                "greeting_style": "business_friendly",
                "business_approach": "profit_oriented",
                "negotiation_style": "shrewd_practical",
                "time_orientation": "time_conscious",
                "hierarchy_importance": "medium",
                "family_involvement": "medium",
                "seasonal_priorities": ["kharif", "rabi"],
                "major_crops": ["cotton", "sugarcane", "groundnut", "wheat"],
                "traditional_units": ["quintal", "acre"],
                "cultural_values": ["business_acumen", "entrepreneurship", "community_cooperation"]
            }
        }
    
    def _initialize_social_hierarchies(self) -> Dict[LanguageCode, Dict[str, Any]]:
        """Initialize social hierarchy patterns"""
        return {
            LanguageCode.HINDI: {
                "respectful_pronouns": {
                    "you_formal": "आप",
                    "you_informal": "तुम",
                    "you_intimate": "तू"
                },
                "honorifics": {
                    "general": ["जी", "साहब", "मैडम"],
                    "elderly": ["बाबूजी", "मातजी", "दादाजी", "दादीजी"],
                    "professional": ["डॉक्टर साहब", "इंजीनियर साहब", "अधिकारी जी"],
                    "farmer": ["किसान भाई", "खेतिहर भाई"]
                },
                "age_based_address": {
                    "older_male": "भाई साहब",
                    "older_female": "बहन जी",
                    "elderly_male": "चाचा जी",
                    "elderly_female": "आंटी जी"
                }
            },
            LanguageCode.ENGLISH: {
                "respectful_pronouns": {
                    "you_formal": "you",
                    "you_informal": "you",
                    "you_intimate": "you"
                },
                "honorifics": {
                    "general": ["sir", "madam", "ji"],
                    "elderly": ["uncle", "aunty", "elder"],
                    "professional": ["doctor", "engineer", "officer"],
                    "farmer": ["farmer", "grower"]
                }
            }
        }
    
    def _initialize_festival_calendar(self) -> Dict[str, Dict[str, Any]]:
        """Initialize festival calendar with cultural significance"""
        return {
            "diwali": {
                "months": [10, 11],  # October-November
                "significance": "wealth_prosperity",
                "agricultural_relevance": "post_harvest_celebration",
                "business_impact": "high_spending",
                "regional_variations": {
                    RegionalContext.NORTH_INDIA: "lakshmi_worship",
                    RegionalContext.SOUTH_INDIA: "naraka_chaturdashi",
                    RegionalContext.EAST_INDIA: "kali_puja",
                    RegionalContext.WEST_INDIA: "dhanteras_focus"
                }
            },
            "holi": {
                "months": [3, 4],  # March-April
                "significance": "spring_harvest",
                "agricultural_relevance": "rabi_harvest_time",
                "business_impact": "moderate",
                "regional_variations": {
                    RegionalContext.NORTH_INDIA: "radha_krishna_celebration",
                    RegionalContext.WEST_INDIA: "rangpanchami"
                }
            },
            "dussehra": {
                "months": [9, 10],  # September-October
                "significance": "good_over_evil",
                "agricultural_relevance": "kharif_harvest_preparation",
                "business_impact": "moderate",
                "regional_variations": {
                    RegionalContext.SOUTH_INDIA: "navaratri_focus",
                    RegionalContext.EAST_INDIA: "durga_puja",
                    RegionalContext.NORTH_INDIA: "ram_leela"
                }
            }
        }
    
    def _initialize_agricultural_calendar(self) -> Dict[str, Dict[str, Any]]:
        """Initialize agricultural calendar with cultural context"""
        return {
            "kharif": {
                "sowing_months": [6, 7, 8],  # June-August
                "harvest_months": [10, 11, 12],  # October-December
                "cultural_significance": "monsoon_dependency",
                "festivals_associated": ["teej", "raksha_bandhan"],
                "regional_crops": {
                    RegionalContext.NORTH_INDIA: ["rice", "cotton", "sugarcane"],
                    RegionalContext.SOUTH_INDIA: ["rice", "cotton", "groundnut"],
                    RegionalContext.EAST_INDIA: ["rice", "jute"],
                    RegionalContext.WEST_INDIA: ["cotton", "sugarcane", "soybean"]
                }
            },
            "rabi": {
                "sowing_months": [11, 12, 1],  # November-January
                "harvest_months": [3, 4, 5],  # March-May
                "cultural_significance": "winter_crop_prosperity",
                "festivals_associated": ["makar_sankranti", "holi"],
                "regional_crops": {
                    RegionalContext.NORTH_INDIA: ["wheat", "barley", "mustard"],
                    RegionalContext.SOUTH_INDIA: ["wheat", "gram", "sunflower"],
                    RegionalContext.EAST_INDIA: ["wheat", "potato", "mustard"],
                    RegionalContext.WEST_INDIA: ["wheat", "gram", "cotton"]
                }
            }
        }
    
    def _initialize_respectful_communication(self) -> Dict[LanguageCode, Dict[str, Any]]:
        """Initialize respectful communication patterns"""
        return {
            LanguageCode.HINDI: {
                "opening_phrases": [
                    "नमस्ते जी",
                    "आदाब",
                    "सत श्री अकाल" # For Punjabi speakers
                ],
                "polite_requests": [
                    "कृपया",
                    "मेहरबानी करके",
                    "अगर आप की अनुमति हो तो"
                ],
                "closing_phrases": [
                    "धन्यवाद जी",
                    "आपका बहुत-बहुत धन्यवाद",
                    "जय हिंद"
                ],
                "agreement_phrases": [
                    "जी हाँ",
                    "बिल्कुल सही",
                    "आप सही कह रहे हैं"
                ],
                "disagreement_phrases": [
                    "माफ करिए, लेकिन",
                    "शायद",
                    "मेरे विचार से"
                ]
            },
            LanguageCode.ENGLISH: {
                "opening_phrases": [
                    "Good morning",
                    "Namaste",
                    "Greetings"
                ],
                "polite_requests": [
                    "Please",
                    "If you don't mind",
                    "Could you kindly"
                ],
                "closing_phrases": [
                    "Thank you",
                    "Much appreciated",
                    "Have a good day"
                ],
                "agreement_phrases": [
                    "Yes, absolutely",
                    "That's correct",
                    "I agree"
                ],
                "disagreement_phrases": [
                    "I respectfully disagree",
                    "Perhaps",
                    "In my opinion"
                ]
            }
        }
    
    def _initialize_taboo_topics(self) -> Dict[RegionalContext, List[str]]:
        """Initialize culturally sensitive topics to handle carefully"""
        return {
            RegionalContext.NORTH_INDIA: [
                "caste_discrimination",
                "religious_conflicts",
                "gender_inequality",
                "dowry_system"
            ],
            RegionalContext.SOUTH_INDIA: [
                "language_politics",
                "caste_issues",
                "regional_autonomy",
                "water_disputes"
            ],
            RegionalContext.EAST_INDIA: [
                "political_violence",
                "migration_issues",
                "cultural_identity",
                "economic_disparity"
            ],
            RegionalContext.WEST_INDIA: [
                "business_ethics",
                "environmental_concerns",
                "urbanization_impact",
                "traditional_vs_modern"
            ]
        }
    
    def _initialize_regional_dialects(self) -> Dict[LanguageCode, Dict[RegionalContext, Dict[str, str]]]:
        """Initialize regional dialect variations"""
        return {
            LanguageCode.HINDI: {
                RegionalContext.NORTH_INDIA: {
                    "water": "पानी",
                    "food": "खाना",
                    "money": "पैसा",
                    "market": "बाजार"
                },
                RegionalContext.CENTRAL_INDIA: {
                    "water": "पानी",
                    "food": "खाना",
                    "money": "रुपया",
                    "market": "मंडी"
                }
            }
        }
    
    async def analyze_cultural_context(
        self,
        text: str,
        user_profile: CulturalProfile
    ) -> Dict[str, Any]:
        """Analyze cultural context from text and user profile"""
        try:
            context_analysis = {
                "social_context": await self._detect_social_context(text),
                "formality_level": await self._assess_formality_level(text, user_profile.language),
                "cultural_references": await self._identify_cultural_references(text),
                "seasonal_context": await self._detect_seasonal_context(text),
                "business_context": await self._detect_business_context(text),
                "sensitivity_flags": await self._check_sensitivity_flags(text, user_profile.region)
            }
            
            return context_analysis
            
        except Exception as e:
            logger.error(f"Cultural context analysis failed: {e}")
            return {}
    
    async def adapt_communication(
        self,
        text: str,
        user_profile: CulturalProfile,
        target_context: Optional[SocialContext] = None
    ) -> CulturalAdaptation:
        """Adapt communication based on cultural context"""
        try:
            adaptations_applied = []
            adapted_text = text
            cultural_notes = []
            
            # Apply regional adaptations
            regional_patterns = self.regional_patterns.get(user_profile.region, {})
            
            # Apply social hierarchy adaptations
            if user_profile.sensitivity_level == CulturalSensitivity.HIGH:
                adapted_text, hierarchy_adaptations = await self._apply_hierarchy_adaptations(
                    adapted_text, user_profile
                )
                adaptations_applied.extend(hierarchy_adaptations)
            
            # Apply respectful communication patterns
            adapted_text, respect_adaptations = await self._apply_respectful_patterns(
                adapted_text, user_profile.language
            )
            adaptations_applied.extend(respect_adaptations)
            
            # Apply regional dialect adaptations
            adapted_text, dialect_adaptations = await self._apply_dialect_adaptations(
                adapted_text, user_profile
            )
            adaptations_applied.extend(dialect_adaptations)
            
            # Check for cultural sensitivity
            sensitivity_notes = await self._check_cultural_sensitivity(
                adapted_text, user_profile
            )
            cultural_notes.extend(sensitivity_notes)
            
            confidence = 0.9 if adaptations_applied else 0.7
            
            return CulturalAdaptation(
                original_text=text,
                adapted_text=adapted_text,
                adaptations_applied=adaptations_applied,
                confidence=confidence,
                cultural_notes=cultural_notes
            )
            
        except Exception as e:
            logger.error(f"Cultural adaptation failed: {e}")
            return CulturalAdaptation(
                original_text=text,
                adapted_text=text,
                adaptations_applied=[],
                confidence=0.5,
                cultural_notes=["Adaptation failed, using original text"]
            )
    
    async def _detect_social_context(self, text: str) -> SocialContext:
        """Detect social context from text"""
        text_lower = text.lower()
        
        # Business context indicators
        business_terms = ["price", "rate", "deal", "contract", "business", "profit", "loss"]
        if any(term in text_lower for term in business_terms):
            return SocialContext.FORMAL_BUSINESS
        
        # Government context indicators
        govt_terms = ["officer", "department", "scheme", "subsidy", "policy", "government"]
        if any(term in text_lower for term in govt_terms):
            return SocialContext.GOVERNMENT_INTERACTION
        
        # Family context indicators
        family_terms = ["family", "home", "children", "wife", "husband", "father", "mother"]
        if any(term in text_lower for term in family_terms):
            return SocialContext.FAMILY_DISCUSSION
        
        # Default to informal market
        return SocialContext.INFORMAL_MARKET
    
    async def _assess_formality_level(self, text: str, language: LanguageCode) -> str:
        """Assess formality level of text"""
        hierarchy_patterns = self.social_hierarchies.get(language, {})
        
        # Check for formal pronouns and honorifics
        formal_indicators = hierarchy_patterns.get("honorifics", {}).get("general", [])
        formal_pronouns = [hierarchy_patterns.get("respectful_pronouns", {}).get("you_formal", "")]
        
        text_lower = text.lower()
        formal_count = sum(1 for indicator in formal_indicators + formal_pronouns 
                          if indicator.lower() in text_lower)
        
        if formal_count >= 2:
            return "high"
        elif formal_count == 1:
            return "medium"
        else:
            return "low"
    
    async def _identify_cultural_references(self, text: str) -> List[str]:
        """Identify cultural references in text"""
        references = []
        text_lower = text.lower()
        
        # Check for festival references
        for festival, details in self.festival_calendar.items():
            if festival in text_lower:
                references.append(f"festival:{festival}")
        
        # Check for agricultural season references
        for season, details in self.agricultural_calendar.items():
            if season in text_lower:
                references.append(f"season:{season}")
        
        return references
    
    async def _detect_seasonal_context(self, text: str) -> Optional[str]:
        """Detect seasonal context from text"""
        current_month = datetime.now().month
        
        # Check which agricultural season we're in
        for season, details in self.agricultural_calendar.items():
            sowing_months = details.get("sowing_months", [])
            harvest_months = details.get("harvest_months", [])
            
            if current_month in sowing_months:
                return f"{season}_sowing"
            elif current_month in harvest_months:
                return f"{season}_harvest"
        
        return None
    
    async def _detect_business_context(self, text: str) -> Dict[str, Any]:
        """Detect business context indicators"""
        text_lower = text.lower()
        
        context = {
            "is_negotiation": any(term in text_lower for term in ["negotiate", "bargain", "deal", "offer"]),
            "is_price_inquiry": any(term in text_lower for term in ["price", "rate", "cost", "how much"]),
            "is_quality_discussion": any(term in text_lower for term in ["quality", "grade", "condition"]),
            "urgency_level": "low"
        }
        
        # Assess urgency
        urgent_terms = ["urgent", "immediate", "quickly", "fast", "emergency"]
        if any(term in text_lower for term in urgent_terms):
            context["urgency_level"] = "high"
        elif any(term in text_lower for term in ["soon", "today", "tomorrow"]):
            context["urgency_level"] = "medium"
        
        return context
    
    async def _check_sensitivity_flags(self, text: str, region: RegionalContext) -> List[str]:
        """Check for culturally sensitive topics"""
        flags = []
        text_lower = text.lower()
        
        taboo_topics = self.taboo_topics.get(region, [])
        
        for topic in taboo_topics:
            topic_keywords = topic.split("_")
            if any(keyword in text_lower for keyword in topic_keywords):
                flags.append(f"sensitive_topic:{topic}")
        
        return flags
    
    async def _apply_hierarchy_adaptations(
        self,
        text: str,
        user_profile: CulturalProfile
    ) -> Tuple[str, List[str]]:
        """Apply social hierarchy adaptations"""
        adaptations = []
        adapted_text = text
        
        hierarchy_patterns = self.social_hierarchies.get(user_profile.language, {})
        
        # Add respectful pronouns
        informal_you = hierarchy_patterns.get("respectful_pronouns", {}).get("you_informal", "")
        formal_you = hierarchy_patterns.get("respectful_pronouns", {}).get("you_formal", "")
        
        if informal_you and formal_you and informal_you in adapted_text:
            adapted_text = adapted_text.replace(informal_you, formal_you)
            adaptations.append("formal_pronoun_substitution")
        
        return adapted_text, adaptations
    
    async def _apply_respectful_patterns(
        self,
        text: str,
        language: LanguageCode
    ) -> Tuple[str, List[str]]:
        """Apply respectful communication patterns"""
        adaptations = []
        adapted_text = text
        
        respectful_patterns = self.respectful_communication.get(language, {})
        
        # Add polite opening if missing
        opening_phrases = respectful_patterns.get("opening_phrases", [])
        if opening_phrases and not any(phrase.lower() in text.lower() for phrase in opening_phrases):
            adapted_text = f"{opening_phrases[0]} {adapted_text}"
            adaptations.append("polite_opening_added")
        
        return adapted_text, adaptations
    
    async def _apply_dialect_adaptations(
        self,
        text: str,
        user_profile: CulturalProfile
    ) -> Tuple[str, List[str]]:
        """Apply regional dialect adaptations"""
        adaptations = []
        adapted_text = text
        
        dialect_patterns = self.regional_dialects.get(user_profile.language, {})
        regional_dialect = dialect_patterns.get(user_profile.region, {})
        
        # Apply dialect substitutions
        for standard_word, dialect_word in regional_dialect.items():
            if standard_word in adapted_text and standard_word != dialect_word:
                adapted_text = adapted_text.replace(standard_word, dialect_word)
                adaptations.append(f"dialect_substitution:{standard_word}->{dialect_word}")
        
        return adapted_text, adaptations
    
    async def _check_cultural_sensitivity(
        self,
        text: str,
        user_profile: CulturalProfile
    ) -> List[str]:
        """Check for cultural sensitivity issues"""
        notes = []
        
        # Check for potential sensitivity issues
        sensitivity_flags = await self._check_sensitivity_flags(text, user_profile.region)
        
        if sensitivity_flags:
            notes.append("Contains culturally sensitive topics - handle with care")
        
        # Check formality level appropriateness
        formality = await self._assess_formality_level(text, user_profile.language)
        if user_profile.sensitivity_level == CulturalSensitivity.HIGH and formality == "low":
            notes.append("Consider increasing formality level for this user")
        
        return notes