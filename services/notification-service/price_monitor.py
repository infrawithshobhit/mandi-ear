"""
Price Movement Monitor
Monitors price movements and generates alerts for significant changes (>10%)
"""

import asyncio
import structlog
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import aiohttp
import json

from models import (
    PriceMovementAlert, AlertType, AlertSeverity, PriceData
)
from database import (
    get_price_data, store_price_data, get_users_by_commodity,
    store_price_alert, get_historical_prices
)
from notification_dispatcher import NotificationDispatcher

logger = structlog.get_logger()

class PriceMovementMonitor:
    """Monitors price movements and generates alerts for significant changes"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.notification_dispatcher: Optional[NotificationDispatcher] = None
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.last_check_time: Optional[datetime] = None
        self.alerts_sent_today = 0
        self.price_cache: Dict[str, PriceData] = {}
        
        # Price movement thresholds
        self.movement_thresholds = {
            'significant': 10.0,  # 10% change triggers alert
            'high': 15.0,         # 15% change is high severity
            'critical': 20.0,     # 20% change is critical
            'emergency': 30.0     # 30% change is emergency
        }
        
        # Commodities to monitor
        self.monitored_commodities = [
            'wheat', 'rice', 'maize', 'bajra', 'jowar',
            'sugarcane', 'cotton', 'soybean', 'groundnut',
            'mustard', 'sunflower', 'sesame', 'castor',
            'turmeric', 'coriander', 'cumin', 'fenugreek',
            'onion', 'potato', 'tomato', 'chilli', 'garlic'
        ]
        
        # Data sources for price information
        self.price_sources = {
            'agmarknet': {
                'url': 'https://agmarknet.gov.in/SearchCmmMkt.aspx',
                'enabled': True,
                'weight': 0.4
            },
            'enam': {
                'url': 'https://enam.gov.in/web/dhanyamandi/home',
                'enabled': True,
                'weight': 0.3
            },
            'local_mandis': {
                'url': 'http://localhost:8003/api/prices',  # Price discovery service
                'enabled': True,
                'weight': 0.3
            }
        }
    
    async def initialize(self):
        """Initialize the price monitor"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60)
            )
            
            self.notification_dispatcher = NotificationDispatcher()
            await self.notification_dispatcher.initialize()
            
            # Load initial price cache
            await self._load_price_cache()
            
            logger.info("Price movement monitor initialized")
            
        except Exception as e:
            logger.error("Failed to initialize price monitor", error=str(e))
            raise
    
    async def shutdown(self):
        """Shutdown the price monitor"""
        await self.stop_monitoring()
        
        if self.notification_dispatcher:
            await self.notification_dispatcher.shutdown()
        
        if self.session:
            await self.session.close()
        
        logger.info("Price monitor shutdown complete")
    
    async def start_monitoring(self):
        """Start price monitoring"""
        if self.is_monitoring:
            logger.warning("Price monitoring already started")
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Price monitoring started")
    
    async def stop_monitoring(self):
        """Stop price monitoring"""
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Price monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop for price movements"""
        while self.is_monitoring:
            try:
                await self.check_price_movements()
                self.last_check_time = datetime.utcnow()
                
                # Check every 15 minutes during market hours (6 AM to 8 PM IST)
                current_hour = datetime.now().hour
                if 6 <= current_hour <= 20:
                    await asyncio.sleep(900)  # 15 minutes
                else:
                    await asyncio.sleep(3600)  # 1 hour during off-hours
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in price monitoring loop", error=str(e))
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    async def _load_price_cache(self):
        """Load recent price data into cache"""
        try:
            for commodity in self.monitored_commodities:
                recent_data = await get_price_data(commodity, limit=1)
                if recent_data:
                    cache_key = f"{commodity}_latest"
                    self.price_cache[cache_key] = recent_data[0]
            
            logger.info("Price cache loaded", cached_items=len(self.price_cache))
            
        except Exception as e:
            logger.error("Error loading price cache", error=str(e))
    
    async def check_price_movements(self):
        """Check for significant price movements across all commodities"""
        try:
            movement_alerts = []
            
            for commodity in self.monitored_commodities:
                try:
                    alerts = await self._check_commodity_price_movement(commodity)
                    movement_alerts.extend(alerts)
                    
                except Exception as e:
                    logger.error("Error checking commodity price", commodity=commodity, error=str(e))
            
            # Send alerts
            for alert in movement_alerts:
                if self.notification_dispatcher:
                    await self.notification_dispatcher.send_notification(alert)
                    self.alerts_sent_today += 1
            
            if movement_alerts:
                logger.info("Price movement alerts generated", count=len(movement_alerts))
            
        except Exception as e:
            logger.error("Error checking price movements", error=str(e))
    
    async def _check_commodity_price_movement(self, commodity: str) -> List[PriceMovementAlert]:
        """Check price movement for a specific commodity"""
        alerts = []
        
        try:
            # Get current price data from multiple sources
            current_prices = await self._fetch_current_prices(commodity)
            if not current_prices:
                return alerts
            
            # Calculate weighted average current price
            current_price = self._calculate_weighted_average(current_prices)
            
            # Get historical price for comparison (24 hours ago)
            historical_prices = await self._get_historical_price(commodity, hours_back=24)
            if not historical_prices:
                return alerts
            
            previous_price = historical_prices.get('price', 0)
            if previous_price == 0:
                return alerts
            
            # Calculate percentage change
            price_change = current_price - previous_price
            percentage_change = (price_change / previous_price) * 100
            
            # Check if movement is significant (>10%)
            if abs(percentage_change) >= self.movement_thresholds['significant']:
                # Determine severity
                severity = self._determine_alert_severity(abs(percentage_change))
                
                # Get affected users
                affected_users = await get_users_by_commodity(commodity)
                
                # Create alerts for each affected user
                for user in affected_users:
                    alert = await self._create_price_movement_alert(
                        user_id=user['user_id'],
                        commodity=commodity,
                        current_price=current_price,
                        previous_price=previous_price,
                        percentage_change=percentage_change,
                        severity=severity,
                        location=user.get('location', 'Multiple markets')
                    )
                    
                    if alert:
                        alerts.append(alert)
                        # Store alert in database
                        await store_price_alert(alert)
            
            # Update price cache
            cache_key = f"{commodity}_latest"
            self.price_cache[cache_key] = PriceData(
                commodity=commodity,
                location="National Average",
                current_price=current_price,
                previous_price=previous_price,
                timestamp=datetime.utcnow(),
                price_change=price_change,
                percentage_change=percentage_change,
                source="aggregated",
                confidence=0.85
            )
            
        except Exception as e:
            logger.error("Error checking commodity price movement", commodity=commodity, error=str(e))
        
        return alerts
    
    async def _fetch_current_prices(self, commodity: str) -> List[Dict[str, Any]]:
        """Fetch current prices from multiple sources"""
        prices = []
        
        try:
            # Fetch from price discovery service (local)
            if self.price_sources['local_mandis']['enabled']:
                local_prices = await self._fetch_from_price_discovery_service(commodity)
                if local_prices:
                    prices.extend(local_prices)
            
            # Simulate fetching from government sources
            # In production, would integrate with actual APIs
            if self.price_sources['agmarknet']['enabled']:
                agmarknet_price = await self._simulate_agmarknet_price(commodity)
                if agmarknet_price:
                    prices.append(agmarknet_price)
            
            if self.price_sources['enam']['enabled']:
                enam_price = await self._simulate_enam_price(commodity)
                if enam_price:
                    prices.append(enam_price)
            
        except Exception as e:
            logger.error("Error fetching current prices", commodity=commodity, error=str(e))
        
        return prices
    
    async def _fetch_from_price_discovery_service(self, commodity: str) -> List[Dict[str, Any]]:
        """Fetch prices from local price discovery service"""
        try:
            url = f"{self.price_sources['local_mandis']['url']}/current/{commodity}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('prices', [])
                else:
                    logger.warning("Price discovery service unavailable", status=response.status)
                    return []
                    
        except Exception as e:
            logger.error("Error fetching from price discovery service", error=str(e))
            return []
    
    async def _simulate_agmarknet_price(self, commodity: str) -> Optional[Dict[str, Any]]:
        """Simulate fetching price from Agmarknet (placeholder)"""
        try:
            # In production, would integrate with actual Agmarknet API
            import random
            base_prices = {
                'wheat': 2000, 'rice': 2500, 'maize': 1800, 'cotton': 5500,
                'soybean': 4000, 'onion': 1200, 'potato': 800, 'tomato': 1500
            }
            
            base_price = base_prices.get(commodity, 2000)
            variation = random.uniform(-0.1, 0.1)  # ±10% variation
            price = base_price * (1 + variation)
            
            return {
                'price': price,
                'source': 'agmarknet',
                'weight': self.price_sources['agmarknet']['weight'],
                'timestamp': datetime.utcnow(),
                'location': 'National Average'
            }
            
        except Exception as e:
            logger.error("Error simulating Agmarknet price", error=str(e))
            return None
    
    async def _simulate_enam_price(self, commodity: str) -> Optional[Dict[str, Any]]:
        """Simulate fetching price from eNAM (placeholder)"""
        try:
            # In production, would integrate with actual eNAM API
            import random
            base_prices = {
                'wheat': 2050, 'rice': 2550, 'maize': 1850, 'cotton': 5600,
                'soybean': 4100, 'onion': 1250, 'potato': 850, 'tomato': 1600
            }
            
            base_price = base_prices.get(commodity, 2050)
            variation = random.uniform(-0.08, 0.08)  # ±8% variation
            price = base_price * (1 + variation)
            
            return {
                'price': price,
                'source': 'enam',
                'weight': self.price_sources['enam']['weight'],
                'timestamp': datetime.utcnow(),
                'location': 'eNAM Markets'
            }
            
        except Exception as e:
            logger.error("Error simulating eNAM price", error=str(e))
            return None
    
    def _calculate_weighted_average(self, prices: List[Dict[str, Any]]) -> float:
        """Calculate weighted average price from multiple sources"""
        if not prices:
            return 0.0
        
        total_weighted_price = 0.0
        total_weight = 0.0
        
        for price_data in prices:
            price = price_data.get('price', 0)
            weight = price_data.get('weight', 1.0)
            
            total_weighted_price += price * weight
            total_weight += weight
        
        return total_weighted_price / total_weight if total_weight > 0 else 0.0
    
    async def _get_historical_price(self, commodity: str, hours_back: int = 24) -> Optional[Dict[str, Any]]:
        """Get historical price for comparison"""
        try:
            # Get from cache first
            cache_key = f"{commodity}_latest"
            if cache_key in self.price_cache:
                cached_data = self.price_cache[cache_key]
                time_diff = datetime.utcnow() - cached_data.timestamp
                
                # If cached data is close to the desired time period, use it
                if abs(time_diff.total_seconds() - (hours_back * 3600)) < 3600:  # Within 1 hour
                    return {
                        'price': cached_data.previous_price or cached_data.current_price,
                        'timestamp': cached_data.timestamp - timedelta(hours=hours_back)
                    }
            
            # Fetch from database
            historical_data = await get_historical_prices(
                commodity, 
                start_time=datetime.utcnow() - timedelta(hours=hours_back + 1),
                end_time=datetime.utcnow() - timedelta(hours=hours_back - 1)
            )
            
            if historical_data:
                return {
                    'price': historical_data[0].get('price', 0),
                    'timestamp': historical_data[0].get('timestamp')
                }
            
            # Simulate historical price if no data available
            current_prices = await self._fetch_current_prices(commodity)
            if current_prices:
                current_price = self._calculate_weighted_average(current_prices)
                # Simulate historical price with some variation
                import random
                variation = random.uniform(-0.15, 0.15)  # ±15% variation
                historical_price = current_price * (1 + variation)
                
                return {
                    'price': historical_price,
                    'timestamp': datetime.utcnow() - timedelta(hours=hours_back)
                }
            
            return None
            
        except Exception as e:
            logger.error("Error getting historical price", commodity=commodity, error=str(e))
            return None
    
    def _determine_alert_severity(self, percentage_change: float) -> AlertSeverity:
        """Determine alert severity based on percentage change"""
        if percentage_change >= self.movement_thresholds['emergency']:
            return AlertSeverity.EMERGENCY
        elif percentage_change >= self.movement_thresholds['critical']:
            return AlertSeverity.CRITICAL
        elif percentage_change >= self.movement_thresholds['high']:
            return AlertSeverity.HIGH
        else:
            return AlertSeverity.MEDIUM
    
    async def _create_price_movement_alert(
        self,
        user_id: str,
        commodity: str,
        current_price: float,
        previous_price: float,
        percentage_change: float,
        severity: AlertSeverity,
        location: str
    ) -> Optional[PriceMovementAlert]:
        """Create a price movement alert"""
        try:
            # Determine alert type based on direction
            if percentage_change > 0:
                alert_type = AlertType.PRICE_RISE
                direction = "risen"
                emoji = "📈"
            else:
                alert_type = AlertType.PRICE_DROP
                direction = "dropped"
                emoji = "📉"
            
            # Create title
            title = f"{emoji} {commodity.title()} Price Alert - {abs(percentage_change):.1f}% {direction.title()}"
            
            # Create detailed message
            message = f"""
