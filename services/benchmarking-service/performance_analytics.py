"""
Performance Analytics System for MANDI EAR™
Provides comprehensive performance analytics including income improvement calculations,
trend analysis, and comparative analytics dashboard
"""

import asyncio
import statistics
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID
import structlog
from models import PerformanceMetric, PerformanceCategory, FarmerBenchmark

logger = structlog.get_logger()

class PerformanceAnalytics:
    """
    Advanced performance analytics system that provides comprehensive insights
    into farmer performance, income improvements, and comparative analytics
    """
    
    def __init__(self):
        """Initialize the performance analytics system"""
        logger.info("PerformanceAnalytics initialized")
    
    async def calculate_income_improvement(
        self,
        farmer_id: UUID,
        commodity: Optional[str] = None,
        baseline_period_days: int = 90,
        comparison_period_days: int = 30,
        db=None
    ) -> Dict[str, Any]:
        """
        Calculate income improvement over time by comparing recent performance
        against historical baseline
        
        Args:
            farmer_id: Farmer's unique identifier
            commodity: Optional commodity filter
            baseline_period_days: Days to look back for baseline calculation
            comparison_period_days: Recent period for comparison
            db: Database connection
            
        Returns:
            Income improvement analysis with metrics and trends
        """
        try:
            logger.info("Calculating income improvement", 
                       farmer_id=str(farmer_id),
                       commodity=commodity,
                       baseline_days=baseline_period_days,
                       comparison_days=comparison_period_days)
            
            # Get baseline period data (older data)
            baseline_end = datetime.utcnow() - timedelta(days=comparison_period_days)
            baseline_start = baseline_end - timedelta(days=baseline_period_days)
            baseline_records = await self._fetch_performance_records_by_period(
                farmer_id, commodity, baseline_start, baseline_end, db
            )
            
            # Get comparison period data (recent data)
            comparison_start = datetime.utcnow() - timedelta(days=comparison_period_days)
            comparison_records = await self._fetch_performance_records_by_period(
                farmer_id, commodity, comparison_start, datetime.utcnow(), db
            )
            
            # Calculate baseline metrics
            baseline_metrics = self._calculate_period_metrics(baseline_records)
            
            # Calculate comparison metrics
            comparison_metrics = self._calculate_period_metrics(comparison_records)
            
            # Calculate improvement metrics
            improvement_analysis = self._calculate_improvement_metrics(
                baseline_metrics, comparison_metrics
            )
            
            # Generate income improvement insights
            insights = self._generate_income_improvement_insights(
                baseline_metrics, comparison_metrics, improvement_analysis
            )
            
            result = {
                "farmer_id": str(farmer_id),
                "commodity_filter": commodity,
                "analysis_period": {
                    "baseline_period": f"{baseline_period_days} days",
                    "comparison_period": f"{comparison_period_days} days",
                    "baseline_start": baseline_start.isoformat(),
                    "baseline_end": baseline_end.isoformat(),
                    "comparison_start": comparison_start.isoformat(),
                    "comparison_end": datetime.utcnow().isoformat()
                },
                "baseline_metrics": baseline_metrics,
                "comparison_metrics": comparison_metrics,
                "improvement_analysis": improvement_analysis,
                "insights": insights,
                "calculated_at": datetime.utcnow().isoformat()
            }
            
            logger.info("Income improvement calculated successfully", 
                       farmer_id=str(farmer_id),
                       improvement_percentage=improvement_analysis.get("revenue_improvement_percentage", 0))
            
            return result
            
        except Exception as e:
            logger.error("Failed to calculate income improvement", error=str(e))
            raise
    
    async def analyze_performance_trends(
        self,
        farmer_id: UUID,
        commodity: Optional[str] = None,
        analysis_period_days: int = 180,
        trend_window_days: int = 30,
        db=None
    ) -> Dict[str, Any]:
        """
        Analyze performance trends over time using rolling windows
        
        Args:
            farmer_id: Farmer's unique identifier
            commodity: Optional commodity filter
            analysis_period_days: Total period to analyze
            trend_window_days: Size of rolling window for trend analysis
            db: Database connection
            
        Returns:
            Comprehensive trend analysis with patterns and predictions
        """
        try:
            logger.info("Analyzing performance trends", 
                       farmer_id=str(farmer_id),
                       commodity=commodity,
                       analysis_days=analysis_period_days)
            
            # Get historical performance data
            start_date = datetime.utcnow() - timedelta(days=analysis_period_days)
            performance_records = await self._fetch_performance_records_by_period(
                farmer_id, commodity, start_date, datetime.utcnow(), db
            )
            
            if not performance_records:
                return self._empty_trend_analysis(farmer_id, commodity)
            
            # Sort records by date
            sorted_records = sorted(performance_records, key=lambda x: x["sale_date"])
            
            # Calculate rolling window trends
            rolling_trends = self._calculate_rolling_trends(sorted_records, trend_window_days)
            
            # Analyze seasonal patterns
            seasonal_patterns = self._analyze_seasonal_patterns(sorted_records)
            
            # Detect trend changes and inflection points
            trend_changes = self._detect_trend_changes(rolling_trends)
            
            # Calculate trend strength and direction
            overall_trend = self._calculate_overall_trend(sorted_records)
            
            # Generate trend predictions
            predictions = self._generate_trend_predictions(rolling_trends, overall_trend)
            
            # Identify performance drivers
            performance_drivers = self._identify_performance_drivers(sorted_records)
            
            result = {
                "farmer_id": str(farmer_id),
                "commodity_filter": commodity,
                "analysis_period": {
                    "total_days": analysis_period_days,
                    "trend_window_days": trend_window_days,
                    "start_date": start_date.isoformat(),
                    "end_date": datetime.utcnow().isoformat()
                },
                "data_summary": {
                    "total_records": len(sorted_records),
                    "date_range": {
                        "earliest": sorted_records[0]["sale_date"].isoformat() if sorted_records else None,
                        "latest": sorted_records[-1]["sale_date"].isoformat() if sorted_records else None
                    }
                },
                "overall_trend": overall_trend,
                "rolling_trends": rolling_trends,
                "seasonal_patterns": seasonal_patterns,
                "trend_changes": trend_changes,
                "predictions": predictions,
                "performance_drivers": performance_drivers,
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
            logger.info("Performance trends analyzed successfully", 
                       farmer_id=str(farmer_id),
                       trend_direction=overall_trend.get("direction", "unknown"))
            
            return result
            
        except Exception as e:
            logger.error("Failed to analyze performance trends", error=str(e))
            raise
    
    async def generate_comparative_analytics(
        self,
        farmer_id: UUID,
        commodity: Optional[str] = None,
        comparison_period_days: int = 90,
        db=None
    ) -> Dict[str, Any]:
        """
        Generate comparative analytics dashboard showing farmer performance
        against various benchmarks and peer comparisons
        
        Args:
            farmer_id: Farmer's unique identifier
            commodity: Optional commodity filter
            comparison_period_days: Period for comparison analysis
            db: Database connection
            
        Returns:
            Comprehensive comparative analytics dashboard
        """
        try:
            logger.info("Generating comparative analytics", 
                       farmer_id=str(farmer_id),
                       commodity=commodity,
                       comparison_days=comparison_period_days)
            
            # Get farmer's performance data
            start_date = datetime.utcnow() - timedelta(days=comparison_period_days)
            farmer_records = await self._fetch_performance_records_by_period(
                farmer_id, commodity, start_date, datetime.utcnow(), db
            )
            
            # Get regional benchmark data (simulated)
            regional_benchmarks = await self._get_regional_benchmarks(commodity, start_date, db)
            
            # Get peer performance data (simulated)
            peer_performance = await self._get_peer_performance_data(
                farmer_id, commodity, start_date, db
            )
            
            # Calculate farmer metrics
            farmer_metrics = self._calculate_period_metrics(farmer_records)
            
            # Generate comparative analysis
            vs_regional = self._compare_against_regional(farmer_metrics, regional_benchmarks)
            vs_peers = self._compare_against_peers(farmer_metrics, peer_performance)
            vs_historical = await self._compare_against_historical(
                farmer_id, commodity, farmer_metrics, db
            )
            
            # Calculate performance rankings
            rankings = self._calculate_performance_rankings(
                farmer_metrics, regional_benchmarks, peer_performance
            )
            
            # Generate improvement opportunities
            opportunities = self._identify_improvement_opportunities(
                farmer_metrics, regional_benchmarks, peer_performance
            )
            
            # Create performance scorecard
            scorecard = self._create_performance_scorecard(
                farmer_metrics, vs_regional, vs_peers, vs_historical
            )
            
            result = {
                "farmer_id": str(farmer_id),
                "commodity_filter": commodity,
                "analysis_period": {
                    "days": comparison_period_days,
                    "start_date": start_date.isoformat(),
                    "end_date": datetime.utcnow().isoformat()
                },
                "farmer_metrics": farmer_metrics,
                "comparative_analysis": {
                    "vs_regional_benchmarks": vs_regional,
                    "vs_peer_farmers": vs_peers,
                    "vs_historical_performance": vs_historical
                },
                "performance_rankings": rankings,
                "improvement_opportunities": opportunities,
                "performance_scorecard": scorecard,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            logger.info("Comparative analytics generated successfully", 
                       farmer_id=str(farmer_id),
                       overall_rank=rankings.get("overall_percentile", "unknown"))
            
            return result
            
        except Exception as e:
            logger.error("Failed to generate comparative analytics", error=str(e))
            raise
    
    def _calculate_period_metrics(self, records: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive metrics for a period"""
        if not records:
            return {
                "total_sales": 0,
                "total_revenue": 0.0,
                "average_price": 0.0,
                "average_performance_score": 0.0,
                "total_quantity": 0.0,
                "price_range": {"min": 0.0, "max": 0.0},
                "performance_distribution": {},
                "benchmark_adherence_rate": 0.0,
                "floor_violation_rate": 0.0
            }
        
        prices = [r["actual_price"] for r in records]
        revenues = [r["total_revenue"] for r in records]
        scores = [r["performance_score"] for r in records]
        quantities = [r.get("quantity_sold", 0) for r in records]
        
        # Calculate benchmark adherence
        benchmark_adherent = len([r for r in records if r.get("vs_benchmark", 0) >= 0])
        benchmark_adherence_rate = benchmark_adherent / len(records)
        
        # Calculate floor violations
        floor_violations = len([r for r in records if r.get("vs_floor", 0) < 0])
        floor_violation_rate = floor_violations / len(records)
        
        # Performance distribution
        performance_distribution = {
            "excellent": len([s for s in scores if s >= 90]) / len(scores),
            "good": len([s for s in scores if 75 <= s < 90]) / len(scores),
            "average": len([s for s in scores if 60 <= s < 75]) / len(scores),
            "below_average": len([s for s in scores if 40 <= s < 60]) / len(scores),
            "poor": len([s for s in scores if s < 40]) / len(scores)
        }
        
        return {
            "total_sales": len(records),
            "total_revenue": sum(revenues),
            "average_revenue_per_sale": statistics.mean(revenues),
            "average_price": statistics.mean(prices),
            "median_price": statistics.median(prices),
            "average_performance_score": statistics.mean(scores),
            "median_performance_score": statistics.median(scores),
            "total_quantity": sum(quantities),
            "average_quantity_per_sale": statistics.mean(quantities),
            "price_range": {
                "min": min(prices),
                "max": max(prices),
                "std_dev": statistics.stdev(prices) if len(prices) > 1 else 0
            },
            "performance_range": {
                "min": min(scores),
                "max": max(scores),
                "std_dev": statistics.stdev(scores) if len(scores) > 1 else 0
            },
            "performance_distribution": performance_distribution,
            "benchmark_adherence_rate": benchmark_adherence_rate,
            "floor_violation_rate": floor_violation_rate,
            "consistency_score": 1 - (statistics.stdev(scores) / 100) if len(scores) > 1 else 1.0
        }
    
    def _calculate_improvement_metrics(
        self, 
        baseline_metrics: Dict[str, Any], 
        comparison_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate improvement metrics between two periods"""
        
        # Revenue improvement
        baseline_revenue = baseline_metrics.get("total_revenue", 0)
        comparison_revenue = comparison_metrics.get("total_revenue", 0)
        revenue_improvement = comparison_revenue - baseline_revenue
        revenue_improvement_percentage = (
            (revenue_improvement / baseline_revenue * 100) if baseline_revenue > 0 else 0
        )
        
        # Performance score improvement
        baseline_score = baseline_metrics.get("average_performance_score", 0)
        comparison_score = comparison_metrics.get("average_performance_score", 0)
        score_improvement = comparison_score - baseline_score
        score_improvement_percentage = (
            (score_improvement / baseline_score * 100) if baseline_score > 0 else 0
        )
        
        # Price improvement
        baseline_price = baseline_metrics.get("average_price", 0)
        comparison_price = comparison_metrics.get("average_price", 0)
        price_improvement = comparison_price - baseline_price
        price_improvement_percentage = (
            (price_improvement / baseline_price * 100) if baseline_price > 0 else 0
        )
        
        # Efficiency improvement (revenue per sale)
        baseline_efficiency = baseline_metrics.get("average_revenue_per_sale", 0)
        comparison_efficiency = comparison_metrics.get("average_revenue_per_sale", 0)
        efficiency_improvement = comparison_efficiency - baseline_efficiency
        efficiency_improvement_percentage = (
            (efficiency_improvement / baseline_efficiency * 100) if baseline_efficiency > 0 else 0
        )
        
        # Consistency improvement
        baseline_consistency = baseline_metrics.get("consistency_score", 0)
        comparison_consistency = comparison_metrics.get("consistency_score", 0)
        consistency_improvement = comparison_consistency - baseline_consistency
        
        return {
            "revenue_improvement": {
                "absolute": revenue_improvement,
                "percentage": revenue_improvement_percentage,
                "trend": "improving" if revenue_improvement > 0 else "declining" if revenue_improvement < 0 else "stable"
            },
            "performance_score_improvement": {
                "absolute": score_improvement,
                "percentage": score_improvement_percentage,
                "trend": "improving" if score_improvement > 0 else "declining" if score_improvement < 0 else "stable"
            },
            "price_improvement": {
                "absolute": price_improvement,
                "percentage": price_improvement_percentage,
                "trend": "improving" if price_improvement > 0 else "declining" if price_improvement < 0 else "stable"
            },
            "efficiency_improvement": {
                "absolute": efficiency_improvement,
                "percentage": efficiency_improvement_percentage,
                "trend": "improving" if efficiency_improvement > 0 else "declining" if efficiency_improvement < 0 else "stable"
            },
            "consistency_improvement": {
                "absolute": consistency_improvement,
                "trend": "improving" if consistency_improvement > 0 else "declining" if consistency_improvement < 0 else "stable"
            },
            "overall_improvement_score": self._calculate_overall_improvement_score(
                revenue_improvement_percentage,
                score_improvement_percentage,
                price_improvement_percentage,
                efficiency_improvement_percentage
            )
        }
    
    def _calculate_overall_improvement_score(
        self, 
        revenue_pct: float, 
        score_pct: float, 
        price_pct: float, 
        efficiency_pct: float
    ) -> float:
        """Calculate weighted overall improvement score"""
        # Weights: revenue (40%), performance score (30%), price (20%), efficiency (10%)
        weights = [0.4, 0.3, 0.2, 0.1]
        improvements = [revenue_pct, score_pct, price_pct, efficiency_pct]
        
        weighted_score = sum(w * imp for w, imp in zip(weights, improvements))
        
        # Normalize to 0-100 scale
        return max(-100, min(100, weighted_score))
    
    def _generate_income_improvement_insights(
        self,
        baseline_metrics: Dict[str, Any],
        comparison_metrics: Dict[str, Any],
        improvement_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate insights about income improvement"""
        insights = []
        
        revenue_improvement = improvement_analysis["revenue_improvement"]
        score_improvement = improvement_analysis["performance_score_improvement"]
        
        # Revenue insights
        if revenue_improvement["percentage"] > 10:
            insights.append({
                "type": "positive",
                "category": "revenue",
                "title": "Significant Revenue Growth",
                "description": f"Revenue increased by {revenue_improvement['percentage']:.1f}% ({revenue_improvement['absolute']:.0f} units)",
                "impact": "high",
                "confidence": 0.9
            })
        elif revenue_improvement["percentage"] < -10:
            insights.append({
                "type": "negative",
                "category": "revenue",
                "title": "Revenue Decline",
                "description": f"Revenue decreased by {abs(revenue_improvement['percentage']):.1f}% ({abs(revenue_improvement['absolute']):.0f} units)",
                "impact": "high",
                "confidence": 0.9
            })
        
        # Performance insights
        if score_improvement["percentage"] > 5:
            insights.append({
                "type": "positive",
                "category": "performance",
                "title": "Performance Improvement",
                "description": f"Performance score improved by {score_improvement['percentage']:.1f}%",
                "impact": "medium",
                "confidence": 0.8
            })
        
        # Consistency insights
        baseline_consistency = baseline_metrics.get("consistency_score", 0)
        comparison_consistency = comparison_metrics.get("consistency_score", 0)
        
        if comparison_consistency > baseline_consistency + 0.1:
            insights.append({
                "type": "positive",
                "category": "consistency",
                "title": "Improved Consistency",
                "description": "Performance has become more consistent over time",
                "impact": "medium",
                "confidence": 0.7
            })
        
        return insights
    
    def _calculate_rolling_trends(self, sorted_records: List[Dict], window_days: int) -> List[Dict[str, Any]]:
        """Calculate rolling window trends"""
        if len(sorted_records) < 2:
            return []
        
        rolling_trends = []
        
        # Group records by time windows
        current_date = sorted_records[0]["sale_date"]
        end_date = sorted_records[-1]["sale_date"]
        
        while current_date <= end_date:
            window_end = current_date + timedelta(days=window_days)
            window_records = [
                r for r in sorted_records 
                if current_date <= r["sale_date"] < window_end
            ]
            
            if window_records:
                window_metrics = self._calculate_period_metrics(window_records)
                rolling_trends.append({
                    "period_start": current_date.isoformat(),
                    "period_end": window_end.isoformat(),
                    "metrics": window_metrics,
                    "record_count": len(window_records)
                })
            
            current_date += timedelta(days=window_days // 2)  # 50% overlap
        
        return rolling_trends
    
    def _analyze_seasonal_patterns(self, sorted_records: List[Dict]) -> Dict[str, Any]:
        """Analyze seasonal patterns in performance"""
        if len(sorted_records) < 12:  # Need at least some data
            return {"insufficient_data": True}
        
        # Group by month
        monthly_data = {}
        for record in sorted_records:
            month = record["sale_date"].month
            if month not in monthly_data:
                monthly_data[month] = []
            monthly_data[month].append(record)
        
        # Calculate monthly averages
        monthly_patterns = {}
        for month, records in monthly_data.items():
            metrics = self._calculate_period_metrics(records)
            monthly_patterns[month] = {
                "month_name": [
                    "January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"
                ][month - 1],
                "average_price": metrics["average_price"],
                "average_performance": metrics["average_performance_score"],
                "total_sales": metrics["total_sales"],
                "total_revenue": metrics["total_revenue"]
            }
        
        # Identify best and worst months
        if monthly_patterns:
            best_month = max(monthly_patterns.keys(), 
                           key=lambda m: monthly_patterns[m]["average_performance"])
            worst_month = min(monthly_patterns.keys(), 
                            key=lambda m: monthly_patterns[m]["average_performance"])
            
            return {
                "monthly_patterns": monthly_patterns,
                "best_performing_month": {
                    "month": best_month,
                    "name": monthly_patterns[best_month]["month_name"],
                    "performance": monthly_patterns[best_month]["average_performance"]
                },
                "worst_performing_month": {
                    "month": worst_month,
                    "name": monthly_patterns[worst_month]["month_name"],
                    "performance": monthly_patterns[worst_month]["average_performance"]
                },
                "seasonal_volatility": self._calculate_seasonal_volatility(monthly_patterns)
            }
        
        return {"insufficient_data": True}
    
    def _calculate_seasonal_volatility(self, monthly_patterns: Dict) -> float:
        """Calculate seasonal volatility in performance"""
        performances = [data["average_performance"] for data in monthly_patterns.values()]
        if len(performances) > 1:
            return statistics.stdev(performances)
        return 0.0
    
    def _detect_trend_changes(self, rolling_trends: List[Dict]) -> List[Dict[str, Any]]:
        """Detect significant trend changes and inflection points"""
        if len(rolling_trends) < 3:
            return []
        
        trend_changes = []
        
        # Look for inflection points in performance scores
        scores = [trend["metrics"]["average_performance_score"] for trend in rolling_trends]
        
        for i in range(1, len(scores) - 1):
            prev_score = scores[i - 1]
            curr_score = scores[i]
            next_score = scores[i + 1]
            
            # Detect local maxima/minima
            if curr_score > prev_score and curr_score > next_score:
                trend_changes.append({
                    "type": "peak",
                    "period": rolling_trends[i]["period_start"],
                    "performance_score": curr_score,
                    "description": f"Performance peak at {curr_score:.1f}"
                })
            elif curr_score < prev_score and curr_score < next_score:
                trend_changes.append({
                    "type": "trough",
                    "period": rolling_trends[i]["period_start"],
                    "performance_score": curr_score,
                    "description": f"Performance trough at {curr_score:.1f}"
                })
        
        return trend_changes
    
    def _calculate_overall_trend(self, sorted_records: List[Dict]) -> Dict[str, Any]:
        """Calculate overall trend direction and strength"""
        if len(sorted_records) < 2:
            return {"direction": "insufficient_data", "strength": 0.0}
        
        # Use first and last quartile for trend calculation
        n = len(sorted_records)
        first_quartile = sorted_records[:n//4] if n >= 4 else sorted_records[:1]
        last_quartile = sorted_records[-n//4:] if n >= 4 else sorted_records[-1:]
        
        first_avg = statistics.mean([r["performance_score"] for r in first_quartile])
        last_avg = statistics.mean([r["performance_score"] for r in last_quartile])
        
        trend_change = last_avg - first_avg
        trend_percentage = (trend_change / first_avg * 100) if first_avg > 0 else 0
        
        # Determine direction
        if trend_percentage > 5:
            direction = "strongly_improving"
        elif trend_percentage > 1:
            direction = "improving"
        elif trend_percentage > -1:
            direction = "stable"
        elif trend_percentage > -5:
            direction = "declining"
        else:
            direction = "strongly_declining"
        
        # Calculate trend strength (R-squared approximation)
        scores = [r["performance_score"] for r in sorted_records]
        x_values = list(range(len(scores)))
        
        # Simple linear correlation
        if len(scores) > 1:
            correlation = abs(statistics.correlation(x_values, scores)) if len(set(scores)) > 1 else 0
        else:
            correlation = 0
        
        return {
            "direction": direction,
            "strength": correlation,
            "change_percentage": trend_percentage,
            "absolute_change": trend_change,
            "confidence": min(0.9, correlation + 0.1)  # Add base confidence
        }
    
    def _generate_trend_predictions(
        self, 
        rolling_trends: List[Dict], 
        overall_trend: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate trend predictions based on historical data"""
        if not rolling_trends or overall_trend["direction"] == "insufficient_data":
            return {"prediction_available": False}
        
        # Simple trend extrapolation
        recent_trends = rolling_trends[-3:] if len(rolling_trends) >= 3 else rolling_trends
        recent_scores = [trend["metrics"]["average_performance_score"] for trend in recent_trends]
        
        if len(recent_scores) >= 2:
            trend_slope = (recent_scores[-1] - recent_scores[0]) / len(recent_scores)
            
            # Predict next period performance
            predicted_score = recent_scores[-1] + trend_slope
            predicted_score = max(0, min(100, predicted_score))  # Clamp to valid range
            
            # Confidence based on trend consistency
            confidence = overall_trend.get("confidence", 0.5)
            
            return {
                "prediction_available": True,
                "predicted_performance_score": predicted_score,
                "trend_direction": overall_trend["direction"],
                "confidence": confidence,
                "prediction_horizon": "next_period",
                "factors": [
                    f"Based on {overall_trend['direction']} trend",
                    f"Recent performance: {recent_scores[-1]:.1f}",
                    f"Trend strength: {overall_trend['strength']:.2f}"
                ]
            }
        
        return {"prediction_available": False}
    
    def _identify_performance_drivers(self, sorted_records: List[Dict]) -> List[Dict[str, Any]]:
        """Identify key factors driving performance"""
        drivers = []
        
        if not sorted_records:
            return drivers
        
        # Analyze location impact
        location_performance = {}
        for record in sorted_records:
            location = record.get("location", "unknown")
            if location not in location_performance:
                location_performance[location] = []
            location_performance[location].append(record["performance_score"])
        
        if len(location_performance) > 1:
            location_averages = {
                loc: statistics.mean(scores) 
                for loc, scores in location_performance.items()
            }
            best_location = max(location_averages, key=location_averages.get)
            worst_location = min(location_averages, key=location_averages.get)
            
            if location_averages[best_location] - location_averages[worst_location] > 10:
                drivers.append({
                    "factor": "location",
                    "impact": "high",
                    "description": f"Location significantly affects performance. {best_location} performs {location_averages[best_location] - location_averages[worst_location]:.1f} points better than {worst_location}",
                    "recommendation": f"Focus sales on {best_location} market"
                })
        
        # Analyze timing patterns
        weekday_performance = {}
        for record in sorted_records:
            weekday = record["sale_date"].weekday()
            if weekday not in weekday_performance:
                weekday_performance[weekday] = []
            weekday_performance[weekday].append(record["performance_score"])
        
        if len(weekday_performance) > 1:
            weekday_averages = {
                day: statistics.mean(scores) 
                for day, scores in weekday_performance.items()
            }
            best_day = max(weekday_averages, key=weekday_averages.get)
            
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            
            drivers.append({
                "factor": "timing",
                "impact": "medium",
                "description": f"Best performance on {day_names[best_day]} with average score {weekday_averages[best_day]:.1f}",
                "recommendation": f"Consider scheduling more sales on {day_names[best_day]}"
            })
        
        return drivers
    
    def _empty_trend_analysis(self, farmer_id: UUID, commodity: Optional[str]) -> Dict[str, Any]:
        """Return empty trend analysis when no data is available"""
        return {
            "farmer_id": str(farmer_id),
            "commodity_filter": commodity,
            "data_summary": {"total_records": 0},
            "overall_trend": {"direction": "insufficient_data", "strength": 0.0},
            "rolling_trends": [],
            "seasonal_patterns": {"insufficient_data": True},
            "trend_changes": [],
            "predictions": {"prediction_available": False},
            "performance_drivers": [],
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    # Comparative analytics helper methods
    def _compare_against_regional(
        self, 
        farmer_metrics: Dict[str, Any], 
        regional_benchmarks: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare farmer performance against regional benchmarks"""
        regional_avg_price = regional_benchmarks.get("average_price", 0)
        regional_avg_performance = regional_benchmarks.get("average_performance_score", 0)
        
        farmer_avg_price = farmer_metrics.get("average_price", 0)
        farmer_avg_performance = farmer_metrics.get("average_performance_score", 0)
        
        price_vs_regional = (
            ((farmer_avg_price - regional_avg_price) / regional_avg_price * 100) 
            if regional_avg_price > 0 else 0
        )
        
        performance_vs_regional = (
            ((farmer_avg_performance - regional_avg_performance) / regional_avg_performance * 100) 
            if regional_avg_performance > 0 else 0
        )
        
        return {
            "price_comparison": {
                "farmer_average": farmer_avg_price,
                "regional_average": regional_avg_price,
                "difference_percentage": price_vs_regional,
                "status": "above" if price_vs_regional > 0 else "below" if price_vs_regional < 0 else "equal"
            },
            "performance_comparison": {
                "farmer_average": farmer_avg_performance,
                "regional_average": regional_avg_performance,
                "difference_percentage": performance_vs_regional,
                "status": "above" if performance_vs_regional > 0 else "below" if performance_vs_regional < 0 else "equal"
            }
        }
    
    def _compare_against_peers(
        self, 
        farmer_metrics: Dict[str, Any], 
        peer_performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare farmer performance against peer farmers"""
        peer_avg_price = peer_performance.get("average_price", 0)
        peer_avg_performance = peer_performance.get("average_performance_score", 0)
        
        farmer_avg_price = farmer_metrics.get("average_price", 0)
        farmer_avg_performance = farmer_metrics.get("average_performance_score", 0)
        
        price_vs_peers = (
            ((farmer_avg_price - peer_avg_price) / peer_avg_price * 100) 
            if peer_avg_price > 0 else 0
        )
        
        performance_vs_peers = (
            ((farmer_avg_performance - peer_avg_performance) / peer_avg_performance * 100) 
            if peer_avg_performance > 0 else 0
        )
        
        return {
            "price_comparison": {
                "farmer_average": farmer_avg_price,
                "peer_average": peer_avg_price,
                "difference_percentage": price_vs_peers,
                "status": "above" if price_vs_peers > 0 else "below" if price_vs_peers < 0 else "equal"
            },
            "performance_comparison": {
                "farmer_average": farmer_avg_performance,
                "peer_average": peer_avg_performance,
                "difference_percentage": performance_vs_peers,
                "status": "above" if performance_vs_peers > 0 else "below" if performance_vs_peers < 0 else "equal"
            },
            "peer_group_size": peer_performance.get("peer_count", 0)
        }
    
    async def _compare_against_historical(
        self, 
        farmer_id: UUID, 
        commodity: Optional[str], 
        current_metrics: Dict[str, Any], 
        db
    ) -> Dict[str, Any]:
        """Compare current performance against farmer's historical performance"""
        # Get historical data (6 months ago)
        historical_start = datetime.utcnow() - timedelta(days=270)
        historical_end = datetime.utcnow() - timedelta(days=180)
        
        historical_records = await self._fetch_performance_records_by_period(
            farmer_id, commodity, historical_start, historical_end, db
        )
        
        if not historical_records:
            return {"comparison_available": False, "reason": "insufficient_historical_data"}
        
        historical_metrics = self._calculate_period_metrics(historical_records)
        
        current_avg_price = current_metrics.get("average_price", 0)
        historical_avg_price = historical_metrics.get("average_price", 0)
        
        current_avg_performance = current_metrics.get("average_performance_score", 0)
        historical_avg_performance = historical_metrics.get("average_performance_score", 0)
        
        price_improvement = (
            ((current_avg_price - historical_avg_price) / historical_avg_price * 100) 
            if historical_avg_price > 0 else 0
        )
        
        performance_improvement = (
            ((current_avg_performance - historical_avg_performance) / historical_avg_performance * 100) 
            if historical_avg_performance > 0 else 0
        )
        
        return {
            "comparison_available": True,
            "price_comparison": {
                "current_average": current_avg_price,
                "historical_average": historical_avg_price,
                "improvement_percentage": price_improvement,
                "trend": "improving" if price_improvement > 0 else "declining" if price_improvement < 0 else "stable"
            },
            "performance_comparison": {
                "current_average": current_avg_performance,
                "historical_average": historical_avg_performance,
                "improvement_percentage": performance_improvement,
                "trend": "improving" if performance_improvement > 0 else "declining" if performance_improvement < 0 else "stable"
            },
            "historical_period": {
                "start": historical_start.isoformat(),
                "end": historical_end.isoformat(),
                "record_count": len(historical_records)
            }
        }
    
    def _calculate_performance_rankings(
        self, 
        farmer_metrics: Dict[str, Any], 
        regional_benchmarks: Dict[str, Any], 
        peer_performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate performance rankings and percentiles"""
        farmer_performance = farmer_metrics.get("average_performance_score", 0)
        farmer_price = farmer_metrics.get("average_price", 0)
        
        # Simulate percentile calculations (in real implementation, would query database)
        performance_percentile = min(95, max(5, 50 + (farmer_performance - 70) * 2))
        price_percentile = min(95, max(5, 50 + (farmer_price - 2000) / 20))
        
        overall_percentile = (performance_percentile + price_percentile) / 2
        
        return {
            "performance_percentile": performance_percentile,
            "price_percentile": price_percentile,
            "overall_percentile": overall_percentile,
            "ranking_category": self._get_ranking_category(overall_percentile),
            "comparison_group": "regional_farmers",
            "total_farmers_in_comparison": peer_performance.get("peer_count", 100)
        }
    
    def _get_ranking_category(self, percentile: float) -> str:
        """Get ranking category based on percentile"""
        if percentile >= 90:
            return "top_10_percent"
        elif percentile >= 75:
            return "top_25_percent"
        elif percentile >= 50:
            return "above_average"
        elif percentile >= 25:
            return "below_average"
        else:
            return "bottom_25_percent"
    
    def _identify_improvement_opportunities(
        self, 
        farmer_metrics: Dict[str, Any], 
        regional_benchmarks: Dict[str, Any], 
        peer_performance: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify specific improvement opportunities"""
        opportunities = []
        
        farmer_performance = farmer_metrics.get("average_performance_score", 0)
        regional_performance = regional_benchmarks.get("average_performance_score", 0)
        peer_performance_avg = peer_performance.get("average_performance_score", 0)
        
        # Performance gap opportunities
        if farmer_performance < regional_performance - 5:
            gap = regional_performance - farmer_performance
            opportunities.append({
                "type": "performance_gap",
                "priority": "high",
                "title": "Close Regional Performance Gap",
                "description": f"Performance is {gap:.1f} points below regional average",
                "potential_impact": f"Could improve performance by {gap:.1f} points",
                "action_items": [
                    "Analyze top-performing regional farmers",
                    "Improve market timing strategies",
                    "Enhance negotiation skills"
                ]
            })
        
        # Price optimization opportunities
        farmer_price = farmer_metrics.get("average_price", 0)
        regional_price = regional_benchmarks.get("average_price", 0)
        
        if farmer_price < regional_price - 50:  # 50 unit threshold
            price_gap = regional_price - farmer_price
            opportunities.append({
                "type": "price_optimization",
                "priority": "high",
                "title": "Price Optimization Opportunity",
                "description": f"Average price is {price_gap:.0f} units below regional average",
                "potential_impact": f"Could increase revenue by {price_gap * farmer_metrics.get('average_quantity_per_sale', 10):.0f} units per sale",
                "action_items": [
                    "Explore higher-value markets",
                    "Improve product quality",
                    "Better market timing"
                ]
            })
        
        # Consistency opportunities
        consistency_score = farmer_metrics.get("consistency_score", 0)
        if consistency_score < 0.8:
            opportunities.append({
                "type": "consistency",
                "priority": "medium",
                "title": "Improve Performance Consistency",
                "description": f"Performance consistency score is {consistency_score:.2f}",
                "potential_impact": "More predictable income and better planning",
                "action_items": [
                    "Standardize selling processes",
                    "Develop consistent market research routine",
                    "Build reliable buyer relationships"
                ]
            })
        
        return opportunities
    
    def _create_performance_scorecard(
        self, 
        farmer_metrics: Dict[str, Any], 
        vs_regional: Dict[str, Any], 
        vs_peers: Dict[str, Any], 
        vs_historical: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create comprehensive performance scorecard"""
        
        # Calculate individual scores (0-100)
        price_score = min(100, max(0, farmer_metrics.get("average_price", 0) / 25))  # Normalize to 100
        performance_score = farmer_metrics.get("average_performance_score", 0)
        consistency_score = farmer_metrics.get("consistency_score", 0) * 100
        
        # Regional comparison score
        regional_comparison_score = 50  # Base score
        if vs_regional.get("performance_comparison", {}).get("difference_percentage", 0) > 0:
            regional_comparison_score += min(25, vs_regional["performance_comparison"]["difference_percentage"])
        else:
            regional_comparison_score += max(-25, vs_regional["performance_comparison"]["difference_percentage"])
        
        # Historical improvement score
        historical_improvement_score = 50  # Base score
        if vs_historical.get("comparison_available", False):
            improvement_pct = vs_historical.get("performance_comparison", {}).get("improvement_percentage", 0)
            historical_improvement_score += min(25, max(-25, improvement_pct))
        
        # Overall scorecard score
        overall_score = statistics.mean([
            price_score, performance_score, consistency_score, 
            regional_comparison_score, historical_improvement_score
        ])
        
        return {
            "overall_score": overall_score,
            "grade": self._get_performance_grade(overall_score),
            "component_scores": {
                "price_performance": price_score,
                "selling_performance": performance_score,
                "consistency": consistency_score,
                "regional_comparison": regional_comparison_score,
                "historical_improvement": historical_improvement_score
            },
            "strengths": self._identify_strengths(farmer_metrics, vs_regional, vs_peers),
            "areas_for_improvement": self._identify_improvement_areas(farmer_metrics, vs_regional, vs_peers),
            "next_steps": self._generate_next_steps(overall_score, farmer_metrics)
        }
    
    def _get_performance_grade(self, score: float) -> str:
        """Get letter grade based on overall score"""
        if score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "A-"
        elif score >= 75:
            return "B+"
        elif score >= 70:
            return "B"
        elif score >= 65:
            return "B-"
        elif score >= 60:
            return "C+"
        elif score >= 55:
            return "C"
        elif score >= 50:
            return "C-"
        else:
            return "D"
    
    def _identify_strengths(
        self, 
        farmer_metrics: Dict[str, Any], 
        vs_regional: Dict[str, Any], 
        vs_peers: Dict[str, Any]
    ) -> List[str]:
        """Identify farmer's key strengths"""
        strengths = []
        
        if farmer_metrics.get("average_performance_score", 0) >= 80:
            strengths.append("Consistently high performance scores")
        
        if farmer_metrics.get("consistency_score", 0) >= 0.8:
            strengths.append("Consistent performance across sales")
        
        if vs_regional.get("price_comparison", {}).get("difference_percentage", 0) > 5:
            strengths.append("Above-average pricing compared to region")
        
        if vs_peers.get("performance_comparison", {}).get("difference_percentage", 0) > 5:
            strengths.append("Outperforming peer farmers")
        
        if farmer_metrics.get("benchmark_adherence_rate", 0) >= 0.8:
            strengths.append("Strong benchmark adherence")
        
        return strengths
    
    def _identify_improvement_areas(
        self, 
        farmer_metrics: Dict[str, Any], 
        vs_regional: Dict[str, Any], 
        vs_peers: Dict[str, Any]
    ) -> List[str]:
        """Identify areas needing improvement"""
        areas = []
        
        if farmer_metrics.get("average_performance_score", 0) < 70:
            areas.append("Overall performance scores need improvement")
        
        if farmer_metrics.get("consistency_score", 0) < 0.7:
            areas.append("Performance consistency needs work")
        
        if vs_regional.get("price_comparison", {}).get("difference_percentage", 0) < -5:
            areas.append("Pricing below regional average")
        
        if farmer_metrics.get("floor_violation_rate", 0) > 0.1:
            areas.append("Too many sales below price floor")
        
        if farmer_metrics.get("benchmark_adherence_rate", 0) < 0.7:
            areas.append("Benchmark adherence needs improvement")
        
        return areas
    
    def _generate_next_steps(self, overall_score: float, farmer_metrics: Dict[str, Any]) -> List[str]:
        """Generate actionable next steps"""
        next_steps = []
        
        if overall_score < 70:
            next_steps.append("Focus on improving overall performance through better market research")
            next_steps.append("Consider working with agricultural extension services")
        
        if farmer_metrics.get("consistency_score", 0) < 0.7:
            next_steps.append("Develop standardized processes for market evaluation and timing")
        
        if farmer_metrics.get("floor_violation_rate", 0) > 0.1:
            next_steps.append("Review and adjust price floor settings")
            next_steps.append("Explore alternative markets when prices are low")
        
        next_steps.append("Continue monitoring performance trends monthly")
        next_steps.append("Set specific improvement targets for next quarter")
        
        return next_steps
    
    # Database simulation methods
    async def _fetch_performance_records_by_period(
        self, 
        farmer_id: UUID, 
        commodity: Optional[str], 
        start_date: datetime, 
        end_date: datetime, 
        db
    ) -> List[Dict]:
        """Fetch performance records for a specific time period"""
        # Simulate database query with delay
        await asyncio.sleep(0.01)
        
        # Generate simulated performance records
        records = []
        current_date = start_date
        
        while current_date < end_date:
            # Simulate some records (not every day)
            if current_date.weekday() < 5 and current_date.day % 3 == 0:  # Some business days
                # Simulate performance record
                base_price = 2000 + (current_date.month * 50)  # Seasonal variation
                price_variation = (hash(str(current_date)) % 400) - 200  # Random variation
                actual_price = base_price + price_variation
                
                performance_score = max(40, min(95, 75 + (hash(str(current_date)) % 30) - 15))
                
                records.append({
                    "id": f"perf-{current_date.strftime('%Y%m%d')}",
                    "commodity": commodity.lower() if commodity else "wheat",
                    "actual_price": actual_price,
                    "benchmark_price": base_price,
                    "performance_score": performance_score,
                    "vs_benchmark": ((actual_price - base_price) / base_price * 100),
                    "vs_floor": max(0, ((actual_price - 1800) / 1800 * 100)),
                    "total_revenue": actual_price * 10,  # Assume 10 units
                    "revenue_difference": (actual_price - base_price) * 10,
                    "quantity_sold": 10,
                    "sale_date": current_date,
                    "location": "local_mandi" if current_date.day % 2 == 0 else "regional_market",
                    "category": "good" if performance_score >= 75 else "average"
                })
            
            current_date += timedelta(days=1)
        
        # Filter by commodity if specified
        if commodity:
            records = [r for r in records if r["commodity"] == commodity.lower()]
        
        return records
    
    async def _get_regional_benchmarks(
        self, 
        commodity: Optional[str], 
        start_date: datetime, 
        db
    ) -> Dict[str, Any]:
        """Get regional benchmark data"""
        await asyncio.sleep(0.01)
        
        return {
            "average_price": 2100.0,
            "average_performance_score": 78.5,
            "total_farmers": 150,
            "region": "state_average",
            "commodity": commodity or "all"
        }
    
    async def _get_peer_performance_data(
        self, 
        farmer_id: UUID, 
        commodity: Optional[str], 
        start_date: datetime, 
        db
    ) -> Dict[str, Any]:
        """Get peer farmer performance data"""
        await asyncio.sleep(0.01)
        
        return {
            "average_price": 2050.0,
            "average_performance_score": 76.2,
            "peer_count": 25,
            "similarity_criteria": "same_region_similar_farm_size",
            "commodity": commodity or "all"
        }