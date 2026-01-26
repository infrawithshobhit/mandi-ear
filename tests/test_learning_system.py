"""
Property-Based Test for Learning System Improvement
**Property 9: Learning System Improvement**
**Validates: Requirements 4.4**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
import sys
import os
import asyncio
import uuid

# Add the service path to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services', 'negotiation-intelligence-service'))

from models import (
    MarketContext, BuyerIntent, NegotiationSession, NegotiationOutcome,
    MarketCondition, UrgencyLevel, RiskLevel, NegotiationTactic
)
from learning_engine import LearningEngine

# Test data generators
@st.composite
def generate_location(draw):
    """Generate valid Indian geographic coordinates"""
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
def generate_negotiation_outcome(draw):
    """Generate valid negotiation outcome"""
    session_id = str(uuid.uuid4())
    final_price = draw(st.floats(min_value=100.0, max_value=10000.0))
    success = draw(st.booleans())
    farmer_satisfaction = draw(st.integers(min_value=1, max_value=5))
    
    return {
        'session_id': session_id,
        'final_price': final_price,
        'success': success,
        'farmer_satisfaction': farmer_satisfaction,
        'strategy_used': {
            'tactics': draw(st.lists(
                st.sampled_from(['hold_firm', 'gradual_concession', 'competitive_bidding']),
                min_size=1, max_size=3
            )),
            'recommended_price': draw(st.floats(min_value=100.0, max_value=10000.0))
        }
    }

@st.composite
def generate_farmer_id(draw):
    """Generate valid farmer ID"""
    return draw(st.text(min_size=5, max_size=20, alphabet=st.characters(min_codepoint=48, max_codepoint=122)))

class TestLearningSystemImprovement:
    """Test Property 9: Learning System Improvement"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.learning_engine = LearningEngine()
        # Reset state for clean test environment
        self.learning_engine.reset_state()
    
    @given(
        commodity=generate_commodity(),
        location=generate_location(),
        market_context=generate_market_context(),
        buyer_intent=generate_buyer_intent(),
        farmer_id=generate_farmer_id(),
        outcomes=st.lists(generate_negotiation_outcome(), min_size=1, max_size=5)  # Reduced size
    )
    @settings(max_examples=20, deadline=20000)  # Reduced examples and increased deadline
    def test_learning_system_improvement(
        self, commodity, location, market_context, buyer_intent, farmer_id, outcomes
    ):
        """
        **Validates: Requirements 4.4**
        
        For any negotiation outcome, the system should correctly incorporate feedback 
        to improve future recommendations
        """
        async def run_test():
            # Reset state to ensure clean test
            self.learning_engine.reset_state()
            
            # Get initial recommendations (should have low confidence due to no data)
            initial_recommendations = await self.learning_engine.get_strategy_recommendations(
                commodity=commodity,
                market_context=market_context,
                buyer_intent=buyer_intent
            )
            
            # Should return recommendations with low confidence initially
            assert 'recommendations' in initial_recommendations
            assert 'confidence' in initial_recommendations
            assert initial_recommendations['confidence'] == 0.3  # Fixed low confidence for no data
            assert initial_recommendations['similar_scenarios_count'] == 0
            
            # Learn from multiple outcomes
            learned_sessions = []
            for i, outcome_data in enumerate(outcomes):
                # Create a session for each outcome
                outcome_session_id = await self.learning_engine.create_session(
                    farmer_id=f"{farmer_id}_{i}",
                    commodity=commodity,
                    location=location,
                    initial_offer=outcome_data['final_price'] * 0.9,  # Slightly lower initial offer
                    market_context=market_context,
                    buyer_intent=buyer_intent
                )
                
                learned_sessions.append(outcome_session_id)
                
                # Learn from the outcome
                await self.learning_engine.learn_from_outcome(
                    session_id=outcome_session_id,
                    final_price=outcome_data['final_price'],
                    strategy_used=outcome_data['strategy_used'],
                    success=outcome_data['success'],
                    farmer_satisfaction=outcome_data['farmer_satisfaction']
                )
                
                # Verify the session was updated with outcome
                updated_session = await self.learning_engine.get_session(outcome_session_id)
                assert updated_session.final_price == outcome_data['final_price']
                assert updated_session.success == outcome_data['success']
                assert updated_session.farmer_satisfaction == outcome_data['farmer_satisfaction']
                assert len(updated_session.lessons_learned) > 0
            
            # Get recommendations after learning
            post_learning_recommendations = await self.learning_engine.get_strategy_recommendations(
                commodity=commodity,
                market_context=market_context,
                buyer_intent=buyer_intent
            )
            
            # System should have learned and improved recommendations
            if len(outcomes) >= 3:  # Sufficient data for learning
                # Should have similar scenarios count
                assert post_learning_recommendations.get('similar_scenarios_count', 0) > 0
                
                # Should have success rate information
                assert 'success_rate' in post_learning_recommendations
                assert 0.0 <= post_learning_recommendations['success_rate'] <= 1.0
            
            # Test performance analytics
            analytics = await self.learning_engine.get_performance_analytics(
                farmer_id=farmer_id,
                commodity=commodity,
                time_period_days=30
            )
            
            # Verify analytics completeness
            assert 'total_negotiations' in analytics
            assert 'success_rate' in analytics
            assert 'avg_price_improvement' in analytics
            assert 'avg_satisfaction' in analytics
            assert 'top_tactics' in analytics
            assert 'lessons_learned' in analytics
            
            # Analytics should reflect the learned outcomes
            assert analytics['total_negotiations'] >= 0
            assert 0.0 <= analytics['success_rate'] <= 1.0
            assert isinstance(analytics['top_tactics'], list)
            assert isinstance(analytics['lessons_learned'], list)
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(
        commodity=generate_commodity(),
        market_context=generate_market_context(),
        buyer_intent=generate_buyer_intent(),
        successful_outcomes=st.lists(generate_negotiation_outcome(), min_size=2, max_size=4),  # Reduced size
        failed_outcomes=st.lists(generate_negotiation_outcome(), min_size=1, max_size=2)  # Reduced size
    )
    @settings(max_examples=15, deadline=20000)  # Reduced examples
    def test_learning_pattern_recognition(
        self, commodity, market_context, buyer_intent, successful_outcomes, failed_outcomes
    ):
        """
        **Validates: Requirements 4.4**
        
        System should recognize patterns between successful and failed negotiations
        """
        async def run_test():
            # Reset state to ensure clean test
            self.learning_engine.reset_state()
            
            # Force outcomes to be successful/failed
            for outcome in successful_outcomes:
                outcome['success'] = True
                outcome['farmer_satisfaction'] = 4  # High satisfaction
            
            for outcome in failed_outcomes:
                outcome['success'] = False
                outcome['farmer_satisfaction'] = 2  # Low satisfaction
            
            all_outcomes = successful_outcomes + failed_outcomes
            
            # Learn from all outcomes
            for i, outcome_data in enumerate(all_outcomes):
                session_id = await self.learning_engine.create_session(
                    farmer_id=f"farmer_{i}",
                    commodity=commodity,
                    location={"lat": 20.0, "lng": 77.0},
                    initial_offer=outcome_data['final_price'] * 0.95,
                    market_context=market_context,
                    buyer_intent=buyer_intent
                )
                
                await self.learning_engine.learn_from_outcome(
                    session_id=session_id,
                    final_price=outcome_data['final_price'],
                    strategy_used=outcome_data['strategy_used'],
                    success=outcome_data['success'],
                    farmer_satisfaction=outcome_data['farmer_satisfaction']
                )
            
            # Get analytics to verify pattern recognition
            analytics = await self.learning_engine.get_performance_analytics(
                commodity=commodity,
                time_period_days=30
            )
            
            # Should recognize patterns in successful vs failed negotiations
            total_negotiations = len(all_outcomes)
            expected_success_rate = len(successful_outcomes) / total_negotiations
            
            assert analytics['total_negotiations'] == total_negotiations
            assert abs(analytics['success_rate'] - expected_success_rate) < 0.1  # Within 10%
            
            # Should have learned lessons
            assert len(analytics['lessons_learned']) > 0
            
            # Should identify top tactics from successful negotiations
            if analytics['top_tactics']:
                # Top tactics should have reasonable success rates
                for tactic_info in analytics['top_tactics']:
                    assert 'tactic' in tactic_info
                    assert 'success_rate' in tactic_info
                    assert 0.0 <= tactic_info['success_rate'] <= 1.0
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(
        commodity=generate_commodity(),
        market_context=generate_market_context(),
        buyer_intent=generate_buyer_intent(),
        farmer_id=generate_farmer_id()
    )
    @settings(max_examples=30, deadline=15000)
    def test_learning_system_memory_management(
        self, commodity, market_context, buyer_intent, farmer_id
    ):
        """
        **Validates: Requirements 4.4**
        
        Learning system should manage memory efficiently and maintain recent patterns
        """
        async def run_test():
            # Create many outcomes to test memory management
            for i in range(150):  # More than the pattern memory limit
                session_id = await self.learning_engine.create_session(
                    farmer_id=f"{farmer_id}_{i}",
                    commodity=commodity,
                    location={"lat": 20.0, "lng": 77.0},
                    initial_offer=1000.0 + i,
                    market_context=market_context,
                    buyer_intent=buyer_intent
                )
                
                await self.learning_engine.learn_from_outcome(
                    session_id=session_id,
                    final_price=1000.0 + i + 50,
                    strategy_used={'tactics': ['hold_firm'], 'recommended_price': 1000.0 + i},
                    success=i % 2 == 0,  # Alternate success/failure
                    farmer_satisfaction=4 if i % 2 == 0 else 2
                )
            
            # Verify memory management
            # Successful patterns should be limited to 100
            assert len(self.learning_engine.successful_patterns) <= 100
            
            # Failed patterns should be limited to 50
            assert len(self.learning_engine.failed_patterns) <= 50
            
            # Should still be able to get recommendations
            recommendations = await self.learning_engine.get_strategy_recommendations(
                commodity=commodity,
                market_context=market_context,
                buyer_intent=buyer_intent
            )
            
            assert 'recommendations' in recommendations
            assert 'confidence' in recommendations
            
            # Should have high confidence due to many data points
            assert recommendations['confidence'] > 0.5
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(
        commodity=generate_commodity(),
        market_context=generate_market_context(),
        buyer_intent=generate_buyer_intent()
    )
    @settings(max_examples=20, deadline=15000)
    def test_competitive_bidding_learning(
        self, commodity, market_context, buyer_intent
    ):
        """
        **Validates: Requirements 4.4**
        
        System should learn specifically from competitive bidding scenarios
        """
        async def run_test():
            # Set up competitive scenario
            market_context.competition_level = "high"
            buyer_intent.alternative_sources = 5
            
            # Create competitive bidding outcomes
            competitive_outcomes = [
                {
                    'final_price': 2000.0,
                    'success': True,
                    'farmer_satisfaction': 5,
                    'strategy_used': {
                        'tactics': ['competitive_bidding', 'hold_firm'],
                        'recommended_price': 1950.0
                    }
                },
                {
                    'final_price': 1800.0,
                    'success': False,
                    'farmer_satisfaction': 2,
                    'strategy_used': {
                        'tactics': ['gradual_concession'],
                        'recommended_price': 1900.0
                    }
                }
            ]
            
            # Learn from competitive scenarios
            for i, outcome_data in enumerate(competitive_outcomes):
                session_id = await self.learning_engine.create_session(
                    farmer_id=f"competitive_farmer_{i}",
                    commodity=commodity,
                    location={"lat": 20.0, "lng": 77.0},
                    initial_offer=1900.0,
                    market_context=market_context,
                    buyer_intent=buyer_intent
                )
                
                await self.learning_engine.learn_from_outcome(
                    session_id=session_id,
                    final_price=outcome_data['final_price'],
                    strategy_used=outcome_data['strategy_used'],
                    success=outcome_data['success'],
                    farmer_satisfaction=outcome_data['farmer_satisfaction']
                )
                
                # Verify competitive bidding learning
                session = await self.learning_engine.get_session(session_id)
                assert len(session.lessons_learned) > 0
                
                # Should have competitive-specific lessons
                lessons_text = ' '.join(session.lessons_learned).lower()
                if outcome_data['success']:
                    assert 'competitive' in lessons_text or 'bidding' in lessons_text
            
            # Get recommendations for competitive scenario
            recommendations = await self.learning_engine.get_strategy_recommendations(
                commodity=commodity,
                market_context=market_context,
                buyer_intent=buyer_intent
            )
            
            # Should provide recommendations based on competitive learning
            assert 'recommendations' in recommendations
            if recommendations['recommendations']:
                # Should favor tactics that worked in competitive scenarios
                recommended_tactics = [r.get('tactic') for r in recommendations['recommendations']]
                assert any('competitive' in str(tactic).lower() or 'hold' in str(tactic).lower() 
                          for tactic in recommended_tactics)
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(
        commodity=generate_commodity(),
        farmer_id=generate_farmer_id(),
        time_period_days=st.integers(min_value=7, max_value=90)
    )
    @settings(max_examples=20, deadline=15000)
    def test_performance_analytics_accuracy(
        self, commodity, farmer_id, time_period_days
    ):
        """
        **Validates: Requirements 4.4**
        
        Performance analytics should accurately reflect learning outcomes
        """
        async def run_test():
            # Create outcomes with known statistics
            known_outcomes = []
            successful_count = 0
            total_satisfaction = 0
            
            for i in range(10):
                success = i < 7  # 70% success rate
                satisfaction = 4 if success else 2
                
                if success:
                    successful_count += 1
                total_satisfaction += satisfaction
                
                known_outcomes.append({
                    'final_price': 1000.0 + i * 10,
                    'success': success,
                    'farmer_satisfaction': satisfaction,
                    'strategy_used': {
                        'tactics': ['hold_firm'] if success else ['gradual_concession'],
                        'recommended_price': 1000.0 + i * 10
                    }
                })
            
            # Learn from known outcomes
            for i, outcome_data in enumerate(known_outcomes):
                session_id = await self.learning_engine.create_session(
                    farmer_id=f"{farmer_id}_{i}",
                    commodity=commodity,
                    location={"lat": 20.0, "lng": 77.0},
                    initial_offer=outcome_data['final_price'] - 50,
                    market_context=None,
                    buyer_intent=None
                )
                
                await self.learning_engine.learn_from_outcome(
                    session_id=session_id,
                    final_price=outcome_data['final_price'],
                    strategy_used=outcome_data['strategy_used'],
                    success=outcome_data['success'],
                    farmer_satisfaction=outcome_data['farmer_satisfaction']
                )
            
            # Get analytics and verify accuracy
            analytics = await self.learning_engine.get_performance_analytics(
                farmer_id=farmer_id,
                commodity=commodity,
                time_period_days=time_period_days
            )
            
            # Verify calculated statistics match expected values
            expected_success_rate = successful_count / len(known_outcomes)
            expected_avg_satisfaction = total_satisfaction / len(known_outcomes)
            
            assert analytics['total_negotiations'] == len(known_outcomes)
            assert abs(analytics['success_rate'] - expected_success_rate) < 0.01
            assert abs(analytics['avg_satisfaction'] - expected_avg_satisfaction) < 0.1
            
            # Should have identified top tactics
            if analytics['top_tactics']:
                # 'hold_firm' should be the top tactic (used in successful negotiations)
                top_tactic = analytics['top_tactics'][0]
                assert top_tactic['tactic'] == 'hold_firm'
                assert top_tactic['success_rate'] == 1.0  # 100% success rate for hold_firm
        
        # Run the async test
        asyncio.run(run_test())

# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])