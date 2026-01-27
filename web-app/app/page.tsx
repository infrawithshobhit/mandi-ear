'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import Header from '@/components/Header';
import VoiceInterface from '@/components/VoiceInterface';
import PriceDiscovery from '@/components/PriceDiscovery';
import MarketAlerts from '@/components/MarketAlerts';
import QuickActions from '@/components/QuickActions';
import LoginModal from '@/components/LoginModal';

export default function HomePage() {
  const { user, isAuthenticated } = useAuth();
  const { t } = useLanguage();
  const [showLogin, setShowLogin] = useState(false);

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100">
        <div className="container mx-auto px-4 py-16">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-primary-900 mb-6">
              MANDI EAR™
            </h1>
            <p className="text-xl md:text-2xl text-primary-700 mb-8 font-hindi">
              भारत का पहला एआई-संचालित कृषि बुद्धिमत्ता मंच
            </p>
            <p className="text-lg text-primary-600 mb-12 max-w-2xl mx-auto">
              India's first ambient AI-powered, farmer-first, multilingual agricultural intelligence platform
            </p>
            
            <div className="grid md:grid-cols-3 gap-8 mb-12">
              <div className="card text-center">
                <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold mb-2">Voice Intelligence</h3>
                <p className="text-gray-600">50+ भारतीय भाषाओं में आवाज़ से बातचीत</p>
              </div>
              
              <div className="card text-center">
                <div className="w-16 h-16 bg-success-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-success-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold mb-2">Real-time Prices</h3>
                <p className="text-gray-600">सभी राज्यों की मंडी के लाइव भाव</p>
              </div>
              
              <div className="card text-center">
                <div className="w-16 h-16 bg-warning-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-warning-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold mb-2">Smart Guidance</h3>
                <p className="text-gray-600">एआई-संचालित फसल योजना और सलाह</p>
              </div>
            </div>
            
            <button
              onClick={() => setShowLogin(true)}
              className="btn-primary text-lg px-8 py-3"
            >
              शुरू करें / Get Started
            </button>
          </div>
        </div>
        
        {showLogin && (
          <LoginModal onClose={() => setShowLogin(false)} />
        )}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="container mx-auto px-4 py-6">
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Welcome Section */}
            <div className="card">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                नमस्ते {user?.name}! 🙏
              </h2>
              <p className="text-gray-600">
                आज आपके लिए क्या कर सकते हैं?
              </p>
            </div>
            
            {/* Voice Interface */}
            <VoiceInterface />
            
            {/* Price Discovery */}
            <PriceDiscovery />
            
            {/* Quick Actions */}
            <QuickActions />
          </div>
          
          {/* Sidebar */}
          <div className="space-y-6">
            {/* Market Alerts */}
            <MarketAlerts />
            
            {/* Recent Activity */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">हाल की गतिविधि</h3>
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-success-500 rounded-full"></div>
                  <span className="text-sm text-gray-600">गेहूं की कीमत अपडेट हुई</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-warning-500 rounded-full"></div>
                  <span className="text-sm text-gray-600">मौसम अलर्ट प्राप्त हुआ</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
                  <span className="text-sm text-gray-600">नई फसल सिफारिश</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}