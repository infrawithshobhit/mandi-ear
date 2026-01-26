"""
Onboarding System for new user guidance and setup
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog
import uuid

from models import (
    OnboardingFlow, OnboardingStep, OnboardingProgress, OnboardingStepType,
    AccessibilitySettings, UserPreferences
)

logger = structlog.get_logger()

class OnboardingSystem:
    """Manages user onboarding process"""
    
    def __init__(self):
        self.onboarding_flows: Dict[str, OnboardingFlow] = {}
        self.user_progress: Dict[str, OnboardingProgress] = {}
        self.active_onboardings: Dict[str, str] = {}  # user_id -> onboarding_id
    
    async def initialize(self):
        """Initialize the onboarding system"""
        try:
            await self._load_default_onboarding_flows()
            logger.info("Onboarding system initialized")
        except Exception as e:
            logger.error("Failed to initialize onboarding system", error=str(e))
            raise
    
    async def shutdown(self):
        """Shutdown the onboarding system"""
        logger.info("Onboarding system shutdown")
    
    async def start_onboarding(
        self, 
        user_id: str, 
        user_profile: Dict[str, Any], 
        language: str = "en"
    ) -> str:
        """Start onboarding process for new user"""
        try:
            # Determine appropriate onboarding flow based on user profile
            flow_id = self._determine_onboarding_flow(user_profile)
            
            if flow_id not in self.onboarding_flows:
                raise ValueError(f"Onboarding flow not found: {flow_id}")
            
            onboarding_id = str(uuid.uuid4())
            
            # Create progress tracking
            progress = OnboardingProgress(
                user_id=user_id,
                onboarding_id=onboarding_id,
                flow_id=flow_id,
                started_at=datetime.now(),
                personalization_data=user_profile
            )
            
            # Store progress
            self.user_progress[onboarding_id] = progress
            self.active_onboardings[user_id] = onboarding_id
            
            logger.info("Onboarding started", 
                       user_id=user_id, 
                       onboarding_id=onboarding_id,
                       flow_id=flow_id)
            
            return onboarding_id
            
        except Exception as e:
            logger.error("Failed to start onboarding", error=str(e))
            raise
    
    async def get_user_status(self, user_id: str) -> Dict[str, Any]:
        """Get user's onboarding status"""
        if user_id not in self.active_onboardings:
            return {
                "onboarding_active": False,
                "completed": True,
                "message": "No active onboarding"
            }
        
        onboarding_id = self.active_onboardings[user_id]
        progress = self.user_progress.get(onboarding_id)
        
        if not progress:
            return {
                "onboarding_active": False,
                "completed": False,
                "error": "Onboarding progress not found"
            }
        
        flow = self.onboarding_flows[progress.flow_id]
        
        return {
            "onboarding_active": True,
            "onboarding_id": onboarding_id,
            "flow_id": progress.flow_id,
            "flow_title": flow.title,
            "current_step": progress.current_step,
            "total_steps": len(flow.steps),
            "completion_percentage": progress.completion_percentage,
            "completed": progress.completed_at is not None,
            "skipped": progress.skipped,
            "started_at": progress.started_at.isoformat()
        }
    
    async def get_next_step(self, user_id: str, onboarding_id: str) -> OnboardingStep:
        """Get the next onboarding step"""
        try:
            if onboarding_id not in self.user_progress:
                raise ValueError("Onboarding progress not found")
            
            progress = self.user_progress[onboarding_id]
            flow = self.onboarding_flows[progress.flow_id]
            
            # Check if onboarding is completed
            if progress.completed_at:
                raise ValueError("Onboarding already completed")
            
            # Find next step
            if progress.current_step >= len(flow.steps):
                # Complete onboarding
                await self._complete_onboarding(onboarding_id)
                raise ValueError("Onboarding completed")
            
            current_step = flow.steps[progress.current_step]
            
            # Personalize step based on user data
            personalized_step = await self._personalize_step(current_step, progress.personalization_data)
            
            return personalized_step
            
        except Exception as e:
            logger.error("Failed to get next onboarding step", error=str(e))
            raise
    
    async def complete_step(
        self, 
        user_id: str, 
        onboarding_id: str, 
        step_id: str,
        step_data: Optional[Dict[str, Any]] = None
    ):
        """Complete an onboarding step"""
        try:
            if onboarding_id not in self.user_progress:
                raise ValueError("Onboarding progress not found")
            
            progress = self.user_progress[onboarding_id]
            flow = self.onboarding_flows[progress.flow_id]
            
            # Validate step
            if progress.current_step >= len(flow.steps):
                raise ValueError("No more steps to complete")
            
            current_step = flow.steps[progress.current_step]
            if current_step.step_id != step_id:
                raise ValueError("Step ID mismatch")
            
            # Store step data
            if step_data:
                progress.step_data[step_id] = step_data
                
                # Update personalization data based on step
                await self._update_personalization_data(progress, current_step, step_data)
            
            # Mark step as completed
            progress.completed_steps.append(step_id)
            progress.current_step += 1
            
            # Update completion percentage
            progress.completion_percentage = (len(progress.completed_steps) / len(flow.steps)) * 100
            
            # Check if onboarding is complete
            if progress.current_step >= len(flow.steps):
                await self._complete_onboarding(onboarding_id)
            
            logger.info("Onboarding step completed", 
                       user_id=user_id, 
                       onboarding_id=onboarding_id,
                       step_id=step_id,
                       completion_percentage=progress.completion_percentage)
            
        except Exception as e:
            logger.error("Failed to complete onboarding step", error=str(e))
            raise
    
    async def skip_onboarding(self, user_id: str, onboarding_id: str):
        """Skip the onboarding process"""
        try:
            if onboarding_id not in self.user_progress:
                raise ValueError("Onboarding progress not found")
            
            progress = self.user_progress[onboarding_id]
            progress.skipped = True
            progress.completed_at = datetime.now()
            progress.completion_percentage = 100.0
            
            # Remove from active onboardings
            if user_id in self.active_onboardings:
                del self.active_onboardings[user_id]
            
            logger.info("Onboarding skipped", 
                       user_id=user_id, 
                       onboarding_id=onboarding_id)
            
        except Exception as e:
            logger.error("Failed to skip onboarding", error=str(e))
            raise
    
    async def _load_default_onboarding_flows(self):
        """Load default onboarding flows"""
        
        # Farmer onboarding flow
        farmer_steps = [
            OnboardingStep(
                step_id="welcome",
                step_type=OnboardingStepType.WELCOME,
                title="Welcome to MANDI EAR",
                description="Welcome to India's first AI-powered agricultural intelligence platform",
                content="Welcome! MANDI EAR helps farmers like you get better prices, plan crops effectively, and stay informed about market conditions. Let's get you started.",
                required=True,
                skippable=False,
                estimated_duration_minutes=2,
                accessibility_instructions="This welcome screen supports screen readers and voice navigation"
            ),
            OnboardingStep(
                step_id="profile_setup",
                step_type=OnboardingStepType.PROFILE_SETUP,
                title="Set Up Your Profile",
                description="Tell us about yourself and your farming activities",
                content="Help us personalize your experience by sharing some basic information about your farming activities.",
                required=True,
                skippable=False,
                form_fields=[
                    {
                        "field_id": "name",
                        "label": "Full Name",
                        "type": "text",
                        "required": True,
                        "accessibility_label": "Enter your full name"
                    },
                    {
                        "field_id": "location",
                        "label": "Location",
                        "type": "location",
                        "required": True,
                        "accessibility_label": "Select your location or allow location access"
                    },
                    {
                        "field_id": "farm_size",
                        "label": "Farm Size (acres)",
                        "type": "number",
                        "required": False,
                        "accessibility_label": "Enter your farm size in acres"
                    },
                    {
                        "field_id": "primary_crops",
                        "label": "Primary Crops",
                        "type": "multi_select",
                        "required": True,
                        "options": ["wheat", "rice", "cotton", "sugarcane", "onion", "potato", "tomato"],
                        "accessibility_label": "Select your primary crops from the list"
                    }
                ],
                estimated_duration_minutes=5,
                accessibility_instructions="Use Tab to navigate form fields, Space to select checkboxes"
            ),
            OnboardingStep(
                step_id="language_selection",
                step_type=OnboardingStepType.LANGUAGE_SELECTION,
                title="Choose Your Language",
                description="Select your preferred language for the platform",
                content="MANDI EAR supports 50+ Indian languages. Choose the language you're most comfortable with.",
                required=True,
                skippable=False,
                form_fields=[
                    {
                        "field_id": "language",
                        "label": "Preferred Language",
                        "type": "select",
                        "required": True,
                        "options": [
                            {"value": "en", "label": "English"},
                            {"value": "hi", "label": "हिंदी (Hindi)"},
                            {"value": "ta", "label": "தமிழ் (Tamil)"},
                            {"value": "te", "label": "తెలుగు (Telugu)"},
                            {"value": "bn", "label": "বাংলা (Bengali)"},
                            {"value": "mr", "label": "मराठी (Marathi)"},
                            {"value": "gu", "label": "ગુજરાતી (Gujarati)"},
                            {"value": "kn", "label": "ಕನ್ನಡ (Kannada)"},
                            {"value": "ml", "label": "മലയാളം (Malayalam)"},
                            {"value": "pa", "label": "ਪੰਜਾਬੀ (Punjabi)"}
                        ],
                        "accessibility_label": "Select your preferred language from the dropdown"
                    }
                ],
                estimated_duration_minutes=2
            ),
            OnboardingStep(
                step_id="accessibility_setup",
                step_type=OnboardingStepType.ACCESSIBILITY_SETUP,
                title="Accessibility Preferences",
                description="Configure accessibility features to suit your needs",
                content="MANDI EAR includes features to make the platform accessible to everyone. Configure these settings based on your preferences.",
                required=False,
                skippable=True,
                form_fields=[
                    {
                        "field_id": "screen_reader",
                        "label": "Enable Screen Reader Support",
                        "type": "checkbox",
                        "required": False,
                        "accessibility_label": "Check this box if you use a screen reader"
                    },
                    {
                        "field_id": "high_contrast",
                        "label": "Enable High Contrast Mode",
                        "type": "checkbox",
                        "required": False,
                        "accessibility_label": "Check this box for high contrast display"
                    },
                    {
                        "field_id": "large_text",
                        "label": "Enable Large Text",
                        "type": "checkbox",
                        "required": False,
                        "accessibility_label": "Check this box for larger text size"
                    },
                    {
                        "field_id": "voice_navigation",
                        "label": "Enable Voice Navigation",
                        "type": "checkbox",
                        "required": False,
                        "accessibility_label": "Check this box to enable voice commands"
                    }
                ],
                estimated_duration_minutes=3,
                accessibility_instructions="These settings can be changed later in your profile settings"
            ),
            OnboardingStep(
                step_id="tutorial_selection",
                step_type=OnboardingStepType.TUTORIAL_SELECTION,
                title="Choose Your Learning Path",
                description="Select tutorials to help you get started",
                content="We recommend starting with these tutorials to make the most of MANDI EAR's features.",
                required=False,
                skippable=True,
                form_fields=[
                    {
                        "field_id": "tutorials",
                        "label": "Select Tutorials",
                        "type": "multi_select",
                        "required": False,
                        "options": [
                            {"value": "basic_navigation", "label": "Basic Navigation", "recommended": True},
                            {"value": "price_discovery", "label": "Price Discovery", "recommended": True},
                            {"value": "voice_commands", "label": "Voice Commands", "recommended": False},
                            {"value": "crop_planning", "label": "Crop Planning", "recommended": True},
                            {"value": "accessibility_features", "label": "Accessibility Features", "recommended": False}
                        ],
                        "accessibility_label": "Select which tutorials you'd like to take"
                    }
                ],
                estimated_duration_minutes=2
            ),
            OnboardingStep(
                step_id="feature_overview",
                step_type=OnboardingStepType.FEATURE_OVERVIEW,
                title="Platform Overview",
                description="Quick overview of key features",
                content="Here's a quick overview of MANDI EAR's key features that will help you in your farming activities.",
                required=True,
                skippable=False,
                estimated_duration_minutes=4,
                accessibility_instructions="This overview includes audio descriptions of key features"
            ),
            OnboardingStep(
                step_id="completion",
                step_type=OnboardingStepType.COMPLETION,
                title="Setup Complete!",
                description="You're all set to start using MANDI EAR",
                content="Congratulations! Your profile is set up and you're ready to start using MANDI EAR. You can always update your preferences in the settings.",
                required=True,
                skippable=False,
                estimated_duration_minutes=1
            )
        ]
        
        farmer_flow = OnboardingFlow(
            flow_id="farmer_onboarding",
            title="Farmer Onboarding",
            description="Complete onboarding flow for farmers",
            language="en",
            target_user_type="farmer",
            steps=farmer_steps,
            personalization_rules={
                "accessibility_features": "auto_enable_based_on_preferences",
                "language_content": "localize_based_on_selection",
                "crop_recommendations": "filter_by_primary_crops"
            },
            completion_rewards=[
                "tutorial_access",
                "personalized_dashboard",
                "welcome_bonus_features"
            ]
        )
        
        # Vendor onboarding flow (simplified)
        vendor_steps = [
            OnboardingStep(
                step_id="vendor_welcome",
                step_type=OnboardingStepType.WELCOME,
                title="Welcome Vendor",
                description="Welcome to MANDI EAR for agricultural vendors",
                content="Welcome! MANDI EAR helps vendors and traders stay informed about market conditions and connect with farmers.",
                required=True,
                skippable=False,
                estimated_duration_minutes=2
            ),
            OnboardingStep(
                step_id="vendor_profile",
                step_type=OnboardingStepType.PROFILE_SETUP,
                title="Vendor Profile Setup",
                description="Set up your vendor profile",
                content="Tell us about your trading activities and areas of operation.",
                required=True,
                skippable=False,
                form_fields=[
                    {
                        "field_id": "business_name",
                        "label": "Business Name",
                        "type": "text",
                        "required": True
                    },
                    {
                        "field_id": "trading_commodities",
                        "label": "Trading Commodities",
                        "type": "multi_select",
                        "required": True,
                        "options": ["wheat", "rice", "cotton", "sugarcane", "onion", "potato", "tomato"]
                    },
                    {
                        "field_id": "operation_areas",
                        "label": "Areas of Operation",
                        "type": "multi_select",
                        "required": True
                    }
                ],
                estimated_duration_minutes=4
            ),
            OnboardingStep(
                step_id="vendor_completion",
                step_type=OnboardingStepType.COMPLETION,
                title="Vendor Setup Complete",
                description="You're ready to start trading with MANDI EAR",
                content="Your vendor profile is set up. You can now access market intelligence and connect with farmers.",
                required=True,
                skippable=False,
                estimated_duration_minutes=1
            )
        ]
        
        vendor_flow = OnboardingFlow(
            flow_id="vendor_onboarding",
            title="Vendor Onboarding",
            description="Onboarding flow for agricultural vendors and traders",
            language="en",
            target_user_type="vendor",
            steps=vendor_steps
        )
        
        # Store flows
        self.onboarding_flows[farmer_flow.flow_id] = farmer_flow
        self.onboarding_flows[vendor_flow.flow_id] = vendor_flow
    
    def _determine_onboarding_flow(self, user_profile: Dict[str, Any]) -> str:
        """Determine appropriate onboarding flow based on user profile"""
        user_type = user_profile.get("user_type", "farmer")
        
        if user_type == "vendor":
            return "vendor_onboarding"
        else:
            return "farmer_onboarding"  # Default to farmer onboarding
    
    async def _personalize_step(
        self, 
        step: OnboardingStep, 
        personalization_data: Dict[str, Any]
    ) -> OnboardingStep:
        """Personalize onboarding step based on user data"""
        
        # Create a copy of the step
        personalized_step = OnboardingStep(**step.dict())
        
        # Personalize content based on user data
        if "name" in personalization_data:
            personalized_step.content = personalized_step.content.replace(
                "farmers like you", f"farmers like you, {personalization_data['name']}"
            )
        
        # Personalize form fields based on previous selections
        if step.step_type == OnboardingStepType.TUTORIAL_SELECTION:
            # Recommend tutorials based on accessibility preferences
            accessibility_prefs = personalization_data.get("accessibility_preferences", {})
            if accessibility_prefs.get("screen_reader") or accessibility_prefs.get("voice_navigation"):
                # Add accessibility tutorial as recommended
                for field in personalized_step.form_fields:
                    if field["field_id"] == "tutorials":
                        for option in field["options"]:
                            if option["value"] == "accessibility_features":
                                option["recommended"] = True
        
        return personalized_step
    
    async def _update_personalization_data(
        self, 
        progress: OnboardingProgress, 
        step: OnboardingStep, 
        step_data: Dict[str, Any]
    ):
        """Update personalization data based on completed step"""
        
        if step.step_type == OnboardingStepType.PROFILE_SETUP:
            # Store profile information
            progress.personalization_data.update({
                "name": step_data.get("name"),
                "location": step_data.get("location"),
                "farm_size": step_data.get("farm_size"),
                "primary_crops": step_data.get("primary_crops", [])
            })
        
        elif step.step_type == OnboardingStepType.LANGUAGE_SELECTION:
            progress.personalization_data["preferred_language"] = step_data.get("language", "en")
        
        elif step.step_type == OnboardingStepType.ACCESSIBILITY_SETUP:
            progress.personalization_data["accessibility_preferences"] = {
                "screen_reader": step_data.get("screen_reader", False),
                "high_contrast": step_data.get("high_contrast", False),
                "large_text": step_data.get("large_text", False),
                "voice_navigation": step_data.get("voice_navigation", False)
            }
        
        elif step.step_type == OnboardingStepType.TUTORIAL_SELECTION:
            progress.personalization_data["selected_tutorials"] = step_data.get("tutorials", [])
    
    async def _complete_onboarding(self, onboarding_id: str):
        """Complete the onboarding process"""
        progress = self.user_progress[onboarding_id]
        progress.completed_at = datetime.now()
        progress.completion_percentage = 100.0
        
        # Remove from active onboardings
        user_id = progress.user_id
        if user_id in self.active_onboardings:
            del self.active_onboardings[user_id]
        
        # Apply personalization settings
        await self._apply_onboarding_results(progress)
        
        logger.info("Onboarding completed", 
                   user_id=user_id, 
                   onboarding_id=onboarding_id,
                   flow_id=progress.flow_id)
    
    async def _apply_onboarding_results(self, progress: OnboardingProgress):
        """Apply the results of onboarding to user settings"""
        try:
            personalization = progress.personalization_data
            
            # This would typically integrate with user management service
            # to create/update user profile and preferences
            
            logger.info("Onboarding results applied", 
                       user_id=progress.user_id,
                       personalization_keys=list(personalization.keys()))
            
        except Exception as e:
            logger.error("Failed to apply onboarding results", error=str(e))