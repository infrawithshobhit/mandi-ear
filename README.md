# MANDI EAR™ - Agricultural Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Property%20Based-brightgreen.svg)](tests/)

## 🌾 Overview

MANDI EAR™ is a comprehensive agricultural intelligence platform designed to empower farmers and vendors with real-time market insights, price discovery, and AI-powered negotiation assistance. The platform leverages ambient AI technology to extract market intelligence from conversations and provides multilingual support for India's diverse agricultural community.

## ✨ Key Features

### 🎯 Core Capabilities
- **Ambient AI Engine**: Real-time conversation analysis for market intelligence
- **Multilingual Voice Interface**: Support for 50+ Indian languages
- **Price Discovery Network**: Cross-mandi price comparison and analysis
- **AI Negotiation Copilot**: Intelligent negotiation assistance
- **Crop Planning Engine**: Data-driven agricultural planning
- **MSP Enforcement**: Minimum Support Price monitoring and compliance
- **Anti-Hoarding Detection**: Market manipulation prevention

### 🌐 Accessibility & User Experience
- **Screen Reader Support**: Full ARIA compliance for visually impaired users
- **High-Contrast Modes**: Customizable themes for better visibility
- **Voice Navigation**: Hands-free operation with voice commands
- **Keyboard Navigation**: Complete keyboard accessibility
- **Offline Mode**: Essential functionality without internet connectivity
- **Progressive Sync**: Intelligent data synchronization for poor connectivity

### 📱 Platform Features
- **Tutorial System**: Interactive user guidance and onboarding
- **Real-time Alerts**: Customizable price and weather notifications
- **Performance Analytics**: Farmer benchmarking and income tracking
- **Multi-channel Notifications**: SMS, voice, and app notifications

## 🏗️ Architecture

The platform follows a microservices architecture with the following components:

```
mandi-ear/
├── services/
│   ├── ambient-ai-service/          # AI conversation analysis
│   ├── voice-processing-service/    # Multilingual voice interface
│   ├── price-discovery-service/     # Market price intelligence
│   ├── negotiation-intelligence-service/ # AI negotiation assistance
│   ├── crop-planning-service/       # Agricultural planning
│   ├── msp-enforcement-service/     # MSP monitoring
│   ├── anti-hoarding-service/       # Market manipulation detection
│   ├── benchmarking-service/        # Performance analytics
│   ├── notification-service/        # Alert system
│   ├── accessibility-service/       # Accessibility features
│   ├── offline-cache-service/       # Offline functionality
│   ├── user-management-service/     # User authentication
│   └── api-gateway/                 # Unified API gateway
├── tests/                           # Property-based tests
├── scripts/                         # Deployment scripts
└── .kiro/specs/                     # Project specifications
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Docker & Docker Compose
- PostgreSQL, MongoDB, Redis, InfluxDB

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/mandi-ear.git
   cd mandi-ear
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start services with Docker**
   ```bash
   docker-compose up -d
   ```

5. **Initialize databases**
   ```bash
   python scripts/init-db.sql
   ```

6. **Run the application**
   ```bash
   # Development
   ./scripts/start-dev.sh  # Linux/Mac
   ./scripts/start-dev.bat # Windows
   
   # Production
   make start
   ```

## 🧪 Testing

The project uses property-based testing with Hypothesis for comprehensive test coverage:

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/test_ambient_ai_extraction.py

# Run with coverage
pytest --cov=services --cov-report=html

# Run property-based tests only
pytest -m "hypothesis"
```

### Test Categories
- **Property-Based Tests**: Universal correctness properties
- **Unit Tests**: Specific functionality validation
- **Integration Tests**: End-to-end workflows
- **Performance Tests**: Load and stress testing

## 📊 Property-Based Testing

The platform includes 24 comprehensive property-based tests covering:

1. **Ambient AI Extraction Accuracy** - Conversation analysis correctness
2. **Price Aggregation Correctness** - Market price calculations
3. **Data Processing Timeliness** - Real-time processing guarantees
4. **Multilingual Processing Consistency** - Language handling accuracy
5. **Language Detection Fallback** - Robust language detection
6. **Cross-Mandi Data Completeness** - Market data integrity
7. **Data Update Frequency Compliance** - Timely data updates
8. **Negotiation Guidance Completeness** - AI assistance quality
9. **Learning System Improvement** - ML model performance
10. **Crop Planning Comprehensiveness** - Agricultural planning accuracy
11. **Seasonal and Resource Optimization** - Resource management
12. **Continuous Price Monitoring** - MSP compliance tracking
13. **Alternative Suggestion System** - Market alternatives
14. **Compliance Reporting** - Regulatory compliance
15. **Anomaly Detection Accuracy** - Market manipulation detection
16. **Supply-Demand Balance Calculation** - Market analysis
17. **Farmer Benchmarking System** - Performance tracking
18. **Performance Analytics Accuracy** - Analytics correctness
19. **Alert System Customization** - Notification reliability
20. **Cross-Platform Consistency** - Multi-platform compatibility
21. **Offline Mode Functionality** - Offline capabilities
22. **Network Optimization** - Connectivity optimization
23. **User Experience Features** - Accessibility compliance

## 🌍 Multilingual Support

Supported languages include:
- Hindi (हिंदी)
- Tamil (தமிழ்)
- Telugu (తెలుగు)
- Bengali (বাংলা)
- Marathi (मराठी)
- Gujarati (ગુજરાતી)
- Kannada (ಕನ್ನಡ)
- Malayalam (മലയാളം)
- Punjabi (ਪੰਜਾਬੀ)
- Odia (ଓଡ଼ିଆ)
- And 40+ more regional languages

## 🔧 Configuration

### Environment Variables
```bash
# Database Configuration
POSTGRES_URL=postgresql://user:pass@localhost:5432/mandiear
MONGODB_URL=mongodb://localhost:27017/mandiear
REDIS_URL=redis://localhost:6379
INFLUXDB_URL=http://localhost:8086

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# AI Services
OPENAI_API_KEY=your_openai_key
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=your_region

# External APIs
WEATHER_API_KEY=your_weather_api_key
GOVERNMENT_API_KEY=your_gov_api_key
```

### Service Configuration
Each microservice can be configured independently through environment variables and configuration files in their respective directories.

## 📈 Monitoring & Analytics

- **Health Checks**: Automated service health monitoring
- **Performance Metrics**: Real-time performance tracking
- **Error Logging**: Comprehensive error tracking and alerting
- **Usage Analytics**: User behavior and system usage insights

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Indian agricultural community for inspiration and feedback
- Open source contributors and maintainers
- Agricultural research institutions for domain expertise

## 📞 Support

- **Documentation**: [Wiki](https://github.com/yourusername/mandi-ear/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/mandi-ear/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/mandi-ear/discussions)
- **Email**: support@mandiear.com

---

**MANDI EAR™** - Empowering farmers with intelligent market insights 🌾