"""
Market Context Analyzer for Negotiation Intelligence Service
Implements real-time market condition assessment
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import statistics
import requests
from dataclasses import dataclass

from models import MarketContext, MarketCondition, GeoLocation

logger = logging.getLogger(__name__)

@dataclass
class PricePoint:
    price: float
    timestamp: datetime
    volume: float
    mandi: str

class MarketContextAnalyzer:
    """Analyzes real-time market conditions for negotiation context"""
    
    def __init__(self):
        self.price_cache = {}
        self.trend_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    async def analyze_market_context(self, commodity: str, location: Dict[str, float]) -> MarketContext:
        """
        Analyze comprehensive market context for negotiation
        
        Args:
            commodity: Name of the commodity
            location: Geographic location {"lat": float, "lng": float}
            
        Returns:
            MarketContext: Complete market analysis
        """
        try:
            # Get current price data
            current_price = await self._get_current_price(commodity, location)
            
            # Analyze price trends
            price_trend = await self._analyze_price_trend(commodity, location)
            
            # Assess market condition
            market_condition = await self._assess_market_condition(commodity, location)
            
            # Get supply and demand levels
            supply_level, demand_level = await self._get_supply_demand_levels(commodity, location)
            
            # Calculate seasonal factors
            seasonal_factor = await self._calculate_seasonal_factor(commodity)
            
            # Get weather impact
            weather_impact = await self._assess_weather_impact(commodity, location)
            
            # Check festival demand
            festival_demand = await self._check_festival_demand(commodity)
            
            # Get export demand
            export_demand = await self._get_export_demand(commodity)
            
            # Calculate costs
            transportation_cost = await self._calculate_transportation_cost(location)
            storage_cost = await self._calculate_storage_cost(commodity)
            quality_premium = await self._calculate_quality_premium(commodity)
            
            # Assess competition
            competition_level = await self._assess_competition_level(commodity, location)
            
            return MarketContext(
                commodity=commodity,
                current_price=current_price,
                price_trend=price_trend,
                market_condition=market_condition,
                supply_level=supply_level,
                demand_level=demand_level,
                seasonal_factor=seasonal_factor,
                weather_impact=weather_impact,
                festival_demand=festival_demand,
                export_demand=export_demand,
                transportation_cost=transportation_cost,
                storage_cost=storage_cost,
                quality_premium=quality_premium,
                competition_level=competition_level
            )
            
        except Exception as e:
            logger.error(f"Market context analysis failed: {str(e)}")
            # Return default context with current price
            return MarketContext(
                commodity=commodity,
                current_price=await self._get_fallback_price(commodity),
                price_trend="stable",
                market_condition=MarketCondition.STABLE,
                supply_level="medium",
                demand_level="medium",
                seasonal_factor=1.0,
                transportation_cost=50.0,
                storage_cost=10.0,
                quality_premium=0.05,
                competition_level="medium"
            )
    
    async def _get_current_price(self, commodity: str, location: Dict[str, float]) -> float:
        """Get current market price for commodity at location"""
        cache_key = f"{commodity}_{location['lat']}_{location['lng']}"
        
        # Check cache first
        if cache_key in self.price_cache:
            cached_data = self.price_cache[cache_key]
            if datetime.now() - cached_data['timestamp'] < timedelta(seconds=self.cache_ttl):
                return cached_data['price']
        
        try:
            # Simulate API call to price discovery service
            # In real implementation, this would call the actual price discovery service
            base_prices = {
                'wheat': 2500.0,
                'rice': 3000.0,
                'onion': 1500.0,
                'potato': 1200.0,
                'tomato': 2000.0,
                'sugarcane': 350.0,
                'cotton': 6000.0,
                'soybean': 4500.0
            }
            
            base_price = base_prices.get(commodity.lower(), 2000.0)
            
            # Add location-based variation (±10%)
            location_factor = (location['lat'] + location['lng']) % 0.2 - 0.1
            current_price = base_price * (1 + location_factor)
            
            # Cache the result
            self.price_cache[cache_key] = {
                'price': current_price,
                'timestamp': datetime.now()
            }
            
            return current_price
            
        except Exception as e:
            logger.error(f"Failed to get current price: {str(e)}")
            return await self._get_fallback_price(commodity)
    
    async def _analyze_price_trend(self, commodity: str, location: Dict[str, float]) -> str:
        """Analyze price trend over recent period"""
        try:
            # Simulate historical price data
            current_price = await self._get_current_price(commodity, location)
            
            # Generate mock historical prices (last 7 days)
            historical_prices = []
            for i in range(7):
                # Simulate price variation
                variation = (i * 0.02) - 0.06  # Trend simulation
                price = current_price * (1 + variation)
                historical_prices.append(price)
            
            # Calculate trend
            if len(historical_prices) >= 3:
                recent_avg = statistics.mean(historical_prices[-3:])
                older_avg = statistics.mean(historical_prices[:3])
                
                change_percent = (recent_avg - older_avg) / older_avg
                
                if change_percent > 0.05:
                    return "increasing"
                elif change_percent < -0.05:
                    return "decreasing"
                else:
                    return "stable"
            
            return "stable"
            
        except Exception as e:
            logger.error(f"Price trend analysis failed: {str(e)}")
            return "stable"
    
    async def _assess_market_condition(self, commodity: str, location: Dict[str, float]) -> MarketCondition:
        """Assess overall market condition"""
        try:
            # Get price volatility
            price_trend = await self._analyze_price_trend(commodity, location)
            
            # Simulate market condition assessment
            # In real implementation, this would analyze multiple factors
            if price_trend == "increasing":
                return MarketCondition.BULLISH
            elif price_trend == "decreasing":
                return MarketCondition.BEARISH
            else:
                return MarketCondition.STABLE
                
        except Exception as e:
            logger.error(f"Market condition assessment failed: {str(e)}")
            return MarketCondition.STABLE
    
    async def _get_supply_demand_levels(self, commodity: str, location: Dict[str, float]) -> tuple[str, str]:
        """Get supply and demand levels"""
        try:
            # Simulate supply/demand analysis
            # In real implementation, this would analyze inventory, production, consumption data
            
            # Mock logic based on commodity and season
            current_month = datetime.now().month
            
            supply_levels = ["low", "medium", "high"]
            demand_levels = ["low", "medium", "high"]
            
            # Seasonal logic simulation
            if commodity.lower() in ['wheat', 'rice'] and current_month in [4, 5, 6]:  # Harvest season
                supply = "high"
                demand = "medium"
            elif commodity.lower() in ['onion', 'potato'] and current_month in [10, 11, 12]:  # Storage season
                supply = "medium"
                demand = "high"
            else:
                supply = "medium"
                demand = "medium"
            
            return supply, demand
            
        except Exception as e:
            logger.error(f"Supply/demand analysis failed: {str(e)}")
            return "medium", "medium"
    
    async def _calculate_seasonal_factor(self, commodity: str) -> float:
        """Calculate seasonal price factor"""
        try:
            current_month = datetime.now().month
            
            # Seasonal factors for different commodities
            seasonal_patterns = {
                'wheat': {1: 1.1, 2: 1.1, 3: 1.0, 4: 0.9, 5: 0.9, 6: 0.9, 
                         7: 1.0, 8: 1.0, 9: 1.0, 10: 1.1, 11: 1.1, 12: 1.1},
                'rice': {1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0,
                        7: 1.1, 8: 1.1, 9: 1.1, 10: 0.9, 11: 0.9, 12: 1.0},
                'onion': {1: 1.2, 2: 1.2, 3: 1.1, 4: 1.0, 5: 0.9, 6: 0.9,
                         7: 0.9, 8: 0.9, 9: 1.0, 10: 1.1, 11: 1.2, 12: 1.2}
            }
            
            pattern = seasonal_patterns.get(commodity.lower())
            if pattern:
                return pattern.get(current_month, 1.0)
            
            return 1.0
            
        except Exception as e:
            logger.error(f"Seasonal factor calculation failed: {str(e)}")
            return 1.0
    
    async def _assess_weather_impact(self, commodity: str, location: Dict[str, float]) -> Optional[str]:
        """Assess weather impact on commodity"""
        try:
            # Simulate weather impact assessment
            # In real implementation, this would integrate with weather APIs
            
            # Mock weather conditions
            weather_conditions = ["drought", "flood", "normal", "favorable"]
            
            # Simple simulation based on location and season
            impact_probability = (location['lat'] + location['lng']) % 1.0
            
            if impact_probability > 0.8:
                return "drought_risk"
            elif impact_probability < 0.2:
                return "flood_risk"
            else:
                return None
                
        except Exception as e:
            logger.error(f"Weather impact assessment failed: {str(e)}")
            return None
    
    async def _check_festival_demand(self, commodity: str) -> bool:
        """Check if there's festival-related demand"""
        try:
            current_month = datetime.now().month
            
            # Festival seasons in India
            festival_months = [3, 4, 9, 10, 11]  # Holi, Ram Navami, Dussehra, Diwali, etc.
            
            # Commodities with festival demand
            festival_commodities = ['rice', 'wheat', 'sugar', 'oil', 'pulses']
            
            return (current_month in festival_months and 
                   commodity.lower() in festival_commodities)
                   
        except Exception as e:
            logger.error(f"Festival demand check failed: {str(e)}")
            return False
    
    async def _get_export_demand(self, commodity: str) -> Optional[float]:
        """Get export demand for commodity"""
        try:
            # Simulate export demand data
            export_commodities = {
                'rice': 0.15,  # 15% of production exported
                'wheat': 0.05,
                'cotton': 0.25,
                'spices': 0.30
            }
            
            return export_commodities.get(commodity.lower())
            
        except Exception as e:
            logger.error(f"Export demand calculation failed: {str(e)}")
            return None
    
    async def _calculate_transportation_cost(self, location: Dict[str, float]) -> float:
        """Calculate transportation cost from location"""
        try:
            # Simulate transportation cost calculation
            # Based on distance from major markets
            
            # Major market locations (simplified)
            major_markets = [
                {'lat': 28.6139, 'lng': 77.2090},  # Delhi
                {'lat': 19.0760, 'lng': 72.8777},  # Mumbai
                {'lat': 13.0827, 'lng': 80.2707},  # Chennai
                {'lat': 22.5726, 'lng': 88.3639}   # Kolkata
            ]
            
            # Find nearest major market
            min_distance = float('inf')
            for market in major_markets:
                distance = ((location['lat'] - market['lat'])**2 + 
                           (location['lng'] - market['lng'])**2)**0.5
                min_distance = min(min_distance, distance)
            
            # Calculate cost (₹ per quintal)
            base_cost = 50.0
            distance_cost = min_distance * 100  # ₹100 per degree distance
            
            return base_cost + distance_cost
            
        except Exception as e:
            logger.error(f"Transportation cost calculation failed: {str(e)}")
            return 50.0
    
    async def _calculate_storage_cost(self, commodity: str) -> float:
        """Calculate storage cost for commodity"""
        try:
            # Storage costs per quintal per month
            storage_costs = {
                'wheat': 15.0,
                'rice': 20.0,
                'onion': 25.0,
                'potato': 30.0,
                'cotton': 10.0
            }
            
            return storage_costs.get(commodity.lower(), 15.0)
            
        except Exception as e:
            logger.error(f"Storage cost calculation failed: {str(e)}")
            return 15.0
    
    async def _calculate_quality_premium(self, commodity: str) -> float:
        """Calculate quality premium percentage"""
        try:
            # Quality premiums for different commodities
            quality_premiums = {
                'wheat': 0.10,  # 10% premium for high quality
                'rice': 0.15,
                'cotton': 0.20,
                'spices': 0.25
            }
            
            return quality_premiums.get(commodity.lower(), 0.05)
            
        except Exception as e:
            logger.error(f"Quality premium calculation failed: {str(e)}")
            return 0.05
    
    async def _assess_competition_level(self, commodity: str, location: Dict[str, float]) -> str:
        """Assess competition level in the market"""
        try:
            # Simulate competition assessment
            # In real implementation, this would analyze number of buyers, market concentration
            
            # Mock logic based on location and commodity
            competition_score = (location['lat'] + location['lng']) % 3
            
            if competition_score < 1:
                return "low"
            elif competition_score < 2:
                return "medium"
            else:
                return "high"
                
        except Exception as e:
            logger.error(f"Competition assessment failed: {str(e)}")
            return "medium"
    
    async def _get_fallback_price(self, commodity: str) -> float:
        """Get fallback price when other methods fail"""
        fallback_prices = {
            'wheat': 2500.0,
            'rice': 3000.0,
            'onion': 1500.0,
            'potato': 1200.0,
            'tomato': 2000.0,
            'sugarcane': 350.0,
            'cotton': 6000.0,
            'soybean': 4500.0
        }
        
        return fallback_prices.get(commodity.lower(), 2000.0)