"""
Database operations for Notification Service
Handles storage and retrieval of alerts, preferences, and monitoring data
"""

import asyncio
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os

from models import (
    AlertConfiguration, UserAlertPreferences, BaseAlert, AlertHistory,
    NotificationDelivery, NotificationTemplate, WeatherData, PriceData,
    AlertType, AlertSeverity, NotificationChannel
)

logger = structlog.get_logger()

# In-memory storage for development/testing
# In production, would use actual databases (PostgreSQL, MongoDB, etc.)
_alert_configurations: Dict[str, AlertConfiguration] = {}
_user_preferences: Dict[str, UserAlertPreferences] = {}
_alert_history: List[AlertHistory] = []
_notification_deliveries: Dict[str, NotificationDelivery] = {}
_notification_templates: List[NotificationTemplate] = []
_weather_data: List[WeatherData] = []
_price_data: List[PriceData] = []
_users_by_location: Dict[str, List[Dict[str, Any]]] = {}
_users_by_commodity: Dict[str, List[Dict[str, Any]]] = {}

async def init_database():
    """Initialize database connections and create tables"""
    try:
        # Initialize sample data for testing
        await _initialize_sample_data()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise

async def close_database():
    """Close database connections"""
    try:
        # In production, would close actual database connections
        logger.info("Database connections closed")
        
    except Exception as e:
        logger.error("Error closing database", error=str(e))

async def _initialize_sample_data():
    """Initialize sample data for testing"""
    global _users_by_location, _users_by_commodity, _notification_templates
    
    # Sample users by location
    _users_by_location = {
        'Punjab': [
            {'user_id': 'user_001', 'location': 'Punjab', 'phone': '+91-9876543210'},
            {'user_id': 'user_002', 'location': 'Punjab', 'phone': '+91-9876543211'}
        ],
        'Haryana': [
            {'user_id': 'user_003', 'location': 'Haryana', 'phone': '+91-9876543212'}
        ],
        'Uttar Pradesh': [
            {'user_id': 'user_004', 'location': 'Uttar Pradesh', 'phone': '+91-9876543213'},
            {'user_id': 'user_005', 'location': 'Uttar Pradesh', 'phone': '+91-9876543214'}
        ]
    }
    
    # Sample users by commodity
    _users_by_commodity = {
        'wheat': [
            {'user_id': 'user_001', 'commodity': 'wheat', 'location': 'Punjab'},
            {'user_id': 'user_002', 'commodity': 'wheat', 'location': 'Punjab'},
            {'user_id': 'user_003', 'commodity': 'wheat', 'location': 'Haryana'}
        ],
        'rice': [
            {'user_id': 'user_001', 'commodity': 'rice', 'location': 'Punjab'},
            {'user_id': 'user_004', 'commodity': 'rice', 'location': 'Uttar Pradesh'}
        ],
        'cotton': [
            {'user_id': 'user_005', 'commodity': 'cotton', 'location': 'Uttar Pradesh'}
        ]
    }
    
    # Sample notification templates
    _notification_templates = [
        NotificationTemplate(
            alert_type=AlertType.PRICE_MOVEMENT,
            severity=AlertSeverity.HIGH,
            language="en",
            channel=NotificationChannel.SMS,
            title_template="🚨 {commodity} Price Alert",
            message_template="{commodity} price {direction} by {percentage}% to ₹{current_price}",
            variables=["commodity", "direction", "percentage", "current_price"]
        ),
        NotificationTemplate(
            alert_type=AlertType.WEATHER_EMERGENCY,
            severity=AlertSeverity.CRITICAL,
            language="en",
            channel=NotificationChannel.SMS,
            title_template="⚠️ Weather Emergency: {weather_event}",
            message_template="URGENT: {weather_event} alert for {location}. Take immediate action.",
            variables=["weather_event", "location"]
        )
    ]

# Alert Configuration operations
async def store_alert_configuration(config: AlertConfiguration):
    """Store alert configuration"""
    try:
        _alert_configurations[config.id] = config
        logger.info("Alert configuration stored", config_id=config.id)
        
    except Exception as e:
        logger.error("Error storing alert configuration", config_id=config.id, error=str(e))
        raise

async def get_alert_configuration(alert_id: str, user_id: str) -> Optional[AlertConfiguration]:
    """Get alert configuration by ID and user ID"""
    try:
        config = _alert_configurations.get(alert_id)
        if config and config.user_id == user_id:
            return config
        return None
        
    except Exception as e:
        logger.error("Error getting alert configuration", alert_id=alert_id, error=str(e))
        return None

async def update_alert_configuration(config: AlertConfiguration):
    """Update alert configuration"""
    try:
        if config.id in _alert_configurations:
            _alert_configurations[config.id] = config
            logger.info("Alert configuration updated", config_id=config.id)
        else:
            raise ValueError(f"Alert configuration {config.id} not found")
            
    except Exception as e:
        logger.error("Error updating alert configuration", config_id=config.id, error=str(e))
        raise

