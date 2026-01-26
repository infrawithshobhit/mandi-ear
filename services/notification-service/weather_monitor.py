"""
Weather Emergency Monitor
Monitors weather conditions and generates emergency alerts
"""

import asyncio
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import aiohttp
import json

from models import (
    WeatherEmergencyAlert, WeatherEventType, AlertSeverity, WeatherData,
    AlertType
)
from database import (
    get_weather_data, store_weather_data, get_users_by_location,
    store_weather_alert
)
from notification_dispatcher import NotificationDispatcher

logger = structlog.get_logger()

class WeatherEmergencyMonitor:
    """Monitors weather conditions and generates emergency alerts"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.notification_dispatcher: Optional[NotificationDispatcher] = None
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.last_check_time: Optional[datetime] = None
        self.alerts_sent_today = 0
        
        # Weather API configurations
        self.weather_apis = {
            'primary': {
                'url': 'https://api.openweathermap.org/data/2.5',
                'key': 'your_api_key_here',
                'enabled': True
            },
            'backup': {
                'url': 'https://api.weatherapi.com/v1',
                'key': 'your_backup_key_here',
                'enabled': False
            }
        }
        
        # Emergency thresholds
        self.emergency_thresholds = {
            WeatherEventType.HEAVY_RAIN: {
                'warning': 50,  # mm in 24h
                'emergency': 100,  # mm in 24h
                'critical': 200   # mm in 24h
            },
            WeatherEventType.EXTREME_HEAT: {
                'warning': 40,  # °C
                'emergency': 45,  # °C
                'critical': 50   # °C
            },
            WeatherEventType.WIND_STORM: {
                'warning': 40,  # km/h
                'emergency': 60,  # km/h
                'critical': 80   # km/h
            },
            WeatherEventType.HAILSTORM: {
                'warning': 10,  # mm hail size
                'emergency': 20,  # mm hail size
                'critical': 30   # mm hail size
            }
        }
        
        # Locations to monitor (major agricultural regions)
        self.monitored_locations = [
            {'name': 'Punjab', 'lat': 31.1471, 'lon': 75.3412},
            {'name': 'Haryana', 'lat': 29.0588, 'lon': 76.0856},
            {'name': 'Uttar Pradesh', 'lat': 26.8467, 'lon': 80.9462},
            {'name': 'Madhya Pradesh', 'lat': 22.9734, 'lon': 78.6569},
            {'name': 'Maharashtra', 'lat': 19.7515, 'lon': 75.7139},
            {'name': 'Gujarat', 'lat': 22.2587, 'lon': 71.1924},
            {'name': 'Rajasthan', 'lat': 27.0238, 'lon': 74.2179},
            {'name': 'Karnataka', 'lat': 15.3173, 'lon': 75.7139},
            {'name': 'Andhra Pradesh', 'lat': 15.9129, 'lon': 79.7400},
            {'name': 'Tamil Nadu', 'lat': 11.1271, 'lon': 78.6569},
            {'name': 'West Bengal', 'lat': 22.9868, 'lon': 87.8550},
            {'name': 'Bihar', 'lat': 25.0961, 'lon': 85.3131},
            {'name': 'Odisha', 'lat': 20.9517, 'lon': 85.0985}
        ]
    
    async def initialize(self):
        """Initialize the weather monitor"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60)
            )
            
            self.notification_dispatcher = NotificationDispatcher()
            await self.notification_dispatcher.initialize()
            
            logger.info("Weather emergency monitor initialized")
            
        except Exception as e:
            logger.error("Failed to initialize weather monitor", error=str(e))
            raise
    
    async def shutdown(self):
        """Shutdown the weather monitor"""
        await self.stop_monitoring()
        
        if self.notification_dispatcher:
            await self.notification_dispatcher.shutdown()
        
        if self.session:
            await self.session.close()
        
        logger.info("Weather monitor shutdown complete")
    
    async def start_monitoring(self):
        """Start weather monitoring"""
        if self.is_monitoring:
            logger.warning("Weather monitoring already started")
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Weather monitoring started")
    
    async def stop_monitoring(self):
        """Stop weather monitoring"""
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Weather monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop for weather emergencies"""
        while self.is_monitoring:
            try:
                await self.check_weather_emergencies()
                self.last_check_time = datetime.utcnow()
                
                # Check every 30 minutes
                await asyncio.sleep(1800)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in weather monitoring loop", error=str(e))
                await asyncio.sleep(600)  # Wait 10 minutes before retrying
    
    async def check_weather_emergencies(self):
        """Check for weather emergencies across all monitored locations"""
        try:
            emergency_alerts = []
            
            for location in self.monitored_locations:
                try:
                    alerts = await self._check_location_weather(location)
                    emergency_alerts.extend(alerts)
                    
                except Exception as e:
                    logger.error("Error checking location weather", location=location['name'], error=str(e))
            
            # Send alerts
            for alert in emergency_alerts:
                if self.notification_dispatcher:
                    await self.notification_dispatcher.send_notification(alert)
                    self.alerts_sent_today += 1
            
            if emergency_alerts:
                logger.info("Weather emergency alerts generated", count=len(emergency_alerts))
            
        except Exception as e:
            logger.error("Error checking weather emergencies", error=str(e))
    
    async def _check_location_weather(self, location: Dict[str, Any]) -> List[WeatherEmergencyAlert]:
        """Check weather conditions for a specific location"""
        alerts = []
        
        try:
            # Fetch current weather data
            weather_data = await self._fetch_weather_data(location)
            if not weather_data:
                return alerts
            
            # Store weather data
            await store_weather_data(weather_data)
            
            # Check for emergency conditions
            emergency_events = await self._detect_weather_emergencies(weather_data)
            
            if emergency_events:
                # Get affected users in this location
                affected_users = await get_users_by_location(location['name'])
                
                # Create alerts for each emergency event
                for event in emergency_events:
                    for user in affected_users:
                        alert = await self._create_weather_emergency_alert(
                            user_id=user['user_id'],
                            location=location['name'],
                            weather_event=event['type'],
                            intensity=event['intensity'],
                            weather_data=weather_data,
                            event_data=event
                        )
                        
                        if alert:
                            alerts.append(alert)
                            # Store alert in database
                            await store_weather_alert(alert)
            
        except Exception as e:
            logger.error("Error checking location weather", location=location['name'], error=str(e))
        
        return alerts
    
    async def _fetch_weather_data(self, location: Dict[str, Any]) -> Optional[WeatherData]:
        """Fetch weather data for a location"""
        try:
            # Try primary weather API first
            if self.weather_apis['primary']['enabled']:
                data = await self._fetch_from_openweather(location)
                if data:
                    return data
            
            # Try backup API if primary fails
            if self.weather_apis['backup']['enabled']:
                data = await self._fetch_from_weatherapi(location)
                if data:
                    return data
            
            # Simulate weather data if APIs are not available
            return await self._simulate_weather_data(location)
            
        except Exception as e:
            logger.error("Error fetching weather data", location=location['name'], error=str(e))
            return None
    
    async def _fetch_from_openweather(self, location: Dict[str, Any]) -> Optional[WeatherData]:
        """Fetch weather data from OpenWeatherMap API"""
        try:
            # In production, would use actual API key and make real requests
            # For now, simulate the response
            return await self._simulate_weather_data(location)
            
        except Exception as e:
            logger.error("Error fetching from OpenWeatherMap", error=str(e))
            return None
    
    async def _fetch_from_weatherapi(self, location: Dict[str, Any]) -> Optional[WeatherData]:
        """Fetch weather data from WeatherAPI"""
        try:
            # In production, would use actual API key and make real requests
            # For now, simulate the response
            return await self._simulate_weather_data(location)
            
        except Exception as e:
            logger.error("Error fetching from WeatherAPI", error=str(e))
            return None
    
    async def _simulate_weather_data(self, location: Dict[str, Any]) -> WeatherData:
        """Simulate weather data for testing purposes"""
        import random
        
        # Simulate realistic weather data based on location and season
        current_month = datetime.now().month
        
        # Base temperature ranges by season
        if current_month in [12, 1, 2]:  # Winter
            temp_range = (10, 25)
            rain_prob = 0.2
        elif current_month in [3, 4, 5]:  # Summer
            temp_range = (25, 45)
            rain_prob = 0.1
        elif current_month in [6, 7, 8, 9]:  # Monsoon
            temp_range = (20, 35)
            rain_prob = 0.7
        else:  # Post-monsoon
            temp_range = (15, 30)
            rain_prob = 0.3
        
        temperature = random.uniform(*temp_range)
        humidity = random.uniform(30, 90)
        rainfall = random.uniform(0, 100) if random.random() < rain_prob else 0
        wind_speed = random.uniform(5, 40)
        
        # Occasionally simulate extreme conditions for testing
        if random.random() < 0.1:  # 10% chance of extreme conditions
            if random.random() < 0.5:
                temperature = random.uniform(45, 50)  # Extreme heat
            else:
                rainfall = random.uniform(100, 200)  # Heavy rain
                wind_speed = random.uniform(60, 100)  # Strong winds
        
        weather_data = WeatherData(
            location=location['name'],
            timestamp=datetime.utcnow(),
            temperature=temperature,
            humidity=humidity,
            rainfall=rainfall,
            wind_speed=wind_speed,
            wind_direction=random.choice(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']),
            pressure=random.uniform(990, 1020),
            visibility=random.uniform(1, 10),
            weather_condition=self._determine_weather_condition(temperature, rainfall, wind_speed),
            alerts=[],
            forecast=None
        )
        
        return weather_data
    
    def _determine_weather_condition(self, temperature: float, rainfall: float, wind_speed: float) -> str:
        """Determine weather condition based on parameters"""
        if rainfall > 50:
            return "Heavy Rain"
        elif rainfall > 10:
            return "Light Rain"
        elif temperature > 40:
            return "Very Hot"
        elif temperature < 15:
            return "Cold"
        elif wind_speed > 50:
            return "Windy"
        else:
            return "Clear"
    
    async def _detect_weather_emergencies(self, weather_data: WeatherData) -> List[Dict[str, Any]]:
        """Detect weather emergency conditions"""
        emergencies = []
        
        try:
            # Check for heavy rain
            if weather_data.rainfall and weather_data.rainfall >= self.emergency_thresholds[WeatherEventType.HEAVY_RAIN]['warning']:
                intensity = self._determine_weather_intensity(
                    weather_data.rainfall,
                    self.emergency_thresholds[WeatherEventType.HEAVY_RAIN]
                )
                
                emergencies.append({
                    'type': WeatherEventType.HEAVY_RAIN,
                    'intensity': intensity,
                    'value': weather_data.rainfall,
                    'unit': 'mm',
                    'description': f"Heavy rainfall of {weather_data.rainfall:.1f}mm detected"
                })
            
            # Check for extreme heat
            if weather_data.temperature and weather_data.temperature >= self.emergency_thresholds[WeatherEventType.EXTREME_HEAT]['warning']:
                intensity = self._determine_weather_intensity(
                    weather_data.temperature,
                    self.emergency_thresholds[WeatherEventType.EXTREME_HEAT]
                )
                
                emergencies.append({
                    'type': WeatherEventType.EXTREME_HEAT,
                    'intensity': intensity,
                    'value': weather_data.temperature,
                    'unit': '°C',
                    'description': f"Extreme heat of {weather_data.temperature:.1f}°C detected"
                })
            
            # Check for wind storms
            if weather_data.wind_speed and weather_data.wind_speed >= self.emergency_thresholds[WeatherEventType.WIND_STORM]['warning']:
                intensity = self._determine_weather_intensity(
                    weather_data.wind_speed,
                    self.emergency_thresholds[WeatherEventType.WIND_STORM]
                )
                
                emergencies.append({
                    'type': WeatherEventType.WIND_STORM,
                    'intensity': intensity,
                    'value': weather_data.wind_speed,
                    'unit': 'km/h',
                    'description': f"Strong winds of {weather_data.wind_speed:.1f}km/h detected"
                })
            
            # Check for combined conditions (e.g., cyclone indicators)
            if (weather_data.wind_speed and weather_data.wind_speed > 60 and 
                weather_data.rainfall and weather_data.rainfall > 50):
                emergencies.append({
                    'type': WeatherEventType.CYCLONE,
                    'intensity': 'high',
                    'value': weather_data.wind_speed,
                    'unit': 'km/h',
                    'description': f"Cyclonic conditions detected: {weather_data.wind_speed:.1f}km/h winds with {weather_data.rainfall:.1f}mm rain"
                })
            
        except Exception as e:
            logger.error("Error detecting weather emergencies", error=str(e))
        
        return emergencies
    
    def _determine_weather_intensity(self, value: float, thresholds: Dict[str, float]) -> str:
        """Determine intensity level based on thresholds"""
        if value >= thresholds['critical']:
            return 'critical'
        elif value >= thresholds['emergency']:
            return 'emergency'
        elif value >= thresholds['warning']:
            return 'warning'
        else:
            return 'low'
    
    async def _create_weather_emergency_alert(
        self,
        user_id: str,
        location: str,
        weather_event: WeatherEventType,
        intensity: str,
        weather_data: WeatherData,
        event_data: Dict[str, Any]
    ) -> Optional[WeatherEmergencyAlert]:
        """Create a weather emergency alert"""
        try:
            # Determine severity based on intensity
            severity_map = {
                'low': AlertSeverity.LOW,
                'warning': AlertSeverity.MEDIUM,
                'emergency': AlertSeverity.HIGH,
                'critical': AlertSeverity.CRITICAL
            }
            severity = severity_map.get(intensity, AlertSeverity.MEDIUM)
            
            # Create title based on event type
            event_names = {
                WeatherEventType.HEAVY_RAIN: "Heavy Rainfall",
                WeatherEventType.EXTREME_HEAT: "Extreme Heat",
                WeatherEventType.WIND_STORM: "Wind Storm",
                WeatherEventType.CYCLONE: "Cyclonic Conditions",
                WeatherEventType.HAILSTORM: "Hailstorm",
                WeatherEventType.DROUGHT: "Drought Conditions",
                WeatherEventType.FLOOD: "Flood Warning",
                WeatherEventType.FROST: "Frost Alert"
            }
            
            event_name = event_names.get(weather_event, weather_event.value.replace('_', ' ').title())
            title = f"⚠️ Weather Emergency: {event_name} - {intensity.title()}"
            
            # Create detailed message
            message = f"""
