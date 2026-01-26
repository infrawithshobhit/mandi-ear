"""
Data models for accessibility service
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class AccessibilityFeature(str, Enum):
    """Available accessibility features"""
    SCREEN_READER = "screen_reader"
    HIGH_CONTRAST = "high_contrast"
    LARGE_TEXT = "large_text"
    VOICE_NAVIGATION = "voice_navigation"
    KEYBOARD_NAVIGATION = "keyboard_navigation"
    REDUCED_MOTION = "reduced_motion"
    AUDIO_DESCRIPTIONS = "audio_descriptions"

class ContrastLevel(str, Enum):
    """High contrast levels"""
    NORMAL = "normal"
    HIGH = "high"
    EXTRA_HIGH = "extra_high"
    CUSTOM = "custom"

class TextSize(str, Enum):
    """Text size options"""
    SMALL = "small"
    NORMAL = "normal"
    LARGE = "large"
    EXTRA_LARGE = "extra_large"
    CUSTOM = "custom"

class TutorialType(str, Enum):
    """Types of tutorials available"""
    BASIC_NAVIGATION = "basic_navigation"
    PRICE_DISCOVERY = "price_discovery"
    VOICE_COMMANDS = "voice_commands"
    MARKET_ANALYSIS = "market_analysis"
    CROP_PLANNING = "crop_planning"
    MSP_MONITORING = "msp_monitoring"
    ACCESSIBILITY_FEATURES = "accessibility_features"

class OnboardingStepType(str, Enum):
    """Types of onboarding steps"""
    WELCOME = "welcome"
    PROFILE_SETUP = "profile_setup"
    ACCESSIBILITY_SETUP = "accessibility_setup"
    LANGUAGE_SELECTION = "language_selection"
    LOCATION_SETUP = "location_setup"
    TUTORIAL_SELECTION = "tutorial_selection"
    FEATURE_OVERVIEW = "feature_overview"
    COMPLETION = "completion"

class AccessibilitySettings(BaseModel):
    """User accessibility settings"""
    user_id: str
    screen_reader_enabled: bool = False
    high_contrast_enabled: bool = False
    contrast_level: ContrastLevel = ContrastLevel.NORMAL
    large_text_enabled: bool = False
    text_size: TextSize = TextSize.NORMAL
    voice_navigation_enabled: bool = False
    keyboard_navigation_enabled: bool = False
    reduced_motion_enabled: bool = False
    audio_descriptions_enabled: bool = False
    custom_css: Optional[str] = None
    keyboard_shortcuts: Dict[str, str] = Field(default_factory=dict)
    voice_commands: Dict[str, str] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.now)

class ScreenReaderContent(BaseModel):
    """Content optimized for screen readers"""
    page: str
    element_id: Optional[str] = None
    aria_label: str
    aria_description: Optional[str] = None
    role: str
    content: str
    navigation_hints: List[str] = Field(default_factory=list)
    keyboard_shortcuts: List[str] = Field(default_factory=list)
    related_elements: List[str] = Field(default_factory=list)
    language: str = "en"

class HighContrastTheme(BaseModel):
    """High contrast theme configuration"""
    user_id: str
    theme_name: str
    background_color: str = "#000000"
    text_color: str = "#FFFFFF"
    link_color: str = "#FFFF00"
    button_color: str = "#FFFFFF"
    button_background: str = "#000000"
    border_color: str = "#FFFFFF"
    focus_color: str = "#FF0000"
    error_color: str = "#FF6666"
    success_color: str = "#66FF66"
    warning_color: str = "#FFFF66"
    custom_properties: Dict[str, str] = Field(default_factory=dict)
    is_active: bool = False

class UserPreferences(BaseModel):
    """General user experience preferences"""
    user_id: str
    language: str = "en"
    region: str = "IN"
    currency: str = "INR"
    measurement_units: str = "metric"
    date_format: str = "DD/MM/YYYY"
    time_format: str = "24h"
    notification_preferences: Dict[str, bool] = Field(default_factory=dict)
    interface_density: str = "normal"  # compact, normal, spacious
    animation_speed: str = "normal"  # slow, normal, fast, none
    auto_save_enabled: bool = True
    offline_mode_preferred: bool = False
    tutorial_completed: List[str] = Field(default_factory=list)
    onboarding_completed: bool = False
    updated_at: datetime = Field(default_factory=datetime.now)

class TutorialStep(BaseModel):
    """Individual tutorial step"""
    step_id: str
    title: str
    description: str
    content: str
    media_url: Optional[str] = None
    media_type: Optional[str] = None  # video, audio, image
    interactive_elements: List[Dict[str, Any]] = Field(default_factory=list)
    completion_criteria: Dict[str, Any] = Field(default_factory=dict)
    estimated_duration_minutes: int = 5
    accessibility_notes: Optional[str] = None
    keyboard_instructions: Optional[str] = None
    voice_instructions: Optional[str] = None

class Tutorial(BaseModel):
    """Complete tutorial definition"""
    tutorial_id: str
    tutorial_type: TutorialType
    title: str
    description: str
    language: str = "en"
    difficulty_level: str = "beginner"  # beginner, intermediate, advanced
    estimated_duration_minutes: int = 30
    prerequisites: List[str] = Field(default_factory=list)
    steps: List[TutorialStep] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    accessibility_features: List[AccessibilityFeature] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class TutorialProgress(BaseModel):
    """User's progress through tutorials"""
    user_id: str
    tutorial_id: str
    current_step: int = 0
    completed_steps: List[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.now)
    last_accessed: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    completion_percentage: float = 0.0
    time_spent_minutes: int = 0
    bookmarks: List[str] = Field(default_factory=list)
    notes: Dict[str, str] = Field(default_factory=dict)

