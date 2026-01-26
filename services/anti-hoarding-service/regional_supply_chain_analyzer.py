"""
Regional Supply Chain Analysis System
Part of the Supply-Demand Analysis System for Anti-Hoarding Detection Service
"""

import asyncio
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import statistics
from collections import defaultdict
from dataclasses import dataclass

logger = structlog.get_logger()

@dataclass
class RegionalSupplyChain:
    """Regional supply chain analysis data"""
    region: str
    commodity: str
    variety: Optional[str]
    supply_sources: Dict[str, float]  # source_region -> supply_amount
    demand_destinations: Dict[str, float]  # destination_region -> demand_amount
    transportation_costs: Dict[str, float]  # route -> cost_per_unit
    bottlenecks: List[str]
    efficiency_score: float
    vulnerability_factors: List[str]

class RegionalSupplyChainAnalyzer:
    """Regional supply chain analysis system"""
    
    def __init__(self):
        pass
    
    async def analyze_regional_supply_chain(
        self,
        commodity: str,
        variety: Optional[str],
        regions: List[str],
        price_data: List[Dict[str, Any]],
        inventory_data: List[Dict[str, Any]],
        transportation_data: Optional[List[Dict[str, Any]]] = None
    ) -> List[RegionalSupplyChain]:
        """
        Analyze regional supply chain patterns and efficiency
        
        Implements regional supply chain analysis component of task 10.3
        """
        try:
            supply_chains = []
            
            for region in regions:
                # Filter data for this region
                regional_price_data = [
                    p for p in price_data
                    if region.lower() in p.get("state", "").lower() or 
                       region.lower() in p.get("district", "").lower()
                ]
                
                regional_inventory_data = [
                    inv for inv in inventory_data
                    if region.lower() in inv.get("state", "").lower() or 
                       region.lower() in inv.get("district", "").lower()
                ]
                
                if not regional_price_data and not regional_inventory_data:
                    continue
                
                # Analyze supply sources
                supply_sources = await self._analyze_supply_sources(
                    region, commodity, regional_inventory_data
                )
                
                # Analyze demand destinations
                demand_destinations = await self._analyze_demand_destinations(
                    region, commodity, regional_price_data
                )
                
                # Calculate transportation costs
                transportation_costs = await self._calculate_transportation_costs(
                    region, supply_sources, demand_destinations, transportation_data
                )
                
                # Identify bottlenecks
                bottlenecks = await self._identify_supply_chain_bottlenecks(
                    region, commodity, regional_price_data, regional_inventory_data
                )
                
                # Calculate efficiency score
                efficiency_score = await self._calculate_supply_chain_efficiency(
                    supply_sources, demand_destinations, transportation_costs, bottlenecks
                )
                
                # Identify vulnerability factors
                vulnerability_factors = await self._identify_vulnerability_factors(
                    region, commodity, supply_sources, demand_destinations
                )
                
                supply_chain = RegionalSupplyChain(
                    region=region,
                    commodity=commodity,
                    variety=variety,
                    supply_sources=supply_sources,
                    demand_destinations=demand_destinations,
                    transportation_costs=transportation_costs,
                    bottlenecks=bottlenecks,
                    efficiency_score=efficiency_score,
                    vulnerability_factors=vulnerability_factors
                )
                
                supply_chains.append(supply_chain)
                
                logger.info(
                    "Regional supply chain analyzed",
                    region=region,
                    commodity=commodity,
                    efficiency_score=efficiency_score,
                    bottlenecks=len(bottlenecks)
                )
            
            return supply_chains
            
        except Exception as e:
            logger.error("Error in regional supply chain analysis", error=str(e))
            return []
    
    async def _analyze_supply_sources(
        self,
        region: str,
        commodity: str,
        inventory_data: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Analyze supply sources for a region"""
        supply_sources = defaultdict(float)
        
        try:
            # Group inventory by source state/district
            for inv in inventory_data:
                source_state = inv.get("state", "Unknown")
                inventory_level = inv.get("inventory_level", 0)
                supply_sources[source_state] += inventory_level
            
            return dict(supply_sources)
            
        except Exception as e:
            logger.error("Error analyzing supply sources", error=str(e))
            return {}
    
    async def _analyze_demand_destinations(
        self,
        region: str,
        commodity: str,
        price_data: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Analyze demand destinations for a region"""
        demand_destinations = defaultdict(float)
        
        try:
            # Use trading volumes as demand proxy
            for price in price_data:
                destination_state = price.get("state", "Unknown")
                quantity = price.get("quantity", 0)
                demand_destinations[destination_state] += quantity
            
            return dict(demand_destinations)
            
        except Exception as e:
            logger.error("Error analyzing demand destinations", error=str(e))
            return {}
    
    async def _calculate_transportation_costs(
        self,
        region: str,
        supply_sources: Dict[str, float],
        demand_destinations: Dict[str, float],
        transportation_data: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, float]:
        """Calculate transportation costs between regions"""
        transportation_costs = {}
        
        try:
            # Mock transportation cost calculation - in production would use real logistics data
            base_cost_per_km = 2.0  # Rs per quintal per km
            
            for source in supply_sources.keys():
                for destination in demand_destinations.keys():
                    if source != destination:
                        # Mock distance calculation
                        estimated_distance = 500  # km - would use real distance calculation
                        route_key = f"{source}->{destination}"
                        transportation_costs[route_key] = base_cost_per_km * estimated_distance
            
            # Use real transportation data if available
            if transportation_data:
                for transport in transportation_data:
                    route = transport.get("route", "")
                    cost = transport.get("cost_per_unit", 0)
                    if route and cost:
                        transportation_costs[route] = cost
            
            return transportation_costs
            
        except Exception as e:
            logger.error("Error calculating transportation costs", error=str(e))
            return {}
    
    async def _identify_supply_chain_bottlenecks(
        self,
        region: str,
        commodity: str,
        price_data: List[Dict[str, Any]],
        inventory_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify supply chain bottlenecks"""
        bottlenecks = []
        
        try:
            # Check for price volatility (indicates supply chain stress)
            if price_data:
                prices = [p.get("price", 0) for p in price_data]
                if len(prices) > 1:
                    price_std = statistics.stdev(prices)
                    price_mean = statistics.mean(prices)
                    if price_std / price_mean > 0.2:  # High volatility
                        bottlenecks.append("High price volatility indicating supply chain stress")
            
            # Check for inventory concentration
            if inventory_data:
                mandi_inventories = defaultdict(float)
                for inv in inventory_data:
                    mandi_id = inv.get("mandi_id", "unknown")
                    mandi_inventories[mandi_id] += inv.get("inventory_level", 0)
                
                total_inventory = sum(mandi_inventories.values())
                if total_inventory > 0:
                    # Check if inventory is too concentrated
                    max_concentration = max(mandi_inventories.values()) / total_inventory
                    if max_concentration > 0.6:  # 60% in one location
                        bottlenecks.append("High inventory concentration in single location")
            
            # Seasonal bottlenecks
            current_month = datetime.utcnow().month
            if current_month in [6, 7, 8, 9]:  # Monsoon
                bottlenecks.append("Monsoon season transportation challenges")
            
            # Regional bottlenecks
            if "hill" in region.lower() or "mountain" in region.lower():
                bottlenecks.append("Difficult terrain transportation constraints")
            
            return bottlenecks
            
        except Exception as e:
            logger.error("Error identifying bottlenecks", error=str(e))
            return []
    
    async def _calculate_supply_chain_efficiency(
        self,
        supply_sources: Dict[str, float],
        demand_destinations: Dict[str, float],
        transportation_costs: Dict[str, float],
        bottlenecks: List[str]
    ) -> float:
        """Calculate supply chain efficiency score (0-1)"""
        try:
            efficiency_score = 1.0
            
            # Reduce efficiency based on number of bottlenecks
            bottleneck_penalty = len(bottlenecks) * 0.1
            efficiency_score -= bottleneck_penalty
            
            # Reduce efficiency based on transportation costs
            if transportation_costs:
                avg_transport_cost = statistics.mean(transportation_costs.values())
                # Normalize cost impact (assuming 1000 Rs/quintal is high cost)
                cost_penalty = min(0.3, avg_transport_cost / 1000 * 0.3)
                efficiency_score -= cost_penalty
            
            # Reduce efficiency if supply/demand is imbalanced
            total_supply = sum(supply_sources.values())
            total_demand = sum(demand_destinations.values())
            
            if total_supply > 0 and total_demand > 0:
                balance_ratio = min(total_supply, total_demand) / max(total_supply, total_demand)
                imbalance_penalty = (1 - balance_ratio) * 0.2
                efficiency_score -= imbalance_penalty
            
            return max(0.0, min(1.0, efficiency_score))
            
        except Exception as e:
            logger.error("Error calculating efficiency score", error=str(e))
            return 0.5  # Default medium efficiency
    
    async def _identify_vulnerability_factors(
        self,
        region: str,
        commodity: str,
        supply_sources: Dict[str, float],
        demand_destinations: Dict[str, float]
    ) -> List[str]:
        """Identify supply chain vulnerability factors"""
        vulnerability_factors = []
        
        try:
            # Single source dependency
            if len(supply_sources) == 1:
                vulnerability_factors.append("Single supply source dependency")
            elif len(supply_sources) <= 2:
                vulnerability_factors.append("Limited supply source diversity")
            
            # Geographic concentration
            if len(set(supply_sources.keys())) <= 2:
                vulnerability_factors.append("Geographic concentration of supply sources")
            
            # Seasonal vulnerability
            current_month = datetime.utcnow().month
            if commodity.lower() in ["wheat", "rice"] and current_month in [4, 5, 6]:
                vulnerability_factors.append("Pre-harvest season supply vulnerability")
            
            # Weather vulnerability
            if current_month in [6, 7, 8, 9]:  # Monsoon
                vulnerability_factors.append("Weather-dependent transportation vulnerability")
            
            # Market concentration
            if len(demand_destinations) <= 2:
                vulnerability_factors.append("Limited market diversification")
            
            return vulnerability_factors
            
        except Exception as e:
            logger.error("Error identifying vulnerability factors", error=str(e))
            return []