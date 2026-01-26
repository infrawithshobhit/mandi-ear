"""
MSP Monitoring Engine
Continuous price vs MSP comparison and violation detection
"""

import asyncio
import structlog
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, date
import aiohttp
from dataclasses import dataclass

from models import (
    MSPRate, MSPViolation, MSPComparisonResult, ViolationType, 
    AlertSeverity, MSPMonitoringStats, MSPSeason
)
from database import (
    get_active_msp_rates, get_current_market_prices, 
    store_msp_violation, get_mandi_info
)

logger = structlog.get_logger()

@dataclass
class MonitoringConfig:
    """Configuration for MSP monitoring"""
    check_interval_minutes: int = 15
    violation_threshold_percentage: float = 5.0  # Alert if price is 5% below MSP
    critical_threshold_percentage: float = 15.0  # Critical alert if 15% below MSP
    min_confidence_score: float = 0.7
    max_price_age_hours: int = 2  # Only consider prices from last 2 hours

class MSPMonitoringEngine:
    """Core MSP monitoring and comparison engine"""
    
    def __init__(self, config: MonitoringConfig = None):
        self.config = config or MonitoringConfig()
        self.is_running = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.current_msp_rates: Dict[str, MSPRate] = {}
        self.violation_cache: Dict[str, MSPViolation] = {}
        
    async def initialize(self):
        """Initialize the monitoring engine"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        await self._load_current_msp_rates()
        logger.info("MSP monitoring engine initialized")
    
    async def shutdown(self):
        """Shutdown the monitoring engine"""
        self.is_running = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self.session:
            await self.session.close()
        
        logger.info("MSP monitoring engine shutdown")
    
    async def start_monitoring(self):
        """Start continuous MSP monitoring"""
        if self.is_running:
            logger.warning("MSP monitoring already running")
            return
        
        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Started MSP monitoring", interval_minutes=self.config.check_interval_minutes)
    
    async def stop_monitoring(self):
        """Stop continuous MSP monitoring"""
        self.is_running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
        logger.info("Stopped MSP monitoring")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                await self._run_monitoring_cycle()
                await asyncio.sleep(self.config.check_interval_minutes * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in monitoring loop", error=str(e))
                await asyncio.sleep(60)  # Wait before retry
    
    async def _run_monitoring_cycle(self):
        """Run a single monitoring cycle"""
        start_time = datetime.utcnow()
        logger.info("Starting MSP monitoring cycle")
        
        try:
            # Refresh MSP rates if needed
            await self._refresh_msp_rates_if_needed()
            
            # Get current market prices
            market_prices = await self._get_current_market_prices()
            
            # Compare prices against MSP
            violations = []
            comparisons = []
            
            for price_data in market_prices:
                comparison = await self._compare_price_with_msp(price_data)
                if comparison:
                    comparisons.append(comparison)
                    
                    if comparison.compliance_status == "violation":
                        violation = await self._create_violation_record(comparison)
                        if violation:
                            violations.append(violation)
            
            # Process violations
            if violations:
                await self._process_violations(violations)
            
            # Update monitoring stats
            await self._update_monitoring_stats(comparisons, violations)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                "MSP monitoring cycle completed",
                comparisons=len(comparisons),
                violations=len(violations),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error("Error in monitoring cycle", error=str(e))
    
    async def _load_current_msp_rates(self):
        """Load current MSP rates from database"""
        try:
            msp_rates = await get_active_msp_rates()
            self.current_msp_rates = {
                f"{rate.commodity}_{rate.variety or 'default'}": rate 
                for rate in msp_rates
            }
            logger.info("Loaded MSP rates", count=len(self.current_msp_rates))
        except Exception as e:
            logger.error("Failed to load MSP rates", error=str(e))
    
    async def _refresh_msp_rates_if_needed(self):
        """Refresh MSP rates if they're outdated"""
        # Check if we need to refresh (e.g., daily or when new season starts)
        last_refresh = getattr(self, '_last_msp_refresh', None)
        if not last_refresh or (datetime.utcnow() - last_refresh).days >= 1:
            await self._load_current_msp_rates()
            self._last_msp_refresh = datetime.utcnow()
    
    async def _get_current_market_prices(self) -> List[Dict[str, Any]]:
        """Get current market prices from price discovery service"""
        try:
            # In production, this would call the price discovery service API
            # For now, we'll simulate getting recent price data
            cutoff_time = datetime.utcnow() - timedelta(hours=self.config.max_price_age_hours)
            market_prices = await get_current_market_prices(
                min_timestamp=cutoff_time,
                min_confidence=self.config.min_confidence_score
            )
            return market_prices
        except Exception as e:
            logger.error("Failed to get market prices", error=str(e))
            return []
    
    async def _compare_price_with_msp(self, price_data: Dict[str, Any]) -> Optional[MSPComparisonResult]:
        """Compare a market price with corresponding MSP rate"""
        try:
            commodity = price_data.get("commodity")
            variety = price_data.get("variety")
            market_price = float(price_data.get("price", 0))
            
            if not commodity or market_price <= 0:
                return None
            
            # Find matching MSP rate
            msp_key = f"{commodity}_{variety or 'default'}"
            msp_rate = self.current_msp_rates.get(msp_key)
            
            if not msp_rate:
                # Try without variety
                msp_key = f"{commodity}_default"
                msp_rate = self.current_msp_rates.get(msp_key)
            
            if not msp_rate:
                logger.debug("No MSP rate found for commodity", commodity=commodity, variety=variety)
                return None
            
            # Calculate price difference
            price_difference = market_price - msp_rate.msp_price
            violation_percentage = abs(price_difference) / msp_rate.msp_price * 100
            
            # Determine compliance status
            compliance_status = "compliant"
            if price_difference < 0:  # Market price below MSP
                if violation_percentage >= self.config.violation_threshold_percentage:
                    compliance_status = "violation"
                else:
                    compliance_status = "warning"
            
            return MSPComparisonResult(
                commodity=commodity,
                variety=variety,
                mandi_id=price_data.get("mandi_id", ""),
                mandi_name=price_data.get("mandi_name", ""),
                location=f"{price_data.get('district', '')}, {price_data.get('state', '')}",
                market_price=market_price,
                msp_price=msp_rate.msp_price,
                price_difference=price_difference,
                compliance_status=compliance_status,
                violation_percentage=violation_percentage if compliance_status != "compliant" else None,
                data_confidence=price_data.get("confidence", 0.8)
            )
            
        except Exception as e:
            logger.error("Error comparing price with MSP", error=str(e))
            return None
    
    async def _create_violation_record(self, comparison: MSPComparisonResult) -> Optional[MSPViolation]:
        """Create a violation record from comparison result"""
        try:
            # Determine violation type and severity
            violation_type = ViolationType.BELOW_MSP
            
            if comparison.violation_percentage >= self.config.critical_threshold_percentage:
                severity = AlertSeverity.CRITICAL
            elif comparison.violation_percentage >= 10.0:
                severity = AlertSeverity.HIGH
            elif comparison.violation_percentage >= 5.0:
                severity = AlertSeverity.MEDIUM
            else:
                severity = AlertSeverity.LOW
            
            violation = MSPViolation(
                commodity=comparison.commodity,
                variety=comparison.variety,
                mandi_id=comparison.mandi_id,
                mandi_name=comparison.mandi_name,
                district=comparison.location.split(",")[0].strip(),
                state=comparison.location.split(",")[1].strip() if "," in comparison.location else "",
                market_price=comparison.market_price,
                msp_price=comparison.msp_price,
                price_difference=comparison.price_difference,
                violation_percentage=comparison.violation_percentage,
                violation_type=violation_type,
                severity=severity,
                evidence={
                    "comparison_data": comparison.dict(),
                    "detection_method": "automated_monitoring",
                    "data_confidence": comparison.data_confidence
                }
            )
            
            return violation
            
        except Exception as e:
            logger.error("Error creating violation record", error=str(e))
            return None
    
    async def _process_violations(self, violations: List[MSPViolation]):
        """Process detected violations"""
        for violation in violations:
            try:
                # Check if this is a duplicate violation
                violation_key = f"{violation.commodity}_{violation.mandi_id}"
                existing_violation = self.violation_cache.get(violation_key)
                
                if existing_violation and not existing_violation.is_resolved:
                    # Update existing violation if price got worse
                    if violation.violation_percentage > existing_violation.violation_percentage:
                        existing_violation.market_price = violation.market_price
                        existing_violation.violation_percentage = violation.violation_percentage
                        existing_violation.severity = violation.severity
                        existing_violation.detected_at = violation.detected_at
                        await store_msp_violation(existing_violation)
                        
                        # Trigger immediate alert for worsening violation
                        await self._trigger_immediate_alert(existing_violation)
                    continue
                
                # Store new violation
                await store_msp_violation(violation)
                self.violation_cache[violation_key] = violation
                
                # Trigger immediate alert for new violation
                await self._trigger_immediate_alert(violation)
                
                logger.warning(
                    "MSP violation detected and alert triggered",
                    commodity=violation.commodity,
                    mandi=violation.mandi_name,
                    market_price=violation.market_price,
                    msp_price=violation.msp_price,
                    violation_percentage=violation.violation_percentage,
                    severity=violation.severity.value
                )
                
            except Exception as e:
                logger.error("Error processing violation", error=str(e))
    
    async def _trigger_immediate_alert(self, violation: MSPViolation):
        """Trigger immediate alert for MSP violation"""
        try:
            # Import here to avoid circular imports
            from alert_system import MSPAlertSystem
            
            # Get or create alert system instance
            if not hasattr(self, '_alert_system'):
                self._alert_system = MSPAlertSystem()
                await self._alert_system.initialize()
            
            # Process violation and generate alerts
            alerts = await self._alert_system.process_violation(violation)
            
            logger.info(
                "Immediate alerts generated for violation",
                violation_id=violation.id,
                alerts_count=len(alerts),
                severity=violation.severity.value
            )
            
        except Exception as e:
            logger.error("Error triggering immediate alert", violation_id=violation.id, error=str(e))
    
    async def _update_monitoring_stats(self, comparisons: List[MSPComparisonResult], violations: List[MSPViolation]):
        """Update monitoring statistics"""
        try:
            total_comparisons = len(comparisons)
            total_violations = len(violations)
            compliance_rate = ((total_comparisons - total_violations) / total_comparisons * 100) if total_comparisons > 0 else 100
            
            # Find most violated commodity
            commodity_violations = {}
            for violation in violations:
                commodity_violations[violation.commodity] = commodity_violations.get(violation.commodity, 0) + 1
            
            most_violated_commodity = max(commodity_violations.keys(), key=commodity_violations.get) if commodity_violations else None
            
            stats = MSPMonitoringStats(
                total_commodities_monitored=len(set(c.commodity for c in comparisons)),
                total_mandis_monitored=len(set(c.mandi_id for c in comparisons)),
                violations_detected_today=total_violations,
                violations_resolved_today=0,  # Would be calculated from database
                average_compliance_rate=compliance_rate,
                most_violated_commodity=most_violated_commodity
            )
            
            # Store stats (implementation would depend on database layer)
            logger.info("Updated monitoring stats", stats=stats.dict())
            
        except Exception as e:
            logger.error("Error updating monitoring stats", error=str(e))
    
    async def get_violations_by_location(self, state: Optional[str] = None, district: Optional[str] = None) -> List[MSPViolation]:
        """Get violations filtered by location"""
        # Implementation would query database
        filtered_violations = []
        for violation in self.violation_cache.values():
            if state and violation.state.lower() != state.lower():
                continue
            if district and violation.district.lower() != district.lower():
                continue
            filtered_violations.append(violation)
        return filtered_violations
    
    async def get_violations_by_commodity(self, commodity: str) -> List[MSPViolation]:
        """Get violations for a specific commodity"""
        return [v for v in self.violation_cache.values() if v.commodity.lower() == commodity.lower()]
    
    async def resolve_violation(self, violation_id: str, resolution_notes: str) -> bool:
        """Mark a violation as resolved"""
        try:
            # Find violation in cache
            for violation in self.violation_cache.values():
                if violation.id == violation_id:
                    violation.is_resolved = True
                    violation.resolution_notes = resolution_notes
                    violation.resolved_at = datetime.utcnow()
                    
                    # Update in database
                    await store_msp_violation(violation)
                    return True
            
            return False
        except Exception as e:
            logger.error("Error resolving violation", violation_id=violation_id, error=str(e))
            return False
    
    async def get_monitoring_stats(self) -> MSPMonitoringStats:
        """Get current monitoring statistics"""
        # This would typically query the database for comprehensive stats
        total_violations = len([v for v in self.violation_cache.values() if not v.is_resolved])
        
        return MSPMonitoringStats(
            total_commodities_monitored=len(self.current_msp_rates),
            total_mandis_monitored=0,  # Would be calculated from database
            violations_detected_today=total_violations,
            violations_resolved_today=0,
            average_compliance_rate=85.0,  # Would be calculated from database
            most_violated_commodity=None
        )