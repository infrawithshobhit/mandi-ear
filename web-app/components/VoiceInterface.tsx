'use client';

import { useState, useRef, useEffect } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';

export default function VoiceInterface() {
  const { language, t } = useLanguage();
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');
  const [error, setError] = useState('');
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      setError('');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await processAudio(audioBlob);
        
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      setError('माइक्रोफोन एक्सेस नहीं मिल सका। कृपया अनुमति दें।');
      console.error('Error accessing microphone:', err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsProcessing(true);
    }
  };

  const processAudio = async (audioBlob: Blob) => {
    try {
      // Convert blob to base64
      const reader = new FileReader();
      reader.onloadend = async () => {
        const base64Audio = reader.result as string;
        const audioData = base64Audio.split(',')[1]; // Remove data:audio/wav;base64, prefix

        // Send to voice processing API
        const response = await fetch('/api/v1/voice/transcribe', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          },
          body: JSON.stringify({
            audio_data: audioData,
            language: language,
          }),
        });

        if (!response.ok) {
          throw new Error('Voice processing failed');
        }

        const result = await response.json();
        setTranscript(result.transcript || '');
        
        // Process the transcript to get AI response
        if (result.transcript) {
          await getAIResponse(result.transcript);
        }
      };
      
      reader.readAsDataURL(audioBlob);
    } catch (err) {
      setError('आवाज़ प्रोसेसिंग में त्रुटि हुई। कृपया फिर से कोशिश करें।');
      console.error('Error processing audio:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  const getAIResponse = async (text: string) => {
    try {
      // This would integrate with your AI service to process the query
      // For now, we'll simulate a response based on common queries
      
      const lowerText = text.toLowerCase();
      let aiResponse = '';

      if (lowerText.includes('भाव') || lowerText.includes('price') || lowerText.includes('rate')) {
        aiResponse = 'आज गेहूं का भाव ₹2,200 प्रति क्विंटल है। यह कल से ₹50 बढ़ा है।';
      } else if (lowerText.includes('मौसम') || lowerText.includes('weather')) {
        aiResponse = 'आज मौसम साफ है। तापमान 28°C है। अगले 3 दिनों में बारिश की संभावना है।';
      } else if (lowerText.includes('फसल') || lowerText.includes('crop')) {
        aiResponse = 'इस सीजन में आपके क्षेत्र के लिए धान और मक्का की खेती अच्छी रहेगी।';
      } else {
        aiResponse = 'मैं आपकी मदद करने के लिए यहाँ हूँ। कृपया मंडी भाव, मौसम या फसल के बारे में पूछें।';
      }

      setResponse(aiResponse);
      
      // Convert response to speech
      await speakResponse(aiResponse);
    } catch (err) {
      console.error('Error getting AI response:', err);
    }
  };

  const speakResponse = async (text: string) => {
    try {
      const response = await fetch('/api/v1/voice/synthesize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
        body: JSON.stringify({
          text: text,
          language: language,
        }),
      });

      if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play();
      }
    } catch (err) {
      console.error('Error synthesizing speech:', err);
    }
  };

  const clearConversation = () => {
    setTranscript('');
    setResponse('');
    setError('');
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">आवाज़ सहायक</h3>
        {(transcript || response) && (
          <button
            onClick={clearConversation}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            साफ़ करें
          </button>
        )}
      </div>

      {/* Voice Button */}
      <div className="flex flex-col items-center mb-6">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isProcessing}
          className={`voice-button ${isRecording ? 'recording' : ''} ${
            isProcessing ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {isProcessing ? (
            <svg className="w-6 h-6 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          ) : isRecording ? (
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6 6h12v12H6z" />
            </svg>
          ) : (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          )}
        </button>
        
        <p className="text-sm text-gray-600 mt-3 text-center">
          {isRecording
            ? 'बोलें... रुकने के लिए क्लिक करें'
            : isProcessing
            ? 'प्रोसेसिंग हो रही है...'
            : 'बोलने के लिए क्लिक करें'
          }
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-error-50 border border-error-200 rounded-lg p-4 mb-4">
          <p className="text-error-700 text-sm">{error}</p>
        </div>
      )}

      {/* Transcript */}
      {transcript && (
        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">आपने कहा:</h4>
          <p className="text-gray-900">{transcript}</p>
        </div>
      )}

      {/* AI Response */}
      {response && (
        <div className="bg-primary-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-primary-700 mb-2">जवाब:</h4>
          <p className="text-primary-900">{response}</p>
        </div>
      )}

      {/* Quick Suggestions */}
      {!transcript && !response && (
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">कुछ इस तरह पूछें:</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {[
              'आज गेहूं का भाव क्या है?',
              'मौसम कैसा रहेगा?',
              'कौन सी फसल बोऊं?',
              'MSP क्या है?',
            ].map((suggestion, index) => (
              <button
                key={index}
                onClick={() => setTranscript(suggestion)}
                className="text-left p-3 text-sm text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded-lg border border-gray-200 hover:border-primary-200 transition-colors"
              >
                "{suggestion}"
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}