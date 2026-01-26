"""
Customizable Alert Engine
Handles user-defined alert thresholds and alert generation logic
"""

import asyncio
import structlog
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, time
import json

from models import (
    AlertConfiguration, AlertConfigurationResponse, AlertToggleResponse,
    BaseAlert, PriceMovementAlert, CustomThresholdAlert, AlertHistory,
    AlertType, AlertSeverity, ThresholdCondition, NotificationChannel
)
from database import (
    store_alert_configuration, get_alert_configuration, update_alert_configuration,
    delete_alert_configuration, get_user_alert_configurations, store_alert_history,
    get_alert_history, get_alert_statistics
)
from notification_dispatcher import NotificationDispatcher

logger = structlog.get_logger()

class CustomizableAlertEngine:
    """Manages customizable alert configurations and triggers"""
    
    def __init__(self):
        self.notification_dispatcher: Optional[NotificationDispatcher] = None
        self.active_configurations: Dict[str, AlertConfiguration] = {}
        self.alert_cache: Dict[str, datetime] = {}  # Last alert time per config
        self.is_running = False
        self.monitoring_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """Initialize the alert engine"""
        try:
            self.notification_dispatcher = NotificationDispatcher()
            await self.notification_dispatcher.initialize()
            
            # Load active alert configurations
            await self._load_active_configurations()
            
            # Start monitoring task
            self.is_running = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            logger.info("Customizable alert engine initialized")
            
        except Exception as e:
            logger.error("Failed to initialize alert engine", error=str(e))
            raise
    
    async def shutdown(self):
        """Shutdown the alert engine"""
        self.is_running = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self.notification_dispatcher:
            await self.notification_dispatcher.shutdown()
        
        logger.info("Alert engine shutdown complete")
    
    async def _load_active_configurations(self):
        """Load all active alert configurations"""
        try:
            # In production, this would load from database
            # For now, initialize empty
            self.active_configurations = {}
            logger.info("Active alert configurations loaded", count=len(self.active_configurations))
            
        except Exception as e:
            logger.error("Error loading alert configurations", error=str(e))
    
    async def _monitoring_loop(self):
        """Main monitoring loop for checking alert conditions"""
        while self.is_running:
            try:
                await self._check_all_alert_conditions()
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in monitoring loop", error=str(e))
                await asyncio.sleep(30)  # Wait before retrying
    
    async def _check_all_alert_conditions(self):
        """Check all active alert configurations for trigger conditions"""
        for config_id, config in self.active_configurations.items():
            try:
                if not config.is_active:
                    continue
                
                # Check if we're in quiet hours
                if await self._is_quiet_hours(config):
                    continue
                
                # Check if we've exceeded daily alert limit
                if await self._exceeded_daily_limit(config):
                    continue
                
                # Check the specific alert condition
                should_trigger = await self._evaluate_alert_condition(config)
                
                if should_trigger:
                    await self._trigger_alert(config)
                
            except Exception as e:
                logger.error("Error checking alert condition", config_id=config_id, error=str(e))
    
    async def _is_quiet_hours(self, config: AlertConfiguration) -> bool:
        """Check if current time is within quiet hours"""
        if not config.quiet_hours_start or not config.quiet_hours_end:
            return False
        
        now = datetime.now().time()
        start = config.quiet_hours_start
        end = config.quiet_hours_end
        
        if start <= end:
            # Same day quiet hours
            return start <= now <= end
        else:
            # Overnight quiet hours
            return now >= start or now <= end
    
    async def _exceeded_daily_limit(self, config: AlertConfiguration) -> bool:
        """Check if daily alert limit has been exceeded"""
        today = datetime.now().date()
        cache_key = f"{config.id}_{today}"
        
        # Get today's alert count from cache or database
        # For now, use simple cache
        if cache_key not in self.alert_cache:
            return False
        
        # In production, would query database for actual count
        return False  # Simplified for now
    
    async def _evaluate_alert_condition(self, config: AlertConfiguration) -> bool:
        """Evaluate if alert condition is met"""
        try:
            if config.alert_type == AlertType.PRICE_MOVEMENT:
                return await self._check_price_movement_condition(config)
            elif config.alert_type == AlertType.PRICE_RISE:
                return await self._check_price_rise_condition(config)
            elif config.alert_type == AlertType.PRICE_DROP:
                return await self._check_price_drop_condition(config)
            elif config.alert_type == AlertType.CUSTOM_THRESHOLD:
                return await self._check_custom_threshold_condition(config)
            else:
                logger.warning("Unknown alert type", alert_type=config.alert_type)
                return False
                
        except Exception as e:
            logger.error("Error evaluating alert condition", config_id=config.id, error=str(e))
            return False
    
    async def _check_price_movement_condition(self, config: AlertConfiguration) -> bool:
        """Check for significant price movement (>10% by default)"""
        try:
            # Get current and previous price data
            current_data = await self._get_current_price_data(config.commodity, config.location)
            if not current_data:
                return False
            
            previous_data = await self._get_previous_price_data(
                config.commodity, 
                config.location, 
                config.comparison_period or "24h"
            )
            if not previous_data:
                return False
            
            # Calculate percentage change
            current_price = current_data.get('price', 0)
            previous_price = previous_data.get('price', 0)
            
            if previous_price == 0:
                return False
            
            percentage_change = abs((current_price - previous_price) / previous_price) * 100
            
            # Check against threshold
            if config.threshold_condition == ThresholdCondition.GREATER_THAN:
                return percentage_change > config.threshold_value
            elif config.threshold_condition == ThresholdCondition.PERCENTAGE_CHANGE:
                return percentage_change >= config.threshold_value
            
            return False
            
        except Exception as e:
            logger.error("Error checking price movement condition", error=str(e))
            return False
    
    async def _check_price_rise_condition(self, config: AlertConfiguration) -> bool:
        """Check for price rise above threshold"""
        try:
            current_data = await self._get_current_price_data(config.commodity, config.location)
            if not current_data:
                return False
            
            current_price = current_data.get('price', 0)
            
            if config.threshold_condition == ThresholdCondition.GREATER_THAN:
                return current_price > config.threshold_value
            elif config.threshold_condition == ThresholdCondition.PERCENTAGE_CHANGE:
                previous_data = await self._get_previous_price_data(
                    config.commodity, config.location, config.comparison_period or "24h"
                )
                if not previous_data:
                    return False
                
                previous_price = previous_data.get('price', 0)
                if previous_price == 0:
                    return False
                
                percentage_change = ((current_price - previous_price) / previous_price) * 100
                return percentage_change >= config.threshold_value
            
            return False
            
        except Exception as e:
            logger.error("Error checking price rise condition", error=str(e))
            return False
    
    async def _check_price_drop_condition(self, config: AlertConfiguration) -> bool:
        """Check for price drop below threshold"""
        try:
            current_data = await self._get_current_price_data(config.commodity, config.location)
            if not current_data:
                return False
            
            current_price = current_data.get('price', 0)
            
            if config.threshold_condition == ThresholdCondition.LESS_THAN:
                return current_price < config.threshold_value
            elif config.threshold_condition == ThresholdCondition.PERCENTAGE_CHANGE:
                previous_data = await self._get_previous_price_data(
                    config.commodity, config.location, config.comparison_period or "24h"
                )
                if not previous_data:
                    return False
                
                previous_price = previous_data.get('price', 0)
                if previous_price == 0:
                    return False
                
                percentage_change = ((previous_price - current_price) / previous_price) * 100
                return percentage_change >= config.threshold_value
            
            return False
            
        except Exception as e:
            logger.error("Error checking price drop condition", error=str(e))
            return False
    
    async def _check_custom_threshold_condition(self, config: AlertConfiguration) -> bool:
        """Check custom threshold condition"""
        try:
            # Get relevant data based on metadata
            data_source = config.metadata.get('data_source') if config.metadata else 'price'
            
            if data_source == 'price':
                current_data = await self._get_current_price_data(config.commodity, config.location)
                current_value = current_data.get('price', 0) if current_data else 0
            elif data_source == 'weather':
                current_data = await self._get_current_weather_data(config.location)
                metric = config.metadata.get('weather_metric', 'temperature')
                current_value = current_data.get(metric, 0) if current_data else 0
            else:
                return False
            
            # Evaluate condition
            if config.threshold_condition == ThresholdCondition.GREATER_THAN:
                return current_value > config.threshold_value
            elif config.threshold_condition == ThresholdCondition.LESS_THAN:
                return current_value < config.threshold_value
            elif config.threshold_condition == ThresholdCondition.EQUALS:
                return abs(current_value - config.threshold_value) < 0.01
            
            return False
            
        except Exception as e:
            logger.error("Error checking custom threshold condition", error=str(e))
            return False
    
    async def _get_current_price_data(self, commodity: str, location: str) -> Optional[Dict[str, Any]]:
        """Get current price data for commodity and location"""
        try:
            # In production, this would query the price discovery service
            # For now, simulate price data
            import random
            base_price = 1000 + random.randint(-200, 200)
            
            return {
                'commodity': commodity,
                'location': location,
                'price': base_price,
                'timestamp': datetime.utcnow(),
                'source': 'price_discovery_service'
            }
            
        except Exception as e:
            logger.error("Error getting current price data", error=str(e))
            return None
    
    async def _get_previous_price_data(self, commodity: str, location: str, period: str) -> Optional[Dict[str, Any]]:
        """Get previous price data for comparison"""
        try:
            # Parse period (e.g., "24h", "7d")
            hours_back = 24  # Default to 24 hours
            if period.endswith('h'):
                hours_back = int(period[:-1])
            elif period.endswith('d'):
                hours_back = int(period[:-1]) * 24
            
            # In production, would query historical data
            # For now, simulate with slight variation
            current_data = await self._get_current_price_data(commodity, location)
            if not current_data:
                return None
            
            import random
            variation = random.uniform(-0.15, 0.15)  # ±15% variation
            previous_price = current_data['price'] * (1 + variation)
            
            return {
                'commodity': commodity,
                'location': location,
                'price': previous_price,
                'timestamp': datetime.utcnow() - timedelta(hours=hours_back),
                'source': 'price_discovery_service'
            }
            
        except Exception as e:
            logger.error("Error getting previous price data", error=str(e))
            return None
    
    async def _get_current_weather_data(self, location: str) -> Optional[Dict[str, Any]]:
        """Get current weather data for location"""
        try:
            # In production, would query weather service
            # For now, simulate weather data
            import random
            
            return {
                'location': location,
                'temperature': random.uniform(15, 40),
                'humidity': random.uniform(30, 90),
                'rainfall': random.uniform(0, 50),
                'wind_speed': random.uniform(0, 30),
                'timestamp': datetime.utcnow(),
                'source': 'weather_service'
            }
            
        except Exception as e:
            logger.error("Error getting weather data", error=str(e))
            return None
    
    async def _trigger_alert(self, config: AlertConfiguration):
        """Trigger an alert based on configuration"""
        try:
            # Create appropriate alert based on type
            if config.alert_type in [AlertType.PRICE_MOVEMENT, AlertType.PRICE_RISE, AlertType.PRICE_DROP]:
                alert = await self._create_price_alert(config)
            elif config.alert_type == AlertType.CUSTOM_THRESHOLD:
                alert = await self._create_custom_threshold_alert(config)
            else:
                logger.warning("Unsupported alert type for triggering", alert_type=config.alert_type)
                return
            
            if not alert:
                return
            
            # Send notification
            if self.notification_dispatcher:
                await self.notification_dispatcher.send_notification(alert)
            
            # Store in history
            await self._store_alert_in_history(alert)
            
            # Update cache to prevent spam
            self.alert_cache[config.id] = datetime.utcnow()
            
            logger.info(
                "Alert triggered",
                config_id=config.id,
                alert_type=config.alert_type,
                user_id=config.user_id
            )
            
        except Exception as e:
            logger.error("Error triggering alert", config_id=config.id, error=str(e))
    
    async def _create_price_alert(self, config: AlertConfiguration) -> Optional[PriceMovementAlert]:
        """Create price movement alert"""
        try:
            current_data = await self._get_current_price_data(config.commodity, config.location)
            previous_data = await self._get_previous_price_data(
                config.commodity, config.location, config.comparison_period or "24h"
            )
            
            if not current_data or not previous_data:
                return None
            
            current_price = current_data['price']
            previous_price = previous_data['price']
            percentage_change = ((current_price - previous_price) / previous_price) * 100 if previous_price != 0 else 0
            
            # Determine severity based on percentage change
            abs_change = abs(percentage_change)
            if abs_change >= 20:
                severity = AlertSeverity.CRITICAL
            elif abs_change >= 15:
                severity = AlertSeverity.HIGH
            elif abs_change >= 10:
                severity = AlertSeverity.MEDIUM
            else:
                severity = AlertSeverity.LOW
            
            # Create title and message
            direction = "risen" if percentage_change > 0 else "dropped"
            title = f"🚨 {config.commodity} Price Alert - {abs(percentage_change):.1f}% {direction.title()}"
            
            message = f"""
📊 PRICE MOVEMENT ALERT 📊

🌾 Commodity: {config.commodity}
📍 Location: {config.location or 'Multiple markets'}
💰 Current Price: ₹{current_price:.2f}/quintal
📈 Previous Price: ₹{previous_price:.2f}/quintal
📊 Change: {percentage_change:+.1f}% ({current_price - previous_price:+.2f})

⏰ Time Period: {config.comparison_period or '24 hours'}
🔔 Your threshold: {config.threshold_value}%

💡 Consider reviewing your trading strategy based on this significant price movement.
            """.strip()
            
            alert = PriceMovementAlert(
                user_id=config.user_id,
                alert_type=config.alert_type,
                severity=severity,
                title=title,
                message=message,
                commodity=config.commodity,
                location=config.location,
                current_price=current_price,
                previous_price=previous_price,
                percentage_change=percentage_change,
                absolute_change=current_price - previous_price,
                mandi_name=current_data.get('mandi_name'),
                metadata={
                    'config_id': config.id,
                    'threshold_value': config.threshold_value,
                    'comparison_period': config.comparison_period
                }
            )
            
            return alert
            
        except Exception as e:
            logger.error("Error creating price alert", error=str(e))
            return None
    
    async def _create_custom_threshold_alert(self, config: AlertConfiguration) -> Optional[CustomThresholdAlert]:
        """Create custom threshold alert"""
        try:
            # Get current value based on data source
            data_source = config.metadata.get('data_source', 'price') if config.metadata else 'price'
            
            if data_source == 'price':
                current_data = await self._get_current_price_data(config.commodity, config.location)
                current_value = current_data.get('price', 0) if current_data else 0
                unit = 'per quintal'
            elif data_source == 'weather':
                current_data = await self._get_current_weather_data(config.location)
                metric = config.metadata.get('weather_metric', 'temperature')
                current_value = current_data.get(metric, 0) if current_data else 0
                unit = '°C' if metric == 'temperature' else 'mm' if metric == 'rainfall' else ''
            else:
                return None
            
            # Determine condition met
            condition_met = ""
            if config.threshold_condition == ThresholdCondition.GREATER_THAN:
                condition_met = f"exceeded {config.threshold_value}"
            elif config.threshold_condition == ThresholdCondition.LESS_THAN:
                condition_met = f"dropped below {config.threshold_value}"
            elif config.threshold_condition == ThresholdCondition.EQUALS:
                condition_met = f"reached {config.threshold_value}"
            
            # Create title and message
            title = f"🎯 Custom Alert: {config.commodity or 'Threshold'} - {condition_met}"
            
            message = f"""
🎯 CUSTOM THRESHOLD ALERT 🎯

📊 Metric: {data_source.title()}
🌾 Commodity: {config.commodity or 'N/A'}
📍 Location: {config.location or 'N/A'}
📈 Current Value: {current_value:.2f} {unit}
🎯 Threshold: {config.threshold_value} {unit}
✅ Condition: {condition_met}

⚠️ Your custom alert condition has been triggered.
            """.strip()
            
            alert = CustomThresholdAlert(
                user_id=config.user_id,
                alert_type=AlertType.CUSTOM_THRESHOLD,
                severity=AlertSeverity.MEDIUM,
                title=title,
                message=message,
                commodity=config.commodity,
                location=config.location,
                threshold_config_id=config.id,
                threshold_value=config.threshold_value,
                current_value=current_value,
                condition_met=condition_met,
                trigger_data=current_data or {}
            )
            
            return alert
            
        except Exception as e:
            logger.error("Error creating custom threshold alert", error=str(e))
            return None
    
    async def _store_alert_in_history(self, alert: BaseAlert):
        """Store alert in history"""
        try:
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
            
        except Exception as e:
            logger.error("Error storing alert history", error=str(e))
    
    # Public API methods
    
    async def configure_alert(self, config: AlertConfiguration) -> AlertConfigurationResponse:
        """Configure a new alert"""
        try:
            # Validate configuration
            await self._validate_alert_configuration(config)
            
            # Store configuration
            await store_alert_configuration(config)
            
            # Add to active configurations
            self.active_configurations[config.id] = config
            
            logger.info(
                "Alert configured",
                config_id=config.id,
                user_id=config.user_id,
                alert_type=config.alert_type
            )
            
            return AlertConfigurationResponse(
                alert_id=config.id,
                success=True,
                message="Alert configured successfully",
                configuration=config
            )
            
        except Exception as e:
            logger.error("Error configuring alert", error=str(e))
            return AlertConfigurationResponse(
                alert_id=config.id,
                success=False,
                message=str(e)
            )
    
    async def _validate_alert_configuration(self, config: AlertConfiguration):
        """Validate alert configuration"""
        if config.alert_type in [AlertType.PRICE_MOVEMENT, AlertType.PRICE_RISE, AlertType.PRICE_DROP]:
            if not config.commodity:
                raise ValueError("Commodity is required for price alerts")
        
        if config.threshold_value <= 0:
            raise ValueError("Threshold value must be positive")
        
        if config.max_alerts_per_day <= 0 or config.max_alerts_per_day > 100:
            raise ValueError("Max alerts per day must be between 1 and 100")
    
    async def get_user_alerts(self, user_id: str, active_only: bool = True) -> List[AlertConfiguration]:
        """Get all alerts for a user"""
        try:
            return await get_user_alert_configurations(user_id, active_only)
        except Exception as e:
            logger.error("Error getting user alerts", user_id=user_id, error=str(e))
            return []
    
    async def toggle_alert(self, alert_id: str, user_id: str) -> AlertToggleResponse:
        """Toggle alert active/inactive status"""
        try:
            config = await get_alert_configuration(alert_id, user_id)
            if not config:
                return AlertToggleResponse(
                    alert_id=alert_id,
                    is_active=False,
                    success=False,
                    message="Alert not found"
                )
            
            config.is_active = not config.is_active
            config.updated_at = datetime.utcnow()
            
            await update_alert_configuration(config)
            
            # Update active configurations
            if config.is_active:
                self.active_configurations[alert_id] = config
            else:
                self.active_configurations.pop(alert_id, None)
            
            return AlertToggleResponse(
                alert_id=alert_id,
                is_active=config.is_active,
                success=True,
                message=f"Alert {'activated' if config.is_active else 'deactivated'}"
            )
            
        except Exception as e:
            logger.error("Error toggling alert", alert_id=alert_id, error=str(e))
            return AlertToggleResponse(
                alert_id=alert_id,
                is_active=False,
                success=False,
                message=str(e)
            )
    
    async def delete_alert(self, alert_id: str, user_id: str) -> bool:
        """Delete an alert configuration"""
        try:
            success = await delete_alert_configuration(alert_id, user_id)
            
            if success:
                # Remove from active configurations
                self.active_configurations.pop(alert_id, None)
                self.alert_cache.pop(alert_id, None)
            
            return success
            
        except Exception as e:
            logger.error("Error deleting alert", alert_id=alert_id, error=str(e))
            return False
    
    async def get_alert_history(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0,
        alert_type: Optional[str] = None
    ) -> List[AlertHistory]:
        """Get alert history for a user"""
        try:
            return await get_alert_history(user_id, limit, offset, alert_type)
        except Exception as e:
            logger.error("Error getting alert history", user_id=user_id, error=str(e))
            return []