"""
Anomaly Detection Algorithms for Anti-Hoarding Detection System
Implements statistical price spike detection, inventory level tracking, and stockpiling pattern detection
"""

import asyncio
import structlog
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import math
import statistics
from dataclasses import dataclass
import numpy as np
from collections import defaultdict, deque

from models import (
    PriceAnomaly, InventoryAnomaly, StockpilingPattern, AnomalyType, 
    AnomalySeverity, DetectionMethod, AnomalyDetectionConfig,
    SupplyDemandBalance, GeoLocation
)

logger = structlog.get_logger()

@dataclass
class PriceDataPoint:
    """Individual price data point for analysis"""
    commodity: str
    variety: Optional[str]
    price: float
    quantity: float
    mandi_id: str
    mandi_name: str
    location: GeoLocation
    timestamp: datetime
    confidence: float

@dataclass
class InventoryDataPoint:
    """Individual inventory data point for analysis"""
    commodity: str
    variety: Optional[str]
    inventory_level: float
    mandi_id: str
    mandi_name: str
    location: GeoLocation
    timestamp: datetime
    storage_capacity: Optional[float] = None

@dataclass
class StatisticalAnalysis:
    """Statistical analysis results"""
    mean: float
    median: float
    std_dev: float
    variance: float
    min_value: float
    max_value: float
    q1: float  # First quartile
    q3: float  # Third quartile
    iqr: float  # Interquartile range
    skewness: float
    kurtosis: float

class StatisticalAnalyzer:
    """Statistical analysis tools for anomaly detection"""
    
    @staticmethod
    def calculate_statistics(values: List[float]) -> StatisticalAnalysis:
        """Calculate comprehensive statistical measures"""
        if not values:
            raise ValueError("Cannot calculate statistics for empty list")
        
        values_sorted = sorted(values)
        n = len(values)
        
        mean = statistics.mean(values)
        median = statistics.median(values)
        std_dev = statistics.stdev(values) if n > 1 else 0.0
        variance = statistics.variance(values) if n > 1 else 0.0
        
        # Quartiles
        q1_idx = n // 4
        q3_idx = 3 * n // 4
        q1 = values_sorted[q1_idx]
        q3 = values_sorted[q3_idx]
        iqr = q3 - q1
        
        # Skewness and kurtosis (simplified calculations)
        if std_dev > 0:
            skewness = sum((x - mean) ** 3 for x in values) / (n * std_dev ** 3)
            kurtosis = sum((x - mean) ** 4 for x in values) / (n * std_dev ** 4) - 3
        else:
            skewness = 0.0
            kurtosis = 0.0
        
        return StatisticalAnalysis(
            mean=mean,
            median=median,
            std_dev=std_dev,
            variance=variance,
            min_value=min(values),
            max_value=max(values),
            q1=q1,
            q3=q3,
            iqr=iqr,
            skewness=skewness,
            kurtosis=kurtosis
        )
    
    @staticmethod
    def calculate_moving_average(values: List[float], window: int) -> List[float]:
        """Calculate moving average with specified window"""
        if len(values) < window:
            return []
        
        moving_averages = []
        for i in range(window - 1, len(values)):
            avg = sum(values[i - window + 1:i + 1]) / window
            moving_averages.append(avg)
        
        return moving_averages
    
    @staticmethod
    def calculate_z_score(value: float, mean: float, std_dev: float) -> float:
        """Calculate z-score for a value"""
        if std_dev == 0:
            return 0.0
        return (value - mean) / std_dev
    
    @staticmethod
    def detect_outliers_iqr(values: List[float], multiplier: float = 1.5) -> List[int]:
        """Detect outliers using IQR method"""
        stats = StatisticalAnalyzer.calculate_statistics(values)
        lower_bound = stats.q1 - multiplier * stats.iqr
        upper_bound = stats.q3 + multiplier * stats.iqr
        
        outlier_indices = []
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                outlier_indices.append(i)
        
        return outlier_indices
    
    @staticmethod
    def detect_outliers_z_score(values: List[float], threshold: float = 2.5) -> List[int]:
        """Detect outliers using z-score method"""
        if len(values) < 2:
            return []
        
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values)
        
        outlier_indices = []
        for i, value in enumerate(values):
            z_score = StatisticalAnalyzer.calculate_z_score(value, mean, std_dev)
            if abs(z_score) > threshold:
                outlier_indices.append(i)
        
        return outlier_indices