🚨 SIGNIFICANT PRICE MOVEMENT DETECTED 🚨

🌾 Commodity: {commodity.title()}
📍 Location: {location}
💰 Current Price: ₹{current_price:.2f}/quintal
📊 Previous Price: ₹{previous_price:.2f}/quintal
{emoji} Change: {percentage_change:+.1f}% (₹{current_price - previous_price:+.2f})

⏰ Time Period: Last 24 hours
🔔 Alert Threshold: {self.movement_thresholds['significant']}%

💡 RECOMMENDATION:
""".strip()
            
            # Add recommendations based on direction and severity
            if percentage_change > 0:
                if severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
                    message += "\n🔥 URGENT: Consider selling immediately if you have stock. Prices may correct soon."
                else:
                    message += "\n📈 Good time to sell if you have inventory. Monitor for further increases."
            else:
                if severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
                    message += "\n⚠️ URGENT: Avoid selling at current prices. Wait for market recovery."
                else:
                    message += "\n📉 Consider holding stock if possible. Look for alternative markets."
            
            message += f"\n\n🕒 Alert generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            alert = PriceMovementAlert(
                user_id=user_id,
                alert_type=alert_type,
                severity=severity,
                title=title,
                message=message,
                commodity=commodity,
                location=location,
                current_price=current_price,
                previous_price=previous_price,
                percentage_change=percentage_change,
                absolute_change=current_price - previous_price,
                price_trend=direction,
                metadata={
                    'threshold_triggered': self.movement_thresholds['significant'],
                    'data_sources': list(self.price_sources.keys()),
                    'monitoring_period': '24h'
                }
            )
            
            return alert
            
        except Exception as e:
            logger.error("Error creating price movement alert", error=str(e))
            return None
    
    # Public API methods
    
    async def force_price_check(self, commodity: Optional[str] = None):
        """Force a price check for specific commodity or all commodities"""
        try:
            if commodity:
                if commodity in self.monitored_commodities:
                    alerts = await self._check_commodity_price_movement(commodity)
                    for alert in alerts:
                        if self.notification_dispatcher:
                            await self.notification_dispatcher.send_notification(alert)
                    
                    logger.info("Forced price check completed", commodity=commodity, alerts=len(alerts))
                else:
                    logger.warning("Commodity not monitored", commodity=commodity)
            else:
                await self.check_price_movements()
                logger.info("Forced price check completed for all commodities")
                
        except Exception as e:
            logger.error("Error in forced price check", commodity=commodity, error=str(e))
    
    async def add_commodity_monitoring(self, commodity: str):
        """Add a new commodity to monitoring list"""
        if commodity not in self.monitored_commodities:
            self.monitored_commodities.append(commodity)
            logger.info("Added commodity to monitoring", commodity=commodity)
    
    async def remove_commodity_monitoring(self, commodity: str):
        """Remove a commodity from monitoring list"""
        if commodity in self.monitored_commodities:
            self.monitored_commodities.remove(commodity)
            # Clean up cache
            cache_key = f"{commodity}_latest"
            self.price_cache.pop(cache_key, None)
            logger.info("Removed commodity from monitoring", commodity=commodity)
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            'is_monitoring': self.is_monitoring,
            'last_check_time': self.last_check_time,
            'alerts_sent_today': self.alerts_sent_today,
            'monitored_commodities': len(self.monitored_commodities),
            'cached_prices': len(self.price_cache),
            'active_sources': sum(1 for source in self.price_sources.values() if source['enabled'])
        }