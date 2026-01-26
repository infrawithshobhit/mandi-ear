"""
Price Comparison and Analysis Engine
Implements cross-mandi price comparison, transportation cost calculation, and net profit analysis
"""

import asyncio
import structlog
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import math
from dataclasses import dataclass
from enum import Enum

from models import PricePoint, PriceData, MandiInfo, GeoLocation
from database import get_commodity_prices, get_mandis

logger = structlog.get_logger()

class TransportMode(str, Enum):
    """Transportation modes"""
    TRUCK = "truck"
    RAIL = "rail"
    COMBINED = "combined"

@dataclass
class TransportationCost:
    """Transportation cost breakdown"""
    distance_km: float
    mode: TransportMode
    fuel_cost: float
    labor_cost: float
    toll_cost: float
    loading_unloading_cost: float
    insurance_cost: float
    total_cost: float
    estimated_time_hours: float

@dataclass
class PriceComparison:
    """Price comparison result"""
    commodity: str
    base_location: GeoLocation
    comparisons: List['MandiComparison']
    best_price_mandi: Optional[str] = None
    best_profit_mandi: Optional[str] = None
    average_price: float = 0.0
    price_variance: float = 0.0

@dataclass
class MandiComparison:
    """Individual mandi comparison"""
    mandi: MandiInfo
    price_data: PriceData
    transportation_cost: TransportationCost
    net_profit: float
    profit_margin_percent: float
    recommendation_score: float

class GeospatialCalculator:
    """Handles geographic calculations"""
    
    EARTH_RADIUS_KM = 6371.0
    
    @staticmethod
    def calculate_distance(loc1: GeoLocation, loc2: GeoLocation) -> float:
        """
        Calculate distance between two locations using Haversine formula
        
        Args:
            loc1: First location
            loc2: Second location
            
        Returns:
            Distance in kilometers
        """
        # Convert latitude and longitude from degrees to radians
        lat1_rad = math.radians(loc1.latitude)
        lon1_rad = math.radians(loc1.longitude)
        lat2_rad = math.radians(loc2.latitude)
        lon2_rad = math.radians(loc2.longitude)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = GeospatialCalculator.EARTH_RADIUS_KM * c
        return distance
    
    @staticmethod
    def find_optimal_route(origin: GeoLocation, destination: GeoLocation) -> Dict[str, Any]:
        """
        Find optimal transportation route
        
        Args:
            origin: Starting location
            destination: Destination location
            
        Returns:
            Route information including distance, estimated time, and recommended mode
        """
        distance = GeospatialCalculator.calculate_distance(origin, destination)
        
        # Determine optimal transportation mode based on distance
        if distance < 100:
            mode = TransportMode.TRUCK
            speed_kmh = 40  # Average speed for short distances
        elif distance < 500:
            mode = TransportMode.TRUCK
            speed_kmh = 50  # Highway speed
        else:
            mode = TransportMode.COMBINED  # Truck + Rail for long distances
            speed_kmh = 45  # Combined mode average
        
        estimated_time = distance / speed_kmh
        
        return {
            "distance_km": distance,
            "mode": mode,
            "estimated_time_hours": estimated_time,
            "route_type": "direct" if distance < 200 else "highway"
        }