class OnboardingStep(BaseModel):
    """Individual onboarding step"""
    step_id: str
    step_type: OnboardingStepType
    title: str
    description: str
    content: str
    required: bool = True
    skippable: bool = False
    form_fields: List[Dict[str, Any]] = Field(default_factory=list)
    validation_rules: Dict[str, Any] = Field(default_factory=dict)
    next_step_conditions: Dict[str, Any] = Field(default_factory=dict)
    accessibility_instructions: Optional[str] = None
    estimated_duration_minutes: int = 3

class OnboardingFlow(BaseModel):
    """Complete onboarding flow definition"""
    flow_id: str
    title: str
    description: str
    language: str = "en"
    target_user_type: str = "farmer"  # farmer, vendor, admin
    steps: List[OnboardingStep] = Field(default_factory=list)
    personalization_rules: Dict[str, Any] = Field(default_factory=dict)
    completion_rewards: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)

class OnboardingProgress(BaseModel):
    """User's onboarding progress"""
    user_id: str
    onboarding_id: str
    flow_id: str
    current_step: int = 0
    completed_steps: List[str] = Field(default_factory=list)
    step_data: Dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    skipped: bool = False
    completion_percentage: float = 0.0
    personalization_data: Dict[str, Any] = Field(default_factory=dict)

class UserFeedback(BaseModel):
    """User feedback for UX improvements"""
    feedback_id: str
    user_id: str
    feedback_type: str  # bug_report, feature_request, usability_issue, general
    content: str
    page: Optional[str] = None
    element: Optional[str] = None
    rating: Optional[int] = None  # 1-5 scale
    severity: Optional[str] = None  # low, medium, high, critical
    status: str = "open"  # open, in_progress, resolved, closed
    tags: List[str] = Field(default_factory=list)
    attachments: List[str] = Field(default_factory=list)
    user_agent: Optional[str] = None
    screen_resolution: Optional[str] = None
    accessibility_context: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class KeyboardShortcut(BaseModel):
    """Keyboard shortcut definition"""
    shortcut_id: str
    key_combination: str
    action: str
    description: str
    category: str  # navigation, actions, accessibility
    context: str  # global, page_specific, element_specific
    accessibility_friendly: bool = True
    customizable: bool = True
    default_enabled: bool = True

class VoiceCommand(BaseModel):
    """Voice command definition"""
    command_id: str
    trigger_phrases: List[str]
    action: str
    description: str
    category: str  # navigation, actions, queries
    context: str  # global, page_specific
    parameters: Dict[str, Any] = Field(default_factory=dict)
    confidence_threshold: float = 0.8
    language: str = "en"
    accessibility_optimized: bool = True

class NavigationResult(BaseModel):
    """Result of voice navigation processing"""
    command_recognized: bool
    action_taken: str
    target_element: Optional[str] = None
    navigation_path: List[str] = Field(default_factory=list)
    feedback_message: str
    audio_feedback: Optional[str] = None
    next_suggestions: List[str] = Field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None

class ContextualHelp(BaseModel):
    """Contextual help content"""
    page: str
    element: Optional[str] = None
    title: str
    content: str
    help_type: str  # tooltip, modal, sidebar, inline
    media_url: Optional[str] = None
    related_topics: List[str] = Field(default_factory=list)
    keyboard_shortcuts: List[str] = Field(default_factory=list)
    voice_commands: List[str] = Field(default_factory=list)
    accessibility_notes: Optional[str] = None
    language: str = "en"
    priority: int = 1  # 1-5, higher is more important

class AccessibilityAudit(BaseModel):
    """Accessibility audit results"""
    audit_id: str
    page: str
    timestamp: datetime = Field(default_factory=datetime.now)
    wcag_level: str = "AA"  # A, AA, AAA
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    passed_checks: List[str] = Field(default_factory=list)
    overall_score: float = 0.0
    recommendations: List[str] = Field(default_factory=list)
    automated_fixes: List[Dict[str, Any]] = Field(default_factory=list)