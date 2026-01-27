"""
End-to-end data flow validation for MANDI EAR microservices
"""

import asyncio
import httpx
import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json
import uuid

from config import settings

logger = structlog.get_logger()

class FlowStatus(Enum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"

@dataclass
class FlowStep:
    service: str
    endpoint: str
    method: str
    payload: Optional[Dict[str, Any]] = None
    expected_fields: Optional[List[str]] = None
    timeout: float = 30.0

@dataclass
class FlowResult:
    step: FlowStep
    status: FlowStatus
    response_time: float
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class DataFlowValidator:
    """Validates end-to-end data flows across microservices"""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=60.0)
        self.test_user_id = "test-user-123"
        self.test_language = "hi"  # Hindi for testing
    
    async def validate_ambient_ai_flow(self) -> List[FlowResult]:
        """Validate ambient AI processing flow"""
        logger.info("Starting ambient AI flow validation")
        
        flow_steps = [
            FlowStep(
                service="ambient-ai",
                endpoint="/process",
                method="POST",
                payload={
                    "audio_data": "base64_encoded_test_audio",
                    "location": {"latitude": 28.6139, "longitude": 77.2090},
                    "timestamp": datetime.utcnow().isoformat()
                },
                expected_fields=["commodity", "price", "confidence", "intent"]
            ),
            FlowStep(
                service="ambient-ai",
                endpoint="/intelligence",
                method="GET",
                expected_fields=["recent_extractions", "market_summary"]
            )
        ]
        
        return await self._execute_flow(flow_steps, "Ambient AI Flow")
    
    async def validate_voice_processing_flow(self) -> List[FlowResult]:
        """Validate voice processing flow"""
        logger.info("Starting voice processing flow validation")
        
        flow_steps = [
            FlowStep(
                service="voice-processing",
                endpoint="/transcribe",
                method="POST",
                payload={
                    "audio_data": "base64_encoded_voice_data",
                    "language": self.test_language
                },
                expected_fields=["transcription", "confidence", "language"]
            ),
            FlowStep(
                service="voice-processing",
                endpoint="/synthesize",
                method="POST",
                payload={
                    "text": "आज गेहूं का भाव क्या है?",
                    "language": self.test_language
                },
                expected_fields=["audio_data", "duration"]
            )
        ]
        
        return await self._execute_flow(flow_steps, "Voice Processing Flow")
    
    async def validate_price_discovery_flow(self) -> List[FlowResult]:
        """Validate price discovery flow"""
        logger.info("Starting price discovery flow validation")
        
        flow_steps = [
            FlowStep(
                service="price-discovery",
                endpoint="/prices/current",
                method="GET",
                expected_fields=["prices", "timestamp", "sources"]
            ),
            FlowStep(
                service="price-discovery",
                endpoint="/prices/trends",
                method="GET",
                expected_fields=["commodity", "trend_data", "analysis"]
            ),
            FlowStep(
                service="price-discovery",
                endpoint="/prices/cross-mandi",
                method="GET",
                expected_fields=["mandis", "price_comparison", "arbitrage_opportunities"]
            )
        ]
        
        return await self._execute_flow(flow_steps, "Price Discovery Flow")
    
    async def validate_negotiation_flow(self) -> List[FlowResult]:
        """Validate negotiation intelligence flow"""
        logger.info("Starting negotiation flow validation")
        
        flow_steps = [
            FlowStep(
                service="negotiation-intelligence",
                endpoint="/analyze",
                method="POST",
                payload={
                    "commodity": "wheat",
                    "current_price": 2500,
                    "quantity": 100,
                    "buyer_context": "urgent_purchase"
                },
                expected_fields=["strategy", "recommended_price", "tactics"]
            ),
            FlowStep(
                service="negotiation-intelligence",
                endpoint="/strategies",
                method="GET",
                expected_fields=["strategies", "market_context"]
            )
        ]
        
        return await self._execute_flow(flow_steps, "Negotiation Flow")
    
    async def validate_crop_planning_flow(self) -> List[FlowResult]:
        """Validate crop planning flow"""
        logger.info("Starting crop planning flow validation")
        
        flow_steps = [
            FlowStep(
                service="crop-planning",
                endpoint="/recommend",
                method="POST",
                payload={
                    "location": {"latitude": 28.6139, "longitude": 77.2090},
                    "farm_size": 5.0,
                    "soil_type": "loamy",
                    "season": "kharif"
                },
                expected_fields=["recommendations", "income_projections", "risk_assessment"]
            ),
            FlowStep(
                service="crop-planning",
                endpoint="/weather",
                method="GET",
                expected_fields=["forecast", "analysis", "recommendations"]
            )
        ]
        
        return await self._execute_flow(flow_steps, "Crop Planning Flow")
    
    async def validate_msp_enforcement_flow(self) -> List[FlowResult]:
        """Validate MSP enforcement flow"""
        logger.info("Starting MSP enforcement flow validation")
        
        flow_steps = [
            FlowStep(
                service="msp-enforcement",
                endpoint="/rates",
                method="GET",
                expected_fields=["msp_rates", "commodities", "season"]
            ),
            FlowStep(
                service="msp-enforcement",
                endpoint="/violations",
                method="GET",
                expected_fields=["violations", "alerts", "alternatives"]
            )
        ]
        
        return await self._execute_flow(flow_steps, "MSP Enforcement Flow")
    
    async def validate_complete_user_journey(self) -> List[FlowResult]:
        """Validate complete user journey from voice input to recommendations"""
        logger.info("Starting complete user journey validation")
        
        # Simulate a complete user journey
        journey_id = str(uuid.uuid4())
        
        flow_steps = [
            # 1. User authentication
            FlowStep(
                service="api-gateway",
                endpoint="/auth/login",
                method="POST",
                payload={
                    "phone_number": "+919876543210",
                    "password": "test_password"
                },
                expected_fields=["access_token", "user_id"]
            ),
            
            # 2. Voice query processing
            FlowStep(
                service="api-gateway",
                endpoint="/api/v1/voice/transcribe",
                method="POST",
                payload={
                    "audio_data": "base64_encoded_query",
                    "journey_id": journey_id
                },
                expected_fields=["transcription", "intent"]
            ),
            
            # 3. Price discovery based on query
            FlowStep(
                service="api-gateway",
                endpoint="/api/v1/prices/current",
                method="GET",
                expected_fields=["prices", "recommendations"]
            ),
            
            # 4. Negotiation guidance
            FlowStep(
                service="api-gateway",
                endpoint="/api/v1/negotiation/analyze",
                method="POST",
                payload={
                    "commodity": "wheat",
                    "context": "selling",
                    "journey_id": journey_id
                },
                expected_fields=["guidance", "strategies"]
            ),
            
            # 5. Voice response synthesis
            FlowStep(
                service="api-gateway",
                endpoint="/api/v1/voice/synthesize",
                method="POST",
                payload={
                    "text": "गेहूं का आज का भाव 2500 रुपये प्रति क्विंटल है।",
                    "language": self.test_language,
                    "journey_id": journey_id
                },
                expected_fields=["audio_data"]
            )
        ]
        
        return await self._execute_flow(flow_steps, "Complete User Journey")
    
    async def _execute_flow(self, flow_steps: List[FlowStep], flow_name: str) -> List[FlowResult]:
        """Execute a flow and return results"""
        results = []
        
        for step in flow_steps:
            result = await self._execute_step(step)
            results.append(result)
            
            # Stop on failure for critical flows
            if result.status == FlowStatus.FAILURE:
                logger.error(
                    "Flow step failed, stopping execution",
                    flow=flow_name,
                    step=step.service,
                    error=result.error_message
                )
                break
        
        # Calculate overall flow status
        success_count = sum(1 for r in results if r.status == FlowStatus.SUCCESS)
        total_count = len(results)
        
        if success_count == total_count:
            overall_status = "SUCCESS"
        elif success_count > 0:
            overall_status = "PARTIAL_SUCCESS"
        else:
            overall_status = "FAILURE"
        
        logger.info(
            "Flow validation completed",
            flow=flow_name,
            status=overall_status,
            success_rate=f"{success_count}/{total_count}"
        )
        
        return results
    
    async def _execute_step(self, step: FlowStep) -> FlowResult:
        """Execute a single flow step"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Build URL
            if step.service == "api-gateway":
                url = f"http://api-gateway:8000{step.endpoint}"
            else:
                service_url = getattr(settings, f"{step.service.upper().replace('-', '_')}_SERVICE_URL")
                url = f"{service_url}{step.endpoint}"
            
            # Prepare headers
            headers = {
                "X-User-ID": self.test_user_id,
                "X-User-Language": self.test_language,
                "Content-Type": "application/json"
            }
            
            # Execute request
            if step.method.upper() == "GET":
                response = await self.http_client.get(url, headers=headers)
            elif step.method.upper() == "POST":
                response = await self.http_client.post(url, headers=headers, json=step.payload)
            else:
                raise ValueError(f"Unsupported method: {step.method}")
            
            end_time = asyncio.get_event_loop().time()
            response_time = (end_time - start_time) * 1000  # ms
            
            # Check response
            if response.status_code == 200:
                response_data = response.json()
                
                # Validate expected fields
                if step.expected_fields:
                    missing_fields = []
                    for field in step.expected_fields:
                        if field not in response_data:
                            missing_fields.append(field)
                    
                    if missing_fields:
                        return FlowResult(
                            step=step,
                            status=FlowStatus.PARTIAL_SUCCESS,
                            response_time=response_time,
                            response_data=response_data,
                            error_message=f"Missing expected fields: {missing_fields}"
                        )
                
                return FlowResult(
                    step=step,
                    status=FlowStatus.SUCCESS,
                    response_time=response_time,
                    response_data=response_data
                )
            else:
                return FlowResult(
                    step=step,
                    status=FlowStatus.FAILURE,
                    response_time=response_time,
                    error_message=f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            response_time = (end_time - start_time) * 1000  # ms
            
            return FlowResult(
                step=step,
                status=FlowStatus.FAILURE,
                response_time=response_time,
                error_message=str(e)
            )
    
    async def validate_all_flows(self) -> Dict[str, List[FlowResult]]:
        """Validate all data flows"""
        logger.info("Starting comprehensive data flow validation")
        
        flows = {
            "ambient_ai": await self.validate_ambient_ai_flow(),
            "voice_processing": await self.validate_voice_processing_flow(),
            "price_discovery": await self.validate_price_discovery_flow(),
            "negotiation": await self.validate_negotiation_flow(),
            "crop_planning": await self.validate_crop_planning_flow(),
            "msp_enforcement": await self.validate_msp_enforcement_flow(),
            "complete_journey": await self.validate_complete_user_journey()
        }
        
        # Generate summary
        total_steps = sum(len(results) for results in flows.values())
        successful_steps = sum(
            sum(1 for r in results if r.status == FlowStatus.SUCCESS)
            for results in flows.values()
        )
        
        logger.info(
            "Data flow validation completed",
            total_flows=len(flows),
            total_steps=total_steps,
            successful_steps=successful_steps,
            success_rate=f"{(successful_steps/total_steps)*100:.1f}%"
        )
        
        return flows

# Global data flow validator instance
data_flow_validator = DataFlowValidator()