class TransportationCostCalculator:
    """Calculates transportation costs for different modes and distances"""
    
    def __init__(self):
        # Cost parameters (in INR)
        self.fuel_cost_per_km = {
            TransportMode.TRUCK: 12.0,  # Diesel cost per km
            TransportMode.RAIL: 3.0,    # Rail freight per km
            TransportMode.COMBINED: 8.0  # Average for combined transport
        }
        
        self.labor_cost_per_hour = {
            TransportMode.TRUCK: 150.0,  # Driver + helper cost per hour
            TransportMode.RAIL: 50.0,    # Reduced labor for rail
            TransportMode.COMBINED: 100.0
        }
        
        self.base_loading_cost = 500.0  # Base loading/unloading cost
        self.insurance_rate = 0.002     # 0.2% of commodity value
        self.toll_rate_per_km = 2.0     # Average toll cost per km
    
    def calculate_cost(
        self, 
        distance_km: float, 
        commodity: str, 
        commodity_value: float,
        transport_mode: Optional[TransportMode] = None
    ) -> TransportationCost:
        """
        Calculate comprehensive transportation cost
        
        Args:
            distance_km: Distance to transport
            commodity: Type of commodity
            commodity_value: Total value of commodity being transported
            transport_mode: Preferred transportation mode
            
        Returns:
            Detailed transportation cost breakdown
        """
        # Determine optimal transport mode if not specified
        if transport_mode is None:
            if distance_km < 100:
                transport_mode = TransportMode.TRUCK
            elif distance_km < 500:
                transport_mode = TransportMode.TRUCK
            else:
                transport_mode = TransportMode.COMBINED
        
        # Calculate individual cost components
        fuel_cost = distance_km * self.fuel_cost_per_km[transport_mode]
        
        # Estimate travel time
        speed_kmh = self._get_average_speed(transport_mode, distance_km)
        travel_time_hours = distance_km / speed_kmh
        labor_cost = travel_time_hours * self.labor_cost_per_hour[transport_mode]
        
        # Toll costs (mainly for truck transport)
        toll_cost = 0.0
        if transport_mode in [TransportMode.TRUCK, TransportMode.COMBINED]:
            toll_cost = distance_km * self.toll_rate_per_km
        
        # Loading/unloading costs
        commodity_multiplier = self._get_commodity_multiplier(commodity)
        loading_cost = self.base_loading_cost * commodity_multiplier
        
        # Insurance cost
        insurance_cost = commodity_value * self.insurance_rate
        
        # Total cost
        total_cost = fuel_cost + labor_cost + toll_cost + loading_cost + insurance_cost
        
        return TransportationCost(
            distance_km=distance_km,
            mode=transport_mode,
            fuel_cost=fuel_cost,
            labor_cost=labor_cost,
            toll_cost=toll_cost,
            loading_unloading_cost=loading_cost,
            insurance_cost=insurance_cost,
            total_cost=total_cost,
            estimated_time_hours=travel_time_hours
        )
    
    def _get_average_speed(self, mode: TransportMode, distance_km: float) -> float:
        """Get average speed for transport mode and distance"""
        base_speeds = {
            TransportMode.TRUCK: 45.0,
            TransportMode.RAIL: 60.0,
            TransportMode.COMBINED: 40.0
        }
        
        speed = base_speeds[mode]
        
        # Adjust speed based on distance (longer distances = higher average speed)
        if distance_km > 300:
            speed *= 1.1  # Highway speeds
        elif distance_km < 50:
            speed *= 0.8  # City/local roads
        
        return speed
    
    def _get_commodity_multiplier(self, commodity: str) -> float:
        """Get loading/handling multiplier for different commodities"""
        multipliers = {
            "wheat": 1.0,
            "rice": 1.0,
            "maize": 1.0,
            "onion": 1.3,      # Requires careful handling
            "potato": 1.2,     # Heavy, requires proper storage
            "tomato": 1.5,     # Perishable, delicate handling
            "cotton": 0.9,     # Lighter, easier to handle
            "sugarcane": 1.4,  # Heavy, bulky
            "chilli": 1.2,     # Requires careful handling
            "turmeric": 1.1    # Powder form, requires sealed transport
        }
        
        return multipliers.get(commodity.lower(), 1.0)

