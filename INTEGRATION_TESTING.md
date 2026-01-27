# MANDI EAR™ Integration Testing Guide

This document describes the comprehensive integration testing system for the MANDI EAR agricultural intelligence platform.

## Overview

The integration testing system validates:
- Complete user journeys from voice input to recommendations
- Data consistency across all microservices
- System performance under various load conditions
- End-to-end data flows and service connectivity
- Error handling and system resilience

## Test Structure

### 1. Integration Workflow Tests (`test_integration_workflows.py`)

Tests complete user journeys and data consistency:

- **Voice-to-Price Discovery Journey**: Voice query → Transcription → Price discovery → Voice response
- **Ambient AI to Negotiation Journey**: Ambient AI extraction → Market analysis → Negotiation guidance
- **Crop Planning to Market Analysis Journey**: Crop planning → Market analysis → Income projections
- **Data Consistency Tests**: Price data, user data, and MSP data consistency across services
- **System Performance Tests**: Concurrent requests, health monitoring, data flow validation
- **Error Handling Tests**: Invalid requests, authentication errors, rate limiting

### 2. Performance Load Tests (`test_performance_load.py`)

Tests system performance under load:

- **Single User Performance**: Response times and success rates for individual users
- **Concurrent Users Performance**: System behavior with multiple simultaneous users
- **Stress Testing**: High-load scenarios to test system limits
- **Resource Utilization**: Memory usage stability and connection handling

### 3. Test Runner (`run_integration_tests.py`)

Comprehensive test execution and reporting:

- Automated test suite execution
- System health checks before testing
- Detailed reporting with JSON output
- Performance metrics collection
- Test result summarization

## Running Tests

### Prerequisites

1. **System Running**: Ensure all services are running:
   ```bash
   make start
   ```

2. **System Health**: Verify system health:
   ```bash
   make health-detailed
   ```

### Test Execution Commands

#### Basic Integration Tests
```bash
# Run integration tests with verbose output
make test-integration

# Or directly with Python
python run_integration_tests.py -v
```

#### Full Integration Tests (Including Performance)
```bash
# Run all integration tests including performance and slow tests
make test-integration-full

# Or directly with Python
python run_integration_tests.py -v --performance --slow
```

#### Performance Tests Only
```bash
# Run performance tests only
make test-performance

# Or directly with pytest
python -m pytest tests/test_performance_load.py -v
```

#### All Tests
```bash
# Run all tests (unit, property, integration)
make test-all
```

#### Data Flow Validation
```bash
# Validate end-to-end data flows
make validate-flows
```

### Test Options

The test runner supports various options:

```bash
python run_integration_tests.py [OPTIONS]

Options:
  -v, --verbose         Verbose output
  --slow               Include slow tests
  --performance        Include performance tests
  --report FILE        Save detailed report to JSON file
  --health-check       Only run health check
```

### Examples

```bash
# Run tests with detailed reporting
python run_integration_tests.py -v --report integration_report.json

# Run only health check
python run_integration_tests.py --health-check

# Run performance tests with slow tests included
python run_integration_tests.py -v --performance --slow
```

## Test Configuration

### Environment Variables

Tests use the following configuration:

- `API_GATEWAY_URL`: Default `http://localhost:8000`
- `TEST_USER_ID`: Test user identifier
- `TEST_PHONE`: Test phone number for authentication
- `TEST_PASSWORD`: Test password

### Test Data

Tests use mock data and test users:
- Phone numbers: `+9187654321XX` (where XX is user ID)
- Password: `load_test_pass` for load tests, `integration_test_pass` for integration tests
- Mock audio data and location coordinates for testing

## Performance Benchmarks

### Expected Performance Metrics

#### Single User Performance
- **Success Rate**: ≥ 95%
- **Mean Response Time**: ≤ 2000ms
- **95th Percentile**: ≤ 5000ms

#### Concurrent Users (10 users)
- **Success Rate**: ≥ 90%
- **Mean Response Time**: ≤ 3000ms
- **95th Percentile**: ≤ 8000ms
- **Throughput**: ≥ 1.0 requests/second

