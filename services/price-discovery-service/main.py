"""
MANDI EAR™ Price Discovery Service
Market data aggregation and real-time price intelligence
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
import structlog
from typing import List, Optional
from datetime import datetime

from data_ingestion import DataIngestionPipeline
from models import PriceData, MandiInfo, DataSource, GeoLocation
from database import init_db, close_db
from price_comparison import PriceComparisonEngine
from trend_analysis import PriceTrendAnalyzer

logger = structlog.get_logger()

# Global pipeline instance
pipeline: Optional[DataIngestionPipeline] = None
comparison_engine: Optional[PriceComparisonEngine] = None
trend_analyzer: Optional[PriceTrendAnalyzer] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global pipeline, comparison_engine, trend_analyzer
    
    # Startup
    logger.info("Starting Price Discovery Service")
    await init_db()
    pipeline = DataIngestionPipeline()
    await pipeline.initialize()
    comparison_engine = PriceComparisonEngine()
    trend_analyzer = PriceTrendAnalyzer()
    yield
    
    # Shutdown
    logger.info("Shutting down Price Discovery Service")
    if pipeline:
        await pipeline.shutdown()
    await close_db()

app = FastAPI(
    title="MANDI EAR™ Price Discovery Service",
    description="Real-time market data and price intelligence",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {
        "service": "Price Discovery Service",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/prices/{commodity}")
async def get_commodity_prices(
    commodity: str,
    state: Optional[str] = None,
    limit: int = 100
) -> List[PriceData]:
    """Get current prices for a commodity"""
    if not pipeline:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        prices = await pipeline.get_commodity_prices(commodity, state, limit)
        return prices
    except Exception as e:
        logger.error("Failed to get commodity prices", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/mandis")
async def get_mandis(state: Optional[str] = None) -> List[MandiInfo]:
    """Get list of mandis"""
    if not pipeline:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        mandis = await pipeline.get_mandis(state)
        return mandis
    except Exception as e:
        logger.error("Failed to get mandis", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/ingest")
async def trigger_data_ingestion(background_tasks: BackgroundTasks):
    """Manually trigger data ingestion"""
    if not pipeline:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    background_tasks.add_task(pipeline.run_ingestion_cycle)
    return {"message": "Data ingestion triggered"}

@app.get("/sources")
async def get_data_sources() -> List[DataSource]:
    """Get list of configured data sources"""
    if not pipeline:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return await pipeline.get_data_sources()

@app.post("/compare")
async def compare_prices(
    commodity: str,
    latitude: float,
    longitude: float,
    district: str,
    state: str,
    radius_km: float = 500,
    max_results: int = 20
):
    """Compare prices across mandis"""
    if not comparison_engine:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        base_location = GeoLocation(
            latitude=latitude,
            longitude=longitude,
            district=district,
            state=state
        )
        
        comparison = await comparison_engine.compare_prices(
            commodity=commodity,
            base_location=base_location,
            radius_km=radius_km,
            max_results=max_results
        )
        
        return comparison
    except Exception as e:
        logger.error("Failed to compare prices", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/trends/{commodity}")
async def get_price_trends(
    commodity: str,
    region: Optional[str] = None,
    days_back: int = 30
):
    """Get price trend analysis for a commodity"""
    if not comparison_engine:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        trends = await comparison_engine.analyze_price_trends(
            commodity=commodity,
            region=region,
            days_back=days_back
        )
        return trends
    except Exception as e:
        logger.error("Failed to analyze trends", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/arbitrage")
async def find_arbitrage_opportunities(
    commodity: str,
    latitude: float,
    longitude: float,
    district: str,
    state: str,
    max_distance_km: float = 1000,
    min_profit_margin: float = 10.0
):
    """Find arbitrage opportunities"""
    if not comparison_engine:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        base_location = GeoLocation(
            latitude=latitude,
            longitude=longitude,
            district=district,
            state=state
        )
        
        opportunities = await comparison_engine.find_arbitrage_opportunities(
            commodity=commodity,
            base_location=base_location,
            max_distance_km=max_distance_km,
            min_profit_margin=min_profit_margin
        )
        
        return {"opportunities": opportunities}
    except Exception as e:
        logger.error("Failed to find arbitrage opportunities", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/analysis/{commodity}")
async def get_trend_analysis(
    commodity: str,
    region: Optional[str] = None,
    analysis_period_days: int = 30
):
    """Get comprehensive trend analysis for a commodity"""
    if not trend_analyzer:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        analysis = await trend_analyzer.analyze_price_trends(
            commodity=commodity,
            region=region,
            analysis_period_days=analysis_period_days
        )
        return analysis
    except Exception as e:
        logger.error("Failed to analyze trends", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/predict")
async def predict_price(
    commodity: str,
    region: Optional[str] = None,
    prediction_horizon_days: int = 7,
    historical_days: int = 60
):
    """Predict future price for a commodity"""
    if not trend_analyzer:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        prediction = await trend_analyzer.predict_price(
            commodity=commodity,
            region=region,
            prediction_horizon_days=prediction_horizon_days,
            historical_days=historical_days
        )
        return prediction
    except Exception as e:
        logger.error("Failed to predict price", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/volatility/{commodity}")
async def get_volatility_indicators(
    commodity: str,
    region: Optional[str] = None,
    measurement_period_days: int = 30
):
    """Get market volatility indicators for a commodity"""
    if not trend_analyzer:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        indicators = await trend_analyzer.calculate_volatility_indicators(
            commodity=commodity,
            region=region,
            measurement_period_days=measurement_period_days
        )
        return indicators
    except Exception as e:
        logger.error("Failed to calculate volatility indicators", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")