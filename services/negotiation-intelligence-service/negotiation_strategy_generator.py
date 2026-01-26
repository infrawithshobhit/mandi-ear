"""
Negotiation Strategy Generator for Negotiation Intelligence Service
Creates AI-powered negotiation strategies and outcome predictions
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random
import statistics

from models import (
    MarketContext, BuyerIntent, NegotiationStrategy, OutcomePrediction,
    PriceRange, TimingRecommendation, AlternativeOption, NegotiationTactic,
    RiskLevel, UrgencyLevel, MarketCondition
)

logger = logging.getLogger(__name__)

class NegotiationStrategyGenerator:
    """Generates AI-powered negotiation strategies based on market context and buyer intent"""
    
    def __init__(self):
        self.strategy_cache = {}
        self.historical_outcomes = []
        
    async def generate_strategy(
        self, 
        commodity: str,
        location: Dict[str, float],
        market_context: MarketContext,
        buyer_intent: BuyerIntent,
        farmer_profile: Dict[str, Any]
    ) -> NegotiationStrategy:
        """
        Generate comprehensive negotiation strategy
        
        Args:
            commodity: Commodity being negotiated
            location: Geographic location
            market_context: Current market conditions
            buyer_intent: Detected buyer intent
            farmer_profile: Farmer's profile and preferences
            
        Returns:
            NegotiationStrategy: Complete negotiation strategy
        """
        try:
            # Calculate recommended price range
            price_range = await self._calculate_price_range(market_context, buyer_intent, farmer_profile)
            
            # Select optimal tactics
            tactics = await self._select_tactics(market_context, buyer_intent)
            
            # Generate timing recommendation
            timing = await self._generate_timing_recommendation(market_context, buyer_intent)
            
            # Identify alternative options
            alternatives = await self._identify_alternatives(commodity, location, market_context)
            
            # Generate key arguments
            key_arguments = await self._generate_key_arguments(market_context, buyer_intent)
            
            # Create concession strategy
            concession_strategy = await self._create_concession_strategy(price_range, buyer_intent)
            
            # Assess risk level
            risk_level = await self._assess_risk_level(market_context, buyer_intent)
            
            # Calculate success probability
            success_probability = await self._calculate_success_probability(
                market_context, buyer_intent, tactics
            )
            
            # Calculate confidence
            confidence = await self._calculate_strategy_confidence(
                market_context, buyer_intent, farmer_profile
            )
            
            return NegotiationStrategy(
                recommended_price=price_range.optimal_price,
                price_range=price_range,
                tactics=tactics,
                timing=timing,
                alternatives=alternatives,
                key_arguments=key_arguments,
                concession_strategy=concession_strategy,
                risk_assessment=risk_level,
                success_probability=success_probability,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Strategy generation failed: {str(e)}")
            # Return fallback strategy
            return await self._generate_fallback_strategy(market_context.current_price)
    
    async def predict_outcome(
        self, 
        strategy: NegotiationStrategy, 
        market_context: MarketContext
    ) -> OutcomePrediction:
        """
        Predict negotiation outcome for given strategy
        
        Args:
            strategy: Proposed negotiation strategy
            market_context: Current market conditions
            
        Returns:
            OutcomePrediction: Predicted outcome with confidence
        """
        try:
            # Calculate success probability
            success_probability = strategy.success_probability
            
            # Predict final price
            expected_final_price = await self._predict_final_price(strategy, market_context)
            
            # Estimate negotiation duration
            negotiation_duration = await self._estimate_duration(strategy, market_context)
            
            # Predict farmer satisfaction
            farmer_satisfaction = await self._predict_satisfaction(strategy, market_context)
            
            # Identify success factors
            success_factors = await self._identify_success_factors(strategy, market_context)
            
            # Identify potential obstacles
            obstacles = await self._identify_obstacles(strategy, market_context)
            
            # Calculate prediction confidence
            confidence = await self._calculate_prediction_confidence(strategy, market_context)
            
            return OutcomePrediction(
                success_probability=success_probability,
                expected_final_price=expected_final_price,
                negotiation_duration=negotiation_duration,
                farmer_satisfaction_score=farmer_satisfaction,
                key_success_factors=success_factors,
                potential_obstacles=obstacles,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Outcome prediction failed: {str(e)}")
            # Return fallback prediction
            return OutcomePrediction(
                success_probability=0.6,
                expected_final_price=strategy.recommended_price * 0.95,
                negotiation_duration=15,
                farmer_satisfaction_score=3.5,
                key_success_factors=["Market knowledge", "Fair pricing"],
                potential_obstacles=["Price competition", "Quality concerns"],
                confidence=0.5
            )
    
    async def _calculate_price_range(
        self, 
        market_context: MarketContext, 
        buyer_intent: BuyerIntent,
        farmer_profile: Dict[str, Any]
    ) -> PriceRange:
        """Calculate optimal price range for negotiation"""
        current_price = market_context.current_price
        
        # Base price adjustments
        seasonal_adjustment = current_price * (market_context.seasonal_factor - 1)
        quality_adjustment = current_price * market_context.quality_premium
        
        # Market condition adjustments
        market_adjustment = 0
        if market_context.market_condition == MarketCondition.BULLISH:
            market_adjustment = current_price * 0.05  # 5% premium
        elif market_context.market_condition == MarketCondition.BEARISH:
            market_adjustment = current_price * -0.05  # 5% discount
        
        # Buyer intent adjustments
        urgency_adjustment = 0
        if buyer_intent.urgency == UrgencyLevel.HIGH:
            urgency_adjustment = current_price * 0.03  # 3% premium for urgent buyers
        elif buyer_intent.urgency == UrgencyLevel.LOW:
            urgency_adjustment = current_price * -0.02  # 2% discount for patient buyers
        
        # Price sensitivity adjustment
        sensitivity_adjustment = current_price * (0.05 - buyer_intent.price_sensitivity * 0.1)
        
        # Calculate base optimal price
        optimal_price = (current_price + seasonal_adjustment + quality_adjustment + 
                        market_adjustment + urgency_adjustment + sensitivity_adjustment)
        
        # Calculate range
        range_width = optimal_price * 0.1  # 10% range
        min_price = max(optimal_price - range_width, current_price * 0.85)  # Don't go below 85% of market
        max_price = optimal_price + range_width
        
        # Farmer's minimum price consideration
        farmer_min = farmer_profile.get('minimum_price', current_price * 0.9)
        min_price = max(min_price, farmer_min)
        
        # Ensure optimal price is within the range
        optimal_price = max(optimal_price, min_price)
        max_price = max(max_price, optimal_price)
        
        return PriceRange(
            min_price=min_price,
            max_price=max_price,
            optimal_price=optimal_price,
            confidence=0.8
        )
    
    async def _select_tactics(
        self, 
        market_context: MarketContext, 
        buyer_intent: BuyerIntent
    ) -> List[NegotiationTactic]:
        """Select optimal negotiation tactics"""
        tactics = []
        
        # Market-based tactics
        if market_context.market_condition == MarketCondition.BULLISH:
            tactics.append(NegotiationTactic.HOLD_FIRM)
        elif market_context.supply_level == "low":
            tactics.append(NegotiationTactic.TIME_PRESSURE)
        
        # Buyer intent-based tactics
        if buyer_intent.urgency == UrgencyLevel.HIGH:
            tactics.append(NegotiationTactic.TIME_PRESSURE)
        elif buyer_intent.quality_focus > 0.7:
            tactics.append(NegotiationTactic.QUALITY_EMPHASIS)
        elif buyer_intent.volume_requirement > 500:  # Large volume
            tactics.append(NegotiationTactic.VOLUME_DISCOUNT)
        
        # Negotiation style-based tactics
        if buyer_intent.negotiation_style == "aggressive":
            tactics.append(NegotiationTactic.COMPETITIVE_BIDDING)
        elif buyer_intent.negotiation_style == "collaborative":
            tactics.append(NegotiationTactic.GRADUAL_CONCESSION)
        
        # Default tactics if none selected
        if not tactics:
            tactics = [NegotiationTactic.GRADUAL_CONCESSION, NegotiationTactic.QUALITY_EMPHASIS]
        
        return tactics[:3]  # Limit to 3 tactics
    
    async def _generate_timing_recommendation(
        self, 
        market_context: MarketContext, 
        buyer_intent: BuyerIntent
    ) -> TimingRecommendation:
        """Generate timing recommendation for negotiation"""
        
        # Analyze market trends
        if market_context.price_trend == "increasing":
            optimal_timing = "immediate"
            price_prediction = "increase"
            wait_duration = None
        elif market_context.price_trend == "decreasing" and buyer_intent.urgency != UrgencyLevel.HIGH:
            optimal_timing = "wait_short"
            price_prediction = "decrease"
            wait_duration = 60  # 1 hour
        else:
            optimal_timing = "immediate"
            price_prediction = "stable"
            wait_duration = None
        
        # Adjust for buyer urgency
        if buyer_intent.urgency == UrgencyLevel.HIGH:
            optimal_timing = "immediate"
            wait_duration = None
        
        return TimingRecommendation(
            optimal_timing=optimal_timing,
            wait_duration=wait_duration,
            price_movement_prediction=price_prediction,
            confidence=0.7
        )
    
    async def _identify_alternatives(
        self, 
        commodity: str, 
        location: Dict[str, float], 
        market_context: MarketContext
    ) -> List[AlternativeOption]:
        """Identify alternative options for the farmer"""
        alternatives = []
        
        # Different buyer alternative
        if market_context.competition_level == "high":
            alternatives.append(AlternativeOption(
                option_type="different_buyer",
                description="Explore other buyers in the same mandi",
                expected_price=market_context.current_price * 1.02,
                time_to_execute=30,
                risk_level=RiskLevel.LOW,
                confidence=0.8
            ))
        
        # Different mandi alternative
        alternatives.append(AlternativeOption(
            option_type="different_mandi",
            description="Transport to nearby mandi with better prices",
            expected_price=market_context.current_price * 1.05 - market_context.transportation_cost,
            time_to_execute=120,
            risk_level=RiskLevel.MEDIUM,
            confidence=0.6
        ))
        
        # Storage alternative (if applicable)
        if market_context.price_trend == "increasing":
            alternatives.append(AlternativeOption(
                option_type="storage",
                description="Store commodity and sell later at higher price",
                expected_price=market_context.current_price * 1.08 - market_context.storage_cost,
                time_to_execute=1440,  # 24 hours
                risk_level=RiskLevel.HIGH,
                confidence=0.5
            ))
        
        return alternatives
    
    async def _generate_key_arguments(
        self, 
        market_context: MarketContext, 
        buyer_intent: BuyerIntent
    ) -> List[str]:
        """Generate key arguments for negotiation"""
        arguments = []
        
        # Quality-based arguments
        if buyer_intent.quality_focus > 0.6:
            arguments.append("Premium quality commodity with superior grade")
            arguments.append("Consistent quality maintained through proper farming practices")
        
        # Market-based arguments
        if market_context.price_trend == "increasing":
            arguments.append("Prices are trending upward in the market")
        
        if market_context.supply_level == "low":
            arguments.append("Limited supply available in the market")
        
        if market_context.demand_level == "high":
            arguments.append("High demand from multiple buyers")
        
        # Seasonal arguments
        if market_context.seasonal_factor > 1.05:
            arguments.append("Seasonal premium due to timing")
        
        # Festival demand
        if market_context.festival_demand:
            arguments.append("Increased demand due to upcoming festivals")
        
        # Transportation and costs
        arguments.append(f"Transportation costs factored at ₹{market_context.transportation_cost:.0f} per quintal")
        
        return arguments[:5]  # Limit to 5 key arguments
    
    async def _create_concession_strategy(
        self, 
        price_range: PriceRange, 
        buyer_intent: BuyerIntent
    ) -> Dict[str, Any]:
        """Create concession strategy"""
        strategy = {
            "initial_offer": price_range.max_price,
            "minimum_acceptable": price_range.min_price,
            "concession_steps": [],
            "concession_triggers": []
        }
        
        # Calculate concession steps
        total_concession = price_range.max_price - price_range.min_price
        num_steps = 3 if buyer_intent.negotiation_style == "collaborative" else 2
        
        step_size = total_concession / num_steps
        current_price = price_range.max_price
        
        for i in range(num_steps):
            current_price -= step_size
            strategy["concession_steps"].append({
                "step": i + 1,
                "price": current_price,
                "condition": f"After {(i + 1) * 5} minutes of negotiation"
            })
        
        # Concession triggers
        if buyer_intent.urgency == UrgencyLevel.HIGH:
            strategy["concession_triggers"].append("Buyer shows signs of walking away")
        
        if buyer_intent.alternative_sources > 2:
            strategy["concession_triggers"].append("Buyer mentions multiple alternatives")
        
        return strategy
    
    async def _assess_risk_level(
        self, 
        market_context: MarketContext, 
        buyer_intent: BuyerIntent
    ) -> RiskLevel:
        """Assess overall risk level of the negotiation"""
        risk_factors = 0
        
        # Market risks
        if market_context.market_condition == MarketCondition.VOLATILE:
            risk_factors += 1
        if market_context.price_trend == "decreasing":
            risk_factors += 1
        
        # Buyer risks
        if buyer_intent.alternative_sources > 3:
            risk_factors += 1
        if buyer_intent.urgency == UrgencyLevel.LOW:
            risk_factors += 1
        if buyer_intent.price_sensitivity > 0.8:
            risk_factors += 1
        
        if risk_factors >= 3:
            return RiskLevel.HIGH
        elif risk_factors >= 1:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    async def _calculate_success_probability(
        self, 
        market_context: MarketContext, 
        buyer_intent: BuyerIntent, 
        tactics: List[NegotiationTactic]
    ) -> float:
        """Calculate probability of successful negotiation"""
        base_probability = 0.6
        
        # Market factors
        if market_context.market_condition == MarketCondition.BULLISH:
            base_probability += 0.1
        elif market_context.market_condition == MarketCondition.BEARISH:
            base_probability -= 0.1
        
        # Supply/demand factors
        if market_context.supply_level == "low":
            base_probability += 0.05
        if market_context.demand_level == "high":
            base_probability += 0.05
        
        # Buyer intent factors
        if buyer_intent.urgency == UrgencyLevel.HIGH:
            base_probability += 0.1
        elif buyer_intent.urgency == UrgencyLevel.LOW:
            base_probability -= 0.05
        
        if buyer_intent.relationship_value > 0.7:
            base_probability += 0.1
        
        # Tactics effectiveness
        effective_tactics = [
            NegotiationTactic.QUALITY_EMPHASIS,
            NegotiationTactic.COMPETITIVE_BIDDING,
            NegotiationTactic.TIME_PRESSURE
        ]
        
        if any(tactic in tactics for tactic in effective_tactics):
            base_probability += 0.05
        
        return max(0.1, min(0.95, base_probability))
    
    async def _calculate_strategy_confidence(
        self, 
        market_context: MarketContext, 
        buyer_intent: BuyerIntent, 
        farmer_profile: Dict[str, Any]
    ) -> float:
        """Calculate confidence in the generated strategy"""
        confidence_factors = [
            market_context.timestamp is not None,  # Recent market data
            buyer_intent.confidence > 0.6,  # Good intent detection
            len(farmer_profile) > 2,  # Sufficient farmer profile
            market_context.current_price > 0,  # Valid price data
        ]
        
        base_confidence = sum(confidence_factors) / len(confidence_factors)
        
        # Adjust based on market volatility
        if market_context.market_condition == MarketCondition.VOLATILE:
            base_confidence *= 0.9
        
        return max(0.3, base_confidence)
    
    async def _generate_fallback_strategy(self, current_price: float) -> NegotiationStrategy:
        """Generate fallback strategy when main generation fails"""
        price_range = PriceRange(
            min_price=current_price * 0.95,
            max_price=current_price * 1.05,
            optimal_price=current_price,
            confidence=0.5
        )
        
        return NegotiationStrategy(
            recommended_price=current_price,
            price_range=price_range,
            tactics=[NegotiationTactic.GRADUAL_CONCESSION],
            timing=TimingRecommendation(
                optimal_timing="immediate",
                price_movement_prediction="stable",
                confidence=0.5
            ),
            alternatives=[],
            key_arguments=["Fair market price", "Quality commodity"],
            concession_strategy={"initial_offer": current_price * 1.05, "minimum_acceptable": current_price * 0.95},
            risk_assessment=RiskLevel.MEDIUM,
            success_probability=0.6,
            confidence=0.5
        )
    
    # Outcome prediction helper methods
    async def _predict_final_price(self, strategy: NegotiationStrategy, market_context: MarketContext) -> float:
        """Predict final negotiated price"""
        # Base prediction on strategy and market conditions
        base_price = strategy.recommended_price
        
        # Adjust based on market conditions
        if market_context.market_condition == MarketCondition.BULLISH:
            return base_price * 0.98  # Slight discount from recommended
        elif market_context.market_condition == MarketCondition.BEARISH:
            return base_price * 0.95  # Larger discount
        else:
            return base_price * 0.97  # Normal discount
    
    async def _estimate_duration(self, strategy: NegotiationStrategy, market_context: MarketContext) -> int:
        """Estimate negotiation duration in minutes"""
        base_duration = 15
        
        # Adjust based on tactics
        if NegotiationTactic.HOLD_FIRM in strategy.tactics:
            base_duration += 10
        if NegotiationTactic.COMPETITIVE_BIDDING in strategy.tactics:
            base_duration += 5
        
        # Adjust based on market volatility
        if market_context.market_condition == MarketCondition.VOLATILE:
            base_duration += 5
        
        return base_duration
    
    async def _predict_satisfaction(self, strategy: NegotiationStrategy, market_context: MarketContext) -> float:
        """Predict farmer satisfaction score (1-5)"""
        base_satisfaction = 3.5
        
        # Higher satisfaction if price is good
        if strategy.recommended_price > market_context.current_price:
            base_satisfaction += 0.5
        
        # Adjust based on success probability
        base_satisfaction += (strategy.success_probability - 0.5)
        
        return max(1.0, min(5.0, base_satisfaction))
    
    async def _identify_success_factors(self, strategy: NegotiationStrategy, market_context: MarketContext) -> List[str]:
        """Identify key success factors"""
        factors = ["Clear pricing strategy", "Market knowledge"]
        
        if market_context.supply_level == "low":
            factors.append("Limited supply advantage")
        
        if NegotiationTactic.QUALITY_EMPHASIS in strategy.tactics:
            factors.append("Quality differentiation")
        
        return factors
    
    async def _identify_obstacles(self, strategy: NegotiationStrategy, market_context: MarketContext) -> List[str]:
        """Identify potential obstacles"""
        obstacles = []
        
        if market_context.competition_level == "high":
            obstacles.append("High competition from other sellers")
        
        if market_context.price_trend == "decreasing":
            obstacles.append("Declining price trend")
        
        if strategy.risk_assessment == RiskLevel.HIGH:
            obstacles.append("High market volatility")
        
        return obstacles or ["Standard market competition"]
    
    async def _calculate_prediction_confidence(self, strategy: NegotiationStrategy, market_context: MarketContext) -> float:
        """Calculate confidence in outcome prediction"""
        return min(strategy.confidence, 0.8)  # Cap at 80% for predictions