class PriceSpikeDetector:
    """Statistical price spike detection algorithm"""
    
    def __init__(self, config: AnomalyDetectionConfig):
        self.config = config
        self.statistical_analyzer = StatisticalAnalyzer()
    
    async def detect_price_spikes(
        self,
        price_data: List[PriceDataPoint],
        commodity: str,
        variety: Optional[str] = None
    ) -> List[PriceAnomaly]:
        """
        Detect price spikes using statistical analysis
        
        Requirements: 7.1 - Identify unusual price spikes that deviate more than 25% from 30-day moving averages
        """
        try:
            if not price_data:
                return []
            
            # Filter data for specific commodity and variety
            filtered_data = [
                p for p in price_data 
                if p.commodity == commodity and (variety is None or p.variety == variety)
            ]
            
            if len(filtered_data) < self.config.min_data_points:
                logger.warning(
                    "Insufficient data for price spike detection",
                    commodity=commodity,
                    variety=variety,
                    data_points=len(filtered_data),
                    min_required=self.config.min_data_points
                )
                return []
            
            # Sort by timestamp
            filtered_data.sort(key=lambda x: x.timestamp)
            
            # Extract prices and calculate moving average
            prices = [p.price for p in filtered_data]
            moving_averages = self.statistical_analyzer.calculate_moving_average(
                prices, self.config.moving_average_window_days
            )
            
            if not moving_averages:
                return []
            
            # Calculate statistical measures
            stats = self.statistical_analyzer.calculate_statistics(prices)
            
            anomalies = []
            
            # Check recent prices against moving average and statistical thresholds
            # The moving averages correspond to prices starting from index (window_size - 1)
            window_size = self.config.moving_average_window_days
            
            for i, moving_avg in enumerate(moving_averages):
                # Get the corresponding data point (moving avg i corresponds to price at index i + window_size - 1)
                data_point_index = i + window_size - 1
                if data_point_index >= len(filtered_data):
                    continue
                    
                data_point = filtered_data[data_point_index]
                current_price = data_point.price
                
                # Calculate deviation from moving average
                price_deviation = current_price - moving_avg
                deviation_percentage = (price_deviation / moving_avg) * 100
                
                # Calculate z-score
                z_score = self.statistical_analyzer.calculate_z_score(
                    current_price, stats.mean, stats.std_dev
                )
                
                # Check if this is a significant spike
                is_spike = (
                    abs(deviation_percentage) >= self.config.price_spike_threshold_percentage or
                    abs(z_score) >= self.config.z_score_threshold
                )
                
                if is_spike:
                    # Determine severity
                    severity = self._determine_price_spike_severity(
                        deviation_percentage, z_score
                    )
                    
                    # Calculate confidence score
                    confidence_score = self._calculate_price_spike_confidence(
                        deviation_percentage, z_score, len(filtered_data)
                    )
                    
                    # Identify contributing factors
                    contributing_factors = self._identify_price_spike_factors(
                        data_point, deviation_percentage, z_score, stats
                    )
                    
                    # Create anomaly record
                    anomaly = PriceAnomaly(
                        commodity=commodity,
                        variety=variety,
                        mandi_id=data_point.mandi_id,
                        mandi_name=data_point.mandi_name,
                        location=data_point.location,
                        anomaly_type=AnomalyType.PRICE_SPIKE,
                        detection_method=DetectionMethod.STATISTICAL_ANALYSIS,
                        severity=severity,
                        current_price=current_price,
                        baseline_price=moving_avg,
                        price_deviation=price_deviation,
                        deviation_percentage=deviation_percentage,
                        moving_average_30d=moving_avg,
                        standard_deviation=stats.std_dev,
                        z_score=z_score,
                        confidence_score=confidence_score,
                        analysis_period_days=self.config.moving_average_window_days,
                        evidence={
                            "statistical_analysis": stats.__dict__,
                            "moving_average_window": self.config.moving_average_window_days,
                            "data_points_analyzed": len(filtered_data),
                            "detection_timestamp": data_point.timestamp.isoformat()
                        },
                        contributing_factors=contributing_factors
                    )
                    
                    anomalies.append(anomaly)
                    
                    logger.warning(
                        "Price spike detected",
                        commodity=commodity,
                        variety=variety,
                        mandi=data_point.mandi_name,
                        current_price=current_price,
                        baseline_price=moving_avg,
                        deviation_percentage=deviation_percentage,
                        z_score=z_score,
                        severity=severity.value
                    )
            
            return anomalies
            
        except Exception as e:
            logger.error("Error in price spike detection", error=str(e))
            return []
    
    def _determine_price_spike_severity(
        self, 
        deviation_percentage: float, 
        z_score: float
    ) -> AnomalySeverity:
        """Determine severity of price spike"""
        abs_deviation = abs(deviation_percentage)
        abs_z_score = abs(z_score)
        
        if abs_deviation >= 50 or abs_z_score >= 4.0:
            return AnomalySeverity.CRITICAL
        elif abs_deviation >= 35 or abs_z_score >= 3.0:
            return AnomalySeverity.HIGH
        elif abs_deviation >= 25 or abs_z_score >= 2.5:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def _calculate_price_spike_confidence(
        self,
        deviation_percentage: float,
        z_score: float,
        data_points: int
    ) -> float:
        """Calculate confidence score for price spike detection"""
        # Base confidence from statistical significance
        z_confidence = min(1.0, abs(z_score) / 5.0)  # Normalize z-score to 0-1
        
        # Deviation confidence
        deviation_confidence = min(1.0, abs(deviation_percentage) / 100.0)
        
        # Data quality confidence
        data_confidence = min(1.0, data_points / 50.0)  # 50 points = full confidence
        
        # Combined confidence
        confidence = (z_confidence * 0.4 + deviation_confidence * 0.4 + data_confidence * 0.2)
        
        return max(0.1, min(1.0, confidence))
    
    def _identify_price_spike_factors(
        self,
        data_point: PriceDataPoint,
        deviation_percentage: float,
        z_score: float,
        stats: StatisticalAnalysis
    ) -> List[str]:
        """Identify contributing factors for price spike"""
        factors = []
        
        if deviation_percentage > 0:
            factors.append("Upward price pressure detected")
        else:
            factors.append("Downward price pressure detected")
        
        if abs(z_score) > 3.0:
            factors.append("Statistically extreme price movement")
        
        if stats.std_dev > stats.mean * 0.2:  # High volatility
            factors.append("High price volatility in recent period")
        
        if data_point.quantity < stats.mean * 0.5:  # Low volume
            factors.append("Lower than average trading volume")
        
        # Time-based factors
        hour = data_point.timestamp.hour
        if hour < 8 or hour > 18:
            factors.append("Price movement outside normal trading hours")
        
        return factors

