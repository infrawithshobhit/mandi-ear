"""
Supply-Demand Analysis System for Anti-Hoarding Detection Service
Implements supply-demand balance calculation
"""

import asyncio
import structlog
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import math
import statistics
from dataclasses import dataclass
from collections import defaultdict

from models import (
    SupplyDemandBalance, AnomalyType, AnomalySeverity, GeoLocation
)

logger = structlog.get_logger()

@dataclass
class SupplyMetrics:
    """Supply-side metrics for analysis"""
    total_supply: float
    available_supply: float
    reserved_supply: float
    production_rate: float
    import_volume: float
    storage_capacity: float
    supply_trend: str  # "increasing", "decreasing", "stable"
    supply_sources: List[str]

@dataclass
class DemandMetrics:
    """Demand-side metrics for analysis"""
    estimated_demand: float
    actual_consumption: float
    export_demand: float
    seasonal_demand_factor: float
    demand_trend: str  # "increasing", "decreasing", "stable"
    demand_drivers: List[str]

class SupplyDemandAnalyzer:
    """Core supply-demand analysis engine"""
    
    def __init__(self):
        self.regional_data_cache = {}
        self.analysis_cache = {}
    
    async def calculate_supply_demand_balance(
        self,
        commodity: str,
        variety: Optional[str],
        region: str,
        price_data: List[Dict[str, Any]],
        inventory_data: List[Dict[str, Any]],
        production_data: Optional[List[Dict[str, Any]]] = None,
        consumption_data: Optional[List[Dict[str, Any]]] = None
    ) -> SupplyDemandBalance:
        """
        Calculate supply-demand balance for a commodity in a region
        
        Implements Requirement 7.5: THE System SHALL provide supply-demand balance indicators 
        for each commodity across different regions
        """
        try:
            # Calculate supply metrics
            supply_metrics = await self._calculate_supply_metrics(
                commodity, variety, region, inventory_data, production_data
            )
            
            # Calculate demand metrics
            demand_metrics = await self._calculate_demand_metrics(
                commodity, variety, region, price_data, consumption_data
            )
            
            # Calculate balance indicators
            supply_demand_ratio = (
                supply_metrics.available_supply / demand_metrics.estimated_demand
                if demand_metrics.estimated_demand > 0 else 0.0
            )
            
            # Determine balance status
            balance_status = self._determine_balance_status(supply_demand_ratio)
            
            # Calculate balance score (-1 to 1)
            balance_score = self._calculate_balance_score(supply_demand_ratio)
            
            # Determine price pressure
            price_pressure = self._analyze_price_pressure(
                supply_metrics, demand_metrics, price_data
            )
            
            # Assess volatility risk
            volatility_risk = self._assess_volatility_risk(price_data, supply_metrics, demand_metrics)
            
            # Identify contributing factors
            supply_factors = self._identify_supply_factors(supply_metrics, inventory_data)
            demand_factors = self._identify_demand_factors(demand_metrics, price_data)
            external_factors = self._identify_external_factors(commodity, region)
            
            # Calculate data freshness
            data_freshness_hours = self._calculate_data_freshness(price_data, inventory_data)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                len(price_data), len(inventory_data), data_freshness_hours
            )
            
            balance = SupplyDemandBalance(
                commodity=commodity,
                variety=variety,
                region=region,
                total_supply=supply_metrics.total_supply,
                available_supply=supply_metrics.available_supply,
                reserved_supply=supply_metrics.reserved_supply,
                supply_trend=supply_metrics.supply_trend,
                estimated_demand=demand_metrics.estimated_demand,
                actual_consumption=demand_metrics.actual_consumption,
                demand_trend=demand_metrics.demand_trend,
                supply_demand_ratio=supply_demand_ratio,
                balance_status=balance_status,
                balance_score=balance_score,
                price_pressure_indicator=price_pressure,
                volatility_risk=volatility_risk,
                data_freshness_hours=data_freshness_hours,
                confidence_score=confidence_score,
                supply_factors=supply_factors,
                demand_factors=demand_factors,
                external_factors=external_factors
            )
            
            logger.info(
                "Supply-demand balance calculated",
                commodity=commodity,
                variety=variety,
                region=region,
                balance_status=balance_status,
                supply_demand_ratio=supply_demand_ratio,
                confidence_score=confidence_score
            )
            
            return balance
            
        except Exception as e:
            logger.error("Error calculating supply-demand balance", error=str(e))
            # Return a default balance with low confidence
            return SupplyDemandBalance(
                commodity=commodity,
                variety=variety,
                region=region,
                total_supply=0.0,
                available_supply=0.0,
                reserved_supply=0.0,
                supply_trend="stable",
                estimated_demand=0.0,
                actual_consumption=0.0,
                demand_trend="stable",
                supply_demand_ratio=1.0,
                balance_status="unknown",
                balance_score=0.0,
                price_pressure_indicator="neutral",
                volatility_risk="high",
                data_freshness_hours=24.0,
                confidence_score=0.1,
                supply_factors=["Insufficient data"],
                demand_factors=["Insufficient data"],
                external_factors=["Data quality issues"]
            )
    
    async def _calculate_supply_metrics(
        self,
        commodity: str,
        variety: Optional[str],
        region: str,
        inventory_data: List[Dict[str, Any]],
        production_data: Optional[List[Dict[str, Any]]] = None
    ) -> SupplyMetrics:
        """Calculate comprehensive supply-side metrics"""
        try:
            # Filter inventory data for the region
            regional_inventory = [
                inv for inv in inventory_data
                if region.lower() in inv.get("state", "").lower() or 
                   region.lower() in inv.get("district", "").lower()
            ]
            
            if not regional_inventory:
                # Use all available data if no regional match
                regional_inventory = inventory_data
            
            # Calculate total and available supply
            total_supply = sum(inv.get("inventory_level", 0) for inv in regional_inventory)
            
            # Estimate reserved supply (typically 20-30% held for local consumption)
            reserved_supply = total_supply * 0.25
            available_supply = max(0, total_supply - reserved_supply)
            
            # Calculate production rate (if production data available)
            production_rate = 0.0
            if production_data:
                recent_production = [
                    p.get("production_volume", 0) for p in production_data
                    if (datetime.utcnow() - p.get("timestamp", datetime.utcnow())).days <= 30
                ]
                if recent_production:
                    production_rate = sum(recent_production) / len(recent_production)
            
            # Estimate import volume (mock data - in production would come from trade data)
            import_volume = total_supply * 0.1  # Assume 10% from imports
            
            # Calculate storage capacity
            storage_capacity = sum(
                inv.get("storage_capacity", inv.get("inventory_level", 0) * 1.5)
                for inv in regional_inventory
            )
            
            # Determine supply trend
            supply_trend = self._calculate_supply_trend(regional_inventory)
            
            # Identify supply sources
            supply_sources = list(set(
                inv.get("state", "Unknown") for inv in regional_inventory
            ))
            
            return SupplyMetrics(
                total_supply=total_supply,
                available_supply=available_supply,
                reserved_supply=reserved_supply,
                production_rate=production_rate,
                import_volume=import_volume,
                storage_capacity=storage_capacity,
                supply_trend=supply_trend,
                supply_sources=supply_sources
            )
            
        except Exception as e:
            logger.error("Error calculating supply metrics", error=str(e))
            return SupplyMetrics(
                total_supply=0.0,
                available_supply=0.0,
                reserved_supply=0.0,
                production_rate=0.0,
                import_volume=0.0,
                storage_capacity=0.0,
                supply_trend="stable",
                supply_sources=[]
            )
    
    async def _calculate_demand_metrics(
        self,
        commodity: str,
        variety: Optional[str],
        region: str,
        price_data: List[Dict[str, Any]],
        consumption_data: Optional[List[Dict[str, Any]]] = None
    ) -> DemandMetrics:
        """Calculate comprehensive demand-side metrics"""
        try:
            # Filter price data for the region
            regional_prices = [
                p for p in price_data
                if region.lower() in p.get("state", "").lower() or 
                   region.lower() in p.get("district", "").lower()
            ]
            
            if not regional_prices:
                regional_prices = price_data
            
            # Estimate demand based on trading volumes
            trading_volumes = [p.get("quantity", 0) for p in regional_prices]
            if trading_volumes:
                # Daily demand estimate based on trading activity
                daily_trading_volume = sum(trading_volumes) / max(1, len(trading_volumes))
                estimated_demand = daily_trading_volume * 30  # Monthly demand estimate
            else:
                estimated_demand = 0.0
            
            # Calculate actual consumption (if consumption data available)
            actual_consumption = estimated_demand * 0.8  # Assume 80% of demand is actual consumption
            if consumption_data:
                recent_consumption = [
                    c.get("consumption_volume", 0) for c in consumption_data
                    if (datetime.utcnow() - c.get("timestamp", datetime.utcnow())).days <= 30
                ]
                if recent_consumption:
                    actual_consumption = sum(recent_consumption)
            
            # Estimate export demand (mock data - in production would come from export statistics)
            export_demand = estimated_demand * 0.15  # Assume 15% for export
            
            # Calculate seasonal demand factor
            seasonal_demand_factor = self._calculate_seasonal_demand_factor(commodity)
            
            # Determine demand trend
            demand_trend = self._calculate_demand_trend(regional_prices)
            
            # Identify demand drivers
            demand_drivers = self._identify_demand_drivers(commodity, regional_prices)
            
            return DemandMetrics(
                estimated_demand=estimated_demand,
                actual_consumption=actual_consumption,
                export_demand=export_demand,
                seasonal_demand_factor=seasonal_demand_factor,
                demand_trend=demand_trend,
                demand_drivers=demand_drivers
            )
            
        except Exception as e:
            logger.error("Error calculating demand metrics", error=str(e))
            return DemandMetrics(
                estimated_demand=0.0,
                actual_consumption=0.0,
                export_demand=0.0,
                seasonal_demand_factor=1.0,
                demand_trend="stable",
                demand_drivers=[]
            )
    
    def _calculate_supply_trend(self, inventory_data: List[Dict[str, Any]]) -> str:
        """Calculate supply trend from inventory data"""
        if len(inventory_data) < 2:
            return "stable"
        
        # Sort by timestamp
        sorted_data = sorted(inventory_data, key=lambda x: x.get("timestamp", datetime.utcnow()))
        
        # Calculate trend over recent period
        recent_data = sorted_data[-min(7, len(sorted_data)):]  # Last 7 data points
        if len(recent_data) < 2:
            return "stable"
        
        levels = [inv.get("inventory_level", 0) for inv in recent_data]
        
        # Simple linear trend calculation
        n = len(levels)
        x_values = list(range(n))
        x_mean = sum(x_values) / n
        y_mean = sum(levels) / n
        
        numerator = sum((x_values[i] - x_mean) * (levels[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        
        # Determine trend based on slope
        if slope > y_mean * 0.05:  # 5% increase
            return "increasing"
        elif slope < -y_mean * 0.05:  # 5% decrease
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_demand_trend(self, price_data: List[Dict[str, Any]]) -> str:
        """Calculate demand trend from price and volume data"""
        if len(price_data) < 2:
            return "stable"
        
        # Sort by timestamp
        sorted_data = sorted(price_data, key=lambda x: x.get("timestamp", datetime.utcnow()))
        
        # Calculate trend over recent period
        recent_data = sorted_data[-min(7, len(sorted_data)):]  # Last 7 data points
        if len(recent_data) < 2:
            return "stable"
        
        # Use trading volumes as demand proxy
        volumes = [p.get("quantity", 0) for p in recent_data]
        
        # Simple linear trend calculation
        n = len(volumes)
        x_values = list(range(n))
        x_mean = sum(x_values) / n
        y_mean = sum(volumes) / n
        
        numerator = sum((x_values[i] - x_mean) * (volumes[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        
        # Determine trend based on slope
        if slope > y_mean * 0.05:  # 5% increase
            return "increasing"
        elif slope < -y_mean * 0.05:  # 5% decrease
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_seasonal_demand_factor(self, commodity: str) -> float:
        """Calculate seasonal demand factor based on commodity and current month"""
        current_month = datetime.utcnow().month
        
        # Seasonal patterns for different commodities
        seasonal_patterns = {
            "wheat": {
                1: 1.2, 2: 1.1, 3: 1.0, 4: 0.9, 5: 0.8, 6: 0.8,
                7: 0.9, 8: 1.0, 9: 1.1, 10: 1.2, 11: 1.3, 12: 1.2
            },
            "rice": {
                1: 1.1, 2: 1.0, 3: 0.9, 4: 0.9, 5: 1.0, 6: 1.1,
                7: 1.2, 8: 1.3, 9: 1.2, 10: 1.1, 11: 1.0, 12: 1.1
            },
            "onion": {
                1: 1.3, 2: 1.2, 3: 1.1, 4: 1.0, 5: 0.9, 6: 0.8,
                7: 0.9, 8: 1.0, 9: 1.1, 10: 1.2, 11: 1.3, 12: 1.4
            }
        }
        
        # Default pattern if commodity not found
        default_pattern = {i: 1.0 for i in range(1, 13)}
        
        pattern = seasonal_patterns.get(commodity.lower(), default_pattern)
        return pattern.get(current_month, 1.0)
    
    def _determine_balance_status(self, supply_demand_ratio: float) -> str:
        """Determine balance status from supply-demand ratio"""
        if supply_demand_ratio >= 1.5:
            return "surplus"
        elif supply_demand_ratio >= 0.9:
            return "balanced"
        elif supply_demand_ratio >= 0.6:
            return "deficit"
        else:
            return "critical_shortage"
    
    def _calculate_balance_score(self, supply_demand_ratio: float) -> float:
        """Calculate balance score from -1 (shortage) to 1 (surplus)"""
        if supply_demand_ratio >= 1.5:
            # Surplus: map 1.5+ to 0.25-1.0
            score = 0.25 + min(0.75, (supply_demand_ratio - 1.5) / 2.0)
        elif supply_demand_ratio >= 0.9:
            # Balanced: map 0.9-1.5 to -0.2-0.2
            normalized = (supply_demand_ratio - 0.9) / (1.5 - 0.9)  # 0 to 1
            score = -0.2 + (normalized * 0.4)  # -0.2 to 0.2
        elif supply_demand_ratio >= 0.6:
            # Deficit: map 0.6-0.9 to -0.5--0.2
            normalized = (supply_demand_ratio - 0.6) / (0.9 - 0.6)  # 0 to 1
            score = -0.5 + (normalized * 0.3)  # -0.5 to -0.2
        else:
            # Critical shortage: map 0.0-0.6 to -1.0--0.5
            normalized = supply_demand_ratio / 0.6  # 0 to 1
            score = -1.0 + (normalized * 0.5)  # -1.0 to -0.5
        
        return max(-1.0, min(1.0, score))
    
    def _analyze_price_pressure(
        self,
        supply_metrics: SupplyMetrics,
        demand_metrics: DemandMetrics,
        price_data: List[Dict[str, Any]]
    ) -> str:
        """Analyze price pressure direction"""
        try:
            # Calculate recent price trend
            if len(price_data) < 2:
                return "neutral"
            
            sorted_prices = sorted(price_data, key=lambda x: x.get("timestamp", datetime.utcnow()))
            recent_prices = [p.get("price", 0) for p in sorted_prices[-5:]]  # Last 5 prices
            
            if len(recent_prices) < 2:
                return "neutral"
            
            price_trend = (recent_prices[-1] - recent_prices[0]) / recent_prices[0] * 100
            
            # Consider supply-demand fundamentals
            supply_demand_ratio = (
                supply_metrics.available_supply / demand_metrics.estimated_demand
                if demand_metrics.estimated_demand > 0 else 1.0
            )
            
            # Determine pressure
            if price_trend > 5 or supply_demand_ratio < 0.8:
                return "upward"
            elif price_trend < -5 or supply_demand_ratio > 1.3:
                return "downward"
            else:
                return "neutral"
                
        except Exception as e:
            logger.error("Error analyzing price pressure", error=str(e))
            return "neutral"
    
    def _assess_volatility_risk(
        self,
        price_data: List[Dict[str, Any]],
        supply_metrics: SupplyMetrics,
        demand_metrics: DemandMetrics
    ) -> str:
        """Assess volatility risk level"""
        try:
            if len(price_data) < 5:
                return "medium"
            
            # Calculate price volatility
            prices = [p.get("price", 0) for p in price_data]
            if len(prices) < 2:
                return "medium"
            
            price_std = statistics.stdev(prices)
            price_mean = statistics.mean(prices)
            
            coefficient_of_variation = price_std / price_mean if price_mean > 0 else 0
            
            # Consider supply-demand stability
            supply_stability = 1.0 if supply_metrics.supply_trend == "stable" else 0.5
            demand_stability = 1.0 if demand_metrics.demand_trend == "stable" else 0.5
            
            stability_factor = (supply_stability + demand_stability) / 2
            
            # Calculate risk score
            risk_score = coefficient_of_variation / stability_factor
            
            if risk_score > 0.3:
                return "high"
            elif risk_score > 0.15:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            logger.error("Error assessing volatility risk", error=str(e))
            return "medium"
    
    def _identify_supply_factors(
        self,
        supply_metrics: SupplyMetrics,
        inventory_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify factors affecting supply"""
        factors = []
        
        if supply_metrics.supply_trend == "increasing":
            factors.append("Increasing inventory levels")
        elif supply_metrics.supply_trend == "decreasing":
            factors.append("Declining inventory levels")
        
        if supply_metrics.production_rate > 0:
            factors.append("Active production contributing to supply")
        
        if supply_metrics.import_volume > supply_metrics.total_supply * 0.2:
            factors.append("Significant import dependency")
        
        # Storage capacity utilization
        if supply_metrics.storage_capacity > 0:
            utilization = supply_metrics.total_supply / supply_metrics.storage_capacity
            if utilization > 0.9:
                factors.append("High storage capacity utilization")
            elif utilization < 0.3:
                factors.append("Low storage capacity utilization")
        
        # Regional diversity
        if len(supply_metrics.supply_sources) > 3:
            factors.append("Diversified supply sources")
        elif len(supply_metrics.supply_sources) == 1:
            factors.append("Single source dependency")
        
        return factors
    
    def _identify_demand_factors(
        self,
        demand_metrics: DemandMetrics,
        price_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify factors affecting demand"""
        factors = []
        
        if demand_metrics.demand_trend == "increasing":
            factors.append("Rising demand trend")
        elif demand_metrics.demand_trend == "decreasing":
            factors.append("Declining demand trend")
        
        if demand_metrics.seasonal_demand_factor > 1.2:
            factors.append("High seasonal demand period")
        elif demand_metrics.seasonal_demand_factor < 0.8:
            factors.append("Low seasonal demand period")
        
        if demand_metrics.export_demand > demand_metrics.estimated_demand * 0.2:
            factors.append("Significant export demand")
        
        # Price elasticity indication
        if price_data:
            recent_prices = [p.get("price", 0) for p in price_data[-5:]]
            if recent_prices and max(recent_prices) > min(recent_prices) * 1.2:
                factors.append("Price-sensitive demand patterns")
        
        return factors
    
    def _identify_external_factors(self, commodity: str, region: str) -> List[str]:
        """Identify external factors affecting supply-demand balance"""
        factors = []
        
        # Seasonal factors
        current_month = datetime.utcnow().month
        if current_month in [6, 7, 8, 9]:  # Monsoon season
            factors.append("Monsoon season impact on transportation")
        
        if current_month in [10, 11, 12]:  # Post-harvest season
            factors.append("Post-harvest season supply increase")
        
        # Festival seasons
        if current_month in [10, 11]:  # Diwali season
            factors.append("Festival season demand increase")
        
        # Regional factors
        if "punjab" in region.lower() or "haryana" in region.lower():
            factors.append("Major agricultural production region")
        
        if "maharashtra" in region.lower():
            factors.append("High consumption urban centers")
        
        # Commodity-specific factors
        if commodity.lower() in ["wheat", "rice"]:
            factors.append("Government procurement and MSP influence")
        
        if commodity.lower() in ["onion", "potato"]:
            factors.append("High price volatility commodity")
        
        return factors
    
    def _identify_demand_drivers(self, commodity: str, price_data: List[Dict[str, Any]]) -> List[str]:
        """Identify demand drivers for the commodity"""
        drivers = []
        
        # Seasonal drivers
        current_month = datetime.utcnow().month
        if current_month in [10, 11, 12]:  # Festival season
            drivers.append("Festival season consumption increase")
        
        # Price-based drivers
        if price_data:
            recent_prices = [p.get("price", 0) for p in price_data[-3:]]
            if recent_prices:
                avg_price = sum(recent_prices) / len(recent_prices)
                if avg_price < 1500:  # Low price threshold
                    drivers.append("Attractive pricing driving demand")
                elif avg_price > 3000:  # High price threshold
                    drivers.append("High prices potentially reducing demand")
        
        # Commodity-specific drivers
        if commodity.lower() in ["wheat", "rice"]:
            drivers.append("Staple food consistent demand")
        
        if commodity.lower() in ["onion", "potato"]:
            drivers.append("Essential cooking ingredient demand")
        
        return drivers
    
    def _calculate_data_freshness(
        self,
        price_data: List[Dict[str, Any]],
        inventory_data: List[Dict[str, Any]]
    ) -> float:
        """Calculate data freshness in hours"""
        try:
            all_timestamps = []
            
            # Collect all timestamps
            for p in price_data:
                if "timestamp" in p:
                    all_timestamps.append(p["timestamp"])
            
            for inv in inventory_data:
                if "timestamp" in inv:
                    all_timestamps.append(inv["timestamp"])
            
            if not all_timestamps:
                return 24.0  # Default to 24 hours if no timestamps
            
            # Find most recent timestamp
            most_recent = max(all_timestamps)
            
            # Calculate hours since most recent data
            hours_since = (datetime.utcnow() - most_recent).total_seconds() / 3600
            
            return max(0.0, hours_since)
            
        except Exception as e:
            logger.error("Error calculating data freshness", error=str(e))
            return 24.0
    
    def _calculate_confidence_score(
        self,
        price_data_points: int,
        inventory_data_points: int,
        data_freshness_hours: float
    ) -> float:
        """Calculate confidence score for the analysis"""
        # Data quantity confidence
        data_quantity_score = min(1.0, (price_data_points + inventory_data_points) / 50)
        
        # Data freshness confidence (decreases with age)
        freshness_score = max(0.1, 1.0 - (data_freshness_hours / 48))  # 48 hours = 0 confidence
        
        # Combined confidence
        confidence = (data_quantity_score * 0.6 + freshness_score * 0.4)
        
        return max(0.1, min(1.0, confidence))