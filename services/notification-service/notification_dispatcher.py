"""
Notification Dispatcher
Handles multi-channel notification delivery with user preferences
"""

import asyncio
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime, time
import aiohttp
import json

from models import (
    BaseAlert, UserAlertPreferences, NotificationChannel, NotificationDelivery,
    AlertSeverity, NotificationTemplate
)
from database import (
    get_user_preferences, store_user_preferences, store_notification_delivery,
    update_notification_delivery, get_notification_templates
)
from delivery_channels import DeliveryChannelFactory, BaseDeliveryChannel
from preference_manager import NotificationPreferenceManager

logger = structlog.get_logger()

class NotificationDispatcher:
    """Enhanced notification dispatcher with multi-channel delivery and intelligent routing"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.delivery_queue: asyncio.Queue = asyncio.Queue()
        self.delivery_workers: List[asyncio.Task] = []
        self.is_running = False
        self.templates: Dict[str, NotificationTemplate] = {}
        self.preference_manager = NotificationPreferenceManager()
        self.delivery_channels: Dict[NotificationChannel, BaseDeliveryChannel] = {}
        
        # Performance metrics
        self.delivery_stats = {
            'total_sent': 0,
            'successful_deliveries': 0,
            'failed_deliveries': 0,
            'average_delivery_time': 0.0
        }
    
    async def initialize(self):
        """Initialize the notification dispatcher"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=120)
            )
            
            # Initialize delivery channels
            await self._initialize_delivery_channels()
            
            # Load notification templates
            await self._load_templates()
            
            # Start delivery workers
            self.is_running = True
            for i in range(3):  # 3 worker tasks
                worker = asyncio.create_task(self._delivery_worker(f"worker-{i}"))
                self.delivery_workers.append(worker)
            
            logger.info("Enhanced notification dispatcher initialized", 
                       workers=len(self.delivery_workers),
                       channels=len(self.delivery_channels))
            
        except Exception as e:
            logger.error("Failed to initialize notification dispatcher", error=str(e))
            raise
    
    async def _initialize_delivery_channels(self):
        """Initialize all delivery channels"""
        try:
            available_channels = DeliveryChannelFactory.get_available_channels()
            
            for channel_type in available_channels:
                try:
                    channel = DeliveryChannelFactory.create_channel(channel_type)
                    self.delivery_channels[channel_type] = channel
                    logger.info("Initialized delivery channel", channel=channel_type.value)
                except Exception as e:
                    logger.error("Failed to initialize channel", channel=channel_type.value, error=str(e))
            
        except Exception as e:
            logger.error("Error initializing delivery channels", error=str(e))
    
    async def shutdown(self):
        """Shutdown the notification dispatcher"""
        self.is_running = False
        
        # Cancel all workers
        for worker in self.delivery_workers:
            worker.cancel()
        
        # Wait for workers to finish
        if self.delivery_workers:
            await asyncio.gather(*self.delivery_workers, return_exceptions=True)
        
        if self.session:
            await self.session.close()
        
        logger.info("Enhanced notification dispatcher shutdown complete")
    
    async def _load_templates(self):
        """Load notification templates"""
        try:
            templates = await get_notification_templates()
            self.templates = {
                f"{t.alert_type}_{t.severity}_{t.language}_{t.channel}": t 
                for t in templates
            }
            logger.info("Notification templates loaded", count=len(self.templates))
            
        except Exception as e:
            logger.error("Error loading templates", error=str(e))
            # Use default templates if loading fails
            self._create_default_templates()
    
    def _create_default_templates(self):
        """Create default notification templates"""
        # Default templates for different alert types and channels
        default_templates = [
            {
                'alert_type': 'price_movement',
                'severity': 'high',
                'language': 'en',
                'channel': 'sms',
                'title': '🚨 Price Alert: {commodity}',
                'message': '{commodity} price {direction} by {percentage}% to ₹{current_price}. Location: {location}'
            },
            {
                'alert_type': 'weather_emergency',
                'severity': 'critical',
                'language': 'en',
                'channel': 'sms',
                'title': '⚠️ Weather Emergency: {weather_event}',
                'message': 'URGENT: {weather_event} alert for {location}. Take immediate action to protect crops.'
            }
        ]
        
        # Convert to template objects (simplified)
        self.templates = {}
        for template_data in default_templates:
            key = f"{template_data['alert_type']}_{template_data['severity']}_{template_data['language']}_{template_data['channel']}"
            # In production, would create proper NotificationTemplate objects
            self.templates[key] = template_data
    
    async def _delivery_worker(self, worker_id: str):
        """Enhanced worker task for processing delivery queue"""
        logger.info("Enhanced delivery worker started", worker_id=worker_id)
        
        while self.is_running:
            try:
                # Wait for delivery task
                delivery = await asyncio.wait_for(
                    self.delivery_queue.get(),
                    timeout=5.0
                )
                
                start_time = datetime.utcnow()
                success = await self._process_delivery_enhanced(delivery)
                end_time = datetime.utcnow()
                
                # Update performance metrics
                self.delivery_stats['total_sent'] += 1
                if success:
                    self.delivery_stats['successful_deliveries'] += 1
                else:
                    self.delivery_stats['failed_deliveries'] += 1
                
                # Update average delivery time
                delivery_time = (end_time - start_time).total_seconds()
                current_avg = self.delivery_stats['average_delivery_time']
                total_sent = self.delivery_stats['total_sent']
                self.delivery_stats['average_delivery_time'] = (
                    (current_avg * (total_sent - 1) + delivery_time) / total_sent
                )
                
                self.delivery_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in enhanced delivery worker", worker_id=worker_id, error=str(e))
        
        logger.info("Enhanced delivery worker stopped", worker_id=worker_id)
    
    async def _process_delivery_enhanced(self, delivery: NotificationDelivery) -> bool:
        """Process a single notification delivery using enhanced channels"""
        try:
            # Update status to sending
            delivery.status = "sending"
            delivery.sent_at = datetime.utcnow()
            await update_notification_delivery(delivery)
            
            # Get user preferences
            preferences = await self.preference_manager.get_or_create_preferences(delivery.user_id)
            
            # Get delivery channel
            channel = self.delivery_channels.get(delivery.channel)
            if not channel:
                logger.error("Delivery channel not available", channel=delivery.channel.value)
                delivery.status = "failed"
                delivery.failure_reason = f"Channel {delivery.channel.value} not available"
                await update_notification_delivery(delivery)
                return False
            
            # Send notification using enhanced channel
            success = await channel.send(delivery, preferences)
            
            # Update delivery status
            if success:
                delivery.status = "delivered"
                delivery.delivered_at = datetime.utcnow()
            else:
                delivery.status = "failed"
                delivery.retry_count += 1
                
                # Retry if under limit
                if delivery.retry_count < delivery.max_retries:
                    delivery.status = "pending"
                    await asyncio.sleep(min(delivery.retry_count * 30, 300))  # Exponential backoff
                    await self.delivery_queue.put(delivery)
            
            await update_notification_delivery(delivery)
            
            logger.info(
                "Enhanced notification delivery processed",
                delivery_id=delivery.id,
                channel=delivery.channel.value,
                status=delivery.status,
                retry_count=delivery.retry_count
            )
            
            return success
            
        except Exception as e:
            logger.error("Error processing enhanced delivery", delivery_id=delivery.id, error=str(e))
            delivery.status = "failed"
            delivery.failure_reason = str(e)
            await update_notification_delivery(delivery)
            return False
    
    # Public API methods
    
    async def send_notification(self, alert: BaseAlert):
        """Send notification for an alert using enhanced routing"""
        try:
            # Get user preferences
            preferences = await self.preference_manager.get_or_create_preferences(alert.user_id)
            
            # Check if we should send during quiet hours
            if not self.preference_manager.should_send_during_quiet_hours(alert, preferences):
                logger.info("Skipping notification due to quiet hours", alert_id=alert.id)
                return
            
            # Determine channels to use with intelligent routing
            channels = self.preference_manager.determine_delivery_channels(alert, preferences)
            
            # Create delivery tasks for each channel
            deliveries_created = 0
            for channel in channels:
                # Check if channel is available
                if channel not in self.delivery_channels:
                    logger.warning("Channel not available, skipping", channel=channel.value)
                    continue
                
                delivery = NotificationDelivery(
                    alert_id=alert.id,
                    user_id=alert.user_id,
                    channel=channel,
                    status="pending",
                    metadata={
                        'alert_type': alert.alert_type.value,
                        'severity': alert.severity.value,
                        'title': alert.title,
                        'message': alert.message,
                        'commodity': alert.commodity,
                        'location': alert.location,
                        'timestamp': alert.created_at.isoformat()
                    }
                )
                
                # Store delivery record
                await store_notification_delivery(delivery)
                
                # Add to delivery queue
                await self.delivery_queue.put(delivery)
                deliveries_created += 1
            
            logger.info(
                "Enhanced notification queued for delivery",
                alert_id=alert.id,
                user_id=alert.user_id,
                channels=deliveries_created,
                alert_severity=alert.severity.value
            )
            
        except Exception as e:
            logger.error("Error sending enhanced notification", alert_id=alert.id, error=str(e))
    
    async def send_bulk_notification(self, alert: BaseAlert, user_ids: List[str]):
        """Send notification to multiple users efficiently"""
        try:
            tasks = []
            for user_id in user_ids:
                # Create a copy of the alert for each user
                user_alert = BaseAlert(
                    user_id=user_id,
                    alert_type=alert.alert_type,
                    severity=alert.severity,
                    title=alert.title,
                    message=alert.message,
                    commodity=alert.commodity,
                    location=alert.location,
                    metadata=alert.metadata
                )
                
                # Create task for sending notification
                task = asyncio.create_task(self.send_notification(user_alert))
                tasks.append(task)
            
            # Send all notifications concurrently
            await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.info("Bulk notification sent", user_count=len(user_ids), alert_type=alert.alert_type.value)
            
        except Exception as e:
            logger.error("Error sending bulk notification", error=str(e))
    
    async def update_user_preferences(self, preferences: UserAlertPreferences):
        """Update user notification preferences"""
        try:
            success = await self.preference_manager.update_preferences(preferences)
            if success:
                logger.info("User preferences updated via dispatcher", user_id=preferences.user_id)
            return success
            
        except Exception as e:
            logger.error("Error updating user preferences via dispatcher", user_id=preferences.user_id, error=str(e))
            return False
    
    async def get_user_preferences(self, user_id: str) -> Optional[UserAlertPreferences]:
        """Get user notification preferences"""
        try:
            return await self.preference_manager.get_or_create_preferences(user_id)
        except Exception as e:
            logger.error("Error getting user preferences via dispatcher", user_id=user_id, error=str(e))
            return None
    
    async def get_preference_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get preference recommendations for user"""
        try:
            return await self.preference_manager.generate_preference_recommendations(user_id)
        except Exception as e:
            logger.error("Error getting preference recommendations", user_id=user_id, error=str(e))
            return []
    
    async def apply_preference_recommendation(self, user_id: str, recommendation_type: str) -> bool:
        """Apply a preference recommendation"""
        try:
            from preference_manager import PreferenceRecommendation
            rec_type = PreferenceRecommendation(recommendation_type)
            return await self.preference_manager.apply_recommendation(user_id, rec_type)
        except Exception as e:
            logger.error("Error applying preference recommendation", user_id=user_id, error=str(e))
            return False
    
    async def get_delivery_statistics(self) -> Dict[str, Any]:
        """Get delivery performance statistics"""
        try:
            stats = self.delivery_stats.copy()
            
            # Calculate success rate
            total_sent = stats['total_sent']
            if total_sent > 0:
                stats['success_rate'] = stats['successful_deliveries'] / total_sent
                stats['failure_rate'] = stats['failed_deliveries'] / total_sent
            else:
                stats['success_rate'] = 0.0
                stats['failure_rate'] = 0.0
            
            # Add queue status
            stats['queue_size'] = self.delivery_queue.qsize()
            stats['active_workers'] = len([w for w in self.delivery_workers if not w.done()])
            stats['available_channels'] = len(self.delivery_channels)
            
            return stats
            
        except Exception as e:
            logger.error("Error getting delivery statistics", error=str(e))
            return {'error': str(e)}
    
    async def test_delivery_channel(self, user_id: str, channel: NotificationChannel) -> Dict[str, Any]:
        """Test a specific delivery channel for a user"""
        try:
            # Get user preferences
            preferences = await self.preference_manager.get_or_create_preferences(user_id)
            
            # Get delivery channel
            delivery_channel = self.delivery_channels.get(channel)
            if not delivery_channel:
                return {
                    'success': False,
                    'error': f'Channel {channel.value} not available'
                }
            
            # Validate delivery requirements
            can_deliver = await delivery_channel.validate_delivery_data(None, preferences)
            if not can_deliver:
                return {
                    'success': False,
                    'error': f'Missing required information for {channel.value}'
                }
            
            # Create test delivery
            test_delivery = NotificationDelivery(
                alert_id="test_alert",
                user_id=user_id,
                channel=channel,
                status="pending",
                metadata={
                    'alert_type': 'test',
                    'severity': 'low',
                    'title': 'Test Notification',
                    'message': 'This is a test notification to verify your delivery settings.',
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            # Send test notification
            success = await delivery_channel.send(test_delivery, preferences)
            
            return {
                'success': success,
                'channel': channel.value,
                'message': 'Test notification sent successfully' if success else 'Test notification failed'
            }
            
        except Exception as e:
            logger.error("Error testing delivery channel", user_id=user_id, channel=channel.value, error=str(e))
            return {
                'success': False,
                'error': str(e)
            }