async def delete_alert_configuration(alert_id: str, user_id: str) -> bool:
    """Delete alert configuration"""
    try:
        config = _alert_configurations.get(alert_id)
        if config and config.user_id == user_id:
            del _alert_configurations[alert_id]
            logger.info("Alert configuration deleted", alert_id=alert_id)
            return True
        return False
        
    except Exception as e:
        logger.error("Error deleting alert configuration", alert_id=alert_id, error=str(e))
        return False

async def get_user_alert_configurations(user_id: str, active_only: bool = True) -> List[AlertConfiguration]:
    """Get all alert configurations for a user"""
    try:
        configs = []
        for config in _alert_configurations.values():
            if config.user_id == user_id:
                if not active_only or config.is_active:
                    configs.append(config)
        
        return configs
        
    except Exception as e:
        logger.error("Error getting user alert configurations", user_id=user_id, error=str(e))
        return []

# User Preferences operations
async def store_user_preferences(preferences: UserAlertPreferences):
    """Store user preferences"""
    try:
        _user_preferences[preferences.user_id] = preferences
        logger.info("User preferences stored", user_id=preferences.user_id)
        
    except Exception as e:
        logger.error("Error storing user preferences", user_id=preferences.user_id, error=str(e))
        raise

async def get_user_preferences(user_id: str) -> Optional[UserAlertPreferences]:
    """Get user preferences"""
    try:
        return _user_preferences.get(user_id)
        
    except Exception as e:
        logger.error("Error getting user preferences", user_id=user_id, error=str(e))
        return None

# Alert History operations
async def store_alert_history(history: AlertHistory):
    """Store alert in history"""
    try:
        _alert_history.append(history)
        logger.info("Alert history stored", alert_id=history.id)
        
    except Exception as e:
        logger.error("Error storing alert history", alert_id=history.id, error=str(e))
        raise

async def get_alert_history(
    user_id: str, 
    limit: int = 50, 
    offset: int = 0,
    alert_type: Optional[str] = None
) -> List[AlertHistory]:
    """Get alert history for a user"""
    try:
        user_history = []
        for history in _alert_history:
            if history.user_id == user_id:
                if not alert_type or history.alert_type.value == alert_type:
                    user_history.append(history)
        
        # Sort by creation time (newest first)
        user_history.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        return user_history[offset:offset + limit]
        
    except Exception as e:
        logger.error("Error getting alert history", user_id=user_id, error=str(e))
        return []

# Notification Delivery operations
async def store_notification_delivery(delivery: NotificationDelivery):
    """Store notification delivery record"""
    try:
        _notification_deliveries[delivery.id] = delivery
        logger.info("Notification delivery stored", delivery_id=delivery.id)
        
    except Exception as e:
        logger.error("Error storing notification delivery", delivery_id=delivery.id, error=str(e))
        raise

async def update_notification_delivery(delivery: NotificationDelivery):
    """Update notification delivery record"""
    try:
        if delivery.id in _notification_deliveries:
            _notification_deliveries[delivery.id] = delivery
            logger.info("Notification delivery updated", delivery_id=delivery.id)
        else:
            raise ValueError(f"Notification delivery {delivery.id} not found")
            
    except Exception as e:
        logger.error("Error updating notification delivery", delivery_id=delivery.id, error=str(e))
        raise

# Template operations
async def get_notification_templates() -> List[NotificationTemplate]:
    """Get all notification templates"""
    try:
        return _notification_templates.copy()
        
    except Exception as e:
        logger.error("Error getting notification templates", error=str(e))
        return []

# Weather Data operations
async def store_weather_data(weather_data: WeatherData):
    """Store weather data"""
    try:
        _weather_data.append(weather_data)
        
        # Keep only last 1000 records to prevent memory issues
        if len(_weather_data) > 1000:
            _weather_data.pop(0)
        
        logger.info("Weather data stored", location=weather_data.location)
        
    except Exception as e:
        logger.error("Error storing weather data", error=str(e))
        raise

async def get_weather_data(location: str, limit: int = 10) -> List[WeatherData]:
    """Get recent weather data for a location"""
    try:
        location_data = []
        for data in reversed(_weather_data):  # Get most recent first
            if data.location.lower() == location.lower():
                location_data.append(data)
                if len(location_data) >= limit:
                    break
        
        return location_data
        
    except Exception as e:
        logger.error("Error getting weather data", location=location, error=str(e))
        return []

# Price Data operations
async def store_price_data(price_data: PriceData):
    """Store price data"""
    try:
        _price_data.append(price_data)
        
        # Keep only last 10000 records to prevent memory issues
        if len(_price_data) > 10000:
            _price_data.pop(0)
        
        logger.info("Price data stored", commodity=price_data.commodity)
        
    except Exception as e:
        logger.error("Error storing price data", error=str(e))
        raise

async def get_price_data(commodity: str, limit: int = 10) -> List[PriceData]:
    """Get recent price data for a commodity"""
    try:
        commodity_data = []
        for data in reversed(_price_data):  # Get most recent first
            if data.commodity.lower() == commodity.lower():
                commodity_data.append(data)
                if len(commodity_data) >= limit:
                    break
        
        return commodity_data
        
    except Exception as e:
        logger.error("Error getting price data", commodity=commodity, error=str(e))
        return []

