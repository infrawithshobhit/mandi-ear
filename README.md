# MANDI EAR™ - Agricultural Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Property%20Based-brightgreen.svg)](tests/)

## 🌾 Overview

MANDI EAR™ is India's first ambient AI-powered, farmer-first, multilingual agricultural intelligence platform designed to empower farmers and vendors with real-time market insights, price discovery, and AI-powered negotiation assistance. The platform leverages ambient AI technology to extract market intelligence from conversations and provides multilingual support for India's diverse agricultural community.

## ✨ Key Features

### 🎯 Core Capabilities
- **🎤 Voice Processing**: Multilingual transcription and synthesis in 50+ Indian languages
- **💰 Price Discovery**: Real-time market prices from mandis across all Indian states
- **🤝 Negotiation Assistant**: AI-powered negotiation strategies with market analysis
- **🌱 Crop Planning**: Intelligent crop recommendations based on weather, soil, and market trends
- **📊 MSP Monitoring**: Continuous monitoring of Minimum Support Prices with alerts
- **🌐 Cross-Mandi Network**: National network of mandi data with transportation costs
- **🥬 Comprehensive Commodities**: Support for grains, vegetables, and cash crops

### 🌐 Enhanced User Experience
- **🌍 Multi-Language Support**: 12+ Indian languages with real-time UI translation
- **📍 Location-Based Pricing**: Different prices for 6+ major mandis
- **🥕 Commodity Filtering**: Filter by grains, top 8 vegetables, or cash crops
- **📱 Mobile Responsive**: Works perfectly on all devices
- **🔔 Smart Notifications**: Real-time feedback with professional notifications
- **🧪 Interactive Testing**: Test all features directly from the web interface

## 🚀 **QUICK START - No Docker Required!**

### **🎯 One-Click Setup (Recommended)**

#### **Requirements:**
- **Python 3.7+** (usually pre-installed on most systems)
- **Internet connection** (for initial dependency download only)
- **Web browser** (Chrome, Firefox, Safari, Edge)

#### **Step 1: Download & Run**
```bash
# Navigate to project directory
cd mandi-ear

# Option 1: Double-click to run (Windows)
start_mandi_ear.bat

# Option 2: Command line (All platforms)
python standalone_mandi_ear.py
```

#### **Step 2: Access the Platform**
Open your web browser and visit: **http://localhost:8001**

### **🌟 What You'll See:**

#### **Main Features Available:**
1. **🌍 Language Selector** - Switch between 12+ Indian languages
2. **📍 Location Selector** - Choose from 6 different mandis
3. **🥬 Commodity Selector** - Filter by grains, vegetables, or cash crops
4. **💰 Live Price Updates** - Real-time market prices with trends
5. **🧪 Interactive API Testing** - Test all features with one click

#### **Supported Commodities:**
- **🌾 Grains & Cereals**: Wheat, Rice, Corn
- **🥬 Top 8 Vegetables**: Tomato, Onion, Potato, Cabbage, Cauliflower, Carrot, Green Beans, Bell Pepper
- **💰 Cash Crops**: Cotton, Sugarcane

#### **Available Locations:**
- 🏛️ Delhi Mandi
- 🏢 Gurgaon Mandi (Haryana)
- 🏭 Faridabad Mandi (Haryana)
- 🌾 Meerut Mandi (UP)
- 🚜 Panipat Mandi (Haryana)

### **🧪 Testing All Features:**

#### **1. Feature Testing Buttons:**
- **🎤 Voice Processing** - Test multilingual voice transcription
- **💰 Price Discovery** - Get real-time wheat prices
- **🤝 Negotiation Assistant** - AI-powered market analysis
- **🌱 Crop Planning** - Intelligent crop recommendations
- **📊 MSP Monitoring** - Government price compliance
- **🌐 Cross-Mandi Network** - Multi-location mandi data

#### **2. System Testing:**
- **🚀 Run All Tests** - Comprehensive system testing
- **⚡ Quick Test** - System functionality check
- **🏥 Health Check** - Server status verification
- **🔄 Refresh Prices** - Update market prices

