"""
Soil Analysis Module for Crop Planning

Analyzes soil conditions including pH, nutrient levels, drainage,
and provides crop suitability recommendations based on soil characteristics.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import random

from models import (
    SoilAssessment, SoilProperties, SoilType, GeoLocation
)

logger = logging.getLogger(__name__)

class SoilAnalyzer:
    """
    Comprehensive soil analysis for crop planning
    
    Provides:
    - Soil type identification
    - Chemical and physical property analysis
    - Crop suitability assessment
    - Soil improvement recommendations
    """
    
    def __init__(self):
        # Soil-crop compatibility matrix
        self.crop_soil_compatibility = {
            SoilType.ALLUVIAL: {
                "excellent": ["rice", "wheat", "sugarcane", "cotton", "maize"],
                "good": ["barley", "pulses", "oilseeds", "vegetables"],
                "moderate": ["millets", "spices"]
            },
            SoilType.BLACK: {
                "excellent": ["cotton", "sugarcane", "wheat", "jowar", "tur"],
                "good": ["maize", "sunflower", "safflower", "onion"],
                "moderate": ["rice", "vegetables"]
            },
            SoilType.RED: {
                "excellent": ["millets", "pulses", "oilseeds", "cotton"],
                "good": ["maize", "tobacco", "vegetables", "fruits"],
                "moderate": ["rice", "wheat", "sugarcane"]
            },
            SoilType.LATERITE: {
                "excellent": ["cashew", "coconut", "areca nut", "spices"],
                "good": ["rice", "ragi", "tapioca"],
                "moderate": ["vegetables", "fruits"]
            },
            SoilType.DESERT: {
                "excellent": ["bajra", "jowar", "moth", "guar"],
                "good": ["dates", "drought-resistant crops"],
                "moderate": ["barley", "mustard"]
            },
            SoilType.MOUNTAIN: {
                "excellent": ["tea", "coffee", "cardamom", "fruits"],
                "good": ["maize", "barley", "vegetables"],
                "moderate": ["wheat", "rice"]
            },
            SoilType.SALINE: {
                "excellent": ["barley", "mustard", "safflower"],
                "good": ["cotton", "berseem"],
                "moderate": ["rice", "wheat"]
            }
        }
        
        # Soil improvement recommendations
        self.improvement_strategies = {
            "low_ph": [
                "Apply lime to increase pH",
                "Use organic matter like compost",
                "Avoid ammonium-based fertilizers"
            ],
            "high_ph": [
                "Apply sulfur to reduce pH",
                "Use acidifying fertilizers",
                "Add organic matter"
            ],
            "low_nitrogen": [
                "Apply nitrogen-rich fertilizers",
                "Use leguminous cover crops",
                "Add compost or manure"
            ],
            "low_phosphorus": [
                "Apply phosphate fertilizers",
                "Use bone meal or rock phosphate",
                "Maintain proper pH for P availability"
            ],
            "low_potassium": [
                "Apply potash fertilizers",
                "Use wood ash (if available)",
                "Add organic matter"
            ],
            "poor_drainage": [
                "Install drainage systems",
                "Create raised beds",
                "Add organic matter to improve structure"
            ],
            "low_organic_matter": [
                "Add compost regularly",
                "Use cover crops",
                "Apply farmyard manure"
            ]
        }
    
    async def assess_conditions(
        self, 
        latitude: float, 
        longitude: float,
        known_soil_type: Optional[str] = None
    ) -> SoilAssessment:
        """
        Assess soil conditions for crop planning
        
        Args:
            latitude: Farm latitude
            longitude: Farm longitude
            known_soil_type: Optional known soil type
            
        Returns:
            Comprehensive soil assessment
        """
        try:
            location = GeoLocation(latitude=latitude, longitude=longitude)
            
            # Determine soil type
            soil_type = self._determine_soil_type(latitude, longitude, known_soil_type)
            
            # Analyze soil properties
            properties = await self._analyze_soil_properties(soil_type, latitude, longitude)
            
            # Get suitable crops
            suitable_crops = self._get_suitable_crops(soil_type, properties)
            
            # Generate improvement recommendations
            improvements = self._generate_improvement_recommendations(properties)
            
            # Calculate scores
            fertility_score = self._calculate_fertility_score(properties)
            water_retention_score = self._calculate_water_retention_score(properties, soil_type)
            
            return SoilAssessment(
                location=location,
                soil_type=soil_type,
                properties=properties,
                suitable_crops=suitable_crops,
                improvement_recommendations=improvements,
                fertility_score=fertility_score,
                water_retention_score=water_retention_score
            )
            
        except Exception as e:
            logger.error(f"Soil assessment failed: {str(e)}")
            return self._generate_fallback_assessment(latitude, longitude)
    
    def _determine_soil_type(
        self, 
        latitude: float, 
        longitude: float, 
        known_soil_type: Optional[str]
    ) -> SoilType:
        """Determine soil type based on location and known information"""
        
        if known_soil_type:
            try:
                return SoilType(known_soil_type.lower())
            except ValueError:
                logger.warning(f"Unknown soil type: {known_soil_type}, using geographic inference")
        
        # Geographic soil type inference for India
        # This is a simplified model - in production, would use soil survey data
        
        # Northern plains (Alluvial)
        if 24 <= latitude <= 32 and 75 <= longitude <= 88:
            return SoilType.ALLUVIAL
        
        # Deccan plateau (Black soil)
        elif 15 <= latitude <= 25 and 74 <= longitude <= 80:
            return SoilType.BLACK
        
        # Eastern and Southern regions (Red soil)
        elif 8 <= latitude <= 20 and 77 <= longitude <= 87:
            return SoilType.RED
        
        # Western coastal areas (Laterite)
        elif 8 <= latitude <= 20 and 72 <= longitude <= 77:
            return SoilType.LATERITE
        
        # Western desert regions
        elif 24 <= latitude <= 30 and 68 <= longitude <= 75:
            return SoilType.DESERT
        
        # Himalayan regions
        elif latitude > 30:
            return SoilType.MOUNTAIN
        
        # Default to alluvial (most common)
        else:
            return SoilType.ALLUVIAL
    
    async def _analyze_soil_properties(
        self, 
        soil_type: SoilType, 
        latitude: float, 
        longitude: float
    ) -> SoilProperties:
        """Analyze soil chemical and physical properties"""
        
        # In production, this would integrate with soil testing APIs or databases
        # For now, generate realistic properties based on soil type
        
        base_properties = {
            SoilType.ALLUVIAL: {
                "ph_level": 6.5 + random.uniform(-0.5, 0.5),
                "organic_matter_percent": 1.5 + random.uniform(-0.3, 0.5),
                "nitrogen_level": "medium",
                "phosphorus_level": "medium",
                "potassium_level": "high",
                "drainage": "good",
                "water_holding_capacity": "high"
            },
            SoilType.BLACK: {
                "ph_level": 7.5 + random.uniform(-0.3, 0.3),
                "organic_matter_percent": 2.0 + random.uniform(-0.4, 0.6),
                "nitrogen_level": "high",
                "phosphorus_level": "medium",
                "potassium_level": "high",
                "drainage": "moderate",
                "water_holding_capacity": "high"
            },
            SoilType.RED: {
                "ph_level": 5.5 + random.uniform(-0.5, 0.5),
                "organic_matter_percent": 1.0 + random.uniform(-0.2, 0.4),
                "nitrogen_level": "low",
                "phosphorus_level": "low",
                "potassium_level": "medium",
                "drainage": "good",
                "water_holding_capacity": "medium"
            },
            SoilType.LATERITE: {
                "ph_level": 5.0 + random.uniform(-0.3, 0.3),
                "organic_matter_percent": 0.8 + random.uniform(-0.2, 0.3),
                "nitrogen_level": "low",
                "phosphorus_level": "low",
                "potassium_level": "low",
                "drainage": "excellent",
                "water_holding_capacity": "low"
            },
            SoilType.DESERT: {
                "ph_level": 8.0 + random.uniform(-0.5, 0.5),
                "organic_matter_percent": 0.5 + random.uniform(-0.1, 0.2),
                "nitrogen_level": "low",
                "phosphorus_level": "low",
                "potassium_level": "medium",
                "drainage": "excellent",
                "water_holding_capacity": "low"
            },
            SoilType.MOUNTAIN: {
                "ph_level": 6.0 + random.uniform(-0.5, 0.5),
                "organic_matter_percent": 3.0 + random.uniform(-0.5, 1.0),
                "nitrogen_level": "medium",
                "phosphorus_level": "medium",
                "potassium_level": "medium",
                "drainage": "good",
                "water_holding_capacity": "medium"
            },
            SoilType.SALINE: {
                "ph_level": 8.5 + random.uniform(-0.3, 0.3),
                "organic_matter_percent": 0.7 + random.uniform(-0.2, 0.3),
                "nitrogen_level": "low",
                "phosphorus_level": "low",
                "potassium_level": "high",
                "drainage": "poor",
                "water_holding_capacity": "medium"
            }
        }
        
        props = base_properties.get(soil_type, base_properties[SoilType.ALLUVIAL])
        
        return SoilProperties(**props)
    
    def _get_suitable_crops(self, soil_type: SoilType, properties: SoilProperties) -> List[str]:
        """Get list of suitable crops based on soil type and properties"""
        
        base_crops = []
        compatibility = self.crop_soil_compatibility.get(soil_type, {})
        
        # Start with excellent matches
        base_crops.extend(compatibility.get("excellent", []))
        
        # Add good matches if pH is suitable
        if 6.0 <= properties.ph_level <= 7.5:
            base_crops.extend(compatibility.get("good", []))
        
        # Add moderate matches if other conditions are favorable
        if (properties.organic_matter_percent > 1.0 and 
            properties.drainage in ["good", "excellent"]):
            base_crops.extend(compatibility.get("moderate", []))
        
        # Remove duplicates and limit to top recommendations
        unique_crops = list(set(base_crops))
        return unique_crops[:10]  # Limit to top 10 recommendations
    
    def _generate_improvement_recommendations(self, properties: SoilProperties) -> List[str]:
        """Generate soil improvement recommendations"""
        recommendations = []
        
        # pH recommendations
        if properties.ph_level < 6.0:
            recommendations.extend(self.improvement_strategies["low_ph"])
        elif properties.ph_level > 8.0:
            recommendations.extend(self.improvement_strategies["high_ph"])
        
        # Nutrient recommendations
        if properties.nitrogen_level == "low":
            recommendations.extend(self.improvement_strategies["low_nitrogen"])
        if properties.phosphorus_level == "low":
            recommendations.extend(self.improvement_strategies["low_phosphorus"])
        if properties.potassium_level == "low":
            recommendations.extend(self.improvement_strategies["low_potassium"])
        
        # Drainage recommendations
        if properties.drainage == "poor":
            recommendations.extend(self.improvement_strategies["poor_drainage"])
        
        # Organic matter recommendations
        if properties.organic_matter_percent < 1.0:
            recommendations.extend(self.improvement_strategies["low_organic_matter"])
        
        # Remove duplicates
        return list(set(recommendations))
    
    def _calculate_fertility_score(self, properties: SoilProperties) -> float:
        """Calculate overall soil fertility score"""
        score = 0.0
        
        # pH score (optimal range: 6.0-7.5)
        if 6.0 <= properties.ph_level <= 7.5:
            ph_score = 1.0
        elif 5.5 <= properties.ph_level < 6.0 or 7.5 < properties.ph_level <= 8.0:
            ph_score = 0.7
        else:
            ph_score = 0.3
        
        # Organic matter score
        if properties.organic_matter_percent >= 2.0:
            om_score = 1.0
        elif properties.organic_matter_percent >= 1.0:
            om_score = 0.7
        else:
            om_score = 0.3
        
        # Nutrient scores
        nutrient_levels = [properties.nitrogen_level, properties.phosphorus_level, properties.potassium_level]
        nutrient_score = sum(1.0 if level == "high" else 0.7 if level == "medium" else 0.3 for level in nutrient_levels) / 3
        
        # Weighted average
        score = (ph_score * 0.3 + om_score * 0.3 + nutrient_score * 0.4)
        
        return round(score, 2)
    
    def _calculate_water_retention_score(self, properties: SoilProperties, soil_type: SoilType) -> float:
        """Calculate water retention capacity score"""
        
        # Base score from water holding capacity
        if properties.water_holding_capacity == "high":
            base_score = 1.0
        elif properties.water_holding_capacity == "medium":
            base_score = 0.7
        else:
            base_score = 0.3
        
        # Adjust based on drainage
        if properties.drainage == "poor":
            drainage_modifier = 0.8  # Too much water retention can be bad
        elif properties.drainage == "excellent":
            drainage_modifier = 0.9  # Good drainage but may reduce retention
        else:
            drainage_modifier = 1.0
        
        # Adjust based on organic matter (improves water retention)
        if properties.organic_matter_percent >= 2.0:
            om_modifier = 1.1
        elif properties.organic_matter_percent >= 1.0:
            om_modifier = 1.0
        else:
            om_modifier = 0.9
        
        score = base_score * drainage_modifier * om_modifier
        return round(min(score, 1.0), 2)  # Cap at 1.0
    
    def _generate_fallback_assessment(self, latitude: float, longitude: float) -> SoilAssessment:
        """Generate fallback assessment when analysis fails"""
        
        location = GeoLocation(latitude=latitude, longitude=longitude)
        soil_type = SoilType.ALLUVIAL  # Default to most common type
        
        properties = SoilProperties(
            ph_level=6.5,
            organic_matter_percent=1.5,
            nitrogen_level="medium",
            phosphorus_level="medium",
            potassium_level="medium",
            drainage="good",
            water_holding_capacity="medium"
        )
        
        return SoilAssessment(
            location=location,
            soil_type=soil_type,
            properties=properties,
            suitable_crops=["rice", "wheat", "maize", "cotton", "vegetables"],
            improvement_recommendations=["Regular soil testing recommended", "Add organic matter"],
            fertility_score=0.6,
            water_retention_score=0.6
        )