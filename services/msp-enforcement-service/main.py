"""
MANDI EAR™ MSP Enforcement Service
Continuous MSP monitoring, violation detection, and alternative suggestions
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from contextlib import asynccontextmanager
import structlog
from typing import List, Optional
from datetime import datetime, date, timedelta

from models import (
    MSPRate, MSPViolation, MSPAlert, ProcurementCenter, 
    AlternativeSuggestion, MSPComparisonResult, MSPMonitoringStats,
    MSPComplianceReport, ViolationType, AlertSeverity
)
from database import init_db, close_db, store_compliance_report, get_compliance_reports, get_compliance_report_by_id
from msp_monitor import MSPMonitoringEngine, MonitoringConfig
from government_data_integration import GovernmentDataIntegrator
from alert_system import MSPAlertSystem
from compliance_reporting import ComplianceReportGenerator, ReportConfig, ReportType, ReportFormat

logger = structlog.get_logger()

# Global service instances
monitoring_engine: Optional[MSPMonitoringEngine] = None
data_integrator: Optional[GovernmentDataIntegrator] = None
alert_system: Optional[MSPAlertSystem] = None
compliance_reporter: Optional[ComplianceReportGenerator] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global monitoring_engine, data_integrator, alert_system, compliance_reporter
    
    # Startup
    logger.info("Starting MSP Enforcement Service")
    await init_db()
    
    # Initialize components
    monitoring_engine = MSPMonitoringEngine()
    await monitoring_engine.initialize()
    
    data_integrator = GovernmentDataIntegrator()
    await data_integrator.initialize()
    
    alert_system = MSPAlertSystem()
    await alert_system.initialize()
    
    compliance_reporter = ComplianceReportGenerator()
    
    # Start background tasks
    await monitoring_engine.start_monitoring()
    await data_integrator.start_sync_tasks()
    
    logger.info("MSP Enforcement Service started successfully")
    yield
    
    # Shutdown
    logger.info("Shutting down MSP Enforcement Service")
    if monitoring_engine:
        await monitoring_engine.shutdown()
    if data_integrator:
        await data_integrator.shutdown()
    if alert_system:
        await alert_system.shutdown()
    await close_db()

app = FastAPI(
    title="MANDI EAR™ MSP Enforcement Service",
    description="Continuous MSP monitoring, violation detection, and farmer protection",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {
        "service": "MSP Enforcement Service",
        "version": "1.0.0",
        "status": "operational",
        "features": [
            "Continuous MSP monitoring",
            "Government data integration",
            "Violation detection and alerts",
            "Alternative market suggestions",
            "Compliance reporting"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "components": {
            "monitoring_engine": monitoring_engine is not None and monitoring_engine.is_running,
            "data_integrator": data_integrator is not None and data_integrator.is_running,
            "alert_system": alert_system is not None and alert_system.is_running,
            "compliance_reporter": compliance_reporter is not None
        }
    }
    return status

# MSP Monitoring Endpoints
@app.get("/monitoring/stats")
async def get_monitoring_stats() -> MSPMonitoringStats:
    """Get current monitoring statistics"""
    if not monitoring_engine:
        raise HTTPException(status_code=503, detail="Monitoring engine not available")
    
    try:
        stats = await monitoring_engine.get_monitoring_stats()
        return stats
    except Exception as e:
        logger.error("Failed to get monitoring stats", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/monitoring/start")
async def start_monitoring():
    """Start MSP monitoring"""
    if not monitoring_engine:
        raise HTTPException(status_code=503, detail="Monitoring engine not available")
    
    try:
        await monitoring_engine.start_monitoring()
        return {"message": "MSP monitoring started"}
    except Exception as e:
        logger.error("Failed to start monitoring", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/monitoring/stop")
async def stop_monitoring():
    """Stop MSP monitoring"""
    if not monitoring_engine:
        raise HTTPException(status_code=503, detail="Monitoring engine not available")
    
    try:
        await monitoring_engine.stop_monitoring()
        return {"message": "MSP monitoring stopped"}
    except Exception as e:
        logger.error("Failed to stop monitoring", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/monitoring/trigger")
async def trigger_monitoring_cycle(background_tasks: BackgroundTasks):
    """Manually trigger a monitoring cycle"""
    if not monitoring_engine:
        raise HTTPException(status_code=503, detail="Monitoring engine not available")
    
    background_tasks.add_task(monitoring_engine._run_monitoring_cycle)
    return {"message": "Monitoring cycle triggered"}

# MSP Rates Endpoints
@app.get("/msp-rates")
async def get_msp_rates(
    commodity: Optional[str] = None,
    season: Optional[str] = None,
    active_only: bool = True
) -> List[MSPRate]:
    """Get MSP rates with optional filters"""
    try:
        from database import get_active_msp_rates
        rates = await get_active_msp_rates()
        
        # Apply filters
        if commodity:
            rates = [r for r in rates if r.commodity.lower() == commodity.lower()]
        if season:
            rates = [r for r in rates if r.season.value.lower() == season.lower()]
        
        return rates
    except Exception as e:
        logger.error("Failed to get MSP rates", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/msp-rates")
async def add_msp_rate(msp_rate: MSPRate):
    """Add or update MSP rate"""
    try:
        from database import store_msp_rate
        success = await store_msp_rate(msp_rate)
        if success:
            return {"message": "MSP rate stored successfully", "id": msp_rate.id}
        else:
            raise HTTPException(status_code=500, detail="Failed to store MSP rate")
    except Exception as e:
        logger.error("Failed to add MSP rate", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# Violations Endpoints
@app.get("/violations")
async def get_violations(
    state: Optional[str] = None,
    district: Optional[str] = None,
    commodity: Optional[str] = None,
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    limit: int = Query(100, le=1000)
) -> List[MSPViolation]:
    """Get MSP violations with filters"""
    if not monitoring_engine:
        raise HTTPException(status_code=503, detail="Monitoring engine not available")
    
    try:
        violations = []
        
        if state or district:
            violations = await monitoring_engine.get_violations_by_location(state, district)
        elif commodity:
            violations = await monitoring_engine.get_violations_by_commodity(commodity)
        else:
            # Get all violations from cache
            violations = list(monitoring_engine.violation_cache.values())
        
        # Apply additional filters
        if severity:
            violations = [v for v in violations if v.severity.value.lower() == severity.lower()]
        if resolved is not None:
            violations = [v for v in violations if v.is_resolved == resolved]
        
        # Sort by detection time (newest first) and limit
        violations.sort(key=lambda x: x.detected_at, reverse=True)
        return violations[:limit]
        
    except Exception as e:
        logger.error("Failed to get violations", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/violations/{violation_id}/resolve")
async def resolve_violation(violation_id: str, resolution_notes: str):
    """Mark a violation as resolved"""
    if not monitoring_engine:
        raise HTTPException(status_code=503, detail="Monitoring engine not available")
    
    try:
        success = await monitoring_engine.resolve_violation(violation_id, resolution_notes)
        if success:
            return {"message": "Violation resolved successfully"}
        else:
            raise HTTPException(status_code=404, detail="Violation not found")
    except Exception as e:
        logger.error("Failed to resolve violation", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# Alerts Endpoints
@app.get("/alerts")
async def get_alerts(
    farmer_id: Optional[str] = None,
    unread_only: bool = False,
    severity: Optional[str] = None,
    limit: int = Query(50, le=200)
) -> List[MSPAlert]:
    """Get MSP alerts"""
    if not alert_system:
        raise HTTPException(status_code=503, detail="Alert system not available")
    
    try:
        if farmer_id:
            alerts = await alert_system.get_alerts_for_farmer(farmer_id, unread_only)
        else:
            # Return empty list for now - would need database query for all alerts
            alerts = []
        
        # Apply severity filter
        if severity:
            alerts = [a for a in alerts if a.severity.value.lower() == severity.lower()]
        
        return alerts[:limit]
    except Exception as e:
        logger.error("Failed to get alerts", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: str, farmer_id: str):
    """Mark an alert as read"""
    if not alert_system:
        raise HTTPException(status_code=503, detail="Alert system not available")
    
    try:
        success = await alert_system.mark_alert_read(alert_id, farmer_id)
        if success:
            return {"message": "Alert marked as read"}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
    except Exception as e:
        logger.error("Failed to mark alert as read", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, farmer_id: str):
    """Acknowledge an alert"""
    if not alert_system:
        raise HTTPException(status_code=503, detail="Alert system not available")
    
    try:
        success = await alert_system.acknowledge_alert(alert_id, farmer_id)
        if success:
            return {"message": "Alert acknowledged"}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
    except Exception as e:
        logger.error("Failed to acknowledge alert", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# Procurement Centers Endpoints
@app.get("/procurement-centers")
async def get_procurement_centers(
    state: Optional[str] = None,
    commodity: Optional[str] = None,
    operational_only: bool = True
) -> List[ProcurementCenter]:
    """Get government procurement centers"""
    try:
        from database import get_procurement_centers
        centers = await get_procurement_centers(state, commodity, operational_only)
        return centers
    except Exception as e:
        logger.error("Failed to get procurement centers", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/procurement-centers")
async def add_procurement_center(center: ProcurementCenter):
    """Add or update procurement center"""
    try:
        from database import store_procurement_center
        success = await store_procurement_center(center)
        if success:
            return {"message": "Procurement center stored successfully", "id": center.id}
        else:
            raise HTTPException(status_code=500, detail="Failed to store procurement center")
    except Exception as e:
        logger.error("Failed to add procurement center", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# Alternative Suggestions Endpoints
@app.get("/alternatives/{commodity}")
async def get_alternatives(
    commodity: str,
    state: str,
    district: str,
    max_distance: float = Query(200, le=1000),
    min_benefit: float = Query(0, ge=0)
) -> List[AlternativeSuggestion]:
    """Get alternative market suggestions for a commodity"""
    try:
        # This would typically query stored suggestions
        # For now, return empty list
        return []
    except Exception as e:
        logger.error("Failed to get alternatives", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# Government Data Integration Endpoints
@app.post("/government-data/sync")
async def sync_government_data(background_tasks: BackgroundTasks):
    """Manually trigger government data sync"""
    if not data_integrator:
        raise HTTPException(status_code=503, detail="Data integrator not available")
    
    background_tasks.add_task(data_integrator.manual_sync_all)
    return {"message": "Government data sync triggered"}

@app.post("/government-data/sync-procurement-centers")
async def sync_procurement_centers(background_tasks: BackgroundTasks):
    """Sync government procurement centers"""
    if not data_integrator:
        raise HTTPException(status_code=503, detail="Data integrator not available")
    
    background_tasks.add_task(data_integrator.sync_procurement_centers)
    return {"message": "Procurement centers sync triggered"}

# Price Comparison Endpoints
@app.post("/compare")
async def compare_with_msp(
    commodity: str,
    market_price: float,
    mandi_id: str,
    state: str,
    district: str
) -> MSPComparisonResult:
    """Compare a market price with MSP"""
    if not monitoring_engine:
        raise HTTPException(status_code=503, detail="Monitoring engine not available")
    
    try:
        # Create mock price data for comparison
        price_data = {
            "commodity": commodity,
            "price": market_price,
            "mandi_id": mandi_id,
            "mandi_name": f"Mandi {mandi_id}",
            "district": district,
            "state": state,
            "confidence": 0.9
        }
        
        comparison = await monitoring_engine._compare_price_with_msp(price_data)
        if comparison:
            return comparison
        else:
            raise HTTPException(status_code=404, detail="No MSP rate found for commodity")
    except Exception as e:
        logger.error("Failed to compare with MSP", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# Reporting Endpoints
@app.get("/reports/compliance")
async def get_compliance_report(
    start_date: date,
    end_date: date,
    region: str = "national",
    commodity: Optional[str] = None
) -> MSPComplianceReport:
    """Generate MSP compliance report"""
    if not compliance_reporter:
        raise HTTPException(status_code=503, detail="Compliance reporter not available")
    
    try:
        # Generate comprehensive compliance report
        report = await compliance_reporter.generate_compliance_report(
            start_date=start_date,
            end_date=end_date,
            region=region,
            commodity=commodity,
            config=ReportConfig(
                report_type=ReportType.CUSTOM,
                format=ReportFormat.JSON,
                include_evidence=True,
                include_recommendations=True,
                include_farmer_impact=True,
                include_market_analysis=True
            )
        )
        
        return report
    except Exception as e:
        logger.error("Failed to generate compliance report", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/reports/compliance/generate")
async def generate_compliance_report(
    background_tasks: BackgroundTasks,
    start_date: date,
    end_date: date,
    region: str = "national",
    commodity: Optional[str] = None,
    report_type: str = "custom",
    auto_submit: bool = False,
    notification_emails: List[str] = []
):
    """Generate compliance report in background"""
    if not compliance_reporter:
        raise HTTPException(status_code=503, detail="Compliance reporter not available")
    
    try:
        config = ReportConfig(
            report_type=ReportType(report_type),
            format=ReportFormat.JSON,
            include_evidence=True,
            include_recommendations=True,
            include_farmer_impact=True,
            include_market_analysis=True,
            auto_submit=auto_submit,
            notification_emails=notification_emails
        )
        
        # Generate report in background
        background_tasks.add_task(
            compliance_reporter.generate_compliance_report,
            start_date, end_date, region, commodity, config
        )
        
        return {
            "message": "Compliance report generation started",
            "parameters": {
                "start_date": start_date,
                "end_date": end_date,
                "region": region,
                "commodity": commodity,
                "auto_submit": auto_submit
            }
        }
    except Exception as e:
        logger.error("Failed to start compliance report generation", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/reports/compliance/list")
async def list_compliance_reports(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    region: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=200)
) -> List[MSPComplianceReport]:
    """List compliance reports with filters"""
    try:
        reports = await get_compliance_reports(
            start_date=start_date,
            end_date=end_date,
            region=region,
            status=status,
            limit=limit
        )
        return reports
    except Exception as e:
        logger.error("Failed to list compliance reports", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/reports/compliance/{report_id}")
async def get_compliance_report_by_id(report_id: str) -> MSPComplianceReport:
    """Get compliance report by ID"""
    try:
        report = await get_compliance_report_by_id(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Compliance report not found")
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get compliance report", report_id=report_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/reports/compliance/{report_id}/submit")
async def submit_compliance_report(
    report_id: str,
    notification_emails: List[str] = []
):
    """Submit compliance report to regulatory authorities"""
    if not compliance_reporter:
        raise HTTPException(status_code=503, detail="Compliance reporter not available")
    
    try:
        # Get the report
        report = await get_compliance_report_by_id(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Compliance report not found")
        
        # Submit to authorities
        success = await compliance_reporter.regulatory_notifier.submit_report_to_authorities(
            report, notification_emails
        )
        
        if success:
            return {"message": "Compliance report submitted successfully", "report_id": report_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to submit compliance report")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to submit compliance report", report_id=report_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/reports/compliance/notify-critical")
async def notify_critical_violations(background_tasks: BackgroundTasks):
    """Send immediate notifications for critical violations"""
    if not compliance_reporter:
        raise HTTPException(status_code=503, detail="Compliance reporter not available")
    
    try:
        # Get recent critical violations
        from datetime import datetime, timedelta
        recent_violations = []
        
        if monitoring_engine:
            # Get violations from the last 24 hours
            for violation in monitoring_engine.violation_cache.values():
                if (violation.severity == AlertSeverity.CRITICAL and 
                    violation.detected_at > datetime.utcnow() - timedelta(hours=24)):
                    recent_violations.append(violation)
        
        if recent_violations:
            # Send notifications in background
            background_tasks.add_task(
                compliance_reporter.regulatory_notifier.notify_critical_violations,
                recent_violations
            )
            
            return {
                "message": "Critical violation notifications sent",
                "critical_violations": len(recent_violations)
            }
        else:
            return {
                "message": "No critical violations found in the last 24 hours",
                "critical_violations": 0
            }
    except Exception as e:
        logger.error("Failed to notify critical violations", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# Configuration Endpoints
@app.get("/config/monitoring")
async def get_monitoring_config():
    """Get current monitoring configuration"""
    if not monitoring_engine:
        raise HTTPException(status_code=503, detail="Monitoring engine not available")
    
    return {
        "check_interval_minutes": monitoring_engine.config.check_interval_minutes,
        "violation_threshold_percentage": monitoring_engine.config.violation_threshold_percentage,
        "critical_threshold_percentage": monitoring_engine.config.critical_threshold_percentage,
        "min_confidence_score": monitoring_engine.config.min_confidence_score,
        "max_price_age_hours": monitoring_engine.config.max_price_age_hours
    }

@app.post("/config/monitoring")
async def update_monitoring_config(config: dict):
    """Update monitoring configuration"""
    if not monitoring_engine:
        raise HTTPException(status_code=503, detail="Monitoring engine not available")
    
    try:
        # Update configuration
        if "check_interval_minutes" in config:
            monitoring_engine.config.check_interval_minutes = config["check_interval_minutes"]
        if "violation_threshold_percentage" in config:
            monitoring_engine.config.violation_threshold_percentage = config["violation_threshold_percentage"]
        if "critical_threshold_percentage" in config:
            monitoring_engine.config.critical_threshold_percentage = config["critical_threshold_percentage"]
        if "min_confidence_score" in config:
            monitoring_engine.config.min_confidence_score = config["min_confidence_score"]
        if "max_price_age_hours" in config:
            monitoring_engine.config.max_price_age_hours = config["max_price_age_hours"]
        
        return {"message": "Monitoring configuration updated"}
    except Exception as e:
        logger.error("Failed to update monitoring config", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")