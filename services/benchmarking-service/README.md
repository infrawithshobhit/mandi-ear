# MANDI EAR™ Benchmarking Service

## Overview

The Benchmarking Service provides personalized benchmarking capabilities for farmers, enabling them to set minimum price floors, create historical benchmarks from conversation data, and track their performance against established benchmarks.

## Features

### 1. Minimum Price Floor Setting
- **Set personalized price floors**: Farmers can set minimum acceptable prices for different commodities
- **Reasoning tracking**: Store the rationale behind price floor decisions
- **Automatic deactivation**: Previous floors are deactivated when new ones are set
- **Multi-commodity support**: Different floors for different commodities

### 2. Historical Benchmark Creation
- **Conversation analysis**: Analyze historical conversation data to extract price patterns
- **Weighted calculations**: Use confidence scores, recency, and quantity to weight price data
- **Location-aware**: Consider location context in benchmark creation
- **Quality indicators**: Track data quality and confidence metrics
- **Time trend analysis**: Analyze price trends over time

### 3. Performance Tracking
- **Real-time tracking**: Track actual sales performance against benchmarks and floors
- **Performance scoring**: Calculate comprehensive performance scores (0-100)
- **Category classification**: Classify performance into categories (Excellent, Good, Average, Below Average, Poor)
- **Revenue analysis**: Calculate revenue differences and improvement opportunities
- **Trend analysis**: Track performance trends over time

### 4. Performance Analytics System ⭐ NEW
- **Income Improvement Calculation**: Calculate and track income improvements over time by comparing recent performance against historical baselines
- **Performance Trend Analysis**: Analyze performance trends using rolling windows, detect seasonal patterns, and identify trend changes
- **Comparative Analytics Dashboard**: Compare farmer performance against regional benchmarks, peer farmers, and historical performance
- **Comprehensive Reporting**: Generate executive summaries with key insights, strengths, and improvement opportunities
- **Predictive Analytics**: Generate trend predictions and identify performance drivers

## API Endpoints

### Price Floors
- `POST /price-floors` - Set a new price floor
- `GET /price-floors/{farmer_id}` - Get all price floors for a farmer
- `DELETE /price-floors/{floor_id}` - Deactivate a price floor

### Benchmarks
- `POST /benchmarks/create` - Create benchmark from conversation data
- `GET /benchmarks/{farmer_id}` - Get farmer's benchmarks
- `POST /benchmarks/{benchmark_id}/update` - Update existing benchmark

### Performance Tracking
- `POST /performance/track` - Track a new performance record
- `GET /performance/{farmer_id}` - Get performance history

### Conversation Recording
- `POST /conversations/record` - Record conversation for future analysis

### Analytics
- `GET /analytics/{farmer_id}` - Get comprehensive farmer analytics

### Performance Analytics ⭐ NEW
- `GET /analytics/{farmer_id}/income-improvement` - Get income improvement analysis
- `GET /analytics/{farmer_id}/performance-trends` - Get performance trends analysis  
- `GET /analytics/{farmer_id}/comparative-dashboard` - Get comparative analytics dashboard
- `GET /analytics/{farmer_id}/comprehensive` - Get comprehensive performance analytics report

## Data Models

### Core Models
- **PriceFloor**: Minimum acceptable price settings
- **FarmerBenchmark**: Historical price benchmarks
- **PerformanceMetric**: Performance tracking records
- **ConversationRecord**: Recorded conversation data
- **BenchmarkAnalysis**: Comprehensive benchmark analysis

### Request Models
- **PriceFloorRequest**: Request to set price floor
- **BenchmarkRequest**: Request to create benchmark
- **PerformanceTrackingRequest**: Request to track performance

## Key Components

### BenchmarkEngine
- Manages price floors and benchmarks
- Provides comprehensive analytics
- Handles benchmark updates and deactivation

### PerformanceTracker
- Tracks performance against benchmarks and floors
- Calculates performance scores and categories
- Analyzes performance trends and patterns

