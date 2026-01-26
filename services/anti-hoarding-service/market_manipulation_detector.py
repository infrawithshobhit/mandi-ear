"""
Market Manipulation Detection System
Part of the Supply-Demand Analysis System for Anti-Hoarding Detection Service
"""

import asyncio
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import statistics
from collections import defaultdict

from models import (
    MarketManipulationAlert, AnomalyType, AnomalySeverity, MarketManipulationType,
    PriceAnomaly, InventoryAnomaly, StockpilingPattern, SupplyDemandBalance
)

logger = structlog.get_logger()

class MarketManipulationDetector:
    """Market manipulation detection system"""
    
    def __init__(self):
        pass
    
    async def detect_market_manipulation(
        self,
        commodity: str,
        variety: Optional[str],
        region: str,
        price_anomalies: List[PriceAnomaly],
        inventory_anomalies: List[InventoryAnomaly],
        stockpiling_patterns: List[StockpilingPattern],
        supply_demand_balance: SupplyDemandBalance
    ) -> List[MarketManipulationAlert]:
        """
        Detect market manipulation patterns
        
        Implements Requirement 7.2: WHEN supply chain manipulation is detected, 
        THE System SHALL alert farmers about artificial scarcity and suggest alternative markets
        """
        try:
            alerts = []
            
            # Detect artificial scarcity manipulation
            scarcity_alerts = await self._detect_artificial_scarcity(
                commodity, variety, region, price_anomalies, inventory_anomalies, supply_demand_balance
            )
            alerts.extend(scarcity_alerts)
            
            # Detect hoarding manipulation
            hoarding_alerts = await self._detect_hoarding_manipulation(
                commodity, variety, region, stockpiling_patterns, supply_demand_balance
            )
            alerts.extend(hoarding_alerts)
            
            # Detect price fixing patterns
            price_fixing_alerts = await self._detect_price_fixing(
                commodity, variety, region, price_anomalies
            )
            alerts.extend(price_fixing_alerts)
            
            # Detect supply restriction manipulation
            supply_restriction_alerts = await self._detect_supply_restriction(
                commodity, variety, region, inventory_anomalies, supply_demand_balance
            )
            alerts.extend(supply_restriction_alerts)
            
            logger.info(
                "Market manipulation detection completed",
                commodity=commodity,
                variety=variety,
                region=region,
                alerts_generated=len(alerts)
            )
            
            return alerts
            
        except Exception as e:
            logger.error("Error in market manipulation detection", error=str(e))
            return []
    
    async def _detect_artificial_scarcity(
        self,
        commodity: str,
        variety: Optional[str],
        region: str,
        price_anomalies: List[PriceAnomaly],
        inventory_anomalies: List[InventoryAnomaly],
        supply_demand_balance: SupplyDemandBalance
    ) -> List[MarketManipulationAlert]:
        """Detect artificial scarcity manipulation"""
        alerts = []
        
        try:
            # Look for price spikes with adequate supply
            significant_price_spikes = [
                anomaly for anomaly in price_anomalies
                if anomaly.severity in [AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]
                and anomaly.deviation_percentage > 30
            ]
            
            # Check if supply is actually adequate
            if (significant_price_spikes and 
                supply_demand_balance.balance_status in ["balanced", "surplus"] and
                supply_demand_balance.available_supply > supply_demand_balance.estimated_demand * 0.8):
                
                # Look for inventory hoarding patterns
                hoarding_anomalies = [
                    anomaly for anomaly in inventory_anomalies
                    if anomaly.anomaly_type == AnomalyType.INVENTORY_HOARDING
                ]
                
                if hoarding_anomalies:
                    # Generate artificial scarcity alert
                    alert = MarketManipulationAlert(
                        manipulation_type=MarketManipulationType.SUPPLY_RESTRICTION,
                        severity=AnomalySeverity.HIGH,
                        price_anomaly_ids=[anomaly.id for anomaly in significant_price_spikes],
                        inventory_anomaly_ids=[anomaly.id for anomaly in hoarding_anomalies],
                        title=f"Artificial Scarcity Detected - {commodity}",
                        message=(
                            f"Artificial scarcity detected for {commodity} in {region}. "
                            f"Despite adequate supply levels ({supply_demand_balance.available_supply:.0f} units), "
                            f"prices have spiked by up to {max(a.deviation_percentage for a in significant_price_spikes):.1f}%. "
                            f"This appears to be caused by inventory hoarding across {len(hoarding_anomalies)} locations."
                        ),
                        commodity=commodity,
                        affected_regions=[region],
                        estimated_impact=f"Price inflation of {max(a.deviation_percentage for a in significant_price_spikes):.1f}%",
                        farmer_recommendations=[
                            "Consider alternative markets with normal pricing",
                            "Wait for market correction if possible",
                            "Report suspicious pricing to authorities",
                            "Form farmer groups for collective bargaining"
                        ],
                        alternative_markets=self._suggest_alternative_markets(commodity, region),
                        authority_actions=[
                            "Investigate inventory hoarding patterns",
                            "Monitor price movements closely",
                            "Consider market intervention if needed",
                            "Increase market transparency measures"
                        ],
                        confidence_score=0.8,
                        evidence_summary={
                            "price_spikes": len(significant_price_spikes),
                            "hoarding_locations": len(hoarding_anomalies),
                            "supply_adequacy": supply_demand_balance.balance_status,
                            "supply_demand_ratio": supply_demand_balance.supply_demand_ratio
                        }
                    )
                    
                    alerts.append(alert)
                    
                    logger.warning(
                        "Artificial scarcity manipulation detected",
                        commodity=commodity,
                        region=region,
                        price_spikes=len(significant_price_spikes),
                        hoarding_locations=len(hoarding_anomalies)
                    )
            
            return alerts
            
        except Exception as e:
            logger.error("Error detecting artificial scarcity", error=str(e))
            return []
    
    async def _detect_hoarding_manipulation(
        self,
        commodity: str,
        variety: Optional[str],
        region: str,
        stockpiling_patterns: List[StockpilingPattern],
        supply_demand_balance: SupplyDemandBalance
    ) -> List[MarketManipulationAlert]:
        """Detect hoarding manipulation patterns"""
        alerts = []
        
        try:
            # Look for coordinated stockpiling patterns
            coordinated_patterns = [
                pattern for pattern in stockpiling_patterns
                if pattern.pattern_type == "coordinated" and
                   pattern.severity in [AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]
            ]
            
            if coordinated_patterns:
                total_accumulated = sum(pattern.total_accumulated_quantity for pattern in coordinated_patterns)
                involved_locations = set()
                for pattern in coordinated_patterns:
                    involved_locations.update(pattern.involved_locations)
                
                # Generate hoarding manipulation alert
                alert = MarketManipulationAlert(
                    manipulation_type=MarketManipulationType.HOARDING,
                    severity=AnomalySeverity.CRITICAL,
                    stockpiling_pattern_ids=[pattern.id for pattern in coordinated_patterns],
                    title=f"Coordinated Hoarding Detected - {commodity}",
                    message=(
                        f"Coordinated hoarding detected for {commodity} across {len(involved_locations)} locations. "
                        f"Total accumulated quantity: {total_accumulated:.0f} units. "
                        f"This coordinated stockpiling may be artificially restricting supply to inflate prices."
                    ),
                    commodity=commodity,
                    affected_regions=list(involved_locations),
                    estimated_impact=f"Supply restriction of {total_accumulated:.0f} units",
                    farmer_recommendations=[
                        "Seek alternative buyers immediately",
                        "Consider direct-to-consumer sales",
                        "Report coordinated hoarding to authorities",
                        "Form farmer cooperatives for better bargaining power"
                    ],
                    alternative_markets=self._suggest_alternative_markets(commodity, region),
                    authority_actions=[
                        "Investigate coordinated hoarding network",
                        "Consider releasing strategic reserves",
                        "Implement anti-hoarding measures",
                        "Monitor inventory movements closely"
                    ],
                    confidence_score=0.9,
                    evidence_summary={
                        "coordinated_patterns": len(coordinated_patterns),
                        "total_accumulated": total_accumulated,
                        "involved_locations": len(involved_locations),
                        "pattern_duration": max(p.pattern_duration_days for p in coordinated_patterns)
                    }
                )
                
                alerts.append(alert)
                
                logger.warning(
                    "Coordinated hoarding manipulation detected",
                    commodity=commodity,
                    region=region,
                    patterns=len(coordinated_patterns),
                    total_accumulated=total_accumulated
                )
            
            return alerts
            
        except Exception as e:
            logger.error("Error detecting hoarding manipulation", error=str(e))
            return []
    
    async def _detect_price_fixing(
        self,
        commodity: str,
        variety: Optional[str],
        region: str,
        price_anomalies: List[PriceAnomaly]
    ) -> List[MarketManipulationAlert]:
        """Detect price fixing patterns"""
        alerts = []
        
        try:
            # Look for synchronized price movements across multiple mandis
            if len(price_anomalies) >= 3:  # Need multiple locations for price fixing
                # Group by mandi
                mandi_anomalies = defaultdict(list)
                for anomaly in price_anomalies:
                    mandi_anomalies[anomaly.mandi_id].append(anomaly)
                
                # Check for synchronized timing and similar price levels
                if len(mandi_anomalies) >= 3:
                    # Check if anomalies occurred within similar timeframe
                    all_timestamps = [anomaly.detected_at for anomaly in price_anomalies]
                    time_span = (max(all_timestamps) - min(all_timestamps)).total_seconds() / 3600  # hours
                    
                    # Check if prices are suspiciously similar
                    current_prices = [anomaly.current_price for anomaly in price_anomalies]
                    price_std = statistics.stdev(current_prices) if len(current_prices) > 1 else 0
                    price_mean = statistics.mean(current_prices)
                    
                    coefficient_of_variation = price_std / price_mean if price_mean > 0 else 0
                    
                    # Suspicious if prices are very similar across mandis and occurred within short timeframe
                    if time_span <= 6 and coefficient_of_variation < 0.05:  # Very similar prices within 6 hours
                        alert = MarketManipulationAlert(
                            manipulation_type=MarketManipulationType.PRICE_FIXING,
                            severity=AnomalySeverity.HIGH,
                            price_anomaly_ids=[anomaly.id for anomaly in price_anomalies],
                            title=f"Potential Price Fixing Detected - {commodity}",
                            message=(
                                f"Potential price fixing detected for {commodity} in {region}. "
                                f"Synchronized price movements across {len(mandi_anomalies)} mandis "
                                f"within {time_span:.1f} hours with unusually similar price levels "
                                f"(variation: {coefficient_of_variation:.3f})."
                            ),
                            commodity=commodity,
                            affected_regions=[region],
                            estimated_impact=f"Artificial price coordination across {len(mandi_anomalies)} markets",
                            farmer_recommendations=[
                                "Seek markets outside the affected region",
                                "Report suspicious price coordination",
                                "Consider holding produce if possible",
                                "Form farmer groups for collective action"
                            ],
                            alternative_markets=self._suggest_alternative_markets(commodity, region),
                            authority_actions=[
                                "Investigate price coordination patterns",
                                "Monitor trader communications",
                                "Implement market surveillance measures",
                                "Consider anti-trust enforcement"
                            ],
                            confidence_score=0.7,
                            evidence_summary={
                                "synchronized_mandis": len(mandi_anomalies),
                                "time_span_hours": time_span,
                                "price_variation": coefficient_of_variation,
                                "average_price": price_mean
                            }
                        )
                        
                        alerts.append(alert)
                        
                        logger.warning(
                            "Potential price fixing detected",
                            commodity=commodity,
                            region=region,
                            mandis=len(mandi_anomalies),
                            time_span=time_span
                        )
            
            return alerts
            
        except Exception as e:
            logger.error("Error detecting price fixing", error=str(e))
            return []
    
    async def _detect_supply_restriction(
        self,
        commodity: str,
        variety: Optional[str],
        region: str,
        inventory_anomalies: List[InventoryAnomaly],
        supply_demand_balance: SupplyDemandBalance
    ) -> List[MarketManipulationAlert]:
        """Detect supply restriction manipulation"""
        alerts = []
        
        try:
            # Look for artificial scarcity patterns
            scarcity_anomalies = [
                anomaly for anomaly in inventory_anomalies
                if anomaly.anomaly_type == AnomalyType.ARTIFICIAL_SCARCITY
            ]
            
            if (scarcity_anomalies and 
                supply_demand_balance.balance_status == "deficit" and
                supply_demand_balance.supply_demand_ratio < 0.8):
                
                alert = MarketManipulationAlert(
                    manipulation_type=MarketManipulationType.SUPPLY_RESTRICTION,
                    severity=AnomalySeverity.HIGH,
                    inventory_anomaly_ids=[anomaly.id for anomaly in scarcity_anomalies],
                    title=f"Supply Restriction Detected - {commodity}",
                    message=(
                        f"Supply restriction detected for {commodity} in {region}. "
                        f"Artificial scarcity patterns identified across {len(scarcity_anomalies)} locations. "
                        f"Supply-demand ratio: {supply_demand_balance.supply_demand_ratio:.2f}"
                    ),
                    commodity=commodity,
                    affected_regions=[region],
                    estimated_impact=f"Supply shortage with ratio {supply_demand_balance.supply_demand_ratio:.2f}",
                    farmer_recommendations=[
                        "Seek alternative markets immediately",
                        "Consider emergency sales to avoid losses",
                        "Report supply restrictions to authorities",
                        "Coordinate with other farmers for collective action"
                    ],
                    alternative_markets=self._suggest_alternative_markets(commodity, region),
                    authority_actions=[
                        "Investigate supply restriction practices",
                        "Consider emergency market interventions",
                        "Monitor inventory movements",
                        "Implement supply chain transparency measures"
                    ],
                    confidence_score=0.8,
                    evidence_summary={
                        "scarcity_locations": len(scarcity_anomalies),
                        "supply_demand_ratio": supply_demand_balance.supply_demand_ratio,
                        "balance_status": supply_demand_balance.balance_status
                    }
                )
                
                alerts.append(alert)
                
                logger.warning(
                    "Supply restriction manipulation detected",
                    commodity=commodity,
                    region=region,
                    scarcity_locations=len(scarcity_anomalies)
                )
            
            return alerts
            
        except Exception as e:
            logger.error("Error detecting supply restriction", error=str(e))
            return []
    
    def _suggest_alternative_markets(self, commodity: str, region: str) -> List[str]:
        """Suggest alternative markets for farmers"""
        # Mock alternative market suggestions - in production would use real market data
        alternative_markets = [
            f"Online platform for {commodity}",
            f"Cooperative markets in neighboring districts",
            f"Direct-to-consumer sales channels",
            f"Export markets for {commodity}",
            f"Processing units requiring {commodity}"
        ]
        
        return alternative_markets[:3]  # Return top 3 suggestions