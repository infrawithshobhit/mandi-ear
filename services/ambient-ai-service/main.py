"""
MANDI EAR™ Ambient AI Service
Processes ambient audio to extract market intelligence
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import structlog
from typing import List, Dict, Any
import asyncio
from audio_processor import AudioProcessor, AudioSegment
from conversation_analyzer import ConversationAnalyzer, ConversationAnalysis
from realtime_processor import RealTimeDataProcessor, MarketIntelligenceData, GeoLocation

logger = structlog.get_logger()

app = FastAPI(
    title="MANDI EAR™ Ambient AI Service",
    description="Real-time audio processing and conversation extraction",
    version="1.0.0"
)

# Initialize processors
audio_processor = AudioProcessor()
conversation_analyzer = ConversationAnalyzer()
realtime_processor = RealTimeDataProcessor()

class TextAnalysisRequest(BaseModel):
    text: str

class RealTimeProcessingRequest(BaseModel):
    text: str
    location: Optional[Dict[str, Any]] = None
    segment_id: Optional[str] = None
    speaker_id: Optional[str] = None

class WeightedPriceRequest(BaseModel):
    commodity: str

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Ambient AI Service",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/process-audio")
async def process_audio(audio_file: UploadFile = File(...)):
    """
    Process uploaded audio file through the ambient AI pipeline
    
    Args:
        audio_file: Uploaded audio file
        
    Returns:
        Processed audio segments with metadata
    """
    try:
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Read audio data
        audio_data = await audio_file.read()
        
        # Process audio through pipeline
        segments = audio_processor.process_audio_stream(audio_data)
        
        # Convert segments to JSON-serializable format
        segments_data = []
        for segment in segments:
            segment_data = {
                "id": segment.id,
                "start_time": segment.start_time,
                "end_time": segment.end_time,
                "duration": segment.end_time - segment.start_time,
                "speaker_id": segment.speaker_id,
                "quality": segment.quality.value,
                "noise_level": segment.noise_level,
                "confidence": segment.confidence,
                "sample_rate": segment.sample_rate
            }
            segments_data.append(segment_data)
        
        logger.info("Audio processing completed", 
                   filename=audio_file.filename,
                   segments_count=len(segments_data))
        
        return {
            "status": "success",
            "filename": audio_file.filename,
            "segments_count": len(segments_data),
            "total_duration": sum(s["duration"] for s in segments_data),
            "average_confidence": sum(s["confidence"] for s in segments_data) / len(segments_data) if segments_data else 0,
            "segments": segments_data
        }
        
    except Exception as e:
        logger.error("Audio processing failed", error=str(e), filename=audio_file.filename)
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")

@app.post("/process-audio-stream")
async def process_audio_stream(audio_data: bytes):
    """
    Process raw audio stream data
    
    Args:
        audio_data: Raw audio bytes
        
    Returns:
        Processed audio segments
    """
    try:
        # Process audio through pipeline
        segments = audio_processor.process_audio_stream(audio_data)
        
        # Convert to response format
        segments_data = []
        for segment in segments:
            segment_data = {
                "id": segment.id,
                "start_time": segment.start_time,
                "end_time": segment.end_time,
                "duration": segment.end_time - segment.start_time,
                "speaker_id": segment.speaker_id,
                "quality": segment.quality.value,
                "noise_level": segment.noise_level,
                "confidence": segment.confidence
            }
            segments_data.append(segment_data)
        
        return {
            "status": "success",
            "segments_count": len(segments_data),
            "segments": segments_data
        }
        
    except Exception as e:
        logger.error("Audio stream processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Audio stream processing failed: {str(e)}")

@app.post("/analyze-text")
async def analyze_text(request: TextAnalysisRequest):
    """
    Analyze text for market intelligence extraction
    
    Args:
        request: Text analysis request containing the text to analyze
        
    Returns:
        Conversation analysis with extracted entities and intent
    """
    try:
        # Analyze conversation
        analysis = conversation_analyzer.analyze_conversation(request.text)
        
        # Convert to JSON-serializable format
        result = {
            "status": "success",
            "text": analysis.text,
            "intent": {
                "type": analysis.intent.value,
                "confidence": analysis.intent_confidence
            },
            "commodity": {
                "type": analysis.commodity.value if analysis.commodity else None,
                "confidence": analysis.commodity_confidence
            } if analysis.commodity else None,
            "price": {
                "amount": analysis.price.amount,
                "currency": analysis.price.currency,
                "unit": analysis.price.unit,
                "confidence": analysis.price.confidence
            } if analysis.price else None,
            "quantity": {
                "amount": analysis.quantity.amount,
                "unit": analysis.quantity.unit,
                "confidence": analysis.quantity.confidence
            } if analysis.quantity else None,
            "location": {
                "name": analysis.location.name,
                "type": analysis.location.type,
                "confidence": analysis.location.confidence
            } if analysis.location else None,
            "entities": [
                {
                    "type": entity.entity_type,
                    "value": entity.value,
                    "confidence": entity.confidence,
                    "start_pos": entity.start_pos,
                    "end_pos": entity.end_pos
                }
                for entity in analysis.entities
            ],
            "overall_confidence": analysis.overall_confidence
        }
        
        logger.info("Text analysis completed", 
                   text_length=len(request.text),
                   intent=analysis.intent.value,
                   entities_count=len(analysis.entities))
        
        return result
        
    except Exception as e:
        logger.error("Text analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Text analysis failed: {str(e)}")

@app.post("/extract-market-intelligence")
async def extract_market_intelligence(audio_file: UploadFile = File(...)):
    """
    Complete pipeline: Process audio and extract market intelligence
    
    Args:
        audio_file: Uploaded audio file
        
    Returns:
        Complete market intelligence analysis
    """
    try:
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Read audio data
        audio_data = await audio_file.read()
        
        # Process audio through pipeline
        segments = audio_processor.process_audio_stream(audio_data)
        
        # For demonstration, analyze a sample text (in real implementation, 
        # this would use speech-to-text on the audio segments)
        sample_conversations = [
            "I want to sell 100 kg wheat at ₹2000 per quintal in Delhi mandi",
            "Looking to buy onions, what is the current rate?",
            "Have 50 bags of rice available for ₹1800 per quintal"
        ]
        
        intelligence_results = []
        
        # Analyze each sample conversation (or in real implementation, transcribed audio)
        for i, text in enumerate(sample_conversations[:len(segments)]):
            analysis = conversation_analyzer.analyze_conversation(text)
            
            intelligence_result = {
                "segment_id": segments[i].id if i < len(segments) else f"sample_{i}",
                "text": text,
                "audio_confidence": segments[i].confidence if i < len(segments) else 0.8,
                "analysis": {
                    "intent": {
                        "type": analysis.intent.value,
                        "confidence": analysis.intent_confidence
                    },
                    "commodity": {
                        "type": analysis.commodity.value if analysis.commodity else None,
                        "confidence": analysis.commodity_confidence
                    } if analysis.commodity else None,
                    "price": {
                        "amount": analysis.price.amount,
                        "currency": analysis.price.currency,
                        "unit": analysis.price.unit,
                        "confidence": analysis.price.confidence
                    } if analysis.price else None,
                    "quantity": {
                        "amount": analysis.quantity.amount,
                        "unit": analysis.quantity.unit,
                        "confidence": analysis.quantity.confidence
                    } if analysis.quantity else None,
                    "location": {
                        "name": analysis.location.name,
                        "type": analysis.location.type,
                        "confidence": analysis.location.confidence
                    } if analysis.location else None,
                    "overall_confidence": analysis.overall_confidence
                }
            }
            intelligence_results.append(intelligence_result)
        
        logger.info("Market intelligence extraction completed", 
                   filename=audio_file.filename,
                   segments_processed=len(intelligence_results))
        
        return {
            "status": "success",
            "filename": audio_file.filename,
            "audio_segments_count": len(segments),
            "intelligence_extractions": len(intelligence_results),
            "results": intelligence_results
        }
        
    except Exception as e:
        logger.error("Market intelligence extraction failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Market intelligence extraction failed: {str(e)}")

@app.post("/process-realtime")
async def process_realtime_data(request: RealTimeProcessingRequest):
    """
    Process conversation text through real-time pipeline with metadata assignment
    
    Args:
        request: Real-time processing request with text and optional metadata
        
    Returns:
        Processed market intelligence with timestamps and geo-tags
    """
    try:
        # Analyze conversation first
        analysis = conversation_analyzer.analyze_conversation(request.text)
        
        # Prepare raw data for real-time processing
        raw_data = {
            "commodity": analysis.commodity.value if analysis.commodity else None,
            "price": analysis.price.amount if analysis.price else None,
            "quantity": analysis.quantity.amount if analysis.quantity else None,
            "intent": analysis.intent.value,
            "confidence": analysis.overall_confidence,
            "segment_id": request.segment_id or "manual_input",
            "speaker_id": request.speaker_id,
            "timestamp": None  # Will be assigned by processor
        }
        
        # Process through real-time pipeline
        intelligence_data = await realtime_processor.process_market_intelligence(
            raw_data, 
            location_hint=request.location
        )
        
        # Convert to JSON-serializable format
        result = {
            "status": "success",
            "data": {
                "id": intelligence_data.id,
                "commodity": intelligence_data.commodity,
                "price": intelligence_data.price,
                "quantity": intelligence_data.quantity,
                "intent": intelligence_data.intent,
                "confidence": intelligence_data.confidence,
                "location": {
                    "latitude": intelligence_data.location.latitude,
                    "longitude": intelligence_data.location.longitude,
                    "accuracy": intelligence_data.location.accuracy,
                    "source": intelligence_data.location.source,
                    "timestamp": intelligence_data.location.timestamp.isoformat()
                } if intelligence_data.location else None,
                "timestamp": intelligence_data.timestamp.isoformat(),
                "processing_time": intelligence_data.processing_time,
                "source_segment_id": intelligence_data.source_segment_id,
                "speaker_id": intelligence_data.speaker_id,
                "metadata": intelligence_data.metadata
            }
        }
        
        logger.info("Real-time processing completed", 
                   id=intelligence_data.id,
                   processing_time=intelligence_data.processing_time)
        
        return result
        
    except Exception as e:
        logger.error("Real-time processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Real-time processing failed: {str(e)}")

@app.get("/weighted-price/{commodity}")
async def get_weighted_price(commodity: str):
    """
    Get weighted average price for a commodity
    
    Args:
        commodity: Commodity name
        
    Returns:
        Weighted price calculation with confidence and data points
    """
    try:
        price_data = realtime_processor.get_weighted_price(commodity)
        
        logger.info("Weighted price retrieved", 
                   commodity=commodity,
                   price=price_data["weighted_price"],
                   confidence=price_data["confidence"])
        
        return {
            "status": "success",
            **price_data
        }
        
    except Exception as e:
        logger.error("Failed to get weighted price", error=str(e), commodity=commodity)
        raise HTTPException(status_code=500, detail=f"Failed to get weighted price: {str(e)}")

@app.get("/processing-stats")
async def get_processing_stats():
    """
    Get current processing statistics
    
    Returns:
        Processing statistics and performance metrics
    """
    try:
        stats = realtime_processor.get_processing_stats()
        streams = realtime_processor.get_active_streams()
        
        return {
            "status": "success",
            "processing_stats": stats,
            "active_streams": streams
        }
        
    except Exception as e:
        logger.error("Failed to get processing stats", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get processing stats: {str(e)}")

@app.post("/add-to-stream")
async def add_to_stream(request: RealTimeProcessingRequest, stream_id: str = "default"):
    """
    Add processed data to streaming pipeline
    
    Args:
        request: Processing request
        stream_id: Stream identifier
        
    Returns:
        Success confirmation
    """
    try:
        # Process the data first
        analysis = conversation_analyzer.analyze_conversation(request.text)
        
        raw_data = {
            "commodity": analysis.commodity.value if analysis.commodity else None,
            "price": analysis.price.amount if analysis.price else None,
            "quantity": analysis.quantity.amount if analysis.quantity else None,
            "intent": analysis.intent.value,
            "confidence": analysis.overall_confidence,
            "segment_id": request.segment_id or "stream_input",
            "speaker_id": request.speaker_id,
            "timestamp": None
        }
        
        intelligence_data = await realtime_processor.process_market_intelligence(
            raw_data, 
            location_hint=request.location
        )
        
        # Add to stream
        await realtime_processor.add_to_stream(intelligence_data, stream_id)
        
        logger.info("Data added to stream", 
                   stream_id=stream_id,
                   data_id=intelligence_data.id)
        
        return {
            "status": "success",
            "message": f"Data added to stream {stream_id}",
            "data_id": intelligence_data.id
        }
        
    except Exception as e:
        logger.error("Failed to add to stream", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to add to stream: {str(e)}")

@app.websocket("/stream/{stream_id}")
async def websocket_stream(websocket: WebSocket, stream_id: str = "default"):
    """
    WebSocket endpoint for real-time data streaming
    
    Args:
        websocket: WebSocket connection
        stream_id: Stream identifier
    """
    await websocket.accept()
    
    try:
        logger.info("WebSocket stream started", stream_id=stream_id)
        
        async for data in realtime_processor.get_streaming_data(stream_id):
            await websocket.send_json(data)
            
    except Exception as e:
        logger.error("WebSocket stream failed", error=str(e), stream_id=stream_id)
        await websocket.close(code=1000)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)