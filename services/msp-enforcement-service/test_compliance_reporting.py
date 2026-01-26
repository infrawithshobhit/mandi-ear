"""
Tests for MSP Compliance Reporting System
"""

import pytest
import asyncio
from datetime import date, datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import json

from compliance_reporting import (
    ComplianceReportGenerator, EvidenceCollector, RegulatoryNotifier,
    ReportConfig, ReportType, ReportFormat
)
from models import MSPViolation, ViolationType, AlertSeverity, MSPComplianceReport

@pytest.fixture
def sample_violations():
    """Create sample violations for testing"""
    violations = []
    
    # Critical violation
    violations.append(MSPViolation(
        id="violation_1",
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
        detected_at=datetime.utcnow() - timedelta(hours=2),
        severity=AlertSeverity.CRITICAL,
        evidence={
            "data_confidence": 0.9,
            "detection_method": "automated_monitoring"
        }
    ))
    
    # High severity violation
    violations.append(MSPViolation(
        id="violation_2",
        commodity="Rice",
        variety="Basmati",
        mandi_id="mandi_002",
        mandi_name="New Mandi Haryana",
        district="Karnal",
        state="Haryana",
        market_price=2800.0,
        msp_price=3200.0,
        price_difference=-400.0,
        violation_percentage=12.5,
        violation_type=ViolationType.BELOW_MSP,
        detected_at=datetime.utcnow() - timedelta(hours=1),
        severity=AlertSeverity.HIGH,
        evidence={
            "data_confidence": 0.85,
            "detection_method": "automated_monitoring"
        }
    ))
    
    # Medium severity violation
    violations.append(MSPViolation(
        id="violation_3",
        commodity="Maize",
        variety="Hybrid",
        mandi_id="mandi_003",
        mandi_name="District Mandi UP",
        district="Meerut",
        state="Uttar Pradesh",
        market_price=1650.0,
        msp_price=1870.0,
        price_difference=-220.0,
        violation_percentage=11.8,
        violation_type=ViolationType.BELOW_MSP,
        detected_at=datetime.utcnow() - timedelta(hours=3),
        severity=AlertSeverity.MEDIUM
    ))
    
    return violations

@pytest.fixture
def report_generator():
    """Create compliance report generator for testing"""
    return ComplianceReportGenerator()

@pytest.fixture
def evidence_collector():
    """Create evidence collector for testing"""
    return EvidenceCollector()

@pytest.fixture
def regulatory_notifier():
    """Create regulatory notifier for testing"""
    return RegulatoryNotifier()

