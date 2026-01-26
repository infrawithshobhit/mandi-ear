"""
Conversation Context Management for MANDI EAR™
Maintains session state and conversation history
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import os
import sys

# Add the current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from language_detector import LanguageCode
except ImportError:
    # Fallback for when running tests
    class LanguageCode(str, Enum):
        HINDI = "hi"
        ENGLISH = "en"
        BENGALI = "bn"
        TELUGU = "te"
        MARATHI = "mr"
        TAMIL = "ta"
        GUJARATI = "gu"
        URDU = "ur"
        KANNADA = "kn"
        ODIA = "or"
        MALAYALAM = "ml"
        PUNJABI = "pa"
        ASSAMESE = "as"
        MAITHILI = "mai"
        SANTALI = "sat"
        KASHMIRI = "ks"
        NEPALI = "ne"
        SINDHI = "sd"
        KONKANI = "gom"
        DOGRI = "doi"
        MANIPURI = "mni"
        BODO = "brx"
        SANTHALI = "sat"

logger = logging.getLogger(__name__)

class InteractionType(str, Enum):
    """Types of user interactions"""
    VOICE_QUERY = "voice_query"
    VOICE_RESPONSE = "voice_response"
    TEXT_INPUT = "text_input"
    SYSTEM_MESSAGE = "system_message"

@dataclass
class Interaction:
    """Single interaction in conversation"""
    id: str
    type: InteractionType
    content: str
    language: LanguageCode
    timestamp: datetime
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserContext:
    """User context information"""
    user_id: str
    preferred_language: LanguageCode
    location: Optional[Dict[str, Any]] = None
    farmer_profile: Optional[Dict[str, Any]] = None
    cultural_preferences: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConversationSession:
    """Complete conversation session"""
    session_id: str
    user_context: UserContext
    interactions: List[Interaction] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    session_metadata: Dict[str, Any] = field(default_factory=dict)

class ConversationContextManager:
    """Manages conversation context and session state"""
    
    def __init__(self, session_timeout_minutes: int = 10):
        self.sessions: Dict[str, ConversationSession] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task for session cleanup"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
    
    async def _cleanup_expired_sessions(self):
        """Background task to clean up expired sessions"""
        while True:
            try:
                current_time = datetime.now()
                expired_sessions = [
                    session_id for session_id, session in self.sessions.items()
                    if current_time - session.last_activity > self.session_timeout
                ]
                
                for session_id in expired_sessions:
                    await self.end_session(session_id)
                
                # Run cleanup every minute
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
                await asyncio.sleep(60)
    
    async def create_session(
        self, 
        session_id: str, 
        user_context: UserContext
    ) -> ConversationSession:
        """Create a new conversation session"""
        session = ConversationSession(
            session_id=session_id,
            user_context=user_context
        )
        
        self.sessions[session_id] = session
        logger.info(f"Created new session: {session_id}")
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get existing session by ID"""
        session = self.sessions.get(session_id)
        if session and session.is_active:
            session.last_activity = datetime.now()
            return session
        return None
    
    async def add_interaction(
        self, 
        session_id: str, 
        interaction: Interaction
    ) -> bool:
        """Add interaction to session"""
        session = await self.get_session(session_id)
        if not session:
            logger.warning(f"Session not found: {session_id}")
            return False
        
        session.interactions.append(interaction)
        session.last_activity = datetime.now()
        
        # Limit interaction history to prevent memory issues
        if len(session.interactions) > 50:
            session.interactions = session.interactions[-40:]  # Keep last 40
        
        logger.debug(f"Added interaction to session {session_id}: {interaction.type}")
        return True
    
    async def get_conversation_history(
        self, 
        session_id: str, 
        limit: Optional[int] = None
    ) -> List[Interaction]:
        """Get conversation history for session"""
        session = await self.get_session(session_id)
        if not session:
            return []
        
        interactions = session.interactions
        if limit:
            interactions = interactions[-limit:]
        
        return interactions
    
    async def get_context_summary(self, session_id: str) -> Dict[str, Any]:
        """Get contextual summary of conversation"""
        session = await self.get_session(session_id)
        if not session:
            return {}
        
        # Analyze recent interactions for context
        recent_interactions = session.interactions[-10:]  # Last 10 interactions
        
        # Extract key topics and entities
        topics = set()
        languages_used = set()
        interaction_types = set()
        
        for interaction in recent_interactions:
            languages_used.add(interaction.language.value)
            interaction_types.add(interaction.type.value)
            
            # Simple keyword extraction for agricultural topics
            content_lower = interaction.content.lower()
            agricultural_keywords = [
                "price", "mandi", "crop", "farmer", "sell", "buy", 
                "wheat", "rice", "cotton", "sugarcane", "market"
            ]
            
            for keyword in agricultural_keywords:
                if keyword in content_lower:
                    topics.add(keyword)
        
        return {
            "session_id": session_id,
            "user_preferred_language": session.user_context.preferred_language.value,
            "languages_used": list(languages_used),
            "interaction_types": list(interaction_types),
            "topics_discussed": list(topics),
            "interaction_count": len(session.interactions),
            "session_duration_minutes": (
                datetime.now() - session.created_at
            ).total_seconds() / 60,
            "last_activity": session.last_activity.isoformat()
        }
    
    async def update_user_context(
        self, 
        session_id: str, 
        context_updates: Dict[str, Any]
    ) -> bool:
        """Update user context in session"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        # Update user context fields
        if "preferred_language" in context_updates:
            try:
                session.user_context.preferred_language = LanguageCode(
                    context_updates["preferred_language"]
                )
            except ValueError:
                logger.warning(f"Invalid language code: {context_updates['preferred_language']}")
        
        if "location" in context_updates:
            session.user_context.location = context_updates["location"]
        
        if "farmer_profile" in context_updates:
            session.user_context.farmer_profile = context_updates["farmer_profile"]
        
        if "cultural_preferences" in context_updates:
            session.user_context.cultural_preferences.update(
                context_updates["cultural_preferences"]
            )
        
        session.last_activity = datetime.now()
        logger.info(f"Updated context for session: {session_id}")
        return True
    
    async def end_session(self, session_id: str) -> bool:
        """End and cleanup session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.is_active = False
            
            # Archive session data if needed
            await self._archive_session(session)
            
            # Remove from active sessions
            del self.sessions[session_id]
            logger.info(f"Ended session: {session_id}")
            return True
        
        return False
    
    async def _archive_session(self, session: ConversationSession):
        """Archive session data for analytics"""
        try:
            # In a real implementation, this would save to database
            # For now, just log the session summary
            summary = {
                "session_id": session.session_id,
                "user_id": session.user_context.user_id,
                "duration_minutes": (
                    session.last_activity - session.created_at
                ).total_seconds() / 60,
                "interaction_count": len(session.interactions),
                "languages_used": list(set(
                    interaction.language.value for interaction in session.interactions
                ))
            }
            
            logger.info(f"Archived session: {json.dumps(summary)}")
            
        except Exception as e:
            logger.error(f"Session archival failed: {e}")
    
    async def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return len([s for s in self.sessions.values() if s.is_active])
    
    async def cleanup_all_sessions(self):
        """Cleanup all sessions (for shutdown)"""
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            await self.end_session(session_id)
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about current sessions"""
        active_sessions = [s for s in self.sessions.values() if s.is_active]
        
        if not active_sessions:
            return {
                "total_sessions": 0,
                "active_sessions": 0,
                "average_duration_minutes": 0,
                "total_interactions": 0
            }
        
        total_interactions = sum(len(s.interactions) for s in active_sessions)
        avg_duration = sum(
            (datetime.now() - s.created_at).total_seconds() / 60 
            for s in active_sessions
        ) / len(active_sessions)
        
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": len(active_sessions),
            "average_duration_minutes": round(avg_duration, 2),
            "total_interactions": total_interactions
        }