### HistoricalAnalyzer
- Analyzes conversation history to create benchmarks
- Records new conversations for future analysis
- Calculates confidence scores and quality metrics

### PerformanceAnalytics ⭐ NEW
- Calculates income improvement over time
- Analyzes performance trends with rolling windows
- Generates comparative analytics against benchmarks and peers
- Provides comprehensive performance reporting
- Identifies performance drivers and improvement opportunities

## Performance Scoring Algorithm

The performance scoring system uses a weighted approach:

1. **Base Score**: 50 points
2. **Benchmark Performance**: 
   - +30 points for 20%+ above benchmark
   - +20 points for 10%+ above benchmark
   - +10 points for at/above benchmark
   - +5 points for within 10% of benchmark
   - -10 points for below 90% of benchmark
3. **Price Floor Performance**:
   - +20 points for above floor
   - -30 points for below floor (major penalty)

Final score is clamped between 0-100.

## Confidence Scoring

Benchmark confidence is calculated using multiple factors:

- **Data Volume** (30%): More data points increase confidence
- **Individual Confidence** (30%): Average confidence of price points
- **Price Consistency** (20%): Lower volatility increases confidence
- **Recency** (10%): Recent data points increase confidence
- **Location Diversity** (10%): Multiple locations increase confidence

## Installation and Setup

### Prerequisites
- Python 3.11+
- FastAPI
- Pydantic
- Structlog

### Installation
```bash
pip install -r requirements.txt
```

### Running the Service
```bash
uvicorn main:app --host 0.0.0.0 --port 8009
```

### Docker
```bash
docker build -t benchmarking-service .
docker run -p 8009:8009 benchmarking-service
```

## Testing

Run the comprehensive test suite:
```bash
pytest test_benchmarking_system.py -v
```

The test suite includes:
- Unit tests for all core components
- Integration tests for complete workflows
- Model validation tests
- Performance calculation tests

## Configuration

The service can be configured through environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `MONGODB_URL`: MongoDB connection string
- `REDIS_URL`: Redis connection string
- `INFLUXDB_URL`: InfluxDB connection string

## Integration with Other Services

### Ambient AI Service
- Receives processed conversation data
- Records conversations for benchmark creation

### Price Discovery Service
- Uses market data for benchmark validation
- Provides regional price context

### User Management Service
- Validates farmer identities
- Manages user preferences

## Analytics and Insights

The service provides comprehensive analytics including:

### Summary Analytics
- Total benchmarks and price floors
- Performance distribution
- Benchmark adherence rates
- Floor violation counts

### Trend Analysis
- Performance improvement over time
- Price trend analysis
- Seasonal pattern detection
- Consistency metrics

### Recommendations
- Benchmark creation suggestions
- Price floor optimization
- Performance improvement strategies
- Market timing recommendations

## API Documentation

When running the service, visit `http://localhost:8009/docs` for interactive API documentation powered by FastAPI's automatic OpenAPI generation.

## Requirements Validation

This service implements the following requirements:

- **Requirement 8.1**: ✅ Personalized minimum selling price floors
- **Requirement 8.2**: ✅ Historical price benchmarks from conversations
- **Requirement 8.3**: ✅ Performance tracking against benchmarks
- **Requirement 8.5**: ✅ Performance analytics showing income improvement over time ⭐ NEW

The implementation provides farmers with powerful tools to:
1. Set and manage minimum acceptable prices
2. Learn from their historical pricing conversations
3. Track and improve their selling performance over time
4. **Analyze income improvements and performance trends** ⭐ NEW
5. **Compare performance against regional and peer benchmarks** ⭐ NEW
6. **Receive comprehensive performance insights and recommendations** ⭐ NEW
7. Make data-driven pricing decisions

## Future Enhancements

Potential future improvements:
- Machine learning-based price prediction
- Advanced seasonal pattern recognition
- Integration with weather and crop yield data
- Mobile app notifications for price opportunities
- Collaborative benchmarking with farmer groups