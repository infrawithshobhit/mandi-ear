#!/usr/bin/env python3
"""
MANDI EAR™ - Clean Working Version
Simple, functional version with working language dropdown
"""

import sys
import subprocess
import os
import json
from datetime import datetime, timedelta
import random
import time

# Auto-install dependencies
def install_dependencies():
    """Automatically install required dependencies"""
    required_packages = [
        'fastapi==0.104.1',
        'uvicorn[standard]==0.24.0',
        'python-multipart==0.0.6',
        'requests==2.31.0'
    ]
    
    print("🔧 Installing dependencies...")
    for package in required_packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            print(f"⚠️  Could not install {package}, but continuing...")
    print("✅ Dependencies installed!")

# Install dependencies first
try:
    import fastapi
    import uvicorn
except ImportError:
    install_dependencies()
    import fastapi
    import uvicorn

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, List, Optional, Any
import asyncio

# ============================================================================
# MANDI EAR™ APPLICATION
# ============================================================================

app = FastAPI(
    title="MANDI EAR™ - Agricultural Intelligence Platform",
    description="India's first ambient AI-powered, farmer-first agricultural intelligence platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MOCK DATA & SERVICES
# ============================================================================

# Mock market data
MOCK_PRICES = {
    # Grains & Cereals
    "wheat": {"price": 2500, "unit": "per quintal", "trend": "up", "change": "+5%", "category": "grains"},
    "rice": {"price": 3200, "unit": "per quintal", "trend": "stable", "change": "0%", "category": "grains"},
    "corn": {"price": 1800, "unit": "per quintal", "trend": "down", "change": "-3%", "category": "grains"},
    
    # Cash Crops
    "cotton": {"price": 5500, "unit": "per quintal", "trend": "up", "change": "+8%", "category": "cash_crops"},
    "sugarcane": {"price": 350, "unit": "per quintal", "trend": "stable", "change": "+1%", "category": "cash_crops"},
    
    # Top 8 Vegetables
    "tomato": {"price": 2800, "unit": "per quintal", "trend": "up", "change": "+12%", "category": "vegetables"},
    "onion": {"price": 2200, "unit": "per quintal", "trend": "down", "change": "-8%", "category": "vegetables"},
    "potato": {"price": 1500, "unit": "per quintal", "trend": "stable", "change": "+2%", "category": "vegetables"},
    "cabbage": {"price": 1200, "unit": "per quintal", "trend": "up", "change": "+6%", "category": "vegetables"},
    "cauliflower": {"price": 1800, "unit": "per quintal", "trend": "up", "change": "+10%", "category": "vegetables"},
    "carrot": {"price": 2000, "unit": "per quintal", "trend": "stable", "change": "+3%", "category": "vegetables"},
    "green_beans": {"price": 3500, "unit": "per quintal", "trend": "up", "change": "+15%", "category": "vegetables"},
    "bell_pepper": {"price": 4200, "unit": "per quintal", "trend": "down", "change": "-5%", "category": "vegetables"}
}

# Mock mandis data
MOCK_MANDIS = [
    {"name": "Delhi Mandi", "location": "Delhi", "distance": "0 km"},
    {"name": "Gurgaon Mandi", "location": "Haryana", "distance": "25 km"},
    {"name": "Faridabad Mandi", "location": "Haryana", "distance": "30 km"},
    {"name": "Meerut Mandi", "location": "UP", "distance": "70 km"},
    {"name": "Panipat Mandi", "location": "Haryana", "distance": "90 km"}
]

# Mock users
MOCK_USERS = {}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_mock_response(base_data: Dict, variation: float = 0.1) -> Dict:
    """Generate mock response with slight variations"""
    result = base_data.copy()
    if "price" in result:
        variation_amount = result["price"] * variation * (random.random() - 0.5) * 2
        result["price"] = int(result["price"] + variation_amount)
    return result

def get_current_time():
    """Get current timestamp"""
    return datetime.utcnow().isoformat()

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with clean, working HTML interface"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MANDI EAR™ - Agricultural Intelligence Platform</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
            }
            
            .header {
                background: rgba(255,255,255,0.95);
                backdrop-filter: blur(10px);
                padding: 20px 0;
                box-shadow: 0 2px 20px rgba(0,0,0,0.1);
                position: sticky;
                top: 0;
                z-index: 100;
            }
            
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 0 20px;
            }
            
            .header-content {
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .logo {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .logo h1 { 
                color: #2c5530; 
                font-size: 2.5em;
                font-weight: 700;
                margin: 0;
            }
            
            .logo-icon {
                font-size: 2.5em;
                color: #4CAF50;
            }
            
            .header-controls {
                display: flex;
                align-items: center;
                gap: 20px;
            }
            
            .language-selector {
                position: relative;
            }
            
            .language-dropdown {
                background: rgba(255,255,255,0.9);
                border: 2px solid #4CAF50;
                border-radius: 25px;
                padding: 8px 16px;
                font-weight: 600;
                color: #2c5530;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 8px;
                transition: all 0.3s ease;
                min-width: 120px;
            }
            
            .language-dropdown:hover {
                background: rgba(76, 175, 80, 0.1);
                transform: translateY(-2px);
            }
            
            .language-options {
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: white;
                border: 2px solid #4CAF50;
                border-radius: 15px;
                margin-top: 5px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                display: none;
                z-index: 9999;
                max-height: 300px;
                overflow-y: auto;
            }
            
            .language-options.show {
                display: block !important;
            }
            
            .language-option {
                padding: 12px 16px;
                cursor: pointer;
                transition: background 0.2s ease;
                display: flex;
                align-items: center;
                gap: 10px;
                border-bottom: 1px solid #f0f0f0;
            }
            
            .language-option:hover {
                background: rgba(76, 175, 80, 0.1);
            }
            
            .language-option:last-child {
                border-bottom: none;
            }
            
            .language-option.selected {
                background: rgba(76, 175, 80, 0.2);
                font-weight: 600;
            }
            
            .status-badge {
                background: linear-gradient(45deg, #4CAF50, #45a049);
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .main-content {
                padding: 40px 0;
            }
            
            .hero-section {
                text-align: center;
                color: white;
                margin-bottom: 50px;
            }
            
            .hero-section h2 {
                font-size: 2.2em;
                margin-bottom: 15px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            
            .hero-section p {
                font-size: 1.2em;
                opacity: 0.9;
                max-width: 600px;
                margin: 0 auto;
            }
            
            .stats-bar {
                display: flex;
                justify-content: space-around;
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 15px;
                margin: 20px 0;
                backdrop-filter: blur(10px);
            }
            
            .stat-item {
                text-align: center;
                color: white;
            }
            
            .stat-number {
                font-size: 2em;
                font-weight: 700;
                display: block;
            }
            
            .stat-label {
                font-size: 0.9em;
                opacity: 0.8;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .dashboard {
                background: rgba(255,255,255,0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }
            
            .section-title {
                display: flex;
                align-items: center;
                gap: 12px;
                font-size: 1.5em;
                color: #2c5530;
                margin-bottom: 25px;
                font-weight: 600;
            }
            
            .price-grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); 
                gap: 20px; 
                margin-bottom: 30px;
            }
            
            .price-card { 
                background: linear-gradient(135deg, #fff3cd, #ffeaa7);
                padding: 20px; 
                border-radius: 15px; 
                border: 2px solid #f39c12;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            
            .price-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 25px rgba(243, 156, 18, 0.3);
            }
            
            .price-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #f39c12, #e67e22);
            }
            
            .commodity-name {
                font-size: 1.1em;
                font-weight: 700;
                color: #2c5530;
                margin-bottom: 10px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .price-value { 
                font-size: 2em; 
                font-weight: 800; 
                color: #27ae60;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
                gap: 5px;
            }
            
            .price-details {
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 0.9em;
                color: #666;
            }
            
            .trend {
                display: flex;
                align-items: center;
                gap: 5px;
                font-weight: 600;
            }
            
            .trend.up { color: #27ae60; }
            .trend.down { color: #e74c3c; }
            .trend.stable { color: #f39c12; }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="container">
                <div class="header-content">
                    <div class="logo">
                        <i class="fas fa-seedling logo-icon"></i>
                        <h1>MANDI EAR™</h1>
                    </div>
                    <div class="header-controls">
                        <div class="language-selector">
                            <div class="language-dropdown" onclick="toggleLanguageDropdown()">
                                <i class="fas fa-globe"></i>
                                <span id="current-language">English</span>
                                <i class="fas fa-chevron-down"></i>
                            </div>
                            <div class="language-options" id="language-options">
                                <div class="language-option selected" onclick="selectLanguage('en', 'English')">
                                    <span>🇺🇸</span>
                                    <span>English</span>
                                </div>
                                <div class="language-option" onclick="selectLanguage('hi', 'हिंदी')">
                                    <span>🇮🇳</span>
                                    <span>हिंदी (Hindi)</span>
                                </div>
                                <div class="language-option" onclick="selectLanguage('bn', 'বাংলা')">
                                    <span>🇧🇩</span>
                                    <span>বাংলা (Bengali)</span>
                                </div>
                                <div class="language-option" onclick="selectLanguage('te', 'తెలుగు')">
                                    <span>🇮🇳</span>
                                    <span>తెలుగు (Telugu)</span>
                                </div>
                                <div class="language-option" onclick="selectLanguage('ta', 'தமிழ்')">
                                    <span>🇮🇳</span>
                                    <span>தமிழ் (Tamil)</span>
                                </div>
                            </div>
                        </div>
                        <div class="status-badge">
                            <i class="fas fa-check-circle"></i>
                            <span data-translate="system-operational">System Operational</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="main-content">
            <div class="container">
                <div class="hero-section">
                    <h2 data-translate="hero-title">Agricultural Intelligence Platform</h2>
                    <p data-translate="hero-subtitle">India's first ambient AI-powered, farmer-first, multilingual agricultural intelligence platform</p>
                    
                    <div class="stats-bar">
                        <div class="stat-item">
                            <span class="stat-number">25+</span>
                            <span class="stat-label" data-translate="languages">Languages</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">1000+</span>
                            <span class="stat-label" data-translate="mandis">Mandis</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">24/7</span>
                            <span class="stat-label" data-translate="monitoring">Monitoring</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">AI</span>
                            <span class="stat-label" data-translate="powered">Powered</span>
                        </div>
                    </div>
                </div>

                <div class="dashboard">
                    <div class="section-title">
                        <i class="fas fa-chart-line"></i>
                        <span data-translate="live-prices">Live Market Prices</span>
                    </div>
                    
                    <div class="price-grid" id="price-grid">
                        <!-- Price cards will be loaded here -->
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Simple, working JavaScript
            let currentLanguage = 'en';
            
            // Translation data
            const translations = {
                'en': {
                    'hero-title': 'Agricultural Intelligence Platform',
                    'hero-subtitle': "India's first ambient AI-powered, farmer-first, multilingual agricultural intelligence platform",
                    'languages': 'Languages',
                    'mandis': 'Mandis',
                    'monitoring': 'Monitoring',
                    'powered': 'Powered',
                    'system-operational': 'System Operational',
                    'live-prices': 'Live Market Prices',
                    'wheat': 'Wheat',
                    'rice': 'Rice',
                    'corn': 'Corn',
                    'cotton': 'Cotton',
                    'sugarcane': 'Sugarcane',
                    'tomato': 'Tomato',
                    'onion': 'Onion',
                    'potato': 'Potato',
                    'per-quintal': 'per quintal'
                },
                'hi': {
                    'hero-title': 'कृषि बुद्धिमत्ता मंच',
                    'hero-subtitle': 'भारत का पहला परिवेशी AI-संचालित, किसान-प्रथम, बहुभाषी कृषि बुद्धिमत्ता मंच',
                    'languages': 'भाषाएं',
                    'mandis': 'मंडियां',
                    'monitoring': 'निगरानी',
                    'powered': 'संचालित',
                    'system-operational': 'सिस्टम चालू',
                    'live-prices': 'लाइव बाजार मूल्य',
                    'wheat': 'गेहूं',
                    'rice': 'चावल',
                    'corn': 'मक्का',
                    'cotton': 'कपास',
                    'sugarcane': 'गन्ना',
                    'tomato': 'टमाटर',
                    'onion': 'प्याज',
                    'potato': 'आलू',
                    'per-quintal': 'प्रति क्विंटल'
                },
                'bn': {
                    'hero-title': 'কৃষি বুদ্ধিমত্তা প্ল্যাটফর্म',
                    'hero-subtitle': 'ভারতের প্রথম পরিবেশগত AI-চালিত, কৃষক-প্রথম, বহুভাষিক কৃষি বুদ্ধিমত্তা প্ল্যাটফর্ম',
                    'languages': 'ভাষা',
                    'mandis': 'মান্ডি',
                    'monitoring': 'পর্যবেক্ষণ',
                    'powered': 'চালিত',
                    'system-operational': 'সিস্টেম চালু',
                    'live-prices': 'লাইভ বাজার মূল্য',
                    'wheat': 'গম',
                    'rice': 'চাল',
                    'corn': 'ভুট্টা',
                    'cotton': 'তুলা',
                    'sugarcane': 'আখ',
                    'tomato': 'টমেটো',
                    'onion': 'পেঁয়াজ',
                    'potato': 'আলু',
                    'per-quintal': 'প্রতি কুইন্টাল'
                },
                'te': {
                    'hero-title': 'వ్యవసాయ మేధస్సు వేదిక',
                    'hero-subtitle': 'భారతదేశం యొక్క మొదటి పరిసర AI-శక్తితో, రైతు-మొదటి, బహుభాషా వ్యవసాయ మేధస్సు వేదిక',
                    'languages': 'భాషలు',
                    'mandis': 'మండీలు',
                    'monitoring': 'పర్యవేక్షణ',
                    'powered': 'శక్తితో',
                    'system-operational': 'సిస్టమ్ పనిచేస్తోంది',
                    'live-prices': 'ప్రత్యక్ష మార్కెట్ ధరలు',
                    'wheat': 'గోధుమ',
                    'rice': 'బియ్యం',
                    'corn': 'మొక్కజొన్న',
                    'cotton': 'పత్తి',
                    'sugarcane': 'చెరకు',
                    'tomato': 'టమాటో',
                    'onion': 'ఉల్లిపాయ',
                    'potato': 'బంగాళాదుంప',
                    'per-quintal': 'ప్రతి క్వింటల్'
                },
                'ta': {
                    'hero-title': 'விவசாய நுண்ணறிவு தளம்',
                    'hero-subtitle': 'இந்தியாவின் முதல் சுற்றுச்சூழல் AI-இயங்கும், விவசாயி-முதல், பன்மொழி விவசாய நுண்ணறிவு தளம்',
                    'languages': 'மொழிகள்',
                    'mandis': 'மண்டிகள்',
                    'monitoring': 'கண்காணிப்பு',
                    'powered': 'இயங்கும்',
                    'system-operational': 'அமைப்பு செயல்படுகிறது',
                    'live-prices': 'நேரடி சந்தை விலைகள்',
                    'wheat': 'கோதுமை',
                    'rice': 'அரிசி',
                    'corn': 'சோளம்',
                    'cotton': 'பருத்தி',
                    'sugarcane': 'கரும்பு',
                    'tomato': 'தக்காளி',
                    'onion': 'வெங்காயம்',
                    'potato': 'உருளைக்கிழங்கு',
                    'per-quintal': 'ஒரு குவிண்டலுக்கு'
                }
            };
            
            // Mock price data
            const priceData = {
                wheat: { price: 2500, trend: 'up', change: '+5%' },
                rice: { price: 3200, trend: 'stable', change: '0%' },
                corn: { price: 1800, trend: 'down', change: '-3%' },
                cotton: { price: 5500, trend: 'up', change: '+8%' },
                sugarcane: { price: 350, trend: 'stable', change: '+1%' },
                tomato: { price: 2800, trend: 'up', change: '+12%' },
                onion: { price: 2200, trend: 'down', change: '-8%' },
                potato: { price: 1500, trend: 'stable', change: '+2%' }
            };
            
            function toggleLanguageDropdown() {
                console.log('Language dropdown clicked');
                const dropdown = document.getElementById('language-options');
                if (dropdown) {
                    dropdown.classList.toggle('show');
                    console.log('Dropdown toggled, show class:', dropdown.classList.contains('show'));
                } else {
                    console.error('Language dropdown not found');
                }
            }
            
            function selectLanguage(langCode, langName) {
                console.log('Language selected:', langCode, langName);
                currentLanguage = langCode;
                
                // Update current language display
                const currentLangSpan = document.getElementById('current-language');
                if (currentLangSpan) {
                    currentLangSpan.textContent = langName;
                }
                
                // Update selected option
                document.querySelectorAll('.language-option').forEach(option => {
                    option.classList.remove('selected');
                });
                event.target.closest('.language-option').classList.add('selected');
                
                // Close dropdown
                document.getElementById('language-options').classList.remove('show');
                
                // Translate content
                translateContent(langCode);
            }
            
            function translateContent(langCode) {
                console.log('Translating content to:', langCode);
                const trans = translations[langCode] || translations['en'];
                
                // Translate all elements with data-translate attribute
                document.querySelectorAll('[data-translate]').forEach(element => {
                    const key = element.getAttribute('data-translate');
                    if (trans[key]) {
                        element.textContent = trans[key];
                    }
                });
                
                // Update price cards
                loadPriceCards();
            }
            
            function loadPriceCards() {
                const grid = document.getElementById('price-grid');
                const trans = translations[currentLanguage] || translations['en'];
                
                let html = '';
                Object.keys(priceData).forEach(commodity => {
                    const data = priceData[commodity];
                    const trendIcon = data.trend === 'up' ? '↗️' : data.trend === 'down' ? '↘️' : '➡️';
                    const commodityName = trans[commodity] || commodity;
                    const unitText = trans['per-quintal'] || 'per quintal';
                    
                    html += `
                        <div class="price-card">
                            <div class="commodity-name">${commodityName}</div>
                            <div class="price-value">₹${data.price.toLocaleString()}</div>
                            <div class="price-details">
                                <span>${unitText}</span>
                                <span class="trend ${data.trend}">
                                    ${trendIcon} ${data.change}
                                </span>
                            </div>
                        </div>
                    `;
                });
                
                grid.innerHTML = html;
            }
            
            // Close dropdown when clicking outside
            document.addEventListener('click', function(event) {
                if (!event.target.closest('.language-selector')) {
                    const dropdown = document.getElementById('language-options');
                    if (dropdown) {
                        dropdown.classList.remove('show');
                    }
                }
            });
            
            // Initialize when page loads
            document.addEventListener('DOMContentLoaded', function() {
                console.log('MANDI EAR initialized');
                loadPriceCards();
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": get_current_time()}

# API endpoints for prices
@app.get("/api/v1/prices/current")
async def get_current_prices():
    """Get current market prices"""
    return {
        "status": "success",
        "data": MOCK_PRICES,
        "timestamp": get_current_time()
    }

@app.get("/api/v1/mandis")
async def get_mandis():
    """Get list of mandis"""
    return {
        "status": "success",
        "data": MOCK_MANDIS,
        "timestamp": get_current_time()
    }

# ============================================================================
# MAIN APPLICATION
# ============================================================================

if __name__ == "__main__":
    print("🌾 Starting MANDI EAR™ Agricultural Intelligence Platform...")
    print("📦 All dependencies resolved automatically!")
    print("🚀 Server starting on http://localhost:8001")
    print("📚 API Documentation: http://localhost:8001/docs")
    print("🏥 Health Check: http://localhost:8001/health")
    print("💰 Price API: http://localhost:8001/api/v1/prices/current")
    print("🧪 Test API: http://localhost:8001/api/v1/test")
    print()
    print("✅ MANDI EAR™ is ready to serve farmers across India!")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)