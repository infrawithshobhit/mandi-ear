"""
Property-Based Tests for Performance Analytics System
Tests the accuracy of income improvement calculations and analytics
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Dict, Any, List
import statistics

# Import the performance analytics system
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services', 'benchmarking-service'))

from performance_analytics import PerformanceAnalytics

class TestPerformanceAnalyticsAccuracy:
    """
    **Feature: mandi-ear, Property 19: Performance Analytics Accuracy**
    
    Tests that the performance analytics system correctly calculates income improvement 
    metrics over time for any farmer's historical data.
    """
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analytics = PerformanceAnalytics()
    
    @given(
        farmer_id=st.uuids(),
        commodity=st.one_of(st.none(), st.sampled_from(["wheat", "rice", "corn", "barley"])),
        baseline_period_days=st.integers(min_value=30, max_value=180),
        comparison_period_days=st.integers(min_value=7, max_value=60)
    )
    @settings(max_examples=50, deadline=10000)
    def test_income_improvement_calculation_accuracy(
        self, farmer_id, commodity, baseline_period_days, comparison_period_days
    ):
        """
        **Validates: Requirements 8.5**
        
        For any farmer's historical data, income improvement calculations should be 
        mathematically accurate and consistent.
        """
        async def run_test():
            # Assume reasonable period constraints
            assume(baseline_period_days > comparison_period_days)
            assume(baseline_period_days >= 30)
            assume(comparison_period_days >= 7)
            
            # Calculate income improvement
            result = await self.analytics.calculate_income_improvement(
                farmer_id=farmer_id,
                commodity=commodity,
                baseline_period_days=baseline_period_days,
                comparison_period_days=comparison_period_days,
                db=None  # Using simulated data
            )
            
            # Verify result structure
            assert isinstance(result, dict), "Result should be a dictionary"
            assert "farmer_id" in result, "Result should contain farmer_id"
            assert "improvement_analysis" in result, "Result should contain improvement_analysis"
            assert "baseline_metrics" in result, "Result should contain baseline_metrics"
            assert "comparison_metrics" in result, "Result should contain comparison_metrics"
            
            # Verify farmer_id consistency
            assert str(farmer_id) == result["farmer_id"], "Farmer ID should match input"
            
            # Verify improvement analysis structure
            improvement = result["improvement_analysis"]
            assert isinstance(improvement, dict), "Improvement analysis should be dictionary"
            
            required_improvement_fields = [
                "revenue_improvement", "performance_score_improvement", 
                "price_improvement", "efficiency_improvement"
            ]
            for field in required_improvement_fields:
                assert field in improvement, f"Improvement analysis should contain {field}"
                assert isinstance(improvement[field], dict), f"{field} should be dictionary"
                assert "absolute" in improvement[field], f"{field} should have absolute value"
                assert "percentage" in improvement[field], f"{field} should have percentage"
                assert "trend" in improvement[field], f"{field} should have trend"
            
            # Verify mathematical accuracy of percentage calculations
            baseline_metrics = result["baseline_metrics"]
            comparison_metrics = result["comparison_metrics"]
            
            # Test revenue improvement calculation accuracy
            baseline_revenue = baseline_metrics.get("total_revenue", 0)
            comparison_revenue = comparison_metrics.get("total_revenue", 0)
            
            if baseline_revenue > 0:
                expected_revenue_pct = ((comparison_revenue - baseline_revenue) / baseline_revenue) * 100
                actual_revenue_pct = improvement["revenue_improvement"]["percentage"]
                assert abs(expected_revenue_pct - actual_revenue_pct) < 0.01, \
                    f"Revenue improvement percentage should be accurate: expected {expected_revenue_pct}, got {actual_revenue_pct}"
            
            # Test performance score improvement calculation accuracy
            baseline_score = baseline_metrics.get("average_performance_score", 0)
            comparison_score = comparison_metrics.get("average_performance_score", 0)
            
            if baseline_score > 0:
                expected_score_pct = ((comparison_score - baseline_score) / baseline_score) * 100
                actual_score_pct = improvement["performance_score_improvement"]["percentage"]
                assert abs(expected_score_pct - actual_score_pct) < 0.01, \
                    f"Performance score improvement percentage should be accurate: expected {expected_score_pct}, got {actual_score_pct}"
            
            # Test price improvement calculation accuracy
            baseline_price = baseline_metrics.get("average_price", 0)
            comparison_price = comparison_metrics.get("average_price", 0)
            
            if baseline_price > 0:
                expected_price_pct = ((comparison_price - baseline_price) / baseline_price) * 100
                actual_price_pct = improvement["price_improvement"]["percentage"]
                assert abs(expected_price_pct - actual_price_pct) < 0.01, \
                    f"Price improvement percentage should be accurate: expected {expected_price_pct}, got {actual_price_pct}"
            
            # Verify trend classification accuracy
            revenue_trend = improvement["revenue_improvement"]["trend"]
            revenue_pct = improvement["revenue_improvement"]["percentage"]
            
            if revenue_pct > 0:
                assert revenue_trend == "improving", "Positive revenue change should be 'improving'"
            elif revenue_pct < 0:
                assert revenue_trend == "declining", "Negative revenue change should be 'declining'"
            else:
                assert revenue_trend == "stable", "Zero revenue change should be 'stable'"
            
            # Verify overall improvement score is within valid range
            overall_score = improvement.get("overall_improvement_score", 0)
            assert -100 <= overall_score <= 100, "Overall improvement score should be between -100 and 100"
            
            # Verify insights are generated
            insights = result.get("insights", [])
            assert isinstance(insights, list), "Insights should be a list"
            
            for insight in insights:
                assert isinstance(insight, dict), "Each insight should be a dictionary"
                required_insight_fields = ["type", "category", "title", "description", "impact", "confidence"]
                for field in required_insight_fields:
                    assert field in insight, f"Insight should contain {field}"
                
                # Verify confidence is valid probability
                assert 0 <= insight["confidence"] <= 1, "Insight confidence should be between 0 and 1"
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(
        farmer_id=st.uuids(),
        commodity=st.one_of(st.none(), st.sampled_from(["wheat", "rice", "corn"])),
        analysis_period_days=st.integers(min_value=60, max_value=365),
        trend_window_days=st.integers(min_value=7, max_value=60)
    )
    @settings(max_examples=30, deadline=15000)
    def test_performance_trends_analysis_accuracy(
        self, farmer_id, commodity, analysis_period_days, trend_window_days
    ):
        """
        **Validates: Requirements 8.5**
        
        Performance trend analysis should accurately identify patterns and calculate 
        trend metrics for any time period.
        """
        async def run_test():
            # Assume reasonable constraints
            assume(analysis_period_days > trend_window_days * 2)
            assume(trend_window_days >= 7)
            
            # Analyze performance trends
            result = await self.analytics.analyze_performance_trends(
                farmer_id=farmer_id,
                commodity=commodity,
                analysis_period_days=analysis_period_days,
                trend_window_days=trend_window_days,
                db=None
            )
            
            # Verify result structure
            assert isinstance(result, dict), "Result should be a dictionary"
            assert "farmer_id" in result, "Result should contain farmer_id"
            assert "overall_trend" in result, "Result should contain overall_trend"
            assert "rolling_trends" in result, "Result should contain rolling_trends"
            assert "seasonal_patterns" in result, "Result should contain seasonal_patterns"
            
            # Verify farmer_id consistency
            assert str(farmer_id) == result["farmer_id"], "Farmer ID should match input"
            
            # Verify overall trend structure
            overall_trend = result["overall_trend"]
            assert isinstance(overall_trend, dict), "Overall trend should be dictionary"
            
            if overall_trend.get("direction") != "insufficient_data":
                assert "direction" in overall_trend, "Overall trend should have direction"
                assert "strength" in overall_trend, "Overall trend should have strength"
                assert "confidence" in overall_trend, "Overall trend should have confidence"
                
                # Verify trend direction is valid
                valid_directions = [
                    "strongly_improving", "improving", "stable", 
                    "declining", "strongly_declining", "insufficient_data"
                ]
                assert overall_trend["direction"] in valid_directions, \
                    f"Trend direction should be one of {valid_directions}"
                
                # Verify strength and confidence are valid probabilities
                assert 0 <= overall_trend["strength"] <= 1, "Trend strength should be between 0 and 1"
                assert 0 <= overall_trend["confidence"] <= 1, "Trend confidence should be between 0 and 1"
            
            # Verify rolling trends structure
            rolling_trends = result["rolling_trends"]
            assert isinstance(rolling_trends, list), "Rolling trends should be a list"
            
            for trend in rolling_trends:
                assert isinstance(trend, dict), "Each rolling trend should be dictionary"
                assert "period_start" in trend, "Rolling trend should have period_start"
                assert "period_end" in trend, "Rolling trend should have period_end"
                assert "metrics" in trend, "Rolling trend should have metrics"
                assert "record_count" in trend, "Rolling trend should have record_count"
                
                # Verify metrics structure
                metrics = trend["metrics"]
                assert isinstance(metrics, dict), "Trend metrics should be dictionary"
                assert "total_sales" in metrics, "Metrics should contain total_sales"
                assert "average_performance_score" in metrics, "Metrics should contain average_performance_score"
                
                # Verify performance score is valid
                if metrics["total_sales"] > 0:
                    assert 0 <= metrics["average_performance_score"] <= 100, \
                        "Average performance score should be between 0 and 100"
            
            # Verify seasonal patterns structure
            seasonal_patterns = result["seasonal_patterns"]
            assert isinstance(seasonal_patterns, dict), "Seasonal patterns should be dictionary"
            
            if not seasonal_patterns.get("insufficient_data", False):
                assert "monthly_patterns" in seasonal_patterns, "Should have monthly patterns"
                monthly_patterns = seasonal_patterns["monthly_patterns"]
                
                for month_data in monthly_patterns.values():
                    assert isinstance(month_data, dict), "Monthly data should be dictionary"
                    assert "average_performance" in month_data, "Monthly data should have average_performance"
                    assert 0 <= month_data["average_performance"] <= 100, \
                        "Monthly average performance should be between 0 and 100"
            
            # Verify predictions structure if available
            predictions = result.get("predictions", {})
            if predictions.get("prediction_available", False):
                assert "predicted_performance_score" in predictions, "Should have predicted score"
                assert "confidence" in predictions, "Should have prediction confidence"
                
                predicted_score = predictions["predicted_performance_score"]
                assert 0 <= predicted_score <= 100, "Predicted score should be between 0 and 100"
                
                confidence = predictions["confidence"]
                assert 0 <= confidence <= 1, "Prediction confidence should be between 0 and 1"
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(
        farmer_id=st.uuids(),
        commodity=st.one_of(st.none(), st.sampled_from(["wheat", "rice", "corn"])),
        comparison_period_days=st.integers(min_value=30, max_value=180)
    )
    @settings(max_examples=25, deadline=15000)
    def test_comparative_analytics_accuracy(
        self, farmer_id, commodity, comparison_period_days
    ):
        """
        **Validates: Requirements 8.5**
        
        Comparative analytics should accurately compare farmer performance against 
        benchmarks and provide correct rankings and insights.
        """
        async def run_test():
            # Generate comparative analytics
            result = await self.analytics.generate_comparative_analytics(
                farmer_id=farmer_id,
                commodity=commodity,
                comparison_period_days=comparison_period_days,
                db=None
            )
            
            # Verify result structure
            assert isinstance(result, dict), "Result should be a dictionary"
            assert "farmer_id" in result, "Result should contain farmer_id"
            assert "farmer_metrics" in result, "Result should contain farmer_metrics"
            assert "comparative_analysis" in result, "Result should contain comparative_analysis"
            assert "performance_rankings" in result, "Result should contain performance_rankings"
            assert "performance_scorecard" in result, "Result should contain performance_scorecard"
            
            # Verify farmer_id consistency
            assert str(farmer_id) == result["farmer_id"], "Farmer ID should match input"
            
            # Verify farmer metrics structure
            farmer_metrics = result["farmer_metrics"]
            assert isinstance(farmer_metrics, dict), "Farmer metrics should be dictionary"
            
            if farmer_metrics.get("total_sales", 0) > 0:
                # Verify metric ranges
                assert farmer_metrics["average_performance_score"] >= 0, "Performance score should be non-negative"
                assert farmer_metrics["average_performance_score"] <= 100, "Performance score should not exceed 100"
                assert farmer_metrics["average_price"] >= 0, "Average price should be non-negative"
                assert farmer_metrics["total_revenue"] >= 0, "Total revenue should be non-negative"
                
                # Verify consistency between metrics
                expected_total_revenue = farmer_metrics["average_price"] * farmer_metrics["total_quantity"]
                actual_total_revenue = farmer_metrics["total_revenue"]
                # Allow for small floating point differences
                assert abs(expected_total_revenue - actual_total_revenue) < 1.0, \
                    "Total revenue should equal average price times total quantity"
            
            # Verify comparative analysis structure
            comparative_analysis = result["comparative_analysis"]
            assert isinstance(comparative_analysis, dict), "Comparative analysis should be dictionary"
            
            required_comparisons = ["vs_regional_benchmarks", "vs_peer_farmers", "vs_historical_performance"]
            for comparison in required_comparisons:
                assert comparison in comparative_analysis, f"Should contain {comparison}"
            
            # Verify regional comparison accuracy
            vs_regional = comparative_analysis["vs_regional_benchmarks"]
            if "price_comparison" in vs_regional:
                price_comp = vs_regional["price_comparison"]
                farmer_price = price_comp.get("farmer_average", 0)
                regional_price = price_comp.get("regional_average", 0)
                
                if regional_price > 0:
                    expected_pct = ((farmer_price - regional_price) / regional_price) * 100
                    actual_pct = price_comp.get("difference_percentage", 0)
                    assert abs(expected_pct - actual_pct) < 0.01, \
                        "Regional price comparison percentage should be accurate"
                    
                    # Verify status consistency
                    status = price_comp.get("status", "equal")
                    if expected_pct > 0:
                        assert status == "above", "Status should be 'above' for positive difference"
                    elif expected_pct < 0:
                        assert status == "below", "Status should be 'below' for negative difference"
                    else:
                        assert status == "equal", "Status should be 'equal' for zero difference"
            
            # Verify performance rankings
            rankings = result["performance_rankings"]
            assert isinstance(rankings, dict), "Rankings should be dictionary"
            
            ranking_fields = ["performance_percentile", "price_percentile", "overall_percentile"]
            for field in ranking_fields:
                if field in rankings:
                    percentile = rankings[field]
                    assert 0 <= percentile <= 100, f"{field} should be between 0 and 100"
            
            # Verify overall percentile is average of component percentiles
            if all(field in rankings for field in ["performance_percentile", "price_percentile"]):
                expected_overall = (rankings["performance_percentile"] + rankings["price_percentile"]) / 2
                actual_overall = rankings.get("overall_percentile", 0)
                assert abs(expected_overall - actual_overall) < 0.01, \
                    "Overall percentile should be average of component percentiles"
            
            # Verify performance scorecard
            scorecard = result["performance_scorecard"]
            assert isinstance(scorecard, dict), "Scorecard should be dictionary"
            assert "overall_score" in scorecard, "Scorecard should have overall_score"
            assert "grade" in scorecard, "Scorecard should have grade"
            assert "component_scores" in scorecard, "Scorecard should have component_scores"
            
            # Verify overall score range
            overall_score = scorecard["overall_score"]
            assert 0 <= overall_score <= 100, "Overall score should be between 0 and 100"
            
            # Verify grade consistency with score
            grade = scorecard["grade"]
            valid_grades = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D"]
            assert grade in valid_grades, f"Grade should be one of {valid_grades}"
            
            # Verify grade matches score range
            if overall_score >= 90:
                assert grade in ["A+", "A"], "Score >= 90 should have A-level grade"
            elif overall_score >= 80:
                assert grade in ["A", "A-", "B+"], "Score >= 80 should have A/B+ grade"
            elif overall_score < 50:
                assert grade in ["D", "C-"], "Score < 50 should have low grade"
            
            # Verify improvement opportunities structure
            opportunities = result.get("improvement_opportunities", [])
            assert isinstance(opportunities, list), "Opportunities should be list"
            
            for opportunity in opportunities:
                assert isinstance(opportunity, dict), "Each opportunity should be dictionary"
                required_opp_fields = ["type", "priority", "title", "description"]
                for field in required_opp_fields:
                    assert field in opportunity, f"Opportunity should contain {field}"
                
                # Verify priority is valid
                priority = opportunity["priority"]
                assert priority in ["high", "medium", "low"], "Priority should be high/medium/low"
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(
        baseline_revenue=st.floats(min_value=1000, max_value=100000),
        comparison_revenue=st.floats(min_value=1000, max_value=100000),
        baseline_score=st.floats(min_value=10, max_value=100),
        comparison_score=st.floats(min_value=10, max_value=100)
    )
    @settings(max_examples=100, deadline=5000)
    def test_improvement_metrics_mathematical_accuracy(
        self, baseline_revenue, comparison_revenue, baseline_score, comparison_score
    ):
        """
        **Validates: Requirements 8.5**
        
        Mathematical calculations for improvement metrics should be accurate 
        for any valid input values.
        """
        # Create mock metrics
        baseline_metrics = {
            "total_revenue": baseline_revenue,
            "average_performance_score": baseline_score,
            "average_price": baseline_revenue / 100,  # Assume 100 units
            "average_revenue_per_sale": baseline_revenue / 10,  # Assume 10 sales
            "consistency_score": 0.8
        }
        
        comparison_metrics = {
            "total_revenue": comparison_revenue,
            "average_performance_score": comparison_score,
            "average_price": comparison_revenue / 100,
            "average_revenue_per_sale": comparison_revenue / 10,
            "consistency_score": 0.85
        }
        
        # Calculate improvement metrics
        improvement = self.analytics._calculate_improvement_metrics(
            baseline_metrics, comparison_metrics
        )
        
        # Verify revenue improvement calculation
        expected_revenue_pct = ((comparison_revenue - baseline_revenue) / baseline_revenue) * 100
        actual_revenue_pct = improvement["revenue_improvement"]["percentage"]
        assert abs(expected_revenue_pct - actual_revenue_pct) < 0.001, \
            f"Revenue improvement should be accurate: expected {expected_revenue_pct}, got {actual_revenue_pct}"
        
        # Verify performance score improvement calculation
        expected_score_pct = ((comparison_score - baseline_score) / baseline_score) * 100
        actual_score_pct = improvement["performance_score_improvement"]["percentage"]
        assert abs(expected_score_pct - actual_score_pct) < 0.001, \
            f"Score improvement should be accurate: expected {expected_score_pct}, got {actual_score_pct}"
        
        # Verify absolute differences
        expected_revenue_abs = comparison_revenue - baseline_revenue
        actual_revenue_abs = improvement["revenue_improvement"]["absolute"]
        assert abs(expected_revenue_abs - actual_revenue_abs) < 0.001, \
            "Revenue absolute difference should be accurate"
        
        expected_score_abs = comparison_score - baseline_score
        actual_score_abs = improvement["performance_score_improvement"]["absolute"]
        assert abs(expected_score_abs - actual_score_abs) < 0.001, \
            "Score absolute difference should be accurate"
        
        # Verify trend classifications
        revenue_trend = improvement["revenue_improvement"]["trend"]
        if expected_revenue_abs > 0:
            assert revenue_trend == "improving", "Positive change should be 'improving'"
        elif expected_revenue_abs < 0:
            assert revenue_trend == "declining", "Negative change should be 'declining'"
        else:
            assert revenue_trend == "stable", "Zero change should be 'stable'"
        
        # Verify overall improvement score is within bounds
        overall_score = improvement["overall_improvement_score"]
        assert -100 <= overall_score <= 100, "Overall improvement score should be between -100 and 100"
    
    def test_empty_data_handling(self):
        """
        **Validates: Requirements 8.5**
        
        System should handle empty or insufficient data gracefully without errors.
        """
        async def run_test():
            farmer_id = uuid4()
            
            # Test with no data
            result = await self.analytics.calculate_income_improvement(
                farmer_id=farmer_id,
                commodity="wheat",
                baseline_period_days=90,
                comparison_period_days=30,
                db=None
            )
            
            # Should return valid structure even with no data
            assert isinstance(result, dict), "Should return dictionary even with no data"
            assert "farmer_id" in result, "Should contain farmer_id"
            assert "improvement_analysis" in result, "Should contain improvement_analysis"
            
            # Test trends analysis with insufficient data
            trends_result = await self.analytics.analyze_performance_trends(
                farmer_id=farmer_id,
                commodity="wheat",
                analysis_period_days=180,
                trend_window_days=30,
                db=None
            )
            
            assert isinstance(trends_result, dict), "Should return dictionary"
            assert "overall_trend" in trends_result, "Should contain overall_trend"
        
        # Run the async test
        asyncio.run(run_test())

if __name__ == "__main__":
    pytest.main([__file__, "-v"])