"""
Health monitoring and service discovery for MANDI EAR microservices
"""

import asyncio
import httpx
import structlog
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

from config import settings

logger = structlog.get_logger()

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class ServiceHealth:
    name: str
    url: str
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_check: Optional[datetime] = None
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    consecutive_failures: int = 0
    uptime_percentage: float = 100.0
    checks_history: List[bool] = field(default_factory=list)

class HealthMonitor:
    """Monitors health of all microservices"""
    
    def __init__(self):
        self.services: Dict[str, ServiceHealth] = {}
        self.http_client = httpx.AsyncClient(timeout=10.0)
        self.check_interval = 30  # seconds
        self.max_history = 100  # Keep last 100 checks for uptime calculation
        
        # Initialize services from config
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize service health tracking"""
        service_configs = {
            "ambient-ai": settings.AMBIENT_AI_SERVICE_URL,
            "voice-processing": settings.VOICE_PROCESSING_SERVICE_URL,
            "price-discovery": settings.PRICE_DISCOVERY_SERVICE_URL,
            "negotiation-intelligence": settings.NEGOTIATION_SERVICE_URL,
            "crop-planning": settings.CROP_PLANNING_SERVICE_URL,
            "msp-enforcement": settings.MSP_SERVICE_URL,
            "anti-hoarding": settings.ANTI_HOARDING_SERVICE_URL,
            "user-management": settings.USER_MANAGEMENT_SERVICE_URL,
            "notification": settings.NOTIFICATION_SERVICE_URL,
            "benchmarking": settings.BENCHMARKING_SERVICE_URL,
            "accessibility": settings.ACCESSIBILITY_SERVICE_URL,
            "offline-cache": settings.OFFLINE_CACHE_SERVICE_URL,
        }
        
        for name, url in service_configs.items():
            self.services[name] = ServiceHealth(name=name, url=url)
    
    async def check_service_health(self, service: ServiceHealth) -> bool:
        """Check health of a single service"""
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Try health endpoint first, fallback to root
            health_endpoints = ["/health", "/"]
            
            for endpoint in health_endpoints:
                try:
                    response = await self.http_client.get(f"{service.url}{endpoint}")
                    if response.status_code == 200:
                        end_time = asyncio.get_event_loop().time()
                        service.response_time = (end_time - start_time) * 1000  # ms
                        service.status = ServiceStatus.HEALTHY
                        service.error_message = None
                        service.consecutive_failures = 0
                        service.last_check = datetime.utcnow()
                        
                        logger.debug(
                            "Service health check passed",
                            service=service.name,
                            response_time=service.response_time
                        )
                        return True
                except httpx.HTTPStatusError:
                    continue  # Try next endpoint
                    
        except Exception as e:
            service.status = ServiceStatus.UNHEALTHY
            service.error_message = str(e)
            service.consecutive_failures += 1
            service.last_check = datetime.utcnow()
            
            logger.warning(
                "Service health check failed",
                service=service.name,
                error=str(e),
                consecutive_failures=service.consecutive_failures
            )
        
        return False
    
    async def check_all_services(self):
        """Check health of all services"""
        logger.info("Starting health check for all services")
        
        tasks = []
        for service in self.services.values():
            tasks.append(self.check_service_health(service))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update history and calculate uptime
        for i, (service_name, service) in enumerate(self.services.items()):
            if i < len(results) and not isinstance(results[i], Exception):
                is_healthy = results[i]
                service.checks_history.append(is_healthy)
                
                # Keep only recent history
                if len(service.checks_history) > self.max_history:
                    service.checks_history = service.checks_history[-self.max_history:]
                
                # Calculate uptime percentage
                if service.checks_history:
                    healthy_checks = sum(service.checks_history)
                    service.uptime_percentage = (healthy_checks / len(service.checks_history)) * 100
        
        # Log summary
        healthy_count = sum(1 for s in self.services.values() if s.status == ServiceStatus.HEALTHY)
        total_count = len(self.services)
        
        logger.info(
            "Health check completed",
            healthy_services=healthy_count,
            total_services=total_count,
            overall_health=f"{(healthy_count/total_count)*100:.1f}%"
        )
    
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        logger.info("Starting health monitoring", interval=self.check_interval)
        
        while True:
            try:
                await self.check_all_services()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error("Health monitoring error", error=str(e))
                await asyncio.sleep(5)  # Short delay before retry
    
    def get_service_status(self, service_name: str) -> Optional[ServiceHealth]:
        """Get status of a specific service"""
        return self.services.get(service_name)
    
    def get_all_services_status(self) -> Dict[str, Dict]:
        """Get status of all services"""
        return {
            name: {
                "status": service.status.value,
                "last_check": service.last_check.isoformat() if service.last_check else None,
                "response_time": service.response_time,
                "error_message": service.error_message,
                "consecutive_failures": service.consecutive_failures,
                "uptime_percentage": service.uptime_percentage,
                "url": service.url
            }
            for name, service in self.services.items()
        }
    
    def get_unhealthy_services(self) -> List[ServiceHealth]:
        """Get list of unhealthy services"""
        return [
            service for service in self.services.values()
            if service.status == ServiceStatus.UNHEALTHY
        ]
    
    def is_system_healthy(self) -> bool:
        """Check if overall system is healthy"""
        unhealthy_services = self.get_unhealthy_services()
        critical_services = ["ambient-ai", "voice-processing", "price-discovery", "user-management"]
        
        # System is unhealthy if any critical service is down
        for service in unhealthy_services:
            if service.name in critical_services:
                return False
        
        # System is unhealthy if more than 50% of services are down
        healthy_count = sum(1 for s in self.services.values() if s.status == ServiceStatus.HEALTHY)
        return (healthy_count / len(self.services)) >= 0.5

# Global health monitor instance
health_monitor = HealthMonitor()