class TestComplianceReportGenerator:
    """Test compliance report generation"""
    
    @pytest.mark.asyncio
    async def test_generate_compliance_report_basic(self, report_generator, sample_violations):
        """Test basic compliance report generation"""
        with patch.object(report_generator, '_get_violations_for_period', return_value=sample_violations):
            with patch.object(report_generator, '_store_compliance_report', return_value=True):
                with patch.object(report_generator.evidence_collector, 'collect_evidence_for_violations', return_value={}):
                    
                    start_date = date.today() - timedelta(days=7)
                    end_date = date.today()
                    
                    report = await report_generator.generate_compliance_report(
                        start_date=start_date,
                        end_date=end_date,
                        region="Punjab",
                        commodity="Wheat"
                    )
                    
                    assert isinstance(report, MSPComplianceReport)
                    assert report.report_period_start == start_date
                    assert report.report_period_end == end_date
                    assert report.region == "Punjab"
                    assert report.total_violations == 3
                    assert "Wheat" in report.violations_by_commodity
                    assert "Ludhiana, Punjab" in report.violations_by_location
                    assert report.average_violation_percentage > 0
                    assert len(report.recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_market_analysis_generation(self, report_generator, sample_violations):
        """Test market analysis generation"""
        analysis = await report_generator._generate_market_analysis(
            violations=sample_violations,
            start_date=date.today() - timedelta(days=7),
            end_date=date.today(),
            region="national",
            commodity=None
        )
        
        assert "violation_statistics" in analysis
        assert "geographic_distribution" in analysis
        assert "commodity_analysis" in analysis
        assert "severity_breakdown" in analysis
        assert "temporal_patterns" in analysis
        assert "market_trends" in analysis
        
        # Check violation statistics
        stats = analysis["violation_statistics"]
        assert stats["total_violations"] == 3
        assert stats["critical_violations"] == 1
        assert stats["average_violation_percentage"] > 0
        assert stats["total_farmer_losses"] > 0
        
        # Check geographic distribution
        geo_dist = analysis["geographic_distribution"]
        assert "Punjab" in geo_dist["by_state"]
        assert "Haryana" in geo_dist["by_state"]
        assert "Uttar Pradesh" in geo_dist["by_state"]
        
        # Check commodity analysis
        commodity_analysis = analysis["commodity_analysis"]
        assert "Wheat" in commodity_analysis["by_commodity"]
        assert "Rice" in commodity_analysis["by_commodity"]
        assert "Maize" in commodity_analysis["by_commodity"]
    
    @pytest.mark.asyncio
    async def test_farmer_impact_calculation(self, report_generator, sample_violations):
        """Test farmer impact calculation"""
        impact = await report_generator._calculate_farmer_impact(sample_violations)
        
        assert "financial_impact" in impact
        assert "severity_impact" in impact
        assert "geographic_impact" in impact
        assert "commodity_impact" in impact
        
        # Check financial impact
        financial = impact["financial_impact"]
        assert financial["total_estimated_losses"] > 0
        assert financial["average_loss_per_violation"] > 0
        assert financial["estimated_affected_farmers"] > 0
        
        # Check severity impact
        severity = impact["severity_impact"]
        assert severity["critical_impact_cases"] == 1
        assert severity["high_impact_cases"] == 1
        assert severity["critical_impact_losses"] > 0
    
    @pytest.mark.asyncio
    async def test_recommendations_generation(self, report_generator, sample_violations):
        """Test recommendations generation"""
        market_analysis = {
            "violation_statistics": {
                "average_violation_percentage": 20.0,
                "resolution_rate": 30.0
            },
            "geographic_distribution": {
                "most_affected_state": "Punjab"
            },
            "commodity_analysis": {
                "most_violated_commodity": "Wheat"
            }
        }
        
        farmer_impact = {
            "financial_impact": {
                "total_estimated_losses": 150000.0
            }
        }
        
        recommendations = await report_generator._generate_recommendations(
            violations=sample_violations,
            market_analysis=market_analysis,
            farmer_impact=farmer_impact
        )
        
        assert len(recommendations) > 0
        assert any("critical" in rec.lower() for rec in recommendations)
        assert any("Punjab" in rec for rec in recommendations)
        assert any("Wheat" in rec for rec in recommendations)
        assert any("compensation" in rec.lower() for rec in recommendations)

class TestEvidenceCollector:
    """Test evidence collection system"""
    
    @pytest.mark.asyncio
    async def test_collect_evidence_for_violations(self, evidence_collector, sample_violations):
        """Test evidence collection for violations"""
        with patch.object(evidence_collector, '_collect_violation_evidence') as mock_collect:
            mock_collect.return_value = {
                "violation_id": "test_id",
                "evidence_files": ["evidence_file_1.json"],
                "price_data": {"market_price": 1800.0},
                "verification_data": {"data_confidence": 0.9}
            }
            
            with patch.object(evidence_collector, '_collect_supporting_documents', return_value=["doc1.pdf"]):
                with patch.object(evidence_collector, '_document_data_sources', return_value=[]):
                    with patch.object(evidence_collector, '_verify_evidence_integrity', return_value={"integrity_status": "VERIFIED"}):
                        
                        evidence_data = await evidence_collector.collect_evidence_for_violations(sample_violations)
                        
                        assert "collection_timestamp" in evidence_data
                        assert evidence_data["total_violations"] == 3
                        assert "violation_evidence" in evidence_data
                        assert "supporting_documents" in evidence_data
                        assert "verification_status" in evidence_data
                        assert len(evidence_data["violation_evidence"]) == 3
    
    @pytest.mark.asyncio
    async def test_collect_violation_evidence(self, evidence_collector, sample_violations):
        """Test evidence collection for individual violation"""
        violation = sample_violations[0]
        
        with patch.object(evidence_collector, '_get_msp_reference_data', return_value={"msp_price": 2125.0}):
            with patch.object(evidence_collector, '_get_market_context_data', return_value={"mandi_name": "Test Mandi"}):
                with patch.object(evidence_collector, '_generate_violation_evidence_file', return_value="evidence_file.json"):
                    
                    evidence = await evidence_collector._collect_violation_evidence(violation)
                    
                    assert evidence["violation_id"] == violation.id
                    assert "price_data" in evidence
                    assert "msp_data" in evidence
                    assert "market_data" in evidence
                    assert "verification_data" in evidence
                    assert "evidence_files" in evidence
                    
                    # Check price data
                    price_data = evidence["price_data"]
                    assert price_data["market_price"] == violation.market_price
                    assert price_data["msp_price"] == violation.msp_price
                    assert price_data["violation_percentage"] == violation.violation_percentage
    
    @pytest.mark.asyncio
    async def test_verify_evidence_integrity(self, evidence_collector):
        """Test evidence integrity verification"""
        evidence_data = {
            "total_violations": 3,
            "violation_evidence": {
                "v1": {"violation_id": "v1"},
                "v2": {"violation_id": "v2"}
            },
            "supporting_documents": ["doc1.pdf"],
            "data_sources": [{"source_name": "test"}],
            "evidence_files": ["file1.json"]
        }
        
        verification = await evidence_collector._verify_evidence_integrity(evidence_data)
        
        assert "verification_timestamp" in verification
        assert "integrity_status" in verification
        assert "completeness_score" in verification
        assert verification["completeness_score"] < 1.0  # 2 out of 3 violations have evidence

class TestRegulatoryNotifier:
    """Test regulatory notification system"""
    
    @pytest.mark.asyncio
    async def test_submit_report_to_authorities(self, regulatory_notifier):
        """Test report submission to authorities"""
        report = MSPComplianceReport(
            report_period_start=date.today() - timedelta(days=7),
            report_period_end=date.today(),
            region="Punjab",
            total_violations=5,
            violations_by_commodity={"Wheat": 3, "Rice": 2},
            violations_by_location={"Ludhiana, Punjab": 2, "Karnal, Haryana": 3},
            average_violation_percentage=12.5,
            recommendations=["Increase monitoring", "Deploy teams"]
        )
        
        with patch.object(regulatory_notifier, '_submit_via_email', return_value=True):
            with patch.object(regulatory_notifier, '_submit_via_api', return_value=True):
                with patch.object(regulatory_notifier, '_submit_via_portal', return_value=True):
                    with patch.object(regulatory_notifier, '_update_report_status', return_value=True):
                        
                        success = await regulatory_notifier.submit_report_to_authorities(
                            report, ["test@example.com"]
                        )
                        
                        assert success is True
                        assert report.report_status == "submitted"
    
    @pytest.mark.asyncio
    async def test_notify_critical_violations(self, regulatory_notifier, sample_violations):
        """Test critical violation notifications"""
        critical_violations = [v for v in sample_violations if v.severity == AlertSeverity.CRITICAL]
        
        with patch.object(regulatory_notifier, '_send_urgent_email', return_value=True):
            with patch.object(regulatory_notifier, '_send_urgent_sms', return_value=True):
                with patch.object(regulatory_notifier, '_send_urgent_api_alert', return_value=True):
                    
                    success = await regulatory_notifier.notify_critical_violations(critical_violations)
                    
                    assert success is True
    
    def test_generate_email_content(self, regulatory_notifier):
        """Test email content generation"""
        report = MSPComplianceReport(
            report_period_start=date.today() - timedelta(days=7),
            report_period_end=date.today(),
            region="Punjab",
            total_violations=5,
            violations_by_commodity={"Wheat": 3, "Rice": 2},
            violations_by_location={"Ludhiana, Punjab": 2, "Karnal, Haryana": 3},
            average_violation_percentage=12.5,
            estimated_farmer_losses=50000.0,
            most_affected_farmers=100,
            recommendations=["Increase monitoring", "Deploy teams"]
        )
        
        content = regulatory_notifier._generate_email_content(report)
        
        assert "MSP Compliance Report" in content
        assert "Total Violations: 5" in content
        assert "Punjab" in content
        assert "Wheat: 3" in content
        assert "Increase monitoring" in content
        assert report.id in content
    
    def test_generate_api_payload(self, regulatory_notifier):
        """Test API payload generation"""
        report = MSPComplianceReport(
            report_period_start=date.today() - timedelta(days=7),
            report_period_end=date.today(),
            region="Punjab",
            total_violations=5,
            violations_by_commodity={"Wheat": 3},
            violations_by_location={"Ludhiana, Punjab": 2},
            average_violation_percentage=12.5,
            recommendations=["Test recommendation"]
        )
        
        payload = regulatory_notifier._generate_api_payload(report)
        
        assert payload["report_id"] == report.id
        assert payload["report_type"] == "msp_compliance"
        assert payload["region"] == "Punjab"
        assert payload["summary"]["total_violations"] == 5
        assert "Wheat" in payload["violations_by_commodity"]
        assert len(payload["recommendations"]) > 0

class TestIntegration:
    """Integration tests for compliance reporting system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_compliance_reporting(self, report_generator, sample_violations):
        """Test end-to-end compliance reporting workflow"""
        with patch.object(report_generator, '_get_violations_for_period', return_value=sample_violations):
            with patch.object(report_generator, '_store_compliance_report', return_value=True):
                with patch.object(report_generator.evidence_collector, 'collect_evidence_for_violations') as mock_evidence:
                    mock_evidence.return_value = {
                        "collection_timestamp": datetime.utcnow().isoformat(),
                        "total_violations": 3,
                        "evidence_files": ["evidence1.json", "evidence2.json"],
                        "violation_evidence": {
                            "violation_1": {"price_data": {"market_price": 1800.0}},
                            "violation_2": {"price_data": {"market_price": 2800.0}},
                            "violation_3": {"price_data": {"market_price": 1650.0}}
                        },
                        "verification_status": {"integrity_status": "VERIFIED"}
                    }
                    
                    with patch.object(report_generator.regulatory_notifier, 'submit_report_to_authorities', return_value=True):
                        
                        config = ReportConfig(
                            report_type=ReportType.CUSTOM,
                            format=ReportFormat.JSON,
                            auto_submit=True,
                            notification_emails=["authority@gov.in"]
                        )
                        
                        report = await report_generator.generate_compliance_report(
                            start_date=date.today() - timedelta(days=7),
                            end_date=date.today(),
                            region="Punjab",
                            commodity="Wheat",
                            config=config
                        )
                        
                        # Verify report structure
                        assert isinstance(report, MSPComplianceReport)
                        assert report.total_violations == 3
                        assert report.region == "Punjab"
                        assert len(report.recommendations) > 0
                        assert hasattr(report, 'market_analysis')
                        assert hasattr(report, 'farmer_impact')
                        assert hasattr(report, 'evidence_summary')
                        
                        # Verify evidence was collected
                        assert report.evidence_summary["total_violations"] == 3
                        assert len(report.evidence_summary["evidence_files"]) == 2
                        
                        # Verify market analysis
                        market_analysis = report.market_analysis
                        assert market_analysis["violation_statistics"]["total_violations"] == 3
                        assert "Punjab" in market_analysis["geographic_distribution"]["by_state"]
                        assert "Wheat" in market_analysis["commodity_analysis"]["by_commodity"]
                        
                        # Verify farmer impact
                        farmer_impact = report.farmer_impact
                        assert farmer_impact["financial_impact"]["total_estimated_losses"] > 0
                        assert farmer_impact["severity_impact"]["critical_impact_cases"] == 1

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])