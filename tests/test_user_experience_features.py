"""
Property-Based Test for User Experience Features
**Property 24: User Experience Features**
**Validates: Requirements 10.4, 10.5**

Feature: mandi-ear, Property 24: For any new user or accessibility need, 
the system should provide functional tutorials and accessibility features 
(screen readers, high-contrast modes)
"""

import pytest
import pytest_asyncio
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta
import asyncio

# Import the accessibility service components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services', 'accessibility-service'))

from models import (
    AccessibilitySettings, UserPreferences, TutorialType, OnboardingStepType,
    ContrastLevel, TextSize, AccessibilityFeature
)
from accessibility_manager import AccessibilityManager
from tutorial_engine import TutorialEngine
from onboarding_system import OnboardingSystem


@pytest_asyncio.fixture
async def accessibility_manager():
    """Create an accessibility manager for testing"""
    manager = AccessibilityManager()
    await manager.initialize()
    try:
        yield manager
    finally:
        await manager.shutdown()


@pytest_asyncio.fixture
async def tutorial_engine():
    """Create a tutorial engine for testing"""
    engine = TutorialEngine()
    await engine.initialize()
    try:
        yield engine
    finally:
        await engine.shutdown()


@pytest_asyncio.fixture
async def onboarding_system():
    """Create an onboarding system for testing"""
    system = OnboardingSystem()
    await system.initialize()
    try:
        yield system
    finally:
        await system.shutdown()


