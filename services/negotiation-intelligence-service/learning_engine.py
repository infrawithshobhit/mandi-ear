"""
Learning Engine for Negotiation Intelligence Service
Implements machine learning pipeline for strategy improvement and outcome tracking
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import statistics
from collections import defaultdict, deque
import uuid

from models import (
    NegotiationSession, NegotiationOutcome, LearningData,
    NegotiationStrategy, MarketContext, BuyerIntent,
    NegotiationTactic, RiskLevel, UrgencyLevel
)

logger = logging.getLogger(__name__)

class LearningEngine:
    """Machine learning engine for negotiation strategy improvement"""
    
    def __init__(self):
        # In-memory storage for demo (in production, use database)
        self.sessions: Dict[str, NegotiationSession] = {}
        self.outcomes: List[NegotiationOutcome] = []
        self.learning_data: Dict[str, LearningData] = {}
        
        # Learning parameters
        self.min_samples_for_learning = 5
        self.learning_window_days = 30
        self.success_threshold = 0.7
        
        # Performance tracking
        self.strategy_performance: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'success_count': 0,
            'total_count': 0,
            'avg_price_improvement': 0.0,
            'avg_satisfaction': 0.0,
            'last_updated': datetime.now()
        })
        
        # Pattern recognition
        self.successful_patterns: List[Dict[str, Any]] = []
        self.failed_patterns: List[Dict[str, Any]] = []
        
    def reset_state(self):
        """Reset all internal state - useful for testing"""
        self.sessions.clear()
        self.outcomes.clear()
        self.learning_data.clear()
        self.strategy_performance.clear()
        self.successful_patterns.clear()
        self.failed_patterns.clear()
        
    async def learn_from_outcome(
        self,
        session_id: str,
        final_price: float,
        strategy_used: Dict[str, Any],
        success: bool,
        farmer_satisfaction: int
    ) -> None:
        """
        Learn from negotiation outcome to improve future strategies
        
        Args:
            session_id: Unique session identifier
            final_price: Final negotiated price
            strategy_used: Strategy that was used
            success: Whether negotiation was successful
            farmer_satisfaction: Farmer satisfaction score (1-5)
        """
        try:
            # Get the session
            session = self.sessions.get(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found for learning")
                return
            
            # Create outcome record
            outcome = NegotiationOutcome(
                session_id=session_id,
                final_price=final_price,
                success=success,
                farmer_satisfaction=farmer_satisfaction,
                strategy_effectiveness=self._calculate_strategy_effectiveness(
                    session, final_price, success, farmer_satisfaction
                ),
                time_to_close=self._calculate_time_to_close(session),
                concessions_made=self._extract_concessions(session, final_price),
                key_factors=self._identify_key_factors(session, success),
                lessons_learned=self._extract_lessons_learned(session, success)
            )
            
            # Store outcome
            self.outcomes.append(outcome)
            
            # Update session with outcome
            session.final_price = final_price
            session.success = success
            session.farmer_satisfaction = farmer_satisfaction
            session.end_time = datetime.now()
            session.lessons_learned = outcome.lessons_learned
            
            # Update strategy performance tracking
            await self._update_strategy_performance(session, outcome)
            
            # Extract patterns for learning
            await self._extract_patterns(session, outcome)
            
            # Update learning data
            await self._update_learning_data(session, outcome)
            
            # Trigger competitive bidding learning if applicable
            if self._is_competitive_scenario(session):
                await self._learn_competitive_bidding(session, outcome)
            
            logger.info(f"Learning completed for session {session_id}")
            
        except Exception as e:
            logger.error(f"Learning from outcome failed: {str(e)}")
    
    async def get_session(self, session_id: str) -> Optional[NegotiationSession]:
        """Get negotiation session by ID"""
        return self.sessions.get(session_id)
    
    async def create_session(
        self,
        farmer_id: str,
        commodity: str,
        location: Dict[str, float],
        initial_offer: float,
        market_context: Optional[MarketContext] = None,
        buyer_intent: Optional[BuyerIntent] = None,
        conversation_data: Optional[str] = None
    ) -> str:
        """Create new negotiation session"""
        session_id = str(uuid.uuid4())
        
        session = NegotiationSession(
            session_id=session_id,
            farmer_id=farmer_id,
            commodity=commodity,
            location={
                "latitude": location["lat"],
                "longitude": location["lng"]
            },
            start_time=datetime.now(),
            initial_offer=initial_offer,
            market_context=market_context,
            buyer_intent=buyer_intent,
            conversation_data=conversation_data
        )
        
        self.sessions[session_id] = session
        return session_id
    
    async def get_strategy_recommendations(
        self,
        commodity: str,
        market_context: MarketContext,
        buyer_intent: BuyerIntent
    ) -> Dict[str, Any]:
        """
        Get strategy recommendations based on learned patterns
        
        Args:
            commodity: Commodity being negotiated
            market_context: Current market conditions
            buyer_intent: Detected buyer intent
            
        Returns:
            Dict with strategy recommendations and confidence scores
        """
        try:
            # Find similar historical scenarios
            similar_scenarios = await self._find_similar_scenarios(
                commodity, market_context, buyer_intent
            )
            
            # Always return consistent structure
            if not similar_scenarios:
                return {
                    "recommendations": [],
                    "confidence": 0.3,  # Fixed low confidence for no data
                    "reason": "No similar historical scenarios found",
                    "similar_scenarios_count": 0,
                    "success_rate": 0.0
                }
            
            # Analyze successful patterns
            successful_tactics = await self._analyze_successful_tactics(similar_scenarios)
            
            # Generate recommendations
            recommendations = await self._generate_learned_recommendations(
                successful_tactics, market_context, buyer_intent
            )
            
            # Calculate deterministic confidence
            confidence = self._calculate_recommendation_confidence(similar_scenarios)
            
            return {
                "recommendations": recommendations,
                "confidence": confidence,
                "similar_scenarios_count": len(similar_scenarios),
                "success_rate": self._calculate_success_rate(similar_scenarios)
            }
            
        except Exception as e:
            logger.error(f"Strategy recommendation generation failed: {str(e)}")
            return {
                "recommendations": [],
                "confidence": 0.3,
                "reason": f"Error: {str(e)}",
                "similar_scenarios_count": 0,
                "success_rate": 0.0
            }
    
    async def get_performance_analytics(
        self,
        farmer_id: Optional[str] = None,
        commodity: Optional[str] = None,
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """Get performance analytics for learning insights"""
        try:
            cutoff_date = datetime.now() - timedelta(days=time_period_days)
            
            # Filter relevant outcomes
            relevant_outcomes = [
                outcome for outcome in self.outcomes
                if outcome.timestamp >= cutoff_date
            ]
            
            if farmer_id:
                relevant_sessions = [
                    session for session in self.sessions.values()
                    if session.farmer_id.startswith(farmer_id)  # Use startswith for partial matching
                ]
                relevant_session_ids = [s.session_id for s in relevant_sessions]
                relevant_outcomes = [
                    outcome for outcome in relevant_outcomes
                    if outcome.session_id in relevant_session_ids
                ]
            
            if commodity:
                relevant_sessions = [
                    session for session in self.sessions.values()
                    if session.commodity == commodity
                ]
                relevant_session_ids = [s.session_id for s in relevant_sessions]
                relevant_outcomes = [
                    outcome for outcome in relevant_outcomes
                    if outcome.session_id in relevant_session_ids
                ]
            
            if not relevant_outcomes:
                return {
                    "total_negotiations": 0,
                    "success_rate": 0.0,
                    "avg_price_improvement": 0.0,
                    "avg_satisfaction": 0.0,
                    "top_tactics": [],
                    "lessons_learned": []
                }
            
            # Calculate analytics
            total_negotiations = len(relevant_outcomes)
            successful_negotiations = sum(1 for o in relevant_outcomes if o.success)
            success_rate = successful_negotiations / total_negotiations
            
            avg_price_improvement = statistics.mean([
                o.strategy_effectiveness for o in relevant_outcomes
            ])
            
            avg_satisfaction = statistics.mean([
                o.farmer_satisfaction for o in relevant_outcomes
            ])
            
            # Analyze top tactics
            top_tactics = await self._analyze_top_tactics(relevant_outcomes)
            
            # Collect lessons learned
            all_lessons = []
            for outcome in relevant_outcomes:
                all_lessons.extend(outcome.lessons_learned)
            
            # Get most common lessons
            lesson_counts = defaultdict(int)
            for lesson in all_lessons:
                lesson_counts[lesson] += 1
            
            top_lessons = sorted(
                lesson_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            return {
                "total_negotiations": total_negotiations,
                "success_rate": success_rate,
                "avg_price_improvement": avg_price_improvement,
                "avg_satisfaction": avg_satisfaction,
                "top_tactics": top_tactics,
                "lessons_learned": [lesson for lesson, count in top_lessons],
                "time_period_days": time_period_days
            }
            
        except Exception as e:
            logger.error(f"Performance analytics generation failed: {str(e)}")
            return {
                "error": str(e),
                "total_negotiations": 0,
                "success_rate": 0.0
            }
    
    # Private helper methods
    
    def _calculate_strategy_effectiveness(
        self,
        session: NegotiationSession,
        final_price: float,
        success: bool,
        farmer_satisfaction: int
    ) -> float:
        """Calculate how effective the strategy was"""
        if not success:
            return 0.0
        
        # Base effectiveness on price improvement
        initial_offer = session.initial_offer
        price_improvement = (final_price - initial_offer) / initial_offer
        
        # Adjust for satisfaction
        satisfaction_factor = farmer_satisfaction / 5.0
        
        # Combine factors
        effectiveness = (price_improvement * 0.7) + (satisfaction_factor * 0.3)
        
        return max(0.0, min(1.0, effectiveness))
    
    def _calculate_time_to_close(self, session: NegotiationSession) -> int:
        """Calculate time to close negotiation in minutes"""
        if session.end_time and session.start_time:
            delta = session.end_time - session.start_time
            return int(delta.total_seconds() / 60)
        return 0
    
    def _extract_concessions(
        self,
        session: NegotiationSession,
        final_price: float
    ) -> List[Dict[str, Any]]:
        """Extract concessions made during negotiation"""
        concessions = []
        
        if session.strategy_used and session.initial_offer:
            initial_offer = session.initial_offer
            price_difference = initial_offer - final_price
            
            if price_difference > 0:
                concessions.append({
                    "type": "price_reduction",
                    "amount": price_difference,
                    "percentage": (price_difference / initial_offer) * 100
                })
        
        return concessions
    
    def _identify_key_factors(
        self,
        session: NegotiationSession,
        success: bool
    ) -> List[str]:
        """Identify key factors that influenced the outcome"""
        factors = []
        
        if session.market_context:
            if session.market_context.market_condition.value == "bullish":
                factors.append("Bullish market conditions")
            elif session.market_context.supply_level == "low":
                factors.append("Low supply levels")
            elif session.market_context.demand_level == "high":
                factors.append("High demand levels")
        
        if session.buyer_intent:
            if session.buyer_intent.urgency.value == "high":
                factors.append("High buyer urgency")
            elif session.buyer_intent.price_sensitivity > 0.7:
                factors.append("High price sensitivity")
            elif session.buyer_intent.quality_focus > 0.7:
                factors.append("Quality-focused buyer")
        
        if success:
            factors.append("Successful negotiation")
        else:
            factors.append("Failed negotiation")
        
        return factors
    
    def _extract_lessons_learned(
        self,
        session: NegotiationSession,
        success: bool
    ) -> List[str]:
        """Extract lessons learned from the negotiation"""
        lessons = []
        
        if success:
            lessons.append("Negotiation was successful")
            if session.strategy_used:
                lessons.append("Strategy was effective for this scenario")
            
            if session.buyer_intent and session.buyer_intent.urgency.value == "high":
                lessons.append("High urgency buyers respond well to time pressure")
            
            if session.market_context and session.market_context.competition_level == "high":
                lessons.append("Competitive markets require firm pricing")
        else:
            lessons.append("Negotiation failed - strategy needs adjustment")
            lessons.append("Strategy needs adjustment for similar scenarios")
            
            if session.buyer_intent and session.buyer_intent.price_sensitivity > 0.8:
                lessons.append("Highly price-sensitive buyers need more flexible pricing")
        
        # Always ensure at least one lesson
        if not lessons:
            lessons.append("General negotiation experience gained")
        
        return lessons
    
    async def _update_strategy_performance(
        self,
        session: NegotiationSession,
        outcome: NegotiationOutcome
    ) -> None:
        """Update strategy performance tracking"""
        if not session.strategy_used:
            return
        
        # Create strategy key
        strategy_key = self._create_strategy_key(session.strategy_used)
        
        # Update performance metrics
        perf = self.strategy_performance[strategy_key]
        perf['total_count'] += 1
        
        if outcome.success:
            perf['success_count'] += 1
        
        # Update averages
        perf['avg_price_improvement'] = (
            (perf['avg_price_improvement'] * (perf['total_count'] - 1) + 
             outcome.strategy_effectiveness) / perf['total_count']
        )
        
        perf['avg_satisfaction'] = (
            (perf['avg_satisfaction'] * (perf['total_count'] - 1) + 
             outcome.farmer_satisfaction) / perf['total_count']
        )
        
        perf['last_updated'] = datetime.now()
    
    async def _extract_patterns(
        self,
        session: NegotiationSession,
        outcome: NegotiationOutcome
    ) -> None:
        """Extract patterns for machine learning"""
        pattern = {
            'commodity': session.commodity,
            'market_context': session.market_context.model_dump() if session.market_context else None,
            'buyer_intent': session.buyer_intent.model_dump() if session.buyer_intent else None,
            'strategy_used': session.strategy_used,
            'outcome': outcome.model_dump(),
            'timestamp': datetime.now()
        }
        
        if outcome.success:
            self.successful_patterns.append(pattern)
            # Keep only recent successful patterns
            if len(self.successful_patterns) > 100:
                self.successful_patterns = self.successful_patterns[-100:]
        else:
            self.failed_patterns.append(pattern)
            # Keep only recent failed patterns
            if len(self.failed_patterns) > 50:
                self.failed_patterns = self.failed_patterns[-50:]
    
    async def _update_learning_data(
        self,
        session: NegotiationSession,
        outcome: NegotiationOutcome
    ) -> None:
        """Update aggregated learning data"""
        commodity = session.commodity
        
        if commodity not in self.learning_data:
            self.learning_data[commodity] = LearningData(
                commodity=commodity,
                market_conditions={},
                strategy_used={},
                outcome={},
                success_rate=0.0,
                average_price_improvement=0.0,
                pattern_insights=[]
            )
        
        learning_data = self.learning_data[commodity]
        
        # Update success rate and price improvement
        commodity_outcomes = [
            o for o in self.outcomes
            if self.sessions.get(o.session_id, {}).commodity == commodity
        ]
        
        if commodity_outcomes:
            success_count = sum(1 for o in commodity_outcomes if o.success)
            learning_data.success_rate = success_count / len(commodity_outcomes)
            
            learning_data.average_price_improvement = statistics.mean([
                o.strategy_effectiveness for o in commodity_outcomes
            ])
        
        learning_data.updated_at = datetime.now()
    
    def _is_competitive_scenario(self, session: NegotiationSession) -> bool:
        """Check if this was a competitive bidding scenario"""
        if not session.market_context or not session.buyer_intent:
            return False
        
        return (session.market_context.competition_level == "high" or
                session.buyer_intent.alternative_sources > 2)
    
    async def _learn_competitive_bidding(
        self,
        session: NegotiationSession,
        outcome: NegotiationOutcome
    ) -> None:
        """Learn from competitive bidding scenarios"""
        if outcome.success:
            # Record successful competitive bidding tactics
            competitive_lesson = f"Competitive bidding successful with {session.strategy_used}"
            if competitive_lesson not in outcome.lessons_learned:
                outcome.lessons_learned.append(competitive_lesson)
        else:
            # Record failed competitive bidding attempts
            competitive_lesson = "Competitive bidding failed - consider alternative approaches"
            if competitive_lesson not in outcome.lessons_learned:
                outcome.lessons_learned.append(competitive_lesson)
    
    async def _find_similar_scenarios(
        self,
        commodity: str,
        market_context: MarketContext,
        buyer_intent: BuyerIntent
    ) -> List[NegotiationSession]:
        """Find similar historical scenarios for learning"""
        similar_sessions = []
        
        for session in self.sessions.values():
            if not session.market_context or not session.buyer_intent:
                continue
            
            # Check commodity match
            if session.commodity != commodity:
                continue
            
            # Calculate similarity score
            similarity_score = self._calculate_similarity_score(
                session.market_context, session.buyer_intent,
                market_context, buyer_intent
            )
            
            if similarity_score > 0.6:  # 60% similarity threshold
                similar_sessions.append(session)
        
        return similar_sessions
    
    def _calculate_similarity_score(
        self,
        hist_market: MarketContext,
        hist_buyer: BuyerIntent,
        curr_market: MarketContext,
        curr_buyer: BuyerIntent
    ) -> float:
        """Calculate similarity score between scenarios"""
        score = 0.0
        total_factors = 0
        
        # Market context similarity
        if hist_market.market_condition == curr_market.market_condition:
            score += 0.2
        total_factors += 0.2
        
        if hist_market.supply_level == curr_market.supply_level:
            score += 0.15
        total_factors += 0.15
        
        if hist_market.demand_level == curr_market.demand_level:
            score += 0.15
        total_factors += 0.15
        
        if hist_market.competition_level == curr_market.competition_level:
            score += 0.1
        total_factors += 0.1
        
        # Buyer intent similarity
        if hist_buyer.urgency == curr_buyer.urgency:
            score += 0.15
        total_factors += 0.15
        
        if hist_buyer.negotiation_style == curr_buyer.negotiation_style:
            score += 0.1
        total_factors += 0.1
        
        # Price sensitivity similarity (within 0.2 range)
        if abs(hist_buyer.price_sensitivity - curr_buyer.price_sensitivity) <= 0.2:
            score += 0.1
        total_factors += 0.1
        
        # Quality focus similarity (within 0.2 range)
        if abs(hist_buyer.quality_focus - curr_buyer.quality_focus) <= 0.2:
            score += 0.05
        total_factors += 0.05
        
        return score / total_factors if total_factors > 0 else 0.0
    
    async def _analyze_successful_tactics(
        self,
        similar_scenarios: List[NegotiationSession]
    ) -> Dict[str, Any]:
        """Analyze successful tactics from similar scenarios"""
        successful_tactics = defaultdict(int)
        total_successful = 0
        
        for session in similar_scenarios:
            if session.success and session.strategy_used:
                total_successful += 1
                # Extract tactics from strategy
                tactics = session.strategy_used.get('tactics', [])
                for tactic in tactics:
                    successful_tactics[tactic] += 1
        
        # Calculate success rates for each tactic
        tactic_success_rates = {}
        for tactic, count in successful_tactics.items():
            tactic_success_rates[tactic] = count / total_successful if total_successful > 0 else 0
        
        return {
            'successful_tactics': dict(successful_tactics),
            'tactic_success_rates': tactic_success_rates,
            'total_successful_scenarios': total_successful
        }
    
    async def _generate_learned_recommendations(
        self,
        successful_tactics: Dict[str, Any],
        market_context: MarketContext,
        buyer_intent: BuyerIntent
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on learned patterns"""
        recommendations = []
        
        tactic_success_rates = successful_tactics.get('tactic_success_rates', {})
        
        # Sort tactics by success rate
        sorted_tactics = sorted(
            tactic_success_rates.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for tactic, success_rate in sorted_tactics[:3]:  # Top 3 tactics
            recommendations.append({
                'tactic': tactic,
                'success_rate': success_rate,
                'confidence': min(success_rate * 1.2, 1.0),  # Boost confidence slightly
                'reason': f"This tactic has {success_rate:.1%} success rate in similar scenarios"
            })
        
        return recommendations
    
    def _calculate_recommendation_confidence(
        self,
        similar_scenarios: List[NegotiationSession]
    ) -> float:
        """Calculate confidence in recommendations based on data quality"""
        if len(similar_scenarios) < self.min_samples_for_learning:
            return 0.3  # Low confidence without sufficient data
        
        # Base confidence on number of similar scenarios
        base_confidence = min(len(similar_scenarios) / 20, 0.8)  # Max 80% base confidence
        
        # Adjust for recency of data
        recent_scenarios = [
            s for s in similar_scenarios
            if s.start_time >= datetime.now() - timedelta(days=self.learning_window_days)
        ]
        
        if not recent_scenarios:
            return 0.3  # Low confidence if no recent data
        
        recency_factor = len(recent_scenarios) / len(similar_scenarios)
        
        return base_confidence * (0.7 + 0.3 * recency_factor)
    
    def _calculate_success_rate(self, similar_scenarios: List[NegotiationSession]) -> float:
        """Calculate success rate for similar scenarios"""
        if not similar_scenarios:
            return 0.0
        
        successful_count = sum(1 for s in similar_scenarios if s.success)
        return successful_count / len(similar_scenarios)
    
    async def _analyze_top_tactics(self, outcomes: List[NegotiationOutcome]) -> List[Dict[str, Any]]:
        """Analyze top performing tactics"""
        tactic_performance = defaultdict(lambda: {'success': 0, 'total': 0, 'avg_satisfaction': 0.0})
        
        for outcome in outcomes:
            session = self.sessions.get(outcome.session_id)
            if session and session.strategy_used:
                tactics = session.strategy_used.get('tactics', [])
                for tactic in tactics:
                    tactic_performance[tactic]['total'] += 1
                    if outcome.success:
                        tactic_performance[tactic]['success'] += 1
                    
                    # Update average satisfaction
                    current_avg = tactic_performance[tactic]['avg_satisfaction']
                    total = tactic_performance[tactic]['total']
                    tactic_performance[tactic]['avg_satisfaction'] = (
                        (current_avg * (total - 1) + outcome.farmer_satisfaction) / total
                    )
        
        # Calculate success rates and sort
        top_tactics = []
        for tactic, perf in tactic_performance.items():
            if perf['total'] >= 3:  # Minimum sample size
                success_rate = perf['success'] / perf['total']
                top_tactics.append({
                    'tactic': tactic,
                    'success_rate': success_rate,
                    'avg_satisfaction': perf['avg_satisfaction'],
                    'sample_size': perf['total']
                })
        
        return sorted(top_tactics, key=lambda x: x['success_rate'], reverse=True)[:5]
    
    def _create_strategy_key(self, strategy_used: Dict[str, Any]) -> str:
        """Create a key for strategy performance tracking"""
        tactics = strategy_used.get('tactics', [])
        tactics_str = '_'.join(sorted(tactics)) if tactics else 'no_tactics'
        return f"strategy_{tactics_str}"