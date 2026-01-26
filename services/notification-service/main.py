"""
Notification Service - Real-time Alert and Notification System
Handles customizable alerts for price movements, weather emergencies, and user-defined thresholds
"""

import asyncio
import structlog
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import uvicorn

from models import (
    AlertConfiguration, PriceMovementAlert, WeatherEmergencyAlert,
    NotificationChannel, AlertType, AlertSeverity, UserAlertPreferences
)
from alert_engine import CustomizableAlertEngine
from notification_dispatcher import NotificationDispatcher
from weather_monitor import WeatherEmergencyMonitor
from price_monitor import PriceMovementMonitor
from database import init_database, close_database

logger = structlog.get_logger()

# Global instances
alert_engine: Optional[CustomizableAlertEngine] = None
notification_dispatcher: Optional[NotificationDispatcher] = None
weather_monitor: Optional[WeatherEmergencyMonitor] = None
price_monitor: Optional[PriceMovementMonitor] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global alert_engine, notification_dispatcher, weather_monitor, price_monitor
    
    try:
        # Initialize database
        await init_database()
        logger.info("Database initialized")
        
        # Initialize core components
        alert_engine = CustomizableAlertEngine()
        notification_dispatcher = NotificationDispatcher()
        weather_monitor = WeatherEmergencyMonitor()
        price_monitor = PriceMovementMonitor()
        
        # Initialize all components
        await alert_engine.initialize()
        await notification_dispatcher.initialize()
        await weather_monitor.initialize()
        await price_monitor.initialize()
        
        # Start monitoring services
        await weather_monitor.start_monitoring()
        await price_monitor.start_monitoring()
        
        logger.info("Notification service initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error("Failed to initialize notification service", error=str(e))
        raise
    finally:
        # Cleanup
        if weather_monitor:
            await weather_monitor.stop_monitoring()
        if price_monitor:
            await price_monitor.stop_monitoring()
        if alert_engine:
            await alert_engine.shutdown()
        if notification_dispatcher:
            await notification_dispatcher.shutdown()
        
        await close_database()
        logger.info("Notification service shutdown complete")

app = FastAPI(
    title="MANDI EAR™ Notification Service",
    description="Real-time alert and notification system for agricultural intelligence",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "notification-service",
        "version": "1.0.0",
        "components": {
            "alert_engine": alert_engine is not None,
            "notification_dispatcher": notification_dispatcher is not None,
            "weather_monitor": weather_monitor is not None,
            "price_monitor": price_monitor is not None
        }
    }

@app.post("/alerts/configure")
async def configure_alert(alert_config: AlertConfiguration):
    """Configure a new alert threshold"""
    try:
        if not alert_engine:
            raise HTTPException(status_code=503, detail="Alert engine not initialized")
        
        result = await alert_engine.configure_alert(alert_config)
        
        logger.info(
            "Alert configured",
            user_id=alert_config.user_id,
            alert_type=alert_config.alert_type,
            commodity=alert_config.commodity
        )
        
        return {
            "success": True,
            "alert_id": result.alert_id,
            "message": "Alert configured successfully"
        }
        
    except Exception as e:
        logger.error("Error configuring alert", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts/user/{user_id}")
async def get_user_alerts(user_id: str, active_only: bool = True):
    """Get all alerts for a user"""
    try:
        if not alert_engine:
            raise HTTPException(status_code=503, detail="Alert engine not initialized")
        
        alerts = await alert_engine.get_user_alerts(user_id, active_only)
        
        return {
            "success": True,
            "alerts": alerts,
            "count": len(alerts)
        }
        
    except Exception as e:
        logger.error("Error getting user alerts", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/alerts/{alert_id}/toggle")
async def toggle_alert(alert_id: str, user_id: str):
    """Toggle alert active/inactive status"""
    try:
        if not alert_engine:
            raise HTTPException(status_code=503, detail="Alert engine not initialized")
        
        result = await alert_engine.toggle_alert(alert_id, user_id)
        
        return {
            "success": True,
            "alert_id": alert_id,
            "is_active": result.is_active,
            "message": f"Alert {'activated' if result.is_active else 'deactivated'}"
        }
        
    except Exception as e:
        logger.error("Error toggling alert", alert_id=alert_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str, user_id: str):
    """Delete an alert configuration"""
    try:
        if not alert_engine:
            raise HTTPException(status_code=503, detail="Alert engine not initialized")
        
        success = await alert_engine.delete_alert(alert_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {
            "success": True,
            "message": "Alert deleted successfully"
        }
        
    except Exception as e:
        logger.error("Error deleting alert", alert_id=alert_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/alerts/preferences")
async def update_notification_preferences(preferences: UserAlertPreferences):
    """Update user notification preferences"""
    try:
        if not notification_dispatcher:
            raise HTTPException(status_code=503, detail="Notification dispatcher not initialized")
        
        await notification_dispatcher.update_user_preferences(preferences)
        
        return {
            "success": True,
            "message": "Notification preferences updated"
        }
        
    except Exception as e:
        logger.error("Error updating preferences", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts/preferences/{user_id}")
async def get_notification_preferences(user_id: str):
    """Get user notification preferences"""
    try:
        if not notification_dispatcher:
            raise HTTPException(status_code=503, detail="Notification dispatcher not initialized")
        
        preferences = await notification_dispatcher.get_user_preferences(user_id)
        
        return {
            "success": True,
            "preferences": preferences
        }
        
    except Exception as e:
        logger.error("Error getting preferences", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/alerts/test")
async def test_alert(user_id: str, alert_type: str, background_tasks: BackgroundTasks):
    """Send a test alert to verify notification channels"""
    try:
        if not notification_dispatcher:
            raise HTTPException(status_code=503, detail="Notification dispatcher not initialized")
        
        # Create test alert
        test_alert = PriceMovementAlert(
            user_id=user_id,
            commodity="Test Commodity",
            current_price=1000.0,
            previous_price=900.0,
            percentage_change=11.1,
            alert_type=AlertType.PRICE_RISE,
            severity=AlertSeverity.MEDIUM,
            message="This is a test alert to verify your notification settings."
        )
        
        # Send test notification in background
        background_tasks.add_task(
            notification_dispatcher.send_notification,
            test_alert
        )
        
        return {
            "success": True,
            "message": "Test alert sent"
        }
        
    except Exception as e:
        logger.error("Error sending test alert", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts/history/{user_id}")
async def get_alert_history(
    user_id: str, 
    limit: int = 50, 
    offset: int = 0,
    alert_type: Optional[str] = None
):
    """Get alert history for a user"""
    try:
        if not alert_engine:
            raise HTTPException(status_code=503, detail="Alert engine not initialized")
        
        history = await alert_engine.get_alert_history(
            user_id, limit, offset, alert_type
        )
        
        return {
            "success": True,
            "history": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error("Error getting alert history", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitoring/status")
async def get_monitoring_status():
    """Get status of monitoring services"""
    try:
        status = {
            "weather_monitor": {
                "active": weather_monitor.is_monitoring if weather_monitor else False,
                "last_check": weather_monitor.last_check_time if weather_monitor else None,
                "alerts_sent_today": weather_monitor.alerts_sent_today if weather_monitor else 0
            },
            "price_monitor": {
                "active": price_monitor.is_monitoring if price_monitor else False,
                "last_check": price_monitor.last_check_time if price_monitor else None,
                "alerts_sent_today": price_monitor.alerts_sent_today if price_monitor else 0
            }
        }
        
        return {
            "success": True,
            "monitoring_status": status
        }
        
    except Exception as e:
        logger.error("Error getting monitoring status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/monitoring/weather/force-check")
async def force_weather_check(background_tasks: BackgroundTasks):
    """Force a weather emergency check"""
    try:
        if not weather_monitor:
            raise HTTPException(status_code=503, detail="Weather monitor not initialized")
        
        background_tasks.add_task(weather_monitor.check_weather_emergencies)
        
        return {
            "success": True,
            "message": "Weather check initiated"
        }
        
    except Exception as e:
        logger.error("Error forcing weather check", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/monitoring/price/force-check")
async def force_price_check(background_tasks: BackgroundTasks):
    """Force a price movement check"""
    try:
        if not price_monitor:
            raise HTTPException(status_code=503, detail="Price monitor not initialized")
        
        background_tasks.add_task(price_monitor.check_price_movements)
        
        return {
            "success": True,
            "message": "Price check initiated"
        }
        
    except Exception as e:
        logger.error("Error forcing price check", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8009,
        reload=True,
        log_level="info"
    )