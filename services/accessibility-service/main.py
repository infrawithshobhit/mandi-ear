"""
MANDI EAR™ Accessibility Service
Screen reader support, high-contrast mode, and user experience features
"""

from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager
import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime

from models import (
    AccessibilitySettings, UserPreferences, TutorialProgress,
    OnboardingStep, ScreenReaderContent, HighContrastTheme
)
from accessibility_manager import AccessibilityManager
from tutorial_engine import TutorialEngine
from onboarding_system import OnboardingSystem

logger = structlog.get_logger()

# Global service instances
accessibility_manager: Optional[AccessibilityManager] = None
tutorial_engine: Optional[TutorialEngine] = None
onboarding_system: Optional[OnboardingSystem] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global accessibility_manager, tutorial_engine, onboarding_system
    
    # Startup
    logger.info("Starting Accessibility Service")
    
    accessibility_manager = AccessibilityManager()
    await accessibility_manager.initialize()
    
    tutorial_engine = TutorialEngine()
    await tutorial_engine.initialize()
    
    onboarding_system = OnboardingSystem()
    await onboarding_system.initialize()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Accessibility Service")
    if accessibility_manager:
        await accessibility_manager.shutdown()
    if tutorial_engine:
        await tutorial_engine.shutdown()
    if onboarding_system:
        await onboarding_system.shutdown()

