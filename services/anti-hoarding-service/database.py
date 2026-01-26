"""
Database operations for Anti-Hoarding Detection Service
"""

import asyncio
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from models import (
    PriceAnomaly, InventoryAnomaly, StockpilingPattern, 
    MarketManipulationAlert, SupplyDemandBalance, EvidenceRecord,
    AnomalyType, AnomalySeverity, DetectionStatistics
)

logger = structlog.get_logger()

# Mock database operations - In production, these would connect to actual databases
class AnomalyDatabase:
    """Database operations for anomaly detection data"""
    
    def __init__(self):
        # In-memory storage for demonstration
        self.price_anomalies: Dict[str, PriceAnomaly] = {}
        self.inventory_anomalies: Dict[str, InventoryAnomaly] = {}
        self.stockpiling_patterns: Dict[str, StockpilingPattern] = {}
        self.manipulation_alerts: Dict[str, MarketManipulationAlert] = {}
        self.supply_demand_balances: Dict[str, SupplyDemandBalance] = {}
        self.evidence_records: Dict[str, EvidenceRecord] = {}
    
    async def store_price_anomaly(self, anomaly: PriceAnomaly) -> bool:
        """Store price anomaly in database"""
        try:
            self.price_anomalies[anomaly.id] = anomaly
            logger.info("Price anomaly stored", anomaly_id=anomaly.id, commodity=anomaly.commodity)
            return True
        except Exception as e:
            logger.error("Failed to store price anomaly", error=str(e))
            return False
    
    async def store_inventory_anomaly(self, anomaly: InventoryAnomaly) -> bool:
        """Store inventory anomaly in database"""
        try:
            self.inventory_anomalies[anomaly.id] = anomaly
            logger.info("Inventory anomaly stored", anomaly_id=anomaly.id, commodity=anomaly.commodity)
            return True
        except Exception as e:
            logger.error("Failed to store inventory anomaly", error=str(e))
            return False
    
    async def store_stockpiling_pattern(self, pattern: StockpilingPattern) -> bool:
        """Store stockpiling pattern in database"""
        try:
            self.stockpiling_patterns[pattern.id] = pattern
            logger.info("Stockpiling pattern stored", pattern_id=pattern.id, commodity=pattern.commodity)
            return True
        except Exception as e:
            logger.error("Failed to store stockpiling pattern", error=str(e))
            return False
    
    async def store_manipulation_alert(self, alert: MarketManipulationAlert) -> bool:
        """Store market manipulation alert in database"""
        try:
            self.manipulation_alerts[alert.id] = alert
            logger.info("Manipulation alert stored", alert_id=alert.id, commodity=alert.commodity)
            return True
        except Exception as e:
            logger.error("Failed to store manipulation alert", error=str(e))
            return False
    
    async def store_supply_demand_balance(self, balance: SupplyDemandBalance) -> bool:
        """Store supply-demand balance in database"""
        try:
            self.supply_demand_balances[balance.id] = balance
            logger.info("Supply-demand balance stored", balance_id=balance.id, commodity=balance.commodity)
            return True
        except Exception as e:
            logger.error("Failed to store supply-demand balance", error=str(e))
            return False
    
    async def store_evidence_record(self, evidence: EvidenceRecord) -> bool:
        """Store evidence record in database"""
        try:
            self.evidence_records[evidence.id] = evidence
            logger.info("Evidence record stored", evidence_id=evidence.id, anomaly_id=evidence.anomaly_id)
            return True
        except Exception as e:
            logger.error("Failed to store evidence record", error=str(e))
            return False
    
    async def get_price_anomalies(
        self,
        commodity: Optional[str] = None,
        severity: Optional[AnomalySeverity] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[PriceAnomaly]:
        """Retrieve price anomalies with filters"""
        try:
            anomalies = list(self.price_anomalies.values())
            
            # Apply filters
            if commodity:
                anomalies = [a for a in anomalies if a.commodity.lower() == commodity.lower()]
            
            if severity:
                anomalies = [a for a in anomalies if a.severity == severity]
            
            if start_date:
                anomalies = [a for a in anomalies if a.detected_at >= start_date]
            
            if end_date:
                anomalies = [a for a in anomalies if a.detected_at <= end_date]
            
            # Sort by detection time (most recent first)
            anomalies.sort(key=lambda x: x.detected_at, reverse=True)
            
            return anomalies[:limit]
            
        except Exception as e:
            logger.error("Failed to retrieve price anomalies", error=str(e))
            return []
    
    async def get_inventory_anomalies(
        self,
        commodity: Optional[str] = None,
        region: Optional[str] = None,
        anomaly_type: Optional[AnomalyType] = None,
        limit: int = 100
    ) -> List[InventoryAnomaly]:
        """Retrieve inventory anomalies with filters"""
        try:
            anomalies = list(self.inventory_anomalies.values())
            
            # Apply filters
            if commodity:
                anomalies = [a for a in anomalies if a.commodity.lower() == commodity.lower()]
            
            if region:
                anomalies = [a for a in anomalies if region.lower() in a.region.lower()]
            
            if anomaly_type:
                anomalies = [a for a in anomalies if a.anomaly_type == anomaly_type]
            
            # Sort by detection time (most recent first)
            anomalies.sort(key=lambda x: x.detected_at, reverse=True)
            
            return anomalies[:limit]
            
        except Exception as e:
            logger.error("Failed to retrieve inventory anomalies", error=str(e))
            return []
    
    async def get_stockpiling_patterns(
        self,
        commodity: Optional[str] = None,
        pattern_type: Optional[str] = None,
        severity: Optional[AnomalySeverity] = None,
        limit: int = 100
    ) -> List[StockpilingPattern]:
        """Retrieve stockpiling patterns with filters"""
        try:
            patterns = list(self.stockpiling_patterns.values())
            
            # Apply filters
            if commodity:
                patterns = [p for p in patterns if p.commodity.lower() == commodity.lower()]
            
            if pattern_type:
                patterns = [p for p in patterns if p.pattern_type == pattern_type]
            
            if severity:
                patterns = [p for p in patterns if p.severity == severity]
            
            # Sort by detection time (most recent first)
            patterns.sort(key=lambda x: x.detected_at, reverse=True)
            
            return patterns[:limit]
            
        except Exception as e:
            logger.error("Failed to retrieve stockpiling patterns", error=str(e))
            return []
    
    async def get_manipulation_alerts(
        self,
        commodity: Optional[str] = None,
        severity: Optional[AnomalySeverity] = None,
        is_sent: Optional[bool] = None,
        limit: int = 100
    ) -> List[MarketManipulationAlert]:
        """Retrieve manipulation alerts with filters"""
        try:
            alerts = list(self.manipulation_alerts.values())
            
            # Apply filters
            if commodity:
                alerts = [a for a in alerts if a.commodity.lower() == commodity.lower()]
            
            if severity:
                alerts = [a for a in alerts if a.severity == severity]
            
            if is_sent is not None:
                alerts = [a for a in alerts if a.is_sent == is_sent]
            
            # Sort by generation time (most recent first)
            alerts.sort(key=lambda x: x.generated_at, reverse=True)
            
            return alerts[:limit]
            
        except Exception as e:
            logger.error("Failed to retrieve manipulation alerts", error=str(e))
            return []
    
    async def get_supply_demand_balances(
        self,
        commodity: Optional[str] = None,
        region: Optional[str] = None,
        balance_status: Optional[str] = None,
        limit: int = 100
    ) -> List[SupplyDemandBalance]:
        """Retrieve supply-demand balances with filters"""
        try:
            balances = list(self.supply_demand_balances.values())
            
            # Apply filters
            if commodity:
                balances = [b for b in balances if b.commodity.lower() == commodity.lower()]
            
            if region:
                balances = [b for b in balances if region.lower() in b.region.lower()]
            
            if balance_status:
                balances = [b for b in balances if b.balance_status == balance_status]
            
            # Sort by calculation time (most recent first)
            balances.sort(key=lambda x: x.calculated_at, reverse=True)
            
            return balances[:limit]
            
        except Exception as e:
            logger.error("Failed to retrieve supply-demand balances", error=str(e))
            return []
    
    async def get_evidence_records(
        self,
        anomaly_id: str,
        evidence_type: Optional[str] = None
    ) -> List[EvidenceRecord]:
        """Retrieve evidence records for an anomaly"""
        try:
            records = [
                record for record in self.evidence_records.values()
                if record.anomaly_id == anomaly_id
            ]
            
            if evidence_type:
                records = [r for r in records if r.evidence_type == evidence_type]
            
            # Sort by collection time (most recent first)
            records.sort(key=lambda x: x.collected_at, reverse=True)
            
            return records
            
        except Exception as e:
            logger.error("Failed to retrieve evidence records", error=str(e))
            return []
    
    async def update_anomaly_status(
        self,
        anomaly_id: str,
        anomaly_type: str,
        is_confirmed: bool,
        is_resolved: bool = False,
        resolution_notes: Optional[str] = None
    ) -> bool:
        """Update anomaly confirmation and resolution status"""
        try:
            if anomaly_type == "price":
                if anomaly_id in self.price_anomalies:
                    anomaly = self.price_anomalies[anomaly_id]
                    anomaly.is_confirmed = is_confirmed
                    anomaly.is_resolved = is_resolved
                    if resolution_notes:
                        anomaly.resolution_notes = resolution_notes
                    if is_resolved:
                        anomaly.resolved_at = datetime.utcnow()
                    return True
            
            elif anomaly_type == "inventory":
                if anomaly_id in self.inventory_anomalies:
                    anomaly = self.inventory_anomalies[anomaly_id]
                    anomaly.is_confirmed = is_confirmed
                    anomaly.is_resolved = is_resolved
                    return True
            
            elif anomaly_type == "stockpiling":
                if anomaly_id in self.stockpiling_patterns:
                    pattern = self.stockpiling_patterns[anomaly_id]
                    pattern.is_confirmed = is_confirmed
                    pattern.is_resolved = is_resolved
                    return True
            
            return False
            
        except Exception as e:
            logger.error("Failed to update anomaly status", error=str(e))
            return False
    
    async def get_detection_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> DetectionStatistics:
        """Calculate detection statistics for a time period"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Filter anomalies by date range
            price_anomalies = [
                a for a in self.price_anomalies.values()
                if start_date <= a.detected_at <= end_date
            ]
            
            inventory_anomalies = [
                a for a in self.inventory_anomalies.values()
                if start_date <= a.detected_at <= end_date
            ]
            
            stockpiling_patterns = [
                p for p in self.stockpiling_patterns.values()
                if start_date <= p.detected_at <= end_date
            ]
            
            # Calculate counts
            total_anomalies = len(price_anomalies) + len(inventory_anomalies) + len(stockpiling_patterns)
            
            # Count by severity
            all_anomalies = price_anomalies + inventory_anomalies + stockpiling_patterns
            critical_count = sum(1 for a in all_anomalies if a.severity == AnomalySeverity.CRITICAL)
            high_count = sum(1 for a in all_anomalies if a.severity == AnomalySeverity.HIGH)
            medium_count = sum(1 for a in all_anomalies if a.severity == AnomalySeverity.MEDIUM)
            low_count = sum(1 for a in all_anomalies if a.severity == AnomalySeverity.LOW)
            
            # Count confirmed and resolved
            confirmed_count = sum(1 for a in all_anomalies if a.is_confirmed)
            resolved_count = sum(1 for a in all_anomalies if a.is_resolved)
            
            # Calculate false positives (confirmed as false)
            false_positives = sum(
                1 for a in all_anomalies 
                if hasattr(a, 'is_confirmed') and not a.is_confirmed and a.is_resolved
            )
            
            # Calculate accuracy rate
            if total_anomalies > 0:
                accuracy_rate = (confirmed_count - false_positives) / total_anomalies
            else:
                accuracy_rate = 0.0
            
            return DetectionStatistics(
                total_anomalies_detected=total_anomalies,
                price_anomalies_count=len(price_anomalies),
                inventory_anomalies_count=len(inventory_anomalies),
                stockpiling_patterns_count=len(stockpiling_patterns),
                critical_anomalies=critical_count,
                high_severity_anomalies=high_count,
                medium_severity_anomalies=medium_count,
                low_severity_anomalies=low_count,
                confirmed_anomalies=confirmed_count,
                resolved_anomalies=resolved_count,
                false_positives=false_positives,
                average_detection_time_minutes=15.0,  # Mock value
                accuracy_rate=accuracy_rate,
                statistics_period_start=start_date,
                statistics_period_end=end_date
            )
            
        except Exception as e:
            logger.error("Failed to calculate detection statistics", error=str(e))
            return DetectionStatistics(
                total_anomalies_detected=0,
                statistics_period_start=start_date or datetime.utcnow(),
                statistics_period_end=end_date or datetime.utcnow()
            )

# Mock data access functions for integration with other services
async def get_price_data_for_analysis(
    commodity: str,
    variety: Optional[str] = None,
    region: Optional[str] = None,
    days_back: int = 30,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    Get price data from price discovery service for anomaly analysis
    In production, this would call the price discovery service API
    """
    try:
        # Mock price data - in production, this would fetch from price discovery service
        from datetime import datetime, timedelta
        import random
        
        price_data = []
        base_price = 2000.0  # Base price per quintal
        
        for i in range(min(limit, days_back * 5)):  # ~5 data points per day
            timestamp = datetime.utcnow() - timedelta(days=days_back - i//5)
            
            # Add some realistic price variation
            price_variation = random.uniform(-0.1, 0.1)  # ±10% variation
            current_price = base_price * (1 + price_variation)
            
            # Occasionally add price spikes for testing
            if random.random() < 0.05:  # 5% chance of spike
                spike_factor = random.uniform(1.3, 1.8)  # 30-80% spike
                current_price *= spike_factor
            
            price_data.append({
                "commodity": commodity,
                "variety": variety,
                "price": current_price,
                "quantity": random.uniform(10, 100),
                "mandi_id": f"mandi_{random.randint(1, 10)}",
                "mandi_name": f"Test Mandi {random.randint(1, 10)}",
                "district": "Test District",
                "state": region or "Test State",
                "timestamp": timestamp,
                "confidence": random.uniform(0.7, 0.95)
            })
        
        return price_data
        
    except Exception as e:
        logger.error("Failed to get price data for analysis", error=str(e))
        return []

async def get_inventory_data_for_analysis(
    commodity: str,
    variety: Optional[str] = None,
    region: Optional[str] = None,
    days_back: int = 30,
    limit: int = 500
) -> List[Dict[str, Any]]:
    """
    Get inventory data from various sources for anomaly analysis
    In production, this would aggregate data from multiple sources
    """
    try:
        # Mock inventory data
        import random
        
        inventory_data = []
        base_inventory = 1000.0  # Base inventory level
        
        for i in range(min(limit, days_back * 2)):  # ~2 data points per day
            timestamp = datetime.utcnow() - timedelta(days=days_back - i//2)
            
            # Add realistic inventory variation
            inventory_variation = random.uniform(-0.2, 0.3)  # -20% to +30% variation
            current_inventory = base_inventory * (1 + inventory_variation)
            
            # Occasionally add hoarding patterns for testing
            if random.random() < 0.1:  # 10% chance of unusual accumulation
                hoarding_factor = random.uniform(1.5, 2.5)  # 50-150% increase
                current_inventory *= hoarding_factor
            
            inventory_data.append({
                "commodity": commodity,
                "variety": variety,
                "inventory_level": current_inventory,
                "mandi_id": f"mandi_{random.randint(1, 10)}",
                "mandi_name": f"Test Mandi {random.randint(1, 10)}",
                "district": "Test District",
                "state": region or "Test State",
                "timestamp": timestamp,
                "storage_capacity": base_inventory * 2.0
            })
        
        return inventory_data
        
    except Exception as e:
        logger.error("Failed to get inventory data for analysis", error=str(e))
        return []

# Global database instance
anomaly_db = AnomalyDatabase()

# Convenience functions for external access
async def store_price_anomaly(anomaly: PriceAnomaly) -> bool:
    """Store price anomaly"""
    return await anomaly_db.store_price_anomaly(anomaly)

async def store_inventory_anomaly(anomaly: InventoryAnomaly) -> bool:
    """Store inventory anomaly"""
    return await anomaly_db.store_inventory_anomaly(anomaly)

async def store_stockpiling_pattern(pattern: StockpilingPattern) -> bool:
    """Store stockpiling pattern"""
    return await anomaly_db.store_stockpiling_pattern(pattern)

async def get_recent_anomalies(
    commodity: Optional[str] = None,
    hours_back: int = 24
) -> Dict[str, List]:
    """Get recent anomalies across all types"""
    start_time = datetime.utcnow() - timedelta(hours=hours_back)
    
    price_anomalies = await anomaly_db.get_price_anomalies(
        commodity=commodity,
        start_date=start_time
    )
    
    inventory_anomalies = await anomaly_db.get_inventory_anomalies(
        commodity=commodity
    )
    
    stockpiling_patterns = await anomaly_db.get_stockpiling_patterns(
        commodity=commodity
    )
    
    return {
        "price_anomalies": price_anomalies,
        "inventory_anomalies": inventory_anomalies,
        "stockpiling_patterns": stockpiling_patterns
    }