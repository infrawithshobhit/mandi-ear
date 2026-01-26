"""
Benchmark Engine for MANDI EAR™
Handles price floor setting and benchmark management
"""

import asyncio
import statistics
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
import structlog
from models import (
    PriceFloor, FarmerBenchmark, BenchmarkStatus, 
    PriceDataPoint, TrendAnalysis, MarketContext
)

logger = structlog.get_logger()

class BenchmarkEngine:
    """
    Core engine for managing farmer benchmarks and price floors
    """
    
    def __init__(self):
        """Initialize the benchmark engine"""
        logger.info("BenchmarkEngine initialized")
    
    async def set_price_floor(
        self, 
        farmer_id: UUID, 
        commodity: str, 
        floor_price: float,
        unit: str = "per_quintal",
        reasoning: Optional[str] = None,
        db=None
    ) -> PriceFloor:
        """
        Set minimum price floor for a farmer's commodity
        
        Args:
            farmer_id: Farmer's unique identifier
            commodity: Commodity name
            floor_price: Minimum acceptable price
            unit: Price unit
            reasoning: Reason for setting this floor
            db: Database connection
            
        Returns:
            Created PriceFloor object
        """
        try:
            logger.info("Setting price floor", 
                       farmer_id=str(farmer_id),
                       commodity=commodity,
                       floor_price=floor_price)
            
            # Deactivate existing price floors for this commodity
            await self._deactivate_existing_floors(farmer_id, commodity, db)
            
            # Create new price floor
            price_floor = PriceFloor(
                farmer_id=farmer_id,
                commodity=commodity.lower().strip(),
                floor_price=floor_price,
                unit=unit,
                reasoning=reasoning,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_active=True
            )
            
            # Store in database (simulated)
            await self._store_price_floor(price_floor, db)
            
            logger.info("Price floor set successfully", 
                       floor_id=str(price_floor.id),
                       farmer_id=str(farmer_id),
                       commodity=commodity)
            
            return price_floor
            
        except Exception as e:
            logger.error("Failed to set price floor", error=str(e))
            raise
    
    async def get_price_floors(self, farmer_id: UUID, db=None) -> List[PriceFloor]:
        """
        Get all active price floors for a farmer
        
        Args:
            farmer_id: Farmer's unique identifier
            db: Database connection
            
        Returns:
            List of active price floors
        """
        try:
            # Simulate database query
            price_floors = await self._fetch_price_floors(farmer_id, db)
            
            logger.info("Retrieved price floors", 
                       farmer_id=str(farmer_id),
                       floors_count=len(price_floors))
            
            return price_floors
            
        except Exception as e:
            logger.error("Failed to get price floors", error=str(e))
            raise
    
    async def get_farmer_benchmarks(
        self, 
        farmer_id: UUID, 
        commodity: Optional[str] = None,
        db=None
    ) -> List[FarmerBenchmark]:
        """
        Get all benchmarks for a farmer
        
        Args:
            farmer_id: Farmer's unique identifier
            commodity: Optional commodity filter
            db: Database connection
            
        Returns:
            List of farmer benchmarks
        """
        try:
            benchmarks = await self._fetch_farmer_benchmarks(farmer_id, commodity, db)
            
            logger.info("Retrieved farmer benchmarks", 
                       farmer_id=str(farmer_id),
                       commodity=commodity,
                       benchmarks_count=len(benchmarks))
            
            return benchmarks
            
        except Exception as e:
            logger.error("Failed to get farmer benchmarks", error=str(e))
            raise
    
    async def update_benchmark(
        self, 
        benchmark_id: UUID, 
        update_data: Dict[str, Any],
        db=None
    ) -> FarmerBenchmark:
        """
        Update an existing benchmark
        
        Args:
            benchmark_id: Benchmark unique identifier
            update_data: Updated benchmark data
            db: Database connection
            
        Returns:
            Updated benchmark
        """
        try:
            logger.info("Updating benchmark", benchmark_id=str(benchmark_id))
            
            # Fetch existing benchmark
            benchmark = await self._fetch_benchmark_by_id(benchmark_id, db)
            if not benchmark:
                raise ValueError(f"Benchmark {benchmark_id} not found")
            
            # Update fields
            if "benchmark_price" in update_data:
                benchmark.benchmark_price = update_data["benchmark_price"]
            if "confidence_score" in update_data:
                benchmark.confidence_score = update_data["confidence_score"]
            if "price_range" in update_data:
                benchmark.price_range = update_data["price_range"]
            if "status" in update_data:
                benchmark.status = BenchmarkStatus(update_data["status"])
            
            benchmark.updated_at = datetime.utcnow()
            
            # Store updated benchmark
            await self._store_benchmark(benchmark, db)
            
            logger.info("Benchmark updated successfully", benchmark_id=str(benchmark_id))
            
            return benchmark
            
        except Exception as e:
            logger.error("Failed to update benchmark", error=str(e))
            raise
    
    async def deactivate_price_floor(self, floor_id: UUID, db=None):
        """
        Deactivate a price floor
        
        Args:
            floor_id: Price floor unique identifier
            db: Database connection
        """
        try:
            logger.info("Deactivating price floor", floor_id=str(floor_id))
            
            # Fetch and deactivate price floor
            await self._deactivate_floor_by_id(floor_id, db)
            
            logger.info("Price floor deactivated successfully", floor_id=str(floor_id))
            
        except Exception as e:
            logger.error("Failed to deactivate price floor", error=str(e))
            raise
    
    async def get_farmer_analytics(
        self, 
        farmer_id: UUID, 
        period: str = "30d",
        db=None
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a farmer
        
        Args:
            farmer_id: Farmer's unique identifier
            period: Analysis period (7d, 30d, 90d, 1y)
            db: Database connection
            
        Returns:
            Comprehensive analytics data
        """
        try:
            logger.info("Generating farmer analytics", 
                       farmer_id=str(farmer_id),
                       period=period)
            
            # Parse period
            days = self._parse_period(period)
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Fetch data
            benchmarks = await self._fetch_farmer_benchmarks(farmer_id, None, db)
            price_floors = await self._fetch_price_floors(farmer_id, db)
            performance_data = await self._fetch_performance_data(farmer_id, start_date, db)
            
            # Calculate analytics
            analytics = {
                "summary": {
                    "total_benchmarks": len(benchmarks),
                    "active_price_floors": len([f for f in price_floors if f.is_active]),
                    "analysis_period": period,
                    "data_from": start_date.isoformat(),
                    "data_to": datetime.utcnow().isoformat()
                },
                "benchmarks": {
                    "by_commodity": self._group_benchmarks_by_commodity(benchmarks),
                    "confidence_distribution": self._analyze_confidence_distribution(benchmarks),
                    "age_analysis": self._analyze_benchmark_age(benchmarks)
                },
                "price_floors": {
                    "by_commodity": self._group_floors_by_commodity(price_floors),
                    "utilization_rate": self._calculate_floor_utilization(price_floors, performance_data)
                },
                "performance": {
                    "total_transactions": len(performance_data),
                    "average_performance_score": self._calculate_avg_performance(performance_data),
                    "benchmark_adherence": self._calculate_benchmark_adherence(performance_data),
                    "floor_violations": self._count_floor_violations(performance_data)
                },
                "trends": {
                    "price_trends": self._analyze_price_trends(performance_data),
                    "performance_trends": self._analyze_performance_trends(performance_data)
                },
                "recommendations": self._generate_recommendations(
                    benchmarks, price_floors, performance_data
                )
            }
            
            logger.info("Farmer analytics generated successfully", 
                       farmer_id=str(farmer_id))
            
            return analytics
            
        except Exception as e:
            logger.error("Failed to generate farmer analytics", error=str(e))
            raise
    
    def _parse_period(self, period: str) -> int:
        """Parse period string to days"""
        period_map = {
            "7d": 7,
            "30d": 30,
            "90d": 90,
            "1y": 365
        }
        return period_map.get(period, 30)
    
    def _group_benchmarks_by_commodity(self, benchmarks: List[FarmerBenchmark]) -> Dict[str, Any]:
        """Group benchmarks by commodity"""
        grouped = {}
        for benchmark in benchmarks:
            commodity = benchmark.commodity
            if commodity not in grouped:
                grouped[commodity] = []
            grouped[commodity].append({
                "benchmark_price": benchmark.benchmark_price,
                "confidence_score": benchmark.confidence_score,
                "data_points_count": benchmark.data_points_count,
                "created_at": benchmark.created_at.isoformat()
            })
        return grouped
    
    def _analyze_confidence_distribution(self, benchmarks: List[FarmerBenchmark]) -> Dict[str, Any]:
        """Analyze confidence score distribution"""
        if not benchmarks:
            return {"average": 0, "distribution": {}}
        
        scores = [b.confidence_score for b in benchmarks]
        return {
            "average": statistics.mean(scores),
            "median": statistics.median(scores),
            "min": min(scores),
            "max": max(scores),
            "distribution": {
                "high (>0.8)": len([s for s in scores if s > 0.8]),
                "medium (0.5-0.8)": len([s for s in scores if 0.5 <= s <= 0.8]),
                "low (<0.5)": len([s for s in scores if s < 0.5])
            }
        }
    
    def _analyze_benchmark_age(self, benchmarks: List[FarmerBenchmark]) -> Dict[str, Any]:
        """Analyze benchmark age distribution"""
        if not benchmarks:
            return {"average_age_days": 0, "distribution": {}}
        
        now = datetime.utcnow()
        ages = [(now - b.created_at).days for b in benchmarks]
        
        return {
            "average_age_days": statistics.mean(ages),
            "distribution": {
                "fresh (<7 days)": len([a for a in ages if a < 7]),
                "recent (7-30 days)": len([a for a in ages if 7 <= a <= 30]),
                "old (>30 days)": len([a for a in ages if a > 30])
            }
        }
    
    def _group_floors_by_commodity(self, price_floors: List[PriceFloor]) -> Dict[str, Any]:
        """Group price floors by commodity"""
        grouped = {}
        for floor in price_floors:
            commodity = floor.commodity
            if commodity not in grouped:
                grouped[commodity] = []
            grouped[commodity].append({
                "floor_price": floor.floor_price,
                "unit": floor.unit,
                "reasoning": floor.reasoning,
                "created_at": floor.created_at.isoformat(),
                "is_active": floor.is_active
            })
        return grouped
    
    def _calculate_floor_utilization(self, price_floors: List[PriceFloor], performance_data: List) -> float:
        """Calculate price floor utilization rate"""
        if not price_floors or not performance_data:
            return 0.0
        
        # Simulate utilization calculation
        active_floors = [f for f in price_floors if f.is_active]
        if not active_floors:
            return 0.0
        
        # In real implementation, this would check actual sales against floors
        return 0.75  # 75% utilization rate (simulated)
    
    def _calculate_avg_performance(self, performance_data: List) -> float:
        """Calculate average performance score"""
        if not performance_data:
            return 0.0
        
        # Simulate performance calculation
        return 78.5  # Average performance score (simulated)
    
    def _calculate_benchmark_adherence(self, performance_data: List) -> float:
        """Calculate benchmark adherence rate"""
        if not performance_data:
            return 0.0
        
        # Simulate adherence calculation
        return 0.82  # 82% adherence rate (simulated)
    
    def _count_floor_violations(self, performance_data: List) -> int:
        """Count price floor violations"""
        # Simulate violation count
        return 2  # 2 violations (simulated)
    
    def _analyze_price_trends(self, performance_data: List) -> Dict[str, Any]:
        """Analyze price trends"""
        return {
            "overall_trend": "rising",
            "trend_strength": 0.65,
            "volatility": "medium",
            "seasonal_patterns": ["harvest_dip", "festival_spike"]
        }
    
    def _analyze_performance_trends(self, performance_data: List) -> Dict[str, Any]:
        """Analyze performance trends"""
        return {
            "improvement_rate": 0.15,  # 15% improvement
            "consistency": "good",
            "best_performing_period": "last_30_days",
            "areas_for_improvement": ["timing", "market_selection"]
        }
    
    def _generate_recommendations(
        self, 
        benchmarks: List[FarmerBenchmark], 
        price_floors: List[PriceFloor], 
        performance_data: List
    ) -> List[Dict[str, Any]]:
        """Generate personalized recommendations"""
        recommendations = []
        
        # Benchmark-based recommendations
        if len(benchmarks) < 3:
            recommendations.append({
                "type": "benchmark_creation",
                "priority": "high",
                "title": "Create More Benchmarks",
                "description": "You have limited benchmarks. Create more to improve price insights.",
                "action": "analyze_more_conversations"
            })
        
        # Price floor recommendations
        active_floors = [f for f in price_floors if f.is_active]
        if len(active_floors) == 0:
            recommendations.append({
                "type": "price_floor",
                "priority": "medium",
                "title": "Set Price Floors",
                "description": "Set minimum price floors to protect against low prices.",
                "action": "set_price_floors"
            })
        
        # Performance recommendations
        recommendations.append({
            "type": "performance",
            "priority": "medium",
            "title": "Market Timing",
            "description": "Consider selling during peak demand periods for better prices.",
            "action": "optimize_timing"
        })
        
        return recommendations
    
    # Database simulation methods
    async def _deactivate_existing_floors(self, farmer_id: UUID, commodity: str, db):
        """Deactivate existing price floors for commodity"""
        # Simulate database operation
        await asyncio.sleep(0.01)
        logger.debug("Deactivated existing floors", farmer_id=str(farmer_id), commodity=commodity)
    
    async def _store_price_floor(self, price_floor: PriceFloor, db):
        """Store price floor in database"""
        # Simulate database operation
        await asyncio.sleep(0.01)
        logger.debug("Stored price floor", floor_id=str(price_floor.id))
    
    async def _fetch_price_floors(self, farmer_id: UUID, db) -> List[PriceFloor]:
        """Fetch price floors from database"""
        # Simulate database operation
        await asyncio.sleep(0.01)
        
        # Return simulated data
        return [
            PriceFloor(
                farmer_id=farmer_id,
                commodity="wheat",
                floor_price=2000.0,
                unit="per_quintal",
                reasoning="Based on production costs",
                created_at=datetime.utcnow() - timedelta(days=10),
                is_active=True
            ),
            PriceFloor(
                farmer_id=farmer_id,
                commodity="rice",
                floor_price=1800.0,
                unit="per_quintal",
                reasoning="Market analysis based",
                created_at=datetime.utcnow() - timedelta(days=5),
                is_active=True
            )
        ]
    
    async def _fetch_farmer_benchmarks(self, farmer_id: UUID, commodity: Optional[str], db) -> List[FarmerBenchmark]:
        """Fetch farmer benchmarks from database"""
        # Simulate database operation
        await asyncio.sleep(0.01)
        
        # Return simulated data
        benchmarks = [
            FarmerBenchmark(
                farmer_id=farmer_id,
                commodity="wheat",
                benchmark_price=2150.0,
                price_range={"min": 1900.0, "max": 2400.0, "avg": 2150.0, "median": 2100.0},
                confidence_score=0.85,
                data_points_count=25,
                analysis_period="30 days",
                location_context="local_mandi",
                created_at=datetime.utcnow() - timedelta(days=15)
            ),
            FarmerBenchmark(
                farmer_id=farmer_id,
                commodity="rice",
                benchmark_price=1950.0,
                price_range={"min": 1700.0, "max": 2200.0, "avg": 1950.0, "median": 1900.0},
                confidence_score=0.78,
                data_points_count=18,
                analysis_period="30 days",
                location_context="regional_market",
                created_at=datetime.utcnow() - timedelta(days=8)
            )
        ]
        
        if commodity:
            benchmarks = [b for b in benchmarks if b.commodity == commodity.lower()]
        
        return benchmarks
    
    async def _fetch_benchmark_by_id(self, benchmark_id: UUID, db) -> Optional[FarmerBenchmark]:
        """Fetch benchmark by ID"""
        # Simulate database operation
        await asyncio.sleep(0.01)
        
        # Return simulated benchmark
        return FarmerBenchmark(
            id=benchmark_id,
            farmer_id=UUID("12345678-1234-5678-9012-123456789012"),
            commodity="wheat",
            benchmark_price=2150.0,
            price_range={"min": 1900.0, "max": 2400.0, "avg": 2150.0, "median": 2100.0},
            confidence_score=0.85,
            data_points_count=25,
            analysis_period="30 days",
            created_at=datetime.utcnow() - timedelta(days=15)
        )
    
    async def _store_benchmark(self, benchmark: FarmerBenchmark, db):
        """Store benchmark in database"""
        # Simulate database operation
        await asyncio.sleep(0.01)
        logger.debug("Stored benchmark", benchmark_id=str(benchmark.id))
    
    async def _deactivate_floor_by_id(self, floor_id: UUID, db):
        """Deactivate price floor by ID"""
        # Simulate database operation
        await asyncio.sleep(0.01)
        logger.debug("Deactivated price floor", floor_id=str(floor_id))
    
    async def _fetch_performance_data(self, farmer_id: UUID, start_date: datetime, db) -> List:
        """Fetch performance data"""
        # Simulate database operation
        await asyncio.sleep(0.01)
        
        # Return simulated performance data
        return [
            {"commodity": "wheat", "performance_score": 85.0, "sale_date": datetime.utcnow() - timedelta(days=5)},
            {"commodity": "rice", "performance_score": 72.0, "sale_date": datetime.utcnow() - timedelta(days=12)},
            {"commodity": "wheat", "performance_score": 78.0, "sale_date": datetime.utcnow() - timedelta(days=20)}
        ]