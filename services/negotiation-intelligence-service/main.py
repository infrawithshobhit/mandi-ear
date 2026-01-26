"""
MANDI EAR™ Negotiation Intelligence Service
Main FastAPI application for AI-powered negotiation assistance
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import uvicorn

from market_context_analyzer import MarketContextAnalyzer
from buyer_intent_detector import BuyerIntentDetector
from negotiation_strategy_generator import NegotiationStrategyGenerator
from learning_engine import LearningEngine
from models import (
    MarketContext, BuyerIntent, NegotiationStrategy, 
    NegotiationSession, NegotiationOutcome, OutcomePrediction
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MANDI EAR™ Negotiation Intelligence Service",
    description="AI-powered negotiation assistance for farmers",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
market_analyzer = MarketContextAnalyzer()
intent_detector = BuyerIntentDetector()
strategy_generator = NegotiationStrategyGenerator()
learning_engine = LearningEngine()

# Request/Response models
class NegotiationRequest(BaseModel):
    commodity: str
    location: Dict[str, float]  # {"lat": float, "lng": float}
    farmer_id: str
    current_price_offer: Optional[float] = None
    conversation_data: Optional[str] = None

class StrategyRequest(BaseModel):
    commodity: str
    location: Dict[str, float]
    market_context: Dict[str, Any]
    buyer_intent: Dict[str, Any]
    farmer_profile: Dict[str, Any]

class OutcomeTrackingRequest(BaseModel):
    session_id: str
    final_price: float
    strategy_used: Dict[str, Any]
    success: bool
    farmer_satisfaction: int  # 1-5 scale

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "negotiation-intelligence"}

@app.post("/analyze-market-context")
async def analyze_market_context(request: NegotiationRequest):
    """Analyze current market context for negotiation"""
    try:
        context = await market_analyzer.analyze_market_context(
            commodity=request.commodity,
            location=request.location
        )
        return {"market_context": context.dict()}
    except Exception as e:
        logger.error(f"Market context analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect-buyer-intent")
async def detect_buyer_intent(request: NegotiationRequest):
    """Detect buyer intent from conversation data"""
    try:
        if not request.conversation_data:
            raise HTTPException(status_code=400, detail="Conversation data required")
        
        intent = await intent_detector.detect_buyer_intent(
            conversation_data=request.conversation_data
        )
        return {"buyer_intent": intent.dict()}
    except Exception as e:
        logger.error(f"Buyer intent detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-strategy")
async def generate_negotiation_strategy(request: StrategyRequest):
    """Generate negotiation strategy based on context and intent"""
    try:
        strategy = await strategy_generator.generate_strategy(
            commodity=request.commodity,
            location=request.location,
            market_context=MarketContext(**request.market_context),
            buyer_intent=BuyerIntent(**request.buyer_intent),
            farmer_profile=request.farmer_profile
        )
        return {"strategy": strategy.dict()}
    except Exception as e:
        logger.error(f"Strategy generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict-outcome")
async def predict_negotiation_outcome(request: StrategyRequest):
    """Predict negotiation outcome for given strategy"""
    try:
        prediction = await strategy_generator.predict_outcome(
            strategy=NegotiationStrategy(**request.buyer_intent),  # Simplified for now
            market_context=MarketContext(**request.market_context)
        )
        return {"prediction": prediction.dict()}
    except Exception as e:
        logger.error(f"Outcome prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/track-outcome")
async def track_negotiation_outcome(request: OutcomeTrackingRequest):
    """Track negotiation outcome for learning"""
    try:
        await learning_engine.learn_from_outcome(
            session_id=request.session_id,
            final_price=request.final_price,
            strategy_used=request.strategy_used,
            success=request.success,
            farmer_satisfaction=request.farmer_satisfaction
        )
        return {"status": "outcome_tracked"}
    except Exception as e:
        logger.error(f"Outcome tracking failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create-session")
async def create_negotiation_session(request: NegotiationRequest):
    """Create new negotiation session"""
    try:
        session_id = await learning_engine.create_session(
            farmer_id=request.farmer_id,
            commodity=request.commodity,
            location=request.location,
            initial_offer=request.current_price_offer or 0.0,
            conversation_data=request.conversation_data
        )
        return {"session_id": session_id}
    except Exception as e:
        logger.error(f"Session creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/strategy-recommendations/{commodity}")
async def get_strategy_recommendations(
    commodity: str,
    market_context: Dict[str, Any],
    buyer_intent: Dict[str, Any]
):
    """Get learned strategy recommendations"""
    try:
        recommendations = await learning_engine.get_strategy_recommendations(
            commodity=commodity,
            market_context=MarketContext(**market_context),
            buyer_intent=BuyerIntent(**buyer_intent)
        )
        return {"recommendations": recommendations}
    except Exception as e:
        logger.error(f"Strategy recommendations failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/performance-analytics")
async def get_performance_analytics(
    farmer_id: Optional[str] = None,
    commodity: Optional[str] = None,
    time_period_days: int = 30
):
    """Get performance analytics"""
    try:
        analytics = await learning_engine.get_performance_analytics(
            farmer_id=farmer_id,
            commodity=commodity,
            time_period_days=time_period_days
        )
        return {"analytics": analytics}
    except Exception as e:
        logger.error(f"Performance analytics failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/negotiation-session/{session_id}")
async def get_negotiation_session(session_id: str):
    """Get negotiation session details"""
    try:
        session = await learning_engine.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"session": session.dict()}
    except Exception as e:
        logger.error(f"Session retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)