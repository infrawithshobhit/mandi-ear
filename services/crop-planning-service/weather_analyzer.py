"""
Weather Analysis Module for Crop Planning

Integrates with weather APIs to provide comprehensive weather analysis
for crop planning decisions including rainfall patterns, temperature trends,
and climate risk assessment.
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import statistics

from models import (
    WeatherAnalysis, WeatherPattern, GeoLocation, RiskLevel
)

logger = logging.getLogger(__name__)

class WeatherAnalyzer:
    """
    Comprehensive weather analysis for crop planning
    
    Integrates multiple weather data sources to provide:
    - Historical weather patterns
    - Seasonal forecasts
    - Risk assessments (drought, flood)
    - Optimal planting windows
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_urls = {
            'openweather': 'https://api.openweathermap.org/data/2.5',
            'weatherapi': 'https://api.weatherapi.com/v1',
            # Fallback to mock data if no API key
            'mock': None
        }
        
    async def analyze_patterns(
        self, 
        latitude: float, 
        longitude: float, 
        timeframe: timedelta
    ) -> WeatherAnalysis:
        """
        Analyze weather patterns for crop planning
        
        Args:
            latitude: Farm latitude
            longitude: Farm longitude
            timeframe: Analysis timeframe
            
        Returns:
            Comprehensive weather analysis
        """
        try:
            location = GeoLocation(latitude=latitude, longitude=longitude)
            
            # Get historical and forecast data
            if self.api_key:
                patterns = await self._fetch_weather_data(latitude, longitude, timeframe)
            else:
                # Use mock data for development/testing
                patterns = self._generate_mock_weather_data(latitude, longitude, timeframe)
            
            # Analyze patterns
            analysis = self._analyze_weather_patterns(location, patterns, timeframe)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Weather analysis failed: {str(e)}")
            # Return mock analysis as fallback
            return self._generate_fallback_analysis(latitude, longitude, timeframe)
    
    async def _fetch_weather_data(
        self, 
        latitude: float, 
        longitude: float, 
        timeframe: timedelta
    ) -> List[WeatherPattern]:
        """Fetch real weather data from APIs"""
        patterns = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Fetch current and forecast data
                current_url = f"{self.base_urls['openweather']}/weather"
                forecast_url = f"{self.base_urls['openweather']}/forecast"
                
                params = {
                    'lat': latitude,
                    'lon': longitude,
                    'appid': self.api_key,
                    'units': 'metric'
                }
                
                # Get current weather
                async with session.get(current_url, params=params) as response:
                    if response.status == 200:
                        current_data = await response.json()
                        patterns.append(self._parse_current_weather(current_data))
                
                # Get forecast data
                async with session.get(forecast_url, params=params) as response:
                    if response.status == 200:
                        forecast_data = await response.json()
                        patterns.extend(self._parse_forecast_data(forecast_data))
                        
        except Exception as e:
            logger.warning(f"API fetch failed, using mock data: {str(e)}")
            patterns = self._generate_mock_weather_data(latitude, longitude, timeframe)
        
        return patterns
    
    def _parse_current_weather(self, data: Dict[str, Any]) -> WeatherPattern:
        """Parse current weather data from API response"""
        main = data.get('main', {})
        wind = data.get('wind', {})
        
        return WeatherPattern(
            temperature_avg=main.get('temp', 25.0),
            temperature_min=main.get('temp_min', 20.0),
            temperature_max=main.get('temp_max', 30.0),
            rainfall_mm=data.get('rain', {}).get('1h', 0.0),
            humidity_percent=main.get('humidity', 60.0),
            wind_speed_kmh=wind.get('speed', 10.0) * 3.6,  # Convert m/s to km/h
            month=datetime.now().month
        )
    
    def _parse_forecast_data(self, data: Dict[str, Any]) -> List[WeatherPattern]:
        """Parse forecast data from API response"""
        patterns = []
        
        for item in data.get('list', [])[:30]:  # Limit to 30 forecast points
            main = item.get('main', {})
            wind = item.get('wind', {})
            dt = datetime.fromtimestamp(item.get('dt', 0))
            
            pattern = WeatherPattern(
                temperature_avg=main.get('temp', 25.0),
                temperature_min=main.get('temp_min', 20.0),
                temperature_max=main.get('temp_max', 30.0),
                rainfall_mm=item.get('rain', {}).get('3h', 0.0),
                humidity_percent=main.get('humidity', 60.0),
                wind_speed_kmh=wind.get('speed', 10.0) * 3.6,
                month=dt.month
            )
            patterns.append(pattern)
        
        return patterns
    
    def _generate_mock_weather_data(
        self, 
        latitude: float, 
        longitude: float, 
        timeframe: timedelta
    ) -> List[WeatherPattern]:
        """Generate realistic mock weather data for development"""
        patterns = []
        current_date = datetime.now()
        
        # Generate patterns for each month in timeframe
        months_to_generate = min(12, int(timeframe.days / 30))
        
        for i in range(months_to_generate):
            month = ((current_date.month - 1 + i) % 12) + 1
            
            # Simulate Indian weather patterns based on latitude
            if latitude > 28:  # Northern India
                temp_base = 25 if month in [6, 7, 8, 9] else 20
                rainfall = 150 if month in [6, 7, 8, 9] else 20
            elif latitude > 20:  # Central India
                temp_base = 28 if month in [4, 5, 6] else 25
                rainfall = 200 if month in [6, 7, 8, 9] else 15
            else:  # Southern India
                temp_base = 30 if month in [3, 4, 5] else 27
                rainfall = 180 if month in [6, 7, 8, 9, 10, 11] else 25
            
            pattern = WeatherPattern(
                temperature_avg=temp_base,
                temperature_min=temp_base - 5,
                temperature_max=temp_base + 8,
                rainfall_mm=rainfall,
                humidity_percent=70 if month in [6, 7, 8, 9] else 55,
                wind_speed_kmh=12.0,
                month=month
            )
            patterns.append(pattern)
        
        return patterns
    
    def _analyze_weather_patterns(
        self, 
        location: GeoLocation, 
        patterns: List[WeatherPattern],
        timeframe: timedelta
    ) -> WeatherAnalysis:
        """Analyze weather patterns and generate insights"""
        
        if not patterns:
            return self._generate_fallback_analysis(
                location.latitude, location.longitude, timeframe
            )
        
        # Calculate aggregated metrics
        total_rainfall = sum(p.rainfall_mm for p in patterns)
        avg_temp = statistics.mean(p.temperature_avg for p in patterns)
        min_temp = min(p.temperature_min for p in patterns)
        max_temp = max(p.temperature_max for p in patterns)
        
        # Assess risks
        drought_risk = self._assess_drought_risk(patterns)
        flood_risk = self._assess_flood_risk(patterns)
        
        # Determine optimal planting windows
        planting_windows = self._determine_planting_windows(patterns)
        
        # Calculate suitability score
        suitability_score = self._calculate_weather_suitability(patterns)
        
        return WeatherAnalysis(
            location=location,
            analysis_period=f"{timeframe.days} days",
            patterns=patterns,
            rainfall_total=total_rainfall,
            temperature_range={
                "average": avg_temp,
                "minimum": min_temp,
                "maximum": max_temp
            },
            drought_risk=drought_risk,
            flood_risk=flood_risk,
            optimal_planting_windows=planting_windows,
            weather_suitability_score=suitability_score
        )
    
    def _assess_drought_risk(self, patterns: List[WeatherPattern]) -> RiskLevel:
        """Assess drought risk based on rainfall patterns"""
        total_rainfall = sum(p.rainfall_mm for p in patterns)
        avg_monthly_rainfall = total_rainfall / len(patterns) if patterns else 0
        
        if avg_monthly_rainfall < 50:
            return RiskLevel.HIGH
        elif avg_monthly_rainfall < 100:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _assess_flood_risk(self, patterns: List[WeatherPattern]) -> RiskLevel:
        """Assess flood risk based on rainfall intensity"""
        if not patterns:
            return RiskLevel.LOW
            
        max_monthly_rainfall = max(p.rainfall_mm for p in patterns)
        
        if max_monthly_rainfall > 300:
            return RiskLevel.HIGH
        elif max_monthly_rainfall > 200:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _determine_planting_windows(self, patterns: List[WeatherPattern]) -> List[Dict[str, Any]]:
        """Determine optimal planting windows based on weather patterns"""
        windows = []
        
        for pattern in patterns:
            # Kharif season (monsoon crops) - June to September
            if pattern.month in [6, 7, 8, 9] and pattern.rainfall_mm > 100:
                windows.append({
                    "season": "kharif",
                    "month": pattern.month,
                    "suitability": "high" if pattern.rainfall_mm > 150 else "medium",
                    "recommended_crops": ["rice", "cotton", "sugarcane", "maize"]
                })
            
            # Rabi season (winter crops) - October to March
            elif pattern.month in [10, 11, 12, 1, 2, 3] and pattern.temperature_avg < 30:
                windows.append({
                    "season": "rabi",
                    "month": pattern.month,
                    "suitability": "high" if pattern.temperature_avg < 25 else "medium",
                    "recommended_crops": ["wheat", "barley", "peas", "mustard"]
                })
            
            # Zaid season (summer crops) - April to June
            elif pattern.month in [4, 5, 6] and pattern.temperature_avg < 35:
                windows.append({
                    "season": "zaid",
                    "month": pattern.month,
                    "suitability": "medium",
                    "recommended_crops": ["watermelon", "cucumber", "fodder"]
                })
        
        return windows
    
    def _calculate_weather_suitability(self, patterns: List[WeatherPattern]) -> float:
        """Calculate overall weather suitability score for agriculture"""
        if not patterns:
            return 0.5
        
        # Factors for suitability calculation
        rainfall_score = 0.0
        temperature_score = 0.0
        consistency_score = 0.0
        
        total_rainfall = sum(p.rainfall_mm for p in patterns)
        avg_rainfall = total_rainfall / len(patterns)
        avg_temp = statistics.mean(p.temperature_avg for p in patterns)
        
        # Rainfall suitability (optimal range: 100-200mm per month)
        if 100 <= avg_rainfall <= 200:
            rainfall_score = 1.0
        elif 50 <= avg_rainfall < 100 or 200 < avg_rainfall <= 300:
            rainfall_score = 0.7
        else:
            rainfall_score = 0.3
        
        # Temperature suitability (optimal range: 20-30°C)
        if 20 <= avg_temp <= 30:
            temperature_score = 1.0
        elif 15 <= avg_temp < 20 or 30 < avg_temp <= 35:
            temperature_score = 0.7
        else:
            temperature_score = 0.3
        
        # Weather consistency (lower variation is better)
        temp_variation = statistics.stdev(p.temperature_avg for p in patterns) if len(patterns) > 1 else 0
        if temp_variation < 5:
            consistency_score = 1.0
        elif temp_variation < 10:
            consistency_score = 0.7
        else:
            consistency_score = 0.4
        
        # Weighted average
        return (rainfall_score * 0.4 + temperature_score * 0.4 + consistency_score * 0.2)
    
    def _generate_fallback_analysis(
        self, 
        latitude: float, 
        longitude: float, 
        timeframe: timedelta
    ) -> WeatherAnalysis:
        """Generate fallback analysis when data is unavailable"""
        location = GeoLocation(latitude=latitude, longitude=longitude)
        
        # Generate basic mock patterns
        patterns = self._generate_mock_weather_data(latitude, longitude, timeframe)
        
        return WeatherAnalysis(
            location=location,
            analysis_period=f"{timeframe.days} days (fallback data)",
            patterns=patterns,
            rainfall_total=sum(p.rainfall_mm for p in patterns),
            temperature_range={
                "average": 25.0,
                "minimum": 18.0,
                "maximum": 35.0
            },
            drought_risk=RiskLevel.MEDIUM,
            flood_risk=RiskLevel.LOW,
            optimal_planting_windows=[
                {
                    "season": "kharif",
                    "month": 7,
                    "suitability": "medium",
                    "recommended_crops": ["rice", "cotton"]
                }
            ],
            weather_suitability_score=0.6
        )