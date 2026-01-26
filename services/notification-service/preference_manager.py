"""
Notification Preference Manager
Handles user notification preferences and recommendation generation
"""

import asyncio
import structlog
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, time, timedelta
from enum import Enum

from models import (
    UserAlertPreferences, NotificationChannel, AlertType, AlertSeverity,
    BaseAlert, NotificationDelivery
)
from database import get_user_preferences, store_user_preferences

logger = structlog.get_logger()

class PreferenceRecommendation(str, Enum):
    """Types of preference recommendations"""
    ENABLE_EMERGENCY_OVERRIDE = "enable_emergency_override"
    ADD_BACKUP_CHANNEL = "add_backup_channel"
    ADJUST_QUIET_HOURS = "adjust_quiet_hours"
    REDUCE_ALERT_FREQUENCY = "reduce_alert_frequency"
    INCREASE_ALERT_FREQUENCY = "increase_alert_frequency"
    ADD_CONTACT_INFO = "add_contact_info"
    ENABLE_VOICE_ALERTS = "enable_voice_alerts"

class NotificationPreferenceManager:
    """Manages user notification preferences and provides intelligent recommendations"""
    
    def __init__(self):
        self.default_preferences = {
            'preferred_channels': [NotificationChannel.PUSH],
            'preferred_language': 'en',
            'emergency_override': True,
            'max_alerts_per_day': 20,
            'group_similar_alerts': True,
            'alert_frequency': 'immediate'
        }
        
        # Channel priority for different alert severities
        self.severity_channel_priority = {
            AlertSeverity.EMERGENCY: [
                NotificationChannel.VOICE,
                NotificationChannel.SMS,
                NotificationChannel.PUSH,
                NotificationChannel.WHATSAPP
            ],
            AlertSeverity.CRITICAL: [
                NotificationChannel.SMS,
                NotificationChannel.PUSH,
                NotificationChannel.VOICE
            ],
            AlertSeverity.HIGH: [
                NotificationChannel.SMS,
                NotificationChannel.PUSH
            ],
            AlertSeverity.MEDIUM: [
                NotificationChannel.PUSH,
                NotificationChannel.SMS
            ],
            AlertSeverity.LOW: [
                NotificationChannel.PUSH
            ]
        }
    
    async def get_or_create_preferences(self, user_id: str) -> UserAlertPreferences:
        """Get user preferences or create default ones"""
        try:
            preferences = await get_user_preferences(user_id)
            
            if not preferences:
                # Create default preferences
                preferences = UserAlertPreferences(
                    user_id=user_id,
                    **self.default_preferences
                )
                await store_user_preferences(preferences)
                
                logger.info("Created default preferences for user", user_id=user_id)
            
            return preferences
            
        except Exception as e:
            logger.error("Error getting user preferences", user_id=user_id, error=str(e))
            # Return default preferences without storing
            return UserAlertPreferences(
                user_id=user_id,
                **self.default_preferences
            )
    
    async def update_preferences(self, preferences: UserAlertPreferences) -> bool:
        """Update user preferences with validation"""
        try:
            # Validate preferences
            validation_result = await self._validate_preferences(preferences)
            if not validation_result['valid']:
                logger.warning(
                    "Invalid preferences update attempted",
                    user_id=preferences.user_id,
                    errors=validation_result['errors']
                )
                return False
            
            # Apply any automatic adjustments
            adjusted_preferences = await self._apply_intelligent_adjustments(preferences)
            
            # Store updated preferences
            await store_user_preferences(adjusted_preferences)
            
            logger.info("User preferences updated", user_id=preferences.user_id)
            return True
            
        except Exception as e:
            logger.error("Error updating preferences", user_id=preferences.user_id, error=str(e))
            return False
    
    async def _validate_preferences(self, preferences: UserAlertPreferences) -> Dict[str, Any]:
        """Validate user preferences"""
        errors = []
        
        # Validate preferred channels
        if not preferences.preferred_channels or len(preferences.preferred_channels) == 0:
            errors.append("At least one preferred channel must be selected")
        
        # Validate max alerts per day
        if preferences.max_alerts_per_day < 1 or preferences.max_alerts_per_day > 100:
            errors.append("Max alerts per day must be between 1 and 100")
        
        # Validate quiet hours
        if preferences.quiet_hours_start and preferences.quiet_hours_end:
            if preferences.quiet_hours_start == preferences.quiet_hours_end:
                errors.append("Quiet hours start and end cannot be the same")
        
        # Validate contact information for selected channels
        if NotificationChannel.SMS in preferences.preferred_channels and not preferences.phone_number:
            errors.append("Phone number required for SMS notifications")
        
        if NotificationChannel.EMAIL in preferences.preferred_channels and not preferences.email:
            errors.append("Email address required for email notifications")
        
        if NotificationChannel.VOICE in preferences.preferred_channels and not preferences.phone_number:
            errors.append("Phone number required for voice call notifications")
        
        if NotificationChannel.WHATSAPP in preferences.preferred_channels and not preferences.whatsapp_number:
            errors.append("WhatsApp number required for WhatsApp notifications")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    async def _apply_intelligent_adjustments(self, preferences: UserAlertPreferences) -> UserAlertPreferences:
        """Apply intelligent adjustments to preferences"""
        adjusted = preferences.copy()
        
        # Ensure emergency override is enabled for safety
        if not adjusted.emergency_override:
            logger.info("Enabling emergency override for safety", user_id=preferences.user_id)
            adjusted.emergency_override = True
        
        # Add SMS as backup for critical alerts if phone number is available
        if (adjusted.phone_number and 
            NotificationChannel.SMS not in adjusted.preferred_channels and
            len(adjusted.preferred_channels) == 1):
            adjusted.preferred_channels.append(NotificationChannel.SMS)
            logger.info("Added SMS as backup channel", user_id=preferences.user_id)
        
        # Adjust max alerts based on frequency preference
        if adjusted.alert_frequency == 'immediate' and adjusted.max_alerts_per_day < 10:
            adjusted.max_alerts_per_day = 10
        elif adjusted.alert_frequency == 'hourly' and adjusted.max_alerts_per_day > 24:
            adjusted.max_alerts_per_day = 24
        elif adjusted.alert_frequency == 'daily' and adjusted.max_alerts_per_day > 5:
            adjusted.max_alerts_per_day = 5
        
        return adjusted
    
    def determine_delivery_channels(self, alert: BaseAlert, preferences: UserAlertPreferences) -> List[NotificationChannel]:
        """Determine which channels to use for alert delivery"""
        try:
            # Get base channels from preferences
            base_channels = preferences.preferred_channels.copy()
            
            # Adjust based on alert severity
            severity_channels = self.severity_channel_priority.get(alert.severity, [])
            
            # For emergency and critical alerts, ensure multiple channels
            if alert.severity in [AlertSeverity.EMERGENCY, AlertSeverity.CRITICAL]:
                # Add high-priority channels if not already included
                for channel in severity_channels[:2]:  # Top 2 channels for severity
                    if channel not in base_channels:
                        # Check if user has required contact info
                        if self._has_contact_info_for_channel(channel, preferences):
                            base_channels.append(channel)
            
            # Remove channels without required contact information
            valid_channels = []
            for channel in base_channels:
                if self._has_contact_info_for_channel(channel, preferences):
                    valid_channels.append(channel)
                else:
                    logger.warning(
                        "Skipping channel due to missing contact info",
                        user_id=alert.user_id,
                        channel=channel.value
                    )
            
            # Ensure at least one channel
            if not valid_channels:
                valid_channels = [NotificationChannel.PUSH]  # Fallback to push
            
            # Sort by priority for this severity
            valid_channels.sort(key=lambda x: self._get_channel_priority(x, alert.severity))
            
            return valid_channels
            
        except Exception as e:
            logger.error("Error determining delivery channels", error=str(e))
            return [NotificationChannel.PUSH]  # Safe fallback
    
    def _has_contact_info_for_channel(self, channel: NotificationChannel, preferences: UserAlertPreferences) -> bool:
        """Check if user has required contact information for channel"""
        if channel == NotificationChannel.SMS:
            return bool(preferences.phone_number)
        elif channel == NotificationChannel.EMAIL:
            return bool(preferences.email)
        elif channel == NotificationChannel.VOICE:
            return bool(preferences.phone_number)
        elif channel == NotificationChannel.WHATSAPP:
            return bool(preferences.whatsapp_number)
        elif channel == NotificationChannel.PUSH:
            return True  # Always available
        else:
            return False
    
    def _get_channel_priority(self, channel: NotificationChannel, severity: AlertSeverity) -> int:
        """Get channel priority for given severity (lower number = higher priority)"""
        severity_channels = self.severity_channel_priority.get(severity, [])
        try:
            return severity_channels.index(channel)
        except ValueError:
            return 999  # Low priority if not in severity list
    
    def should_send_during_quiet_hours(self, alert: BaseAlert, preferences: UserAlertPreferences) -> bool:
        """Determine if alert should be sent during quiet hours"""
        # Always send emergency alerts
        if alert.severity == AlertSeverity.EMERGENCY:
            return True
        
        # Check emergency override setting
        if alert.severity == AlertSeverity.CRITICAL and preferences.emergency_override:
            return True
        
        # Check if we're in quiet hours
        if not preferences.quiet_hours_start or not preferences.quiet_hours_end:
            return True  # No quiet hours set
        
        now = datetime.now().time()
        start = preferences.quiet_hours_start
        end = preferences.quiet_hours_end
        
        if start <= end:
            # Same day quiet hours
            in_quiet_hours = start <= now <= end
        else:
            # Overnight quiet hours
            in_quiet_hours = now >= start or now <= end
        
        return not in_quiet_hours
    
    async def generate_preference_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """Generate intelligent preference recommendations for user"""
        try:
            preferences = await self.get_or_create_preferences(user_id)
            recommendations = []
            
            # Analyze current preferences and suggest improvements
            
            # Recommendation 1: Enable emergency override if disabled
            if not preferences.emergency_override:
                recommendations.append({
                    'type': PreferenceRecommendation.ENABLE_EMERGENCY_OVERRIDE,
                    'title': 'Enable Emergency Override',
                    'description': 'Allow critical alerts during quiet hours for your safety',
                    'priority': 'high',
                    'action': 'Set emergency override to enabled'
                })
            
            # Recommendation 2: Add backup channel
            if len(preferences.preferred_channels) == 1:
                missing_channels = []
                if preferences.phone_number and NotificationChannel.SMS not in preferences.preferred_channels:
                    missing_channels.append('SMS')
                if preferences.email and NotificationChannel.EMAIL not in preferences.preferred_channels:
                    missing_channels.append('Email')
                
                if missing_channels:
                    recommendations.append({
                        'type': PreferenceRecommendation.ADD_BACKUP_CHANNEL,
                        'title': 'Add Backup Notification Channel',
                        'description': f'Add {", ".join(missing_channels)} as backup for important alerts',
                        'priority': 'medium',
                        'action': f'Enable {missing_channels[0]} notifications'
                    })
            
            # Recommendation 3: Set quiet hours if not set
            if not preferences.quiet_hours_start:
                recommendations.append({
                    'type': PreferenceRecommendation.ADJUST_QUIET_HOURS,
                    'title': 'Set Quiet Hours',
                    'description': 'Set quiet hours to avoid non-critical alerts during sleep',
                    'priority': 'low',
                    'action': 'Set quiet hours (e.g., 10 PM to 6 AM)'
                })
            
            # Recommendation 4: Add missing contact information
            missing_contact = []
            if NotificationChannel.SMS in preferences.preferred_channels and not preferences.phone_number:
                missing_contact.append('phone number')
            if NotificationChannel.EMAIL in preferences.preferred_channels and not preferences.email:
                missing_contact.append('email address')
            if NotificationChannel.WHATSAPP in preferences.preferred_channels and not preferences.whatsapp_number:
                missing_contact.append('WhatsApp number')
            
            if missing_contact:
                recommendations.append({
                    'type': PreferenceRecommendation.ADD_CONTACT_INFO,
                    'title': 'Complete Contact Information',
                    'description': f'Add {", ".join(missing_contact)} to receive all selected notifications',
                    'priority': 'high',
                    'action': f'Add {missing_contact[0]}'
                })
            
            # Recommendation 5: Enable voice alerts for critical situations
            if (preferences.phone_number and 
                NotificationChannel.VOICE not in preferences.preferred_channels):
                recommendations.append({
                    'type': PreferenceRecommendation.ENABLE_VOICE_ALERTS,
                    'title': 'Enable Voice Alerts',
                    'description': 'Get voice calls for emergency weather and price alerts',
                    'priority': 'medium',
                    'action': 'Enable voice call notifications'
                })
            
            # Sort by priority
            priority_order = {'high': 0, 'medium': 1, 'low': 2}
            recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))
            
            return recommendations
            
        except Exception as e:
            logger.error("Error generating preference recommendations", user_id=user_id, error=str(e))
            return []
    
    async def apply_recommendation(self, user_id: str, recommendation_type: PreferenceRecommendation) -> bool:
        """Apply a specific recommendation to user preferences"""
        try:
            preferences = await self.get_or_create_preferences(user_id)
            
            if recommendation_type == PreferenceRecommendation.ENABLE_EMERGENCY_OVERRIDE:
                preferences.emergency_override = True
            
            elif recommendation_type == PreferenceRecommendation.ADD_BACKUP_CHANNEL:
                if preferences.phone_number and NotificationChannel.SMS not in preferences.preferred_channels:
                    preferences.preferred_channels.append(NotificationChannel.SMS)
                elif preferences.email and NotificationChannel.EMAIL not in preferences.preferred_channels:
                    preferences.preferred_channels.append(NotificationChannel.EMAIL)
            
            elif recommendation_type == PreferenceRecommendation.ADJUST_QUIET_HOURS:
                # Set default quiet hours: 10 PM to 6 AM
                preferences.quiet_hours_start = time(22, 0)  # 10 PM
                preferences.quiet_hours_end = time(6, 0)     # 6 AM
            
            elif recommendation_type == PreferenceRecommendation.ENABLE_VOICE_ALERTS:
                if preferences.phone_number and NotificationChannel.VOICE not in preferences.preferred_channels:
                    preferences.preferred_channels.append(NotificationChannel.VOICE)
            
            # Update preferences
            success = await self.update_preferences(preferences)
            
            if success:
                logger.info(
                    "Applied preference recommendation",
                    user_id=user_id,
                    recommendation=recommendation_type.value
                )
            
            return success
            
        except Exception as e:
            logger.error(
                "Error applying recommendation",
                user_id=user_id,
                recommendation=recommendation_type.value,
                error=str(e)
            )
            return False
    
    async def get_delivery_summary(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Get delivery summary for user over specified days"""
        try:
            # In production, would query actual delivery data
            # For now, return simulated summary
            
            summary = {
                'user_id': user_id,
                'period_days': days,
                'total_alerts': 0,
                'alerts_by_channel': {},
                'alerts_by_severity': {},
                'delivery_success_rate': 0.0,
                'average_delivery_time': 0.0,
                'recommendations_applied': 0
            }
            
            # Simulate some data
            import random
            summary['total_alerts'] = random.randint(5, 25)
            summary['delivery_success_rate'] = random.uniform(0.85, 0.98)
            summary['average_delivery_time'] = random.uniform(2.0, 8.0)
            
            return summary
            
        except Exception as e:
            logger.error("Error getting delivery summary", user_id=user_id, error=str(e))
            return {
                'user_id': user_id,
                'period_days': days,
                'total_alerts': 0,
                'error': str(e)
            }
    
    def get_channel_capabilities(self) -> Dict[NotificationChannel, Dict[str, Any]]:
        """Get capabilities and limitations of each notification channel"""
        return {
            NotificationChannel.SMS: {
                'max_length': 160,
                'supports_rich_content': False,
                'delivery_speed': 'fast',
                'reliability': 'high',
                'cost': 'low',
                'requires': ['phone_number']
            },
            NotificationChannel.PUSH: {
                'max_length': 1000,
                'supports_rich_content': True,
                'delivery_speed': 'very_fast',
                'reliability': 'high',
                'cost': 'free',
                'requires': ['app_installation']
            },
            NotificationChannel.EMAIL: {
                'max_length': 'unlimited',
                'supports_rich_content': True,
                'delivery_speed': 'medium',
                'reliability': 'medium',
                'cost': 'free',
                'requires': ['email_address']
            },
            NotificationChannel.VOICE: {
                'max_length': 300,  # words
                'supports_rich_content': False,
                'delivery_speed': 'medium',
                'reliability': 'high',
                'cost': 'high',
                'requires': ['phone_number']
            },
            NotificationChannel.WHATSAPP: {
                'max_length': 4096,
                'supports_rich_content': True,
                'delivery_speed': 'fast',
                'reliability': 'high',
                'cost': 'low',
                'requires': ['whatsapp_number', 'business_api_approval']
            }
        }