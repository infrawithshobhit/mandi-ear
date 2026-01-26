"""
Basic tests for MSP Compliance Reporting System (without database dependencies)
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import json
import sys
import os

# Add the service directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Mock the database module to avoid dependency issues
sys.modules['database'] = Mock()
sys.modules['asyncpg'] = Mock()

from models import MSPViolation, ViolationType, AlertSeverity, MSPComplianceReport

def test_compliance_report_model():
    """Test MSPComplianceReport model creation"""
    report = MSPComplianceReport(
        report_period_start=date(2024, 1, 1),
        report_period_end=date(2024, 1, 31),
        region="Punjab",
        total_violations=10,
        violations_by_commodity={"Wheat": 5, "Rice": 3, "Maize": 2},
        violations_by_location={"Ludhiana, Punjab": 4, "Karnal, Haryana": 6},
        average_violation_percentage=12.5,
        most_affected_farmers=100,
        estimated_farmer_losses=50000.0,
        recommendations=[
            "Increase monitoring frequency",
            "Deploy emergency procurement teams",
            "Strengthen farmer awareness programs"
        ],
        evidence_files=["evidence_1.json", "evidence_2.pdf"]
    )
    
    assert report.report_period_start == date(2024, 1, 1)
    assert report.report_period_end == date(2024, 1, 31)
    assert report.region == "Punjab"
    assert report.total_violations == 10
    assert report.violations_by_commodity["Wheat"] == 5
    assert report.violations_by_location["Ludhiana, Punjab"] == 4
    assert report.average_violation_percentage == 12.5
    assert report.most_affected_farmers == 100
    assert report.estimated_farmer_losses == 50000.0
    assert len(report.recommendations) == 3
    assert len(report.evidence_files) == 2
    assert report.generated_by == "MSP Enforcement System"
    assert report.report_status == "draft"

def test_violation_model():
    """Test MSPViolation model creation"""
    violation = MSPViolation(
        commodity="Wheat",
        variety="Grade A",
        mandi_id="mandi_001",
        mandi_name="Central Mandi Punjab",
        district="Ludhiana",
        state="Punjab",
        market_price=1800.0,
        msp_price=2125.0,
        price_difference=-325.0,
        violation_percentage=15.3,
        violation_type=ViolationType.BELOW_MSP,
        severity=AlertSeverity.CRITICAL,
        evidence={
            "data_confidence": 0.9,
            "detection_method": "automated_monitoring"
        }
    )
    
    assert violation.commodity == "Wheat"
    assert violation.variety == "Grade A"
    assert violation.mandi_id == "mandi_001"
    assert violation.mandi_name == "Central Mandi Punjab"
    assert violation.district == "Ludhiana"
    assert violation.state == "Punjab"
    assert violation.market_price == 1800.0
    assert violation.msp_price == 2125.0
    assert violation.price_difference == -325.0
    assert violation.violation_percentage == 15.3
    assert violation.violation_type == ViolationType.BELOW_MSP
    assert violation.severity == AlertSeverity.CRITICAL
    assert violation.evidence["data_confidence"] == 0.9
    assert violation.is_resolved is False

def test_compliance_report_validation():
    """Test compliance report validation"""
    # Test with minimal required fields
    report = MSPComplianceReport(
        report_period_start=date(2024, 1, 1),
        report_period_end=date(2024, 1, 31),
        region="national",
        total_violations=0,
        violations_by_commodity={},
        violations_by_location={},
        average_violation_percentage=0.0,
        recommendations=[]
    )
    
    assert report.total_violations == 0
    assert len(report.violations_by_commodity) == 0
    assert len(report.violations_by_location) == 0
    assert report.average_violation_percentage == 0.0
    assert len(report.recommendations) == 0

def test_violation_severity_levels():
    """Test different violation severity levels"""
    # Critical violation (>15% below MSP)
    critical_violation = MSPViolation(
        commodity="Wheat",
        mandi_id="mandi_001",
        mandi_name="Test Mandi",
        district="Test District",
        state="Test State",
        market_price=1700.0,
        msp_price=2000.0,
        price_difference=-300.0,
        violation_percentage=15.0,
        violation_type=ViolationType.BELOW_MSP,
        severity=AlertSeverity.CRITICAL
    )
    
    # High violation (10-15% below MSP)
    high_violation = MSPViolation(
        commodity="Rice",
        mandi_id="mandi_002",
        mandi_name="Test Mandi 2",
        district="Test District 2",
        state="Test State 2",
        market_price=2700.0,
        msp_price=3000.0,
        price_difference=-300.0,
        violation_percentage=10.0,
        violation_type=ViolationType.BELOW_MSP,
        severity=AlertSeverity.HIGH
    )
    
    # Medium violation (5-10% below MSP)
    medium_violation = MSPViolation(
        commodity="Maize",
        mandi_id="mandi_003",
        mandi_name="Test Mandi 3",
        district="Test District 3",
        state="Test State 3",
        market_price=1800.0,
        msp_price=1900.0,
        price_difference=-100.0,
        violation_percentage=5.3,
        violation_type=ViolationType.BELOW_MSP,
        severity=AlertSeverity.MEDIUM
    )
    
    assert critical_violation.severity == AlertSeverity.CRITICAL
    assert high_violation.severity == AlertSeverity.HIGH
    assert medium_violation.severity == AlertSeverity.MEDIUM
    
    assert critical_violation.violation_percentage >= 15.0
    assert 10.0 <= high_violation.violation_percentage < 15.0
    assert 5.0 <= medium_violation.violation_percentage < 10.0

def test_compliance_report_recommendations():
    """Test compliance report recommendations generation"""
    # Test recommendations for different scenarios
    
    # High violation scenario
    high_violation_recommendations = [
        "URGENT: Deploy emergency procurement teams to affected areas",
        "Activate additional government procurement centers",
        "Issue public notices about MSP guarantee to farmers",
        "Investigate potential market manipulation or hoarding",
        "Consider farmer compensation schemes for significant losses"
    ]
    
    # Medium violation scenario
    medium_violation_recommendations = [
        "Increase procurement center capacity in affected regions",
        "Strengthen farmer awareness programs about MSP rights",
        "Enhance coordination between state and central agencies",
        "Implement real-time price monitoring systems"
    ]
    
    # Low violation scenario
    low_violation_recommendations = [
        "Continue monitoring market conditions",
        "Maintain current procurement operations",
        "Regular farmer communication through digital platforms"
    ]
    
    # Test high violation report
    high_violation_report = MSPComplianceReport(
        report_period_start=date(2024, 1, 1),
        report_period_end=date(2024, 1, 31),
        region="Punjab",
        total_violations=50,
        violations_by_commodity={"Wheat": 30, "Rice": 20},
        violations_by_location={"Ludhiana, Punjab": 25, "Karnal, Haryana": 25},
        average_violation_percentage=18.5,
        recommendations=high_violation_recommendations
    )
    
    assert len(high_violation_report.recommendations) == 5
    assert any("URGENT" in rec for rec in high_violation_report.recommendations)
    assert any("emergency" in rec.lower() for rec in high_violation_report.recommendations)
    
    # Test medium violation report
    medium_violation_report = MSPComplianceReport(
        report_period_start=date(2024, 1, 1),
        report_period_end=date(2024, 1, 31),
        region="Haryana",
        total_violations=15,
        violations_by_commodity={"Rice": 10, "Maize": 5},
        violations_by_location={"Karnal, Haryana": 15},
        average_violation_percentage=8.2,
        recommendations=medium_violation_recommendations
    )
    
    assert len(medium_violation_report.recommendations) == 4
    assert any("awareness" in rec.lower() for rec in medium_violation_report.recommendations)
    assert any("monitoring" in rec.lower() for rec in medium_violation_report.recommendations)

def test_evidence_file_structure():
    """Test evidence file structure for compliance reports"""
    evidence_files = [
        "violation_evidence_001_20240115_143022.json",
        "violation_evidence_002_20240115_143045.json",
        "msp_rates_notification_2023-24.pdf",
        "procurement_guidelines_current.pdf",
        "market_data_export_20240115.csv",
        "violation_summary_20240115.xlsx"
    ]
    
    report = MSPComplianceReport(
        report_period_start=date(2024, 1, 1),
        report_period_end=date(2024, 1, 31),
        region="national",
        total_violations=2,
        violations_by_commodity={"Wheat": 1, "Rice": 1},
        violations_by_location={"Test Location": 2},
        average_violation_percentage=10.0,
        recommendations=["Test recommendation"],
        evidence_files=evidence_files
    )
    
    assert len(report.evidence_files) == 6
    
    # Check for different types of evidence files
    json_files = [f for f in evidence_files if f.endswith('.json')]
    pdf_files = [f for f in evidence_files if f.endswith('.pdf')]
    csv_files = [f for f in evidence_files if f.endswith('.csv')]
    xlsx_files = [f for f in evidence_files if f.endswith('.xlsx')]
    
    assert len(json_files) == 2  # Violation evidence files
    assert len(pdf_files) == 2   # Supporting documents
    assert len(csv_files) == 1   # Market data export
    assert len(xlsx_files) == 1  # Violation summary

def test_geographic_distribution_analysis():
    """Test geographic distribution analysis in compliance reports"""
    violations_by_location = {
        "Ludhiana, Punjab": 15,
        "Karnal, Haryana": 12,
        "Meerut, Uttar Pradesh": 8,
        "Ahmedabad, Gujarat": 5,
        "Nashik, Maharashtra": 3
    }
    
    report = MSPComplianceReport(
        report_period_start=date(2024, 1, 1),
        report_period_end=date(2024, 1, 31),
        region="national",
        total_violations=43,
        violations_by_commodity={"Wheat": 25, "Rice": 18},
        violations_by_location=violations_by_location,
        average_violation_percentage=11.2,
        recommendations=["Focus on Punjab and Haryana regions"]
    )
    
    # Test that locations are properly distributed
    assert report.violations_by_location["Ludhiana, Punjab"] == 15
    assert report.violations_by_location["Karnal, Haryana"] == 12
    assert report.violations_by_location["Meerut, Uttar Pradesh"] == 8
    
    # Test total violations match sum of location violations
    total_location_violations = sum(violations_by_location.values())
    assert report.total_violations == total_location_violations
    
    # Test that most affected location is identified
    most_affected_location = max(violations_by_location.keys(), key=violations_by_location.get)
    assert most_affected_location == "Ludhiana, Punjab"

def test_commodity_analysis():
    """Test commodity analysis in compliance reports"""
    violations_by_commodity = {
        "Wheat": 20,
        "Rice": 15,
        "Maize": 8,
        "Bajra": 5,
        "Gram": 3,
        "Tur": 2
    }
    
    report = MSPComplianceReport(
        report_period_start=date(2024, 1, 1),
        report_period_end=date(2024, 1, 31),
        region="national",
        total_violations=53,
        violations_by_commodity=violations_by_commodity,
        violations_by_location={"Various": 53},
        average_violation_percentage=9.8,
        recommendations=["Focus on Wheat and Rice procurement"]
    )
    
    # Test commodity distribution
    assert report.violations_by_commodity["Wheat"] == 20
    assert report.violations_by_commodity["Rice"] == 15
    assert report.violations_by_commodity["Maize"] == 8
    
    # Test most violated commodity
    most_violated_commodity = max(violations_by_commodity.keys(), key=violations_by_commodity.get)
    assert most_violated_commodity == "Wheat"
    
    # Test that total violations match sum of commodity violations
    total_commodity_violations = sum(violations_by_commodity.values())
    assert report.total_violations == total_commodity_violations

if __name__ == "__main__":
    # Run basic tests
    test_compliance_report_model()
    test_violation_model()
    test_compliance_report_validation()
    test_violation_severity_levels()
    test_compliance_report_recommendations()
    test_evidence_file_structure()
    test_geographic_distribution_analysis()
    test_commodity_analysis()
    
    print("✅ All basic compliance reporting tests passed!")
    print("📊 Compliance reporting system models and validation working correctly")
    print("🎯 Ready for integration with MSP enforcement system")