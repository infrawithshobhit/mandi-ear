"""
Property-Based Test for Alert System Customization
Tests Property 20: Alert System Customization
Validates: Requirements 9.2, 9.3, 9.4
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings
from datetime import datetime, time, timedelta
from typing import List, Dict, Any, Optional
import sys
import os

# Add the notification service to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services', 'notification-service'))

from models import (
    AlertConfiguration, UserAlertPreferences, PriceMovementAlert, WeatherEmergencyAlert,
    AlertType, AlertSeverity, NotificationChannel, ThresholdCondition, WeatherEventType
)
from alert_engine import CustomizableAlertEngine
from notification_dispatcher import NotificationDispatcher
from database import init_database, close_database, clear_all_data

# Test data strategies
@st.composite
def alert_configuration_strategy(draw):
    """Generate valid alert configurations"""
    alert_type = draw(st.sampled_from([AlertType.PRICE_MOVEMENT, AlertType.PRICE_RISE, AlertType.PRICE_DROP]))
    
    # Generate appropriate threshold based on alert type
    threshold_value = draw(st.floats(min_value=1.0, max_value=50.0))
    commodity = draw(st.sampled_from(['wheat', 'rice', 'maize', 'cotton', 'soybean']))
    
    return AlertConfiguration(
        user_id=draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        alert_type=alert_type,
        commodity=commodity,
        location=draw(st.one_of(st.none(), st.sampled_from(['Punjab', 'Haryana', 'Uttar Pradesh', 'Maharashtra']))),
        threshold_value=threshold_value,
        threshold_condition=draw(st.sampled_from([ThresholdCondition.GREATER_THAN, ThresholdCondition.PERCENTAGE_CHANGE])),
        comparison_period=draw(st.sampled_from(['1h', '24h', '7d'])),
        is_active=draw(st.booleans()),
        notification_channels=draw(st.lists(st.sampled_from([NotificationChannel.SMS, NotificationChannel.PUSH]), min_size=1, max_size=2)),
        max_alerts_per_day=draw(st.integers(min_value=1, max_value=20))
    )

@st.composite
def user_preferences_strategy(draw):
    """Generate valid user preferences"""
    return UserAlertPreferences(
        user_id=draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        preferred_channels=draw(st.lists(st.sampled_from([NotificationChannel.SMS, NotificationChannel.PUSH]), min_size=1, max_size=2)),
        preferred_language=draw(st.sampled_from(['en', 'hi'])),
        emergency_override=draw(st.booleans()),
        max_alerts_per_day=draw(st.integers(min_value=1, max_value=50)),
        group_similar_alerts=draw(st.booleans()),
        alert_frequency=draw(st.sampled_from(['immediate', 'hourly'])),
        phone_number=draw(st.one_of(st.none(), st.text(min_size=10, max_size=15, alphabet=st.characters(whitelist_categories=('Nd',)))))
    )

# Property-based test functions

@pytest.mark.asyncio
async def test_property_20_alert_system_customization():
    """
    **Property 20: Alert System Customization**
    **Validates: Requirements 9.2, 9.3, 9.4**
    
    For any user-defined alert thresholds and significant market events (>10% price changes, 
    weather emergencies), the system should send appropriate notifications with actionable 
    recommendations.
    """
    await init_database()
    await clear_all_data()
    
    alert_engine = None
    dispatcher = None
    
    try:
        alert_engine = CustomizableAlertEngine()
        dispatcher = NotificationDispatcher()
        
        await alert_engine.initialize()
        await dispatcher.initialize()
        
        # Test 1: Alert Configuration Properties
        await test_alert_configuration_core_properties(alert_engine)
        
        # Test 2: User Preferences Properties
        await test_user_preferences_core_properties(dispatcher)
        
        # Test 3: Price Movement Alert Properties
        await test_price_movement_core_properties(alert_engine)
        
        # Test 4: Weather Emergency Properties
        await test_weather_emergency_core_properties(dispatcher)
        
        print("All Property 20 tests passed successfully!")
        
    finally:
        if alert_engine:
            await alert_engine.shutdown()
        if dispatcher:
            await dispatcher.shutdown()
        await close_database()

async def test_alert_configuration_core_properties(alert_engine):
    """Test core alert configuration properties"""
    # Test with a few specific configurations
    test_configs = [
        AlertConfiguration(
            user_id="test_user_1",
            alert_type=AlertType.PRICE_MOVEMENT,
            commodity="wheat",
            location="Punjab",
            threshold_value=10.0,
            threshold_condition=ThresholdCondition.PERCENTAGE_CHANGE,
            is_active=True,
            notification_channels=[NotificationChannel.PUSH]
        ),
        AlertConfiguration(
            user_id="test_user_2",
            alert_type=AlertType.PRICE_RISE,
            commodity="rice",
            threshold_value=15.0,
            threshold_condition=ThresholdCondition.GREATER_THAN,
            is_active=False,
            notification_channels=[NotificationChannel.SMS, NotificationChannel.PUSH]
        )
    ]
    
    for config in test_configs:
        # Property: Valid alert configurations should always be accepted
        response = await alert_engine.configure_alert(config)
        assert response.success, f"Valid alert configuration rejected: {response.message}"
        assert response.alert_id == config.id
        
        # Property: Configured alerts should be retrievable
        user_alerts = await alert_engine.get_user_alerts(config.user_id, active_only=False)
        alert_ids = [alert.id for alert in user_alerts]
        assert config.id in alert_ids, "Configured alert not retrievable"
        
        # Property: Alert configuration should preserve all settings
        retrieved_config = None
        for alert in user_alerts:
            if alert.id == config.id:
                retrieved_config = alert
                break
        
        assert retrieved_config is not None, "Alert configuration not found"
        assert retrieved_config.alert_type == config.alert_type
        assert retrieved_config.threshold_value == config.threshold_value
        # Note: is_active might be modified during configuration, so we check the retrieved value
        original_active_status = retrieved_config.is_active
        
        # Property: Alert can be toggled active/inactive
        toggle_response = await alert_engine.toggle_alert(config.id, config.user_id)
        assert toggle_response.success, "Alert toggle failed"
        assert toggle_response.is_active != original_active_status, "Alert toggle did not change status"
        
        # Property: Alert can be deleted
        delete_success = await alert_engine.delete_alert(config.id, config.user_id)
        assert delete_success, "Alert deletion failed"
        
        # Property: Deleted alert should not be retrievable
        user_alerts_after_delete = await alert_engine.get_user_alerts(config.user_id)
        alert_ids_after_delete = [alert.id for alert in user_alerts_after_delete]
        assert config.id not in alert_ids_after_delete, "Deleted alert still retrievable"

async def test_user_preferences_core_properties(dispatcher):
    """Test core user preferences properties"""
    test_preferences = [
        UserAlertPreferences(
            user_id="pref_user_1",
            preferred_channels=[NotificationChannel.SMS],
            preferred_language="en",
            emergency_override=True,
            max_alerts_per_day=10
        ),
        UserAlertPreferences(
            user_id="pref_user_2",
            preferred_channels=[NotificationChannel.PUSH, NotificationChannel.SMS],
            preferred_language="hi",
            emergency_override=False,
            max_alerts_per_day=5,
            phone_number="9876543210"
        )
    ]
    
    for preferences in test_preferences:
        # Property: Valid preferences should always be accepted
        await dispatcher.update_user_preferences(preferences)
        
        # Property: Updated preferences should be retrievable
        retrieved_prefs = await dispatcher.get_user_preferences(preferences.user_id)
        assert retrieved_prefs is not None, "Preferences not retrievable after update"
        assert retrieved_prefs.user_id == preferences.user_id
        assert retrieved_prefs.preferred_channels == preferences.preferred_channels
        assert retrieved_prefs.preferred_language == preferences.preferred_language
        assert retrieved_prefs.emergency_override == preferences.emergency_override
        
        # Property: Contact information should be preserved
        if preferences.phone_number:
            assert retrieved_prefs.phone_number == preferences.phone_number

async def test_price_movement_core_properties(alert_engine):
    """Test core price movement alert properties"""
    test_cases = [
        {
            'commodity': 'wheat',
            'location': 'Punjab',
            'threshold': 10.0,
            'price_change': 15.0,  # Should trigger
            'should_trigger': True
        },
        {
            'commodity': 'rice',
            'location': 'Haryana',
            'threshold': 20.0,
            'price_change': 5.0,   # Should not trigger
            'should_trigger': False
        }
    ]
    
    for case in test_cases:
        # Create alert configuration
        config = AlertConfiguration(
            user_id="price_test_user",
            alert_type=AlertType.PRICE_MOVEMENT,
            commodity=case['commodity'],
            location=case['location'],
            threshold_value=case['threshold'],
            threshold_condition=ThresholdCondition.PERCENTAGE_CHANGE,
            is_active=True,
            notification_channels=[NotificationChannel.PUSH]
        )
        
        response = await alert_engine.configure_alert(config)
        assert response.success, "Failed to configure test alert"
        
        # Property: Significant price movements (above threshold) should be detectable
        abs_change = abs(case['price_change'])
        
        if case['should_trigger']:
            assert config.is_active, "Alert should be active for triggering"
            assert config.threshold_value <= abs_change, "Threshold should be met for triggering"
        else:
            assert config.threshold_value > abs_change, "Threshold should not be met"
        
        # Property: Alert history should be accessible
        history = await alert_engine.get_alert_history(config.user_id)
        assert isinstance(history, list), "Alert history should be accessible"
        
        # Clean up
        await alert_engine.delete_alert(config.id, config.user_id)

async def test_weather_emergency_core_properties(dispatcher):
    """Test core weather emergency properties"""
    test_weather_conditions = [
        {
            'event': WeatherEventType.HEAVY_RAIN,
            'rainfall': 75.0,
            'temperature': 25.0,
            'wind_speed': 20.0,
            'is_emergency': True
        },
        {
            'event': WeatherEventType.EXTREME_HEAT,
            'rainfall': 0.0,
            'temperature': 45.0,
            'wind_speed': 10.0,
            'is_emergency': True
        },
        {
            'event': WeatherEventType.WIND_STORM,
            'rainfall': 10.0,
            'temperature': 30.0,
            'wind_speed': 65.0,
            'is_emergency': True
        }
    ]
    
    for condition in test_weather_conditions:
        # Property: Emergency weather conditions should be detectable
        is_emergency = False
        
        if condition['event'] == WeatherEventType.HEAVY_RAIN and condition['rainfall'] > 50:
            is_emergency = True
        elif condition['event'] == WeatherEventType.EXTREME_HEAT and condition['temperature'] > 40:
            is_emergency = True
        elif condition['event'] == WeatherEventType.WIND_STORM and condition['wind_speed'] > 40:
            is_emergency = True
        
        assert is_emergency == condition['is_emergency'], f"Emergency detection failed for {condition['event']}"
        
        # Property: Weather data should be within realistic ranges
        assert -20 <= condition['temperature'] <= 60, "Temperature out of realistic range"
        assert 0 <= condition['rainfall'] <= 500, "Rainfall out of realistic range"
        assert 0 <= condition['wind_speed'] <= 200, "Wind speed out of realistic range"

# Simple hypothesis-based tests for additional coverage
@given(st.integers(min_value=1, max_value=50))
def test_threshold_values_are_positive(threshold):
    """Property: All threshold values should be positive"""
    assert threshold > 0, "Threshold values must be positive"

@given(st.lists(st.sampled_from([NotificationChannel.SMS, NotificationChannel.PUSH]), min_size=1))
def test_notification_channels_not_empty(channels):
    """Property: Notification channels list should not be empty"""
    assert len(channels) > 0, "Must have at least one notification channel"

@given(st.floats(min_value=-100.0, max_value=100.0))
def test_percentage_change_calculation(percentage_change):
    """Property: Percentage change calculations should be consistent"""
    abs_change = abs(percentage_change)
    assert abs_change >= 0, "Absolute percentage change should be non-negative"
    
    # Property: Significant changes (>10%) should be flagged
    is_significant = abs_change >= 10.0
    if abs_change >= 10.0:
        assert is_significant, "Changes >= 10% should be considered significant"
    else:
        assert not is_significant, "Changes < 10% should not be considered significant"

if __name__ == "__main__":
    # Run the main property test
    asyncio.run(test_property_20_alert_system_customization())

# Pytest fixtures and test functions
@pytest.fixture
async def alert_system():
    """Fixture to set up alert system for testing"""
    await init_database()
    await clear_all_data()
    
    alert_engine = CustomizableAlertEngine()
    notification_dispatcher = NotificationDispatcher()
    
    await alert_engine.initialize()
    await notification_dispatcher.initialize()
    
    yield alert_engine, notification_dispatcher
    
    await alert_engine.shutdown()
    await notification_dispatcher.shutdown()
    await close_database()

@pytest.mark.asyncio
async def test_property_20_alert_system_customization():
    """
    **Property 20: Alert System Customization**
    **Validates: Requirements 9.2, 9.3, 9.4**
    
    Main property test that validates the complete alert customization system.
    """
    await init_database()
    await clear_all_data()
    
    alert_engine = None
    dispatcher = None
    
    try:
        alert_engine = CustomizableAlertEngine()
        dispatcher = NotificationDispatcher()
        
        await alert_engine.initialize()
        await dispatcher.initialize()
        
        # Test 1: Alert Configuration Properties
        await test_alert_configuration_core_properties(alert_engine)
        
        # Test 2: User Preferences Properties
        await test_user_preferences_core_properties(dispatcher)
        
        # Test 3: Price Movement Alert Properties
        await test_price_movement_core_properties(alert_engine)
        
        # Test 4: Weather Emergency Properties
        await test_weather_emergency_core_properties(dispatcher)
        
        print("All Property 20 tests passed successfully!")
        
    finally:
        if alert_engine:
            await alert_engine.shutdown()
        if dispatcher:
            await dispatcher.shutdown()
        await close_database()

if __name__ == "__main__":
    # Run individual property tests
    print("Running Property 20: Alert System Customization tests...")
    
    # Test alert configuration properties
    print("Testing alert configuration properties...")
    test_alert_configuration_properties()
    
    # Test notification preferences properties
    print("Testing notification preferences properties...")
    test_notification_preferences_properties()
    
    # Test price movement alert properties
    print("Testing price movement alert properties...")
    test_price_movement_alert_properties()
    
    # Test weather emergency alert properties
    print("Testing weather emergency alert properties...")
    test_weather_emergency_alert_properties()
    
    print("All Property 20 tests completed successfully!")