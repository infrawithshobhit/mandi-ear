"""
Property-Based Test for Negotiation Guidance Completeness
**Property 8: Negotiation Guidance Completeness**
**Validates: Requirements 4.1, 4.2, 4.3, 4.5**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
import sys
import os
import asyncio

# Add the service path to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services', 'negotiation-intelligence-service'))

from models import (
    MarketContext, BuyerIntent, NegotiationStrategy, OutcomePrediction,
    MarketCondition, UrgencyLevel, RiskLevel, NegotiationTactic
)
from market_context_analyzer import MarketContextAnalyzer
from buyer_intent_detector import BuyerIntentDetector
from negotiation_strategy_generator import NegotiationStrategyGenerator

# Test data generators
@st.composite
def generate_location(draw):
    """Generate valid Indian geographic coordinates"""
    # India's approximate bounds
    lat = draw(st.floats(min_value=8.0, max_value=37.0))
    lng = draw(st.floats(min_value=68.0, max_value=97.0))
    return {"lat": lat, "lng": lng}

@st.composite
def generate_commodity(draw):
    """Generate valid commodity names"""
    commodities = ['wheat', 'rice', 'onion', 'potato', 'tomato', 'sugarcane', 'cotton', 'soybean']
    return draw(st.sampled_from(commodities))

@st.composite
def generate_market_context(draw):
    """Generate valid market context"""
    commodity = draw(generate_commodity())
    current_price = draw(st.floats(min_value=100.0, max_value=10000.0))
    
    return MarketContext(
        commodity=commodity,
        current_price=current_price,
        price_trend=draw(st.sampled_from(["increasing", "decreasing", "stable"])),
        market_condition=draw(st.sampled_from(list(MarketCondition))),
        supply_level=draw(st.sampled_from(["low", "medium", "high"])),
        demand_level=draw(st.sampled_from(["low", "medium", "high"])),
        seasonal_factor=draw(st.floats(min_value=0.8, max_value=1.3)),
        weather_impact=draw(st.one_of(st.none(), st.sampled_from(["drought_risk", "flood_risk"]))),
        festival_demand=draw(st.booleans()),
        export_demand=draw(st.one_of(st.none(), st.floats(min_value=0.0, max_value=0.5))),
        transportation_cost=draw(st.floats(min_value=10.0, max_value=200.0)),
        storage_cost=draw(st.floats(min_value=5.0, max_value=50.0)),
        quality_premium=draw(st.floats(min_value=0.0, max_value=0.3)),
        competition_level=draw(st.sampled_from(["low", "medium", "high"]))
    )

@st.composite
def generate_buyer_intent(draw):
    """Generate valid buyer intent"""
    return BuyerIntent(
        urgency=draw(st.sampled_from(list(UrgencyLevel))),
        price_sensitivity=draw(st.floats(min_value=0.0, max_value=1.0)),
        quality_focus=draw(st.floats(min_value=0.0, max_value=1.0)),
        volume_requirement=draw(st.floats(min_value=1.0, max_value=1000.0)),
        negotiation_style=draw(st.sampled_from(["aggressive", "collaborative", "passive"])),
        budget_constraint=draw(st.one_of(st.none(), st.floats(min_value=100.0, max_value=50000.0))),
        alternative_sources=draw(st.integers(min_value=1, max_value=10)),
        relationship_value=draw(st.floats(min_value=0.0, max_value=1.0)),
        repeat_buyer=draw(st.booleans()),
        payment_terms_flexibility=draw(st.floats(min_value=0.0, max_value=1.0)),
        confidence=draw(st.floats(min_value=0.3, max_value=1.0))
    )

@st.composite
def generate_farmer_profile(draw):
    """Generate valid farmer profile"""
    return {
        "farmer_id": draw(st.text(min_size=5, max_size=20)),
        "experience_years": draw(st.integers(min_value=1, max_value=50)),
        "minimum_price": draw(st.floats(min_value=100.0, max_value=5000.0)),
        "preferred_payment": draw(st.sampled_from(["cash", "credit", "advance"])),
        "quality_grade": draw(st.sampled_from(["A", "B", "C"]))
    }

@st.composite
def generate_conversation_data(draw):
    """Generate conversation data for buyer intent detection"""
    urgency_words = draw(st.lists(
        st.sampled_from(["urgent", "immediately", "today", "soon", "flexible", "no rush"]),
        min_size=0, max_size=3
    ))
    
    price_words = draw(st.lists(
        st.sampled_from(["cheap", "discount", "premium", "quality", "reasonable", "fair"]),
        min_size=0, max_size=2
    ))
    
    quantity_info = draw(st.one_of(
        st.just(""),
        st.text().map(lambda x: f"{draw(st.integers(min_value=1, max_value=500))} quintal")
    ))
    
    conversation = " ".join(urgency_words + price_words + [quantity_info])
    return conversation.strip()

class TestNegotiationGuidanceCompleteness:
    """Test Property 8: Negotiation Guidance Completeness"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.market_analyzer = MarketContextAnalyzer()
        self.intent_detector = BuyerIntentDetector()
        self.strategy_generator = NegotiationStrategyGenerator()
    
    @given(
        commodity=generate_commodity(),
        location=generate_location(),
        market_context=generate_market_context(),
        buyer_intent=generate_buyer_intent(),
        farmer_profile=generate_farmer_profile()
    )
    @settings(max_examples=100, deadline=30000)
    def test_negotiation_strategy_completeness(
        self, commodity, location, market_context, buyer_intent, farmer_profile
    ):
        """
        **Validates: Requirements 4.1, 4.2, 4.3, 4.5**
        
        For any negotiation context, the system should provide:
        - Real-time price benchmarks (Req 4.1)
        - Counter-offer suggestions within 5 seconds (Req 4.2)
        - Holding strategies with time-based predictions (Req 4.3)
        - Competitive bidding facilitation (Req 4.5)
        """
        async def run_test():
            # Test market context analysis (Requirement 4.1)
            start_time = datetime.now()
            analyzed_context = await self.market_analyzer.analyze_market_context(commodity, location)
            analysis_time = (datetime.now() - start_time).total_seconds()
            
            # Verify real-time market condition assessment
            assert analyzed_context.commodity == commodity
            assert analyzed_context.current_price > 0
            assert analyzed_context.price_trend in ["increasing", "decreasing", "stable"]
            assert analyzed_context.market_condition in list(MarketCondition)
            assert analyzed_context.supply_level in ["low", "medium", "high"]
            assert analyzed_context.demand_level in ["low", "medium", "high"]
            assert 0.5 <= analyzed_context.seasonal_factor <= 2.0
            assert analyzed_context.transportation_cost >= 0
            assert analyzed_context.storage_cost >= 0
            assert 0.0 <= analyzed_context.quality_premium <= 1.0
            assert analyzed_context.competition_level in ["low", "medium", "high"]
            
            # Test strategy generation (Requirements 4.1, 4.2, 4.3, 4.5)
            start_time = datetime.now()
            strategy = await self.strategy_generator.generate_strategy(
                commodity=commodity,
                location=location,
                market_context=market_context,
                buyer_intent=buyer_intent,
                farmer_profile=farmer_profile
            )
            strategy_time = (datetime.now() - start_time).total_seconds()
            
            # Requirement 4.2: Counter-offer suggestions within 5 seconds
            assert strategy_time <= 5.0, f"Strategy generation took {strategy_time:.2f}s, should be ≤ 5s"
            
            # Verify strategy completeness
            assert strategy.recommended_price > 0
            assert strategy.price_range.min_price <= strategy.price_range.optimal_price <= strategy.price_range.max_price
            assert 0.0 <= strategy.price_range.confidence <= 1.0
            assert len(strategy.tactics) > 0
            assert all(isinstance(tactic, NegotiationTactic) for tactic in strategy.tactics)
            assert strategy.timing.optimal_timing in ["immediate", "wait_short", "wait_long"]
            assert strategy.timing.price_movement_prediction in ["increase", "decrease", "stable"]
            assert 0.0 <= strategy.timing.confidence <= 1.0
            assert len(strategy.key_arguments) > 0
            assert isinstance(strategy.concession_strategy, dict)
            assert strategy.risk_assessment in list(RiskLevel)
            assert 0.0 <= strategy.success_probability <= 1.0
            assert 0.0 <= strategy.confidence <= 1.0
            
            # Requirement 4.3: Holding strategies with time-based predictions
            if market_context.price_trend == "increasing" or market_context.demand_level == "high":
                # Should suggest holding or immediate action
                assert strategy.timing.optimal_timing in ["immediate", "wait_short"]
                if strategy.timing.optimal_timing == "wait_short":
                    assert strategy.timing.wait_duration is not None
                    assert strategy.timing.wait_duration > 0
            
            # Requirement 4.5: Competitive bidding facilitation
            if (market_context.competition_level == "high" or 
                buyer_intent.alternative_sources > 2 or
                NegotiationTactic.COMPETITIVE_BIDDING in strategy.tactics):
                # Should have alternatives or competitive elements
                assert (len(strategy.alternatives) > 0 or 
                       NegotiationTactic.COMPETITIVE_BIDDING in strategy.tactics or
                       "competition" in " ".join(strategy.key_arguments).lower())
            
            # Test outcome prediction
            prediction = await self.strategy_generator.predict_outcome(strategy, market_context)
            
            # Verify prediction completeness
            assert 0.0 <= prediction.success_probability <= 1.0
            assert prediction.expected_final_price > 0
            assert prediction.negotiation_duration > 0
            assert 1.0 <= prediction.farmer_satisfaction_score <= 5.0
            assert len(prediction.key_success_factors) > 0
            assert len(prediction.potential_obstacles) >= 0  # Can be empty
            assert 0.0 <= prediction.confidence <= 1.0
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(conversation_data=generate_conversation_data())
    @settings(max_examples=50, deadline=15000)
    def test_buyer_intent_detection_completeness(self, conversation_data):
        """
        **Validates: Requirements 4.1, 4.2**
        
        For any conversation data, buyer intent detection should provide complete analysis
        """
        assume(len(conversation_data.strip()) > 0)  # Ensure non-empty conversation
        
        async def run_test():
            intent = await self.intent_detector.detect_buyer_intent(conversation_data)
            
            # Verify intent completeness
            assert intent.urgency in list(UrgencyLevel)
            assert 0.0 <= intent.price_sensitivity <= 1.0
            assert 0.0 <= intent.quality_focus <= 1.0
            assert intent.volume_requirement > 0
            assert intent.negotiation_style in ["aggressive", "collaborative", "passive"]
            assert intent.alternative_sources >= 1
            assert 0.0 <= intent.relationship_value <= 1.0
            assert isinstance(intent.repeat_buyer, bool)
            assert 0.0 <= intent.payment_terms_flexibility <= 1.0
            assert 0.0 <= intent.confidence <= 1.0
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(
        commodity=generate_commodity(),
        location=generate_location()
    )
    @settings(max_examples=30, deadline=20000)
    def test_market_context_analysis_timeliness(self, commodity, location):
        """
        **Validates: Requirements 4.1, 4.2**
        
        Market context analysis should complete within reasonable time
        """
        async def run_test():
            start_time = datetime.now()
            context = await self.market_analyzer.analyze_market_context(commodity, location)
            analysis_time = (datetime.now() - start_time).total_seconds()
            
            # Should complete within 5 seconds for real-time requirements
            assert analysis_time <= 5.0, f"Market analysis took {analysis_time:.2f}s, should be ≤ 5s"
            
            # Verify context is complete and valid
            assert context.commodity == commodity
            assert context.current_price > 0
            assert context.timestamp is not None
            assert (datetime.now() - context.timestamp).total_seconds() < 60  # Recent data
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(
        market_context=generate_market_context(),
        buyer_intent=generate_buyer_intent()
    )
    @settings(max_examples=50, deadline=20000)
    def test_strategy_adaptation_to_context(self, market_context, buyer_intent):
        """
        **Validates: Requirements 4.1, 4.2, 4.3**
        
        Strategy should adapt appropriately to different market contexts and buyer intents
        """
        async def run_test():
            farmer_profile = {"farmer_id": "test", "minimum_price": market_context.current_price * 0.9}
            location = {"lat": 20.0, "lng": 77.0}
            
            strategy = await self.strategy_generator.generate_strategy(
                commodity=market_context.commodity,
                location=location,
                market_context=market_context,
                buyer_intent=buyer_intent,
                farmer_profile=farmer_profile
            )
            
            # Strategy should reflect market conditions
            if market_context.market_condition == MarketCondition.BULLISH:
                # Should recommend higher prices or firm tactics
                assert (strategy.recommended_price >= market_context.current_price or
                       NegotiationTactic.HOLD_FIRM in strategy.tactics)
            
            if market_context.market_condition == MarketCondition.BEARISH:
                # Should be more flexible or suggest alternatives
                assert (len(strategy.alternatives) > 0 or
                       NegotiationTactic.GRADUAL_CONCESSION in strategy.tactics)
            
            # Strategy should reflect buyer urgency
            if buyer_intent.urgency == UrgencyLevel.HIGH:
                # Should capitalize on urgency
                assert (strategy.timing.optimal_timing == "immediate" or
                       NegotiationTactic.TIME_PRESSURE in strategy.tactics)
            
            # Strategy should respect farmer's minimum price
            assert strategy.price_range.min_price >= farmer_profile["minimum_price"]
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(
        market_context=generate_market_context(),
        buyer_intent=generate_buyer_intent()
    )
    @settings(max_examples=30, deadline=15000)
    def test_competitive_bidding_facilitation(self, market_context, buyer_intent):
        """
        **Validates: Requirements 4.5**
        
        System should facilitate competitive bidding when multiple buyers are present
        """
        async def run_test():
            # Simulate high competition scenario
            market_context.competition_level = "high"
            buyer_intent.alternative_sources = 5  # Multiple alternatives
            
            farmer_profile = {"farmer_id": "test", "minimum_price": market_context.current_price * 0.9}
            location = {"lat": 20.0, "lng": 77.0}
            
            strategy = await self.strategy_generator.generate_strategy(
                commodity=market_context.commodity,
                location=location,
                market_context=market_context,
                buyer_intent=buyer_intent,
                farmer_profile=farmer_profile
            )
            
            # Should facilitate competitive bidding
            competitive_indicators = [
                NegotiationTactic.COMPETITIVE_BIDDING in strategy.tactics,
                len(strategy.alternatives) > 0,
                any("competition" in arg.lower() for arg in strategy.key_arguments),
                any("bidding" in arg.lower() for arg in strategy.key_arguments),
                strategy.timing.optimal_timing == "immediate"  # Strike while competition is high
            ]
            
            # At least one competitive indicator should be present
            assert any(competitive_indicators), "Strategy should facilitate competitive bidding in high competition scenarios"
        
        # Run the async test
        asyncio.run(run_test())

# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])