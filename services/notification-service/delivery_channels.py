"""
Notification Delivery Channels
Implements specific delivery mechanisms for different notification channels
"""

import asyncio
import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime
import aiohttp
import json
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

from models import (
    NotificationDelivery, NotificationChannel, UserAlertPreferences,
    BaseAlert, AlertSeverity
)

logger = structlog.get_logger()

class BaseDeliveryChannel:
    """Base class for notification delivery channels"""
    
    def __init__(self, channel: NotificationChannel):
        self.channel = channel
        self.is_enabled = True
        self.max_retries = 3
        self.timeout = 30
    
    async def send(self, delivery: NotificationDelivery, preferences: UserAlertPreferences) -> bool:
        """Send notification through this channel"""
        raise NotImplementedError("Subclasses must implement send method")
    
    async def validate_delivery_data(self, delivery: NotificationDelivery, preferences: UserAlertPreferences) -> bool:
        """Validate that required data is available for delivery"""
        return True
    
    def format_message(self, delivery: NotificationDelivery, preferences: UserAlertPreferences) -> Dict[str, str]:
        """Format message for this channel"""
        metadata = delivery.metadata or {}
        
        title = metadata.get('title', 'MANDI EAR Alert')
        message = metadata.get('message', 'You have a new alert')
        
        # Truncate for channels with length limits
        if self.channel == NotificationChannel.SMS:
            # SMS limit: 160 characters
            if len(message) > 140:
                message = message[:137] + "..."
        
        return {
            'title': title,
            'message': message,
            'formatted_content': self._format_content_for_channel(title, message, metadata)
        }
    
    def _format_content_for_channel(self, title: str, message: str, metadata: Dict[str, Any]) -> str:
        """Format content specifically for this channel"""
        return f"{title}\n\n{message}"

class SMSDeliveryChannel(BaseDeliveryChannel):
    """SMS notification delivery channel"""
    
    def __init__(self):
        super().__init__(NotificationChannel.SMS)
        self.api_url = "https://api.sms-service.com/send"
        self.api_key = "your_sms_api_key"
        self.sender_id = "MANDIEAR"
    
    async def validate_delivery_data(self, delivery: NotificationDelivery, preferences: UserAlertPreferences) -> bool:
        """Validate SMS delivery requirements"""
        if not preferences.phone_number:
            logger.warning("No phone number for SMS delivery", user_id=delivery.user_id)
            return False
        
        # Validate phone number format
        phone = preferences.phone_number.strip()
        if not phone or len(phone) < 10:
            logger.warning("Invalid phone number format", user_id=delivery.user_id, phone=phone)
            return False
        
        return True
    
    async def send(self, delivery: NotificationDelivery, preferences: UserAlertPreferences) -> bool:
        """Send SMS notification"""
        try:
            if not await self.validate_delivery_data(delivery, preferences):
                return False
            
            formatted = self.format_message(delivery, preferences)
            
            # Prepare SMS payload
            payload = {
                'to': preferences.phone_number,
                'from': self.sender_id,
                'message': formatted['formatted_content'],
                'api_key': self.api_key
            }
            
            # In production, would make actual API call
            # For now, simulate SMS sending
            await self._simulate_sms_send(payload)
            
            logger.info(
                "SMS sent successfully",
                user_id=delivery.user_id,
                phone=preferences.phone_number,
                message_length=len(formatted['formatted_content'])
            )
            
            return True
            
        except Exception as e:
            logger.error("Error sending SMS", delivery_id=delivery.id, error=str(e))
            return False
    
    async def _simulate_sms_send(self, payload: Dict[str, Any]):
        """Simulate SMS sending (for development/testing)"""
        # Simulate network delay
        await asyncio.sleep(0.1)
        
        # Log the SMS that would be sent
        logger.info(
            "SMS simulation",
            to=payload['to'],
            message=payload['message'][:50] + "..." if len(payload['message']) > 50 else payload['message']
        )
    
    def _format_content_for_channel(self, title: str, message: str, metadata: Dict[str, Any]) -> str:
        """Format SMS content with character limits"""
        # SMS-specific formatting
        content = f"🚨 {title}\n\n{message}"
        
        # Add actionable recommendations if available
        if metadata.get('alert_type') in ['price_movement', 'price_rise', 'price_drop']:
            content += f"\n\n💡 Check MANDI EAR app for detailed recommendations"
        
        # Ensure within SMS limits
        if len(content) > 160:
            content = content[:157] + "..."
        
        return content