async def get_historical_prices(
    commodity: str, 
    start_time: datetime, 
    end_time: datetime
) -> List[Dict[str, Any]]:
    """Get historical price data for a time range"""
    try:
        historical_data = []
        for data in _price_data:
            if (data.commodity.lower() == commodity.lower() and 
                start_time <= data.timestamp <= end_time):
                historical_data.append({
                    'price': data.current_price,
                    'timestamp': data.timestamp,
                    'location': data.location,
                    'source': data.source
                })
        
        # Sort by timestamp
        historical_data.sort(key=lambda x: x['timestamp'])
        return historical_data
        
    except Exception as e:
        logger.error("Error getting historical prices", commodity=commodity, error=str(e))
        return []

# User Location/Commodity mapping operations
async def get_users_by_location(location: str) -> List[Dict[str, Any]]:
    """Get users in a specific location"""
    try:
        return _users_by_location.get(location, [])
        
    except Exception as e:
        logger.error("Error getting users by location", location=location, error=str(e))
        return []

async def get_users_by_commodity(commodity: str) -> List[Dict[str, Any]]:
    """Get users interested in a specific commodity"""
    try:
        return _users_by_commodity.get(commodity, [])
        
    except Exception as e:
        logger.error("Error getting users by commodity", commodity=commodity, error=str(e))
        return []

# Alert storage operations
async def store_weather_alert(alert: BaseAlert):
    """Store weather alert"""
    try:
        # Convert to history record
        history = AlertHistory(
            user_id=alert.user_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            title=alert.title,
            message=alert.message,
            commodity=alert.commodity,
            location=alert.location,
            created_at=alert.created_at,
            metadata=alert.metadata
        )
        
        await store_alert_history(history)
        logger.info("Weather alert stored", alert_id=alert.id)
        
    except Exception as e:
        logger.error("Error storing weather alert", alert_id=alert.id, error=str(e))
        raise

async def store_price_alert(alert: BaseAlert):
    """Store price alert"""
    try:
        # Convert to history record
        history = AlertHistory(
            user_id=alert.user_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            title=alert.title,
            message=alert.message,
            commodity=alert.commodity,
            location=alert.location,
            created_at=alert.created_at,
            metadata=alert.metadata
        )
        
        await store_alert_history(history)
        logger.info("Price alert stored", alert_id=alert.id)
        
    except Exception as e:
        logger.error("Error storing price alert", alert_id=alert.id, error=str(e))
        raise

# Statistics operations
async def get_alert_statistics(user_id: str, date: datetime) -> Dict[str, Any]:
    """Get alert statistics for a user and date"""
    try:
        stats = {
            'total_alerts': 0,
            'alerts_by_type': {},
            'alerts_by_severity': {},
            'read_rate': 0.0,
            'acknowledgment_rate': 0.0
        }
        
        # Count alerts for the specific date
        target_date = date.date()
        user_alerts = []
        
        for history in _alert_history:
            if (history.user_id == user_id and 
                history.created_at.date() == target_date):
                user_alerts.append(history)
        
        stats['total_alerts'] = len(user_alerts)
        
        if user_alerts:
            # Count by type
            for alert in user_alerts:
                alert_type = alert.alert_type.value
                stats['alerts_by_type'][alert_type] = stats['alerts_by_type'].get(alert_type, 0) + 1
                
                severity = alert.severity.value
                stats['alerts_by_severity'][severity] = stats['alerts_by_severity'].get(severity, 0) + 1
            
            # Calculate rates (simplified)
            read_count = sum(1 for alert in user_alerts if alert.was_read)
            ack_count = sum(1 for alert in user_alerts if alert.was_acknowledged)
            
            stats['read_rate'] = read_count / len(user_alerts)
            stats['acknowledgment_rate'] = ack_count / len(user_alerts)
        
        return stats
        
    except Exception as e:
        logger.error("Error getting alert statistics", user_id=user_id, error=str(e))
        return {
            'total_alerts': 0,
            'alerts_by_type': {},
            'alerts_by_severity': {},
            'read_rate': 0.0,
            'acknowledgment_rate': 0.0
        }

# Utility functions for testing
async def clear_all_data():
    """Clear all data (for testing purposes)"""
    global _alert_configurations, _user_preferences, _alert_history
    global _notification_deliveries, _weather_data, _price_data
    
    _alert_configurations.clear()
    _user_preferences.clear()
    _alert_history.clear()
    _notification_deliveries.clear()
    _weather_data.clear()
    _price_data.clear()
    
    logger.info("All data cleared")

async def get_data_counts() -> Dict[str, int]:
    """Get counts of all data types (for monitoring)"""
    return {
        'alert_configurations': len(_alert_configurations),
        'user_preferences': len(_user_preferences),
        'alert_history': len(_alert_history),
        'notification_deliveries': len(_notification_deliveries),
        'weather_data': len(_weather_data),
        'price_data': len(_price_data),
        'notification_templates': len(_notification_templates)
    }