#### Stress Test (25 users)
- **Success Rate**: ≥ 70%
- **System Stability**: No crashes or unrecoverable errors

#### Health Endpoint
- **Success Rate**: ≥ 96% (48/50 requests)
- **Mean Response Time**: ≤ 500ms
- **Max Response Time**: ≤ 2000ms

## Test Reports

### Console Output

Tests provide real-time console output with:
- Test execution progress
- Success/failure indicators
- Performance metrics
- Error details (in verbose mode)

### JSON Reports

Detailed JSON reports include:
- Test execution summary
- Individual test results
- Performance metrics
- Error details and stack traces
- Timing information

Example report structure:
```json
{
  "timestamp": "2024-01-27 10:30:00",
  "duration_seconds": 120.5,
  "summary": {
    "total_suites": 2,
    "passed_suites": 2,
    "failed_suites": 0
  },
  "suites": {
    "Integration Workflows": {
      "status": "passed",
      "total_tests": 15,
      "passed_tests": 15,
      "failed_tests": 0,
      "duration": 45.2
    }
  }
}
```

## Troubleshooting

### Common Issues

#### 1. System Not Responding
```bash
# Check if services are running
docker-compose ps

# Check service logs
make logs

# Restart services
make stop && make start
```

#### 2. Authentication Failures
- Ensure user management service is running
- Check database connectivity
- Verify test user creation in logs

#### 3. Performance Test Failures
- Check system resources (CPU, memory)
- Verify network connectivity
- Reduce concurrent user count for resource-constrained environments

#### 4. Timeout Errors
- Increase timeout values in test configuration
- Check service response times individually
- Verify database performance

### Debug Mode

Run tests with maximum verbosity:
```bash
python run_integration_tests.py -v --report debug_report.json
```

Check individual service health:
```bash
curl http://localhost:8000/health/services/{service_name}
```

## Continuous Integration

### CI/CD Integration

Add to your CI pipeline:

```yaml
# Example GitHub Actions step
- name: Run Integration Tests
  run: |
    make start
    sleep 30  # Wait for services to start
    make test-integration
    make stop
```

### Test Scheduling

For continuous monitoring:
```bash
# Run tests every hour
0 * * * * cd /path/to/mandi-ear && python run_integration_tests.py --report hourly_report.json
```

## Extending Tests

### Adding New Test Cases

1. **Integration Tests**: Add to `test_integration_workflows.py`
2. **Performance Tests**: Add to `test_performance_load.py`
3. **New Test Suites**: Create new files and update `run_integration_tests.py`

### Test Patterns

Follow these patterns when adding tests:

```python
@pytest.mark.asyncio
async def test_new_workflow(test_client):
    """Test description"""
    # Step 1: Setup
    # Step 2: Execute workflow
    # Step 3: Verify results
    # Step 4: Assert expectations
```

### Performance Test Patterns

```python
@pytest.mark.asyncio
@pytest.mark.slow
async def test_new_performance_scenario(self):
    """Performance test description"""
    # Setup metrics collection
    # Execute load scenario
    # Analyze results
    # Assert performance criteria
```

## Monitoring and Alerting

### Health Monitoring

The system provides continuous health monitoring:
- Service availability checks every 30 seconds
- Response time tracking
- Error rate monitoring
- Uptime percentage calculation

### Alerting Thresholds

Configure alerts for:
- Service downtime > 5 minutes
- Response time > 5 seconds (95th percentile)
- Error rate > 10%
- System-wide health < 80%

## Best Practices

1. **Run tests regularly** to catch regressions early
2. **Monitor performance trends** over time
3. **Update test data** to reflect real-world scenarios
4. **Review failed tests** immediately
5. **Maintain test environment** separate from production
6. **Document test results** for compliance and analysis
7. **Scale test load** based on expected production traffic

## Support

For issues with integration testing:
1. Check service logs: `make logs`
2. Verify system health: `make health-detailed`
3. Run diagnostic flows: `make validate-flows`
4. Review test reports for detailed error information
5. Check individual service endpoints manually