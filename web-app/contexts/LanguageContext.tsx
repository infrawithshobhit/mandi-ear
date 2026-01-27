'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

interface LanguageContextType {
  language: string;
  setLanguage: (lang: string) => void;
  t: (key: string) => string;
  isRTL: boolean;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

// Translations
const translations: Record<string, Record<string, string>> = {
  hi: {
    welcome: 'स्वागत है',
    home: 'होम',
    prices: 'भाव',
    voice: 'आवाज़',
    profile: 'प्रोफाइल',
    login: 'लॉगिन',
    logout: 'लॉगआउट',
    search: 'खोजें',
    loading: 'लोड हो रहा है...',
    error: 'त्रुटि',
    success: 'सफल',
    cancel: 'रद्द करें',
    save: 'सेव करें',
    edit: 'संपादित करें',
    delete: 'हटाएं',
    confirm: 'पुष्टि करें',
    back: 'वापस',
    next: 'आगे',
    previous: 'पिछला',
    submit: 'जमा करें',
    reset: 'रीसेट करें',
    close: 'बंद करें',
    open: 'खोलें',
    select: 'चुनें',
    clear: 'साफ़ करें',
    refresh: 'रिफ्रेश करें',
    update: 'अपडेट करें',
    settings: 'सेटिंग्स',
    help: 'सहायता',
    about: 'के बारे में',
    contact: 'संपर्क',
    feedback: 'फीडबैक',
    share: 'साझा करें',
    download: 'डाउनलोड करें',
    upload: 'अपलोड करें',
    copy: 'कॉपी करें',
    paste: 'पेस्ट करें',
    cut: 'कट करें',
    undo: 'पूर्ववत करें',
    redo: 'फिर से करें',
  },
  en: {
    welcome: 'Welcome',
    home: 'Home',
    prices: 'Prices',
    voice: 'Voice',
    profile: 'Profile',
    login: 'Login',
    logout: 'Logout',
    search: 'Search',
    loading: 'Loading...',
    error: 'Error',
    success: 'Success',
    cancel: 'Cancel',
    save: 'Save',
    edit: 'Edit',
    delete: 'Delete',
    confirm: 'Confirm',
    back: 'Back',
    next: 'Next',
    previous: 'Previous',
    submit: 'Submit',
    reset: 'Reset',
    close: 'Close',
    open: 'Open',
    select: 'Select',
    clear: 'Clear',
    refresh: 'Refresh',
    update: 'Update',
    settings: 'Settings',
    help: 'Help',
    about: 'About',
    contact: 'Contact',
    feedback: 'Feedback',
    share: 'Share',
    download: 'Download',
    upload: 'Upload',
    copy: 'Copy',
    paste: 'Paste',
    cut: 'Cut',
    undo: 'Undo',
    redo: 'Redo',
  },
  ta: {
    welcome: 'வரவேற்கிறோம்',
    home: 'முகப்பு',
    prices: 'விலைகள்',
    voice: 'குரல்',
    profile: 'சுயவிவரம்',
    login: 'உள்நுழைய',
    logout: 'வெளியேறு',
    search: 'தேடு',
    loading: 'ஏற்றுகிறது...',
    error: 'பிழை',
    success: 'வெற்றி',
    cancel: 'ரத்து செய்',
    save: 'சேமி',
    edit: 'திருத்து',
    delete: 'நீக்கு',
    confirm: 'உறுதிப்படுத்து',
    back: 'பின்',
    next: 'அடுத்து',
    previous: 'முந்தைய',
    submit: 'சமர்ப்பி',
    reset: 'மீட்டமை',
    close: 'மூடு',
    open: 'திற',
    select: 'தேர்ந்தெடு',
    clear: 'அழி',
    refresh: 'புதுப்பி',
    update: 'புதுப்பி',
    settings: 'அமைப்புகள்',
    help: 'உதவி',
    about: 'பற்றி',
    contact: 'தொடர்பு',
    feedback: 'கருத்து',
    share: 'பகிர்',
    download: 'பதிவிறக்கு',
    upload: 'பதிவேற்று',
    copy: 'நகலெடு',
    paste: 'ஒட்டு',
    cut: 'வெட்டு',
    undo: 'செயல்தவிர்',
    redo: 'மீண்டும் செய்',
  },
};

const RTL_LANGUAGES = ['ar', 'ur', 'fa'];

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState('hi');

  const isRTL = RTL_LANGUAGES.includes(language);

  useEffect(() => {
    // Load saved language from localStorage
    const savedLanguage = localStorage.getItem('preferred_language');
    if (savedLanguage && translations[savedLanguage]) {
      setLanguageState(savedLanguage);
    }
  }, []);

  const setLanguage = (lang: string) => {
    if (translations[lang]) {
      setLanguageState(lang);
      localStorage.setItem('preferred_language', lang);
      
      // Update document direction for RTL languages
      document.documentElement.dir = RTL_LANGUAGES.includes(lang) ? 'rtl' : 'ltr';
      document.documentElement.lang = lang;
    }
  };

  const t = (key: string): string => {
    return translations[language]?.[key] || translations['en']?.[key] || key;
  };

  const value = {
    language,
    setLanguage,
    t,
    isRTL,
  };

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}