app = FastAPI(
    title="MANDI EAR™ Accessibility Service",
    description="Accessibility features and user experience enhancements",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {
        "service": "Accessibility Service",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Accessibility Settings Endpoints

@app.get("/accessibility/settings/{user_id}")
async def get_accessibility_settings(user_id: str) -> AccessibilitySettings:
    """Get user's accessibility settings"""
    if not accessibility_manager:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        settings = await accessibility_manager.get_user_settings(user_id)
        return settings
    except Exception as e:
        logger.error("Failed to get accessibility settings", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/accessibility/settings/{user_id}")
async def update_accessibility_settings(
    user_id: str, 
    settings: AccessibilitySettings
):
    """Update user's accessibility settings"""
    if not accessibility_manager:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        await accessibility_manager.update_user_settings(user_id, settings)
        return {"message": "Settings updated successfully"}
    except Exception as e:
        logger.error("Failed to update accessibility settings", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/accessibility/screen-reader/{user_id}")
async def get_screen_reader_content(
    user_id: str,
    page: str,
    element_id: Optional[str] = None
) -> ScreenReaderContent:
    """Get screen reader optimized content"""
    if not accessibility_manager:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        content = await accessibility_manager.get_screen_reader_content(
            user_id=user_id,
            page=page,
            element_id=element_id
        )
        return content
    except Exception as e:
        logger.error("Failed to get screen reader content", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/accessibility/high-contrast/{user_id}")
async def get_high_contrast_theme(user_id: str) -> HighContrastTheme:
    """Get high-contrast theme settings"""
    if not accessibility_manager:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        theme = await accessibility_manager.get_high_contrast_theme(user_id)
        return theme
    except Exception as e:
        logger.error("Failed to get high-contrast theme", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/accessibility/high-contrast/{user_id}")
async def update_high_contrast_theme(
    user_id: str,
    theme: HighContrastTheme
):
    """Update high-contrast theme settings"""
    if not accessibility_manager:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        await accessibility_manager.update_high_contrast_theme(user_id, theme)
        return {"message": "Theme updated successfully"}
    except Exception as e:
        logger.error("Failed to update high-contrast theme", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# Tutorial System Endpoints

@app.get("/tutorial/progress/{user_id}")
async def get_tutorial_progress(user_id: str) -> TutorialProgress:
    """Get user's tutorial progress"""
    if not tutorial_engine:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        progress = await tutorial_engine.get_user_progress(user_id)
        return progress
    except Exception as e:
        logger.error("Failed to get tutorial progress", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/tutorial/start/{user_id}")
async def start_tutorial(
    user_id: str,
    tutorial_type: str,
    language: Optional[str] = "en"
):
    """Start a tutorial for the user"""
    if not tutorial_engine:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        tutorial_id = await tutorial_engine.start_tutorial(
            user_id=user_id,
            tutorial_type=tutorial_type,
            language=language
        )
        return {"tutorial_id": tutorial_id, "status": "started"}
    except Exception as e:
        logger.error("Failed to start tutorial", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/tutorial/complete-step/{user_id}")
async def complete_tutorial_step(
    user_id: str,
    tutorial_id: str,
    step_id: str
):
    """Mark a tutorial step as completed"""
    if not tutorial_engine:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        await tutorial_engine.complete_step(
            user_id=user_id,
            tutorial_id=tutorial_id,
            step_id=step_id
        )
        return {"message": "Step completed successfully"}
    except Exception as e:
        logger.error("Failed to complete tutorial step", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/tutorial/next-step/{user_id}")
async def get_next_tutorial_step(
    user_id: str,
    tutorial_id: str
) -> Dict[str, Any]:
    """Get the next tutorial step for the user"""
    if not tutorial_engine:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        next_step = await tutorial_engine.get_next_step(
            user_id=user_id,
            tutorial_id=tutorial_id
        )
        return next_step
    except Exception as e:
        logger.error("Failed to get next tutorial step", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/tutorial/available")
async def get_available_tutorials(language: Optional[str] = "en") -> List[Dict[str, Any]]:
    """Get list of available tutorials"""
    if not tutorial_engine:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        tutorials = await tutorial_engine.get_available_tutorials(language)
        return tutorials
    except Exception as e:
        logger.error("Failed to get available tutorials", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# Onboarding System Endpoints

@app.get("/onboarding/status/{user_id}")
async def get_onboarding_status(user_id: str) -> Dict[str, Any]:
    """Get user's onboarding status"""
    if not onboarding_system:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        status = await onboarding_system.get_user_status(user_id)
        return status
    except Exception as e:
        logger.error("Failed to get onboarding status", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/onboarding/start/{user_id}")
async def start_onboarding(
    user_id: str,
    user_profile: Dict[str, Any],
    language: Optional[str] = "en"
):
    """Start onboarding process for new user"""
    if not onboarding_system:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        onboarding_id = await onboarding_system.start_onboarding(
            user_id=user_id,
            user_profile=user_profile,
            language=language
        )
        return {"onboarding_id": onboarding_id, "status": "started"}
    except Exception as e:
        logger.error("Failed to start onboarding", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/onboarding/complete-step/{user_id}")
async def complete_onboarding_step(
    user_id: str,
    onboarding_id: str,
    step_id: str,
    step_data: Optional[Dict[str, Any]] = None
):
    """Complete an onboarding step"""
    if not onboarding_system:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        await onboarding_system.complete_step(
            user_id=user_id,
            onboarding_id=onboarding_id,
            step_id=step_id,
            step_data=step_data
        )
        return {"message": "Onboarding step completed"}
    except Exception as e:
        logger.error("Failed to complete onboarding step", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/onboarding/next-step/{user_id}")
async def get_next_onboarding_step(
    user_id: str,
    onboarding_id: str
) -> OnboardingStep:
    """Get the next onboarding step"""
    if not onboarding_system:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        next_step = await onboarding_system.get_next_step(
            user_id=user_id,
            onboarding_id=onboarding_id
        )
        return next_step
    except Exception as e:
        logger.error("Failed to get next onboarding step", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/onboarding/skip/{user_id}")
async def skip_onboarding(user_id: str, onboarding_id: str):
    """Skip the onboarding process"""
    if not onboarding_system:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        await onboarding_system.skip_onboarding(
            user_id=user_id,
            onboarding_id=onboarding_id
        )
        return {"message": "Onboarding skipped"}
    except Exception as e:
        logger.error("Failed to skip onboarding", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# User Experience Enhancement Endpoints

@app.get("/ux/preferences/{user_id}")
async def get_user_preferences(user_id: str) -> UserPreferences:
    """Get user's UX preferences"""
    if not accessibility_manager:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        preferences = await accessibility_manager.get_user_preferences(user_id)
        return preferences
    except Exception as e:
        logger.error("Failed to get user preferences", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/ux/preferences/{user_id}")
async def update_user_preferences(
    user_id: str,
    preferences: UserPreferences
):
    """Update user's UX preferences"""
    if not accessibility_manager:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        await accessibility_manager.update_user_preferences(user_id, preferences)
        return {"message": "Preferences updated successfully"}
    except Exception as e:
        logger.error("Failed to update user preferences", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/ux/help-context")
async def get_contextual_help(
    page: str,
    element: Optional[str] = None,
    language: Optional[str] = "en"
) -> Dict[str, Any]:
    """Get contextual help for UI elements"""
    if not tutorial_engine:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        help_content = await tutorial_engine.get_contextual_help(
            page=page,
            element=element,
            language=language
        )
        return help_content
    except Exception as e:
        logger.error("Failed to get contextual help", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/ux/feedback")
async def submit_user_feedback(
    user_id: str,
    feedback_type: str,
    content: str,
    page: Optional[str] = None,
    rating: Optional[int] = None
):
    """Submit user feedback for UX improvements"""
    if not accessibility_manager:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        feedback_id = await accessibility_manager.submit_feedback(
            user_id=user_id,
            feedback_type=feedback_type,
            content=content,
            page=page,
            rating=rating
        )
        return {"feedback_id": feedback_id, "message": "Feedback submitted successfully"}
    except Exception as e:
        logger.error("Failed to submit feedback", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/ux/keyboard-shortcuts")
async def get_keyboard_shortcuts(language: Optional[str] = "en") -> Dict[str, Any]:
    """Get keyboard shortcuts for accessibility"""
    if not accessibility_manager:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        shortcuts = await accessibility_manager.get_keyboard_shortcuts(language)
        return shortcuts
    except Exception as e:
        logger.error("Failed to get keyboard shortcuts", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/ux/voice-navigation")
async def process_voice_navigation(
    user_id: str,
    voice_command: str,
    current_page: str
) -> Dict[str, Any]:
    """Process voice navigation commands for accessibility"""
    if not accessibility_manager:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        navigation_result = await accessibility_manager.process_voice_navigation(
            user_id=user_id,
            voice_command=voice_command,
            current_page=current_page
        )
        return navigation_result
    except Exception as e:
        logger.error("Failed to process voice navigation", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")