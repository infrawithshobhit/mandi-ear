# MSP Enforcement Service

## Overview

The MSP Enforcement Service is a comprehensive system for monitoring Minimum Support Price (MSP) compliance, detecting violations, and providing alternative market suggestions to farmers. This service implements Requirements 6.1 and 6.3 from the MANDI EAR™ specification.

## Features

### 🔍 Continuous MSP Monitoring
- Real-time comparison of market prices against government MSP rates
- Automated violation detection with configurable thresholds
- Multi-commodity support across all MSP-covered crops
- Confidence-based filtering for data quality assurance

### 🏛️ Government Data Integration
- Automated sync with government data sources (CACP, FCI, AgMarkNet)
- Web scraping and API integration for MSP rate updates
- Support for multiple data formats (CSV, Excel, PDF, HTML)
- Reliable data validation and normalization

### 🚨 Intelligent Alert System
- Severity-based alert classification (Low, Medium, High, Critical)
- Multi-channel notification delivery (SMS, Push, Voice)
- Contextual alert messages with actionable recommendations
- Farmer-specific alert preferences and targeting

### 🏪 Alternative Market Suggestions
- Government procurement center directory
- Distance-based market recommendations
- Transportation cost calculations
- Net benefit analysis for farmers

### 📊 Compliance Reporting
- Violation tracking and evidence collection
- Regulatory compliance reports
- Performance analytics and trends
- Regional and commodity-wise insights

## Architecture

### Core Components

1. **MSP Monitoring Engine** (`msp_monitor.py`)
   - Continuous price comparison logic
   - Violation detection algorithms
   - Configurable monitoring parameters
   - Real-time processing pipeline

2. **Government Data Integrator** (`government_data_integration.py`)
   - Multi-source data collection
   - Web scraping and API integration
   - Data parsing and validation
   - Automated sync scheduling

3. **Alert System** (`alert_system.py`)
   - Violation processing and alert generation
   - Alternative market discovery
   - Multi-channel notification delivery
   - User preference management

4. **Database Layer** (`database.py`)
   - PostgreSQL integration
   - Data models and operations
   - Query optimization
   - Transaction management

5. **REST API** (`main.py`)
   - FastAPI-based service endpoints
   - Real-time monitoring controls
   - Data access and management
   - Configuration management

### Data Models

#### MSP Rate
```python
MSPRate(
    commodity="Wheat",
    season=MSPSeason.RABI,
    crop_year="2023-24",
    msp_price=2125.0,
    commodity_type=MSPCommodityType.CEREALS,
    effective_date=date(2023, 4, 1),
    announcement_date=date(2023, 3, 15)
)
```

#### MSP Violation
```python
MSPViolation(
    commodity="Wheat",
    mandi_id="mandi_punjab_001",
    market_price=2000.0,
    msp_price=2125.0,
    violation_percentage=5.88,
    severity=AlertSeverity.MEDIUM
)
```

#### Procurement Center
```python
ProcurementCenter(
    name="FCI Depot Delhi",
    center_type="FCI",
    address="Sector 12, Dwarka, New Delhi",
    commodities_accepted=["Wheat", "Rice", "Maize"]
)
```

## API Endpoints

### Monitoring
- `GET /monitoring/stats` - Get monitoring statistics
- `POST /monitoring/start` - Start MSP monitoring
- `POST /monitoring/stop` - Stop MSP monitoring
- `POST /monitoring/trigger` - Trigger manual monitoring cycle

### MSP Rates
- `GET /msp-rates` - Get MSP rates with filters
- `POST /msp-rates` - Add/update MSP rate

### Violations
- `GET /violations` - Get violations with filters
- `POST /violations/{id}/resolve` - Mark violation as resolved

### Alerts
- `GET /alerts` - Get alerts for farmers
- `POST /alerts/{id}/read` - Mark alert as read
- `POST /alerts/{id}/acknowledge` - Acknowledge alert

### Procurement Centers
- `GET /procurement-centers` - Get procurement centers
- `POST /procurement-centers` - Add procurement center

### Government Data
- `POST /government-data/sync` - Trigger data sync
- `POST /government-data/sync-procurement-centers` - Sync procurement centers

### Price Comparison
- `POST /compare` - Compare market price with MSP

## Configuration

### Monitoring Configuration
```python
MonitoringConfig(
    check_interval_minutes=15,           # Check every 15 minutes
    violation_threshold_percentage=5.0,  # Alert at 5% below MSP
    critical_threshold_percentage=15.0,  # Critical at 15% below MSP
    min_confidence_score=0.7,           # Minimum data confidence
    max_price_age_hours=2               # Use prices from last 2 hours
)
```

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/mandi_ear
REDIS_URL=redis://localhost:6379
INFLUXDB_URL=http://localhost:8086
```

## Database Schema

### Tables
- `msp_rates` - MSP rate data
- `msp_violations` - Detected violations
- `msp_alerts` - Generated alerts
- `procurement_centers` - Government procurement centers
- `alternative_suggestions` - Market alternatives
- `government_data_sources` - Data source configurations

### Indexes
- Commodity-based indexes for fast lookups
- Location-based indexes for regional queries
- Time-based indexes for trend analysis

## Deployment

### Docker
```bash
# Build the service
docker build -t msp-enforcement-service .

# Run with docker-compose
docker-compose up msp-enforcement-service
```

### Service Port
- Default port: 8005
- Health check: `GET /health`
- API documentation: `GET /docs`

## Integration Points

### Price Discovery Service
- Real-time market price data
- Mandi information and metadata
- Price confidence scores

### Voice Processing Service
- Multilingual alert delivery
- Voice-based notifications
- Regional language support

### User Management Service
- Farmer profiles and preferences
- Notification settings
- Location-based targeting

## Monitoring and Observability

### Metrics
- Violations detected per hour
- Alert delivery success rates
- Data source sync status
- API response times

### Logging
- Structured logging with structlog
- Error tracking and alerting
- Performance monitoring
- Audit trails

## Testing

### Basic Tests
```bash
python test_basic.py
```

### Unit Tests
- Model validation tests
- Business logic tests
- API endpoint tests
- Database operation tests

### Integration Tests
- End-to-end workflow tests
- External service integration
- Performance tests
- Load tests

## Security

### Data Protection
- Sensitive data encryption
- Secure API authentication
- Rate limiting and throttling
- Input validation and sanitization

### Compliance
- GDPR compliance for farmer data
- Government data usage policies
- Audit logging requirements
- Data retention policies

## Performance

### Optimization
- Database query optimization
- Caching strategies (Redis)
- Asynchronous processing
- Connection pooling

### Scalability
- Horizontal scaling support
- Load balancing ready
- Microservice architecture
- Event-driven processing

## Future Enhancements

### Planned Features
- Machine learning for price prediction
- Advanced analytics dashboard
- Mobile app integration
- Blockchain-based audit trails

### Integration Roadmap
- Additional government data sources
- International market data
- Weather data correlation
- Supply chain tracking

## Support

### Documentation
- API documentation at `/docs`
- Database schema documentation
- Deployment guides
- Troubleshooting guides

### Monitoring
- Health check endpoints
- Metrics and alerting
- Log aggregation
- Performance dashboards

---

**Service Status**: ✅ Implemented and Tested
**Requirements Covered**: 6.1 (Continuous MSP monitoring), 6.3 (MSP rate management)
**Last Updated**: January 2025