🌦️ WEATHER EMERGENCY ALERT 🌦️

⚠️ Event: {event_name}
📍 Location: {location}
🔴 Intensity: {intensity.title()}
📊 Value: {event_data['value']:.1f} {event_data['unit']}

📈 CURRENT CONDITIONS:
🌡️ Temperature: {weather_data.temperature:.1f}°C
💧 Humidity: {weather_data.humidity:.1f}%
🌧️ Rainfall: {weather_data.rainfall:.1f}mm
💨 Wind Speed: {weather_data.wind_speed:.1f}km/h
🧭 Wind Direction: {weather_data.wind_direction}

⚠️ IMMEDIATE ACTIONS REQUIRED:
""".strip()
            
            # Add specific recommendations based on event type
            recommendations = self._get_weather_recommendations(weather_event, intensity, event_data)
            message += "\n" + "\n".join(f"• {rec}" for rec in recommendations)
            
            message += f"\n\n🕒 Alert issued at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            message += f"\n📱 Stay updated with MANDI EAR for latest conditions"
            
            alert = WeatherEmergencyAlert(
                user_id=user_id,
                alert_type=AlertType.WEATHER_EMERGENCY,
                severity=severity,
                title=title,
                message=message,
                location=location,
                weather_event=weather_event,
                intensity=intensity,
                start_time=datetime.utcnow(),
                end_time=None,  # Will be updated when conditions improve
                affected_areas=[location],
                impact_assessment=event_data.get('description', ''),
                recommended_actions=recommendations,
                weather_data={
                    'temperature': weather_data.temperature,
                    'humidity': weather_data.humidity,
                    'rainfall': weather_data.rainfall,
                    'wind_speed': weather_data.wind_speed,
                    'wind_direction': weather_data.wind_direction,
                    'pressure': weather_data.pressure
                }
            )
            
            return alert
            
        except Exception as e:
            logger.error("Error creating weather emergency alert", error=str(e))
            return None
    
    def _get_weather_recommendations(self, weather_event: WeatherEventType, intensity: str, event_data: Dict[str, Any]) -> List[str]:
        """Get specific recommendations based on weather event"""
        recommendations = []
        
        if weather_event == WeatherEventType.HEAVY_RAIN:
            recommendations.extend([
                "Ensure proper drainage in fields to prevent waterlogging",
                "Cover harvested crops and protect them from rain damage",
                "Avoid field operations until conditions improve",
                "Check for pest and disease outbreaks after rain stops"
            ])
            
            if intensity in ['emergency', 'critical']:
                recommendations.extend([
                    "URGENT: Move livestock to higher ground if flooding expected",
                    "Secure farm equipment and machinery",
                    "Prepare for potential power outages"
                ])
        
        elif weather_event == WeatherEventType.EXTREME_HEAT:
            recommendations.extend([
                "Increase irrigation frequency for crops",
                "Provide shade and extra water for livestock",
                "Avoid field work during peak heat hours (11 AM - 4 PM)",
                "Monitor crops for heat stress symptoms"
            ])
            
            if intensity in ['emergency', 'critical']:
                recommendations.extend([
                    "URGENT: Implement emergency cooling measures for livestock",
                    "Consider harvesting early if crops are mature",
                    "Ensure adequate water supply for irrigation"
                ])
        
        elif weather_event == WeatherEventType.WIND_STORM:
            recommendations.extend([
                "Secure loose farm equipment and structures",
                "Provide windbreaks for sensitive crops",
                "Check and reinforce greenhouse structures",
                "Monitor for crop lodging after storm passes"
            ])
            
            if intensity in ['emergency', 'critical']:
                recommendations.extend([
                    "URGENT: Move livestock to sheltered areas",
                    "Avoid outdoor activities until winds subside",
                    "Prepare for potential power line damage"
                ])
        
        elif weather_event == WeatherEventType.CYCLONE:
            recommendations.extend([
                "URGENT: Evacuate livestock to safe locations",
                "Secure all farm equipment and structures",
                "Harvest mature crops immediately if possible",
                "Stock up on emergency supplies",
                "Follow official evacuation orders if issued"
            ])
        
        # Add general safety recommendations
        recommendations.extend([
            "Stay informed through official weather updates",
            "Keep emergency contact numbers handy",
            "Document any crop damage for insurance claims"
        ])
        
        return recommendations
    
    # Public API methods
    
    async def force_weather_check(self, location: Optional[str] = None):
        """Force a weather check for specific location or all locations"""
        try:
            if location:
                # Find the location in monitored locations
                target_location = None
                for loc in self.monitored_locations:
                    if loc['name'].lower() == location.lower():
                        target_location = loc
                        break
                
                if target_location:
                    alerts = await self._check_location_weather(target_location)
                    for alert in alerts:
                        if self.notification_dispatcher:
                            await self.notification_dispatcher.send_notification(alert)
                    
                    logger.info("Forced weather check completed", location=location, alerts=len(alerts))
                else:
                    logger.warning("Location not monitored", location=location)
            else:
                await self.check_weather_emergencies()
                logger.info("Forced weather check completed for all locations")
                
        except Exception as e:
            logger.error("Error in forced weather check", location=location, error=str(e))
    
    async def add_location_monitoring(self, location_name: str, lat: float, lon: float):
        """Add a new location to monitoring list"""
        new_location = {'name': location_name, 'lat': lat, 'lon': lon}
        
        # Check if location already exists
        for loc in self.monitored_locations:
            if loc['name'].lower() == location_name.lower():
                logger.warning("Location already monitored", location=location_name)
                return
        
        self.monitored_locations.append(new_location)
        logger.info("Added location to monitoring", location=location_name)
    
    async def remove_location_monitoring(self, location_name: str):
        """Remove a location from monitoring list"""
        for i, loc in enumerate(self.monitored_locations):
            if loc['name'].lower() == location_name.lower():
                del self.monitored_locations[i]
                logger.info("Removed location from monitoring", location=location_name)
                return
        
        logger.warning("Location not found in monitoring list", location=location_name)
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            'is_monitoring': self.is_monitoring,
            'last_check_time': self.last_check_time,
            'alerts_sent_today': self.alerts_sent_today,
            'monitored_locations': len(self.monitored_locations),
            'active_apis': sum(1 for api in self.weather_apis.values() if api['enabled']),
            'emergency_thresholds': self.emergency_thresholds
        }