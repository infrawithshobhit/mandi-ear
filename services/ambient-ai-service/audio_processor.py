"""
Audio Processing Pipeline for MANDI EAR™ Ambient AI
Handles audio stream capture, noise filtering, and speaker boundary detection
"""

import numpy as np
import librosa
import soundfile as sf
import webrtcvad
from scipy import signal
from typing import List, Tuple, Optional, Generator
import structlog
from dataclasses import dataclass
from enum import Enum
import io

logger = structlog.get_logger()

class AudioQuality(Enum):
    HIGH = "high"
    MEDIUM = "medium" 
    LOW = "low"
    POOR = "poor"

@dataclass
class AudioSegment:
    """Represents a processed audio segment"""
    id: str
    start_time: float
    end_time: float
    audio_data: np.ndarray
    sample_rate: int
    speaker_id: Optional[str] = None
    quality: AudioQuality = AudioQuality.MEDIUM
    noise_level: float = 0.0
    confidence: float = 1.0

@dataclass
class SpeakerBoundary:
    """Represents detected speaker change points"""
    timestamp: float
    speaker_id: str
    confidence: float

class AudioProcessor:
    """
    Core audio processing pipeline for ambient AI
    Handles noise filtering, segmentation, and speaker detection
    """
    
    def __init__(self, 
                 sample_rate: int = 16000,
                 frame_duration_ms: int = 30,
                 noise_threshold: float = 0.01,
                 min_segment_duration: float = 1.0):
        """
        Initialize audio processor
        
        Args:
            sample_rate: Target sample rate for processing
            frame_duration_ms: Frame duration for VAD processing
            noise_threshold: Threshold for noise detection
            min_segment_duration: Minimum segment duration in seconds
        """
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.noise_threshold = noise_threshold
        self.min_segment_duration = min_segment_duration
        
        # Initialize VAD (Voice Activity Detection)
        self.vad = webrtcvad.Vad(2)  # Aggressiveness level 2
        
        # Frame size for VAD
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        
        logger.info("AudioProcessor initialized", 
                   sample_rate=sample_rate,
                   frame_duration_ms=frame_duration_ms)
    
    def capture_audio_stream(self, audio_data: bytes) -> np.ndarray:
        """
        Capture and preprocess audio stream
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Preprocessed audio array
        """
        try:
            # Convert bytes to numpy array
            audio_array, sr = sf.read(io.BytesIO(audio_data))
            
            # Resample if necessary
            if sr != self.sample_rate:
                audio_array = librosa.resample(audio_array, orig_sr=sr, target_sr=self.sample_rate)
            
            # Ensure mono audio
            if len(audio_array.shape) > 1:
                audio_array = librosa.to_mono(audio_array)
            
            # Normalize audio
            audio_array = librosa.util.normalize(audio_array)
            
            logger.debug("Audio stream captured", 
                        duration=len(audio_array) / self.sample_rate,
                        sample_rate=self.sample_rate)
            
            return audio_array
            
        except Exception as e:
            logger.error("Failed to capture audio stream", error=str(e))
            raise
    
    def reduce_noise(self, audio: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Apply noise reduction and audio enhancement
        
        Args:
            audio: Input audio array
            
        Returns:
            Tuple of (enhanced_audio, noise_level)
        """
        try:
            # Estimate noise level from first 0.5 seconds
            noise_sample_size = int(0.5 * self.sample_rate)
            noise_sample = audio[:min(noise_sample_size, len(audio))]
            noise_level = np.std(noise_sample)
            
            # Apply spectral subtraction for noise reduction
            # Get STFT
            stft = librosa.stft(audio, n_fft=2048, hop_length=512)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Estimate noise spectrum from first few frames
            noise_frames = min(10, magnitude.shape[1])
            noise_spectrum = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)
            
            # Apply spectral subtraction
            alpha = 2.0  # Over-subtraction factor
            enhanced_magnitude = magnitude - alpha * noise_spectrum
            
            # Ensure non-negative values
            enhanced_magnitude = np.maximum(enhanced_magnitude, 0.1 * magnitude)
            
            # Reconstruct audio
            enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
            enhanced_audio = librosa.istft(enhanced_stft, hop_length=512)
            
            # Apply high-pass filter to remove low-frequency noise
            sos = signal.butter(4, 300, btype='high', fs=self.sample_rate, output='sos')
            enhanced_audio = signal.sosfilt(sos, enhanced_audio)
            
            logger.debug("Noise reduction applied", 
                        noise_level=float(noise_level),
                        enhancement_ratio=float(np.std(enhanced_audio) / max(noise_level, 1e-6)))
            
            return enhanced_audio, float(noise_level)
            
        except Exception as e:
            logger.error("Failed to reduce noise", error=str(e))
            return audio, float(np.std(audio))
    
    def detect_voice_activity(self, audio: np.ndarray) -> List[Tuple[float, float]]:
        """
        Detect voice activity segments using VAD
        
        Args:
            audio: Input audio array
            
        Returns:
            List of (start_time, end_time) tuples for voice segments
        """
        try:
            # Convert to 16-bit PCM for VAD
            audio_16bit = (audio * 32767).astype(np.int16)
            
            voice_segments = []
            frame_duration = self.frame_duration_ms / 1000.0
            
            # Process audio in frames
            is_speech = False
            segment_start = None
            
            for i in range(0, len(audio_16bit), self.frame_size):
                frame = audio_16bit[i:i + self.frame_size]
                
                # Pad frame if necessary
                if len(frame) < self.frame_size:
                    frame = np.pad(frame, (0, self.frame_size - len(frame)))
                
                # Convert to bytes for VAD
                frame_bytes = frame.tobytes()
                
                # Check if frame contains speech
                try:
                    contains_speech = self.vad.is_speech(frame_bytes, self.sample_rate)
                except:
                    contains_speech = False
                
                timestamp = i / self.sample_rate
                
                if contains_speech and not is_speech:
                    # Start of speech segment
                    segment_start = timestamp
                    is_speech = True
                elif not contains_speech and is_speech:
                    # End of speech segment
                    if segment_start is not None:
                        segment_duration = timestamp - segment_start
                        if segment_duration >= self.min_segment_duration:
                            voice_segments.append((segment_start, timestamp))
                    is_speech = False
            
            # Handle case where audio ends during speech
            if is_speech and segment_start is not None:
                final_timestamp = len(audio) / self.sample_rate
                if final_timestamp - segment_start >= self.min_segment_duration:
                    voice_segments.append((segment_start, final_timestamp))
            
            logger.debug("Voice activity detected", 
                        segments_count=len(voice_segments),
                        total_speech_duration=sum(end - start for start, end in voice_segments))
            
            return voice_segments
            
        except Exception as e:
            logger.error("Failed to detect voice activity", error=str(e))
            return []
    
    def detect_speaker_boundaries(self, audio: np.ndarray) -> List[SpeakerBoundary]:
        """
        Detect speaker change points using spectral features
        
        Args:
            audio: Input audio array
            
        Returns:
            List of speaker boundaries
        """
        try:
            # Extract MFCC features for speaker change detection
            mfccs = librosa.feature.mfcc(y=audio, sr=self.sample_rate, n_mfcc=13)
            
            # Calculate frame-to-frame distance
            frame_distances = []
            for i in range(1, mfccs.shape[1]):
                dist = np.linalg.norm(mfccs[:, i] - mfccs[:, i-1])
                frame_distances.append(dist)
            
            frame_distances = np.array(frame_distances)
            
            # Find peaks in distance (potential speaker changes)
            # Use adaptive threshold based on mean and std
            threshold = np.mean(frame_distances) + 2 * np.std(frame_distances)
            
            # Find peaks above threshold
            peaks, _ = signal.find_peaks(frame_distances, height=threshold, distance=20)
            
            # Convert frame indices to timestamps
            hop_length = 512
            boundaries = []
            
            for i, peak_idx in enumerate(peaks):
                timestamp = (peak_idx * hop_length) / self.sample_rate
                confidence = min(frame_distances[peak_idx] / threshold, 1.0)
                
                boundary = SpeakerBoundary(
                    timestamp=timestamp,
                    speaker_id=f"speaker_{i % 4}",  # Simple speaker ID assignment
                    confidence=confidence
                )
                boundaries.append(boundary)
            
            logger.debug("Speaker boundaries detected", 
                        boundaries_count=len(boundaries))
            
            return boundaries
            
        except Exception as e:
            logger.error("Failed to detect speaker boundaries", error=str(e))
            return []
    
    def segment_audio(self, audio: np.ndarray, enhanced_audio: np.ndarray, 
                     noise_level: float) -> List[AudioSegment]:
        """
        Segment audio into processable chunks
        
        Args:
            audio: Original audio array
            enhanced_audio: Noise-reduced audio array
            noise_level: Detected noise level
            
        Returns:
            List of audio segments
        """
        try:
            # Detect voice activity
            voice_segments = self.detect_voice_activity(enhanced_audio)
            
            # Detect speaker boundaries
            speaker_boundaries = self.detect_speaker_boundaries(enhanced_audio)
            
            # Create audio segments
            segments = []
            
            for i, (start_time, end_time) in enumerate(voice_segments):
                start_sample = int(start_time * self.sample_rate)
                end_sample = int(end_time * self.sample_rate)
                
                # Extract segment audio
                segment_audio = enhanced_audio[start_sample:end_sample]
                
                # Determine audio quality based on noise level and duration
                duration = end_time - start_time
                quality = self._assess_audio_quality(noise_level, duration)
                
                # Find relevant speaker for this segment
                speaker_id = self._find_speaker_for_segment(start_time, end_time, speaker_boundaries)
                
                # Calculate confidence based on quality and duration
                confidence = self._calculate_segment_confidence(quality, duration, noise_level)
                
                segment = AudioSegment(
                    id=f"segment_{i:04d}",
                    start_time=start_time,
                    end_time=end_time,
                    audio_data=segment_audio,
                    sample_rate=self.sample_rate,
                    speaker_id=speaker_id,
                    quality=quality,
                    noise_level=noise_level,
                    confidence=confidence
                )
                
                segments.append(segment)
            
            logger.info("Audio segmentation completed", 
                       segments_count=len(segments),
                       total_duration=sum(s.end_time - s.start_time for s in segments))
            
            return segments
            
        except Exception as e:
            logger.error("Failed to segment audio", error=str(e))
            return []
    
    def _assess_audio_quality(self, noise_level: float, duration: float) -> AudioQuality:
        """Assess audio quality based on noise level and duration"""
        if noise_level < 0.01 and duration > 3.0:
            return AudioQuality.HIGH
        elif noise_level < 0.05 and duration > 1.5:
            return AudioQuality.MEDIUM
        elif noise_level < 0.1 and duration > 0.5:
            return AudioQuality.LOW
        else:
            return AudioQuality.POOR
    
    def _find_speaker_for_segment(self, start_time: float, end_time: float, 
                                 boundaries: List[SpeakerBoundary]) -> Optional[str]:
        """Find the most likely speaker for a given segment"""
        if not boundaries:
            return "speaker_0"
        
        # Find the boundary closest to the segment start
        closest_boundary = None
        min_distance = float('inf')
        
        for boundary in boundaries:
            if boundary.timestamp <= start_time:
                distance = start_time - boundary.timestamp
                if distance < min_distance:
                    min_distance = distance
                    closest_boundary = boundary
        
        return closest_boundary.speaker_id if closest_boundary else "speaker_0"
    
    def _calculate_segment_confidence(self, quality: AudioQuality, 
                                    duration: float, noise_level: float) -> float:
        """Calculate confidence score for a segment"""
        base_confidence = {
            AudioQuality.HIGH: 0.95,
            AudioQuality.MEDIUM: 0.80,
            AudioQuality.LOW: 0.60,
            AudioQuality.POOR: 0.30
        }[quality]
        
        # Adjust for duration (longer segments are more reliable)
        duration_factor = min(duration / 5.0, 1.0)  # Max boost at 5 seconds
        
        # Adjust for noise level
        noise_factor = max(0.1, 1.0 - noise_level * 10)
        
        confidence = base_confidence * duration_factor * noise_factor
        return min(max(confidence, 0.1), 1.0)
    
    def process_audio_stream(self, audio_data: bytes) -> List[AudioSegment]:
        """
        Complete audio processing pipeline
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            List of processed audio segments
        """
        try:
            logger.info("Starting audio processing pipeline")
            
            # Step 1: Capture and preprocess audio
            audio = self.capture_audio_stream(audio_data)
            
            # Step 2: Apply noise reduction
            enhanced_audio, noise_level = self.reduce_noise(audio)
            
            # Step 3: Segment audio
            segments = self.segment_audio(audio, enhanced_audio, noise_level)
            
            logger.info("Audio processing pipeline completed", 
                       segments_count=len(segments),
                       average_quality=np.mean([s.confidence for s in segments]) if segments else 0)
            
            return segments
            
        except Exception as e:
            logger.error("Audio processing pipeline failed", error=str(e))
            raise