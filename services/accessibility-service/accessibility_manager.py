"""
Accessibility Manager for screen reader support and high-contrast modes
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog
import json
import uuid

from models import (
    AccessibilitySettings, UserPreferences, ScreenReaderContent,
    HighContrastTheme, UserFeedback, KeyboardShortcut, VoiceCommand,
    NavigationResult, ContrastLevel, TextSize, AccessibilityFeature
)

logger = structlog.get_logger()

class AccessibilityManager:
    """Manages accessibility features and user preferences"""
    
    def __init__(self):
        self.user_settings: Dict[str, AccessibilitySettings] = {}
        self.user_preferences: Dict[str, UserPreferences] = {}
        self.high_contrast_themes: Dict[str, HighContrastTheme] = {}
        self.keyboard_shortcuts: Dict[str, List[KeyboardShortcut]] = {}
        self.voice_commands: Dict[str, List[VoiceCommand]] = {}
        self.feedback_store: Dict[str, UserFeedback] = {}
        
        # Screen reader content templates
        self.screen_reader_templates = {
            "price_display": {
                "aria_label": "Price information for {commodity}",
                "content": "{commodity} price is {price} {currency} per {unit} at {mandi} market",
                "navigation_hints": ["Use arrow keys to navigate between price entries", "Press Enter for detailed information"],
                "keyboard_shortcuts": ["P for price details", "M for market information"]
            },
            "mandi_list": {
                "aria_label": "Market list with {count} markets",
                "content": "List of {count} markets. Use arrow keys to navigate.",
                "navigation_hints": ["Up/Down arrows to navigate markets", "Enter to select market"],
                "keyboard_shortcuts": ["L for location details", "D for distance information"]
            },
            "navigation_menu": {
                "aria_label": "Main navigation menu",
                "content": "Main navigation with {count} options",
                "navigation_hints": ["Tab to navigate menu items", "Enter to activate"],
                "keyboard_shortcuts": ["Alt+M for main menu", "Escape to close menu"]
            }
        }
        
        # Default high contrast themes
        self.default_themes = {
            "high_contrast_dark": HighContrastTheme(
                user_id="default",
                theme_name="High Contrast Dark",
                background_color="#000000",
                text_color="#FFFFFF",
                link_color="#FFFF00",
                button_color="#FFFFFF",
                button_background="#000000",
                border_color="#FFFFFF",
                focus_color="#FF0000",
                error_color="#FF6666",
                success_color="#66FF66",
                warning_color="#FFFF66"
            ),
            "high_contrast_light": HighContrastTheme(
                user_id="default",
                theme_name="High Contrast Light",
                background_color="#FFFFFF",
                text_color="#000000",
                link_color="#0000FF",
                button_color="#000000",
                button_background="#FFFFFF",
                border_color="#000000",
                focus_color="#FF0000",
                error_color="#CC0000",
                success_color="#006600",
                warning_color="#CC6600"
            )
        }
    
    async def initialize(self):
        """Initialize the accessibility manager"""
        try:
            await self._load_default_keyboard_shortcuts()
            await self._load_default_voice_commands()
            logger.info("Accessibility manager initialized")
        except Exception as e:
            logger.error("Failed to initialize accessibility manager", error=str(e))
            raise
    
    async def shutdown(self):
        """Shutdown the accessibility manager"""
        logger.info("Accessibility manager shutdown")
    
    async def get_user_settings(self, user_id: str) -> AccessibilitySettings:
        """Get user's accessibility settings"""
        if user_id not in self.user_settings:
            # Create default settings for new user
            self.user_settings[user_id] = AccessibilitySettings(
                user_id=user_id,
                keyboard_shortcuts=await self._get_default_keyboard_shortcuts(),
                voice_commands=await self._get_default_voice_commands()
            )
        
        return self.user_settings[user_id]
    
    async def update_user_settings(self, user_id: str, settings: AccessibilitySettings):
        """Update user's accessibility settings"""
        settings.user_id = user_id
        settings.updated_at = datetime.now()
        self.user_settings[user_id] = settings
        
        logger.info("User accessibility settings updated", 
                   user_id=user_id,
                   features_enabled=[
                       feature for feature in AccessibilityFeature 
                       if getattr(settings, f"{feature.value}_enabled", False)
                   ])
    
    async def get_screen_reader_content(
        self, 
        user_id: str, 
        page: str, 
        element_id: Optional[str] = None
    ) -> ScreenReaderContent:
        """Get screen reader optimized content"""
        try:
            user_settings = await self.get_user_settings(user_id)
            
            # Get template based on page/element
            template_key = self._get_screen_reader_template_key(page, element_id)
            template = self.screen_reader_templates.get(template_key, {})
            
            # Generate contextual content based on user settings
            # Always generate enhanced content if any accessibility features are enabled
            content = await self._generate_screen_reader_content(
                page=page,
                element_id=element_id,
                template=template,
                user_settings=user_settings
            )
            
            return content
            
        except Exception as e:
            logger.error("Failed to get screen reader content", error=str(e))
            # Return fallback content
            return ScreenReaderContent(
                page=page,
                element_id=element_id,
                aria_label=f"Content for {page}",
                role="main",
                content="Content not available"
            )
    
    async def get_high_contrast_theme(self, user_id: str) -> HighContrastTheme:
        """Get user's high contrast theme"""
        user_settings = await self.get_user_settings(user_id)
        
        if user_id in self.high_contrast_themes:
            return self.high_contrast_themes[user_id]
        
        # Return default theme based on user preference
        if user_settings.high_contrast_enabled:
            if user_settings.contrast_level == ContrastLevel.EXTRA_HIGH:
                return self.default_themes["high_contrast_dark"]
            else:
                return self.default_themes["high_contrast_light"]
        
        # Return normal theme
        return HighContrastTheme(
            user_id=user_id,
            theme_name="Normal",
            background_color="#FFFFFF",
            text_color="#333333",
            is_active=False
        )
    
    async def update_high_contrast_theme(self, user_id: str, theme: HighContrastTheme):
        """Update user's high contrast theme"""
        theme.user_id = user_id
        self.high_contrast_themes[user_id] = theme
        
        # Update user settings to enable high contrast
        user_settings = await self.get_user_settings(user_id)
        user_settings.high_contrast_enabled = theme.is_active
        await self.update_user_settings(user_id, user_settings)
        
        logger.info("High contrast theme updated", 
                   user_id=user_id, 
                   theme_name=theme.theme_name,
                   is_active=theme.is_active)
    
    async def get_user_preferences(self, user_id: str) -> UserPreferences:
        """Get user's UX preferences"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = UserPreferences(
                user_id=user_id,
                notification_preferences={
                    "price_alerts": True,
                    "weather_alerts": True,
                    "msp_alerts": True,
                    "tutorial_reminders": True,
                    "system_updates": False
                }
            )
        
        return self.user_preferences[user_id]
    
    async def update_user_preferences(self, user_id: str, preferences: UserPreferences):
        """Update user's UX preferences"""
        preferences.user_id = user_id
        preferences.updated_at = datetime.now()
        self.user_preferences[user_id] = preferences
        
        logger.info("User preferences updated", 
                   user_id=user_id,
                   language=preferences.language,
                   region=preferences.region)
    
    async def submit_feedback(
        self, 
        user_id: str, 
        feedback_type: str, 
        content: str,
        page: Optional[str] = None,
        rating: Optional[int] = None
    ) -> str:
        """Submit user feedback"""
        feedback_id = str(uuid.uuid4())
        
        feedback = UserFeedback(
            feedback_id=feedback_id,
            user_id=user_id,
            feedback_type=feedback_type,
            content=content,
            page=page,
            rating=rating
        )
        
        # Add accessibility context if user has accessibility features enabled
        user_settings = await self.get_user_settings(user_id)
        feedback.accessibility_context = {
            "screen_reader_enabled": user_settings.screen_reader_enabled,
            "high_contrast_enabled": user_settings.high_contrast_enabled,
            "large_text_enabled": user_settings.large_text_enabled,
            "voice_navigation_enabled": user_settings.voice_navigation_enabled,
            "keyboard_navigation_enabled": user_settings.keyboard_navigation_enabled
        }
        
        self.feedback_store[feedback_id] = feedback
        
        logger.info("User feedback submitted", 
                   feedback_id=feedback_id,
                   user_id=user_id,
                   feedback_type=feedback_type)
        
        return feedback_id
    
    async def get_keyboard_shortcuts(self, language: str = "en") -> Dict[str, Any]:
        """Get keyboard shortcuts for accessibility"""
        shortcuts = self.keyboard_shortcuts.get(language, [])
        
        return {
            "shortcuts": [
                {
                    "key_combination": shortcut.key_combination,
                    "action": shortcut.action,
                    "description": shortcut.description,
                    "category": shortcut.category
                }
                for shortcut in shortcuts
            ],
            "categories": list(set(shortcut.category for shortcut in shortcuts)),
            "customization_available": True
        }
    
    async def process_voice_navigation(
        self, 
        user_id: str, 
        voice_command: str, 
        current_page: str
    ) -> NavigationResult:
        """Process voice navigation commands"""
        try:
            user_settings = await self.get_user_settings(user_id)
            
            if not user_settings.voice_navigation_enabled:
                return NavigationResult(
                    command_recognized=False,
                    action_taken="none",
                    feedback_message="Voice navigation is not enabled",
                    success=False,
                    error_message="Voice navigation disabled"
                )
            
            # Process the voice command
            command_result = await self._process_voice_command(
                voice_command=voice_command,
                current_page=current_page,
                user_settings=user_settings
            )
            
            return command_result
            
        except Exception as e:
            logger.error("Failed to process voice navigation", error=str(e))
            return NavigationResult(
                command_recognized=False,
                action_taken="none",
                feedback_message="Failed to process voice command",
                success=False,
                error_message=str(e)
            )
    
    async def _load_default_keyboard_shortcuts(self):
        """Load default keyboard shortcuts"""
        default_shortcuts = [
            KeyboardShortcut(
                shortcut_id="nav_main_menu",
                key_combination="Alt+M",
                action="open_main_menu",
                description="Open main navigation menu",
                category="navigation",
                context="global"
            ),
            KeyboardShortcut(
                shortcut_id="nav_search",
                key_combination="Alt+S",
                action="focus_search",
                description="Focus on search input",
                category="navigation",
                context="global"
            ),
            KeyboardShortcut(
                shortcut_id="nav_help",
                key_combination="F1",
                action="open_help",
                description="Open contextual help",
                category="accessibility",
                context="global"
            ),
            KeyboardShortcut(
                shortcut_id="nav_skip_content",
                key_combination="Alt+1",
                action="skip_to_content",
                description="Skip to main content",
                category="accessibility",
                context="global"
            ),
            KeyboardShortcut(
                shortcut_id="toggle_high_contrast",
                key_combination="Alt+H",
                action="toggle_high_contrast",
                description="Toggle high contrast mode",
                category="accessibility",
                context="global"
            ),
            KeyboardShortcut(
                shortcut_id="increase_text_size",
                key_combination="Ctrl++",
                action="increase_text_size",
                description="Increase text size",
                category="accessibility",
                context="global"
            ),
            KeyboardShortcut(
                shortcut_id="decrease_text_size",
                key_combination="Ctrl+-",
                action="decrease_text_size",
                description="Decrease text size",
                category="accessibility",
                context="global"
            )
        ]
        
        self.keyboard_shortcuts["en"] = default_shortcuts
    
    async def _load_default_voice_commands(self):
        """Load default voice commands"""
        default_commands = [
            VoiceCommand(
                command_id="nav_home",
                trigger_phrases=["go home", "navigate home", "home page"],
                action="navigate_home",
                description="Navigate to home page",
                category="navigation",
                context="global"
            ),
            VoiceCommand(
                command_id="nav_prices",
                trigger_phrases=["show prices", "price information", "market prices"],
                action="navigate_prices",
                description="Navigate to price information",
                category="navigation",
                context="global"
            ),
            VoiceCommand(
                command_id="nav_mandis",
                trigger_phrases=["show markets", "market list", "find markets"],
                action="navigate_mandis",
                description="Navigate to market list",
                category="navigation",
                context="global"
            ),
            VoiceCommand(
                command_id="read_content",
                trigger_phrases=["read this", "read content", "what's on screen"],
                action="read_current_content",
                description="Read current page content",
                category="accessibility",
                context="global"
            ),
            VoiceCommand(
                command_id="help",
                trigger_phrases=["help", "how to use", "what can I do"],
                action="show_help",
                description="Show help information",
                category="accessibility",
                context="global"
            )
        ]
        
        self.voice_commands["en"] = default_commands
    
    async def _get_default_keyboard_shortcuts(self) -> Dict[str, str]:
        """Get default keyboard shortcuts mapping"""
        return {
            "Alt+M": "open_main_menu",
            "Alt+S": "focus_search",
            "F1": "open_help",
            "Alt+1": "skip_to_content",
            "Alt+H": "toggle_high_contrast",
            "Ctrl++": "increase_text_size",
            "Ctrl+-": "decrease_text_size"
        }
    
    async def _get_default_voice_commands(self) -> Dict[str, str]:
        """Get default voice commands mapping"""
        return {
            "go home": "navigate_home",
            "show prices": "navigate_prices",
            "show markets": "navigate_mandis",
            "read this": "read_current_content",
            "help": "show_help"
        }
    
    def _get_screen_reader_template_key(self, page: str, element_id: Optional[str]) -> str:
        """Get the appropriate screen reader template key"""
        if element_id:
            return f"{page}_{element_id}"
        
        # Map pages to template keys
        page_mapping = {
            "prices": "price_display",
            "mandis": "mandi_list",
            "navigation": "navigation_menu"
        }
        
        return page_mapping.get(page, "default")
    
    async def _generate_screen_reader_content(
        self,
        page: str,
        element_id: Optional[str],
        template: Dict[str, Any],
        user_settings: AccessibilitySettings
    ) -> ScreenReaderContent:
        """Generate screen reader content based on template and context"""
        
        # Start with template content
        navigation_hints = list(template.get("navigation_hints", []))
        keyboard_shortcuts = list(template.get("keyboard_shortcuts", []))
        
        # Customize based on user settings
        if user_settings.keyboard_navigation_enabled:
            keyboard_shortcuts.extend([
                "Tab to navigate elements",
                "Enter to activate",
                "Escape to go back"
            ])
            navigation_hints.extend([
                "Use Tab key to navigate between elements",
                "Press Enter to activate buttons and links",
                "Use arrow keys for menu navigation"
            ])
        
        if user_settings.voice_navigation_enabled:
            navigation_hints.extend([
                "Voice commands available - say 'help' for options",
                "Say 'go home' to navigate to home page",
                "Say 'read this' to hear current content"
            ])
        
        # Default content structure
        content = ScreenReaderContent(
            page=page,
            element_id=element_id,
            aria_label=template.get("aria_label", f"Content for {page}"),
            role="main",
            content=template.get("content", f"Page content for {page}"),
            navigation_hints=navigation_hints,
            keyboard_shortcuts=keyboard_shortcuts
        )
        
        return content
    
    async def _process_voice_command(
        self,
        voice_command: str,
        current_page: str,
        user_settings: AccessibilitySettings
    ) -> NavigationResult:
        """Process a voice command and return navigation result"""
        
        # Normalize the command
        command_lower = voice_command.lower().strip()
        
        # Get available voice commands
        available_commands = self.voice_commands.get("en", [])
        
        # Find matching command
        matched_command = None
        for cmd in available_commands:
            for trigger in cmd.trigger_phrases:
                if trigger.lower() in command_lower:
                    matched_command = cmd
                    break
            if matched_command:
                break
        
        if not matched_command:
            return NavigationResult(
                command_recognized=False,
                action_taken="none",
                feedback_message=f"Command '{voice_command}' not recognized. Try 'help' for available commands.",
                next_suggestions=["help", "go home", "show prices", "show markets"]
            )
        
        # Execute the command
        action_result = await self._execute_voice_action(
            action=matched_command.action,
            current_page=current_page,
            parameters=matched_command.parameters
        )
        
        return NavigationResult(
            command_recognized=True,
            action_taken=matched_command.action,
            target_element=action_result.get("target_element"),
            navigation_path=action_result.get("navigation_path", []),
            feedback_message=action_result.get("feedback_message", "Command executed successfully"),
            audio_feedback=action_result.get("audio_feedback"),
            next_suggestions=action_result.get("next_suggestions", []),
            success=action_result.get("success", True)
        )
    
    async def _execute_voice_action(
        self,
        action: str,
        current_page: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a voice navigation action"""
        
        action_handlers = {
            "navigate_home": self._handle_navigate_home,
            "navigate_prices": self._handle_navigate_prices,
            "navigate_mandis": self._handle_navigate_mandis,
            "read_current_content": self._handle_read_content,
            "show_help": self._handle_show_help
        }
        
        handler = action_handlers.get(action)
        if not handler:
            return {
                "success": False,
                "feedback_message": f"Action '{action}' not implemented",
                "next_suggestions": ["help"]
            }
        
        return await handler(current_page, parameters)
    
    async def _handle_navigate_home(self, current_page: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle navigation to home page"""
        return {
            "success": True,
            "target_element": "home_page",
            "navigation_path": ["home"],
            "feedback_message": "Navigating to home page",
            "audio_feedback": "Going to home page",
            "next_suggestions": ["show prices", "show markets", "help"]
        }
    
    async def _handle_navigate_prices(self, current_page: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle navigation to prices page"""
        return {
            "success": True,
            "target_element": "prices_page",
            "navigation_path": ["prices"],
            "feedback_message": "Navigating to price information",
            "audio_feedback": "Showing current market prices",
            "next_suggestions": ["show markets", "go home", "help"]
        }
    
    async def _handle_navigate_mandis(self, current_page: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle navigation to mandis page"""
        return {
            "success": True,
            "target_element": "mandis_page",
            "navigation_path": ["mandis"],
            "feedback_message": "Navigating to market list",
            "audio_feedback": "Showing available markets",
            "next_suggestions": ["show prices", "go home", "help"]
        }
    
    async def _handle_read_content(self, current_page: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle reading current content"""
        return {
            "success": True,
            "feedback_message": f"Reading content from {current_page} page",
            "audio_feedback": f"Current page is {current_page}. Use arrow keys to navigate content.",
            "next_suggestions": ["help", "go home"]
        }
    
    async def _handle_show_help(self, current_page: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle showing help"""
        return {
            "success": True,
            "target_element": "help_dialog",
            "feedback_message": "Showing help information",
            "audio_feedback": "Available commands: go home, show prices, show markets, read this, help",
            "next_suggestions": ["go home", "show prices", "show markets"]
        }