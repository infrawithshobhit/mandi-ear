"""
Tutorial Engine for user onboarding and feature tutorials
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import structlog
import json
import uuid

from models import (
    Tutorial, TutorialStep, TutorialProgress, TutorialType,
    ContextualHelp, AccessibilityFeature
)

logger = structlog.get_logger()

class TutorialEngine:
    """Manages tutorials and contextual help system"""
    
    def __init__(self):
        self.tutorials: Dict[str, Tutorial] = {}
        self.user_progress: Dict[str, Dict[str, TutorialProgress]] = {}
        self.contextual_help: Dict[str, Dict[str, ContextualHelp]] = {}
        self.active_tutorials: Dict[str, str] = {}  # user_id -> tutorial_id
    
    async def initialize(self):
        """Initialize the tutorial engine"""
        try:
            await self._load_default_tutorials()
            await self._load_contextual_help()
            logger.info("Tutorial engine initialized")
        except Exception as e:
            logger.error("Failed to initialize tutorial engine", error=str(e))
            raise
    
    async def shutdown(self):
        """Shutdown the tutorial engine"""
        logger.info("Tutorial engine shutdown")
    
    async def get_available_tutorials(self, language: str = "en") -> List[Dict[str, Any]]:
        """Get list of available tutorials"""
        available = []
        
        for tutorial in self.tutorials.values():
            if tutorial.language == language:
                available.append({
                    "tutorial_id": tutorial.tutorial_id,
                    "title": tutorial.title,
                    "description": tutorial.description,
                    "tutorial_type": tutorial.tutorial_type.value,
                    "difficulty_level": tutorial.difficulty_level,
                    "estimated_duration_minutes": tutorial.estimated_duration_minutes,
                    "prerequisites": tutorial.prerequisites,
                    "tags": tutorial.tags,
                    "accessibility_features": [f.value for f in tutorial.accessibility_features]
                })
        
        return available
    
    async def start_tutorial(
        self, 
        user_id: str, 
        tutorial_type: str, 
        language: str = "en"
    ) -> str:
        """Start a tutorial for the user"""
        try:
            # Find the tutorial
            tutorial = None
            for t in self.tutorials.values():
                if t.tutorial_type.value == tutorial_type and t.language == language:
                    tutorial = t
                    break
            
            if not tutorial:
                raise ValueError(f"Tutorial not found: {tutorial_type}")
            
            # Create progress tracking
            progress = TutorialProgress(
                user_id=user_id,
                tutorial_id=tutorial.tutorial_id,
                current_step=0,
                started_at=datetime.now(),
                last_accessed=datetime.now()
            )
            
            # Store progress
            if user_id not in self.user_progress:
                self.user_progress[user_id] = {}
            
            self.user_progress[user_id][tutorial.tutorial_id] = progress
            self.active_tutorials[user_id] = tutorial.tutorial_id
            
            logger.info("Tutorial started", 
                       user_id=user_id, 
                       tutorial_id=tutorial.tutorial_id,
                       tutorial_type=tutorial_type)
            
            return tutorial.tutorial_id
            
        except Exception as e:
            logger.error("Failed to start tutorial", error=str(e))
            raise
    
    async def get_user_progress(self, user_id: str) -> Dict[str, TutorialProgress]:
        """Get user's tutorial progress"""
        return self.user_progress.get(user_id, {})
    
    async def complete_step(self, user_id: str, tutorial_id: str, step_id: str):
        """Mark a tutorial step as completed"""
        try:
            if user_id not in self.user_progress:
                raise ValueError("No tutorial progress found for user")
            
            if tutorial_id not in self.user_progress[user_id]:
                raise ValueError("Tutorial not found in user progress")
            
            progress = self.user_progress[user_id][tutorial_id]
            
            # Add step to completed list
            if step_id not in progress.completed_steps:
                progress.completed_steps.append(step_id)
            
            # Update progress
            tutorial = self.tutorials[tutorial_id]
            total_steps = len(tutorial.steps)
            progress.completion_percentage = (len(progress.completed_steps) / total_steps) * 100
            progress.last_accessed = datetime.now()
            
            # Check if tutorial is completed
            if len(progress.completed_steps) == total_steps:
                progress.completed_at = datetime.now()
                if user_id in self.active_tutorials and self.active_tutorials[user_id] == tutorial_id:
                    del self.active_tutorials[user_id]
            
            logger.info("Tutorial step completed", 
                       user_id=user_id, 
                       tutorial_id=tutorial_id,
                       step_id=step_id,
                       completion_percentage=progress.completion_percentage)
            
        except Exception as e:
            logger.error("Failed to complete tutorial step", error=str(e))
            raise
    
    async def get_next_step(self, user_id: str, tutorial_id: str) -> Dict[str, Any]:
        """Get the next tutorial step for the user"""
        try:
            if user_id not in self.user_progress:
                raise ValueError("No tutorial progress found for user")
            
            if tutorial_id not in self.user_progress[user_id]:
                raise ValueError("Tutorial not found in user progress")
            
            progress = self.user_progress[user_id][tutorial_id]
            tutorial = self.tutorials[tutorial_id]
            
            # Find next uncompleted step
            for i, step in enumerate(tutorial.steps):
                if step.step_id not in progress.completed_steps:
                    progress.current_step = i
                    progress.last_accessed = datetime.now()
                    
                    return {
                        "step_id": step.step_id,
                        "title": step.title,
                        "description": step.description,
                        "content": step.content,
                        "media_url": step.media_url,
                        "media_type": step.media_type,
                        "interactive_elements": step.interactive_elements,
                        "estimated_duration_minutes": step.estimated_duration_minutes,
                        "accessibility_notes": step.accessibility_notes,
                        "keyboard_instructions": step.keyboard_instructions,
                        "voice_instructions": step.voice_instructions,
                        "step_number": i + 1,
                        "total_steps": len(tutorial.steps),
                        "completion_percentage": progress.completion_percentage
                    }
            
            # All steps completed
            return {
                "completed": True,
                "message": "Tutorial completed successfully!",
                "completion_percentage": 100.0
            }
            
        except Exception as e:
            logger.error("Failed to get next tutorial step", error=str(e))
            raise
    
    async def get_contextual_help(
        self, 
        page: str, 
        element: Optional[str] = None, 
        language: str = "en"
    ) -> Dict[str, Any]:
        """Get contextual help for UI elements"""
        try:
            help_key = f"{page}_{element}" if element else page
            
            if language in self.contextual_help and help_key in self.contextual_help[language]:
                help_content = self.contextual_help[language][help_key]
                
                return {
                    "title": help_content.title,
                    "content": help_content.content,
                    "help_type": help_content.help_type,
                    "media_url": help_content.media_url,
                    "related_topics": help_content.related_topics,
                    "keyboard_shortcuts": help_content.keyboard_shortcuts,
                    "voice_commands": help_content.voice_commands,
                    "accessibility_notes": help_content.accessibility_notes
                }
            
            # Return generic help if specific help not found
            return await self._generate_generic_help(page, element, language)
            
        except Exception as e:
            logger.error("Failed to get contextual help", error=str(e))
            return {
                "title": "Help",
                "content": "Help information is not available for this element.",
                "help_type": "tooltip"
            }
    
    async def _load_default_tutorials(self):
        """Load default tutorials"""
        
        # Basic Navigation Tutorial
        basic_nav_steps = [
            TutorialStep(
                step_id="nav_welcome",
                title="Welcome to MANDI EAR",
                description="Introduction to the agricultural intelligence platform",
                content="Welcome to MANDI EAR, India's first ambient AI-powered agricultural intelligence platform. This tutorial will guide you through the basic navigation features.",
                estimated_duration_minutes=2,
                accessibility_notes="This tutorial supports screen readers and keyboard navigation",
                keyboard_instructions="Use Tab to navigate, Enter to continue",
                voice_instructions="Say 'continue' to proceed to the next step"
            ),
            TutorialStep(
                step_id="nav_menu",
                title="Main Navigation Menu",
                description="Learn how to use the main navigation menu",
                content="The main navigation menu provides access to all platform features. You can access it using the menu button or Alt+M keyboard shortcut.",
                estimated_duration_minutes=3,
                keyboard_instructions="Press Alt+M to open menu, use arrow keys to navigate",
                voice_instructions="Say 'open menu' to access navigation options"
            ),
            TutorialStep(
                step_id="nav_search",
                title="Search Functionality",
                description="Learn how to search for information",
                content="Use the search feature to quickly find prices, markets, or other information. Access it with Alt+S or click the search icon.",
                estimated_duration_minutes=2,
                keyboard_instructions="Press Alt+S to focus search, type your query and press Enter",
                voice_instructions="Say 'search for [item]' to perform voice search"
            )
        ]
        
        basic_nav_tutorial = Tutorial(
            tutorial_id="basic_navigation_tutorial",
            tutorial_type=TutorialType.BASIC_NAVIGATION,
            title="Basic Navigation",
            description="Learn the basics of navigating the MANDI EAR platform",
            language="en",
            difficulty_level="beginner",
            estimated_duration_minutes=7,
            steps=basic_nav_steps,
            tags=["navigation", "basics", "getting-started"],
            accessibility_features=[
                AccessibilityFeature.SCREEN_READER,
                AccessibilityFeature.KEYBOARD_NAVIGATION,
                AccessibilityFeature.VOICE_NAVIGATION
            ]
        )
        
        # Price Discovery Tutorial
        price_discovery_steps = [
            TutorialStep(
                step_id="price_intro",
                title="Price Discovery Overview",
                description="Understanding price discovery features",
                content="MANDI EAR provides real-time price information from markets across India. Learn how to access and interpret this data.",
                estimated_duration_minutes=3
            ),
            TutorialStep(
                step_id="price_search",
                title="Searching for Prices",
                description="How to search for commodity prices",
                content="Use the price search feature to find current prices for specific commodities in your region or across different markets.",
                estimated_duration_minutes=4
            ),
            TutorialStep(
                step_id="price_comparison",
                title="Comparing Prices",
                description="Compare prices across different markets",
                content="Learn how to compare prices across multiple markets to find the best selling opportunities.",
                estimated_duration_minutes=5
            )
        ]
        
        price_discovery_tutorial = Tutorial(
            tutorial_id="price_discovery_tutorial",
            tutorial_type=TutorialType.PRICE_DISCOVERY,
            title="Price Discovery",
            description="Learn how to use price discovery features effectively",
            language="en",
            difficulty_level="beginner",
            estimated_duration_minutes=12,
            steps=price_discovery_steps,
            tags=["prices", "markets", "discovery"],
            accessibility_features=[AccessibilityFeature.SCREEN_READER]
        )
        
        # Accessibility Features Tutorial
        accessibility_steps = [
            TutorialStep(
                step_id="accessibility_intro",
                title="Accessibility Features Overview",
                description="Introduction to accessibility features",
                content="MANDI EAR includes comprehensive accessibility features to ensure the platform is usable by everyone, including users with visual, hearing, or motor impairments.",
                estimated_duration_minutes=2,
                accessibility_notes="This tutorial demonstrates all accessibility features"
            ),
            TutorialStep(
                step_id="screen_reader",
                title="Screen Reader Support",
                description="Using screen readers with MANDI EAR",
                content="The platform is fully compatible with screen readers. All content includes proper ARIA labels and descriptions.",
                estimated_duration_minutes=4,
                accessibility_notes="Screen reader users will hear detailed descriptions of all interface elements"
            ),
            TutorialStep(
                step_id="high_contrast",
                title="High Contrast Mode",
                description="Using high contrast themes",
                content="Enable high contrast mode for better visibility. Use Alt+H to toggle or access through settings.",
                estimated_duration_minutes=3,
                keyboard_instructions="Press Alt+H to toggle high contrast mode"
            ),
            TutorialStep(
                step_id="voice_navigation",
                title="Voice Navigation",
                description="Navigating using voice commands",
                content="Use voice commands to navigate the platform hands-free. Say 'help' to hear available commands.",
                estimated_duration_minutes=5,
                voice_instructions="Try saying 'go home', 'show prices', or 'help' to test voice navigation"
            )
        ]
        
        accessibility_tutorial = Tutorial(
            tutorial_id="accessibility_features_tutorial",
            tutorial_type=TutorialType.ACCESSIBILITY_FEATURES,
            title="Accessibility Features",
            description="Learn about accessibility features and how to use them",
            language="en",
            difficulty_level="beginner",
            estimated_duration_minutes=14,
            steps=accessibility_steps,
            tags=["accessibility", "screen-reader", "voice", "contrast"],
            accessibility_features=[
                AccessibilityFeature.SCREEN_READER,
                AccessibilityFeature.HIGH_CONTRAST,
                AccessibilityFeature.VOICE_NAVIGATION,
                AccessibilityFeature.KEYBOARD_NAVIGATION
            ]
        )
        
        # Store tutorials
        self.tutorials[basic_nav_tutorial.tutorial_id] = basic_nav_tutorial
        self.tutorials[price_discovery_tutorial.tutorial_id] = price_discovery_tutorial
        self.tutorials[accessibility_tutorial.tutorial_id] = accessibility_tutorial
    
    async def _load_contextual_help(self):
        """Load contextual help content"""
        
        help_content = {
            "en": {
                "home": ContextualHelp(
                    page="home",
                    title="Home Page Help",
                    content="The home page provides an overview of current market conditions, recent price updates, and quick access to key features.",
                    help_type="modal",
                    keyboard_shortcuts=["Alt+M for menu", "Alt+S for search", "F1 for help"],
                    voice_commands=["go home", "show prices", "help"]
                ),
                "prices": ContextualHelp(
                    page="prices",
                    title="Price Information Help",
                    content="View current commodity prices from markets across India. Use filters to narrow down results by commodity, region, or date.",
                    help_type="sidebar",
                    keyboard_shortcuts=["Arrow keys to navigate prices", "Enter for details"],
                    voice_commands=["show prices", "search for [commodity]"],
                    accessibility_notes="Price information includes audio descriptions for screen reader users"
                ),
                "mandis": ContextualHelp(
                    page="mandis",
                    title="Market List Help",
                    content="Browse markets (mandis) in your region or across India. View market details, operating hours, and facilities.",
                    help_type="tooltip",
                    keyboard_shortcuts=["Tab to navigate markets", "Enter to view details"],
                    voice_commands=["show markets", "find markets near me"]
                ),
                "search": ContextualHelp(
                    page="search",
                    title="Search Help",
                    content="Search for commodities, markets, or price information. Use voice search by saying your query or type in the search box.",
                    help_type="inline",
                    keyboard_shortcuts=["Alt+S to focus search", "Enter to search"],
                    voice_commands=["search for [item]", "find [commodity] prices"]
                )
            }
        }
        
        self.contextual_help = help_content
    
    async def _generate_generic_help(
        self, 
        page: str, 
        element: Optional[str], 
        language: str
    ) -> Dict[str, Any]:
        """Generate generic help content when specific help is not available"""
        
        generic_help = {
            "title": f"Help for {page}",
            "content": f"This is the {page} page. Use the navigation menu to access other features, or use keyboard shortcuts for quick access.",
            "help_type": "tooltip",
            "keyboard_shortcuts": [
                "Alt+M - Open main menu",
                "Alt+S - Focus search",
                "F1 - Open help",
                "Tab - Navigate elements",
                "Enter - Activate element",
                "Escape - Go back"
            ],
            "voice_commands": [
                "help - Show available commands",
                "go home - Navigate to home page",
                "show menu - Open navigation menu"
            ],
            "accessibility_notes": "All elements support keyboard navigation and screen readers"
        }
        
        return generic_help