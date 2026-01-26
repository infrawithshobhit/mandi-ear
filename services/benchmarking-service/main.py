"""
MANDI EAR™ Benchmarking Service
Personalized benchmarking system for farmers
"""

import asyncio
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import structlog
from database import get_database
from models import (
    FarmerBenchmark, PriceFloor, ConversationRecord, 
    PerformanceMetric, BenchmarkAnalysis, BenchmarkRequest,
    PriceFloorRequest, PerformanceTrackingRequest
)
from benchmark_engine import BenchmarkEngine
from performance_tracker import PerformanceTracker
from historical_analyzer import HistoricalAnalyzer
from performance_analytics import PerformanceAnalytics

logger = structlog.get_logger()

app = FastAPI(
    title="MANDI EAR™ Benchmarking Service",
    description="Personalized benchmarking and performance tracking for farmers",
    version="1.0.0"
)

# Initialize components
benchmark_engine = BenchmarkEngine()
performance_tracker = PerformanceTracker()
historical_analyzer = HistoricalAnalyzer()
performance_analytics = PerformanceAnalytics()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Benchmarking Service",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/price-floors", response_model=Dict[str, Any])
async def set_price_floor(request: PriceFloorRequest, db=Depends(get_database)):
    """
    Set minimum price floor for a farmer's commodity
    
    Args:
        request: Price floor setting request
        
    Returns:
        Confirmation of price floor setting
    """
    try:
        logger.info("Setting price floor", 
                   farmer_id=request.farmer_id,
                   commodity=request.commodity,
                   floor_price=request.floor_price)
        
        # Create or update price floor
        price_floor = await benchmark_engine.set_price_floor(
            farmer_id=request.farmer_id,
            commodity=request.commodity,
            floor_price=request.floor_price,
            unit=request.unit,
            reasoning=request.reasoning,
            db=db
        )
        
        return {
            "status": "success",
            "message": "Price floor set successfully",
            "price_floor": {
                "id": str(price_floor.id),
                "farmer_id": str(price_floor.farmer_id),
                "commodity": price_floor.commodity,
                "floor_price": price_floor.floor_price,
                "unit": price_floor.unit,
                "reasoning": price_floor.reasoning,
                "created_at": price_floor.created_at.isoformat(),
                "is_active": price_floor.is_active
            }
        }
        
    except Exception as e:
        logger.error("Failed to set price floor", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to set price floor: {str(e)}")

@app.get("/price-floors/{farmer_id}", response_model=Dict[str, Any])
async def get_price_floors(farmer_id: UUID, db=Depends(get_database)):
    """
    Get all price floors for a farmer
    
    Args:
        farmer_id: Farmer's unique identifier
        
    Returns:
        List of active price floors
    """
    try:
        price_floors = await benchmark_engine.get_price_floors(farmer_id, db)
        
        floors_data = []
        for floor in price_floors:
            floors_data.append({
                "id": str(floor.id),
                "commodity": floor.commodity,
                "floor_price": floor.floor_price,
                "unit": floor.unit,
                "reasoning": floor.reasoning,
                "created_at": floor.created_at.isoformat(),
                "updated_at": floor.updated_at.isoformat(),
                "is_active": floor.is_active
            })
        
        return {
            "status": "success",
            "farmer_id": str(farmer_id),
            "price_floors": floors_data,
            "total_floors": len(floors_data)
        }
        
    except Exception as e:
        logger.error("Failed to get price floors", error=str(e), farmer_id=str(farmer_id))
        raise HTTPException(status_code=500, detail=f"Failed to get price floors: {str(e)}")

@app.post("/benchmarks/create", response_model=Dict[str, Any])
async def create_benchmark(request: BenchmarkRequest, db=Depends(get_database)):
    """
    Create historical benchmark from conversation data
    
    Args:
        request: Benchmark creation request
        
    Returns:
        Created benchmark analysis
    """
    try:
        logger.info("Creating benchmark", 
                   farmer_id=request.farmer_id,
                   commodity=request.commodity,
                   analysis_period=request.analysis_period_days)
        
        # Analyze historical conversations
        benchmark = await historical_analyzer.create_benchmark_from_conversations(
            farmer_id=request.farmer_id,
            commodity=request.commodity,
            analysis_period_days=request.analysis_period_days,
            location_filter=request.location_filter,
            db=db
        )
        
        return {
            "status": "success",
            "message": "Benchmark created successfully",
            "benchmark": {
                "id": str(benchmark.id),
                "farmer_id": str(benchmark.farmer_id),
                "commodity": benchmark.commodity,
                "benchmark_price": benchmark.benchmark_price,
                "price_range": benchmark.price_range,
                "confidence_score": benchmark.confidence_score,
                "data_points_count": benchmark.data_points_count,
                "analysis_period": benchmark.analysis_period,
                "location_context": benchmark.location_context,
                "created_at": benchmark.created_at.isoformat(),
                "metadata": benchmark.metadata
            }
        }
        
    except Exception as e:
        logger.error("Failed to create benchmark", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create benchmark: {str(e)}")

@app.get("/benchmarks/{farmer_id}", response_model=Dict[str, Any])
async def get_farmer_benchmarks(
    farmer_id: UUID, 
    commodity: Optional[str] = None,
    db=Depends(get_database)
):
    """
    Get all benchmarks for a farmer
    
    Args:
        farmer_id: Farmer's unique identifier
        commodity: Optional commodity filter
        
    Returns:
        List of farmer's benchmarks
    """
    try:
        benchmarks = await benchmark_engine.get_farmer_benchmarks(
            farmer_id, commodity, db
        )
        
        benchmarks_data = []
        for benchmark in benchmarks:
            benchmarks_data.append({
                "id": str(benchmark.id),
                "commodity": benchmark.commodity,
                "benchmark_price": benchmark.benchmark_price,
                "price_range": benchmark.price_range,
                "confidence_score": benchmark.confidence_score,
                "data_points_count": benchmark.data_points_count,
                "analysis_period": benchmark.analysis_period,
                "location_context": benchmark.location_context,
                "created_at": benchmark.created_at.isoformat(),
                "is_active": benchmark.is_active
            })
        
        return {
            "status": "success",
            "farmer_id": str(farmer_id),
            "commodity_filter": commodity,
            "benchmarks": benchmarks_data,
            "total_benchmarks": len(benchmarks_data)
        }
        
    except Exception as e:
        logger.error("Failed to get benchmarks", error=str(e), farmer_id=str(farmer_id))
        raise HTTPException(status_code=500, detail=f"Failed to get benchmarks: {str(e)}")

@app.post("/performance/track", response_model=Dict[str, Any])
async def track_performance(request: PerformanceTrackingRequest, db=Depends(get_database)):
    """
    Track farmer's performance against benchmarks
    
    Args:
        request: Performance tracking request
        
    Returns:
        Performance analysis results
    """
    try:
        logger.info("Tracking performance", 
                   farmer_id=request.farmer_id,
                   commodity=request.commodity,
                   actual_price=request.actual_price)
        
        # Track performance against benchmarks
        performance = await performance_tracker.track_performance(
            farmer_id=request.farmer_id,
            commodity=request.commodity,
            actual_price=request.actual_price,
            quantity_sold=request.quantity_sold,
            sale_date=request.sale_date,
            location=request.location,
            db=db
        )
        
        return {
            "status": "success",
            "message": "Performance tracked successfully",
            "performance": {
                "id": str(performance.id),
                "farmer_id": str(performance.farmer_id),
                "commodity": performance.commodity,
                "actual_price": performance.actual_price,
                "benchmark_price": performance.benchmark_price,
                "price_floor": performance.price_floor,
                "performance_score": performance.performance_score,
                "vs_benchmark": performance.vs_benchmark,
                "vs_floor": performance.vs_floor,
                "quantity_sold": performance.quantity_sold,
                "total_revenue": performance.total_revenue,
                "benchmark_revenue": performance.benchmark_revenue,
                "revenue_difference": performance.revenue_difference,
                "sale_date": performance.sale_date.isoformat(),
                "location": performance.location,
                "analysis": performance.analysis
            }
        }
        
    except Exception as e:
        logger.error("Failed to track performance", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to track performance: {str(e)}")

@app.get("/performance/{farmer_id}", response_model=Dict[str, Any])
async def get_performance_history(
    farmer_id: UUID,
    commodity: Optional[str] = None,
    days: int = 30,
    db=Depends(get_database)
):
    """
    Get farmer's performance history
    
    Args:
        farmer_id: Farmer's unique identifier
        commodity: Optional commodity filter
        days: Number of days to look back
        
    Returns:
        Performance history and analytics
    """
    try:
        performance_data = await performance_tracker.get_performance_history(
            farmer_id, commodity, days, db
        )
        
        return {
            "status": "success",
            "farmer_id": str(farmer_id),
            "commodity_filter": commodity,
            "analysis_period_days": days,
            "performance_summary": performance_data["summary"],
            "performance_records": performance_data["records"],
            "trends": performance_data["trends"],
            "recommendations": performance_data["recommendations"]
        }
        
    except Exception as e:
        logger.error("Failed to get performance history", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get performance history: {str(e)}")

@app.post("/conversations/record", response_model=Dict[str, Any])
async def record_conversation(
    farmer_id: UUID,
    conversation_data: Dict[str, Any],
    db=Depends(get_database)
):
    """
    Record conversation data for benchmark creation
    
    Args:
        farmer_id: Farmer's unique identifier
        conversation_data: Processed conversation data from ambient AI
        
    Returns:
        Confirmation of conversation recording
    """
    try:
        logger.info("Recording conversation", 
                   farmer_id=str(farmer_id),
                   commodity=conversation_data.get("commodity"))
        
        # Record conversation for future benchmark analysis
        conversation_record = await historical_analyzer.record_conversation(
            farmer_id=farmer_id,
            conversation_data=conversation_data,
            db=db
        )
        
        return {
            "status": "success",
            "message": "Conversation recorded successfully",
            "record_id": str(conversation_record.id),
            "farmer_id": str(farmer_id),
            "commodity": conversation_record.commodity,
            "price_extracted": conversation_record.price_extracted,
            "confidence": conversation_record.confidence,
            "recorded_at": conversation_record.recorded_at.isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to record conversation", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to record conversation: {str(e)}")

@app.get("/analytics/{farmer_id}", response_model=Dict[str, Any])
async def get_farmer_analytics(
    farmer_id: UUID,
    period: str = "30d",
    db=Depends(get_database)
):
    """
    Get comprehensive analytics for a farmer
    
    Args:
        farmer_id: Farmer's unique identifier
        period: Analysis period (7d, 30d, 90d, 1y)
        
    Returns:
        Comprehensive farmer analytics
    """
    try:
        analytics = await benchmark_engine.get_farmer_analytics(
            farmer_id, period, db
        )
        
        return {
            "status": "success",
            "farmer_id": str(farmer_id),
            "analysis_period": period,
            "analytics": analytics
        }
        
    except Exception as e:
        logger.error("Failed to get farmer analytics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get farmer analytics: {str(e)}")

@app.post("/benchmarks/{benchmark_id}/update", response_model=Dict[str, Any])
async def update_benchmark(
    benchmark_id: UUID,
    update_data: Dict[str, Any],
    db=Depends(get_database)
):
    """
    Update an existing benchmark
    
    Args:
        benchmark_id: Benchmark unique identifier
        update_data: Updated benchmark data
        
    Returns:
        Updated benchmark information
    """
    try:
        updated_benchmark = await benchmark_engine.update_benchmark(
            benchmark_id, update_data, db
        )
        
        return {
            "status": "success",
            "message": "Benchmark updated successfully",
            "benchmark": {
                "id": str(updated_benchmark.id),
                "commodity": updated_benchmark.commodity,
                "benchmark_price": updated_benchmark.benchmark_price,
                "confidence_score": updated_benchmark.confidence_score,
                "updated_at": updated_benchmark.updated_at.isoformat()
            }
        }
        
    except Exception as e:
        logger.error("Failed to update benchmark", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update benchmark: {str(e)}")

@app.delete("/price-floors/{floor_id}", response_model=Dict[str, Any])
async def deactivate_price_floor(floor_id: UUID, db=Depends(get_database)):
    """
    Deactivate a price floor
    
    Args:
        floor_id: Price floor unique identifier
        
    Returns:
        Confirmation of deactivation
    """
    try:
        await benchmark_engine.deactivate_price_floor(floor_id, db)
        
        return {
            "status": "success",
            "message": "Price floor deactivated successfully",
            "floor_id": str(floor_id)
        }
        
    except Exception as e:
        logger.error("Failed to deactivate price floor", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to deactivate price floor: {str(e)}")

@app.get("/analytics/{farmer_id}/income-improvement", response_model=Dict[str, Any])
async def get_income_improvement_analysis(
    farmer_id: UUID,
    commodity: Optional[str] = None,
    baseline_period_days: int = 90,
    comparison_period_days: int = 30,
    db=Depends(get_database)
):
    """
    Get income improvement analysis comparing recent performance against baseline
    
    Args:
        farmer_id: Farmer's unique identifier
        commodity: Optional commodity filter
        baseline_period_days: Days to look back for baseline calculation
        comparison_period_days: Recent period for comparison
        
    Returns:
        Income improvement analysis with metrics and trends
    """
    try:
        logger.info("Getting income improvement analysis", 
                   farmer_id=str(farmer_id),
                   commodity=commodity)
        
        analysis = await performance_analytics.calculate_income_improvement(
            farmer_id=farmer_id,
            commodity=commodity,
            baseline_period_days=baseline_period_days,
            comparison_period_days=comparison_period_days,
            db=db
        )
        
        return {
            "status": "success",
            "message": "Income improvement analysis completed",
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error("Failed to get income improvement analysis", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get income improvement analysis: {str(e)}")

@app.get("/analytics/{farmer_id}/performance-trends", response_model=Dict[str, Any])
async def get_performance_trends_analysis(
    farmer_id: UUID,
    commodity: Optional[str] = None,
    analysis_period_days: int = 180,
    trend_window_days: int = 30,
    db=Depends(get_database)
):
    """
    Get comprehensive performance trends analysis
    
    Args:
        farmer_id: Farmer's unique identifier
        commodity: Optional commodity filter
        analysis_period_days: Total period to analyze
        trend_window_days: Size of rolling window for trend analysis
        
    Returns:
        Comprehensive trend analysis with patterns and predictions
    """
    try:
        logger.info("Getting performance trends analysis", 
                   farmer_id=str(farmer_id),
                   commodity=commodity)
        
        analysis = await performance_analytics.analyze_performance_trends(
            farmer_id=farmer_id,
            commodity=commodity,
            analysis_period_days=analysis_period_days,
            trend_window_days=trend_window_days,
            db=db
        )
        
        return {
            "status": "success",
            "message": "Performance trends analysis completed",
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error("Failed to get performance trends analysis", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get performance trends analysis: {str(e)}")

@app.get("/analytics/{farmer_id}/comparative-dashboard", response_model=Dict[str, Any])
async def get_comparative_analytics_dashboard(
    farmer_id: UUID,
    commodity: Optional[str] = None,
    comparison_period_days: int = 90,
    db=Depends(get_database)
):
    """
    Get comprehensive comparative analytics dashboard
    
    Args:
        farmer_id: Farmer's unique identifier
        commodity: Optional commodity filter
        comparison_period_days: Period for comparison analysis
        
    Returns:
        Comprehensive comparative analytics dashboard
    """
    try:
        logger.info("Getting comparative analytics dashboard", 
                   farmer_id=str(farmer_id),
                   commodity=commodity)
        
        dashboard = await performance_analytics.generate_comparative_analytics(
            farmer_id=farmer_id,
            commodity=commodity,
            comparison_period_days=comparison_period_days,
            db=db
        )
        
        return {
            "status": "success",
            "message": "Comparative analytics dashboard generated",
            "dashboard": dashboard
        }
        
    except Exception as e:
        logger.error("Failed to get comparative analytics dashboard", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get comparative analytics dashboard: {str(e)}")

@app.get("/analytics/{farmer_id}/comprehensive", response_model=Dict[str, Any])
async def get_comprehensive_performance_analytics(
    farmer_id: UUID,
    commodity: Optional[str] = None,
    analysis_period_days: int = 180,
    db=Depends(get_database)
):
    """
    Get comprehensive performance analytics combining all analysis types
    
    Args:
        farmer_id: Farmer's unique identifier
        commodity: Optional commodity filter
        analysis_period_days: Period for comprehensive analysis
        
    Returns:
        Comprehensive performance analytics report
    """
    try:
        logger.info("Getting comprehensive performance analytics", 
                   farmer_id=str(farmer_id),
                   commodity=commodity)
        
        # Get all analytics in parallel
        income_improvement_task = performance_analytics.calculate_income_improvement(
            farmer_id=farmer_id,
            commodity=commodity,
            baseline_period_days=analysis_period_days // 2,
            comparison_period_days=analysis_period_days // 4,
            db=db
        )
        
        trends_analysis_task = performance_analytics.analyze_performance_trends(
            farmer_id=farmer_id,
            commodity=commodity,
            analysis_period_days=analysis_period_days,
            trend_window_days=30,
            db=db
        )
        
        comparative_analytics_task = performance_analytics.generate_comparative_analytics(
            farmer_id=farmer_id,
            commodity=commodity,
            comparison_period_days=analysis_period_days // 2,
            db=db
        )
        
        # Wait for all analyses to complete
        income_improvement, trends_analysis, comparative_analytics = await asyncio.gather(
            income_improvement_task,
            trends_analysis_task,
            comparative_analytics_task
        )
        
        # Combine all analytics
        comprehensive_report = {
            "farmer_id": str(farmer_id),
            "commodity_filter": commodity,
            "analysis_period_days": analysis_period_days,
            "generated_at": datetime.utcnow().isoformat(),
            "income_improvement": income_improvement,
            "performance_trends": trends_analysis,
            "comparative_analytics": comparative_analytics,
            "executive_summary": {
                "overall_performance_trend": trends_analysis.get("overall_trend", {}).get("direction", "unknown"),
                "income_improvement_percentage": income_improvement.get("improvement_analysis", {}).get("revenue_improvement", {}).get("percentage", 0),
                "regional_ranking": comparative_analytics.get("performance_rankings", {}).get("overall_percentile", 0),
                "key_strengths": comparative_analytics.get("performance_scorecard", {}).get("strengths", []),
                "improvement_opportunities": comparative_analytics.get("improvement_opportunities", [])
            }
        }
        
        return {
            "status": "success",
            "message": "Comprehensive performance analytics completed",
            "report": comprehensive_report
        }
        
    except Exception as e:
        logger.error("Failed to get comprehensive performance analytics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get comprehensive performance analytics: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)