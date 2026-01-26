"""
Anti-Hoarding Detection Service
Main FastAPI application for anomaly detection and market manipulation detection
"""

import asyncio
import structlog
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from models import (
    PriceAnomaly, InventoryAnomaly, StockpilingPattern, MarketManipulationAlert,
    SupplyDemandBalance, AnomalyDetectionConfig, DetectionStatistics,
    AnomalyType, AnomalySeverity, GeoLocation
)
from anomaly_detector import (
    AnomalyDetectionEngine, PriceDataPoint, InventoryDataPoint
)
from supply_demand_analyzer import SupplyDemandAnalyzer
from market_manipulation_detector import MarketManipulationDetector
from regional_supply_chain_analyzer import RegionalSupplyChainAnalyzer
from database import (
    anomaly_db, get_price_data_for_analysis, get_inventory_data_for_analysis,
    store_price_anomaly, store_inventory_anomaly, store_stockpiling_pattern,
    get_recent_anomalies
)

# Configure logging
logger = structlog.get_logger()

# FastAPI app
app = FastAPI(
    title="Anti-Hoarding Detection Service",
    description="Anomaly detection algorithms for identifying market manipulation and hoarding patterns",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global detection engine and analyzers
detection_engine: Optional[AnomalyDetectionEngine] = None
supply_demand_analyzer: Optional[SupplyDemandAnalyzer] = None
manipulation_detector: Optional[MarketManipulationDetector] = None
supply_chain_analyzer: Optional[RegionalSupplyChainAnalyzer] = None
detection_config = AnomalyDetectionConfig()

# Pydantic models for API requests/responses
class AnomalyDetectionRequest(BaseModel):
    commodity: str
    variety: Optional[str] = None
    region: Optional[str] = None
    analysis_period_days: int = 30

class PriceSpikeDetectionRequest(BaseModel):
    commodity: str
    variety: Optional[str] = None
    threshold_percentage: Optional[float] = None
    analysis_period_days: int = 30

class InventoryAnalysisRequest(BaseModel):
    commodity: str
    variety: Optional[str] = None
    region: Optional[str] = None
    analysis_period_days: int = 30

class StockpilingAnalysisRequest(BaseModel):
    commodity: str
    variety: Optional[str] = None
    analysis_period_days: int = 30

class AnomalyStatusUpdate(BaseModel):
    anomaly_id: str
    anomaly_type: str  # "price", "inventory", "stockpiling"
    is_confirmed: bool
    is_resolved: bool = False
    resolution_notes: Optional[str] = None

class DetectionResponse(BaseModel):
    success: bool
    message: str
    total_anomalies: int
    price_anomalies: int
    inventory_anomalies: int
    stockpiling_patterns: int
    analysis_timestamp: datetime

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize the detection engine and analyzers on startup"""
    global detection_engine, supply_demand_analyzer, manipulation_detector, supply_chain_analyzer
    try:
        detection_engine = AnomalyDetectionEngine(detection_config)
        supply_demand_analyzer = SupplyDemandAnalyzer()
        manipulation_detector = MarketManipulationDetector()
        supply_chain_analyzer = RegionalSupplyChainAnalyzer()
        logger.info("Anti-hoarding detection service started successfully")
    except Exception as e:
        logger.error("Failed to start detection service", error=str(e))
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Anti-hoarding detection service shutting down")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "anti-hoarding-detection",
        "timestamp": datetime.utcnow().isoformat(),
        "detection_engine_ready": detection_engine is not None,
        "supply_demand_analyzer_ready": supply_demand_analyzer is not None,
        "manipulation_detector_ready": manipulation_detector is not None,
        "supply_chain_analyzer_ready": supply_chain_analyzer is not None
    }

# Configuration endpoints
@app.get("/config")
async def get_detection_config():
    """Get current detection configuration"""
    return detection_config.dict()

@app.put("/config")
async def update_detection_config(config: AnomalyDetectionConfig):
    """Update detection configuration"""
    global detection_config, detection_engine, supply_demand_analyzer, manipulation_detector, supply_chain_analyzer
    try:
        detection_config = config
        detection_engine = AnomalyDetectionEngine(detection_config)
        supply_demand_analyzer = SupplyDemandAnalyzer()
        manipulation_detector = MarketManipulationDetector()
        supply_chain_analyzer = RegionalSupplyChainAnalyzer()
        logger.info("Detection configuration updated")
        return {"success": True, "message": "Configuration updated successfully"}
    except Exception as e:
        logger.error("Failed to update configuration", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update configuration")

# Main detection endpoints
@app.post("/detect/comprehensive", response_model=DetectionResponse)
async def run_comprehensive_detection(
    request: AnomalyDetectionRequest,
    background_tasks: BackgroundTasks
):
    """
    Run comprehensive anomaly detection analysis
    
    Implements Requirements 7.1, 7.3:
    - Statistical price spike detection (>25% deviation)
    - Inventory level tracking across mandis
    - Stockpiling pattern detection
    """
    if not detection_engine:
        raise HTTPException(status_code=503, detail="Detection engine not initialized")
    
    try:
        # Get data for analysis
        price_data_raw = await get_price_data_for_analysis(
            commodity=request.commodity,
            variety=request.variety,
            region=request.region,
            days_back=request.analysis_period_days
        )
        
        inventory_data_raw = await get_inventory_data_for_analysis(
            commodity=request.commodity,
            variety=request.variety,
            region=request.region,
            days_back=request.analysis_period_days
        )
        
        # Convert to detection data structures
        price_data = [
            PriceDataPoint(
                commodity=p["commodity"],
                variety=p.get("variety"),
                price=p["price"],
                quantity=p["quantity"],
                mandi_id=p["mandi_id"],
                mandi_name=p["mandi_name"],
                location=GeoLocation(
                    latitude=0.0,  # Mock coordinates
                    longitude=0.0,
                    district=p.get("district", ""),
                    state=p.get("state", ""),
                    country="India"
                ),
                timestamp=p["timestamp"],
                confidence=p["confidence"]
            )
            for p in price_data_raw
        ]
        
        inventory_data = [
            InventoryDataPoint(
                commodity=i["commodity"],
                variety=i.get("variety"),
                inventory_level=i["inventory_level"],
                mandi_id=i["mandi_id"],
                mandi_name=i["mandi_name"],
                location=GeoLocation(
                    latitude=0.0,  # Mock coordinates
                    longitude=0.0,
                    district=i.get("district", ""),
                    state=i.get("state", ""),
                    country="India"
                ),
                timestamp=i["timestamp"],
                storage_capacity=i.get("storage_capacity")
            )
            for i in inventory_data_raw
        ]
        
        # Run comprehensive analysis
        results = await detection_engine.run_comprehensive_analysis(
            price_data=price_data,
            inventory_data=inventory_data,
            commodity=request.commodity,
            variety=request.variety,
            region=request.region
        )
        
        # Store results in background
        background_tasks.add_task(store_detection_results, results)
        
        # Count total anomalies
        total_anomalies = (
            len(results["price_anomalies"]) +
            len(results["inventory_anomalies"]) +
            len(results["stockpiling_patterns"])
        )
        
        logger.info(
            "Comprehensive detection completed",
            commodity=request.commodity,
            total_anomalies=total_anomalies
        )
        
        return DetectionResponse(
            success=True,
            message=f"Comprehensive analysis completed for {request.commodity}",
            total_anomalies=total_anomalies,
            price_anomalies=len(results["price_anomalies"]),
            inventory_anomalies=len(results["inventory_anomalies"]),
            stockpiling_patterns=len(results["stockpiling_patterns"]),
            analysis_timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error("Comprehensive detection failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

@app.post("/detect/price-spikes")
async def detect_price_spikes(
    request: PriceSpikeDetectionRequest,
    background_tasks: BackgroundTasks
):
    """
    Detect price spikes using statistical analysis
    
    Implements Requirement 7.1: Identify unusual price spikes that deviate 
    more than 25% from 30-day moving averages
    """
    if not detection_engine:
        raise HTTPException(status_code=503, detail="Detection engine not initialized")
    
    try:
        # Update threshold if provided
        if request.threshold_percentage:
            detection_config.price_spike_threshold_percentage = request.threshold_percentage
        
        # Get price data
        price_data_raw = await get_price_data_for_analysis(
            commodity=request.commodity,
            variety=request.variety,
            days_back=request.analysis_period_days
        )
        
        # Convert to detection data structures
        price_data = [
            PriceDataPoint(
                commodity=p["commodity"],
                variety=p.get("variety"),
                price=p["price"],
                quantity=p["quantity"],
                mandi_id=p["mandi_id"],
                mandi_name=p["mandi_name"],
                location=GeoLocation(
                    latitude=0.0,
                    longitude=0.0,
                    district=p.get("district", ""),
                    state=p.get("state", ""),
                    country="India"
                ),
                timestamp=p["timestamp"],
                confidence=p["confidence"]
            )
            for p in price_data_raw
        ]
        
        # Run price spike detection
        price_anomalies = await detection_engine.price_spike_detector.detect_price_spikes(
            price_data=price_data,
            commodity=request.commodity,
            variety=request.variety
        )
        
        # Store results in background
        for anomaly in price_anomalies:
            background_tasks.add_task(store_price_anomaly, anomaly)
        
        return {
            "success": True,
            "message": f"Price spike detection completed for {request.commodity}",
            "anomalies_detected": len(price_anomalies),
            "anomalies": [anomaly.dict() for anomaly in price_anomalies],
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Price spike detection failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Price spike detection failed: {str(e)}")

@app.post("/detect/inventory-anomalies")
async def detect_inventory_anomalies(
    request: InventoryAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Detect inventory level anomalies across mandis
    
    Implements Requirement 7.3: Implement inventory level tracking across mandis
    """
    if not detection_engine:
        raise HTTPException(status_code=503, detail="Detection engine not initialized")
    
    try:
        # Get inventory data
        inventory_data_raw = await get_inventory_data_for_analysis(
            commodity=request.commodity,
            variety=request.variety,
            region=request.region,
            days_back=request.analysis_period_days
        )
        
        # Convert to detection data structures
        inventory_data = [
            InventoryDataPoint(
                commodity=i["commodity"],
                variety=i.get("variety"),
                inventory_level=i["inventory_level"],
                mandi_id=i["mandi_id"],
                mandi_name=i["mandi_name"],
                location=GeoLocation(
                    latitude=0.0,
                    longitude=0.0,
                    district=i.get("district", ""),
                    state=i.get("state", ""),
                    country="India"
                ),
                timestamp=i["timestamp"],
                storage_capacity=i.get("storage_capacity")
            )
            for i in inventory_data_raw
        ]
        
        # Run inventory anomaly detection
        inventory_anomalies = await detection_engine.inventory_tracker.detect_inventory_anomalies(
            inventory_data=inventory_data,
            commodity=request.commodity,
            variety=request.variety,
            region=request.region
        )
        
        # Store results in background
        for anomaly in inventory_anomalies:
            background_tasks.add_task(store_inventory_anomaly, anomaly)
        
        return {
            "success": True,
            "message": f"Inventory anomaly detection completed for {request.commodity}",
            "anomalies_detected": len(inventory_anomalies),
            "anomalies": [anomaly.dict() for anomaly in inventory_anomalies],
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Inventory anomaly detection failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Inventory anomaly detection failed: {str(e)}")

@app.post("/detect/stockpiling-patterns")
async def detect_stockpiling_patterns(
    request: StockpilingAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Detect stockpiling patterns across regions
    
    Implements Requirement 7.3: Create stockpiling pattern detection
    """
    if not detection_engine:
        raise HTTPException(status_code=503, detail="Detection engine not initialized")
    
    try:
        # Get both price and inventory data for pattern analysis
        price_data_raw = await get_price_data_for_analysis(
            commodity=request.commodity,
            variety=request.variety,
            days_back=request.analysis_period_days
        )
        
        inventory_data_raw = await get_inventory_data_for_analysis(
            commodity=request.commodity,
            variety=request.variety,
            days_back=request.analysis_period_days
        )
        
        # Convert to detection data structures
        price_data = [
            PriceDataPoint(
                commodity=p["commodity"],
                variety=p.get("variety"),
                price=p["price"],
                quantity=p["quantity"],
                mandi_id=p["mandi_id"],
                mandi_name=p["mandi_name"],
                location=GeoLocation(
                    latitude=0.0,
                    longitude=0.0,
                    district=p.get("district", ""),
                    state=p.get("state", ""),
                    country="India"
                ),
                timestamp=p["timestamp"],
                confidence=p["confidence"]
            )
            for p in price_data_raw
        ]
        
        inventory_data = [
            InventoryDataPoint(
                commodity=i["commodity"],
                variety=i.get("variety"),
                inventory_level=i["inventory_level"],
                mandi_id=i["mandi_id"],
                mandi_name=i["mandi_name"],
                location=GeoLocation(
                    latitude=0.0,
                    longitude=0.0,
                    district=i.get("district", ""),
                    state=i.get("state", ""),
                    country="India"
                ),
                timestamp=i["timestamp"],
                storage_capacity=i.get("storage_capacity")
            )
            for i in inventory_data_raw
        ]
        
        # Run stockpiling pattern detection
        stockpiling_patterns = await detection_engine.stockpiling_detector.detect_stockpiling_patterns(
            inventory_data=inventory_data,
            price_data=price_data,
            commodity=request.commodity,
            variety=request.variety
        )
        
        # Store results in background
        for pattern in stockpiling_patterns:
            background_tasks.add_task(store_stockpiling_pattern, pattern)
        
        return {
            "success": True,
            "message": f"Stockpiling pattern detection completed for {request.commodity}",
            "patterns_detected": len(stockpiling_patterns),
            "patterns": [pattern.dict() for pattern in stockpiling_patterns],
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Stockpiling pattern detection failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Stockpiling pattern detection failed: {str(e)}")

# Query endpoints
@app.get("/anomalies/price")
async def get_price_anomalies(
    commodity: Optional[str] = Query(None),
    severity: Optional[AnomalySeverity] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get price anomalies with optional filters"""
    try:
        anomalies = await anomaly_db.get_price_anomalies(
            commodity=commodity,
            severity=severity,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return {
            "success": True,
            "count": len(anomalies),
            "anomalies": [anomaly.dict() for anomaly in anomalies]
        }
        
    except Exception as e:
        logger.error("Failed to retrieve price anomalies", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve price anomalies")

@app.get("/anomalies/inventory")
async def get_inventory_anomalies(
    commodity: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    anomaly_type: Optional[AnomalyType] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get inventory anomalies with optional filters"""
    try:
        anomalies = await anomaly_db.get_inventory_anomalies(
            commodity=commodity,
            region=region,
            anomaly_type=anomaly_type,
            limit=limit
        )
        
        return {
            "success": True,
            "count": len(anomalies),
            "anomalies": [anomaly.dict() for anomaly in anomalies]
        }
        
    except Exception as e:
        logger.error("Failed to retrieve inventory anomalies", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve inventory anomalies")

@app.get("/patterns/stockpiling")
async def get_stockpiling_patterns(
    commodity: Optional[str] = Query(None),
    pattern_type: Optional[str] = Query(None),
    severity: Optional[AnomalySeverity] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get stockpiling patterns with optional filters"""
    try:
        patterns = await anomaly_db.get_stockpiling_patterns(
            commodity=commodity,
            pattern_type=pattern_type,
            severity=severity,
            limit=limit
        )
        
        return {
            "success": True,
            "count": len(patterns),
            "patterns": [pattern.dict() for pattern in patterns]
        }
        
    except Exception as e:
        logger.error("Failed to retrieve stockpiling patterns", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve stockpiling patterns")

@app.get("/anomalies/recent")
async def get_recent_anomalies_endpoint(
    commodity: Optional[str] = Query(None),
    hours_back: int = Query(24, le=168)  # Max 1 week
):
    """Get recent anomalies across all types"""
    try:
        anomalies = await get_recent_anomalies(
            commodity=commodity,
            hours_back=hours_back
        )
        
        total_count = (
            len(anomalies["price_anomalies"]) +
            len(anomalies["inventory_anomalies"]) +
            len(anomalies["stockpiling_patterns"])
        )
        
        return {
            "success": True,
            "total_count": total_count,
            "price_anomalies_count": len(anomalies["price_anomalies"]),
            "inventory_anomalies_count": len(anomalies["inventory_anomalies"]),
            "stockpiling_patterns_count": len(anomalies["stockpiling_patterns"]),
            "anomalies": anomalies
        }
        
    except Exception as e:
        logger.error("Failed to retrieve recent anomalies", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve recent anomalies")

# Supply-Demand Analysis Endpoints
@app.post("/analyze/supply-demand-balance")
async def analyze_supply_demand_balance(
    commodity: str = Query(...),
    variety: Optional[str] = Query(None),
    region: str = Query(...),
    analysis_period_days: int = Query(30, le=90)
):
    """
    Calculate supply-demand balance for a commodity in a region
    
    Implements Requirement 7.5: THE System SHALL provide supply-demand balance indicators 
    for each commodity across different regions
    """
    if not supply_demand_analyzer:
        raise HTTPException(status_code=503, detail="Supply-demand analyzer not initialized")
    
    try:
        # Get data for analysis
        price_data_raw = await get_price_data_for_analysis(
            commodity=commodity,
            variety=variety,
            region=region,
            days_back=analysis_period_days
        )
        
        inventory_data_raw = await get_inventory_data_for_analysis(
            commodity=commodity,
            variety=variety,
            region=region,
            days_back=analysis_period_days
        )
        
        # Calculate supply-demand balance
        balance = await supply_demand_analyzer.calculate_supply_demand_balance(
            commodity=commodity,
            variety=variety,
            region=region,
            price_data=price_data_raw,
            inventory_data=inventory_data_raw
        )
        
        # Store the balance in database
        await anomaly_db.store_supply_demand_balance(balance)
        
        return {
            "success": True,
            "message": f"Supply-demand balance calculated for {commodity} in {region}",
            "balance": balance.dict(),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Supply-demand balance analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/analyze/market-manipulation")
async def analyze_market_manipulation(
    commodity: str = Query(...),
    variety: Optional[str] = Query(None),
    region: str = Query(...),
    analysis_period_days: int = Query(30, le=90)
):
    """
    Detect market manipulation patterns
    
    Implements Requirement 7.2: WHEN supply chain manipulation is detected, 
    THE System SHALL alert farmers about artificial scarcity and suggest alternative markets
    """
    if not manipulation_detector or not supply_demand_analyzer:
        raise HTTPException(status_code=503, detail="Market manipulation detector not initialized")
    
    try:
        # Get recent anomalies
        price_anomalies = await anomaly_db.get_price_anomalies(
            commodity=commodity,
            start_date=datetime.utcnow() - timedelta(days=analysis_period_days),
            limit=100
        )
        
        inventory_anomalies = await anomaly_db.get_inventory_anomalies(
            commodity=commodity,
            limit=100
        )
        
        stockpiling_patterns = await anomaly_db.get_stockpiling_patterns(
            commodity=commodity,
            limit=100
        )
        
        # Get current supply-demand balance
        price_data_raw = await get_price_data_for_analysis(
            commodity=commodity,
            variety=variety,
            region=region,
            days_back=analysis_period_days
        )
        
        inventory_data_raw = await get_inventory_data_for_analysis(
            commodity=commodity,
            variety=variety,
            region=region,
            days_back=analysis_period_days
        )
        
        supply_demand_balance = await supply_demand_analyzer.calculate_supply_demand_balance(
            commodity=commodity,
            variety=variety,
            region=region,
            price_data=price_data_raw,
            inventory_data=inventory_data_raw
        )
        
        # Detect market manipulation
        manipulation_alerts = await manipulation_detector.detect_market_manipulation(
            commodity=commodity,
            variety=variety,
            region=region,
            price_anomalies=price_anomalies,
            inventory_anomalies=inventory_anomalies,
            stockpiling_patterns=stockpiling_patterns,
            supply_demand_balance=supply_demand_balance
        )
        
        # Store alerts in database
        for alert in manipulation_alerts:
            await anomaly_db.store_manipulation_alert(alert)
        
        return {
            "success": True,
            "message": f"Market manipulation analysis completed for {commodity} in {region}",
            "alerts_generated": len(manipulation_alerts),
            "alerts": [alert.dict() for alert in manipulation_alerts],
            "supply_demand_balance": supply_demand_balance.dict(),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Market manipulation analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/analyze/regional-supply-chain")
async def analyze_regional_supply_chain(
    commodity: str = Query(...),
    variety: Optional[str] = Query(None),
    regions: List[str] = Query(...),
    analysis_period_days: int = Query(30, le=90)
):
    """
    Analyze regional supply chain patterns and efficiency
    
    Implements regional supply chain analysis component of task 10.3
    """
    if not supply_chain_analyzer:
        raise HTTPException(status_code=503, detail="Supply chain analyzer not initialized")
    
    try:
        # Get data for analysis across all regions
        all_price_data = []
        all_inventory_data = []
        
        for region in regions:
            price_data = await get_price_data_for_analysis(
                commodity=commodity,
                variety=variety,
                region=region,
                days_back=analysis_period_days
            )
            all_price_data.extend(price_data)
            
            inventory_data = await get_inventory_data_for_analysis(
                commodity=commodity,
                variety=variety,
                region=region,
                days_back=analysis_period_days
            )
            all_inventory_data.extend(inventory_data)
        
        # Analyze regional supply chains
        supply_chains = await supply_chain_analyzer.analyze_regional_supply_chain(
            commodity=commodity,
            variety=variety,
            regions=regions,
            price_data=all_price_data,
            inventory_data=all_inventory_data
        )
        
        return {
            "success": True,
            "message": f"Regional supply chain analysis completed for {commodity}",
            "regions_analyzed": len(supply_chains),
            "supply_chains": [
                {
                    "region": sc.region,
                    "commodity": sc.commodity,
                    "variety": sc.variety,
                    "supply_sources": sc.supply_sources,
                    "demand_destinations": sc.demand_destinations,
                    "transportation_costs": sc.transportation_costs,
                    "bottlenecks": sc.bottlenecks,
                    "efficiency_score": sc.efficiency_score,
                    "vulnerability_factors": sc.vulnerability_factors
                }
                for sc in supply_chains
            ],
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Regional supply chain analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# Query endpoints for supply-demand data
@app.get("/supply-demand-balances")
async def get_supply_demand_balances(
    commodity: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    balance_status: Optional[str] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get supply-demand balances with optional filters"""
    try:
        balances = await anomaly_db.get_supply_demand_balances(
            commodity=commodity,
            region=region,
            balance_status=balance_status,
            limit=limit
        )
        
        return {
            "success": True,
            "count": len(balances),
            "balances": [balance.dict() for balance in balances]
        }
        
    except Exception as e:
        logger.error("Failed to retrieve supply-demand balances", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve supply-demand balances")

@app.get("/manipulation-alerts")
async def get_manipulation_alerts(
    commodity: Optional[str] = Query(None),
    severity: Optional[AnomalySeverity] = Query(None),
    is_sent: Optional[bool] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get market manipulation alerts with optional filters"""
    try:
        alerts = await anomaly_db.get_manipulation_alerts(
            commodity=commodity,
            severity=severity,
            is_sent=is_sent,
            limit=limit
        )
        
        return {
            "success": True,
            "count": len(alerts),
            "alerts": [alert.dict() for alert in alerts]
        }
        
    except Exception as e:
        logger.error("Failed to retrieve manipulation alerts", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve manipulation alerts")

# Management endpoints
@app.put("/anomalies/status")
async def update_anomaly_status(request: AnomalyStatusUpdate):
    """Update anomaly confirmation and resolution status"""
    try:
        success = await anomaly_db.update_anomaly_status(
            anomaly_id=request.anomaly_id,
            anomaly_type=request.anomaly_type,
            is_confirmed=request.is_confirmed,
            is_resolved=request.is_resolved,
            resolution_notes=request.resolution_notes
        )
        
        if success:
            return {"success": True, "message": "Anomaly status updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Anomaly not found")
            
    except Exception as e:
        logger.error("Failed to update anomaly status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update anomaly status")

@app.get("/statistics")
async def get_detection_statistics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get detection statistics for a time period"""
    try:
        stats = await anomaly_db.get_detection_statistics(
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "success": True,
            "statistics": stats.dict()
        }
        
    except Exception as e:
        logger.error("Failed to retrieve detection statistics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

# Background task functions
async def store_detection_results(results: Dict[str, List]):
    """Store detection results in database"""
    try:
        # Store price anomalies
        for anomaly in results["price_anomalies"]:
            await store_price_anomaly(anomaly)
        
        # Store inventory anomalies
        for anomaly in results["inventory_anomalies"]:
            await store_inventory_anomaly(anomaly)
        
        # Store stockpiling patterns
        for pattern in results["stockpiling_patterns"]:
            await store_stockpiling_pattern(pattern)
        
        logger.info("Detection results stored successfully")
        
    except Exception as e:
        logger.error("Failed to store detection results", error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)