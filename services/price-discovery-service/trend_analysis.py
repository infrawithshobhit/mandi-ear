"""
Price Trend Analysis and Prediction System
Implements historical trend analysis, price prediction algorithms, and market volatility indicators
"""

import asyncio
import structlog
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import math
import statistics
from dataclasses import dataclass
from enum import Enum
import numpy as np

from models import PricePoint, PriceData, MandiInfo
from database import get_commodity_prices

logger = structlog.get_logger()

class TrendDirection(str, Enum):
    """Price trend directions"""
    BULLISH = "bullish"      # Strong upward trend
    BEARISH = "bearish"      # Strong downward trend
    SIDEWAYS = "sideways"    # No clear trend
    VOLATILE = "volatile"    # High volatility, no clear direction

class VolatilityLevel(str, Enum):
    """Market volatility levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

class SeasonalPattern(str, Enum):
    """Seasonal price patterns"""
    HARVEST_SEASON = "harvest_season"
    POST_HARVEST = "post_harvest"
    PRE_HARVEST = "pre_harvest"
    FESTIVAL_DEMAND = "festival_demand"
    MONSOON_IMPACT = "monsoon_impact"

@dataclass
class TrendAnalysis:
    """Trend analysis result"""
    commodity: str
    region: Optional[str]
    analysis_period_days: int
    trend_direction: TrendDirection
    trend_strength: float  # 0.0 to 1.0
    price_change_percent: float
    volatility_level: VolatilityLevel
    volatility_score: float
    current_price: float
    average_price: float
    min_price: float
    max_price: float
    support_level: float  # Technical analysis support
    resistance_level: float  # Technical analysis resistance
    confidence_score: float  # 0.0 to 1.0
    key_factors: List[str]
    analysis_timestamp: datetime

@dataclass
class PricePrediction:
    """Price prediction result"""
    commodity: str
    region: Optional[str]
    prediction_horizon_days: int
    predicted_price: float
    price_range: Dict[str, float]  # min, max, confidence_interval
    confidence_score: float
    trend_continuation_probability: float
    key_drivers: List[str]
    risk_factors: List[str]
    prediction_timestamp: datetime

@dataclass
class MarketVolatilityIndicator:
    """Market volatility indicator"""
    commodity: str
    region: Optional[str]
    volatility_score: float  # 0.0 to 1.0
    volatility_level: VolatilityLevel
    price_variance: float
    coefficient_of_variation: float
    max_daily_change_percent: float
    volatility_trend: str  # "increasing", "decreasing", "stable"
    measurement_period_days: int

class TechnicalAnalyzer:
    """Technical analysis tools for price data"""
    
    @staticmethod
    def calculate_moving_average(prices: List[float], window: int) -> List[float]:
        """Calculate simple moving average"""
        if len(prices) < window:
            return []
        
        moving_averages = []
        for i in range(window - 1, len(prices)):
            avg = sum(prices[i - window + 1:i + 1]) / window
            moving_averages.append(avg)
        
        return moving_averages
    
    @staticmethod
    def calculate_exponential_moving_average(prices: List[float], window: int) -> List[float]:
        """Calculate exponential moving average"""
        if len(prices) < window:
            return []
        
        alpha = 2 / (window + 1)
        ema = [prices[0]]
        
        for i in range(1, len(prices)):
            ema_value = alpha * prices[i] + (1 - alpha) * ema[-1]
            ema.append(ema_value)
        
        return ema
    
    @staticmethod
    def calculate_rsi(prices: List[float], window: int = 14) -> List[float]:
        """Calculate Relative Strength Index"""
        if len(prices) < window + 1:
            return []
        
        price_changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        gains = [max(0, change) for change in price_changes]
        losses = [abs(min(0, change)) for change in price_changes]
        
        rsi_values = []
        
        # Calculate initial average gain and loss
        avg_gain = sum(gains[:window]) / window
        avg_loss = sum(losses[:window]) / window
        
        for i in range(window, len(gains)):
            avg_gain = (avg_gain * (window - 1) + gains[i]) / window
            avg_loss = (avg_loss * (window - 1) + losses[i]) / window
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
        
        return rsi_values
    
    @staticmethod
    def find_support_resistance(prices: List[float], window: int = 20) -> Tuple[float, float]:
        """Find support and resistance levels"""
        if len(prices) < window:
            return min(prices), max(prices)
        
        # Find local minima and maxima
        local_mins = []
        local_maxs = []
        
        for i in range(window, len(prices) - window):
            if prices[i] == min(prices[i-window:i+window+1]):
                local_mins.append(prices[i])
            if prices[i] == max(prices[i-window:i+window+1]):
                local_maxs.append(prices[i])
        
        # Support is around the average of recent local minima
        support = statistics.median(local_mins[-5:]) if local_mins else min(prices)
        
        # Resistance is around the average of recent local maxima
        resistance = statistics.median(local_maxs[-5:]) if local_maxs else max(prices)
        
        return support, resistance
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], window: int = 20, num_std: float = 2) -> Dict[str, List[float]]:
        """Calculate Bollinger Bands"""
        if len(prices) < window:
            return {"upper": [], "middle": [], "lower": []}
        
        moving_avg = TechnicalAnalyzer.calculate_moving_average(prices, window)
        
        upper_band = []
        lower_band = []
        
        for i in range(window - 1, len(prices)):
            price_slice = prices[i - window + 1:i + 1]
            std_dev = statistics.stdev(price_slice)
            ma = moving_avg[i - window + 1]
            
            upper_band.append(ma + num_std * std_dev)
            lower_band.append(ma - num_std * std_dev)
        
        return {
            "upper": upper_band,
            "middle": moving_avg,
            "lower": lower_band
        }

class SeasonalAnalyzer:
    """Analyzes seasonal patterns in agricultural prices"""
    
    def __init__(self):
        # Indian agricultural seasons
        self.seasons = {
            "kharif": {"start_month": 6, "end_month": 10},    # June-October
            "rabi": {"start_month": 11, "end_month": 4},      # November-April
            "zaid": {"start_month": 3, "end_month": 6}        # March-June
        }
        
        # Festival periods affecting demand
        self.festival_periods = [
            {"name": "Diwali", "month": 10, "duration_days": 15},
            {"name": "Dussehra", "month": 9, "duration_days": 10},
            {"name": "Holi", "month": 3, "duration_days": 7},
            {"name": "Eid", "month": 5, "duration_days": 5}  # Approximate
        ]
    
    def identify_seasonal_pattern(self, timestamp: datetime, commodity: str) -> SeasonalPattern:
        """Identify current seasonal pattern"""
        month = timestamp.month
        
        # Check for festival periods
        for festival in self.festival_periods:
            if abs(month - festival["month"]) <= 1:  # Within 1 month of festival
                return SeasonalPattern.FESTIVAL_DEMAND
        
        # Check for monsoon impact (June-September)
        if 6 <= month <= 9:
            return SeasonalPattern.MONSOON_IMPACT
        
        # Check agricultural seasons
        if 6 <= month <= 10:  # Kharif harvest
            return SeasonalPattern.HARVEST_SEASON
        elif 11 <= month <= 12 or 1 <= month <= 2:  # Post-harvest
            return SeasonalPattern.POST_HARVEST
        else:  # Pre-harvest
            return SeasonalPattern.PRE_HARVEST
    
    def get_seasonal_price_multiplier(self, pattern: SeasonalPattern, commodity: str) -> float:
        """Get expected price multiplier for seasonal pattern"""
        multipliers = {
            SeasonalPattern.HARVEST_SEASON: 0.85,    # Lower prices during harvest
            SeasonalPattern.POST_HARVEST: 0.90,      # Slightly higher post-harvest
            SeasonalPattern.PRE_HARVEST: 1.15,       # Higher prices before harvest
            SeasonalPattern.FESTIVAL_DEMAND: 1.20,   # Higher demand during festivals
            SeasonalPattern.MONSOON_IMPACT: 1.10     # Weather uncertainty
        }
        
        return multipliers.get(pattern, 1.0)

class PriceTrendAnalyzer:
    """Main class for price trend analysis and prediction"""
    
    def __init__(self):
        self.technical_analyzer = TechnicalAnalyzer()
        self.seasonal_analyzer = SeasonalAnalyzer()
    
    async def analyze_price_trends(
        self,
        commodity: str,
        region: Optional[str] = None,
        analysis_period_days: int = 30
    ) -> TrendAnalysis:
        """
        Comprehensive price trend analysis
        
        Args:
            commodity: Commodity to analyze
            region: Specific region (optional)
            analysis_period_days: Number of days to analyze
            
        Returns:
            Detailed trend analysis
        """
        try:
            # Get historical price data
            price_data_list = await get_commodity_prices(commodity, state=region, limit=1000)
            
            if not price_data_list:
                raise ValueError("No price data available for analysis")
            
            # Extract price points and sort by timestamp
            all_price_points = []
            for price_data in price_data_list:
                all_price_points.extend(price_data.price_points)
            
            # Filter by analysis period
            cutoff_date = datetime.utcnow() - timedelta(days=analysis_period_days)
            recent_points = [p for p in all_price_points if p.timestamp >= cutoff_date]
            
            if len(recent_points) < 5:
                raise ValueError("Insufficient data points for trend analysis")
            
            # Sort by timestamp
            recent_points.sort(key=lambda x: x.timestamp)
            prices = [p.price for p in recent_points]
            
            # Basic statistics
            current_price = prices[-1]
            average_price = statistics.mean(prices)
            min_price = min(prices)
            max_price = max(prices)
            
            # Calculate trend direction and strength
            trend_direction, trend_strength = self._calculate_trend(prices)
            
            # Calculate volatility
            volatility_level, volatility_score = self._calculate_volatility(prices)
            
            # Technical analysis
            support_level, resistance_level = self.technical_analyzer.find_support_resistance(prices)
            
            # Price change percentage
            if len(prices) > 1:
                price_change_percent = ((current_price - prices[0]) / prices[0]) * 100
            else:
                price_change_percent = 0.0
            
            # Identify key factors
            key_factors = self._identify_key_factors(
                commodity, recent_points, trend_direction, volatility_level
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                len(recent_points), analysis_period_days, volatility_score
            )
            
            return TrendAnalysis(
                commodity=commodity,
                region=region,
                analysis_period_days=analysis_period_days,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                price_change_percent=price_change_percent,
                volatility_level=volatility_level,
                volatility_score=volatility_score,
                current_price=current_price,
                average_price=average_price,
                min_price=min_price,
                max_price=max_price,
                support_level=support_level,
                resistance_level=resistance_level,
                confidence_score=confidence_score,
                key_factors=key_factors,
                analysis_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error("Failed to analyze price trends", error=str(e))
            raise
    
    async def predict_price(
        self,
        commodity: str,
        region: Optional[str] = None,
        prediction_horizon_days: int = 7,
        historical_days: int = 60
    ) -> PricePrediction:
        """
        Predict future price based on historical trends and patterns
        
        Args:
            commodity: Commodity to predict
            region: Specific region (optional)
            prediction_horizon_days: Days ahead to predict
            historical_days: Historical data to use for prediction
            
        Returns:
            Price prediction with confidence intervals
        """
        try:
            # Get trend analysis
            trend_analysis = await self.analyze_price_trends(
                commodity, region, historical_days
            )
            
            # Get historical price data
            price_data_list = await get_commodity_prices(commodity, state=region, limit=1000)
            
            # Extract and prepare price data
            all_price_points = []
            for price_data in price_data_list:
                all_price_points.extend(price_data.price_points)
            
            cutoff_date = datetime.utcnow() - timedelta(days=historical_days)
            recent_points = [p for p in all_price_points if p.timestamp >= cutoff_date]
            recent_points.sort(key=lambda x: x.timestamp)
            prices = [p.price for p in recent_points]
            
            if len(prices) < 10:
                raise ValueError("Insufficient data for price prediction")
            
            # Apply prediction algorithms
            predicted_price = self._predict_using_trend_analysis(
                prices, trend_analysis, prediction_horizon_days
            )
            
            # Calculate prediction confidence
            confidence_score = self._calculate_prediction_confidence(
                trend_analysis, len(prices), prediction_horizon_days
            )
            
            # Calculate price range with confidence intervals
            price_variance = statistics.variance(prices[-30:])  # Last 30 data points
            std_dev = math.sqrt(price_variance)
            
            # Confidence interval (assuming normal distribution)
            confidence_interval = 1.96 * std_dev  # 95% confidence
            
            price_range = {
                "min": max(0, predicted_price - confidence_interval),
                "max": predicted_price + confidence_interval,
                "confidence_interval": confidence_interval
            }
            
            # Identify key drivers and risk factors
            key_drivers = self._identify_price_drivers(commodity, trend_analysis)
            risk_factors = self._identify_risk_factors(commodity, trend_analysis)
            
            # Calculate trend continuation probability
            trend_continuation_prob = self._calculate_trend_continuation_probability(
                trend_analysis, prediction_horizon_days
            )
            
            return PricePrediction(
                commodity=commodity,
                region=region,
                prediction_horizon_days=prediction_horizon_days,
                predicted_price=predicted_price,
                price_range=price_range,
                confidence_score=confidence_score,
                trend_continuation_probability=trend_continuation_prob,
                key_drivers=key_drivers,
                risk_factors=risk_factors,
                prediction_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error("Failed to predict price", error=str(e))
            raise
    
    async def calculate_volatility_indicators(
        self,
        commodity: str,
        region: Optional[str] = None,
        measurement_period_days: int = 30
    ) -> MarketVolatilityIndicator:
        """
        Calculate comprehensive volatility indicators
        
        Args:
            commodity: Commodity to analyze
            region: Specific region (optional)
            measurement_period_days: Period for volatility measurement
            
        Returns:
            Volatility indicators and metrics
        """
        try:
            # Get price data
            price_data_list = await get_commodity_prices(commodity, state=region, limit=500)
            
            # Extract price points
            all_price_points = []
            for price_data in price_data_list:
                all_price_points.extend(price_data.price_points)
            
            # Filter by measurement period
            cutoff_date = datetime.utcnow() - timedelta(days=measurement_period_days)
            recent_points = [p for p in all_price_points if p.timestamp >= cutoff_date]
            recent_points.sort(key=lambda x: x.timestamp)
            
            if len(recent_points) < 5:
                raise ValueError("Insufficient data for volatility analysis")
            
            prices = [p.price for p in recent_points]
            
            # Calculate daily price changes
            daily_changes = []
            for i in range(1, len(prices)):
                change_percent = ((prices[i] - prices[i-1]) / prices[i-1]) * 100
                daily_changes.append(abs(change_percent))
            
            # Volatility metrics
            price_variance = statistics.variance(prices)
            mean_price = statistics.mean(prices)
            coefficient_of_variation = (math.sqrt(price_variance) / mean_price) * 100
            max_daily_change = max(daily_changes) if daily_changes else 0
            
            # Volatility score (0-1 scale)
            volatility_score = min(1.0, coefficient_of_variation / 50)  # Normalize to 50% CV
            
            # Volatility level classification
            if volatility_score < 0.2:
                volatility_level = VolatilityLevel.LOW
            elif volatility_score < 0.5:
                volatility_level = VolatilityLevel.MEDIUM
            elif volatility_score < 0.8:
                volatility_level = VolatilityLevel.HIGH
            else:
                volatility_level = VolatilityLevel.EXTREME
            
            # Volatility trend (compare recent vs earlier period)
            if len(prices) >= 20:
                recent_volatility = statistics.stdev(prices[-10:])
                earlier_volatility = statistics.stdev(prices[-20:-10])
                
                if recent_volatility > earlier_volatility * 1.1:
                    volatility_trend = "increasing"
                elif recent_volatility < earlier_volatility * 0.9:
                    volatility_trend = "decreasing"
                else:
                    volatility_trend = "stable"
            else:
                volatility_trend = "stable"
            
            return MarketVolatilityIndicator(
                commodity=commodity,
                region=region,
                volatility_score=volatility_score,
                volatility_level=volatility_level,
                price_variance=price_variance,
                coefficient_of_variation=coefficient_of_variation,
                max_daily_change_percent=max_daily_change,
                volatility_trend=volatility_trend,
                measurement_period_days=measurement_period_days
            )
            
        except Exception as e:
            logger.error("Failed to calculate volatility indicators", error=str(e))
            raise
    
    def _calculate_trend(self, prices: List[float]) -> Tuple[TrendDirection, float]:
        """Calculate trend direction and strength"""
        if len(prices) < 2:
            return TrendDirection.SIDEWAYS, 0.0
        
        # Linear regression to find trend
        n = len(prices)
        x_values = list(range(n))
        
        # Calculate slope
        x_mean = sum(x_values) / n
        y_mean = sum(prices) / n
        
        numerator = sum((x_values[i] - x_mean) * (prices[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return TrendDirection.SIDEWAYS, 0.0
        
        slope = numerator / denominator
        
        # Calculate R-squared for trend strength
        y_pred = [y_mean + slope * (x - x_mean) for x in x_values]
        ss_res = sum((prices[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((prices[i] - y_mean) ** 2 for i in range(n))
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        trend_strength = max(0, min(1, r_squared))
        
        # Determine trend direction
        price_change_percent = ((prices[-1] - prices[0]) / prices[0]) * 100
        
        if abs(price_change_percent) < 2:  # Less than 2% change
            return TrendDirection.SIDEWAYS, trend_strength
        elif slope > 0 and price_change_percent > 5:
            return TrendDirection.BULLISH, trend_strength
        elif slope < 0 and price_change_percent < -5:
            return TrendDirection.BEARISH, trend_strength
        else:
            # Check for high volatility
            volatility = statistics.stdev(prices) / statistics.mean(prices)
            if volatility > 0.15:  # High volatility
                return TrendDirection.VOLATILE, trend_strength
            else:
                return TrendDirection.SIDEWAYS, trend_strength
    
    def _calculate_volatility(self, prices: List[float]) -> Tuple[VolatilityLevel, float]:
        """Calculate volatility level and score"""
        if len(prices) < 2:
            return VolatilityLevel.LOW, 0.0
        
        # Calculate coefficient of variation
        mean_price = statistics.mean(prices)
        std_dev = statistics.stdev(prices)
        cv = (std_dev / mean_price) * 100 if mean_price > 0 else 0
        
        # Normalize to 0-1 scale
        volatility_score = min(1.0, cv / 30)  # 30% CV = max score
        
        # Classify volatility level
        if cv < 5:
            volatility_level = VolatilityLevel.LOW
        elif cv < 15:
            volatility_level = VolatilityLevel.MEDIUM
        elif cv < 25:
            volatility_level = VolatilityLevel.HIGH
        else:
            volatility_level = VolatilityLevel.EXTREME
        
        return volatility_level, volatility_score
    
    def _identify_key_factors(
        self,
        commodity: str,
        price_points: List[PricePoint],
        trend_direction: TrendDirection,
        volatility_level: VolatilityLevel
    ) -> List[str]:
        """Identify key factors affecting price trends"""
        factors = []
        
        # Seasonal factors
        current_season = self.seasonal_analyzer.identify_seasonal_pattern(
            datetime.utcnow(), commodity
        )
        factors.append(f"Seasonal pattern: {current_season.value}")
        
        # Trend factors
        if trend_direction == TrendDirection.BULLISH:
            factors.append("Strong upward price momentum")
        elif trend_direction == TrendDirection.BEARISH:
            factors.append("Downward price pressure")
        elif trend_direction == TrendDirection.VOLATILE:
            factors.append("High market uncertainty and volatility")
        
        # Volatility factors
        if volatility_level == VolatilityLevel.HIGH:
            factors.append("High price volatility indicating market instability")
        elif volatility_level == VolatilityLevel.EXTREME:
            factors.append("Extreme volatility suggesting major market disruption")
        
        # Data quality factors
        if len(price_points) < 20:
            factors.append("Limited data availability affecting analysis reliability")
        
        return factors
    
    def _calculate_confidence_score(
        self,
        data_points: int,
        analysis_period: int,
        volatility_score: float
    ) -> float:
        """Calculate confidence score for analysis"""
        # Base confidence from data availability
        data_confidence = min(1.0, data_points / 50)  # 50 points = full confidence
        
        # Period confidence (longer periods = higher confidence)
        period_confidence = min(1.0, analysis_period / 30)  # 30 days = full confidence
        
        # Volatility penalty (higher volatility = lower confidence)
        volatility_penalty = 1.0 - (volatility_score * 0.3)  # Max 30% penalty
        
        # Combined confidence
        confidence = (data_confidence * 0.4 + period_confidence * 0.3 + volatility_penalty * 0.3)
        
        return max(0.1, min(1.0, confidence))
    
    def _predict_using_trend_analysis(
        self,
        prices: List[float],
        trend_analysis: TrendAnalysis,
        prediction_days: int
    ) -> float:
        """Predict price using trend analysis"""
        current_price = prices[-1]
        
        # Base prediction on trend direction and strength
        if trend_analysis.trend_direction == TrendDirection.BULLISH:
            # Extrapolate upward trend
            daily_change_rate = (trend_analysis.price_change_percent / trend_analysis.analysis_period_days) / 100
            predicted_change = daily_change_rate * prediction_days * trend_analysis.trend_strength
            predicted_price = current_price * (1 + predicted_change)
            
        elif trend_analysis.trend_direction == TrendDirection.BEARISH:
            # Extrapolate downward trend
            daily_change_rate = (trend_analysis.price_change_percent / trend_analysis.analysis_period_days) / 100
            predicted_change = daily_change_rate * prediction_days * trend_analysis.trend_strength
            predicted_price = current_price * (1 + predicted_change)
            
        else:
            # Sideways or volatile - predict mean reversion
            predicted_price = trend_analysis.average_price
        
        # Apply seasonal adjustment
        seasonal_pattern = self.seasonal_analyzer.identify_seasonal_pattern(
            datetime.utcnow() + timedelta(days=prediction_days),
            trend_analysis.commodity
        )
        seasonal_multiplier = self.seasonal_analyzer.get_seasonal_price_multiplier(
            seasonal_pattern, trend_analysis.commodity
        )
        
        predicted_price *= seasonal_multiplier
        
        # Ensure prediction is within reasonable bounds
        min_bound = trend_analysis.min_price * 0.8
        max_bound = trend_analysis.max_price * 1.2
        
        predicted_price = max(min_bound, min(max_bound, predicted_price))
        
        return predicted_price
    
    def _calculate_prediction_confidence(
        self,
        trend_analysis: TrendAnalysis,
        data_points: int,
        prediction_days: int
    ) -> float:
        """Calculate confidence for price prediction"""
        # Base confidence from trend analysis
        base_confidence = trend_analysis.confidence_score
        
        # Prediction horizon penalty (longer predictions = lower confidence)
        horizon_penalty = max(0.3, 1.0 - (prediction_days / 30))  # 30 days = 30% confidence
        
        # Trend strength bonus
        trend_bonus = trend_analysis.trend_strength * 0.2
        
        # Volatility penalty
        volatility_penalty = trend_analysis.volatility_score * 0.3
        
        confidence = base_confidence * horizon_penalty + trend_bonus - volatility_penalty
        
        return max(0.1, min(0.9, confidence))
    
    def _identify_price_drivers(self, commodity: str, trend_analysis: TrendAnalysis) -> List[str]:
        """Identify key drivers for price prediction"""
        drivers = []
        
        if trend_analysis.trend_direction == TrendDirection.BULLISH:
            drivers.extend([
                "Strong demand fundamentals",
                "Supply constraints",
                "Positive market sentiment"
            ])
        elif trend_analysis.trend_direction == TrendDirection.BEARISH:
            drivers.extend([
                "Oversupply conditions",
                "Weak demand",
                "Market correction"
            ])
        
        # Seasonal drivers
        seasonal_pattern = self.seasonal_analyzer.identify_seasonal_pattern(
            datetime.utcnow(), commodity
        )
        if seasonal_pattern == SeasonalPattern.HARVEST_SEASON:
            drivers.append("Harvest season supply increase")
        elif seasonal_pattern == SeasonalPattern.FESTIVAL_DEMAND:
            drivers.append("Festival season demand surge")
        
        return drivers
    
    def _identify_risk_factors(self, commodity: str, trend_analysis: TrendAnalysis) -> List[str]:
        """Identify risk factors for price prediction"""
        risk_factors = []
        
        if trend_analysis.volatility_level in [VolatilityLevel.HIGH, VolatilityLevel.EXTREME]:
            risk_factors.append("High market volatility")
        
        if trend_analysis.confidence_score < 0.6:
            risk_factors.append("Limited data reliability")
        
        # Seasonal risks
        seasonal_pattern = self.seasonal_analyzer.identify_seasonal_pattern(
            datetime.utcnow(), commodity
        )
        if seasonal_pattern == SeasonalPattern.MONSOON_IMPACT:
            risk_factors.append("Weather-related supply disruption risk")
        
        # General agricultural risks
        risk_factors.extend([
            "Weather and climate variability",
            "Government policy changes",
            "Global market fluctuations"
        ])
        
        return risk_factors
    
    def _calculate_trend_continuation_probability(
        self,
        trend_analysis: TrendAnalysis,
        prediction_days: int
    ) -> float:
        """Calculate probability of trend continuation"""
        # Base probability from trend strength
        base_prob = trend_analysis.trend_strength
        
        # Adjust for trend direction
        if trend_analysis.trend_direction in [TrendDirection.BULLISH, TrendDirection.BEARISH]:
            direction_bonus = 0.2
        else:
            direction_bonus = 0.0
        
        # Time decay (longer predictions = lower probability)
        time_decay = max(0.3, 1.0 - (prediction_days / 60))  # 60 days = 30% probability
        
        # Volatility penalty
        volatility_penalty = trend_analysis.volatility_score * 0.2
        
        probability = (base_prob + direction_bonus) * time_decay - volatility_penalty
        
        return max(0.1, min(0.9, probability))