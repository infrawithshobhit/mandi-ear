# 🌾 MANDI EAR™ - Quick Start Guide

## 🚀 **One-Click Setup** (No Docker Required!)

### **Option 1: Double-Click to Run**
1. **Double-click** `start_mandi_ear.bat`
2. **Wait 30 seconds** for dependencies to install
3. **Open browser**: http://localhost:8001
4. **Done!** 🎉

### **Option 2: Command Line**
```bash
# Navigate to project directory
cd mandi-ear

# Run the standalone version
python standalone_mandi_ear.py
```

## 🌐 **Access the Platform**

Once running, visit these URLs:

| Feature | URL | Description |
|---------|-----|-------------|
| **Main Interface** | http://localhost:8000 | Beautiful web interface |
| **API Documentation** | http://localhost:8000/docs | Interactive API testing |
| **Health Check** | http://localhost:8000/health | System status |
| **Current Prices** | http://localhost:8000/api/v1/prices/current | Live market prices |
| **Test Endpoint** | http://localhost:8000/api/v1/test | Quick functionality test |

## 🧪 **Test the Features**

### **1. Check Current Prices**
```
GET http://localhost:8000/api/v1/prices/current
```

### **2. Get Specific Commodity Price**
```
GET http://localhost:8000/api/v1/prices/current?commodity=wheat
```

### **3. Voice Processing (Mock)**
```
POST http://localhost:8000/api/v1/voice/transcribe
Body: {"audio_data": "mock_audio", "language": "hi"}
```

### **4. Negotiation Analysis**
```
POST http://localhost:8000/api/v1/negotiation/analyze
Body: {"commodity": "wheat", "current_price": 2400, "quantity": 100}
```

### **5. Crop Recommendations**
```
POST http://localhost:8000/api/v1/crop-planning/recommend
Body: {"farm_size": 5.0, "season": "kharif"}
```

## ✅ **What's Included**

- ✅ **Auto-dependency installation** - No manual setup needed
- ✅ **Mock data for all features** - Realistic agricultural data
- ✅ **Interactive web interface** - Beautiful HTML interface
- ✅ **Complete API documentation** - Swagger UI at /docs
- ✅ **All MANDI EAR features** - Voice, prices, negotiation, planning
- ✅ **Cross-platform** - Works on Windows, Mac, Linux
- ✅ **No Docker required** - Pure Python implementation

## 🔧 **Requirements**

- **Python 3.7+** (usually pre-installed on most systems)
- **Internet connection** (for initial dependency download)

## 🚨 **Troubleshooting**

### **Python not found?**
1. Install Python from: https://python.org/downloads
2. Make sure "Add to PATH" is checked during installation

### **Permission errors?**
1. Run as Administrator (Windows)
2. Or use: `sudo python standalone_mandi_ear.py` (Mac/Linux)

### **Port 8000 in use?**
Edit `standalone_mandi_ear.py` and change:
```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # Use port 8001
```

## 🎯 **Success Indicators**

When everything works, you should see:

1. ✅ **Console output**: "MANDI EAR™ is ready to serve farmers"
2. ✅ **Web interface**: Beautiful homepage at http://localhost:8000
3. ✅ **API responses**: JSON data from all endpoints
4. ✅ **Interactive docs**: Working Swagger UI at /docs

## 🌟 **Features Demonstrated**

- **🎤 Voice Processing**: Multilingual transcription and synthesis
- **💰 Price Discovery**: Real-time market prices from multiple mandis
- **🤝 Negotiation Assistant**: AI-powered negotiation strategies
- **🌱 Crop Planning**: Intelligent crop recommendations
- **📊 MSP Monitoring**: Government price compliance checking
- **🏪 Mandi Network**: Cross-mandi price comparison

## 📞 **Support**

If you encounter any issues:
1. Check the console output for error messages
2. Ensure Python 3.7+ is installed
3. Try running as Administrator
4. Check if port 8000 is available

**The system is designed to be completely self-contained and should work out of the box!** 🚀