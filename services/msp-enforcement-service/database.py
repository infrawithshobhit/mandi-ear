"""
Database operations for MSP Enforcement Service
"""

import asyncio
import asyncpg
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import json
import os

from models import (
    MSPRate, MSPViolation, MSPAlert, ProcurementCenter, 
    AlternativeSuggestion, GovernmentDataSource, MSPComplianceReport
)

logger = structlog.get_logger()

# Database connection pool
_pool: Optional[asyncpg.Pool] = None

async def init_db():
    """Initialize database connection pool"""
    global _pool
    
    database_url = os.getenv("DATABASE_URL", "postgresql://mandi_user:mandi_pass@localhost:5432/mandi_ear")
    
    try:
        _pool = await asyncpg.create_pool(
            database_url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        
        # Create tables if they don't exist
        await _create_tables()
        
        logger.info("MSP database initialized")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise

async def close_db():
    """Close database connection pool"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("MSP database connection closed")

async def _create_tables():
    """Create database tables for MSP service"""
    if not _pool:
        return
    
    async with _pool.acquire() as conn:
        # MSP rates table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS msp_rates (
                id VARCHAR PRIMARY KEY,
                commodity VARCHAR NOT NULL,
                variety VARCHAR,
                season VARCHAR NOT NULL,
                crop_year VARCHAR NOT NULL,
                msp_price DECIMAL(10,2) NOT NULL,
                unit VARCHAR DEFAULT 'quintal',
                commodity_type VARCHAR NOT NULL,
                effective_date DATE NOT NULL,
                expiry_date DATE,
                announcement_date DATE NOT NULL,
                source_document VARCHAR,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # MSP violations table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS msp_violations (
                id VARCHAR PRIMARY KEY,
                commodity VARCHAR NOT NULL,
                variety VARCHAR,
                mandi_id VARCHAR NOT NULL,
                mandi_name VARCHAR NOT NULL,
                district VARCHAR NOT NULL,
                state VARCHAR NOT NULL,
                market_price DECIMAL(10,2) NOT NULL,
                msp_price DECIMAL(10,2) NOT NULL,
                price_difference DECIMAL(10,2) NOT NULL,
                violation_percentage DECIMAL(5,2) NOT NULL,
                violation_type VARCHAR NOT NULL,
                detected_at TIMESTAMP DEFAULT NOW(),
                severity VARCHAR NOT NULL,
                is_resolved BOOLEAN DEFAULT FALSE,
                resolution_notes TEXT,
                resolved_at TIMESTAMP,
                evidence JSONB
            )
        """)
        
        # MSP alerts table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS msp_alerts (
                id VARCHAR PRIMARY KEY,
                violation_id VARCHAR NOT NULL,
                farmer_id VARCHAR,
                alert_type VARCHAR DEFAULT 'msp_violation',
                title VARCHAR NOT NULL,
                message TEXT NOT NULL,
                severity VARCHAR NOT NULL,
                commodity VARCHAR NOT NULL,
                location VARCHAR NOT NULL,
                suggested_actions JSONB,
                alternative_centers JSONB,
                sent_at TIMESTAMP DEFAULT NOW(),
                is_read BOOLEAN DEFAULT FALSE,
                is_acknowledged BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Procurement centers table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS procurement_centers (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                center_type VARCHAR NOT NULL,
                address TEXT NOT NULL,
                district VARCHAR NOT NULL,
                state VARCHAR NOT NULL,
                pincode VARCHAR,
                latitude DECIMAL(10,8),
                longitude DECIMAL(11,8),
                contact_person VARCHAR,
                phone_number VARCHAR,
                email VARCHAR,
                operating_hours VARCHAR,
                commodities_accepted JSONB,
                storage_capacity DECIMAL(12,2),
                current_stock DECIMAL(12,2),
                is_operational BOOLEAN DEFAULT TRUE,
                last_updated TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Alternative suggestions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS alternative_suggestions (
                id VARCHAR PRIMARY KEY,
                commodity VARCHAR NOT NULL,
                original_location VARCHAR NOT NULL,
                suggested_center_id VARCHAR NOT NULL,
                suggested_center_name VARCHAR NOT NULL,
                suggested_location VARCHAR NOT NULL,
                distance_km DECIMAL(8,2) NOT NULL,
                price_offered DECIMAL(10,2) NOT NULL,
                price_advantage DECIMAL(10,2) NOT NULL,
                transportation_cost DECIMAL(10,2),
                net_benefit DECIMAL(10,2),
                contact_info JSONB,
                directions TEXT,
                estimated_travel_time VARCHAR,
                suggestion_reason VARCHAR NOT NULL,
                confidence_score DECIMAL(3,2) DEFAULT 0.8,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Government data sources table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS government_data_sources (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                url VARCHAR NOT NULL,
                api_endpoint VARCHAR,
                update_frequency INTEGER NOT NULL,
                last_sync TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                reliability_score DECIMAL(3,2) DEFAULT 0.9,
                auth_required BOOLEAN DEFAULT FALSE,
                api_key VARCHAR
            )
        """)
        
        # Compliance reports table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS compliance_reports (
                id VARCHAR PRIMARY KEY,
                report_period_start DATE NOT NULL,
                report_period_end DATE NOT NULL,
                region VARCHAR NOT NULL,
                total_violations INTEGER DEFAULT 0,
                violations_by_commodity JSONB,
                violations_by_location JSONB,
                average_violation_percentage DECIMAL(5,2) DEFAULT 0,
                most_affected_farmers INTEGER,
                estimated_farmer_losses DECIMAL(15,2),
                recommendations JSONB,
                evidence_files JSONB,
                generated_at TIMESTAMP DEFAULT NOW(),
                generated_by VARCHAR DEFAULT 'MSP Enforcement System',
                report_status VARCHAR DEFAULT 'draft',
                submitted_at TIMESTAMP,
                report_data JSONB
            )
        """)
        
        # Create indexes for better performance
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_msp_rates_commodity ON msp_rates(commodity, is_active)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_msp_violations_commodity ON msp_violations(commodity, detected_at)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_msp_violations_location ON msp_violations(state, district)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_procurement_centers_location ON procurement_centers(state, district, is_operational)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_msp_alerts_farmer ON msp_alerts(farmer_id, sent_at)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_compliance_reports_period ON compliance_reports(report_period_start, report_period_end)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_compliance_reports_region ON compliance_reports(region, generated_at)")

# MSP Rates operations
async def store_msp_rate(msp_rate: MSPRate) -> bool:
    """Store MSP rate in database"""
    if not _pool:
        return False
    
    try:
        async with _pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO msp_rates (
                    id, commodity, variety, season, crop_year, msp_price, unit,
                    commodity_type, effective_date, expiry_date, announcement_date,
                    source_document, is_active
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (id) DO UPDATE SET
                    msp_price = EXCLUDED.msp_price,
                    effective_date = EXCLUDED.effective_date,
                    expiry_date = EXCLUDED.expiry_date,
                    updated_at = NOW()
            """, 
                msp_rate.id, msp_rate.commodity, msp_rate.variety, 
                msp_rate.season.value, msp_rate.crop_year, msp_rate.msp_price,
                msp_rate.unit, msp_rate.commodity_type.value, msp_rate.effective_date,
                msp_rate.expiry_date, msp_rate.announcement_date, 
                msp_rate.source_document, msp_rate.is_active
            )
        return True
    except Exception as e:
        logger.error("Error storing MSP rate", error=str(e))
        return False

async def get_active_msp_rates() -> List[MSPRate]:
    """Get all active MSP rates"""
    if not _pool:
        return []
    
    try:
        async with _pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM msp_rates 
                WHERE is_active = TRUE 
                AND (expiry_date IS NULL OR expiry_date > CURRENT_DATE)
                ORDER BY commodity, season
            """)
            
            rates = []
            for row in rows:
                rate = MSPRate(
                    id=row['id'],
                    commodity=row['commodity'],
                    variety=row['variety'],
                    season=row['season'],
                    crop_year=row['crop_year'],
                    msp_price=float(row['msp_price']),
                    unit=row['unit'],
                    commodity_type=row['commodity_type'],
                    effective_date=row['effective_date'],
                    expiry_date=row['expiry_date'],
                    announcement_date=row['announcement_date'],
                    source_document=row['source_document'],
                    is_active=row['is_active'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                rates.append(rate)
            
            return rates
    except Exception as e:
        logger.error("Error getting active MSP rates", error=str(e))
        return []

# Violations operations
async def store_msp_violation(violation: MSPViolation) -> bool:
    """Store MSP violation in database"""
    if not _pool:
        return False
    
    try:
        async with _pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO msp_violations (
                    id, commodity, variety, mandi_id, mandi_name, district, state,
                    market_price, msp_price, price_difference, violation_percentage,
                    violation_type, severity, is_resolved, resolution_notes,
                    resolved_at, evidence
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                ON CONFLICT (id) DO UPDATE SET
                    market_price = EXCLUDED.market_price,
                    violation_percentage = EXCLUDED.violation_percentage,
                    severity = EXCLUDED.severity,
                    is_resolved = EXCLUDED.is_resolved,
                    resolution_notes = EXCLUDED.resolution_notes,
                    resolved_at = EXCLUDED.resolved_at,
                    evidence = EXCLUDED.evidence
            """,
                violation.id, violation.commodity, violation.variety,
                violation.mandi_id, violation.mandi_name, violation.district,
                violation.state, violation.market_price, violation.msp_price,
                violation.price_difference, violation.violation_percentage,
                violation.violation_type.value, violation.severity.value,
                violation.is_resolved, violation.resolution_notes,
                violation.resolved_at, json.dumps(violation.evidence) if violation.evidence else None
            )
        return True
    except Exception as e:
        logger.error("Error storing MSP violation", error=str(e))
        return False

# Alerts operations
async def store_msp_alert(alert: MSPAlert) -> bool:
    """Store MSP alert in database"""
    if not _pool:
        return False
    
    try:
        async with _pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO msp_alerts (
                    id, violation_id, farmer_id, alert_type, title, message,
                    severity, commodity, location, suggested_actions,
                    alternative_centers, is_read, is_acknowledged
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """,
                alert.id, alert.violation_id, alert.farmer_id, alert.alert_type,
                alert.title, alert.message, alert.severity.value, alert.commodity,
                alert.location, json.dumps(alert.suggested_actions),
                json.dumps(alert.alternative_centers), alert.is_read, alert.is_acknowledged
            )
        return True
    except Exception as e:
        logger.error("Error storing MSP alert", error=str(e))
        return False

# Procurement centers operations
async def store_procurement_center(center: ProcurementCenter) -> bool:
    """Store procurement center in database"""
    if not _pool:
        return False
    
    try:
        async with _pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO procurement_centers (
                    id, name, center_type, address, district, state, pincode,
                    latitude, longitude, contact_person, phone_number, email,
                    operating_hours, commodities_accepted, storage_capacity,
                    current_stock, is_operational
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    address = EXCLUDED.address,
                    phone_number = EXCLUDED.phone_number,
                    email = EXCLUDED.email,
                    operating_hours = EXCLUDED.operating_hours,
                    commodities_accepted = EXCLUDED.commodities_accepted,
                    storage_capacity = EXCLUDED.storage_capacity,
                    current_stock = EXCLUDED.current_stock,
                    is_operational = EXCLUDED.is_operational,
                    last_updated = NOW()
            """,
                center.id, center.name, center.center_type, center.address,
                center.district, center.state, center.pincode, center.latitude,
                center.longitude, center.contact_person, center.phone_number,
                center.email, center.operating_hours, json.dumps(center.commodities_accepted),
                center.storage_capacity, center.current_stock, center.is_operational
            )
        return True
    except Exception as e:
        logger.error("Error storing procurement center", error=str(e))
        return False

async def get_procurement_centers(
    state: Optional[str] = None,
    commodity: Optional[str] = None,
    is_operational: bool = True
) -> List[ProcurementCenter]:
    """Get procurement centers with filters"""
    if not _pool:
        return []
    
    try:
        query = "SELECT * FROM procurement_centers WHERE is_operational = $1"
        params = [is_operational]
        
        if state:
            query += " AND LOWER(state) = LOWER($2)"
            params.append(state)
        
        if commodity:
            query += f" AND (commodities_accepted IS NULL OR commodities_accepted::text ILIKE ${'3' if state else '2'})"
            params.append(f'%{commodity}%')
        
        query += " ORDER BY name"
        
        async with _pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
            centers = []
            for row in rows:
                center = ProcurementCenter(
                    id=row['id'],
                    name=row['name'],
                    center_type=row['center_type'],
                    address=row['address'],
                    district=row['district'],
                    state=row['state'],
                    pincode=row['pincode'],
                    latitude=row['latitude'],
                    longitude=row['longitude'],
                    contact_person=row['contact_person'],
                    phone_number=row['phone_number'],
                    email=row['email'],
                    operating_hours=row['operating_hours'],
                    commodities_accepted=json.loads(row['commodities_accepted']) if row['commodities_accepted'] else [],
                    storage_capacity=row['storage_capacity'],
                    current_stock=row['current_stock'],
                    is_operational=row['is_operational'],
                    last_updated=row['last_updated']
                )
                centers.append(center)
            
            return centers
    except Exception as e:
        logger.error("Error getting procurement centers", error=str(e))
        return []

# Alternative suggestions operations
async def store_alternative_suggestion(suggestion: AlternativeSuggestion) -> bool:
    """Store alternative suggestion in database"""
    if not _pool:
        return False
    
    try:
        async with _pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO alternative_suggestions (
                    id, commodity, original_location, suggested_center_id,
                    suggested_center_name, suggested_location, distance_km,
                    price_offered, price_advantage, transportation_cost,
                    net_benefit, contact_info, directions, estimated_travel_time,
                    suggestion_reason, confidence_score
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            """,
                suggestion.id, suggestion.commodity, suggestion.original_location,
                suggestion.suggested_center_id, suggestion.suggested_center_name,
                suggestion.suggested_location, suggestion.distance_km,
                suggestion.price_offered, suggestion.price_advantage,
                suggestion.transportation_cost, suggestion.net_benefit,
                json.dumps(suggestion.contact_info) if suggestion.contact_info else None,
                suggestion.directions, suggestion.estimated_travel_time,
                suggestion.suggestion_reason, suggestion.confidence_score
            )
        return True
    except Exception as e:
        logger.error("Error storing alternative suggestion", error=str(e))
        return False

# Mock functions for integration with other services
async def get_current_market_prices(
    min_timestamp: datetime,
    min_confidence: float = 0.7
) -> List[Dict[str, Any]]:
    """Get current market prices from price discovery service"""
    # This would integrate with the price discovery service
    # For now, return mock data
    import random
    
    commodities = ["Wheat", "Rice", "Maize", "Bajra", "Gram", "Tur", "Groundnut", "Mustard"]
    states = ["Punjab", "Haryana", "Uttar Pradesh", "Maharashtra", "Gujarat", "Rajasthan"]
    
    mock_prices = []
    for _ in range(random.randint(20, 50)):
        commodity = random.choice(commodities)
        state = random.choice(states)
        base_price = random.uniform(1500, 4000)
        
        mock_prices.append({
            'commodity': commodity,
            'variety': f'{commodity} Grade A',
            'price': base_price + random.uniform(-300, 300),
            'mandi_id': f'mandi_{state.lower()}_{random.randint(1, 100)}',
            'mandi_name': f'{random.choice(["Central", "Main", "New"])} Mandi {state}',
            'district': f'District {random.randint(1, 10)}',
            'state': state,
            'confidence': random.uniform(0.7, 0.95),
            'timestamp': datetime.utcnow()
        })
    
    return mock_prices

async def get_nearby_mandis(
    state: str,
    district: str,
    commodity: str,
    radius_km: float = 200,
    min_price: float = 0
) -> List[Dict[str, Any]]:
    """Get nearby mandis with better prices"""
    # Mock implementation
    import random
    
    nearby_mandis = []
    for i in range(random.randint(3, 8)):
        price = random.uniform(min_price, min_price * 1.2)
        distance = random.uniform(50, radius_km)
        
        nearby_mandis.append({
            'mandi_id': f'nearby_mandi_{i}',
            'mandi_name': f'Mandi {i+1}',
            'location': f'District {i+1}, {state}',
            'price': price,
            'distance_km': distance,
            'confidence': random.uniform(0.7, 0.9)
        })
    
    return nearby_mandis

async def get_government_data_sources() -> List[GovernmentDataSource]:
    """Get government data sources from database"""
    if not _pool:
        return []
    
    try:
        async with _pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM government_data_sources WHERE is_active = TRUE")
            
            sources = []
            for row in rows:
                source = GovernmentDataSource(
                    id=row['id'],
                    name=row['name'],
                    url=row['url'],
                    api_endpoint=row['api_endpoint'],
                    update_frequency=row['update_frequency'],
                    last_sync=row['last_sync'],
                    is_active=row['is_active'],
                    reliability_score=float(row['reliability_score']),
                    auth_required=row['auth_required'],
                    api_key=row['api_key']
                )
                sources.append(source)
            
            return sources
    except Exception as e:
        logger.error("Error getting government data sources", error=str(e))
        return []

async def get_mandi_info(mandi_id: str) -> Optional[Dict[str, Any]]:
    """Get mandi information"""
    # Mock implementation - would integrate with price discovery service
    return {
        'id': mandi_id,
        'name': f'Mandi {mandi_id}',
        'location': 'Sample Location',
        'district': 'Sample District',
        'state': 'Sample State'
    }

async def get_farmer_preferences(farmer_id: str) -> Dict[str, Any]:
    """Get farmer preferences for notifications"""
    # Mock implementation
    return {
        'preferred_language': 'hindi',
        'notification_channels': ['sms', 'push'],
        'alert_threshold': 5.0,
        'location': {'state': 'Punjab', 'district': 'Ludhiana'}
    }

# Compliance Reports operations
async def store_compliance_report(report: MSPComplianceReport) -> bool:
    """Store compliance report in database"""
    if not _pool:
        return False
    
    try:
        async with _pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO compliance_reports (
                    id, report_period_start, report_period_end, region,
                    total_violations, violations_by_commodity, violations_by_location,
                    average_violation_percentage, most_affected_farmers,
                    estimated_farmer_losses, recommendations, evidence_files,
                    generated_at, generated_by, report_status, report_data
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                ON CONFLICT (id) DO UPDATE SET
                    report_status = EXCLUDED.report_status,
                    submitted_at = CASE WHEN EXCLUDED.report_status = 'submitted' THEN NOW() ELSE compliance_reports.submitted_at END
            """,
                report.id, report.report_period_start, report.report_period_end,
                report.region, report.total_violations,
                json.dumps(report.violations_by_commodity),
                json.dumps(report.violations_by_location),
                report.average_violation_percentage, report.most_affected_farmers,
                report.estimated_farmer_losses, json.dumps(report.recommendations),
                json.dumps(report.evidence_files), report.generated_at,
                report.generated_by, report.report_status,
                json.dumps(getattr(report, 'report_data', {}))
            )
        return True
    except Exception as e:
        logger.error("Error storing compliance report", error=str(e))
        return False

async def get_compliance_reports(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    region: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
) -> List[MSPComplianceReport]:
    """Get compliance reports with filters"""
    if not _pool:
        return []
    
    try:
        query = "SELECT * FROM compliance_reports WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND report_period_start >= $" + str(len(params) + 1)
            params.append(start_date)
        
        if end_date:
            query += " AND report_period_end <= $" + str(len(params) + 1)
            params.append(end_date)
        
        if region:
            query += " AND LOWER(region) = LOWER($" + str(len(params) + 1) + ")"
            params.append(region)
        
        if status:
            query += " AND report_status = $" + str(len(params) + 1)
            params.append(status)
        
        query += " ORDER BY generated_at DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)
        
        async with _pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
            reports = []
            for row in rows:
                report = MSPComplianceReport(
                    id=row['id'],
                    report_period_start=row['report_period_start'],
                    report_period_end=row['report_period_end'],
                    region=row['region'],
                    total_violations=row['total_violations'],
                    violations_by_commodity=json.loads(row['violations_by_commodity']) if row['violations_by_commodity'] else {},
                    violations_by_location=json.loads(row['violations_by_location']) if row['violations_by_location'] else {},
                    average_violation_percentage=float(row['average_violation_percentage']),
                    most_affected_farmers=row['most_affected_farmers'],
                    estimated_farmer_losses=float(row['estimated_farmer_losses']) if row['estimated_farmer_losses'] else 0,
                    recommendations=json.loads(row['recommendations']) if row['recommendations'] else [],
                    evidence_files=json.loads(row['evidence_files']) if row['evidence_files'] else [],
                    generated_at=row['generated_at'],
                    generated_by=row['generated_by'],
                    report_status=row['report_status']
                )
                reports.append(report)
            
            return reports
    except Exception as e:
        logger.error("Error getting compliance reports", error=str(e))
        return []

async def get_compliance_report_by_id(report_id: str) -> Optional[MSPComplianceReport]:
    """Get compliance report by ID"""
    if not _pool:
        return None
    
    try:
        async with _pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM compliance_reports WHERE id = $1", 
                report_id
            )
            
            if row:
                report = MSPComplianceReport(
                    id=row['id'],
                    report_period_start=row['report_period_start'],
                    report_period_end=row['report_period_end'],
                    region=row['region'],
                    total_violations=row['total_violations'],
                    violations_by_commodity=json.loads(row['violations_by_commodity']) if row['violations_by_commodity'] else {},
                    violations_by_location=json.loads(row['violations_by_location']) if row['violations_by_location'] else {},
                    average_violation_percentage=float(row['average_violation_percentage']),
                    most_affected_farmers=row['most_affected_farmers'],
                    estimated_farmer_losses=float(row['estimated_farmer_losses']) if row['estimated_farmer_losses'] else 0,
                    recommendations=json.loads(row['recommendations']) if row['recommendations'] else [],
                    evidence_files=json.loads(row['evidence_files']) if row['evidence_files'] else [],
                    generated_at=row['generated_at'],
                    generated_by=row['generated_by'],
                    report_status=row['report_status']
                )
                
                # Add additional data if available
                if row['report_data']:
                    report_data = json.loads(row['report_data'])
                    report.market_analysis = report_data.get('market_analysis', {})
                    report.farmer_impact = report_data.get('farmer_impact', {})
                    report.evidence_summary = report_data.get('evidence_summary', {})
                    report.violation_details = report_data.get('violation_details', [])
                
                return report
            
            return None
    except Exception as e:
        logger.error("Error getting compliance report by ID", report_id=report_id, error=str(e))
        return None