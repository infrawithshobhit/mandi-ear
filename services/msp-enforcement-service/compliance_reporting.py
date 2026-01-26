"""
MSP Compliance Reporting System
Generates comprehensive compliance reports for regulatory authorities
"""

import asyncio
import structlog
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
import json
import uuid
from dataclasses import dataclass
from enum import Enum

from models import (
    MSPViolation, MSPComplianceReport, ViolationType, AlertSeverity,
    MSPRate, ProcurementCenter
)
from database import _pool

logger = structlog.get_logger()

class ReportType(str, Enum):
    """Types of compliance reports"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    INCIDENT = "incident"
    CUSTOM = "custom"

class ReportFormat(str, Enum):
    """Report output formats"""
    JSON = "json"
    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"

@dataclass
class ReportConfig:
    """Configuration for compliance reports"""
    report_type: ReportType
    format: ReportFormat
    include_evidence: bool = True
    include_recommendations: bool = True
    include_farmer_impact: bool = True
    include_market_analysis: bool = True
    auto_submit: bool = False
    notification_emails: List[str] = None

class ComplianceReportGenerator:
    """Generates comprehensive MSP compliance reports"""
    
    def __init__(self):
        self.evidence_collector = EvidenceCollector()
        self.regulatory_notifier = RegulatoryNotifier()
    
    async def generate_compliance_report(
        self,
        start_date: date,
        end_date: date,
        region: str = "national",
        commodity: Optional[str] = None,
        config: Optional[ReportConfig] = None
    ) -> MSPComplianceReport:
        """Generate comprehensive MSP compliance report"""
        try:
            config = config or ReportConfig(
                report_type=ReportType.CUSTOM,
                format=ReportFormat.JSON
            )
            
            logger.info(
                "Generating MSP compliance report",
                start_date=start_date,
                end_date=end_date,
                region=region,
                commodity=commodity
            )
            
            # Collect violations data
            violations = await self._get_violations_for_period(
                start_date, end_date, region, commodity
            )
            
            # Collect evidence for violations
            evidence_data = {}
            if config.include_evidence:
                evidence_data = await self.evidence_collector.collect_evidence_for_violations(
                    violations
                )
            
            # Generate market analysis
            market_analysis = {}
            if config.include_market_analysis:
                market_analysis = await self._generate_market_analysis(
                    violations, start_date, end_date, region, commodity
                )
            
            # Calculate farmer impact
            farmer_impact = {}
            if config.include_farmer_impact:
                farmer_impact = await self._calculate_farmer_impact(violations)
            
            # Generate recommendations
            recommendations = []
            if config.include_recommendations:
                recommendations = await self._generate_recommendations(
                    violations, market_analysis, farmer_impact
                )
            
            # Create comprehensive report
            report = await self._create_compliance_report(
                start_date, end_date, region, commodity,
                violations, evidence_data, market_analysis,
                farmer_impact, recommendations
            )
            
            # Store report in database
            await self._store_compliance_report(report)
            
            # Auto-submit to authorities if configured
            if config.auto_submit:
                await self.regulatory_notifier.submit_report_to_authorities(
                    report, config.notification_emails or []
                )
            
            logger.info(
                "MSP compliance report generated successfully",
                report_id=report.id,
                violations_count=len(violations),
                period=f"{start_date} to {end_date}"
            )
            
            return report
            
        except Exception as e:
            logger.error("Error generating compliance report", error=str(e))
            raise
    
    async def _get_violations_for_period(
        self,
        start_date: date,
        end_date: date,
        region: str,
        commodity: Optional[str]
    ) -> List[MSPViolation]:
        """Get violations for the specified period and filters"""
        if not _pool:
            return []
        
        try:
            query = """
                SELECT * FROM msp_violations 
                WHERE detected_at::date BETWEEN $1 AND $2
            """
            params = [start_date, end_date]
            
            # Add region filter
            if region != "national":
                if "," in region:  # State, District format
                    state, district = region.split(",", 1)
                    query += " AND LOWER(state) = LOWER($3) AND LOWER(district) = LOWER($4)"
                    params.extend([state.strip(), district.strip()])
                else:  # State only
                    query += " AND LOWER(state) = LOWER($3)"
                    params.append(region)
            
            # Add commodity filter
            if commodity:
                param_num = len(params) + 1
                query += f" AND LOWER(commodity) = LOWER(${param_num})"
                params.append(commodity)
            
            query += " ORDER BY detected_at DESC"
            
            async with _pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                
                violations = []
                for row in rows:
                    violation = MSPViolation(
                        id=row['id'],
                        commodity=row['commodity'],
                        variety=row['variety'],
                        mandi_id=row['mandi_id'],
                        mandi_name=row['mandi_name'],
                        district=row['district'],
                        state=row['state'],
                        market_price=float(row['market_price']),
                        msp_price=float(row['msp_price']),
                        price_difference=float(row['price_difference']),
                        violation_percentage=float(row['violation_percentage']),
                        violation_type=ViolationType(row['violation_type']),
                        detected_at=row['detected_at'],
                        severity=AlertSeverity(row['severity']),
                        is_resolved=row['is_resolved'],
                        resolution_notes=row['resolution_notes'],
                        resolved_at=row['resolved_at'],
                        evidence=json.loads(row['evidence']) if row['evidence'] else None
                    )
                    violations.append(violation)
                
                return violations
                
        except Exception as e:
            logger.error("Error getting violations for period", error=str(e))
            return []
    
    async def _generate_market_analysis(
        self,
        violations: List[MSPViolation],
        start_date: date,
        end_date: date,
        region: str,
        commodity: Optional[str]
    ) -> Dict[str, Any]:
        """Generate comprehensive market analysis"""
        try:
            analysis = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "duration_days": (end_date - start_date).days
                },
                "violation_statistics": {},
                "geographic_distribution": {},
                "commodity_analysis": {},
                "severity_breakdown": {},
                "temporal_patterns": {},
                "market_trends": {}
            }
            
            if not violations:
                return analysis
            
            # Violation statistics
            total_violations = len(violations)
            resolved_violations = len([v for v in violations if v.is_resolved])
            critical_violations = len([v for v in violations if v.severity == AlertSeverity.CRITICAL])
            
            analysis["violation_statistics"] = {
                "total_violations": total_violations,
                "resolved_violations": resolved_violations,
                "unresolved_violations": total_violations - resolved_violations,
                "critical_violations": critical_violations,
                "resolution_rate": (resolved_violations / total_violations * 100) if total_violations > 0 else 0,
                "average_violation_percentage": sum(v.violation_percentage for v in violations) / total_violations,
                "max_violation_percentage": max(v.violation_percentage for v in violations),
                "total_farmer_losses": sum(abs(v.price_difference) for v in violations)
            }
            
            # Geographic distribution
            state_violations = {}
            district_violations = {}
            for violation in violations:
                state_violations[violation.state] = state_violations.get(violation.state, 0) + 1
                district_key = f"{violation.district}, {violation.state}"
                district_violations[district_key] = district_violations.get(district_key, 0) + 1
            
            analysis["geographic_distribution"] = {
                "by_state": dict(sorted(state_violations.items(), key=lambda x: x[1], reverse=True)),
                "by_district": dict(sorted(district_violations.items(), key=lambda x: x[1], reverse=True)[:20]),
                "most_affected_state": max(state_violations.keys(), key=state_violations.get) if state_violations else None,
                "most_affected_district": max(district_violations.keys(), key=district_violations.get) if district_violations else None
            }
            
            # Commodity analysis
            commodity_violations = {}
            commodity_losses = {}
            for violation in violations:
                commodity_violations[violation.commodity] = commodity_violations.get(violation.commodity, 0) + 1
                commodity_losses[violation.commodity] = commodity_losses.get(violation.commodity, 0) + abs(violation.price_difference)
            
            analysis["commodity_analysis"] = {
                "by_commodity": dict(sorted(commodity_violations.items(), key=lambda x: x[1], reverse=True)),
                "losses_by_commodity": dict(sorted(commodity_losses.items(), key=lambda x: x[1], reverse=True)),
                "most_violated_commodity": max(commodity_violations.keys(), key=commodity_violations.get) if commodity_violations else None,
                "highest_loss_commodity": max(commodity_losses.keys(), key=commodity_losses.get) if commodity_losses else None
            }
            
            # Severity breakdown
            severity_count = {}
            for violation in violations:
                severity_count[violation.severity.value] = severity_count.get(violation.severity.value, 0) + 1
            
            analysis["severity_breakdown"] = severity_count
            
            # Temporal patterns
            daily_violations = {}
            for violation in violations:
                day = violation.detected_at.date().isoformat()
                daily_violations[day] = daily_violations.get(day, 0) + 1
            
            analysis["temporal_patterns"] = {
                "daily_violations": daily_violations,
                "peak_violation_day": max(daily_violations.keys(), key=daily_violations.get) if daily_violations else None,
                "average_daily_violations": sum(daily_violations.values()) / len(daily_violations) if daily_violations else 0
            }
            
            # Market trends (would integrate with price discovery service)
            analysis["market_trends"] = {
                "price_volatility": "High" if analysis["violation_statistics"]["average_violation_percentage"] > 15 else "Medium" if analysis["violation_statistics"]["average_violation_percentage"] > 5 else "Low",
                "market_stability": "Unstable" if critical_violations > total_violations * 0.3 else "Stable",
                "intervention_needed": critical_violations > 0 or total_violations > 50
            }
            
            return analysis
            
        except Exception as e:
            logger.error("Error generating market analysis", error=str(e))
            return {}
    
    async def _calculate_farmer_impact(self, violations: List[MSPViolation]) -> Dict[str, Any]:
        """Calculate impact on farmers"""
        try:
            if not violations:
                return {}
            
            # Calculate financial impact
            total_loss = sum(abs(v.price_difference) for v in violations)
            average_loss_per_violation = total_loss / len(violations)
            
            # Estimate affected farmers (assuming average 10 quintals per farmer)
            estimated_affected_farmers = len(violations) * 10  # Rough estimate
            average_loss_per_farmer = total_loss / estimated_affected_farmers if estimated_affected_farmers > 0 else 0
            
            # Categorize impact by severity
            critical_impact_violations = [v for v in violations if v.severity == AlertSeverity.CRITICAL]
            high_impact_violations = [v for v in violations if v.severity == AlertSeverity.HIGH]
            
            impact = {
                "financial_impact": {
                    "total_estimated_losses": round(total_loss, 2),
                    "average_loss_per_violation": round(average_loss_per_violation, 2),
                    "estimated_affected_farmers": estimated_affected_farmers,
                    "average_loss_per_farmer": round(average_loss_per_farmer, 2)
                },
                "severity_impact": {
                    "critical_impact_cases": len(critical_impact_violations),
                    "high_impact_cases": len(high_impact_violations),
                    "critical_impact_losses": sum(abs(v.price_difference) for v in critical_impact_violations),
                    "high_impact_losses": sum(abs(v.price_difference) for v in high_impact_violations)
                },
                "geographic_impact": {},
                "commodity_impact": {}
            }
            
            # Geographic impact
            state_impact = {}
            for violation in violations:
                if violation.state not in state_impact:
                    state_impact[violation.state] = {"violations": 0, "losses": 0}
                state_impact[violation.state]["violations"] += 1
                state_impact[violation.state]["losses"] += abs(violation.price_difference)
            
            impact["geographic_impact"] = dict(sorted(
                state_impact.items(), 
                key=lambda x: x[1]["losses"], 
                reverse=True
            ))
            
            # Commodity impact
            commodity_impact = {}
            for violation in violations:
                if violation.commodity not in commodity_impact:
                    commodity_impact[violation.commodity] = {"violations": 0, "losses": 0}
                commodity_impact[violation.commodity]["violations"] += 1
                commodity_impact[violation.commodity]["losses"] += abs(violation.price_difference)
            
            impact["commodity_impact"] = dict(sorted(
                commodity_impact.items(), 
                key=lambda x: x[1]["losses"], 
                reverse=True
            ))
            
            return impact
            
        except Exception as e:
            logger.error("Error calculating farmer impact", error=str(e))
            return {}
    
    async def _generate_recommendations(
        self,
        violations: List[MSPViolation],
        market_analysis: Dict[str, Any],
        farmer_impact: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        try:
            recommendations = []
            
            if not violations:
                recommendations.append("No MSP violations detected during this period. Continue monitoring.")
                return recommendations
            
            # Critical violations recommendations
            critical_violations = len([v for v in violations if v.severity == AlertSeverity.CRITICAL])
            if critical_violations > 0:
                recommendations.extend([
                    f"URGENT: {critical_violations} critical MSP violations require immediate intervention",
                    "Deploy emergency procurement teams to affected areas",
                    "Activate additional government procurement centers",
                    "Issue public notices about MSP guarantee to farmers"
                ])
            
            # High violation rate recommendations
            violation_stats = market_analysis.get("violation_statistics", {})
            if violation_stats.get("average_violation_percentage", 0) > 15:
                recommendations.extend([
                    "Market prices significantly below MSP - consider market intervention",
                    "Increase procurement center capacity in affected regions",
                    "Investigate potential market manipulation or hoarding"
                ])
            
            # Geographic recommendations
            geo_dist = market_analysis.get("geographic_distribution", {})
            most_affected_state = geo_dist.get("most_affected_state")
            if most_affected_state:
                recommendations.append(
                    f"Focus enforcement efforts on {most_affected_state} - highest violation count"
                )
            
            # Commodity-specific recommendations
            commodity_analysis = market_analysis.get("commodity_analysis", {})
            most_violated_commodity = commodity_analysis.get("most_violated_commodity")
            if most_violated_commodity:
                recommendations.extend([
                    f"Increase {most_violated_commodity} procurement operations",
                    f"Review {most_violated_commodity} MSP rates for adequacy",
                    f"Strengthen {most_violated_commodity} supply chain monitoring"
                ])
            
            # Resolution rate recommendations
            if violation_stats.get("resolution_rate", 0) < 50:
                recommendations.extend([
                    "Improve violation resolution processes - current resolution rate below 50%",
                    "Establish dedicated violation response teams",
                    "Implement faster farmer notification systems"
                ])
            
            # Farmer impact recommendations
            financial_impact = farmer_impact.get("financial_impact", {})
            if financial_impact.get("total_estimated_losses", 0) > 100000:  # ₹1 lakh
                recommendations.extend([
                    "Consider farmer compensation schemes for significant losses",
                    "Implement preventive measures to reduce future violations",
                    "Strengthen farmer awareness programs about MSP rights"
                ])
            
            # Systemic recommendations
            if len(violations) > 100:  # High volume of violations
                recommendations.extend([
                    "Review and strengthen MSP enforcement mechanisms",
                    "Increase frequency of market monitoring",
                    "Enhance coordination between state and central agencies",
                    "Consider policy interventions to improve market efficiency"
                ])
            
            # Technology recommendations
            recommendations.extend([
                "Implement real-time price monitoring systems",
                "Deploy mobile procurement units in remote areas",
                "Enhance farmer communication through digital platforms",
                "Establish automated violation detection systems"
            ])
            
            return recommendations
            
        except Exception as e:
            logger.error("Error generating recommendations", error=str(e))
            return ["Error generating recommendations - manual review required"]
    
    async def _create_compliance_report(
        self,
        start_date: date,
        end_date: date,
        region: str,
        commodity: Optional[str],
        violations: List[MSPViolation],
        evidence_data: Dict[str, Any],
        market_analysis: Dict[str, Any],
        farmer_impact: Dict[str, Any],
        recommendations: List[str]
    ) -> MSPComplianceReport:
        """Create comprehensive compliance report"""
        try:
            # Aggregate violations by commodity and location
            violations_by_commodity = {}
            violations_by_location = {}
            
            for violation in violations:
                # By commodity
                violations_by_commodity[violation.commodity] = violations_by_commodity.get(violation.commodity, 0) + 1
                
                # By location
                location_key = f"{violation.district}, {violation.state}"
                violations_by_location[location_key] = violations_by_location.get(location_key, 0) + 1
            
            # Calculate average violation percentage
            avg_violation_percentage = 0
            if violations:
                avg_violation_percentage = sum(v.violation_percentage for v in violations) / len(violations)
            
            # Estimate affected farmers
            estimated_affected_farmers = len(violations) * 10  # Rough estimate
            
            # Calculate estimated losses
            estimated_losses = sum(abs(v.price_difference) for v in violations)
            
            # Prepare evidence files list
            evidence_files = []
            if evidence_data:
                evidence_files = evidence_data.get("evidence_files", [])
            
            report = MSPComplianceReport(
                report_period_start=start_date,
                report_period_end=end_date,
                region=region,
                total_violations=len(violations),
                violations_by_commodity=violations_by_commodity,
                violations_by_location=violations_by_location,
                average_violation_percentage=round(avg_violation_percentage, 2),
                most_affected_farmers=estimated_affected_farmers,
                estimated_farmer_losses=round(estimated_losses, 2),
                recommendations=recommendations,
                evidence_files=evidence_files
            )
            
            # Add additional metadata
            report.market_analysis = market_analysis
            report.farmer_impact = farmer_impact
            report.evidence_summary = evidence_data
            report.violation_details = [
                {
                    "id": v.id,
                    "commodity": v.commodity,
                    "location": f"{v.district}, {v.state}",
                    "violation_percentage": v.violation_percentage,
                    "severity": v.severity.value,
                    "detected_at": v.detected_at.isoformat(),
                    "is_resolved": v.is_resolved
                }
                for v in violations
            ]
            
            return report
            
        except Exception as e:
            logger.error("Error creating compliance report", error=str(e))
            raise
    
    async def _store_compliance_report(self, report: MSPComplianceReport) -> bool:
        """Store compliance report in database"""
        try:
            from database import store_compliance_report
            return await store_compliance_report(report)
        except Exception as e:
            logger.error("Error storing compliance report", error=str(e))
            return False

class EvidenceCollector:
    """Collects and organizes evidence for MSP violations"""
    
    async def collect_evidence_for_violations(
        self, 
        violations: List[MSPViolation]
    ) -> Dict[str, Any]:
        """Collect comprehensive evidence for violations"""
        try:
            evidence_data = {
                "collection_timestamp": datetime.utcnow().isoformat(),
                "total_violations": len(violations),
                "evidence_files": [],
                "violation_evidence": {},
                "supporting_documents": [],
                "data_sources": [],
                "verification_status": {}
            }
            
            for violation in violations:
                violation_evidence = await self._collect_violation_evidence(violation)
                evidence_data["violation_evidence"][violation.id] = violation_evidence
                
                # Add evidence files
                if violation_evidence.get("evidence_files"):
                    evidence_data["evidence_files"].extend(violation_evidence["evidence_files"])
            
            # Collect supporting documents
            evidence_data["supporting_documents"] = await self._collect_supporting_documents(violations)
            
            # Document data sources
            evidence_data["data_sources"] = await self._document_data_sources()
            
            # Verify evidence integrity
            evidence_data["verification_status"] = await self._verify_evidence_integrity(evidence_data)
            
            logger.info(
                "Evidence collection completed",
                violations_count=len(violations),
                evidence_files_count=len(evidence_data["evidence_files"])
            )
            
            return evidence_data
            
        except Exception as e:
            logger.error("Error collecting evidence", error=str(e))
            return {}
    
    async def _collect_violation_evidence(self, violation: MSPViolation) -> Dict[str, Any]:
        """Collect evidence for a specific violation"""
        try:
            evidence = {
                "violation_id": violation.id,
                "detection_timestamp": violation.detected_at.isoformat(),
                "evidence_files": [],
                "price_data": {},
                "msp_data": {},
                "market_data": {},
                "verification_data": {}
            }
            
            # Price evidence
            evidence["price_data"] = {
                "market_price": violation.market_price,
                "msp_price": violation.msp_price,
                "price_difference": violation.price_difference,
                "violation_percentage": violation.violation_percentage,
                "price_source": violation.evidence.get("comparison_data", {}).get("data_confidence", 0.8) if violation.evidence else 0.8
            }
            
            # MSP reference data
            evidence["msp_data"] = await self._get_msp_reference_data(violation.commodity, violation.detected_at.date())
            
            # Market context data
            evidence["market_data"] = await self._get_market_context_data(violation)
            
            # Generate evidence files
            evidence_file = await self._generate_violation_evidence_file(violation, evidence)
            if evidence_file:
                evidence["evidence_files"].append(evidence_file)
            
            # Verification data
            evidence["verification_data"] = {
                "data_confidence": violation.evidence.get("data_confidence", 0.8) if violation.evidence else 0.8,
                "detection_method": violation.evidence.get("detection_method", "automated_monitoring") if violation.evidence else "automated_monitoring",
                "verified_by": "MSP Enforcement System",
                "verification_timestamp": datetime.utcnow().isoformat()
            }
            
            return evidence
            
        except Exception as e:
            logger.error("Error collecting violation evidence", violation_id=violation.id, error=str(e))
            return {}
    
    async def _get_msp_reference_data(self, commodity: str, detection_date: date) -> Dict[str, Any]:
        """Get MSP reference data for evidence"""
        try:
            if not _pool:
                return {}
            
            async with _pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM msp_rates 
                    WHERE LOWER(commodity) = LOWER($1) 
                    AND effective_date <= $2 
                    AND (expiry_date IS NULL OR expiry_date >= $2)
                    AND is_active = TRUE
                    ORDER BY effective_date DESC
                    LIMIT 1
                """, commodity, detection_date)
                
                if row:
                    return {
                        "msp_rate_id": row['id'],
                        "commodity": row['commodity'],
                        "variety": row['variety'],
                        "season": row['season'],
                        "crop_year": row['crop_year'],
                        "msp_price": float(row['msp_price']),
                        "effective_date": row['effective_date'].isoformat(),
                        "announcement_date": row['announcement_date'].isoformat(),
                        "source_document": row['source_document']
                    }
                
                return {}
                
        except Exception as e:
            logger.error("Error getting MSP reference data", error=str(e))
            return {}
    
    async def _get_market_context_data(self, violation: MSPViolation) -> Dict[str, Any]:
        """Get market context data for evidence"""
        try:
            # This would integrate with price discovery service
            # For now, provide basic context
            return {
                "mandi_id": violation.mandi_id,
                "mandi_name": violation.mandi_name,
                "location": f"{violation.district}, {violation.state}",
                "detection_date": violation.detected_at.date().isoformat(),
                "market_conditions": "Normal trading conditions",
                "nearby_markets": [],  # Would be populated from price discovery service
                "historical_prices": []  # Would be populated from price discovery service
            }
            
        except Exception as e:
            logger.error("Error getting market context data", error=str(e))
            return {}
    
    async def _generate_violation_evidence_file(
        self, 
        violation: MSPViolation, 
        evidence: Dict[str, Any]
    ) -> Optional[str]:
        """Generate evidence file for violation"""
        try:
            # Generate evidence document
            evidence_doc = {
                "document_type": "MSP_VIOLATION_EVIDENCE",
                "violation_id": violation.id,
                "generated_at": datetime.utcnow().isoformat(),
                "violation_details": {
                    "commodity": violation.commodity,
                    "variety": violation.variety,
                    "mandi": violation.mandi_name,
                    "location": f"{violation.district}, {violation.state}",
                    "detected_at": violation.detected_at.isoformat(),
                    "severity": violation.severity.value
                },
                "price_evidence": evidence["price_data"],
                "msp_reference": evidence["msp_data"],
                "market_context": evidence["market_data"],
                "verification": evidence["verification_data"]
            }
            
            # In production, this would save to file system or cloud storage
            filename = f"violation_evidence_{violation.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Simulate file creation
            logger.info("Generated evidence file", filename=filename, violation_id=violation.id)
            
            return filename
            
        except Exception as e:
            logger.error("Error generating evidence file", violation_id=violation.id, error=str(e))
            return None
    
    async def _collect_supporting_documents(self, violations: List[MSPViolation]) -> List[str]:
        """Collect supporting documents for violations"""
        try:
            documents = []
            
            # MSP notification documents
            documents.append("msp_rates_notification_2023-24.pdf")
            documents.append("procurement_guidelines_current.pdf")
            
            # Market data exports
            documents.append(f"market_data_export_{datetime.utcnow().strftime('%Y%m%d')}.csv")
            
            # Violation summary
            documents.append(f"violation_summary_{datetime.utcnow().strftime('%Y%m%d')}.xlsx")
            
            return documents
            
        except Exception as e:
            logger.error("Error collecting supporting documents", error=str(e))
            return []
    
    async def _document_data_sources(self) -> List[Dict[str, Any]]:
        """Document data sources used for evidence"""
        try:
            sources = [
                {
                    "source_name": "MSP Enforcement Monitoring System",
                    "source_type": "Internal System",
                    "reliability": 0.95,
                    "last_updated": datetime.utcnow().isoformat()
                },
                {
                    "source_name": "Government MSP Database",
                    "source_type": "Official Government Data",
                    "reliability": 1.0,
                    "last_updated": datetime.utcnow().isoformat()
                },
                {
                    "source_name": "Price Discovery Service",
                    "source_type": "Market Data Aggregator",
                    "reliability": 0.85,
                    "last_updated": datetime.utcnow().isoformat()
                }
            ]
            
            return sources
            
        except Exception as e:
            logger.error("Error documenting data sources", error=str(e))
            return []
    
    async def _verify_evidence_integrity(self, evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify evidence integrity and completeness"""
        try:
            verification = {
                "verification_timestamp": datetime.utcnow().isoformat(),
                "integrity_status": "VERIFIED",
                "completeness_score": 0.0,
                "issues": [],
                "recommendations": []
            }
            
            # Check completeness
            required_fields = ["violation_evidence", "supporting_documents", "data_sources"]
            missing_fields = [field for field in required_fields if not evidence_data.get(field)]
            
            if missing_fields:
                verification["issues"].append(f"Missing required fields: {', '.join(missing_fields)}")
                verification["integrity_status"] = "INCOMPLETE"
            
            # Calculate completeness score
            total_violations = evidence_data.get("total_violations", 0)
            violations_with_evidence = len(evidence_data.get("violation_evidence", {}))
            
            if total_violations > 0:
                verification["completeness_score"] = violations_with_evidence / total_violations
            
            # Add recommendations
            if verification["completeness_score"] < 1.0:
                verification["recommendations"].append("Collect missing violation evidence")
            
            if len(evidence_data.get("evidence_files", [])) == 0:
                verification["recommendations"].append("Generate evidence files for violations")
            
            return verification
            
        except Exception as e:
            logger.error("Error verifying evidence integrity", error=str(e))
            return {"integrity_status": "ERROR", "error": str(e)}

class RegulatoryNotifier:
    """Handles notifications to regulatory authorities"""
    
    def __init__(self):
        self.notification_channels = {
            "email": True,
            "api": True,
            "portal": True,
            "sms": False  # For urgent notifications only
        }
    
    async def submit_report_to_authorities(
        self, 
        report: MSPComplianceReport, 
        notification_emails: List[str]
    ) -> bool:
        """Submit compliance report to regulatory authorities"""
        try:
            logger.info(
                "Submitting compliance report to authorities",
                report_id=report.id,
                notification_emails=len(notification_emails)
            )
            
            # Submit via multiple channels
            submission_results = {}
            
            # Email submission
            if self.notification_channels["email"]:
                submission_results["email"] = await self._submit_via_email(report, notification_emails)
            
            # API submission
            if self.notification_channels["api"]:
                submission_results["api"] = await self._submit_via_api(report)
            
            # Portal submission
            if self.notification_channels["portal"]:
                submission_results["portal"] = await self._submit_via_portal(report)
            
            # Check if any submission was successful
            success = any(submission_results.values())
            
            if success:
                # Update report status
                report.report_status = "submitted"
                await self._update_report_status(report)
                
                logger.info(
                    "Compliance report submitted successfully",
                    report_id=report.id,
                    submission_results=submission_results
                )
            else:
                logger.error(
                    "Failed to submit compliance report",
                    report_id=report.id,
                    submission_results=submission_results
                )
            
            return success
            
        except Exception as e:
            logger.error("Error submitting report to authorities", report_id=report.id, error=str(e))
            return False
    
    async def _submit_via_email(self, report: MSPComplianceReport, emails: List[str]) -> bool:
        """Submit report via email"""
        try:
            # In production, this would integrate with email service
            email_content = self._generate_email_content(report)
            
            # Simulate email sending
            for email in emails:
                logger.info("Sending compliance report email", recipient=email, report_id=report.id)
            
            return True
            
        except Exception as e:
            logger.error("Error submitting via email", error=str(e))
            return False
    
    async def _submit_via_api(self, report: MSPComplianceReport) -> bool:
        """Submit report via government API"""
        try:
            # In production, this would call government APIs
            api_payload = self._generate_api_payload(report)
            
            # Simulate API submission
            logger.info("Submitting compliance report via API", report_id=report.id)
            
            return True
            
        except Exception as e:
            logger.error("Error submitting via API", error=str(e))
            return False
    
    async def _submit_via_portal(self, report: MSPComplianceReport) -> bool:
        """Submit report via government portal"""
        try:
            # In production, this would integrate with government portals
            portal_data = self._generate_portal_data(report)
            
            # Simulate portal submission
            logger.info("Submitting compliance report via portal", report_id=report.id)
            
            return True
            
        except Exception as e:
            logger.error("Error submitting via portal", error=str(e))
            return False
    
    def _generate_email_content(self, report: MSPComplianceReport) -> str:
        """Generate email content for compliance report"""
        content = f"""
Subject: MSP Compliance Report - {report.report_period_start} to {report.report_period_end}

Dear Regulatory Authority,

Please find attached the MSP Compliance Report for the period {report.report_period_start} to {report.report_period_end}.

EXECUTIVE SUMMARY:
- Total Violations: {report.total_violations}
- Region: {report.region}
- Average Violation Percentage: {report.average_violation_percentage}%
- Estimated Farmer Losses: ₹{report.estimated_farmer_losses:,.2f}
- Affected Farmers: {report.most_affected_farmers}

KEY FINDINGS:
"""
        
        # Add top violations by commodity
        if report.violations_by_commodity:
            content += "\nTop Violated Commodities:\n"
            for commodity, count in list(report.violations_by_commodity.items())[:5]:
                content += f"- {commodity}: {count} violations\n"
        
        # Add top affected locations
        if report.violations_by_location:
            content += "\nMost Affected Locations:\n"
            for location, count in list(report.violations_by_location.items())[:5]:
                content += f"- {location}: {count} violations\n"
        
        # Add recommendations
        if report.recommendations:
            content += "\nKEY RECOMMENDATIONS:\n"
            for i, rec in enumerate(report.recommendations[:5], 1):
                content += f"{i}. {rec}\n"
        
        content += f"""
Report ID: {report.id}
Generated: {report.generated_at}
Generated By: {report.generated_by}

This is an automated report from the MANDI EAR™ MSP Enforcement System.
For questions or clarifications, please contact the MSP Enforcement Team.

Best regards,
MANDI EAR™ MSP Enforcement System
"""
        
        return content
    
    def _generate_api_payload(self, report: MSPComplianceReport) -> Dict[str, Any]:
        """Generate API payload for compliance report"""
        return {
            "report_id": report.id,
            "report_type": "msp_compliance",
            "period": {
                "start_date": report.report_period_start.isoformat(),
                "end_date": report.report_period_end.isoformat()
            },
            "region": report.region,
            "summary": {
                "total_violations": report.total_violations,
                "average_violation_percentage": report.average_violation_percentage,
                "estimated_losses": report.estimated_farmer_losses,
                "affected_farmers": report.most_affected_farmers
            },
            "violations_by_commodity": report.violations_by_commodity,
            "violations_by_location": report.violations_by_location,
            "recommendations": report.recommendations,
            "evidence_files": report.evidence_files,
            "generated_at": report.generated_at.isoformat(),
            "generated_by": report.generated_by
        }
    
    def _generate_portal_data(self, report: MSPComplianceReport) -> Dict[str, Any]:
        """Generate portal data for compliance report"""
        return {
            "report_metadata": {
                "id": report.id,
                "type": "MSP_COMPLIANCE_REPORT",
                "period_start": report.report_period_start.isoformat(),
                "period_end": report.report_period_end.isoformat(),
                "region": report.region,
                "generated_at": report.generated_at.isoformat()
            },
            "violation_summary": {
                "total_count": report.total_violations,
                "by_commodity": report.violations_by_commodity,
                "by_location": report.violations_by_location,
                "average_severity": report.average_violation_percentage
            },
            "impact_assessment": {
                "estimated_losses": report.estimated_farmer_losses,
                "affected_farmers": report.most_affected_farmers
            },
            "recommendations": report.recommendations,
            "evidence_package": report.evidence_files
        }
    
    async def _update_report_status(self, report: MSPComplianceReport) -> bool:
        """Update report status in database"""
        if not _pool:
            return False
        
        try:
            async with _pool.acquire() as conn:
                await conn.execute("""
                    UPDATE compliance_reports 
                    SET report_status = $1, submitted_at = NOW()
                    WHERE id = $2
                """, report.report_status, report.id)
            return True
        except Exception as e:
            logger.error("Error updating report status", error=str(e))
            return False
    
    async def notify_critical_violations(self, violations: List[MSPViolation]) -> bool:
        """Send immediate notifications for critical violations"""
        try:
            critical_violations = [v for v in violations if v.severity == AlertSeverity.CRITICAL]
            
            if not critical_violations:
                return True
            
            # Generate urgent notification
            notification = {
                "type": "CRITICAL_MSP_VIOLATIONS",
                "timestamp": datetime.utcnow().isoformat(),
                "violation_count": len(critical_violations),
                "violations": [
                    {
                        "id": v.id,
                        "commodity": v.commodity,
                        "location": f"{v.district}, {v.state}",
                        "violation_percentage": v.violation_percentage,
                        "detected_at": v.detected_at.isoformat()
                    }
                    for v in critical_violations
                ],
                "immediate_actions_required": [
                    "Deploy emergency procurement teams",
                    "Activate additional procurement centers",
                    "Issue public MSP guarantee notices",
                    "Investigate market manipulation"
                ]
            }
            
            # Send via multiple urgent channels
            await self._send_urgent_email(notification)
            await self._send_urgent_sms(notification)
            await self._send_urgent_api_alert(notification)
            
            logger.warning(
                "Critical MSP violations notification sent",
                critical_violations=len(critical_violations)
            )
            
            return True
            
        except Exception as e:
            logger.error("Error notifying critical violations", error=str(e))
            return False
    
    async def _send_urgent_email(self, notification: Dict[str, Any]) -> bool:
        """Send urgent email notification"""
        # Simulate urgent email
        logger.info("Urgent email notification sent", type=notification["type"])
        return True
    
    async def _send_urgent_sms(self, notification: Dict[str, Any]) -> bool:
        """Send urgent SMS notification"""
        # Simulate urgent SMS
        logger.info("Urgent SMS notification sent", type=notification["type"])
        return True
    
    async def _send_urgent_api_alert(self, notification: Dict[str, Any]) -> bool:
        """Send urgent API alert"""
        # Simulate urgent API alert
        logger.info("Urgent API alert sent", type=notification["type"])
        return True