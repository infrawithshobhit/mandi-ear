"""
Demand Analysis Module for Crop Planning

Analyzes market demand patterns, seasonal trends, export opportunities,
and price projections to inform crop planning decisions.
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import statistics
import random

from models import (
    DemandForecast, MarketTrend, GeoLocation
)

logger = logging.getLogger(__name__)

class DemandAnalyzer:
    """
    Comprehensive market demand analysis for crop planning
    
    Provides:
    - Historical demand pattern analysis
    - Seasonal trend identification
    - Export opportunity assessment
    - Price projection modeling
    """
    
    def __init__(self):
        # Seasonal demand patterns for major crops (normalized 0-1)
        self.seasonal_patterns = {
            "rice": {
                1: 0.8, 2: 0.7, 3: 0.6, 4: 0.5, 5: 0.4, 6: 0.3,
                7: 0.4, 8: 0.5, 9: 0.6, 10: 0.8, 11: 1.0, 12: 0.9
            },
            "wheat": {
                1: 0.9, 2: 1.0, 3: 0.8, 4: 0.6, 5: 0.4, 6: 0.3,
                7: 0.3, 8: 0.4, 9: 0.5, 10: 0.6, 11: 0.7, 12: 0.8
            },
            "cotton": {
                1: 0.6, 2: 0.7, 3: 0.8, 4: 0.9, 5: 1.0, 6: 0.9,
                7: 0.8, 8: 0.7, 9: 0.6, 10: 0.5, 11: 0.5, 12: 0.6
            },
            "sugarcane": {
                1: 1.0, 2: 0.9, 3: 0.8, 4: 0.7, 5: 0.6, 6: 0.5,
                7: 0.5, 8: 0.6, 9: 0.7, 10: 0.8, 11: 0.9, 12: 1.0
            },
            "maize": {
                1: 0.7, 2: 0.6, 3: 0.5, 4: 0.6, 5: 0.7, 6: 0.8,
                7: 0.9, 8: 1.0, 9: 0.9, 10: 0.8, 11: 0.7, 12: 0.7
            },
            "pulses": {
                1: 0.8, 2: 0.9, 3: 1.0, 4: 0.8, 5: 0.6, 6: 0.5,
                7: 0.4, 8: 0.5, 9: 0.6, 10: 0.7, 11: 0.8, 12: 0.8
            },
            "vegetables": {
                1: 0.9, 2: 0.8, 3: 0.7, 4: 0.8, 5: 0.9, 6: 1.0,
                7: 1.0, 8: 0.9, 9: 0.8, 10: 0.9, 11: 1.0, 12: 0.9
            },
            "fruits": {
                1: 0.6, 2: 0.7, 3: 0.8, 4: 0.9, 5: 1.0, 6: 1.0,
                7: 0.9, 8: 0.8, 9: 0.7, 10: 0.6, 11: 0.6, 12: 0.6
            }
        }
        
        # Export demand factors by crop
        self.export_opportunities = {
            "rice": {
                "export_potential": 0.8,
                "major_markets": ["Middle East", "Africa", "Europe"],
                "seasonal_export_peak": [3, 4, 5, 6]
            },
            "wheat": {
                "export_potential": 0.6,
                "major_markets": ["Bangladesh", "Nepal", "Sri Lanka"],
                "seasonal_export_peak": [4, 5, 6]
            },
            "cotton": {
                "export_potential": 0.9,
                "major_markets": ["China", "Bangladesh", "Vietnam"],
                "seasonal_export_peak": [1, 2, 3, 4]
            },
            "spices": {
                "export_potential": 0.95,
                "major_markets": ["USA", "Europe", "Middle East"],
                "seasonal_export_peak": [10, 11, 12, 1]
            },
            "tea": {
                "export_potential": 0.85,
                "major_markets": ["Russia", "UK", "USA"],
                "seasonal_export_peak": [6, 7, 8, 9]
            },
            "coffee": {
                "export_potential": 0.8,
                "major_markets": ["Europe", "USA", "Japan"],
                "seasonal_export_peak": [1, 2, 3]
            }
        }
        
        # Regional demand multipliers
        self.regional_multipliers = {
            "north": {"wheat": 1.2, "rice": 1.0, "vegetables": 1.1},
            "south": {"rice": 1.3, "cotton": 1.2, "spices": 1.4},
            "west": {"cotton": 1.3, "sugarcane": 1.2, "vegetables": 1.1},
            "east": {"rice": 1.4, "jute": 1.5, "tea": 1.3},
            "central": {"pulses": 1.2, "oilseeds": 1.1, "cotton": 1.1}
        }
    
    async def forecast_demand(
        self, 
        commodity: str, 
        region: str, 
        timeframe: timedelta
    ) -> DemandForecast:
        """
        Forecast market demand for a commodity
        
        Args:
            commodity: Crop/commodity name
            region: Geographic region
            timeframe: Forecast timeframe
            
        Returns:
            Comprehensive demand forecast
        """
        try:
            # Normalize commodity name
            commodity_normalized = self._normalize_commodity_name(commodity)
            
            # Generate market trends
            trends = self._generate_market_trends(commodity_normalized, region, timeframe)
            
            # Get seasonal patterns
            seasonal_patterns = self._get_seasonal_patterns(commodity_normalized)
            
            # Assess export opportunities
            export_opportunities = self._assess_export_opportunities(commodity_normalized)
            
            # Generate price projections
            price_projection = self._generate_price_projections(commodity_normalized, trends)
            
            # Calculate demand growth rate
            demand_growth_rate = self._calculate_demand_growth_rate(trends)
            
            return DemandForecast(
                commodity=commodity,
                region=region,
                forecast_period=f"{timeframe.days} days",
                trends=trends,
                seasonal_patterns=seasonal_patterns,
                export_opportunities=export_opportunities,
                price_projection=price_projection,
                demand_growth_rate=demand_growth_rate
            )
            
        except Exception as e:
            logger.error(f"Demand forecast failed for {commodity}: {str(e)}")
            return self._generate_fallback_forecast(commodity, region, timeframe)
    
    def _normalize_commodity_name(self, commodity: str) -> str:
        """Normalize commodity name to match internal patterns"""
        commodity_lower = commodity.lower().strip()
        
        # Map variations to standard names
        mappings = {
            "paddy": "rice",
            "bajra": "milses",
            "jowar": "millets",
            "arhar": "pulses",
            "tur": "pulses",
            "moong": "pulses",
            "chana": "pulses",
            "groundnut": "oilseeds",
            "mustard": "oilseeds",
            "sunflower": "oilseeds",
            "onion": "vegetables",
            "potato": "vegetables",
            "tomato": "vegetables",
            "mango": "fruits",
            "banana": "fruits",
            "apple": "fruits"
        }
        
        return mappings.get(commodity_lower, commodity_lower)
    
    def _generate_market_trends(
        self, 
        commodity: str, 
        region: str, 
        timeframe: timedelta
    ) -> List[MarketTrend]:
        """Generate market trend data for the forecast period"""
        trends = []
        current_date = datetime.now()
        months_to_generate = min(12, int(timeframe.days / 30))
        
        # Base price (would come from real market data in production)
        base_price = self._get_base_price(commodity)
        
        # Regional multiplier
        region_key = self._get_region_key(region)
        regional_multiplier = self.regional_multipliers.get(region_key, {}).get(commodity, 1.0)
        
        for i in range(months_to_generate):
            month = ((current_date.month - 1 + i) % 12) + 1
            
            # Get seasonal demand factor
            seasonal_factor = self.seasonal_patterns.get(commodity, {}).get(month, 0.7)
            
            # Add some randomness for market volatility
            volatility = random.uniform(0.9, 1.1)
            
            # Calculate trend values
            price_avg = base_price * regional_multiplier * seasonal_factor * volatility
            demand_index = seasonal_factor * regional_multiplier * random.uniform(0.95, 1.05)
            supply_index = random.uniform(0.8, 1.2)  # Supply varies more
            export_demand = self._calculate_export_demand(commodity, month)
            
            trend = MarketTrend(
                month=month,
                price_avg=round(price_avg, 2),
                demand_index=round(demand_index, 2),
                supply_index=round(supply_index, 2),
                export_demand=round(export_demand, 2)
            )
            trends.append(trend)
        
        return trends
    
    def _get_base_price(self, commodity: str) -> float:
        """Get base price for commodity (would come from real data)"""
        base_prices = {
            "rice": 2500.0,
            "wheat": 2200.0,
            "cotton": 5500.0,
            "sugarcane": 350.0,
            "maize": 1800.0,
            "pulses": 6000.0,
            "oilseeds": 4500.0,
            "vegetables": 2000.0,
            "fruits": 3000.0,
            "spices": 15000.0,
            "tea": 200.0,
            "coffee": 8000.0
        }
        return base_prices.get(commodity, 2000.0)
    
    def _get_region_key(self, region: str) -> str:
        """Map region to internal region key"""
        region_lower = region.lower()
        
        if any(state in region_lower for state in ["punjab", "haryana", "delhi", "rajasthan", "himachal", "uttarakhand"]):
            return "north"
        elif any(state in region_lower for state in ["tamil nadu", "kerala", "karnataka", "andhra", "telangana"]):
            return "south"
        elif any(state in region_lower for state in ["maharashtra", "gujarat", "goa"]):
            return "west"
        elif any(state in region_lower for state in ["west bengal", "odisha", "jharkhand", "bihar", "assam"]):
            return "east"
        else:
            return "central"
    
    def _get_seasonal_patterns(self, commodity: str) -> Dict[str, float]:
        """Get seasonal demand patterns for commodity"""
        patterns = self.seasonal_patterns.get(commodity, {})
        
        # Convert month numbers to month names
        month_names = {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December"
        }
        
        return {month_names[month]: demand for month, demand in patterns.items()}
    
    def _assess_export_opportunities(self, commodity: str) -> List[Dict[str, Any]]:
        """Assess export opportunities for commodity"""
        export_info = self.export_opportunities.get(commodity, {
            "export_potential": 0.3,
            "major_markets": ["Regional markets"],
            "seasonal_export_peak": [6, 7, 8]
        })
        
        opportunities = []
        
        for market in export_info["major_markets"]:
            opportunity = {
                "market": market,
                "potential_volume": f"{export_info['export_potential'] * 100:.0f}%",
                "peak_months": export_info["seasonal_export_peak"],
                "estimated_premium": f"{random.uniform(5, 20):.1f}%"
            }
            opportunities.append(opportunity)
        
        return opportunities
    
    def _calculate_export_demand(self, commodity: str, month: int) -> float:
        """Calculate export demand for specific month"""
        export_info = self.export_opportunities.get(commodity, {})
        base_potential = export_info.get("export_potential", 0.3)
        peak_months = export_info.get("seasonal_export_peak", [])
        
        if month in peak_months:
            return base_potential * random.uniform(1.2, 1.5)
        else:
            return base_potential * random.uniform(0.7, 1.0)
    
    def _generate_price_projections(
        self, 
        commodity: str, 
        trends: List[MarketTrend]
    ) -> Dict[str, float]:
        """Generate price projections based on trends"""
        if not trends:
            return {"current": 2000.0, "3_month": 2100.0, "6_month": 2200.0, "12_month": 2300.0}
        
        current_price = trends[0].price_avg
        
        # Calculate trend direction
        if len(trends) >= 3:
            recent_prices = [t.price_avg for t in trends[:3]]
            trend_direction = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        else:
            trend_direction = 0.02  # Default 2% growth
        
        projections = {
            "current": round(current_price, 2),
            "3_month": round(current_price * (1 + trend_direction * 3), 2),
            "6_month": round(current_price * (1 + trend_direction * 6), 2),
            "12_month": round(current_price * (1 + trend_direction * 12), 2)
        }
        
        return projections
    
    def _calculate_demand_growth_rate(self, trends: List[MarketTrend]) -> float:
        """Calculate overall demand growth rate"""
        if len(trends) < 2:
            return 0.05  # Default 5% growth
        
        demand_values = [t.demand_index for t in trends]
        
        # Calculate linear trend
        if len(demand_values) >= 6:
            first_half = statistics.mean(demand_values[:3])
            second_half = statistics.mean(demand_values[-3:])
            growth_rate = (second_half - first_half) / first_half
        else:
            growth_rate = (demand_values[-1] - demand_values[0]) / demand_values[0]
        
        return round(growth_rate, 3)
    
    def _generate_fallback_forecast(
        self, 
        commodity: str, 
        region: str, 
        timeframe: timedelta
    ) -> DemandForecast:
        """Generate fallback forecast when analysis fails"""
        
        # Generate basic trends
        trends = []
        base_price = 2000.0
        
        for month in range(1, 7):  # 6 months
            trend = MarketTrend(
                month=month,
                price_avg=base_price * random.uniform(0.95, 1.05),
                demand_index=random.uniform(0.8, 1.2),
                supply_index=random.uniform(0.9, 1.1),
                export_demand=random.uniform(0.3, 0.7)
            )
            trends.append(trend)
        
        return DemandForecast(
            commodity=commodity,
            region=region,
            forecast_period=f"{timeframe.days} days (fallback data)",
            trends=trends,
            seasonal_patterns={"peak_season": 0.8, "off_season": 0.6},
            export_opportunities=[{
                "market": "Regional markets",
                "potential_volume": "30%",
                "peak_months": [6, 7, 8],
                "estimated_premium": "10%"
            }],
            price_projection={
                "current": base_price,
                "3_month": base_price * 1.05,
                "6_month": base_price * 1.10,
                "12_month": base_price * 1.15
            },
            demand_growth_rate=0.05
        )