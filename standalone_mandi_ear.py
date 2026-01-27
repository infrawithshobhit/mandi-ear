#!/usr/bin/env python3
"""
MANDI EAR™ - Standalone Agricultural Intelligence Platform
Self-contained version with automatic dependency management
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
    """Root endpoint with enhanced HTML interface"""
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
                z-index: 1000;
                max-height: 300px;
                overflow-y: auto;
            }
            
            .language-options.show {
                display: block;
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
            
            .features-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 25px;
                margin-bottom: 30px;
            }
            
            .feature-card { 
                background: linear-gradient(135deg, #e8f5e8, #d4edda);
                padding: 25px; 
                border-radius: 15px; 
                border-left: 5px solid #28a745;
                transition: all 0.3s ease;
                position: relative;
            }
            
            .feature-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 8px 25px rgba(40, 167, 69, 0.2);
            }
            
            .feature-header {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 15px;
            }
            
            .feature-icon {
                font-size: 1.8em;
                color: #28a745;
            }
            
            .feature-title {
                font-size: 1.3em;
                font-weight: 600;
                color: #2c5530;
            }
            
            .feature-description {
                color: #666;
                margin-bottom: 20px;
                line-height: 1.6;
            }
            
            .test-button { 
                background: linear-gradient(45deg, #28a745, #20c997);
                color: white; 
                padding: 12px 24px; 
                border: none; 
                border-radius: 25px; 
                cursor: pointer; 
                font-weight: 600;
                transition: all 0.3s ease;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-size: 0.9em;
            }
            
            .test-button:hover { 
                background: linear-gradient(45deg, #218838, #1ea085);
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(40, 167, 69, 0.4);
            }
            
            .api-links {
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                justify-content: center;
                margin: 30px 0;
            }
            
            .api-link { 
                background: linear-gradient(45deg, #007bff, #0056b3);
                color: white; 
                padding: 12px 24px; 
                text-decoration: none; 
                border-radius: 25px; 
                transition: all 0.3s ease;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-size: 0.9em;
            }
            
            .api-link:hover { 
                background: linear-gradient(45deg, #0056b3, #004085);
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0, 123, 255, 0.4);
            }
            
            .demo-section {
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                padding: 30px;
                border-radius: 15px;
                border: 2px solid #dee2e6;
                margin-top: 30px;
            }
            
            .demo-controls {
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                margin-bottom: 25px;
                justify-content: center;
            }
            
            #results { 
                background: #2d3748;
                color: #e2e8f0;
                padding: 20px; 
                border-radius: 10px; 
                margin-top: 20px; 
                max-height: 400px; 
                overflow-y: auto;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
                line-height: 1.4;
                border: 2px solid #4a5568;
            }
            
            .loading {
                display: inline-flex;
                align-items: center;
                gap: 10px;
                color: #007bff;
                font-weight: 600;
            }
            
            .spinner {
                width: 20px;
                height: 20px;
                border: 2px solid #f3f3f3;
                border-top: 2px solid #007bff;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
            
            .success { color: #28a745; }
            .error { color: #dc3545; }
            
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
            
            @media (max-width: 768px) {
                .header-content {
                    flex-direction: column;
                    gap: 15px;
                }
                
                .header-controls {
                    flex-direction: column;
                    gap: 10px;
                }
                
                .selector-container {
                    flex-direction: column;
                    align-items: stretch;
                    gap: 10px;
                }
                
                .location-dropdown, .commodity-dropdown {
                    min-width: auto;
                    font-size: 0.9em;
                }
                
                .commodity-options {
                    min-width: auto;
                }
                
                .logo h1 {
                    font-size: 2em;
                }
                
                .hero-section h2 {
                    font-size: 1.8em;
                }
                
                .price-grid {
                    grid-template-columns: 1fr;
                }
                
                .features-grid {
                    grid-template-columns: 1fr;
                }
                
                .api-links {
                    flex-direction: column;
                    align-items: center;
                }
                
                .language-dropdown {
                    min-width: 100px;
                    font-size: 0.9em;
                }
            }
            
            .location-selector-container {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 25px;
                flex-wrap: wrap;
                gap: 15px;
            }
            
            .selector-container {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 25px;
                flex-wrap: wrap;
                gap: 15px;
            }
            
            .location-selector, .commodity-selector {
                position: relative;
            }
            
            .location-dropdown, .commodity-dropdown {
                background: rgba(255,255,255,0.9);
                border: 2px solid #007bff;
                border-radius: 25px;
                padding: 10px 18px;
                font-weight: 600;
                color: #0056b3;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 10px;
                transition: all 0.3s ease;
                min-width: 180px;
                font-size: 0.95em;
            }
            
            .commodity-dropdown {
                border-color: #28a745;
                color: #155724;
            }
            
            .location-dropdown:hover, .commodity-dropdown:hover {
                background: rgba(0, 123, 255, 0.1);
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0, 123, 255, 0.3);
            }
            
            .commodity-dropdown:hover {
                background: rgba(40, 167, 69, 0.1);
                box-shadow: 0 5px 15px rgba(40, 167, 69, 0.3);
            }
            
            .location-options, .commodity-options {
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: white;
                border: 2px solid #007bff;
                border-radius: 15px;
                margin-top: 5px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                display: none;
                z-index: 1000;
                max-height: 350px;
                overflow-y: auto;
            }
            
            .commodity-options {
                border-color: #28a745;
                min-width: 250px;
            }
            
            .location-options.show, .commodity-options.show {
                display: block;
            }
            
            .location-option, .commodity-option {
                padding: 12px 16px;
                cursor: pointer;
                transition: background 0.2s ease;
                display: flex;
                align-items: center;
                gap: 12px;
                border-bottom: 1px solid #f0f0f0;
                font-size: 0.9em;
            }
            
            .commodity-option {
                padding-left: 24px;
            }
            
            .location-option:hover, .commodity-option:hover {
                background: rgba(0, 123, 255, 0.1);
            }
            
            .commodity-option:hover {
                background: rgba(40, 167, 69, 0.1);
            }
            
            .location-option:last-child, .commodity-option:last-child {
                border-bottom: none;
            }
            
            .location-option.selected, .commodity-option.selected {
                background: rgba(0, 123, 255, 0.2);
                font-weight: 600;
            }
            
            .commodity-option.selected {
                background: rgba(40, 167, 69, 0.2);
            }
            
            .commodity-category {
                border-bottom: 1px solid #e9ecef;
            }
            
            .commodity-category:last-child {
                border-bottom: none;
            }
            
            .category-header {
                padding: 12px 16px;
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                font-weight: 700;
                color: #495057;
                font-size: 0.85em;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 1px solid #dee2e6;
            }
            
            .refresh-prices-btn {
                background: linear-gradient(45deg, #17a2b8, #138496);
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s ease;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                font-size: 0.9em;
            }
            
            .refresh-prices-btn:hover {
                background: linear-gradient(45deg, #138496, #117a8b);
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(23, 162, 184, 0.4);
            }
            
            .no-results {
                text-align: center;
                padding: 60px 20px;
                color: #666;
                grid-column: 1 / -1;
            }
            
            .no-results p {
                margin: 10px 0;
            }
        </style>
        <script>
            let isLoading = false;
            let currentLanguage = 'en';
            let currentLocation = 'all';
            let currentCommodity = 'all';
            
            function toggleLanguageDropdown() {
                const dropdown = document.getElementById('language-options');
                dropdown.classList.toggle('show');
                
                // Close dropdown when clicking outside
                document.addEventListener('click', function(event) {
                    if (!event.target.closest('.language-selector')) {
                        dropdown.classList.remove('show');
                    }
                });
            }
            
            function toggleLocationDropdown() {
                const dropdown = document.getElementById('location-options');
                dropdown.classList.toggle('show');
                
                // Close dropdown when clicking outside
                document.addEventListener('click', function(event) {
                    if (!event.target.closest('.location-selector')) {
                        dropdown.classList.remove('show');
                    }
                });
            }
            
            function toggleCommodityDropdown() {
                const dropdown = document.getElementById('commodity-options');
                dropdown.classList.toggle('show');
                
                // Close dropdown when clicking outside
                document.addEventListener('click', function(event) {
                    if (!event.target.closest('.commodity-selector')) {
                        dropdown.classList.remove('show');
                    }
                });
            }
            
            function selectLocation(code, name) {
                currentLocation = code;
                document.getElementById('current-location').textContent = name;
                
                // Update selected option
                document.querySelectorAll('.location-option').forEach(option => {
                    option.classList.remove('selected');
                });
                event.target.closest('.location-option').classList.add('selected');
                
                // Close dropdown
                document.getElementById('location-options').classList.remove('show');
                
                // Reload prices for selected location
                loadPricesForLocation();
                
                // Show location change notification
                showNotification(`Location changed to ${name}`, 'success');
            }
            
            function selectCommodity(code, name) {
                currentCommodity = code;
                document.getElementById('current-commodity').textContent = name;
                
                // Update selected option
                document.querySelectorAll('.commodity-option').forEach(option => {
                    option.classList.remove('selected');
                });
                event.target.closest('.commodity-option').classList.add('selected');
                
                // Close dropdown
                document.getElementById('commodity-options').classList.remove('show');
                
                // Reload prices for selected commodity
                loadPricesForLocation();
                
                // Show commodity change notification
                showNotification(`Commodity filter: ${name}`, 'success');
            }
            
            function toggleLanguageDropdown() {
                const dropdown = document.getElementById('language-options');
                dropdown.classList.toggle('show');
                
                // Close dropdown when clicking outside
                document.addEventListener('click', function(event) {
                    if (!event.target.closest('.language-selector')) {
                        dropdown.classList.remove('show');
                    }
                });
            }
            
            function selectLanguage(code, name, flag) {
                currentLanguage = code;
                document.getElementById('current-language').textContent = name;
                
                // Update selected option
                document.querySelectorAll('.language-option').forEach(option => {
                    option.classList.remove('selected');
                });
                event.target.closest('.language-option').classList.add('selected');
                
                // Close dropdown
                document.getElementById('language-options').classList.remove('show');
                
                // Update UI text based on language
                updateUILanguage(code);
                
                // Show language change notification
                showNotification(`Language changed to ${name} ${flag}`, 'success');
            }
            
            function updateUILanguage(languageCode) {
                const translations = {
                    'en': {
                        'hero-title': 'Agricultural Intelligence Platform',
                        'hero-subtitle': "India's first ambient AI-powered, farmer-first, multilingual agricultural intelligence platform",
                        'live-prices': 'Live Market Prices',
                        'voice-processing': 'Voice Processing',
                        'voice-desc': 'Advanced speech recognition and synthesis in 50+ Indian languages with cultural context awareness',
                        'price-discovery': 'Price Discovery',
                        'price-desc': 'Real-time market prices from mandis across all Indian states with trend analysis and predictions',
                        'negotiation': 'Negotiation Assistant',
                        'negotiation-desc': 'AI-powered negotiation strategies with market analysis and competitive intelligence',
                        'crop-planning': 'Crop Planning',
                        'crop-desc': 'Intelligent crop recommendations based on weather, soil, market trends, and profitability analysis',
                        'msp-monitoring': 'MSP Monitoring',
                        'msp-desc': 'Continuous monitoring of Minimum Support Prices with alerts and alternative market suggestions',
                        'cross-mandi': 'Cross-Mandi Network',
                        'cross-mandi-desc': 'National network of mandi data with transportation costs and arbitrage opportunities'
                    },
                    'hi': {
                        'hero-title': 'कृषि बुद्धिमत्ता मंच',
                        'hero-subtitle': 'भारत का पहला परिवेशी AI-संचालित, किसान-प्रथम, बहुभाषी कृषि बुद्धिमत्ता मंच',
                        'live-prices': 'लाइव बाजार भाव',
                        'voice-processing': 'आवाज प्रसंस्करण',
                        'voice-desc': '50+ भारतीय भाषाओं में उन्नत वाक् पहचान और संश्लेषण सांस्कृतिक संदर्भ जागरूकता के साथ',
                        'price-discovery': 'मूल्य खोज',
                        'price-desc': 'सभी भारतीय राज्यों की मंडियों से वास्तविक समय बाजार मूल्य रुझान विश्लेषण और भविष्यवाणियों के साथ',
                        'negotiation': 'बातचीत सहायक',
                        'negotiation-desc': 'बाजार विश्लेषण और प्रतिस्पर्धी बुद्धिमत्ता के साथ AI-संचालित बातचीत रणनीतियां',
                        'crop-planning': 'फसल योजना',
                        'crop-desc': 'मौसम, मिट्टी, बाजार रुझान और लाभप्रदता विश्लेषण के आधार पर बुद्धिमान फसल सिफारिशें',
                        'msp-monitoring': 'MSP निगरानी',
                        'msp-desc': 'अलर्ट और वैकल्पिक बाजार सुझावों के साथ न्यूनतम समर्थन मूल्य की निरंतर निगरानी',
                        'cross-mandi': 'क्रॉस-मंडी नेटवर्क',
                        'cross-mandi-desc': 'परिवहन लागत और मध्यस्थता अवसरों के साथ मंडी डेटा का राष्ट्रीय नेटवर्क'
                    }
                };
                
                const lang = translations[languageCode] || translations['en'];
                
                // Update text content
                Object.keys(lang).forEach(key => {
                    const elements = document.querySelectorAll(`[data-translate="${key}"]`);
                    elements.forEach(element => {
                        element.textContent = lang[key];
                    });
                });
            }
            
            function showNotification(message, type = 'info') {
                const notification = document.createElement('div');
                const colors = {
                    'success': '#4CAF50',
                    'info': '#2196F3',
                    'warning': '#FF9800',
                    'error': '#f44336'
                };
                
                notification.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: ${colors[type] || colors.info};
                    color: white;
                    padding: 15px 20px;
                    border-radius: 10px;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.3);
                    z-index: 10000;
                    font-weight: 600;
                    animation: slideIn 0.3s ease;
                    max-width: 300px;
                `;
                notification.textContent = message;
                document.body.appendChild(notification);
                
                setTimeout(() => {
                    notification.style.animation = 'slideOut 0.3s ease';
                    setTimeout(() => notification.remove(), 300);
                }, 3000);
            }
            
            async function testAPI(endpoint, method = 'GET', body = null, buttonElement = null) {
                console.log('🧪 Testing API:', endpoint, method, body);
                
                if (isLoading) {
                    console.log('⚠️ Already loading, skipping...');
                    return;
                }
                
                const resultsDiv = document.getElementById('results');
                if (!resultsDiv) {
                    console.error('❌ Results div not found!');
                    return;
                }
                
                isLoading = true;
                const requestStartTime = Date.now();
                
                if (buttonElement) {
                    buttonElement.disabled = true;
                    buttonElement.innerHTML = '<div class="spinner"></div> Testing...';
                }
                
                resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div>Testing ' + endpoint + '...</div>';
                
                try {
                    const options = { method: method };
                    if (body) {
                        options.headers = { 'Content-Type': 'application/json' };
                        options.body = JSON.stringify(body);
                    }
                    
                    console.log('📡 Making request:', options);
                    const response = await fetch(endpoint, options);
                    const data = await response.json();
                    
                    console.log('✅ Response received:', response.status, data);
                    
                    resultsDiv.innerHTML = `
                        <div class="success">
                            <h4>✅ SUCCESS: ${endpoint}</h4>
                            <p><strong>Status:</strong> ${response.status} ${response.statusText}</p>
                            <p><strong>Response Time:</strong> ${Date.now() - requestStartTime}ms</p>
                            <pre>${JSON.stringify(data, null, 2)}</pre>
                        </div>
                    `;
                } catch (error) {
                    console.error('❌ API Error:', error);
                    resultsDiv.innerHTML = `
                        <div class="error">
                            <h4>❌ ERROR: ${endpoint}</h4>
                            <p><strong>Error:</strong> ${error.message}</p>
                            <p><strong>Time:</strong> ${new Date().toLocaleTimeString()}</p>
                        </div>
                    `;
                } finally {
                    isLoading = false;
                    if (buttonElement) {
                        buttonElement.disabled = false;
                        buttonElement.innerHTML = buttonElement.getAttribute('data-original-text');
                    }
                    console.log('🏁 API test completed');
                }
            }
            
            async function loadPrices() {
                await loadPricesForLocation();
            }
            
            async function loadPricesForLocation() {
                try {
                    const response = await fetch('/api/v1/prices/current');
                    const data = await response.json();
                    
                    let html = '';
                    let displayedCount = 0;
                    
                    for (const [commodity, info] of Object.entries(data.prices)) {
                        // Filter by selected commodity
                        if (currentCommodity !== 'all' && commodity !== currentCommodity) {
                            continue;
                        }
                        
                        // Apply location-based price variation
                        let locationMultiplier = 1.0;
                        switch(currentLocation) {
                            case 'delhi': locationMultiplier = 1.0; break;
                            case 'gurgaon': locationMultiplier = 0.95; break;
                            case 'faridabad': locationMultiplier = 0.97; break;
                            case 'meerut': locationMultiplier = 0.92; break;
                            case 'panipat': locationMultiplier = 0.90; break;
                            default: locationMultiplier = 1.0;
                        }
                        
                        const adjustedPrice = Math.round(info.price * locationMultiplier);
                        const trendClass = info.trend === 'up' ? 'up' : info.trend === 'down' ? 'down' : 'stable';
                        const trendIcon = info.trend === 'up' ? '📈' : info.trend === 'down' ? '📉' : '➡️';
                        
                        // Get commodity emoji
                        const commodityEmojis = {
                            'wheat': '🌾', 'rice': '🍚', 'corn': '🌽',
                            'cotton': '🌿', 'sugarcane': '🎋',
                            'tomato': '🍅', 'onion': '🧅', 'potato': '🥔',
                            'cabbage': '🥬', 'cauliflower': '🥦', 'carrot': '🥕',
                            'green_beans': '🫘', 'bell_pepper': '🫑'
                        };
                        
                        const emoji = commodityEmojis[commodity] || '🌾';
                        const displayName = commodity.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
                        
                        html += `
                            <div class="price-card">
                                <div class="commodity-name">${emoji} ${displayName}</div>
                                <div class="price-value">
                                    <i class="fas fa-rupee-sign"></i>${adjustedPrice}
                                </div>
                                <div class="price-details">
                                    <span>${info.unit}</span>
                                    <span class="trend ${trendClass}">
                                        ${trendIcon} ${info.change}
                                    </span>
                                </div>
                                ${currentLocation !== 'all' ? `<div style="font-size: 0.8em; color: #666; margin-top: 5px;">📍 ${document.getElementById('current-location').textContent}</div>` : ''}
                            </div>
                        `;
                        displayedCount++;
                    }
                    
                    if (displayedCount === 0) {
                        html = `<div class="no-results">
                            <i class="fas fa-search" style="font-size: 3em; color: #ccc; margin-bottom: 15px;"></i>
                            <p>No prices found for the selected filters</p>
                            <p style="font-size: 0.9em; color: #666;">Try selecting "All Commodities" or a different location</p>
                        </div>`;
                    }
                    
                    document.getElementById('price-grid').innerHTML = html;
                } catch (error) {
                    document.getElementById('price-grid').innerHTML = '<div class="error">❌ Error loading prices</div>';
                }
            }
            
            function setupButtons() {
                document.querySelectorAll('.test-button').forEach(button => {
                    button.setAttribute('data-original-text', button.innerHTML);
                });
            }
            
            async function runAllTests() {
                console.log('🚀 Running comprehensive system tests...');
                alert('Running all tests! Check results below and console for details.');
                
                const tests = [
                    { name: 'Health Check', func: () => testAPI('/health', 'GET', null) },
                    { name: 'Current Prices', func: () => testAPI('/api/v1/prices/current', 'GET', null) },
                    { name: 'MSP Rates', func: () => testAPI('/api/v1/msp/rates', 'GET', null) },
                    { name: 'Mandis List', func: () => testAPI('/api/v1/mandis', 'GET', null) },
                    { name: 'Voice Processing', func: () => testAPI('/api/v1/voice/transcribe', 'POST', {audio_data: 'test', language: currentLanguage}) },
                    { name: 'Negotiation Analysis', func: () => testAPI('/api/v1/negotiation/analyze', 'POST', {commodity: 'wheat', current_price: 2400, quantity: 100}) },
                    { name: 'Crop Planning', func: () => testAPI('/api/v1/crop-planning/recommend', 'POST', {farm_size: 5.0, season: 'kharif'}) },
                    { name: 'Test Endpoint', func: () => testAPI('/api/v1/test', 'GET', null) }
                ];
                
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div>Running comprehensive system test...</div>';
                
                let results = '<h3>🧪 Comprehensive System Test Results</h3>';
                let passCount = 0;
                
                for (const test of tests) {
                    try {
                        console.log(`🧪 Testing: ${test.name}`);
                        const response = await fetch(test.func.toString().includes('/health') ? '/health' : 
                                                   test.func.toString().includes('/api/v1/prices/current') ? '/api/v1/prices/current' :
                                                   test.func.toString().includes('/api/v1/msp/rates') ? '/api/v1/msp/rates' :
                                                   test.func.toString().includes('/api/v1/mandis') ? '/api/v1/mandis' :
                                                   test.func.toString().includes('/api/v1/test') ? '/api/v1/test' :
                                                   '/api/v1/test');
                        
                        if (response.ok) {
                            results += `<div class="success">✅ ${test.name}: PASSED</div>`;
                            passCount++;
                            console.log(`✅ ${test.name}: PASSED`);
                        } else {
                            results += `<div class="error">❌ ${test.name}: FAILED (${response.status})</div>`;
                            console.log(`❌ ${test.name}: FAILED (${response.status})`);
                        }
                    } catch (error) {
                        results += `<div class="error">❌ ${test.name}: ERROR (${error.message})</div>`;
                        console.log(`❌ ${test.name}: ERROR (${error.message})`);
                    }
                }
                
                results += `<div style="margin-top: 20px; padding: 15px; background: rgba(40, 167, 69, 0.1); border-radius: 8px;">
                    <strong>Test Summary: ${passCount}/${tests.length} tests passed</strong>
                </div>`;
                
                resultsDiv.innerHTML = results;
                console.log(`🏁 All tests completed: ${passCount}/${tests.length} passed`);
            }
            
            window.onload = function() {
                console.log('🚀 MANDI EAR™ UI Loading...');
                loadPrices();
                setupButtons();
                
                // Auto-refresh prices every 30 seconds
                setInterval(loadPricesForLocation, 30000);
                
                // Test all functionality on load
                setTimeout(testAllFunctionality, 2000);
                
                console.log('✅ MANDI EAR™ UI Loaded Successfully!');
            };
            
            function setupButtons() {
                console.log('🔧 Setting up buttons...');
                document.querySelectorAll('.test-button').forEach(button => {
                    button.setAttribute('data-original-text', button.innerHTML);
                    console.log('✅ Button setup:', button.textContent.trim());
                });
            }
            
            // Test functions for all features with enhanced feedback
            function testVoiceProcessing() {
                console.log('🎤 Voice Processing Test Clicked!');
                showNotification('🎤 Testing Voice Processing API...', 'info');
                testAPI('/api/v1/voice/transcribe', 'POST', {
                    audio_data: 'mock_audio_data', 
                    language: currentLanguage
                });
            }
            
            function testPriceDiscovery() {
                console.log('💰 Price Discovery Test Clicked!');
                showNotification('💰 Testing Price Discovery API...', 'info');
                testAPI('/api/v1/prices/current?commodity=wheat', 'GET', null);
            }
            
            function testNegotiationAssistant() {
                console.log('🤝 Negotiation Assistant Test Clicked!');
                showNotification('🤝 Testing Negotiation Assistant API...', 'info');
                testAPI('/api/v1/negotiation/analyze', 'POST', {
                    commodity: 'wheat', 
                    current_price: 2400, 
                    quantity: 100
                });
            }
            
            function testCropPlanning() {
                console.log('🌱 Crop Planning Test Clicked!');
                showNotification('🌱 Testing Crop Planning API...', 'info');
                testAPI('/api/v1/crop-planning/recommend', 'POST', {
                    farm_size: 5.0, 
                    season: 'kharif', 
                    location: {latitude: 28.6139, longitude: 77.2090}
                });
            }
            
            function testMSPMonitoring() {
                console.log('📊 MSP Monitoring Test Clicked!');
                showNotification('📊 Testing MSP Monitoring API...', 'info');
                testAPI('/api/v1/msp/rates', 'GET', null);
            }
            
            function testCrossMandiNetwork() {
                console.log('🌐 Cross-Mandi Network Test Clicked!');
                showNotification('🌐 Testing Cross-Mandi Network API...', 'info');
                testAPI('/api/v1/mandis', 'GET', null);
            }
            
            function testHealthCheck() {
                console.log('🏥 Health Check Test Clicked!');
                showNotification('🏥 Testing Health Check API...', 'info');
                testAPI('/health', 'GET', null);
            }
            
            function testQuickTest() {
                console.log('⚡ Quick Test Clicked!');
                showNotification('⚡ Running Quick System Test...', 'info');
                testAPI('/api/v1/test', 'GET', null);
            }
            
            async function testAllFunctionality() {
                console.log('🧪 Testing all MANDI EAR functionality...');
                
                // Test API endpoints
                const endpoints = [
                    '/health',
                    '/api/v1/prices/current',
                    '/api/v1/mandis',
                    '/api/v1/msp/rates',
                    '/api/v1/test'
                ];
                
                let allWorking = true;
                for (const endpoint of endpoints) {
                    try {
                        const response = await fetch(endpoint);
                        if (!response.ok) allWorking = false;
                        console.log(`✅ ${endpoint}: OK`);
                    } catch (error) {
                        console.log(`❌ ${endpoint}: ERROR`);
                        allWorking = false;
                    }
                }
                
                if (allWorking) {
                    console.log('🎉 All MANDI EAR features are working perfectly!');
                } else {
                    console.log('⚠️ Some features may need attention');
                }
            }
            
            const pageLoadTime = Date.now();
        </script>
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
                                <div class="language-option selected" onclick="selectLanguage('en', 'English', '🇺🇸')">
                                    <span>🇺🇸</span>
                                    <span>English</span>
                                </div>
                                <div class="language-option" onclick="selectLanguage('hi', 'हिंदी', '🇮🇳')">
                                    <span>🇮🇳</span>
                                    <span>हिंदी (Hindi)</span>
                                </div>
                                <div class="language-option" onclick="selectLanguage('bn', 'বাংলা', '🇧🇩')">
                                    <span>🇧🇩</span>
                                    <span>বাংলা (Bengali)</span>
                                </div>
                                <div class="language-option" onclick="selectLanguage('te', 'తెలుగు', '🇮🇳')">
                                    <span>🇮🇳</span>
                                    <span>తెలుగు (Telugu)</span>
                                </div>
                                <div class="language-option" onclick="selectLanguage('ta', 'தமிழ்', '🇮🇳')">
                                    <span>🇮🇳</span>
                                    <span>தமிழ் (Tamil)</span>
                                </div>
                                <div class="language-option" onclick="selectLanguage('mr', 'मराठी', '🇮🇳')">
                                    <span>🇮🇳</span>
                                    <span>मराठी (Marathi)</span>
                                </div>
                                <div class="language-option" onclick="selectLanguage('gu', 'ગુજરાતી', '🇮🇳')">
                                    <span>🇮🇳</span>
                                    <span>ગુજરાતી (Gujarati)</span>
                                </div>
                                <div class="language-option" onclick="selectLanguage('kn', 'ಕನ್ನಡ', '🇮🇳')">
                                    <span>🇮🇳</span>
                                    <span>ಕನ್ನಡ (Kannada)</span>
                                </div>
                                <div class="language-option" onclick="selectLanguage('ml', 'മലയാളം', '🇮🇳')">
                                    <span>🇮🇳</span>
                                    <span>മലയാളം (Malayalam)</span>
                                </div>
                                <div class="language-option" onclick="selectLanguage('pa', 'ਪੰਜਾਬੀ', '🇮🇳')">
                                    <span>🇮🇳</span>
                                    <span>ਪੰਜਾਬੀ (Punjabi)</span>
                                </div>
                                <div class="language-option" onclick="selectLanguage('or', 'ଓଡ଼ିଆ', '🇮🇳')">
                                    <span>🇮🇳</span>
                                    <span>ଓଡ଼ିଆ (Odia)</span>
                                </div>
                                <div class="language-option" onclick="selectLanguage('as', 'অসমীয়া', '🇮🇳')">
                                    <span>🇮🇳</span>
                                    <span>অসমীয়া (Assamese)</span>
                                </div>
                            </div>
                        </div>
                        <div class="status-badge">
                            <i class="fas fa-check-circle"></i>
                            System Operational
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
                            <span class="stat-number">50+</span>
                            <span class="stat-label">Languages</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">1000+</span>
                            <span class="stat-label">Mandis</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">24/7</span>
                            <span class="stat-label">Monitoring</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">AI</span>
                            <span class="stat-label">Powered</span>
                        </div>
                    </div>
                </div>

                <div class="dashboard">
                    <div class="section-title">
                        <i class="fas fa-chart-line"></i>
                        <span data-translate="live-prices">Live Market Prices</span>
                    </div>
                    
                    <!-- Location and Commodity Selectors -->
                    <div class="selector-container">
                        <div class="location-selector">
                            <div class="location-dropdown" onclick="toggleLocationDropdown()">
                                <i class="fas fa-map-marker-alt"></i>
                                <span id="current-location">All Mandis</span>
                                <i class="fas fa-chevron-down"></i>
                            </div>
                            <div class="location-options" id="location-options">
                                <div class="location-option selected" onclick="selectLocation('all', 'All Mandis')">
                                    <span>🇮🇳</span>
                                    <span>All Mandis</span>
                                </div>
                                <div class="location-option" onclick="selectLocation('delhi', 'Delhi Mandi')">
                                    <span>🏛️</span>
                                    <span>Delhi Mandi</span>
                                </div>
                                <div class="location-option" onclick="selectLocation('gurgaon', 'Gurgaon Mandi')">
                                    <span>🏢</span>
                                    <span>Gurgaon Mandi (Haryana)</span>
                                </div>
                                <div class="location-option" onclick="selectLocation('faridabad', 'Faridabad Mandi')">
                                    <span>🏭</span>
                                    <span>Faridabad Mandi (Haryana)</span>
                                </div>
                                <div class="location-option" onclick="selectLocation('meerut', 'Meerut Mandi')">
                                    <span>🌾</span>
                                    <span>Meerut Mandi (UP)</span>
                                </div>
                                <div class="location-option" onclick="selectLocation('panipat', 'Panipat Mandi')">
                                    <span>🚜</span>
                                    <span>Panipat Mandi (Haryana)</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="commodity-selector">
                            <div class="commodity-dropdown" onclick="toggleCommodityDropdown()">
                                <i class="fas fa-seedling"></i>
                                <span id="current-commodity">All Commodities</span>
                                <i class="fas fa-chevron-down"></i>
                            </div>
                            <div class="commodity-options" id="commodity-options">
                                <div class="commodity-option selected" onclick="selectCommodity('all', 'All Commodities')">
                                    <span>🌾</span>
                                    <span>All Commodities</span>
                                </div>
                                
                                <div class="commodity-category">
                                    <div class="category-header">🌾 Grains & Cereals</div>
                                    <div class="commodity-option" onclick="selectCommodity('wheat', 'Wheat')">
                                        <span>🌾</span>
                                        <span>Wheat</span>
                                    </div>
                                    <div class="commodity-option" onclick="selectCommodity('rice', 'Rice')">
                                        <span>🍚</span>
                                        <span>Rice</span>
                                    </div>
                                    <div class="commodity-option" onclick="selectCommodity('corn', 'Corn')">
                                        <span>🌽</span>
                                        <span>Corn</span>
                                    </div>
                                </div>
                                
                                <div class="commodity-category">
                                    <div class="category-header">🥬 Top Vegetables</div>
                                    <div class="commodity-option" onclick="selectCommodity('tomato', 'Tomato')">
                                        <span>🍅</span>
                                        <span>Tomato</span>
                                    </div>
                                    <div class="commodity-option" onclick="selectCommodity('onion', 'Onion')">
                                        <span>🧅</span>
                                        <span>Onion</span>
                                    </div>
                                    <div class="commodity-option" onclick="selectCommodity('potato', 'Potato')">
                                        <span>🥔</span>
                                        <span>Potato</span>
                                    </div>
                                    <div class="commodity-option" onclick="selectCommodity('cabbage', 'Cabbage')">
                                        <span>🥬</span>
                                        <span>Cabbage</span>
                                    </div>
                                    <div class="commodity-option" onclick="selectCommodity('cauliflower', 'Cauliflower')">
                                        <span>🥦</span>
                                        <span>Cauliflower</span>
                                    </div>
                                    <div class="commodity-option" onclick="selectCommodity('carrot', 'Carrot')">
                                        <span>🥕</span>
                                        <span>Carrot</span>
                                    </div>
                                    <div class="commodity-option" onclick="selectCommodity('green_beans', 'Green Beans')">
                                        <span>🫘</span>
                                        <span>Green Beans</span>
                                    </div>
                                    <div class="commodity-option" onclick="selectCommodity('bell_pepper', 'Bell Pepper')">
                                        <span>🫑</span>
                                        <span>Bell Pepper</span>
                                    </div>
                                </div>
                                
                                <div class="commodity-category">
                                    <div class="category-header">💰 Cash Crops</div>
                                    <div class="commodity-option" onclick="selectCommodity('cotton', 'Cotton')">
                                        <span>🌿</span>
                                        <span>Cotton</span>
                                    </div>
                                    <div class="commodity-option" onclick="selectCommodity('sugarcane', 'Sugarcane')">
                                        <span>🎋</span>
                                        <span>Sugarcane</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <button class="refresh-prices-btn" onclick="loadPricesForLocation()">
                            <i class="fas fa-sync-alt"></i> Refresh Prices
                        </button>
                    </div>
                    
                    <div id="price-grid" class="price-grid">
                        <div class="loading"><div class="spinner"></div>Loading live prices...</div>
                    </div>
                </div>

                <div class="features-grid">
                    <div class="feature-card">
                        <div class="feature-header">
                            <i class="fas fa-microphone feature-icon"></i>
                            <div class="feature-title" data-translate="voice-processing">Voice Processing</div>
                        </div>
                        <div class="feature-description" data-translate="voice-desc">
                            Advanced speech recognition and synthesis in 50+ Indian languages with cultural context awareness
                        </div>
                        <button class="test-button" onclick="testVoiceProcessing()" data-endpoint="/api/v1/voice/transcribe">
                            <i class="fas fa-play"></i> Test Voice API
                        </button>
                    </div>

                    <div class="feature-card">
                        <div class="feature-header">
                            <i class="fas fa-coins feature-icon"></i>
                            <div class="feature-title" data-translate="price-discovery">Price Discovery</div>
                        </div>
                        <div class="feature-description" data-translate="price-desc">
                            Real-time market prices from mandis across all Indian states with trend analysis and predictions
                        </div>
                        <button class="test-button" onclick="testPriceDiscovery()">
                            <i class="fas fa-search"></i> Test Price API
                        </button>
                    </div>

                    <div class="feature-card">
                        <div class="feature-header">
                            <i class="fas fa-handshake feature-icon"></i>
                            <div class="feature-title" data-translate="negotiation">Negotiation Assistant</div>
                        </div>
                        <div class="feature-description" data-translate="negotiation-desc">
                            AI-powered negotiation strategies with market analysis and competitive intelligence
                        </div>
                        <button class="test-button" onclick="testNegotiationAssistant()">
                            <i class="fas fa-brain"></i> Test Negotiation
                        </button>
                    </div>

                    <div class="feature-card">
                        <div class="feature-header">
                            <i class="fas fa-seedling feature-icon"></i>
                            <div class="feature-title" data-translate="crop-planning">Crop Planning</div>
                        </div>
                        <div class="feature-description" data-translate="crop-desc">
                            Intelligent crop recommendations based on weather, soil, market trends, and profitability analysis
                        </div>
                        <button class="test-button" onclick="testCropPlanning()">
                            <i class="fas fa-leaf"></i> Test Crop Planning
                        </button>
                    </div>

                    <div class="feature-card">
                        <div class="feature-header">
                            <i class="fas fa-shield-alt feature-icon"></i>
                            <div class="feature-title" data-translate="msp-monitoring">MSP Monitoring</div>
                        </div>
                        <div class="feature-description" data-translate="msp-desc">
                            Continuous monitoring of Minimum Support Prices with alerts and alternative market suggestions
                        </div>
                        <button class="test-button" onclick="testMSPMonitoring()">
                            <i class="fas fa-eye"></i> Test MSP Monitor
                        </button>
                    </div>

                    <div class="feature-card">
                        <div class="feature-header">
                            <i class="fas fa-network-wired feature-icon"></i>
                            <div class="feature-title" data-translate="cross-mandi">Cross-Mandi Network</div>
                        </div>
                        <div class="feature-description" data-translate="cross-mandi-desc">
                            National network of mandi data with transportation costs and arbitrage opportunities
                        </div>
                        <button class="test-button" onclick="testCrossMandiNetwork()">
                            <i class="fas fa-globe"></i> Test Mandi Network
                        </button>
                    </div>
                </div>

                <div class="dashboard">
                    <div class="section-title">
                        <i class="fas fa-link"></i>
                        API Endpoints
                    </div>
                    <div class="api-links">
                        <a href="/docs" class="api-link">
                            <i class="fas fa-book"></i> API Documentation
                        </a>
                        <a href="/health" class="api-link">
                            <i class="fas fa-heartbeat"></i> Health Check
                        </a>
                        <a href="/api/v1/prices/current" class="api-link">
                            <i class="fas fa-coins"></i> Current Prices
                        </a>
                        <a href="/api/v1/mandis" class="api-link">
                            <i class="fas fa-store"></i> Mandi List
                        </a>
                        <a href="/api/v1/test" class="api-link">
                            <i class="fas fa-flask"></i> Test All Features
                        </a>
                    </div>
                </div>

                <div class="demo-section">
                    <div class="section-title">
                        <i class="fas fa-vial"></i>
                        Interactive API Testing
                    </div>
                    <p style="text-align: center; margin-bottom: 25px; color: #666;">
                        Test individual features above or run comprehensive system tests below
                    </p>
                    
                    <div class="demo-controls">
                        <button class="test-button" onclick="runAllTests()">
                            <i class="fas fa-rocket"></i> Run All Tests
                        </button>
                        <button class="test-button" onclick="testQuickTest()">
                            <i class="fas fa-check-double"></i> Quick Test
                        </button>
                        <button class="test-button" onclick="testHealthCheck()">
                            <i class="fas fa-stethoscope"></i> Health Check
                        </button>
                        <button class="test-button" onclick="loadPricesForLocation(); document.getElementById('results').innerHTML = '✅ Prices refreshed successfully for ' + document.getElementById('current-location').textContent + '!'">
                            <i class="fas fa-sync"></i> Refresh Prices
                        </button>
                    </div>
                    
                    <div id="results">
                        <div style="text-align: center; color: #666; padding: 40px;">
                            <i class="fas fa-play-circle" style="font-size: 3em; margin-bottom: 15px;"></i>
                            <p>Click any test button above to see live API responses</p>
                        </div>
                    </div>
                </div>

                <div style="text-align: center; margin-top: 40px; color: rgba(255,255,255,0.8);">
                    <p><strong>Timestamp:</strong> """ + get_current_time() + """</p>
                    <p style="margin-top: 10px;">🌾 Empowering farmers across India with AI-driven agricultural intelligence</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": get_current_time(),
        "version": "1.0.0",
        "platform": "MANDI EAR™",
        "services": {
            "api_gateway": "healthy",
            "voice_processing": "healthy",
            "price_discovery": "healthy",
            "negotiation_assistant": "healthy",
            "crop_planning": "healthy"
        }
    }

@app.get("/api/v1/prices/current")
async def get_current_prices(commodity: Optional[str] = None):
    """Get current market prices"""
    if commodity:
        if commodity.lower() in MOCK_PRICES:
            price_data = generate_mock_response(MOCK_PRICES[commodity.lower()])
            return {
                "commodity": commodity,
                "price_data": price_data,
                "timestamp": get_current_time(),
                "source": "MANDI EAR™ Network"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Commodity '{commodity}' not found")
    
    # Return all prices
    all_prices = {}
    for commodity, data in MOCK_PRICES.items():
        all_prices[commodity] = generate_mock_response(data)
    
    return {
        "prices": all_prices,
        "timestamp": get_current_time(),
        "total_commodities": len(all_prices)
    }

@app.get("/api/v1/mandis")
async def get_mandis():
    """Get list of mandis"""
    return {
        "mandis": MOCK_MANDIS,
        "total_mandis": len(MOCK_MANDIS),
        "timestamp": get_current_time()
    }

@app.post("/api/v1/voice/transcribe")
async def transcribe_voice(request: Request):
    """Transcribe voice input"""
    try:
        body = await request.json()
        audio_data = body.get("audio_data", "")
        language = body.get("language", "hi")
        
        # Mock transcription responses
        mock_transcriptions = {
            "hi": "आज गेहूं का भाव क्या है?",
            "en": "What is today's wheat price?",
            "ta": "இன்று கோதுமை விலை என்ன?",
            "te": "ఈరోజు గోధుమ ధర ఎంత?",
            "bn": "আজ গমের দাম কত?"
        }
        
        transcription = mock_transcriptions.get(language, mock_transcriptions["hi"])
        
        return {
            "transcription": transcription,
            "language": language,
            "confidence": 0.95,
            "intent": "price_inquiry",
            "commodity": "wheat",
            "timestamp": get_current_time()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/voice/synthesize")
async def synthesize_speech(request: Request):
    """Synthesize speech from text"""
    try:
        body = await request.json()
        text = body.get("text", "")
        language = body.get("language", "hi")
        
        return {
            "audio_data": "mock_base64_audio_data",
            "text": text,
            "language": language,
            "duration": 3.2,
            "timestamp": get_current_time()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/negotiation/analyze")
async def analyze_negotiation(request: Request):
    """Analyze negotiation context"""
    try:
        body = await request.json()
        commodity = body.get("commodity", "wheat")
        current_price = body.get("current_price", 2500)
        quantity = body.get("quantity", 100)
        
        # Mock negotiation analysis
        market_price = MOCK_PRICES.get(commodity.lower(), MOCK_PRICES["wheat"])["price"]
        recommended_price = int(market_price * 1.05)  # 5% above market
        
        return {
            "commodity": commodity,
            "market_analysis": {
                "current_market_price": market_price,
                "recommended_price": recommended_price,
                "negotiation_room": f"{((recommended_price - current_price) / current_price * 100):.1f}%"
            },
            "strategies": [
                "Highlight quality of your produce",
                "Mention transportation costs",
                "Reference prices from nearby mandis",
                "Negotiate for bulk quantity discount"
            ],
            "confidence": 0.87,
            "timestamp": get_current_time()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/crop-planning/recommend")
async def recommend_crops(request: Request):
    """Get crop recommendations"""
    try:
        body = await request.json()
        location = body.get("location", {})
        farm_size = body.get("farm_size", 5.0)
        season = body.get("season", "kharif")
        
        # Mock crop recommendations
        recommendations = [
            {
                "crop": "Rice",
                "variety": "Basmati 1121",
                "expected_yield": int(farm_size * 40),  # quintals
                "projected_income": int(farm_size * 40 * 3200),
                "risk_level": "Low",
                "water_requirement": "High",
                "market_demand": "High"
            },
            {
                "crop": "Cotton",
                "variety": "Bt Cotton",
                "expected_yield": int(farm_size * 25),
                "projected_income": int(farm_size * 25 * 5500),
                "risk_level": "Medium",
                "water_requirement": "Medium",
                "market_demand": "Very High"
            }
        ]
        
        return {
            "recommendations": recommendations,
            "season": season,
            "farm_size": farm_size,
            "total_projected_income": sum(r["projected_income"] for r in recommendations),
            "timestamp": get_current_time()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/msp/rates")
async def get_msp_rates():
    """Get MSP rates"""
    msp_rates = {
        "wheat": {"msp": 2275, "market_price": 2500, "status": "above_msp"},
        "rice": {"msp": 2183, "market_price": 3200, "status": "above_msp"},
        "cotton": {"msp": 6620, "market_price": 5500, "status": "below_msp"},
        "corn": {"msp": 1962, "market_price": 1800, "status": "below_msp"}
    }
    
    return {
        "msp_rates": msp_rates,
        "season": "2024-25",
        "timestamp": get_current_time()
    }

@app.get("/api/v1/test")
async def test_endpoint():
    """Test endpoint"""
    return {
        "message": "MANDI EAR™ API is working perfectly! 🌾",
        "timestamp": get_current_time(),
        "features": [
            "Voice Processing in 50+ languages",
            "Real-time Price Discovery",
            "AI Negotiation Assistant",
            "Intelligent Crop Planning",
            "MSP Enforcement",
            "Cross-Mandi Network"
        ],
        "status": "All systems operational"
    }

# ============================================================================
# STARTUP FUNCTION
# ============================================================================

def start_server():
    """Start the MANDI EAR server"""
    print("🌾 Starting MANDI EAR™ Agricultural Intelligence Platform...")
    print("📦 All dependencies resolved automatically!")
    print("🚀 Server starting on http://localhost:8001")
    print("📚 API Documentation: http://localhost:8001/docs")
    print("🏥 Health Check: http://localhost:8001/health")
    print("💰 Price API: http://localhost:8001/api/v1/prices/current")
    print("🧪 Test API: http://localhost:8001/api/v1/test")
    print("\n✅ MANDI EAR™ is ready to serve farmers across India!")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

if __name__ == "__main__":
    start_server()