class InventoryTracker:
    """Inventory level tracking across mandis"""
    
    def __init__(self, config: AnomalyDetectionConfig):
        self.config = config
        self.statistical_analyzer = StatisticalAnalyzer()
    
    async def detect_inventory_anomalies(
        self,
        inventory_data: List[InventoryDataPoint],
        commodity: str,
        variety: Optional[str] = None,
        region: Optional[str] = None
    ) -> List[InventoryAnomaly]:
        """
        Detect inventory level anomalies across mandis
        
        Requirements: 7.3 - Implement inventory level tracking across mandis
        """
        try:
            if not inventory_data:
                return []
            
            # Filter data
            filtered_data = [
                inv for inv in inventory_data
                if inv.commodity == commodity and (variety is None or inv.variety == variety)
            ]
            
            if len(filtered_data) < 3:  # Need minimum data for analysis
                return []
            
            # Group by region if specified
            if region:
                filtered_data = [
                    inv for inv in filtered_data
                    if region.lower() in inv.location.state.lower() or 
                       region.lower() in inv.location.district.lower()
                ]
            
            # Sort by timestamp
            filtered_data.sort(key=lambda x: x.timestamp)
            
            # Calculate normal inventory levels
            inventory_levels = [inv.inventory_level for inv in filtered_data]
            stats = self.statistical_analyzer.calculate_statistics(inventory_levels)
            
            # Calculate moving average for trend analysis
            window_size = min(7, len(inventory_levels) // 2)  # 7-day window or half the data
            if window_size >= 2:
                moving_averages = self.statistical_analyzer.calculate_moving_average(
                    inventory_levels, window_size
                )
            else:
                moving_averages = inventory_levels
            
            anomalies = []
            
            # Analyze recent inventory levels
            recent_data = filtered_data[-len(moving_averages):] if moving_averages else filtered_data
            
            for i, data_point in enumerate(recent_data):
                current_level = data_point.inventory_level
                normal_level = moving_averages[i] if i < len(moving_averages) else stats.mean
                
                # Calculate deviation
                deviation = current_level - normal_level
                deviation_percentage = (deviation / normal_level) * 100 if normal_level > 0 else 0
                
                # Check for significant deviation
                if abs(deviation_percentage) >= self.config.inventory_deviation_threshold:
                    # Determine anomaly type
                    if deviation > 0:
                        anomaly_type = AnomalyType.INVENTORY_HOARDING
                    else:
                        anomaly_type = AnomalyType.ARTIFICIAL_SCARCITY
                    
                    # Calculate severity
                    severity = self._determine_inventory_severity(deviation_percentage)
                    
                    # Analyze affected mandis and concentration
                    affected_mandis, concentration_ratio = self._analyze_inventory_concentration(
                        filtered_data, current_level, stats.mean
                    )
                    
                    # Determine trend
                    trend_direction = self._determine_inventory_trend(
                        inventory_levels[-window_size:] if len(inventory_levels) >= window_size else inventory_levels
                    )
                    
                    # Create anomaly record
                    anomaly = InventoryAnomaly(
                        commodity=commodity,
                        variety=variety,
                        region=region or data_point.location.state,
                        anomaly_type=anomaly_type,
                        detection_method=DetectionMethod.INVENTORY_TRACKING,
                        severity=severity,
                        current_inventory_level=current_level,
                        normal_inventory_level=normal_level,
                        inventory_deviation=deviation,
                        deviation_percentage=deviation_percentage,
                        affected_mandis=affected_mandis,
                        total_mandis_monitored=len(set(inv.mandi_id for inv in filtered_data)),
                        concentration_ratio=concentration_ratio,
                        accumulation_period_days=self.config.stockpiling_threshold_days,
                        trend_direction=trend_direction,
                        evidence={
                            "statistical_analysis": stats.__dict__,
                            "inventory_data_points": len(filtered_data),
                            "analysis_window_days": window_size,
                            "detection_timestamp": data_point.timestamp.isoformat()
                        },
                        stockpiling_indicators=self._identify_stockpiling_indicators(
                            data_point, deviation_percentage, trend_direction
                        )
                    )
                    
                    anomalies.append(anomaly)
                    
                    logger.warning(
                        "Inventory anomaly detected",
                        commodity=commodity,
                        variety=variety,
                        region=region,
                        anomaly_type=anomaly_type.value,
                        current_level=current_level,
                        normal_level=normal_level,
                        deviation_percentage=deviation_percentage,
                        severity=severity.value
                    )
            
            return anomalies
            
        except Exception as e:
            logger.error("Error in inventory anomaly detection", error=str(e))
            return []
    
    def _determine_inventory_severity(self, deviation_percentage: float) -> AnomalySeverity:
        """Determine severity of inventory anomaly"""
        abs_deviation = abs(deviation_percentage)
        
        if abs_deviation >= 75:
            return AnomalySeverity.CRITICAL
        elif abs_deviation >= 50:
            return AnomalySeverity.HIGH
        elif abs_deviation >= 30:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def _analyze_inventory_concentration(
        self,
        inventory_data: List[InventoryDataPoint],
        current_level: float,
        average_level: float
    ) -> Tuple[List[str], float]:
        """Analyze inventory concentration across mandis"""
        # Group by mandi
        mandi_inventories = defaultdict(list)
        for inv in inventory_data:
            mandi_inventories[inv.mandi_id].append(inv.inventory_level)
        
        # Calculate average inventory per mandi
        mandi_averages = {
            mandi_id: statistics.mean(levels)
            for mandi_id, levels in mandi_inventories.items()
        }
        
        # Find mandis with high inventory concentration
        affected_mandis = []
        total_inventory = sum(mandi_averages.values())
        
        for mandi_id, avg_level in mandi_averages.items():
            if avg_level > average_level * 1.5:  # 50% above average
                affected_mandis.append(mandi_id)
        
        # Calculate concentration ratio (Herfindahl-Hirschman Index style)
        if total_inventory > 0:
            concentration_ratio = sum(
                (level / total_inventory) ** 2 
                for level in mandi_averages.values()
            )
        else:
            concentration_ratio = 0.0
        
        return affected_mandis, concentration_ratio
    
    def _determine_inventory_trend(self, recent_levels: List[float]) -> str:
        """Determine inventory trend direction"""
        if len(recent_levels) < 2:
            return "stable"
        
        # Calculate trend using linear regression slope
        n = len(recent_levels)
        x_values = list(range(n))
        
        x_mean = sum(x_values) / n
        y_mean = sum(recent_levels) / n
        
        numerator = sum((x_values[i] - x_mean) * (recent_levels[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        
        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"
    
    def _identify_stockpiling_indicators(
        self,
        data_point: InventoryDataPoint,
        deviation_percentage: float,
        trend_direction: str
    ) -> List[str]:
        """Identify indicators of stockpiling behavior"""
        indicators = []
        
        if deviation_percentage > 50:
            indicators.append("Significantly above normal inventory levels")
        
        if trend_direction == "increasing":
            indicators.append("Consistent inventory accumulation pattern")
        
        if data_point.storage_capacity and data_point.inventory_level > data_point.storage_capacity * 0.9:
            indicators.append("Near maximum storage capacity utilization")
        
        # Time-based indicators
        current_month = data_point.timestamp.month
        if current_month in [3, 4, 5]:  # Pre-harvest season
            indicators.append("Unusual stockpiling during pre-harvest period")
        elif current_month in [10, 11, 12]:  # Post-harvest season
            indicators.append("Extended storage beyond normal post-harvest period")
        
        return indicators

class StockpilingPatternDetector:
    """Stockpiling pattern detection across regions"""
    
    def __init__(self, config: AnomalyDetectionConfig):
        self.config = config
        self.statistical_analyzer = StatisticalAnalyzer()
    
    async def detect_stockpiling_patterns(
        self,
        inventory_data: List[InventoryDataPoint],
        price_data: List[PriceDataPoint],
        commodity: str,
        variety: Optional[str] = None
    ) -> List[StockpilingPattern]:
        """
        Detect coordinated stockpiling patterns
        
        Requirements: 7.3 - Create stockpiling pattern detection
        """
        try:
            if not inventory_data or not price_data:
                return []
            
            # Filter data for commodity
            filtered_inventory = [
                inv for inv in inventory_data
                if inv.commodity == commodity and (variety is None or inv.variety == variety)
            ]
            
            filtered_prices = [
                p for p in price_data
                if p.commodity == commodity and (variety is None or p.variety == variety)
            ]
            
            if len(filtered_inventory) < 5 or len(filtered_prices) < 5:
                return []
            
            patterns = []
            
            # Detect coordinated stockpiling
            coordinated_patterns = await self._detect_coordinated_stockpiling(
                filtered_inventory, commodity, variety
            )
            patterns.extend(coordinated_patterns)
            
            # Detect cross-regional patterns
            cross_regional_patterns = await self._detect_cross_regional_patterns(
                filtered_inventory, filtered_prices, commodity, variety
            )
            patterns.extend(cross_regional_patterns)
            
            # Detect seasonal unusual patterns
            seasonal_patterns = await self._detect_seasonal_unusual_patterns(
                filtered_inventory, commodity, variety
            )
            patterns.extend(seasonal_patterns)
            
            return patterns
            
        except Exception as e:
            logger.error("Error in stockpiling pattern detection", error=str(e))
            return []
    
    async def _detect_coordinated_stockpiling(
        self,
        inventory_data: List[InventoryDataPoint],
        commodity: str,
        variety: Optional[str]
    ) -> List[StockpilingPattern]:
        """Detect coordinated stockpiling across multiple locations"""
        patterns = []
        
        # Group by location (state/district)
        location_groups = defaultdict(list)
        for inv in inventory_data:
            location_key = f"{inv.location.state}_{inv.location.district}"
            location_groups[location_key].append(inv)
        
        # Analyze for coordination
        if len(location_groups) >= 3:  # Need at least 3 locations for coordination
            # Calculate inventory trends for each location
            location_trends = {}
            for location, inventories in location_groups.items():
                if len(inventories) >= 3:
                    inventories.sort(key=lambda x: x.timestamp)
                    levels = [inv.inventory_level for inv in inventories]
                    
                    # Calculate accumulation rate
                    time_span = (inventories[-1].timestamp - inventories[0].timestamp).days
                    if time_span > 0:
                        accumulation_rate = (levels[-1] - levels[0]) / time_span
                        location_trends[location] = {
                            'rate': accumulation_rate,
                            'total': sum(levels),
                            'inventories': inventories
                        }
            
            # Look for synchronized accumulation
            if len(location_trends) >= 3:
                rates = [trend['rate'] for trend in location_trends.values()]
                
                # Check if accumulation rates are similar (coordinated)
                if len(rates) > 1:
                    rate_std = statistics.stdev(rates)
                    rate_mean = statistics.mean(rates)
                    
                    # If rates are similar and positive (accumulating)
                    if rate_std < rate_mean * 0.3 and rate_mean > 0:
                        # Calculate pattern characteristics
                        involved_locations = list(location_trends.keys())
                        total_accumulated = sum(trend['total'] for trend in location_trends.values())
                        avg_accumulation_rate = rate_mean
                        
                        # Estimate pattern duration
                        all_timestamps = []
                        for trend in location_trends.values():
                            all_timestamps.extend([inv.timestamp for inv in trend['inventories']])
                        
                        pattern_duration = (max(all_timestamps) - min(all_timestamps)).days
                        
                        # Calculate confidence
                        confidence_score = self._calculate_coordination_confidence(
                            location_trends, rate_std, rate_mean
                        )
                        
                        if confidence_score >= self.config.pattern_confidence_threshold:
                            pattern = StockpilingPattern(
                                commodity=commodity,
                                variety=variety,
                                pattern_type="coordinated",
                                detection_method=DetectionMethod.PATTERN_RECOGNITION,
                                severity=self._determine_pattern_severity(
                                    len(involved_locations), total_accumulated, avg_accumulation_rate
                                ),
                                involved_locations=involved_locations,
                                pattern_duration_days=pattern_duration,
                                accumulation_rate=avg_accumulation_rate,
                                total_accumulated_quantity=total_accumulated,
                                confidence_score=confidence_score,
                                pattern_indicators=[
                                    "Synchronized inventory accumulation across multiple locations",
                                    f"Similar accumulation rates detected in {len(involved_locations)} locations",
                                    f"Total accumulated quantity: {total_accumulated:.2f} units"
                                ],
                                evidence={
                                    "location_trends": {
                                        loc: {
                                            "accumulation_rate": trend["rate"],
                                            "total_inventory": trend["total"]
                                        }
                                        for loc, trend in location_trends.items()
                                    },
                                    "statistical_analysis": {
                                        "rate_mean": rate_mean,
                                        "rate_std": rate_std,
                                        "coordination_coefficient": rate_std / rate_mean if rate_mean > 0 else 0
                                    }
                                },
                                coordination_evidence={
                                    "synchronized_locations": len(involved_locations),
                                    "rate_similarity": 1 - (rate_std / rate_mean) if rate_mean > 0 else 0,
                                    "temporal_overlap": pattern_duration
                                }
                            )
                            
                            patterns.append(pattern)
                            
                            logger.warning(
                                "Coordinated stockpiling pattern detected",
                                commodity=commodity,
                                variety=variety,
                                locations=len(involved_locations),
                                total_accumulated=total_accumulated,
                                confidence=confidence_score
                            )
        
        return patterns
    
    async def _detect_cross_regional_patterns(
        self,
        inventory_data: List[InventoryDataPoint],
        price_data: List[PriceDataPoint],
        commodity: str,
        variety: Optional[str]
    ) -> List[StockpilingPattern]:
        """Detect cross-regional stockpiling patterns"""
        patterns = []
        
        # Group inventory by state
        state_inventories = defaultdict(list)
        for inv in inventory_data:
            state_inventories[inv.location.state].append(inv)
        
        # Group prices by state
        state_prices = defaultdict(list)
        for price in price_data:
            state_prices[price.location.state].append(price)
        
        # Look for patterns where inventory accumulation in one region correlates with price increases in others
        for accumulating_state, inventories in state_inventories.items():
            if len(inventories) < 3:
                continue
            
            # Calculate inventory trend
            inventories.sort(key=lambda x: x.timestamp)
            levels = [inv.inventory_level for inv in inventories]
            
            if len(levels) > 1:
                # Check if inventory is increasing
                recent_trend = (levels[-1] - levels[0]) / len(levels)
                
                if recent_trend > 0:  # Inventory accumulating
                    # Check price trends in other states
                    for other_state, prices in state_prices.items():
                        if other_state != accumulating_state and len(prices) >= 3:
                            prices.sort(key=lambda x: x.timestamp)
                            price_values = [p.price for p in prices]
                            
                            # Check if prices are rising in other state
                            price_trend = (price_values[-1] - price_values[0]) / len(price_values)
                            
                            if price_trend > 0:  # Prices rising
                                # Calculate correlation strength
                                correlation_strength = self._calculate_cross_regional_correlation(
                                    inventories, prices
                                )
                                
                                if correlation_strength > 0.6:  # Strong correlation
                                    pattern = StockpilingPattern(
                                        commodity=commodity,
                                        variety=variety,
                                        pattern_type="cross_regional",
                                        detection_method=DetectionMethod.PATTERN_RECOGNITION,
                                        severity=AnomalySeverity.HIGH,
                                        involved_locations=[accumulating_state, other_state],
                                        pattern_duration_days=(
                                            max(inventories[-1].timestamp, prices[-1].timestamp) -
                                            min(inventories[0].timestamp, prices[0].timestamp)
                                        ).days,
                                        accumulation_rate=recent_trend,
                                        total_accumulated_quantity=sum(levels),
                                        price_impact_percentage=(price_trend / price_values[0]) * 100,
                                        confidence_score=correlation_strength,
                                        pattern_indicators=[
                                            f"Inventory accumulation in {accumulating_state}",
                                            f"Price increases in {other_state}",
                                            f"Cross-regional correlation: {correlation_strength:.2f}"
                                        ],
                                        evidence={
                                            "accumulating_region": accumulating_state,
                                            "affected_price_region": other_state,
                                            "inventory_trend": recent_trend,
                                            "price_trend": price_trend,
                                            "correlation_strength": correlation_strength
                                        }
                                    )
                                    
                                    patterns.append(pattern)
        
        return patterns
    
    async def _detect_seasonal_unusual_patterns(
        self,
        inventory_data: List[InventoryDataPoint],
        commodity: str,
        variety: Optional[str]
    ) -> List[StockpilingPattern]:
        """Detect seasonally unusual stockpiling patterns"""
        patterns = []
        
        # Group by month to identify seasonal patterns
        monthly_inventories = defaultdict(list)
        for inv in inventory_data:
            month = inv.timestamp.month
            monthly_inventories[month].append(inv.inventory_level)
        
        # Calculate seasonal baselines
        seasonal_baselines = {}
        for month, levels in monthly_inventories.items():
            if len(levels) >= 3:
                seasonal_baselines[month] = statistics.mean(levels)
        
        # Check current month against seasonal baseline
        current_month = datetime.utcnow().month
        if current_month in seasonal_baselines:
            recent_inventories = [
                inv for inv in inventory_data
                if inv.timestamp.month == current_month and
                   (datetime.utcnow() - inv.timestamp).days <= 30
            ]
            
            if recent_inventories:
                current_levels = [inv.inventory_level for inv in recent_inventories]
                current_average = statistics.mean(current_levels)
                seasonal_baseline = seasonal_baselines[current_month]
                
                # Check for unusual deviation from seasonal pattern
                seasonal_deviation = (current_average - seasonal_baseline) / seasonal_baseline * 100
                
                if abs(seasonal_deviation) > 40:  # 40% deviation from seasonal norm
                    pattern = StockpilingPattern(
                        commodity=commodity,
                        variety=variety,
                        pattern_type="seasonal_unusual",
                        detection_method=DetectionMethod.PATTERN_RECOGNITION,
                        severity=self._determine_seasonal_severity(seasonal_deviation),
                        involved_locations=[inv.location.state for inv in recent_inventories],
                        pattern_duration_days=30,
                        accumulation_rate=seasonal_deviation / 30,  # Daily rate
                        total_accumulated_quantity=sum(current_levels),
                        confidence_score=min(1.0, abs(seasonal_deviation) / 100),
                        pattern_indicators=[
                            f"Unusual seasonal pattern detected for month {current_month}",
                            f"Deviation from seasonal baseline: {seasonal_deviation:.1f}%",
                            "Inventory levels significantly different from historical seasonal pattern"
                        ],
                        evidence={
                            "current_month": current_month,
                            "seasonal_baseline": seasonal_baseline,
                            "current_average": current_average,
                            "seasonal_deviation_percentage": seasonal_deviation,
                            "historical_data_points": len(monthly_inventories[current_month])
                        }
                    )
                    
                    patterns.append(pattern)
        
        return patterns
    
    def _calculate_coordination_confidence(
        self,
        location_trends: Dict[str, Dict],
        rate_std: float,
        rate_mean: float
    ) -> float:
        """Calculate confidence score for coordination detection"""
        # Similarity of rates (lower std = higher confidence)
        rate_similarity = 1 - (rate_std / rate_mean) if rate_mean > 0 else 0
        
        # Number of locations (more locations = higher confidence)
        location_confidence = min(1.0, len(location_trends) / 5)  # 5 locations = full confidence
        
        # Magnitude of accumulation (higher rates = higher confidence)
        magnitude_confidence = min(1.0, rate_mean / 10)  # 10 units/day = full confidence
        
        # Combined confidence
        confidence = (rate_similarity * 0.5 + location_confidence * 0.3 + magnitude_confidence * 0.2)
        
        return max(0.1, min(1.0, confidence))
    
    def _determine_pattern_severity(
        self,
        num_locations: int,
        total_accumulated: float,
        accumulation_rate: float
    ) -> AnomalySeverity:
        """Determine severity of stockpiling pattern"""
        # Score based on multiple factors
        location_score = min(4, num_locations)  # Max 4 points
        quantity_score = min(4, total_accumulated / 1000)  # 1000 units = 4 points
        rate_score = min(4, accumulation_rate * 10)  # 0.4 units/day = 4 points
        
        total_score = location_score + quantity_score + rate_score
        
        if total_score >= 10:
            return AnomalySeverity.CRITICAL
        elif total_score >= 7:
            return AnomalySeverity.HIGH
        elif total_score >= 4:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def _calculate_cross_regional_correlation(
        self,
        inventories: List[InventoryDataPoint],
        prices: List[PriceDataPoint]
    ) -> float:
        """Calculate correlation between inventory accumulation and price changes"""
        # Simplified correlation calculation
        # In practice, this would use more sophisticated time-series correlation
        
        if len(inventories) < 2 or len(prices) < 2:
            return 0.0
        
        # Calculate trends
        inv_levels = [inv.inventory_level for inv in inventories]
        price_values = [p.price for p in prices]
        
        inv_trend = (inv_levels[-1] - inv_levels[0]) / len(inv_levels)
        price_trend = (price_values[-1] - price_values[0]) / len(price_values)
        
        # Normalize trends
        inv_trend_norm = inv_trend / statistics.mean(inv_levels) if statistics.mean(inv_levels) > 0 else 0
        price_trend_norm = price_trend / statistics.mean(price_values) if statistics.mean(price_values) > 0 else 0
        
        # Simple correlation measure (positive inventory trend with positive price trend)
        if inv_trend_norm > 0 and price_trend_norm > 0:
            correlation = min(1.0, (inv_trend_norm + price_trend_norm) / 2)
        else:
            correlation = 0.0
        
        return correlation
    
    def _determine_seasonal_severity(self, seasonal_deviation: float) -> AnomalySeverity:
        """Determine severity of seasonal pattern anomaly"""
        abs_deviation = abs(seasonal_deviation)
        
        if abs_deviation >= 80:
            return AnomalySeverity.CRITICAL
        elif abs_deviation >= 60:
            return AnomalySeverity.HIGH
        elif abs_deviation >= 40:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW

class AnomalyDetectionEngine:
    """Main anomaly detection engine coordinating all detection algorithms"""
    
    def __init__(self, config: AnomalyDetectionConfig = None):
        self.config = config or AnomalyDetectionConfig()
        self.price_spike_detector = PriceSpikeDetector(self.config)
        self.inventory_tracker = InventoryTracker(self.config)
        self.stockpiling_detector = StockpilingPatternDetector(self.config)
    
    async def run_comprehensive_analysis(
        self,
        price_data: List[PriceDataPoint],
        inventory_data: List[InventoryDataPoint],
        commodity: str,
        variety: Optional[str] = None,
        region: Optional[str] = None
    ) -> Dict[str, List]:
        """
        Run comprehensive anomaly detection analysis
        
        Returns:
            Dictionary containing all detected anomalies by type
        """
        results = {
            "price_anomalies": [],
            "inventory_anomalies": [],
            "stockpiling_patterns": []
        }
        
        try:
            # Run price spike detection
            if price_data:
                price_anomalies = await self.price_spike_detector.detect_price_spikes(
                    price_data, commodity, variety
                )
                results["price_anomalies"] = price_anomalies
            
            # Run inventory anomaly detection
            if inventory_data:
                inventory_anomalies = await self.inventory_tracker.detect_inventory_anomalies(
                    inventory_data, commodity, variety, region
                )
                results["inventory_anomalies"] = inventory_anomalies
            
            # Run stockpiling pattern detection
            if inventory_data and price_data:
                stockpiling_patterns = await self.stockpiling_detector.detect_stockpiling_patterns(
                    inventory_data, price_data, commodity, variety
                )
                results["stockpiling_patterns"] = stockpiling_patterns
            
            # Log summary
            total_anomalies = (
                len(results["price_anomalies"]) +
                len(results["inventory_anomalies"]) +
                len(results["stockpiling_patterns"])
            )
            
            logger.info(
                "Comprehensive anomaly analysis completed",
                commodity=commodity,
                variety=variety,
                region=region,
                total_anomalies=total_anomalies,
                price_anomalies=len(results["price_anomalies"]),
                inventory_anomalies=len(results["inventory_anomalies"]),
                stockpiling_patterns=len(results["stockpiling_patterns"])
            )
            
        except Exception as e:
            logger.error("Error in comprehensive anomaly analysis", error=str(e))
        
        return results