### **🌐 API Endpoints Available:**

| Feature | URL | Description |
|---------|-----|-------------|
| **Main Interface** | http://localhost:8001 | Beautiful web interface with all features |
| **API Documentation** | http://localhost:8001/docs | Interactive Swagger UI for API testing |
| **Health Check** | http://localhost:8001/health | System status and service health |
| **Current Prices** | http://localhost:8001/api/v1/prices/current | Live market prices for all commodities |
| **Voice Processing** | http://localhost:8001/api/v1/voice/transcribe | Multilingual voice transcription |
| **Negotiation Analysis** | http://localhost:8001/api/v1/negotiation/analyze | AI-powered negotiation strategies |
| **Crop Planning** | http://localhost:8001/api/v1/crop-planning/recommend | Intelligent crop recommendations |
| **MSP Rates** | http://localhost:8001/api/v1/msp/rates | Government minimum support prices |
| **Mandi List** | http://localhost:8001/api/v1/mandis | Available mandis and locations |

## 🔧 **Advanced Setup (Docker)**

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

3. **Start services with Docker**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   ```bash
   # API Gateway: http://localhost:8080
   # Individual services: http://localhost:8081-8092
   ```

## 🚨 **Troubleshooting**

### **Common Issues & Solutions:**

#### **1. Python not found?**
- **Windows**: Install Python from https://python.org/downloads
- **Mac**: Use Homebrew: `brew install python3`
- **Linux**: Use package manager: `sudo apt install python3`
- **Make sure "Add to PATH" is checked during installation**

#### **2. Permission errors?**
- **Windows**: Run as Administrator
- **Mac/Linux**: Use `sudo python standalone_mandi_ear.py`

#### **3. Port 8001 in use?**
- Check what's using the port: `netstat -ano | findstr :8001`
- Kill the process or change port in `standalone_mandi_ear.py`

#### **4. Dependencies not installing?**
- Ensure internet connection is stable
- Try manual installation: `pip install fastapi uvicorn`
- Use virtual environment: `python -m venv venv && source venv/bin/activate`

#### **5. Browser can't connect?**
- Ensure server is running (check console output)
- Try different browser or incognito mode
- Clear browser cache (Ctrl+F5)
- Check firewall settings

### **🎯 Success Indicators:**

When everything works correctly, you should see:

1. ✅ **Console Output**: 
   ```
   🌾 Starting MANDI EAR™ Agricultural Intelligence Platform...
   📦 All dependencies resolved automatically!
   🚀 Server starting on http://localhost:8001
   ✅ MANDI EAR™ is ready to serve farmers across India!
   ```

2. ✅ **Web Interface**: Beautiful homepage with all features working
3. ✅ **API Responses**: JSON data from all test buttons
4. ✅ **Interactive Features**: Language selector, location selector, commodity filtering

## 🏗️ Architecture

The platform follows a microservices architecture with the following components:

```
mandi-ear/
├── standalone_mandi_ear.py         # 🚀 Self-contained version (RECOMMENDED)
├── start_mandi_ear.bat            # 🖱️ One-click startup script
├── QUICK_START.md                 # 📖 Quick setup guide
├── services/                      # 🏗️ Microservices architecture
│   ├── ambient-ai-service/        # AI conversation analysis
│   ├── voice-processing-service/  # Multilingual voice interface
│   ├── price-discovery-service/   # Market price intelligence
│   ├── negotiation-intelligence-service/ # AI negotiation assistance
│   ├── crop-planning-service/     # Agricultural planning
│   ├── msp-enforcement-service/   # MSP monitoring
│   ├── anti-hoarding-service/     # Market manipulation detection
│   ├── benchmarking-service/      # Performance analytics
│   ├── notification-service/      # Alert system
│   ├── accessibility-service/     # Accessibility features
│   ├── offline-cache-service/     # Offline functionality
│   ├── user-management-service/   # User authentication
│   └── api-gateway/               # Unified API gateway
├── tests/                         # Property-based tests
├── scripts/                       # Deployment scripts
└── .kiro/specs/                   # Project specifications
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