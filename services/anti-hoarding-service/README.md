# Anti-Hoarding Detection Service

The Anti-Hoarding Detection Service implements advanced anomaly detection algorithms to identify market manipulation and hoarding patterns in agricultural commodities. This service is a critical component of the MANDI EAR™ platform's anti-hoarding detection system.

## Features

### Core Algorithms

1. **Statistical Price Spike Detection**
   - Detects price spikes that deviate more than 25% from 30-day moving averages
   - Uses z-score analysis for statistical significance
   - Configurable thresholds and analysis windows
   - Confidence scoring for detection reliability

2. **Inventory Level Tracking**
   - Monitors inventory levels across multiple mandis
   - Detects unusual accumulation patterns
   - Identifies artificial scarcity scenarios
   - Cross-mandi concentration analysis

3. **Stockpiling Pattern Detection**
   - Coordinated stockpiling across multiple locations
   - Cross-regional pattern analysis
   - Seasonal anomaly detection
   - Pattern correlation with price movements

### Requirements Implemented

- **Requirement 7.1**: Identify unusual price spikes that deviate more than 25% from 30-day moving averages
- **Requirement 7.3**: Track inventory levels across mandis and detect abnormal stockpiling patterns

## API Endpoints

### Detection Endpoints

- `POST /detect/comprehensive` - Run comprehensive anomaly detection
- `POST /detect/price-spikes` - Detect price spikes only
- `POST /detect/inventory-anomalies` - Detect inventory anomalies only
- `POST /detect/stockpiling-patterns` - Detect stockpiling patterns only

### Query Endpoints

- `GET /anomalies/price` - Retrieve price anomalies with filters
- `GET /anomalies/inventory` - Retrieve inventory anomalies with filters
- `GET /patterns/stockpiling` - Retrieve stockpiling patterns with filters
- `GET /anomalies/recent` - Get recent anomalies across all types

### Management Endpoints

- `GET /config` - Get current detection configuration
- `PUT /config` - Update detection configuration
- `PUT /anomalies/status` - Update anomaly status (confirmed/resolved)
- `GET /statistics` - Get detection statistics

### Health and Monitoring

- `GET /health` - Health check endpoint

## Data Models

### Core Anomaly Types

1. **PriceAnomaly**
   - Price spike detection results
   - Statistical analysis data
   - Confidence scoring
   - Contributing factors

2. **InventoryAnomaly**
   - Inventory level anomalies
   - Cross-mandi analysis
   - Stockpiling indicators
   - Trend analysis

3. **StockpilingPattern**
   - Pattern detection results
   - Coordination evidence
   - Market impact analysis
   - Confidence scoring

## Configuration

The service uses `AnomalyDetectionConfig` for algorithm parameters:

```python
{
    "price_spike_threshold_percentage": 25.0,
    "moving_average_window_days": 30,
    "min_data_points": 10,
    "z_score_threshold": 2.5,
    "inventory_deviation_threshold": 30.0,
    "stockpiling_threshold_days": 7,
    "pattern_confidence_threshold": 0.75
}
```

## Usage Examples

### Comprehensive Detection

```bash
curl -X POST "http://localhost:8007/detect/comprehensive" \
  -H "Content-Type: application/json" \
  -d '{
    "commodity": "wheat",
    "variety": "HD-2967",
    "region": "Punjab",
    "analysis_period_days": 30
  }'
```

### Price Spike Detection

```bash
curl -X POST "http://localhost:8007/detect/price-spikes" \
  -H "Content-Type: application/json" \
  -d '{
    "commodity": "rice",
    "variety": "Basmati",
    "threshold_percentage": 25.0,
    "analysis_period_days": 30
  }'
```

### Query Recent Anomalies

```bash
curl "http://localhost:8007/anomalies/recent?commodity=wheat&hours_back=24"
```

## Algorithm Details

### Statistical Price Spike Detection

1. **Data Collection**: Gather price data for specified commodity and time period
2. **Moving Average Calculation**: Calculate 30-day moving average
3. **Deviation Analysis**: Compare current prices against moving average
4. **Statistical Validation**: Use z-score analysis for significance testing
5. **Severity Classification**: Classify anomalies by severity level
6. **Confidence Scoring**: Calculate detection confidence based on multiple factors

### Inventory Tracking Algorithm

1. **Data Aggregation**: Collect inventory data across multiple mandis
2. **Baseline Calculation**: Establish normal inventory levels
3. **Deviation Detection**: Identify significant deviations from baseline
4. **Concentration Analysis**: Analyze inventory concentration patterns
5. **Trend Analysis**: Determine accumulation/depletion trends
6. **Pattern Classification**: Classify as hoarding or artificial scarcity

### Stockpiling Pattern Detection

1. **Multi-Location Analysis**: Analyze inventory patterns across regions
2. **Coordination Detection**: Identify synchronized accumulation patterns
3. **Cross-Regional Correlation**: Correlate inventory with price movements
4. **Seasonal Analysis**: Detect seasonally unusual patterns
5. **Confidence Assessment**: Calculate pattern detection confidence
6. **Evidence Collection**: Gather supporting evidence for patterns

## Testing

Run the test suite:

```bash
pytest test_anomaly_detection.py -v
```

Test categories:
- Unit tests for individual algorithms
- Integration tests for complete workflows
- Statistical validation tests
- Edge case handling tests

## Performance Considerations

- **Data Volume**: Optimized for processing large datasets efficiently
- **Real-time Processing**: Designed for near real-time anomaly detection
- **Scalability**: Horizontal scaling support through microservices architecture
- **Memory Management**: Efficient memory usage for large time-series data

## Monitoring and Alerting

The service provides comprehensive monitoring:
- Detection statistics and performance metrics
- Anomaly confirmation and resolution tracking
- False positive rate monitoring
- System health and availability metrics

## Integration

The service integrates with:
- **Price Discovery Service**: For real-time price data
- **MSP Enforcement Service**: For market manipulation alerts
- **Notification Service**: For farmer and authority alerts
- **Analytics Service**: For reporting and insights

## Security and Compliance

- Input validation and sanitization
- Rate limiting for API endpoints
- Audit logging for all detections
- Evidence preservation for regulatory compliance

## Deployment

### Docker Deployment

```bash
docker build -t anti-hoarding-service .
docker run -p 8007:8007 anti-hoarding-service
```

### Environment Variables

- `LOG_LEVEL`: Logging level (default: INFO)
- `API_PORT`: Service port (default: 8007)
- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection for caching

## Contributing

1. Follow the existing code structure and patterns
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure compliance with agricultural market regulations

## License

This service is part of the MANDI EAR™ platform and follows the project's licensing terms.