class PushNotificationChannel(BaseDeliveryChannel):
    """Push notification delivery channel"""
    
    def __init__(self):
        super().__init__(NotificationChannel.PUSH)
        self.fcm_url = "https://fcm.googleapis.com/fcm/send"
        self.server_key = "your_fcm_server_key"
    
    async def validate_delivery_data(self, delivery: NotificationDelivery, preferences: UserAlertPreferences) -> bool:
        """Validate push notification requirements"""
        # In production, would check for device tokens
        # For now, assume all users have push capability
        return True
    
    async def send(self, delivery: NotificationDelivery, preferences: UserAlertPreferences) -> bool:
        """Send push notification"""
        try:
            formatted = self.format_message(delivery, preferences)
            metadata = delivery.metadata or {}
            
            # Prepare push notification payload
            payload = {
                'to': f"user_device_token_{delivery.user_id}",  # Would be actual device token
                'notification': {
                    'title': formatted['title'],
                    'body': formatted['message'],
                    'icon': 'mandi_ear_icon',
                    'sound': 'default'
                },
                'data': {
                    'alert_id': delivery.alert_id,
                    'alert_type': metadata.get('alert_type', ''),
                    'commodity': metadata.get('commodity', ''),
                    'location': metadata.get('location', ''),
                    'severity': metadata.get('severity', ''),
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            
            # Add priority based on alert severity
            severity = metadata.get('severity', 'medium')
            if severity in ['critical', 'emergency']:
                payload['priority'] = 'high'
                payload['notification']['sound'] = 'emergency_alert'
            
            # In production, would make actual FCM API call
            await self._simulate_push_send(payload)
            
            logger.info(
                "Push notification sent successfully",
                user_id=delivery.user_id,
                title=formatted['title']
            )
            
            return True
            
        except Exception as e:
            logger.error("Error sending push notification", delivery_id=delivery.id, error=str(e))
            return False
    
    async def _simulate_push_send(self, payload: Dict[str, Any]):
        """Simulate push notification sending"""
        await asyncio.sleep(0.05)
        
        logger.info(
            "Push notification simulation",
            to=payload['to'],
            title=payload['notification']['title'],
            body=payload['notification']['body'][:50] + "..." if len(payload['notification']['body']) > 50 else payload['notification']['body']
        )

class EmailDeliveryChannel(BaseDeliveryChannel):
    """Email notification delivery channel"""
    
    def __init__(self):
        super().__init__(NotificationChannel.EMAIL)
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = "alerts@mandiear.com"
        self.sender_password = "your_email_password"
    
    async def validate_delivery_data(self, delivery: NotificationDelivery, preferences: UserAlertPreferences) -> bool:
        """Validate email delivery requirements"""
        if not preferences.email:
            logger.warning("No email address for email delivery", user_id=delivery.user_id)
            return False
        
        # Basic email validation
        email = preferences.email.strip()
        if not email or '@' not in email or '.' not in email:
            logger.warning("Invalid email format", user_id=delivery.user_id, email=email)
            return False
        
        return True
    
    async def send(self, delivery: NotificationDelivery, preferences: UserAlertPreferences) -> bool:
        """Send email notification"""
        try:
            if not await self.validate_delivery_data(delivery, preferences):
                return False
            
            formatted = self.format_message(delivery, preferences)
            
            # Create email content
            html_content = self._create_html_email(formatted, delivery.metadata or {})
            
            # In production, would send actual email
            await self._simulate_email_send(preferences.email, formatted['title'], html_content)
            
            logger.info(
                "Email sent successfully",
                user_id=delivery.user_id,
                email=preferences.email,
                subject=formatted['title']
            )
            
            return True
            
        except Exception as e:
            logger.error("Error sending email", delivery_id=delivery.id, error=str(e))
            return False
    
    def _create_html_email(self, formatted: Dict[str, str], metadata: Dict[str, Any]) -> str:
        """Create HTML email content"""
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{formatted['title']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .header {{ background-color: #2E7D32; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .content {{ line-height: 1.6; color: #333; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }}
                .alert-high {{ border-left: 4px solid #f44336; padding-left: 15px; }}
                .alert-medium {{ border-left: 4px solid #ff9800; padding-left: 15px; }}
                .alert-low {{ border-left: 4px solid #4caf50; padding-left: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🌾 MANDI EAR™ Alert</h2>
                </div>
                <div class="content">
                    <h3>{formatted['title']}</h3>
                    <div class="alert-{metadata.get('severity', 'medium')}">
                        <p>{formatted['message'].replace(chr(10), '<br>')}</p>
                    </div>
                    
                    {self._add_metadata_section(metadata)}
                </div>
                <div class="footer">
                    <p>This alert was sent by MANDI EAR™ - India's Agricultural Intelligence Platform</p>
                    <p>To manage your alert preferences, visit the MANDI EAR app or website.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def _add_metadata_section(self, metadata: Dict[str, Any]) -> str:
        """Add metadata section to email"""
        if not metadata:
            return ""
        
        sections = []
        
        if metadata.get('commodity'):
            sections.append(f"<p><strong>Commodity:</strong> {metadata['commodity']}</p>")
        
        if metadata.get('location'):
            sections.append(f"<p><strong>Location:</strong> {metadata['location']}</p>")
        
        if metadata.get('alert_type'):
            sections.append(f"<p><strong>Alert Type:</strong> {metadata['alert_type'].replace('_', ' ').title()}</p>")
        
        if sections:
            return f"<div style='margin-top: 20px; padding: 15px; background-color: #f9f9f9; border-radius: 5px;'>{''.join(sections)}</div>"
        
        return ""
    
    async def _simulate_email_send(self, to_email: str, subject: str, html_content: str):
        """Simulate email sending"""
        await asyncio.sleep(0.2)
        
        logger.info(
            "Email simulation",
            to=to_email,
            subject=subject,
            content_length=len(html_content)
        )

class VoiceCallChannel(BaseDeliveryChannel):
    """Voice call notification delivery channel"""
    
    def __init__(self):
        super().__init__(NotificationChannel.VOICE)
        self.voice_api_url = "https://api.voice-service.com/call"
        self.api_key = "your_voice_api_key"
    
    async def validate_delivery_data(self, delivery: NotificationDelivery, preferences: UserAlertPreferences) -> bool:
        """Validate voice call requirements"""
        if not preferences.phone_number:
            logger.warning("No phone number for voice call", user_id=delivery.user_id)
            return False
        
        # Only use voice calls for high severity alerts
        metadata = delivery.metadata or {}
        severity = metadata.get('severity', 'medium')
        if severity not in ['high', 'critical', 'emergency']:
            logger.info("Voice call skipped for non-critical alert", severity=severity)
            return False
        
        return True
    
    async def send(self, delivery: NotificationDelivery, preferences: UserAlertPreferences) -> bool:
        """Send voice call notification"""
        try:
            if not await self.validate_delivery_data(delivery, preferences):
                return False
            
            formatted = self.format_message(delivery, preferences)
            
            # Create voice script
            voice_script = self._create_voice_script(formatted, delivery.metadata or {}, preferences)
            
            # Prepare voice call payload
            payload = {
                'to': preferences.phone_number,
                'script': voice_script,
                'language': preferences.preferred_language or 'en',
                'voice': 'female',  # Default voice
                'api_key': self.api_key
            }
            
            # In production, would make actual voice API call
            await self._simulate_voice_call(payload)
            
            logger.info(
                "Voice call initiated successfully",
                user_id=delivery.user_id,
                phone=preferences.phone_number,
                language=payload['language']
            )
            
            return True
            
        except Exception as e:
            logger.error("Error initiating voice call", delivery_id=delivery.id, error=str(e))
            return False
    
    def _create_voice_script(self, formatted: Dict[str, str], metadata: Dict[str, Any], preferences: UserAlertPreferences) -> str:
        """Create voice script for the call"""
        language = preferences.preferred_language or 'en'
        
        # Basic voice script in English (would be localized in production)
        script = f"""
        Hello, this is an urgent alert from MANDI EAR.
        
        {formatted['title']}
        
        {formatted['message']}
        
        Please check your MANDI EAR app for detailed information and recommendations.
        
        Thank you.
        """
        
        # Clean up the script for voice synthesis
        script = script.replace('\n', ' ').replace('  ', ' ').strip()
        
        return script
    
    async def _simulate_voice_call(self, payload: Dict[str, Any]):
        """Simulate voice call"""
        await asyncio.sleep(0.5)  # Simulate call setup time
        
        logger.info(
            "Voice call simulation",
            to=payload['to'],
            language=payload['language'],
            script_length=len(payload['script'])
        )

class WhatsAppChannel(BaseDeliveryChannel):
    """WhatsApp notification delivery channel"""
    
    def __init__(self):
        super().__init__(NotificationChannel.WHATSAPP)
        self.whatsapp_api_url = "https://api.whatsapp-business.com/send"
        self.api_key = "your_whatsapp_api_key"
        self.is_enabled = False  # Disabled by default (requires WhatsApp Business API approval)
    
    async def validate_delivery_data(self, delivery: NotificationDelivery, preferences: UserAlertPreferences) -> bool:
        """Validate WhatsApp delivery requirements"""
        if not self.is_enabled:
            return False
        
        if not preferences.whatsapp_number:
            logger.warning("No WhatsApp number for delivery", user_id=delivery.user_id)
            return False
        
        return True
    
    async def send(self, delivery: NotificationDelivery, preferences: UserAlertPreferences) -> bool:
        """Send WhatsApp notification"""
        try:
            if not await self.validate_delivery_data(delivery, preferences):
                return False
            
            formatted = self.format_message(delivery, preferences)
            
            # Prepare WhatsApp payload
            payload = {
                'to': preferences.whatsapp_number,
                'type': 'text',
                'text': {
                    'body': formatted['formatted_content']
                },
                'api_key': self.api_key
            }
            
            # In production, would make actual WhatsApp API call
            await self._simulate_whatsapp_send(payload)
            
            logger.info(
                "WhatsApp message sent successfully",
                user_id=delivery.user_id,
                whatsapp=preferences.whatsapp_number
            )
            
            return True
            
        except Exception as e:
            logger.error("Error sending WhatsApp message", delivery_id=delivery.id, error=str(e))
            return False
    
    async def _simulate_whatsapp_send(self, payload: Dict[str, Any]):
        """Simulate WhatsApp sending"""
        await asyncio.sleep(0.1)
        
        logger.info(
            "WhatsApp simulation",
            to=payload['to'],
            message=payload['text']['body'][:50] + "..." if len(payload['text']['body']) > 50 else payload['text']['body']
        )
    
    def _format_content_for_channel(self, title: str, message: str, metadata: Dict[str, Any]) -> str:
        """Format WhatsApp content with rich formatting"""
        # WhatsApp supports basic markdown formatting
        content = f"*🚨 {title}*\n\n{message}"
        
        # Add metadata in a structured format
        if metadata.get('commodity'):
            content += f"\n\n🌾 *Commodity:* {metadata['commodity']}"
        
        if metadata.get('location'):
            content += f"\n📍 *Location:* {metadata['location']}"
        
        if metadata.get('alert_type'):
            content += f"\n🔔 *Alert Type:* {metadata['alert_type'].replace('_', ' ').title()}"
        
        content += f"\n\n💡 _Check MANDI EAR app for detailed recommendations_"
        
        return content

# Channel factory
class DeliveryChannelFactory:
    """Factory for creating delivery channel instances"""
    
    _channels = {
        NotificationChannel.SMS: SMSDeliveryChannel,
        NotificationChannel.PUSH: PushNotificationChannel,
        NotificationChannel.EMAIL: EmailDeliveryChannel,
        NotificationChannel.VOICE: VoiceCallChannel,
        NotificationChannel.WHATSAPP: WhatsAppChannel
    }
    
    @classmethod
    def create_channel(cls, channel_type: NotificationChannel) -> BaseDeliveryChannel:
        """Create a delivery channel instance"""
        channel_class = cls._channels.get(channel_type)
        if not channel_class:
            raise ValueError(f"Unsupported channel type: {channel_type}")
        
        return channel_class()
    
    @classmethod
    def get_available_channels(cls) -> List[NotificationChannel]:
        """Get list of available delivery channels"""
        return list(cls._channels.keys())
    
    @classmethod
    def is_channel_supported(cls, channel_type: NotificationChannel) -> bool:
        """Check if a channel type is supported"""
        return channel_type in cls._channels