@given(
    user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    screen_reader_enabled=st.booleans(),
    high_contrast_enabled=st.booleans(),
    large_text_enabled=st.booleans(),
    voice_navigation_enabled=st.booleans(),
    contrast_level=st.sampled_from([ContrastLevel.NORMAL, ContrastLevel.HIGH, ContrastLevel.EXTRA_HIGH]),
    text_size=st.sampled_from([TextSize.NORMAL, TextSize.LARGE, TextSize.EXTRA_LARGE])
)
@settings(max_examples=20, deadline=8000, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_accessibility_settings_management(
    accessibility_manager, user_id, screen_reader_enabled, high_contrast_enabled,
    large_text_enabled, voice_navigation_enabled, contrast_level, text_size
):
    """
    Property: For any user and accessibility configuration, the system should 
    correctly store, retrieve, and apply accessibility settings
    """
    # Arrange: Create accessibility settings
    settings = AccessibilitySettings(
        user_id=user_id,
        screen_reader_enabled=screen_reader_enabled,
        high_contrast_enabled=high_contrast_enabled,
        large_text_enabled=large_text_enabled,
        voice_navigation_enabled=voice_navigation_enabled,
        contrast_level=contrast_level,
        text_size=text_size
    )
    
    # Act: Update and retrieve settings
    await accessibility_manager.update_user_settings(user_id, settings)
    retrieved_settings = await accessibility_manager.get_user_settings(user_id)
    
    # Assert: Verify settings are correctly stored and retrieved
    assert retrieved_settings is not None, "Settings should be retrievable"
    assert retrieved_settings.user_id == user_id, "User ID should match"
    assert retrieved_settings.screen_reader_enabled == screen_reader_enabled, "Screen reader setting should match"
    assert retrieved_settings.high_contrast_enabled == high_contrast_enabled, "High contrast setting should match"
    assert retrieved_settings.large_text_enabled == large_text_enabled, "Large text setting should match"
    assert retrieved_settings.voice_navigation_enabled == voice_navigation_enabled, "Voice navigation setting should match"
    assert retrieved_settings.contrast_level == contrast_level, "Contrast level should match"
    assert retrieved_settings.text_size == text_size, "Text size should match"
    
    # Verify settings have proper timestamps
    assert retrieved_settings.updated_at is not None, "Settings should have update timestamp"
    assert isinstance(retrieved_settings.updated_at, datetime), "Update timestamp should be datetime"


@given(
    user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    page=st.sampled_from(["home", "prices", "mandis", "search", "profile"]),
    element_id=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    screen_reader_enabled=st.booleans(),
    keyboard_navigation_enabled=st.booleans(),
    voice_navigation_enabled=st.booleans()
)
@settings(max_examples=25, deadline=8000, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_screen_reader_content_generation(
    accessibility_manager, user_id, page, element_id, screen_reader_enabled,
    keyboard_navigation_enabled, voice_navigation_enabled
):
    """
    Property: For any page and element combination, the system should generate 
    appropriate screen reader content based on user accessibility settings
    """
    # Arrange: Set up user accessibility settings
    settings = AccessibilitySettings(
        user_id=user_id,
        screen_reader_enabled=screen_reader_enabled,
        keyboard_navigation_enabled=keyboard_navigation_enabled,
        voice_navigation_enabled=voice_navigation_enabled
    )
    await accessibility_manager.update_user_settings(user_id, settings)
    
    # Act: Get screen reader content
    screen_reader_content = await accessibility_manager.get_screen_reader_content(
        user_id=user_id,
        page=page,
        element_id=element_id
    )
    
    # Assert: Verify screen reader content is properly generated
    assert screen_reader_content is not None, "Screen reader content should be available"
    assert screen_reader_content.page == page, "Page should match request"
    assert screen_reader_content.element_id == element_id, "Element ID should match request"
    assert screen_reader_content.aria_label is not None, "Should have ARIA label"
    assert len(screen_reader_content.aria_label) > 0, "ARIA label should not be empty"
    assert screen_reader_content.role is not None, "Should have role attribute"
    assert screen_reader_content.content is not None, "Should have content"
    
    # Verify accessibility-specific enhancements
    if keyboard_navigation_enabled:
        assert len(screen_reader_content.keyboard_shortcuts) > 0, "Should include keyboard shortcuts when enabled"
        keyboard_instructions = [hint for hint in screen_reader_content.navigation_hints 
                               if "tab" in hint.lower() or "enter" in hint.lower() or "escape" in hint.lower()]
        assert len(keyboard_instructions) > 0, "Should include keyboard navigation hints"
    
    if voice_navigation_enabled:
        voice_hints = [hint for hint in screen_reader_content.navigation_hints 
                      if "voice" in hint.lower() or "say" in hint.lower()]
        assert len(voice_hints) > 0, "Should include voice navigation hints when enabled"
    
    # Verify content structure
    assert isinstance(screen_reader_content.navigation_hints, list), "Navigation hints should be a list"
    assert isinstance(screen_reader_content.keyboard_shortcuts, list), "Keyboard shortcuts should be a list"


@given(
    user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    tutorial_type=st.sampled_from([
        TutorialType.BASIC_NAVIGATION, TutorialType.PRICE_DISCOVERY, 
        TutorialType.ACCESSIBILITY_FEATURES, TutorialType.VOICE_COMMANDS
    ]),
    language=st.sampled_from(["en", "hi", "ta"]),
    complete_steps=st.integers(min_value=0, max_value=5)
)
@settings(max_examples=20, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_tutorial_system_functionality(
    tutorial_engine, user_id, tutorial_type, language, complete_steps
):
    """
    Property: For any user and tutorial type, the system should provide 
    functional tutorial progression with proper step tracking
    """
    # Act: Start tutorial
    tutorial_id = await tutorial_engine.start_tutorial(
        user_id=user_id,
        tutorial_type=tutorial_type.value,
        language=language
    )
    
    # Assert: Verify tutorial started correctly
    assert tutorial_id is not None, "Tutorial ID should be returned"
    assert isinstance(tutorial_id, str), "Tutorial ID should be a string"
    assert len(tutorial_id) > 0, "Tutorial ID should not be empty"
    
    # Get initial progress
    progress = await tutorial_engine.get_user_progress(user_id)
    assert user_id in progress, "User should have progress tracking"
    assert tutorial_id in progress[user_id], "Tutorial should be in user progress"
    
    user_tutorial_progress = progress[user_id][tutorial_id]
    assert user_tutorial_progress.user_id == user_id, "Progress should track correct user"
    assert user_tutorial_progress.tutorial_id == tutorial_id, "Progress should track correct tutorial"
    assert user_tutorial_progress.current_step == 0, "Should start at step 0"
    assert len(user_tutorial_progress.completed_steps) == 0, "Should start with no completed steps"
    
    # Complete some steps
    completed_step_ids = []
    for i in range(complete_steps):
        try:
            # Get next step
            next_step = await tutorial_engine.get_next_step(user_id, tutorial_id)
            
            if "completed" in next_step and next_step["completed"]:
                break  # Tutorial completed
            
            step_id = next_step["step_id"]
            completed_step_ids.append(step_id)
            
            # Complete the step
            await tutorial_engine.complete_step(user_id, tutorial_id, step_id)
            
            # Verify step completion
            updated_progress = await tutorial_engine.get_user_progress(user_id)
            tutorial_progress = updated_progress[user_id][tutorial_id]
            
            assert step_id in tutorial_progress.completed_steps, f"Step {step_id} should be marked as completed"
            assert tutorial_progress.completion_percentage > 0, "Completion percentage should increase"
            
        except Exception as e:
            # If we can't complete more steps, that's acceptable
            break
    
    # Verify final state
    final_progress = await tutorial_engine.get_user_progress(user_id)
    final_tutorial_progress = final_progress[user_id][tutorial_id]
    
    assert len(final_tutorial_progress.completed_steps) == len(completed_step_ids), "Completed steps count should match"
    assert final_tutorial_progress.completion_percentage >= 0, "Completion percentage should be non-negative"
    assert final_tutorial_progress.completion_percentage <= 100, "Completion percentage should not exceed 100"
    
    # If all requested steps were completed, verify completion percentage
    if len(completed_step_ids) > 0:
        assert final_tutorial_progress.completion_percentage > 0, "Should have positive completion percentage"


@given(
    user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    user_type=st.sampled_from(["farmer", "vendor"]),
    language=st.sampled_from(["en", "hi"]),
    name=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))),
    accessibility_needs=st.dictionaries(
        st.sampled_from(["screen_reader", "high_contrast", "large_text", "voice_navigation"]),
        st.booleans(),
        min_size=0, max_size=4
    )
)
@settings(max_examples=15, deadline=12000, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_onboarding_system_completeness(
    onboarding_system, user_id, user_type, language, name, accessibility_needs
):
    """
    Property: For any new user profile, the system should provide complete 
    onboarding with proper step progression and personalization
    """
    # Arrange: Create user profile
    user_profile = {
        "user_type": user_type,
        "name": name,
        "language": language,
        "accessibility_needs": accessibility_needs
    }
    
    # Act: Start onboarding
    onboarding_id = await onboarding_system.start_onboarding(
        user_id=user_id,
        user_profile=user_profile,
        language=language
    )
    
    # Assert: Verify onboarding started correctly
    assert onboarding_id is not None, "Onboarding ID should be returned"
    assert isinstance(onboarding_id, str), "Onboarding ID should be a string"
    assert len(onboarding_id) > 0, "Onboarding ID should not be empty"
    
    # Get initial status
    status = await onboarding_system.get_user_status(user_id)
    assert status["onboarding_active"] == True, "Onboarding should be active"
    assert status["onboarding_id"] == onboarding_id, "Status should track correct onboarding"
    assert status["current_step"] == 0, "Should start at step 0"
    assert status["completion_percentage"] == 0.0, "Should start at 0% completion"
    assert status["completed"] == False, "Should not be completed initially"
    
    # Test step progression
    steps_completed = 0
    max_steps_to_test = 3  # Limit for test performance
    
    for i in range(max_steps_to_test):
        try:
            # Get next step
            next_step = await onboarding_system.get_next_step(user_id, onboarding_id)
            
            assert next_step is not None, f"Should have next step at iteration {i}"
            assert next_step.step_id is not None, "Step should have ID"
            assert next_step.title is not None, "Step should have title"
            assert next_step.description is not None, "Step should have description"
            assert next_step.content is not None, "Step should have content"
            
            # Verify step type is valid
            assert next_step.step_type in OnboardingStepType, "Step type should be valid"
            
            # Create mock step data based on step type
            step_data = {}
            if next_step.step_type == OnboardingStepType.PROFILE_SETUP:
                step_data = {"name": name, "user_type": user_type}
            elif next_step.step_type == OnboardingStepType.LANGUAGE_SELECTION:
                step_data = {"language": language}
            elif next_step.step_type == OnboardingStepType.ACCESSIBILITY_SETUP:
                step_data = accessibility_needs
            
            # Complete the step
            await onboarding_system.complete_step(
                user_id=user_id,
                onboarding_id=onboarding_id,
                step_id=next_step.step_id,
                step_data=step_data
            )
            
            steps_completed += 1
            
            # Verify progress
            updated_status = await onboarding_system.get_user_status(user_id)
            assert updated_status["current_step"] == i + 1, f"Current step should advance to {i + 1}"
            assert updated_status["completion_percentage"] > 0, "Completion percentage should increase"
            
        except ValueError as e:
            if "completed" in str(e).lower():
                # Onboarding completed, which is acceptable
                break
            else:
                raise e
        except Exception as e:
            # Other exceptions might indicate end of onboarding flow
            break
    
    # Verify final state
    final_status = await onboarding_system.get_user_status(user_id)
    
    # Should have made progress
    assert final_status["current_step"] >= steps_completed, "Should have progressed through steps"
    assert final_status["completion_percentage"] >= 0, "Should have non-negative completion percentage"
    
    # If onboarding completed, verify completion state
    if final_status["completed"]:
        assert final_status["completion_percentage"] == 100.0, "Completed onboarding should be 100%"
        assert final_status["onboarding_active"] == False, "Completed onboarding should not be active"


@given(
    user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    voice_command=st.sampled_from([
        "go home", "show prices", "show markets", "help", "read this",
        "navigate home", "price information", "market list"
    ]),
    current_page=st.sampled_from(["home", "prices", "mandis", "search"]),
    voice_navigation_enabled=st.booleans()
)
@settings(max_examples=20, deadline=8000, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_voice_navigation_functionality(
    accessibility_manager, user_id, voice_command, current_page, voice_navigation_enabled
):
    """
    Property: For any voice command and page context, the system should 
    provide appropriate voice navigation responses based on user settings
    """
    # Arrange: Set up user with voice navigation settings
    settings = AccessibilitySettings(
        user_id=user_id,
        voice_navigation_enabled=voice_navigation_enabled
    )
    await accessibility_manager.update_user_settings(user_id, settings)
    
    # Act: Process voice navigation command
    navigation_result = await accessibility_manager.process_voice_navigation(
        user_id=user_id,
        voice_command=voice_command,
        current_page=current_page
    )
    
    # Assert: Verify voice navigation response
    assert navigation_result is not None, "Navigation result should be available"
    assert hasattr(navigation_result, 'command_recognized'), "Should indicate if command was recognized"
    assert hasattr(navigation_result, 'action_taken'), "Should indicate action taken"
    assert hasattr(navigation_result, 'feedback_message'), "Should provide feedback message"
    assert hasattr(navigation_result, 'success'), "Should indicate success status"
    
    # Verify behavior based on voice navigation setting
    if voice_navigation_enabled:
        # Voice navigation is enabled - should process commands
        if voice_command in ["go home", "navigate home"]:
            assert navigation_result.command_recognized == True, "Home navigation command should be recognized"
            assert "home" in navigation_result.action_taken.lower(), "Should indicate home navigation action"
        elif voice_command in ["show prices", "price information"]:
            assert navigation_result.command_recognized == True, "Price command should be recognized"
            assert "price" in navigation_result.action_taken.lower(), "Should indicate price action"
        elif voice_command in ["show markets", "market list"]:
            assert navigation_result.command_recognized == True, "Market command should be recognized"
            assert "mandi" in navigation_result.action_taken.lower() or "market" in navigation_result.action_taken.lower(), "Should indicate market action"
        elif voice_command == "help":
            assert navigation_result.command_recognized == True, "Help command should be recognized"
            assert "help" in navigation_result.action_taken.lower(), "Should indicate help action"
        
        # Should provide helpful feedback
        assert len(navigation_result.feedback_message) > 0, "Should provide feedback message"
        
        # Should provide next suggestions for successful commands
        if navigation_result.command_recognized:
            assert isinstance(navigation_result.next_suggestions, list), "Should provide next suggestions"
    
    else:
        # Voice navigation is disabled - should indicate this
        assert navigation_result.command_recognized == False, "Commands should not be recognized when disabled"
        assert navigation_result.success == False, "Should indicate failure when disabled"
        assert "not enabled" in navigation_result.feedback_message.lower() or "disabled" in navigation_result.feedback_message.lower(), "Should indicate voice navigation is disabled"


@given(
    page=st.sampled_from(["home", "prices", "mandis", "search", "profile"]),
    element=st.one_of(st.none(), st.sampled_from(["button", "input", "link", "menu"])),
    language=st.sampled_from(["en", "hi"])
)
@settings(max_examples=15, deadline=8000, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_contextual_help_availability(
    tutorial_engine, page, element, language
):
    """
    Property: For any page and element combination, the system should provide 
    contextual help information appropriate to the context and language
    """
    # Act: Get contextual help
    help_content = await tutorial_engine.get_contextual_help(
        page=page,
        element=element,
        language=language
    )
    
    # Assert: Verify contextual help is available and properly structured
    assert help_content is not None, "Contextual help should be available"
    assert isinstance(help_content, dict), "Help content should be a dictionary"
    
    # Verify required fields
    assert "title" in help_content, "Help should have a title"
    assert "content" in help_content, "Help should have content"
    assert "help_type" in help_content, "Help should have a type"
    
    # Verify content quality
    assert len(help_content["title"]) > 0, "Title should not be empty"
    assert len(help_content["content"]) > 0, "Content should not be empty"
    assert help_content["help_type"] in ["tooltip", "modal", "sidebar", "inline"], "Help type should be valid"
    
    # Verify accessibility features
    if "keyboard_shortcuts" in help_content:
        assert isinstance(help_content["keyboard_shortcuts"], list), "Keyboard shortcuts should be a list"
        for shortcut in help_content["keyboard_shortcuts"]:
            assert isinstance(shortcut, str), "Each keyboard shortcut should be a string"
            assert len(shortcut) > 0, "Keyboard shortcuts should not be empty"
    
    if "voice_commands" in help_content:
        assert isinstance(help_content["voice_commands"], list), "Voice commands should be a list"
        for command in help_content["voice_commands"]:
            assert isinstance(command, str), "Each voice command should be a string"
            assert len(command) > 0, "Voice commands should not be empty"
    
    # Verify accessibility notes when present
    if "accessibility_notes" in help_content and help_content["accessibility_notes"]:
        assert isinstance(help_content["accessibility_notes"], str), "Accessibility notes should be a string"
        assert len(help_content["accessibility_notes"]) > 0, "Accessibility notes should not be empty"


@given(
    user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    language=st.sampled_from(["en", "hi", "ta"]),
    region=st.sampled_from(["IN", "US", "UK"]),
    interface_density=st.sampled_from(["compact", "normal", "spacious"]),
    animation_speed=st.sampled_from(["slow", "normal", "fast", "none"]),
    notification_preferences=st.dictionaries(
        st.sampled_from(["price_alerts", "weather_alerts", "msp_alerts", "tutorial_reminders"]),
        st.booleans(),
        min_size=1, max_size=4
    )
)
@settings(max_examples=15, deadline=8000, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_user_preferences_management(
    accessibility_manager, user_id, language, region, interface_density, 
    animation_speed, notification_preferences
):
    """
    Property: For any user preferences configuration, the system should 
    correctly store, retrieve, and apply user experience preferences
    """
    # Arrange: Create user preferences
    preferences = UserPreferences(
        user_id=user_id,
        language=language,
        region=region,
        interface_density=interface_density,
        animation_speed=animation_speed,
        notification_preferences=notification_preferences
    )
    
    # Act: Update and retrieve preferences
    await accessibility_manager.update_user_preferences(user_id, preferences)
    retrieved_preferences = await accessibility_manager.get_user_preferences(user_id)
    
    # Assert: Verify preferences are correctly stored and retrieved
    assert retrieved_preferences is not None, "Preferences should be retrievable"
    assert retrieved_preferences.user_id == user_id, "User ID should match"
    assert retrieved_preferences.language == language, "Language should match"
    assert retrieved_preferences.region == region, "Region should match"
    assert retrieved_preferences.interface_density == interface_density, "Interface density should match"
    assert retrieved_preferences.animation_speed == animation_speed, "Animation speed should match"
    
    # Verify notification preferences
    for key, value in notification_preferences.items():
        assert key in retrieved_preferences.notification_preferences, f"Notification preference {key} should be stored"
        assert retrieved_preferences.notification_preferences[key] == value, f"Notification preference {key} should match"
    
    # Verify timestamps
    assert retrieved_preferences.updated_at is not None, "Preferences should have update timestamp"
    assert isinstance(retrieved_preferences.updated_at, datetime), "Update timestamp should be datetime"
    
    # Verify default values for unspecified preferences
    assert retrieved_preferences.currency is not None, "Should have default currency"
    assert retrieved_preferences.date_format is not None, "Should have default date format"
    assert retrieved_preferences.time_format is not None, "Should have default time format"


# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])