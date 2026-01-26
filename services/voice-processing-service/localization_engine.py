"""
Localization Engine for MANDI EAR™
Handles currency, units, and cultural context localization
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime
import json

from .language_detector import LanguageCode

logger = logging.getLogger(__name__)

class CurrencyFormat(str, Enum):
    """Currency format styles"""
    SYMBOL_BEFORE = "symbol_before"  # ₹100
    SYMBOL_AFTER = "symbol_after"    # 100₹
    WORD_AFTER = "word_after"        # 100 रुपये
    ABBREVIATED = "abbreviated"      # Rs. 100

class UnitSystem(str, Enum):
    """Unit system types"""
    METRIC = "metric"
    IMPERIAL = "imperial"
    TRADITIONAL = "traditional"

@dataclass
class LocalizationContext:
    """Context for localization"""
    language: LanguageCode
    region: Optional[str] = None
    user_preferences: Optional[Dict[str, Any]] = None
    cultural_context: Optional[Dict[str, Any]] = None

@dataclass
class LocalizedValue:
    """Localized value with formatting"""
    original_value: Any
    localized_text: str
    language: LanguageCode
    format_type: str
    confidence: float = 1.0

class LocalizationEngine:
    """Advanced localization engine for Indian regional contexts"""
    
    def __init__(self):
        self.currency_formats = self._initialize_currency_formats()
        self.unit_conversions = self._initialize_unit_conversions()
        self.number_formats = self._initialize_number_formats()
        self.cultural_patterns = self._initialize_cultural_patterns()
        self.regional_preferences = self._initialize_regional_preferences()
    
    def _initialize_currency_formats(self) -> Dict[LanguageCode, Dict[str, Any]]:
        """Initialize currency formatting rules for different languages"""
        return {
            LanguageCode.HINDI: {
                "symbol": "₹",
                "word_forms": {
                    "singular": "रुपया",
                    "plural": "रुपये",
                    "abbreviated": "रु"
                },
                "formats": {
                    CurrencyFormat.SYMBOL_BEFORE: "₹{amount}",
                    CurrencyFormat.WORD_AFTER: "{amount} रुपये",
                    CurrencyFormat.ABBREVIATED: "{amount} रु"
                },
                "decimal_separator": ".",
                "thousand_separator": ",",
                "preferred_format": CurrencyFormat.WORD_AFTER
            },
            LanguageCode.ENGLISH: {
                "symbol": "₹",
                "word_forms": {
                    "singular": "rupee",
                    "plural": "rupees",
                    "abbreviated": "Rs"
                },
                "formats": {
                    CurrencyFormat.SYMBOL_BEFORE: "₹{amount}",
                    CurrencyFormat.WORD_AFTER: "{amount} rupees",
                    CurrencyFormat.ABBREVIATED: "Rs. {amount}"
                },
                "decimal_separator": ".",
                "thousand_separator": ",",
                "preferred_format": CurrencyFormat.ABBREVIATED
            },
            LanguageCode.BENGALI: {
                "symbol": "₹",
                "word_forms": {
                    "singular": "টাকা",
                    "plural": "টাকা",
                    "abbreviated": "টা"
                },
                "formats": {
                    CurrencyFormat.SYMBOL_BEFORE: "₹{amount}",
                    CurrencyFormat.WORD_AFTER: "{amount} টাকা",
                    CurrencyFormat.ABBREVIATED: "{amount} টা"
                },
                "decimal_separator": ".",
                "thousand_separator": ",",
                "preferred_format": CurrencyFormat.WORD_AFTER
            },
            LanguageCode.TELUGU: {
                "symbol": "₹",
                "word_forms": {
                    "singular": "రూపాయి",
                    "plural": "రూపాయలు",
                    "abbreviated": "రూ"
                },
                "formats": {
                    CurrencyFormat.SYMBOL_BEFORE: "₹{amount}",
                    CurrencyFormat.WORD_AFTER: "{amount} రూపాయలు",
                    CurrencyFormat.ABBREVIATED: "{amount} రూ"
                },
                "decimal_separator": ".",
                "thousand_separator": ",",
                "preferred_format": CurrencyFormat.WORD_AFTER
            },
            LanguageCode.TAMIL: {
                "symbol": "₹",
                "word_forms": {
                    "singular": "ரூபாய்",
                    "plural": "ரூபாய்",
                    "abbreviated": "ரூ"
                },
                "formats": {
                    CurrencyFormat.SYMBOL_BEFORE: "₹{amount}",
                    CurrencyFormat.WORD_AFTER: "{amount} ரூபாய்",
                    CurrencyFormat.ABBREVIATED: "{amount} ரூ"
                },
                "decimal_separator": ".",
                "thousand_separator": ",",
                "preferred_format": CurrencyFormat.WORD_AFTER
            }
        }
    
    def _initialize_unit_conversions(self) -> Dict[LanguageCode, Dict[str, Any]]:
        """Initialize unit conversion and formatting rules"""
        return {
            LanguageCode.HINDI: {
                "weight": {
                    "kg": {"name": "किलो", "plural": "किलो", "conversion": 1.0},
                    "quintal": {"name": "क्विंटल", "plural": "क्विंटल", "conversion": 100.0},
                    "ton": {"name": "टन", "plural": "टन", "conversion": 1000.0},
                    "maund": {"name": "मन", "plural": "मन", "conversion": 37.32}  # Traditional unit
                },
                "area": {
                    "acre": {"name": "एकड़", "plural": "एकड़", "conversion": 1.0},
                    "hectare": {"name": "हेक्टेयर", "plural": "हेक्टेयर", "conversion": 2.47},
                    "bigha": {"name": "बीघा", "plural": "बीघा", "conversion": 0.62}  # Traditional unit
                },
                "volume": {
                    "liter": {"name": "लीटर", "plural": "लीटर", "conversion": 1.0},
                    "gallon": {"name": "गैलन", "plural": "गैलन", "conversion": 3.78}
                }
            },
            LanguageCode.ENGLISH: {
                "weight": {
                    "kg": {"name": "kg", "plural": "kg", "conversion": 1.0},
                    "quintal": {"name": "quintal", "plural": "quintals", "conversion": 100.0},
                    "ton": {"name": "ton", "plural": "tons", "conversion": 1000.0},
                    "maund": {"name": "maund", "plural": "maunds", "conversion": 37.32}
                },
                "area": {
                    "acre": {"name": "acre", "plural": "acres", "conversion": 1.0},
                    "hectare": {"name": "hectare", "plural": "hectares", "conversion": 2.47},
                    "bigha": {"name": "bigha", "plural": "bighas", "conversion": 0.62}
                },
                "volume": {
                    "liter": {"name": "liter", "plural": "liters", "conversion": 1.0},
                    "gallon": {"name": "gallon", "plural": "gallons", "conversion": 3.78}
                }
            },
            LanguageCode.BENGALI: {
                "weight": {
                    "kg": {"name": "কেজি", "plural": "কেজি", "conversion": 1.0},
                    "quintal": {"name": "কুইন্টাল", "plural": "কুইন্টাল", "conversion": 100.0},
                    "ton": {"name": "টন", "plural": "টন", "conversion": 1000.0},
                    "maund": {"name": "মন", "plural": "মন", "conversion": 37.32}
                },
                "area": {
                    "acre": {"name": "একর", "plural": "একর", "conversion": 1.0},
                    "hectare": {"name": "হেক্টর", "plural": "হেক্টর", "conversion": 2.47},
                    "bigha": {"name": "বিঘা", "plural": "বিঘা", "conversion": 0.62}
                }
            }
        }
    
    def _initialize_number_formats(self) -> Dict[LanguageCode, Dict[str, Any]]:
        """Initialize number formatting rules"""
        return {
            LanguageCode.HINDI: {
                "decimal_separator": ".",
                "thousand_separator": ",",
                "lakh_crore_system": True,
                "digit_grouping": "indian",  # 1,23,45,678
                "number_words": {
                    "lakh": "लाख",
                    "crore": "करोड़",
                    "thousand": "हजार"
                }
            },
            LanguageCode.ENGLISH: {
                "decimal_separator": ".",
                "thousand_separator": ",",
                "lakh_crore_system": True,
                "digit_grouping": "indian",
                "number_words": {
                    "lakh": "lakh",
                    "crore": "crore",
                    "thousand": "thousand"
                }
            },
            LanguageCode.BENGALI: {
                "decimal_separator": ".",
                "thousand_separator": ",",
                "lakh_crore_system": True,
                "digit_grouping": "indian",
                "number_words": {
                    "lakh": "লাখ",
                    "crore": "কোটি",
                    "thousand": "হাজার"
                }
            }
        }
    
    def _initialize_cultural_patterns(self) -> Dict[LanguageCode, Dict[str, Any]]:
        """Initialize cultural context patterns"""
        return {
            LanguageCode.HINDI: {
                "festivals": {
                    "diwali": "दीवाली",
                    "holi": "होली",
                    "dussehra": "दशहरा",
                    "karva_chauth": "करवा चौथ"
                },
                "seasons": {
                    "kharif": "खरीफ",
                    "rabi": "रबी",
                    "zaid": "जायद"
                },
                "agricultural_terms": {
                    "sowing": "बुआई",
                    "harvesting": "कटाई",
                    "irrigation": "सिंचाई",
                    "fertilizer": "खाद"
                },
                "respectful_address": {
                    "farmer": "किसान भाई",
                    "trader": "व्यापारी जी",
                    "officer": "अधिकारी जी"
                }
            },
            LanguageCode.ENGLISH: {
                "festivals": {
                    "diwali": "Diwali",
                    "holi": "Holi",
                    "dussehra": "Dussehra",
                    "karva_chauth": "Karva Chauth"
                },
                "seasons": {
                    "kharif": "Kharif",
                    "rabi": "Rabi",
                    "zaid": "Zaid"
                },
                "agricultural_terms": {
                    "sowing": "sowing",
                    "harvesting": "harvesting",
                    "irrigation": "irrigation",
                    "fertilizer": "fertilizer"
                },
                "respectful_address": {
                    "farmer": "farmer",
                    "trader": "trader",
                    "officer": "officer"
                }
            }
        }
    
    def _initialize_regional_preferences(self) -> Dict[str, Dict[str, Any]]:
        """Initialize regional preferences"""
        return {
            "north_india": {
                "preferred_units": ["quintal", "acre", "maund"],
                "currency_format": CurrencyFormat.WORD_AFTER,
                "languages": [LanguageCode.HINDI, LanguageCode.PUNJABI]
            },
            "south_india": {
                "preferred_units": ["kg", "acre"],
                "currency_format": CurrencyFormat.SYMBOL_BEFORE,
                "languages": [LanguageCode.TELUGU, LanguageCode.TAMIL, LanguageCode.KANNADA, LanguageCode.MALAYALAM]
            },
            "east_india": {
                "preferred_units": ["kg", "bigha"],
                "currency_format": CurrencyFormat.WORD_AFTER,
                "languages": [LanguageCode.BENGALI, LanguageCode.ODIA, LanguageCode.ASSAMESE]
            },
            "west_india": {
                "preferred_units": ["quintal", "acre"],
                "currency_format": CurrencyFormat.ABBREVIATED,
                "languages": [LanguageCode.GUJARATI, LanguageCode.MARATHI]
            }
        }
    
    async def localize_currency(
        self,
        amount: float,
        context: LocalizationContext,
        format_style: Optional[CurrencyFormat] = None
    ) -> LocalizedValue:
        """Localize currency amount with proper formatting"""
        try:
            currency_config = self.currency_formats.get(context.language)
            if not currency_config:
                # Fallback to English
                currency_config = self.currency_formats[LanguageCode.ENGLISH]
            
            # Determine format style
            if format_style is None:
                format_style = currency_config["preferred_format"]
            
            # Format the amount with proper number formatting
            formatted_amount = await self._format_number(amount, context)
            
            # Apply currency format
            format_template = currency_config["formats"][format_style]
            localized_text = format_template.format(amount=formatted_amount)
            
            return LocalizedValue(
                original_value=amount,
                localized_text=localized_text,
                language=context.language,
                format_type="currency",
                confidence=1.0
            )
            
        except Exception as e:
            logger.error(f"Currency localization failed: {e}")
            return LocalizedValue(
                original_value=amount,
                localized_text=f"₹{amount}",
                language=context.language,
                format_type="currency",
                confidence=0.5
            )
    
    async def localize_units(
        self,
        value: float,
        unit_type: str,
        unit_name: str,
        context: LocalizationContext
    ) -> LocalizedValue:
        """Localize units with proper conversion and formatting"""
        try:
            unit_config = self.unit_conversions.get(context.language, {})
            unit_category = unit_config.get(unit_type, {})
            
            if unit_name not in unit_category:
                # Fallback to English
                unit_config = self.unit_conversions[LanguageCode.ENGLISH]
                unit_category = unit_config.get(unit_type, {})
            
            if unit_name in unit_category:
                unit_info = unit_category[unit_name]
                localized_unit = unit_info["plural"] if value != 1 else unit_info["name"]
                
                # Format the number
                formatted_value = await self._format_number(value, context)
                
                localized_text = f"{formatted_value} {localized_unit}"
                
                return LocalizedValue(
                    original_value=f"{value} {unit_name}",
                    localized_text=localized_text,
                    language=context.language,
                    format_type="unit",
                    confidence=1.0
                )
            else:
                # Unit not found, return as-is
                return LocalizedValue(
                    original_value=f"{value} {unit_name}",
                    localized_text=f"{value} {unit_name}",
                    language=context.language,
                    format_type="unit",
                    confidence=0.3
                )
                
        except Exception as e:
            logger.error(f"Unit localization failed: {e}")
            return LocalizedValue(
                original_value=f"{value} {unit_name}",
                localized_text=f"{value} {unit_name}",
                language=context.language,
                format_type="unit",
                confidence=0.5
            )
    
    async def _format_number(self, number: float, context: LocalizationContext) -> str:
        """Format number according to regional preferences"""
        try:
            number_config = self.number_formats.get(context.language, {})
            
            # Handle Indian numbering system (lakh, crore)
            if number_config.get("lakh_crore_system", False):
                return await self._format_indian_number(number, number_config)
            else:
                return await self._format_standard_number(number, number_config)
                
        except Exception as e:
            logger.warning(f"Number formatting failed: {e}")
            return str(number)
    
    async def _format_indian_number(self, number: float, config: Dict[str, Any]) -> str:
        """Format number using Indian numbering system"""
        if number >= 10000000:  # 1 crore
            crores = number / 10000000
            crore_word = config.get("number_words", {}).get("crore", "crore")
            if crores >= 1:
                return f"{crores:.1f} {crore_word}".rstrip('0').rstrip('.')
        
        elif number >= 100000:  # 1 lakh
            lakhs = number / 100000
            lakh_word = config.get("number_words", {}).get("lakh", "lakh")
            if lakhs >= 1:
                return f"{lakhs:.1f} {lakh_word}".rstrip('0').rstrip('.')
        
        elif number >= 1000:  # 1 thousand
            thousands = number / 1000
            thousand_word = config.get("number_words", {}).get("thousand", "thousand")
            if thousands >= 1:
                return f"{thousands:.1f} {thousand_word}".rstrip('0').rstrip('.')
        
        # For numbers less than 1000, return as-is with proper decimal formatting
        if number == int(number):
            return str(int(number))
        else:
            return f"{number:.2f}".rstrip('0').rstrip('.')
    
    async def _format_standard_number(self, number: float, config: Dict[str, Any]) -> str:
        """Format number using standard formatting"""
        decimal_sep = config.get("decimal_separator", ".")
        thousand_sep = config.get("thousand_separator", ",")
        
        # Format with thousand separators
        if number >= 1000:
            formatted = f"{number:,.2f}".replace(",", thousand_sep).replace(".", decimal_sep)
            return formatted.rstrip('0').rstrip(decimal_sep)
        else:
            if number == int(number):
                return str(int(number))
            else:
                return f"{number:.2f}".replace(".", decimal_sep).rstrip('0').rstrip(decimal_sep)
    
    async def localize_cultural_terms(
        self,
        text: str,
        context: LocalizationContext
    ) -> LocalizedValue:
        """Localize cultural terms and context"""
        try:
            cultural_config = self.cultural_patterns.get(context.language, {})
            localized_text = text
            
            # Replace festival names
            festivals = cultural_config.get("festivals", {})
            for english_name, local_name in festivals.items():
                localized_text = re.sub(
                    rf'\b{english_name}\b',
                    local_name,
                    localized_text,
                    flags=re.IGNORECASE
                )
            
            # Replace agricultural terms
            ag_terms = cultural_config.get("agricultural_terms", {})
            for english_term, local_term in ag_terms.items():
                localized_text = re.sub(
                    rf'\b{english_term}\b',
                    local_term,
                    localized_text,
                    flags=re.IGNORECASE
                )
            
            # Replace seasonal terms
            seasons = cultural_config.get("seasons", {})
            for english_season, local_season in seasons.items():
                localized_text = re.sub(
                    rf'\b{english_season}\b',
                    local_season,
                    localized_text,
                    flags=re.IGNORECASE
                )
            
            confidence = 0.9 if localized_text != text else 0.7
            
            return LocalizedValue(
                original_value=text,
                localized_text=localized_text,
                language=context.language,
                format_type="cultural",
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Cultural localization failed: {e}")
            return LocalizedValue(
                original_value=text,
                localized_text=text,
                language=context.language,
                format_type="cultural",
                confidence=0.5
            )
    
    async def get_regional_preferences(self, region: str) -> Dict[str, Any]:
        """Get regional preferences for localization"""
        return self.regional_preferences.get(region, {})
    
    def get_supported_languages(self) -> List[LanguageCode]:
        """Get list of supported languages for localization"""
        return list(self.currency_formats.keys())
    
    async def detect_cultural_context(self, text: str, language: LanguageCode) -> Dict[str, Any]:
        """Detect cultural context from text"""
        cultural_config = self.cultural_patterns.get(language, {})
        context = {
            "festivals_mentioned": [],
            "agricultural_terms": [],
            "seasonal_context": [],
            "respectful_terms": []
        }
        
        text_lower = text.lower()
        
        # Check for festivals
        festivals = cultural_config.get("festivals", {})
        for eng_name, local_name in festivals.items():
            if eng_name in text_lower or local_name.lower() in text_lower:
                context["festivals_mentioned"].append(eng_name)
        
        # Check for agricultural terms
        ag_terms = cultural_config.get("agricultural_terms", {})
        for eng_term, local_term in ag_terms.items():
            if eng_term in text_lower or local_term.lower() in text_lower:
                context["agricultural_terms"].append(eng_term)
        
        # Check for seasonal context
        seasons = cultural_config.get("seasons", {})
        for eng_season, local_season in seasons.items():
            if eng_season in text_lower or local_season.lower() in text_lower:
                context["seasonal_context"].append(eng_season)
        
        return context