class PriceComparisonEngine:
    """Main engine for cross-mandi price comparison and analysis"""
    
    def __init__(self):
        self.geo_calculator = GeospatialCalculator()
        self.transport_calculator = TransportationCostCalculator()
    
    async def compare_prices(
        self,
        commodity: str,
        base_location: GeoLocation,
        radius_km: float = 500,
        max_results: int = 20,
        min_quantity: float = 10.0
    ) -> PriceComparison:
        """
        Compare prices across mandis within specified radius
        
        Args:
            commodity: Commodity to compare
            base_location: Base location for comparison
            radius_km: Search radius in kilometers
            max_results: Maximum number of results to return
            min_quantity: Minimum quantity threshold
            
        Returns:
            Comprehensive price comparison
        """
        try:
            # Get price data from all relevant mandis
            price_data_list = await get_commodity_prices(commodity, limit=max_results * 2)
            
            # Filter by radius and create comparisons
            comparisons = []
            
            for price_data in price_data_list:
                # Calculate distance
                distance = self.geo_calculator.calculate_distance(
                    base_location, price_data.mandi.location
                )
                
                # Skip if outside radius
                if distance > radius_km:
                    continue
                
                # Skip if insufficient quantity
                if price_data.price_points and min_quantity > 0:
                    total_quantity = sum(p.quantity or 0 for p in price_data.price_points)
                    if total_quantity < min_quantity:
                        continue
                
                # Calculate transportation cost
                commodity_value = price_data.current_price * min_quantity
                transport_cost = self.transport_calculator.calculate_cost(
                    distance, commodity, commodity_value
                )
                
                # Calculate net profit (price - transportation cost per unit)
                transport_cost_per_unit = transport_cost.total_cost / min_quantity
                net_profit = price_data.current_price - transport_cost_per_unit
                
                # Calculate profit margin percentage
                profit_margin = (net_profit / price_data.current_price) * 100 if price_data.current_price > 0 else 0
                
                # Calculate recommendation score (weighted combination of factors)
                recommendation_score = self._calculate_recommendation_score(
                    price_data, transport_cost, net_profit, distance
                )
                
                comparison = MandiComparison(
                    mandi=price_data.mandi,
                    price_data=price_data,
                    transportation_cost=transport_cost,
                    net_profit=net_profit,
                    profit_margin_percent=profit_margin,
                    recommendation_score=recommendation_score
                )
                
                comparisons.append(comparison)
            
            # Sort by recommendation score (highest first)
            comparisons.sort(key=lambda x: x.recommendation_score, reverse=True)
            
            # Limit results
            comparisons = comparisons[:max_results]
            
            # Calculate summary statistics
            if comparisons:
                prices = [c.price_data.current_price for c in comparisons]
                average_price = sum(prices) / len(prices)
                price_variance = sum((p - average_price) ** 2 for p in prices) / len(prices)
                
                # Find best options
                best_price_mandi = min(comparisons, key=lambda x: x.price_data.current_price).mandi.id
                best_profit_mandi = max(comparisons, key=lambda x: x.net_profit).mandi.id
            else:
                average_price = 0.0
                price_variance = 0.0
                best_price_mandi = None
                best_profit_mandi = None
            
            return PriceComparison(
                commodity=commodity,
                base_location=base_location,
                comparisons=comparisons,
                best_price_mandi=best_price_mandi,
                best_profit_mandi=best_profit_mandi,
                average_price=average_price,
                price_variance=price_variance
            )
            
        except Exception as e:
            logger.error("Failed to compare prices", error=str(e))
            return PriceComparison(
                commodity=commodity,
                base_location=base_location,
                comparisons=[]
            )
    
    def _calculate_recommendation_score(
        self,
        price_data: PriceData,
        transport_cost: TransportationCost,
        net_profit: float,
        distance_km: float
    ) -> float:
        """
        Calculate recommendation score for a mandi
        
        Factors considered:
        - Net profit (40% weight)
        - Price competitiveness (25% weight)
        - Distance/convenience (20% weight)
        - Mandi reliability (15% weight)
        
        Returns:
            Score between 0-100
        """
        score = 0.0
        
        # Net profit score (40% weight)
        if net_profit > 0:
            # Normalize profit to 0-40 scale
            profit_score = min(40, (net_profit / 100) * 10)  # Assume 100 INR profit = 10 points
        else:
            profit_score = 0
        score += profit_score
        
        # Price competitiveness (25% weight)
        # Lower price = higher score
        if price_data.current_price > 0:
            # Assume base price of 2000 INR, score inversely proportional
            price_score = max(0, 25 - (price_data.current_price / 2000) * 25)
        else:
            price_score = 0
        score += price_score
        
        # Distance convenience (20% weight)
        # Closer distance = higher score
        distance_score = max(0, 20 - (distance_km / 500) * 20)  # 500km = 0 points
        score += distance_score
        
        # Mandi reliability (15% weight)
        reliability_score = price_data.mandi.reliability_score * 15
        score += reliability_score
        
        return min(100, max(0, score))
    
    async def analyze_price_trends(
        self,
        commodity: str,
        region: Optional[str] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze price trends for a commodity
        
        Args:
            commodity: Commodity to analyze
            region: Specific region to analyze (optional)
            days_back: Number of days to look back
            
        Returns:
            Trend analysis results
        """
        try:
            # Get historical price data
            price_data_list = await get_commodity_prices(commodity, state=region, limit=1000)
            
            if not price_data_list:
                return {"error": "No price data available"}
            
            # Filter by date range
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            recent_prices = []
            
            for price_data in price_data_list:
                for price_point in price_data.price_points:
                    if price_point.timestamp >= cutoff_date:
                        recent_prices.append({
                            "price": price_point.price,
                            "timestamp": price_point.timestamp,
                            "mandi": price_data.mandi.name,
                            "state": price_data.mandi.location.state
                        })
            
            if len(recent_prices) < 2:
                return {"error": "Insufficient data for trend analysis"}
            
            # Sort by timestamp
            recent_prices.sort(key=lambda x: x["timestamp"])
            
            # Calculate trend metrics
            prices = [p["price"] for p in recent_prices]
            
            # Simple linear trend
            n = len(prices)
            x_values = list(range(n))
            
            # Calculate slope (trend direction)
            x_mean = sum(x_values) / n
            y_mean = sum(prices) / n
            
            numerator = sum((x_values[i] - x_mean) * (prices[i] - y_mean) for i in range(n))
            denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
            
            slope = numerator / denominator if denominator != 0 else 0
            
            # Determine trend direction
            if slope > 5:  # Price increasing by more than 5 INR per day
                trend_direction = "rising"
            elif slope < -5:  # Price decreasing by more than 5 INR per day
                trend_direction = "falling"
            else:
                trend_direction = "stable"
            
            # Calculate volatility (standard deviation)
            price_mean = sum(prices) / len(prices)
            volatility = math.sqrt(sum((p - price_mean) ** 2 for p in prices) / len(prices))
            
            # Calculate min, max, and current price
            min_price = min(prices)
            max_price = max(prices)
            current_price = prices[-1]  # Most recent price
            
            return {
                "commodity": commodity,
                "region": region,
                "analysis_period_days": days_back,
                "data_points": len(recent_prices),
                "trend_direction": trend_direction,
                "trend_slope": slope,
                "current_price": current_price,
                "average_price": price_mean,
                "min_price": min_price,
                "max_price": max_price,
                "volatility": volatility,
                "price_change_percent": ((current_price - prices[0]) / prices[0]) * 100 if prices[0] > 0 else 0,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to analyze price trends", error=str(e))
            return {"error": f"Trend analysis failed: {str(e)}"}
    
    async def find_arbitrage_opportunities(
        self,
        commodity: str,
        base_location: GeoLocation,
        max_distance_km: float = 1000,
        min_profit_margin: float = 10.0
    ) -> List[Dict[str, Any]]:
        """
        Find arbitrage opportunities for a commodity
        
        Args:
            commodity: Commodity to analyze
            base_location: Base location for analysis
            max_distance_km: Maximum distance to consider
            min_profit_margin: Minimum profit margin percentage
            
        Returns:
            List of arbitrage opportunities
        """
        try:
            # Get price comparison
            comparison = await self.compare_prices(
                commodity, base_location, max_distance_km, max_results=50
            )
            
            opportunities = []
            
            for comp in comparison.comparisons:
                if comp.profit_margin_percent >= min_profit_margin:
                    opportunity = {
                        "mandi_id": comp.mandi.id,
                        "mandi_name": comp.mandi.name,
                        "location": {
                            "state": comp.mandi.location.state,
                            "district": comp.mandi.location.district
                        },
                        "price": comp.price_data.current_price,
                        "net_profit": comp.net_profit,
                        "profit_margin_percent": comp.profit_margin_percent,
                        "distance_km": comp.transportation_cost.distance_km,
                        "transport_cost": comp.transportation_cost.total_cost,
                        "estimated_travel_time": comp.transportation_cost.estimated_time_hours,
                        "recommendation_score": comp.recommendation_score,
                        "last_updated": comp.price_data.last_updated.isoformat()
                    }
                    opportunities.append(opportunity)
            
            # Sort by profit margin (highest first)
            opportunities.sort(key=lambda x: x["profit_margin_percent"], reverse=True)
            
            return opportunities
            
        except Exception as e:
            logger.error("Failed to find arbitrage opportunities", error=str(e))
            return []