"""
Performance Tracker for MANDI EAR™
Tracks farmer performance against benchmarks and price floors
"""

import asyncio
import statistics
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
import structlog
from models import (
    PerformanceMetric, PerformanceCategory, FarmerBenchmark, PriceFloor
)

logger = structlog.get_logger()

class PerformanceTracker:
    """
    Tracks farmer performance against established benchmarks and price floors
    """
    
    def __init__(self):
        """Initialize the performance tracker"""
        logger.info("PerformanceTracker initialized")
    
    async def track_performance(
        self,
        farmer_id: UUID,
        commodity: str,
        actual_price: float,
        quantity_sold: float,
        sale_date: datetime,
        location: Optional[str] = None,
        db=None
    ) -> PerformanceMetric:
        """
        Track farmer's performance against benchmarks and price floors
        
        Args:
            farmer_id: Farmer's unique identifier
            commodity: Commodity sold
            actual_price: Actual selling price
            quantity_sold: Quantity sold
            sale_date: Date of sale
            location: Sale location
            db: Database connection
            
        Returns:
            PerformanceMetric with analysis
        """
        try:
            logger.info("Tracking performance", 
                       farmer_id=str(farmer_id),
                       commodity=commodity,
                       actual_price=actual_price,
                       quantity_sold=quantity_sold)
            
            # Get relevant benchmark and price floor
            benchmark = await self._get_relevant_benchmark(farmer_id, commodity, db)
            price_floor = await self._get_active_price_floor(farmer_id, commodity, db)
            
            # Calculate performance metrics
            performance_score = self._calculate_performance_score(
                actual_price, benchmark, price_floor
            )
            
            vs_benchmark = self._calculate_vs_benchmark(actual_price, benchmark)
            vs_floor = self._calculate_vs_floor(actual_price, price_floor)
            
            # Calculate revenue metrics
            total_revenue = actual_price * quantity_sold
            benchmark_revenue = (benchmark.benchmark_price * quantity_sold) if benchmark else None
            revenue_difference = (total_revenue - benchmark_revenue) if benchmark_revenue else None
            
            # Determine performance category
            category = self._determine_performance_category(performance_score)
            
            # Generate analysis
            analysis = self._generate_performance_analysis(
                actual_price, benchmark, price_floor, vs_benchmark, vs_floor, location
            )
            
            # Create performance metric
            performance = PerformanceMetric(
                farmer_id=farmer_id,
                commodity=commodity.lower().strip(),
                actual_price=actual_price,
                benchmark_price=benchmark.benchmark_price if benchmark else None,
                price_floor=price_floor.floor_price if price_floor else None,
                performance_score=performance_score,
                vs_benchmark=vs_benchmark,
                vs_floor=vs_floor,
                quantity_sold=quantity_sold,
                total_revenue=total_revenue,
                benchmark_revenue=benchmark_revenue,
                revenue_difference=revenue_difference,
                sale_date=sale_date,
                location=location,
                category=category,
                analysis=analysis,
                created_at=datetime.utcnow()
            )
            
            # Store performance metric
            await self._store_performance_metric(performance, db)
            
            logger.info("Performance tracked successfully", 
                       performance_id=str(performance.id),
                       performance_score=performance_score,
                       category=category.value)
            
            return performance
            
        except Exception as e:
            logger.error("Failed to track performance", error=str(e))
            raise
    
    async def get_performance_history(
        self,
        farmer_id: UUID,
        commodity: Optional[str] = None,
        days: int = 30,
        db=None
    ) -> Dict[str, Any]:
        """
        Get farmer's performance history with analytics
        
        Args:
            farmer_id: Farmer's unique identifier
            commodity: Optional commodity filter
            days: Number of days to look back
            db: Database connection
            
        Returns:
            Performance history and analytics
        """
        try:
            logger.info("Getting performance history", 
                       farmer_id=str(farmer_id),
                       commodity=commodity,
                       days=days)
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Fetch performance records
            performance_records = await self._fetch_performance_records(
                farmer_id, commodity, start_date, db
            )
            
            # Generate summary analytics
            summary = self._generate_performance_summary(performance_records)
            
            # Analyze trends
            trends = self._analyze_performance_trends(performance_records)
            
            # Generate recommendations
            recommendations = self._generate_performance_recommendations(
                performance_records, summary, trends
            )
            
            # Format records for response
            formatted_records = []
            for record in performance_records:
                formatted_records.append({
                    "id": str(record["id"]),
                    "commodity": record["commodity"],
                    "actual_price": record["actual_price"],
                    "benchmark_price": record.get("benchmark_price"),
                    "performance_score": record["performance_score"],
                    "vs_benchmark": record.get("vs_benchmark"),
                    "vs_floor": record.get("vs_floor"),
                    "total_revenue": record["total_revenue"],
                    "revenue_difference": record.get("revenue_difference"),
                    "sale_date": record["sale_date"],
                    "location": record.get("location"),
                    "category": record["category"]
                })
            
            result = {
                "summary": summary,
                "records": formatted_records,
                "trends": trends,
                "recommendations": recommendations
            }
            
            logger.info("Performance history retrieved successfully", 
                       farmer_id=str(farmer_id),
                       records_count=len(formatted_records))
            
            return result
            
        except Exception as e:
            logger.error("Failed to get performance history", error=str(e))
            raise
    
    def _calculate_performance_score(
        self,
        actual_price: float,
        benchmark: Optional[FarmerBenchmark],
        price_floor: Optional[PriceFloor]
    ) -> float:
        """
        Calculate overall performance score (0-100)
        
        Args:
            actual_price: Actual selling price
            benchmark: Relevant benchmark
            price_floor: Active price floor
            
        Returns:
            Performance score between 0 and 100
        """
        score = 50.0  # Base score
        
        # Score against benchmark
        if benchmark:
            benchmark_ratio = actual_price / benchmark.benchmark_price
            if benchmark_ratio >= 1.2:  # 20% above benchmark
                score += 30
            elif benchmark_ratio >= 1.1:  # 10% above benchmark
                score += 20
            elif benchmark_ratio >= 1.0:  # At or above benchmark
                score += 10
            elif benchmark_ratio >= 0.9:  # Within 10% of benchmark
                score += 5
            else:  # Below 90% of benchmark
                score -= 10
        
        # Score against price floor
        if price_floor:
            if actual_price >= price_floor.floor_price:
                score += 20  # Above floor
            else:
                score -= 30  # Below floor (major penalty)
        
        # Ensure score is within bounds
        return max(0.0, min(100.0, score))
    
    def _calculate_vs_benchmark(
        self,
        actual_price: float,
        benchmark: Optional[FarmerBenchmark]
    ) -> Optional[float]:
        """Calculate percentage difference vs benchmark"""
        if not benchmark:
            return None
        
        return ((actual_price - benchmark.benchmark_price) / benchmark.benchmark_price) * 100
    
    def _calculate_vs_floor(
        self,
        actual_price: float,
        price_floor: Optional[PriceFloor]
    ) -> Optional[float]:
        """Calculate percentage above price floor"""
        if not price_floor:
            return None
        
        return ((actual_price - price_floor.floor_price) / price_floor.floor_price) * 100
    
    def _determine_performance_category(self, performance_score: float) -> PerformanceCategory:
        """Determine performance category based on score"""
        if performance_score >= 90:
            return PerformanceCategory.EXCELLENT
        elif performance_score >= 75:
            return PerformanceCategory.GOOD
        elif performance_score >= 60:
            return PerformanceCategory.AVERAGE
        elif performance_score >= 40:
            return PerformanceCategory.BELOW_AVERAGE
        else:
            return PerformanceCategory.POOR
    
    def _generate_performance_analysis(
        self,
        actual_price: float,
        benchmark: Optional[FarmerBenchmark],
        price_floor: Optional[PriceFloor],
        vs_benchmark: Optional[float],
        vs_floor: Optional[float],
        location: Optional[str]
    ) -> Dict[str, Any]:
        """Generate detailed performance analysis"""
        analysis = {
            "price_analysis": {
                "actual_price": actual_price,
                "benchmark_comparison": None,
                "floor_comparison": None
            },
            "market_context": {
                "location": location,
                "timing_analysis": "good",  # Simplified
                "market_conditions": "favorable"  # Simplified
            },
            "insights": [],
            "areas_for_improvement": []
        }
        
        # Benchmark analysis
        if benchmark and vs_benchmark is not None:
            analysis["price_analysis"]["benchmark_comparison"] = {
                "benchmark_price": benchmark.benchmark_price,
                "difference_percentage": vs_benchmark,
                "performance": "above" if vs_benchmark > 0 else "below"
            }
            
            if vs_benchmark > 10:
                analysis["insights"].append("Excellent price achievement - significantly above benchmark")
            elif vs_benchmark > 0:
                analysis["insights"].append("Good price achievement - above benchmark")
            else:
                analysis["insights"].append("Price below benchmark - room for improvement")
                analysis["areas_for_improvement"].append("Price negotiation skills")
        
        # Floor analysis
        if price_floor and vs_floor is not None:
            analysis["price_analysis"]["floor_comparison"] = {
                "floor_price": price_floor.floor_price,
                "difference_percentage": vs_floor,
                "status": "above" if vs_floor > 0 else "below"
            }
            
            if vs_floor < 0:
                analysis["insights"].append("WARNING: Price below set floor - consider alternative markets")
                analysis["areas_for_improvement"].append("Market selection and timing")
        
        # Location insights
        if location:
            analysis["insights"].append(f"Sale location: {location}")
        
        return analysis
    
    def _generate_performance_summary(self, performance_records: List[Dict]) -> Dict[str, Any]:
        """Generate performance summary statistics"""
        if not performance_records:
            return {
                "total_sales": 0,
                "total_revenue": 0.0,
                "average_performance_score": 0.0,
                "best_performance": None,
                "worst_performance": None,
                "benchmark_adherence_rate": 0.0,
                "floor_violation_count": 0
            }
        
        scores = [r["performance_score"] for r in performance_records]
        revenues = [r["total_revenue"] for r in performance_records]
        
        # Count benchmark adherence
        benchmark_adherent = len([r for r in performance_records 
                                if r.get("vs_benchmark", 0) >= 0])
        benchmark_adherence_rate = benchmark_adherent / len(performance_records)
        
        # Count floor violations
        floor_violations = len([r for r in performance_records 
                              if r.get("vs_floor", 0) < 0])
        
        return {
            "total_sales": len(performance_records),
            "total_revenue": sum(revenues),
            "average_revenue_per_sale": statistics.mean(revenues),
            "average_performance_score": statistics.mean(scores),
            "best_performance": max(scores),
            "worst_performance": min(scores),
            "benchmark_adherence_rate": benchmark_adherence_rate,
            "floor_violation_count": floor_violations,
            "performance_distribution": {
                "excellent": len([s for s in scores if s >= 90]),
                "good": len([s for s in scores if 75 <= s < 90]),
                "average": len([s for s in scores if 60 <= s < 75]),
                "below_average": len([s for s in scores if 40 <= s < 60]),
                "poor": len([s for s in scores if s < 40])
            }
        }
    
    def _analyze_performance_trends(self, performance_records: List[Dict]) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        if len(performance_records) < 2:
            return {
                "trend_direction": "insufficient_data",
                "improvement_rate": 0.0,
                "consistency": "unknown",
                "seasonal_patterns": []
            }
        
        # Sort by date
        sorted_records = sorted(performance_records, key=lambda x: x["sale_date"])
        
        # Calculate trend
        scores = [r["performance_score"] for r in sorted_records]
        recent_scores = scores[-5:] if len(scores) >= 5 else scores
        early_scores = scores[:5] if len(scores) >= 5 else scores[:-len(recent_scores)]
        
        if early_scores and recent_scores:
            recent_avg = statistics.mean(recent_scores)
            early_avg = statistics.mean(early_scores)
            improvement_rate = (recent_avg - early_avg) / early_avg if early_avg > 0 else 0
        else:
            improvement_rate = 0.0
        
        # Determine trend direction
        if improvement_rate > 0.1:
            trend_direction = "improving"
        elif improvement_rate < -0.1:
            trend_direction = "declining"
        else:
            trend_direction = "stable"
        
        # Calculate consistency (coefficient of variation)
        if len(scores) > 1:
            cv = statistics.stdev(scores) / statistics.mean(scores)
            if cv < 0.1:
                consistency = "very_consistent"
            elif cv < 0.2:
                consistency = "consistent"
            elif cv < 0.3:
                consistency = "moderate"
            else:
                consistency = "inconsistent"
        else:
            consistency = "unknown"
        
        return {
            "trend_direction": trend_direction,
            "improvement_rate": improvement_rate,
            "consistency": consistency,
            "volatility": statistics.stdev(scores) if len(scores) > 1 else 0,
            "recent_performance": statistics.mean(recent_scores) if recent_scores else 0,
            "seasonal_patterns": self._detect_seasonal_patterns(sorted_records)
        }
    
    def _detect_seasonal_patterns(self, sorted_records: List[Dict]) -> List[str]:
        """Detect seasonal patterns in performance"""
        # Simplified seasonal pattern detection
        patterns = []
        
        # Group by month
        monthly_performance = {}
        for record in sorted_records:
            month = record["sale_date"].month
            if month not in monthly_performance:
                monthly_performance[month] = []
            monthly_performance[month].append(record["performance_score"])
        
        # Analyze monthly averages
        monthly_averages = {
            month: statistics.mean(scores) 
            for month, scores in monthly_performance.items()
        }
        
        if len(monthly_averages) >= 3:
            best_month = max(monthly_averages, key=monthly_averages.get)
            worst_month = min(monthly_averages, key=monthly_averages.get)
            
            month_names = {
                1: "January", 2: "February", 3: "March", 4: "April",
                5: "May", 6: "June", 7: "July", 8: "August",
                9: "September", 10: "October", 11: "November", 12: "December"
            }
            
            patterns.append(f"Best performance in {month_names.get(best_month, best_month)}")
            patterns.append(f"Lowest performance in {month_names.get(worst_month, worst_month)}")
        
        return patterns
    
    def _generate_performance_recommendations(
        self,
        performance_records: List[Dict],
        summary: Dict[str, Any],
        trends: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        # Benchmark adherence recommendations
        if summary["benchmark_adherence_rate"] < 0.7:
            recommendations.append({
                "type": "benchmark_adherence",
                "priority": "high",
                "title": "Improve Benchmark Performance",
                "description": f"Only {summary['benchmark_adherence_rate']:.1%} of sales meet benchmark. Focus on better market timing and negotiation.",
                "action_items": [
                    "Review market timing strategies",
                    "Improve negotiation skills",
                    "Consider alternative markets"
                ]
            })
        
        # Floor violation recommendations
        if summary["floor_violation_count"] > 0:
            recommendations.append({
                "type": "floor_violations",
                "priority": "high",
                "title": "Avoid Price Floor Violations",
                "description": f"{summary['floor_violation_count']} sales below price floor. Review floor settings and market selection.",
                "action_items": [
                    "Review price floor settings",
                    "Explore alternative markets",
                    "Improve market intelligence"
                ]
            })
        
        # Trend-based recommendations
        if trends["trend_direction"] == "declining":
            recommendations.append({
                "type": "performance_decline",
                "priority": "medium",
                "title": "Address Performance Decline",
                "description": "Performance trending downward. Analyze recent sales for improvement opportunities.",
                "action_items": [
                    "Analyze recent market conditions",
                    "Review selling strategies",
                    "Consider market diversification"
                ]
            })
        
        # Consistency recommendations
        if trends["consistency"] == "inconsistent":
            recommendations.append({
                "type": "consistency",
                "priority": "medium",
                "title": "Improve Consistency",
                "description": "Performance varies significantly. Develop more consistent selling strategies.",
                "action_items": [
                    "Standardize market research process",
                    "Develop consistent timing strategies",
                    "Build reliable buyer relationships"
                ]
            })
        
        return recommendations
    
    # Database simulation methods
    async def _get_relevant_benchmark(
        self, 
        farmer_id: UUID, 
        commodity: str, 
        db
    ) -> Optional[FarmerBenchmark]:
        """Get most relevant benchmark for commodity"""
        # Simulate database query
        await asyncio.sleep(0.01)
        
        # Return simulated benchmark
        return FarmerBenchmark(
            farmer_id=farmer_id,
            commodity=commodity.lower(),
            benchmark_price=2150.0,
            price_range={"min": 1900.0, "max": 2400.0, "avg": 2150.0, "median": 2100.0},
            confidence_score=0.85,
            data_points_count=25,
            analysis_period="30 days",
            created_at=datetime.utcnow() - timedelta(days=15)
        )
    
    async def _get_active_price_floor(
        self, 
        farmer_id: UUID, 
        commodity: str, 
        db
    ) -> Optional[PriceFloor]:
        """Get active price floor for commodity"""
        # Simulate database query
        await asyncio.sleep(0.01)
        
        # Return simulated price floor
        return PriceFloor(
            farmer_id=farmer_id,
            commodity=commodity.lower(),
            floor_price=2000.0,
            unit="per_quintal",
            reasoning="Based on production costs",
            created_at=datetime.utcnow() - timedelta(days=10),
            is_active=True
        )
    
    async def _store_performance_metric(self, performance: PerformanceMetric, db):
        """Store performance metric in database"""
        # Simulate database operation
        await asyncio.sleep(0.01)
        logger.debug("Stored performance metric", performance_id=str(performance.id))
    
    async def _fetch_performance_records(
        self, 
        farmer_id: UUID, 
        commodity: Optional[str], 
        start_date: datetime, 
        db
    ) -> List[Dict]:
        """Fetch performance records from database"""
        # Simulate database query
        await asyncio.sleep(0.01)
        
        # Return simulated performance records
        records = [
            {
                "id": "perf-1",
                "commodity": "wheat",
                "actual_price": 2200.0,
                "benchmark_price": 2150.0,
                "performance_score": 85.0,
                "vs_benchmark": 2.3,
                "vs_floor": 10.0,
                "total_revenue": 22000.0,
                "revenue_difference": 500.0,
                "sale_date": datetime.utcnow() - timedelta(days=5),
                "location": "local_mandi",
                "category": "good"
            },
            {
                "id": "perf-2",
                "commodity": "rice",
                "actual_price": 1850.0,
                "benchmark_price": 1950.0,
                "performance_score": 72.0,
                "vs_benchmark": -5.1,
                "vs_floor": 2.8,
                "total_revenue": 18500.0,
                "revenue_difference": -1000.0,
                "sale_date": datetime.utcnow() - timedelta(days=12),
                "location": "regional_market",
                "category": "average"
            },
            {
                "id": "perf-3",
                "commodity": "wheat",
                "actual_price": 2050.0,
                "benchmark_price": 2150.0,
                "performance_score": 78.0,
                "vs_benchmark": -4.7,
                "vs_floor": 2.5,
                "total_revenue": 20500.0,
                "revenue_difference": -1000.0,
                "sale_date": datetime.utcnow() - timedelta(days=20),
                "location": "local_mandi",
                "category": "good"
            }
        ]
        
        # Filter by commodity if specified
        if commodity:
            records = [r for r in records if r["commodity"] == commodity.lower()]
        
        return records