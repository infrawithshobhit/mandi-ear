"""
MSP Alert and Alternative Suggestion System
Handles alerts for MSP violations and suggests alternative markets
"""

import asyncio
import structlog
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import aiohttp
import math

from models import (
    MSPViolation, MSPAlert, AlternativeSuggestion, ProcurementCenter,
    AlertSeverity, ViolationType
)
from database import (
    get_procurement_centers, get_nearby_mandis, store_msp_alert,
    store_alternative_suggestion, get_farmer_preferences
)

logger = structlog.get_logger()

class MSPAlertSystem:
    """Handles MSP violation alerts and alternative suggestions"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.notification_queue: asyncio.Queue = asyncio.Queue()
        self.notification_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    async def initialize(self):
        """Initialize the alert system"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        await self._start_notification_processor()
        logger.info("MSP alert system initialized")
    
    async def shutdown(self):
        """Shutdown the alert system"""
        self.is_running = False
        
        if self.notification_task:
            self.notification_task.cancel()
            try:
                await self.notification_task
            except asyncio.CancelledError:
                pass
        
        if self.session:
            await self.session.close()
        
        logger.info("MSP alert system shutdown")
    
    async def _start_notification_processor(self):
        """Start the notification processing task"""
        self.is_running = True
        self.notification_task = asyncio.create_task(self._process_notifications())
    
    async def _process_notifications(self):
        """Process notification queue"""
        while self.is_running:
            try:
                # Wait for notification with timeout
                alert = await asyncio.wait_for(
                    self.notification_queue.get(), 
                    timeout=5.0
                )
                
                await self._send_notification(alert)
                self.notification_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error processing notification", error=str(e))
    
    async def process_violation(self, violation: MSPViolation) -> List[MSPAlert]:
        """Process a violation and generate alerts"""
        try:
            alerts = []
            
            # Create main violation alert
            main_alert = await self._create_violation_alert(violation)
            if main_alert:
                alerts.append(main_alert)
                await self.notification_queue.put(main_alert)
            
            # Find alternative suggestions
            alternatives = await self._find_alternatives(violation)
            
            # Create alternative suggestion alerts
            if alternatives:
                alt_alert = await self._create_alternative_alert(violation, alternatives)
                if alt_alert:
                    alerts.append(alt_alert)
                    await self.notification_queue.put(alt_alert)
            
            # Store alerts
            for alert in alerts:
                await store_msp_alert(alert)
            
            logger.info(
                "Processed MSP violation",
                violation_id=violation.id,
                alerts_created=len(alerts),
                alternatives_found=len(alternatives)
            )
            
            return alerts
            
        except Exception as e:
            logger.error("Error processing violation", violation_id=violation.id, error=str(e))
            return []
    
    async def _create_violation_alert(self, violation: MSPViolation) -> Optional[MSPAlert]:
        """Create alert for MSP violation"""
        try:
            # Determine alert message based on severity with immediate action focus
            if violation.severity == AlertSeverity.CRITICAL:
                title = f"🚨 URGENT: Critical MSP Violation - {violation.commodity}"
                message = (
                    f"⚠️ IMMEDIATE ACTION REQUIRED ⚠️\n"
                    f"{violation.commodity} prices at {violation.mandi_name} are "
                    f"{violation.violation_percentage:.1f}% below MSP!\n\n"
                    f"💰 Current Market: ₹{violation.market_price:.2f}/quintal\n"
                    f"💰 Guaranteed MSP: ₹{violation.msp_price:.2f}/quintal\n"
                    f"💸 Loss per quintal: ₹{abs(violation.price_difference):.2f}\n\n"
                    f"🛑 DO NOT SELL at current prices!\n"
                    f"📞 Call helpline: 1800-180-1551 (Kisan Call Centre)"
                )
            elif violation.severity == AlertSeverity.HIGH:
                title = f"⚠️ HIGH PRIORITY: MSP Violation - {violation.commodity}"
                message = (
                    f"🔴 HIGH PRIORITY ALERT 🔴\n"
                    f"{violation.commodity} prices at {violation.mandi_name} are "
                    f"{violation.violation_percentage:.1f}% below MSP.\n\n"
                    f"💰 Current Market: ₹{violation.market_price:.2f}/quintal\n"
                    f"💰 Guaranteed MSP: ₹{violation.msp_price:.2f}/quintal\n"
                    f"💸 Loss per quintal: ₹{abs(violation.price_difference):.2f}\n\n"
                    f"⏰ Consider waiting or seeking alternatives.\n"
                    f"📞 Helpline: 1800-180-1551"
                )
            elif violation.severity == AlertSeverity.MEDIUM:
                title = f"📉 MSP Alert: {violation.commodity} Below Support Price"
                message = (
                    f"🟡 PRICE ALERT 🟡\n"
                    f"{violation.commodity} at {violation.mandi_name} is "
                    f"{violation.violation_percentage:.1f}% below MSP.\n\n"
                    f"💰 Market: ₹{violation.market_price:.2f} | MSP: ₹{violation.msp_price:.2f}\n"
                    f"💸 Potential loss: ₹{abs(violation.price_difference):.2f}/quintal\n\n"
                    f"💡 Check alternatives before selling."
                )
            else:
                title = f"📊 Price Notice: {violation.commodity} Near MSP Threshold"
                message = (
                    f"🟢 PRICE NOTICE 🟢\n"
                    f"{violation.commodity} at {violation.mandi_name} is slightly below MSP.\n\n"
                    f"💰 Market: ₹{violation.market_price:.2f} | MSP: ₹{violation.msp_price:.2f}\n"
                    f"📈 Monitor prices closely."
                )
            
            # Generate immediate action suggestions based on severity
            suggested_actions = []
            
            if violation.severity == AlertSeverity.CRITICAL:
                suggested_actions = [
                    "🛑 STOP: Do not sell at current market price",
                    "📞 CALL: Kisan Call Centre at 1800-180-1551 immediately",
                    "🏛️ VISIT: Nearest government procurement center",
                    "📋 PREPARE: Farmer ID, land records, quality certificate",
                    "🚛 ARRANGE: Transportation to procurement center",
                    "⏰ ACT NOW: Prices may drop further"
                ]
            elif violation.severity == AlertSeverity.HIGH:
                suggested_actions = [
                    "⏸️ PAUSE: Avoid selling at current prices",
                    "🔍 SEARCH: Check government procurement centers",
                    "📞 CONTACT: Local agriculture officer",
                    "🤝 CONNECT: Farmer Producer Organizations",
                    "📊 MONITOR: Price trends for next 24-48 hours",
                    "🚛 PLAN: Transportation to better markets"
                ]
            elif violation.severity == AlertSeverity.MEDIUM:
                suggested_actions = [
                    "⏳ WAIT: Consider delaying sale if possible",
                    "🔍 EXPLORE: Alternative markets and buyers",
                    "📞 INQUIRE: Government procurement availability",
                    "📈 TRACK: Price movements in nearby mandis",
                    "🤝 CONSULT: Fellow farmers and FPOs"
                ]
            else:
                suggested_actions = [
                    "📊 MONITOR: Keep tracking price changes",
                    "🔍 COMPARE: Prices in nearby markets",
                    "📞 STAY INFORMED: Regular price updates",
                    "🤝 NETWORK: Connect with other farmers"
                ]
            
            alert = MSPAlert(
                violation_id=violation.id,
                title=title,
                message=message,
                severity=violation.severity,
                commodity=violation.commodity,
                location=f"{violation.district}, {violation.state}",
                suggested_actions=suggested_actions
            )
            
            return alert
            
        except Exception as e:
            logger.error("Error creating violation alert", error=str(e))
            return None
    
    async def _find_alternatives(self, violation: MSPViolation) -> List[AlternativeSuggestion]:
        """Find alternative markets and procurement centers"""
        alternatives = []
        
        try:
            # Find government procurement centers (highest priority)
            procurement_centers = await self._find_procurement_centers(violation)
            for center in procurement_centers:
                alt = await self._create_procurement_suggestion(violation, center)
                if alt:
                    alternatives.append(alt)
            
            # Find nearby mandis with better prices
            nearby_mandis = await self._find_better_price_mandis(violation)
            for mandi in nearby_mandis:
                alt = await self._create_mandi_suggestion(violation, mandi)
                if alt:
                    alternatives.append(alt)
            
            # Find FPO (Farmer Producer Organization) centers
            fpo_centers = await self._find_fpo_centers(violation)
            for fpo in fpo_centers:
                alt = await self._create_fpo_suggestion(violation, fpo)
                if alt:
                    alternatives.append(alt)
            
            # Find private buyers offering better prices
            private_buyers = await self._find_private_buyers(violation)
            for buyer in private_buyers:
                alt = await self._create_private_buyer_suggestion(violation, buyer)
                if alt:
                    alternatives.append(alt)
            
            # Sort by priority: Government centers first, then by net benefit
            alternatives.sort(key=lambda x: (
                0 if 'government' in x.suggestion_reason.lower() or 'msp' in x.suggestion_reason.lower() else 1,
                -(x.net_benefit or 0)
            ))
            
            # Limit to top 8 alternatives for better coverage
            return alternatives[:8]
            
        except Exception as e:
            logger.error("Error finding alternatives", error=str(e))
            return []
    
    async def _find_procurement_centers(self, violation: MSPViolation) -> List[ProcurementCenter]:
        """Find government procurement centers for the commodity"""
        try:
            # Get procurement centers from multiple sources
            centers = []
            
            # Primary search: same state, commodity-specific
            state_centers = await get_procurement_centers(
                state=violation.state,
                commodity=violation.commodity,
                is_operational=True
            )
            centers.extend(state_centers)
            
            # Secondary search: neighboring states if not enough centers found
            if len(centers) < 3:
                neighboring_states = await self._get_neighboring_states(violation.state)
                for neighbor_state in neighboring_states[:2]:  # Check up to 2 neighboring states
                    neighbor_centers = await get_procurement_centers(
                        state=neighbor_state,
                        commodity=violation.commodity,
                        is_operational=True
                    )
                    centers.extend(neighbor_centers[:2])  # Add up to 2 centers per state
            
            # Tertiary search: any center accepting the commodity (broader search)
            if len(centers) < 2:
                all_centers = await get_procurement_centers(
                    commodity=violation.commodity,
                    is_operational=True
                )
                # Add centers not already included
                existing_ids = {c.id for c in centers}
                for center in all_centers:
                    if center.id not in existing_ids and len(centers) < 5:
                        centers.append(center)
            
            # Filter and sort centers by distance and capacity
            filtered_centers = []
            for center in centers:
                # Calculate approximate distance
                distance = await self._calculate_distance(
                    violation.district, violation.state,
                    center.district, center.state
                )
                
                # Only include centers within reasonable distance (500km)
                if distance <= 500:
                    # Add distance as attribute for sorting
                    center.estimated_distance = distance
                    filtered_centers.append(center)
            
            # Sort by priority: FCI first, then by distance, then by capacity
            filtered_centers.sort(key=lambda c: (
                0 if c.center_type == 'FCI' else 1,  # FCI centers first
                getattr(c, 'estimated_distance', 999),  # Closer centers first
                -(c.storage_capacity or 0)  # Higher capacity first
            ))
            
            return filtered_centers[:6]  # Return top 6 centers
            
        except Exception as e:
            logger.error("Error finding procurement centers", error=str(e))
            return []
    
    async def _get_neighboring_states(self, state: str) -> List[str]:
        """Get neighboring states for expanded search"""
        # Simplified neighboring states mapping
        neighbors = {
            'Punjab': ['Haryana', 'Himachal Pradesh', 'Rajasthan'],
            'Haryana': ['Punjab', 'Uttar Pradesh', 'Rajasthan', 'Delhi'],
            'Uttar Pradesh': ['Haryana', 'Madhya Pradesh', 'Rajasthan', 'Bihar'],
            'Madhya Pradesh': ['Uttar Pradesh', 'Rajasthan', 'Gujarat', 'Maharashtra'],
            'Maharashtra': ['Madhya Pradesh', 'Gujarat', 'Karnataka', 'Andhra Pradesh'],
            'Gujarat': ['Madhya Pradesh', 'Maharashtra', 'Rajasthan'],
            'Rajasthan': ['Punjab', 'Haryana', 'Uttar Pradesh', 'Madhya Pradesh', 'Gujarat'],
            'Karnataka': ['Maharashtra', 'Andhra Pradesh', 'Tamil Nadu', 'Kerala'],
            'Andhra Pradesh': ['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Telangana'],
            'Tamil Nadu': ['Karnataka', 'Andhra Pradesh', 'Kerala'],
            'Kerala': ['Karnataka', 'Tamil Nadu'],
            'West Bengal': ['Bihar', 'Jharkhand', 'Odisha'],
            'Bihar': ['Uttar Pradesh', 'West Bengal', 'Jharkhand'],
            'Odisha': ['West Bengal', 'Jharkhand', 'Chhattisgarh', 'Andhra Pradesh'],
            'Telangana': ['Andhra Pradesh', 'Karnataka', 'Maharashtra'],
            'Assam': ['Meghalaya', 'Arunachal Pradesh', 'Nagaland'],
            'Himachal Pradesh': ['Punjab', 'Uttarakhand'],
            'Uttarakhand': ['Himachal Pradesh', 'Uttar Pradesh'],
            'Jharkhand': ['Bihar', 'West Bengal', 'Odisha', 'Chhattisgarh'],
            'Chhattisgarh': ['Jharkhand', 'Odisha', 'Madhya Pradesh', 'Maharashtra']
        }
        
        return neighbors.get(state, [])
    
    async def _find_better_price_mandis(self, violation: MSPViolation) -> List[Dict[str, Any]]:
        """Find nearby mandis with better prices"""
        try:
            # Get nearby mandis within 200km
            nearby_mandis = await get_nearby_mandis(
                state=violation.state,
                district=violation.district,
                commodity=violation.commodity,
                radius_km=200,
                min_price=violation.msp_price * 0.95  # At least 95% of MSP
            )
            
            return nearby_mandis[:10]  # Limit to 10 mandis
            
        except Exception as e:
            logger.error("Error finding better price mandis", error=str(e))
            return []
    
    async def _find_fpo_centers(self, violation: MSPViolation) -> List[Dict[str, Any]]:
        """Find Farmer Producer Organization centers"""
        try:
            # In production, this would query FPO database
            # For now, simulate FPO centers
            fpo_centers = []
            
            # Generate sample FPO centers based on location
            fpo_names = [
                f"{violation.district} Farmers Collective",
                f"{violation.state} Agricultural Cooperative",
                f"United Farmers {violation.commodity} FPO",
                f"Progressive {violation.commodity} Growers Association"
            ]
            
            for i, name in enumerate(fpo_names[:3]):  # Limit to 3 FPOs
                # FPOs typically offer 2-5% above market price
                fpo_price = violation.market_price * (1.02 + i * 0.01)
                
                fpo_centers.append({
                    'id': f'fpo_{violation.state.lower()}_{i+1}',
                    'name': name,
                    'location': f"{violation.district}, {violation.state}",
                    'price_offered': min(fpo_price, violation.msp_price),  # Cap at MSP
                    'distance_km': 25 + i * 15,  # 25-55 km range
                    'contact_phone': f'+91-{9000000000 + i}',
                    'member_count': 500 + i * 200,
                    'storage_capacity': 10000 + i * 5000,
                    'confidence': 0.85
                })
            
            return fpo_centers
            
        except Exception as e:
            logger.error("Error finding FPO centers", error=str(e))
            return []
    
    async def _find_private_buyers(self, violation: MSPViolation) -> List[Dict[str, Any]]:
        """Find private buyers offering better prices"""
        try:
            # In production, this would query private buyer database
            # For now, simulate private buyers
            private_buyers = []
            
            buyer_types = [
                "Food Processing Company",
                "Export House",
                "Commodity Trader",
                "Retail Chain Procurement"
            ]
            
            for i, buyer_type in enumerate(buyer_types[:2]):  # Limit to 2 buyers
                # Private buyers might offer competitive prices
                buyer_price = violation.market_price * (1.03 + i * 0.02)
                
                # Only include if they offer better than current market
                if buyer_price > violation.market_price:
                    private_buyers.append({
                        'id': f'buyer_{violation.commodity.lower()}_{i+1}',
                        'name': f"{violation.commodity} {buyer_type}",
                        'buyer_type': buyer_type,
                        'location': f"Industrial Area, {violation.state}",
                        'price_offered': min(buyer_price, violation.msp_price * 0.98),  # Slightly below MSP
                        'distance_km': 50 + i * 25,
                        'contact_phone': f'+91-{8000000000 + i}',
                        'payment_terms': "Immediate payment",
                        'quality_requirements': "Standard grade",
                        'confidence': 0.75
                    })
            
            return private_buyers
            
        except Exception as e:
            logger.error("Error finding private buyers", error=str(e))
            return []
    
    async def _create_procurement_suggestion(
        self, 
        violation: MSPViolation, 
        center: ProcurementCenter
    ) -> Optional[AlternativeSuggestion]:
        """Create suggestion for government procurement center"""
        try:
            # Use pre-calculated distance if available, otherwise calculate
            distance_km = getattr(center, 'estimated_distance', None)
            if distance_km is None:
                distance_km = await self._calculate_distance(
                    violation.district, violation.state,
                    center.district, center.state
                )
            
            # Estimate transportation cost (₹2 per km per quintal)
            transport_cost = distance_km * 2.0
            
            # Net benefit (MSP - transport cost - current market price)
            net_benefit = violation.msp_price - transport_cost - violation.market_price
            
            # Generate comprehensive directions and contact information
            directions = self._generate_procurement_center_directions(center, distance_km, violation)
            
            # Estimate travel time (assuming 40 km/hr average speed)
            travel_time_hours = distance_km / 40
            travel_time_str = f"{int(travel_time_hours)}h {int((travel_time_hours % 1) * 60)}m"
            
            # Determine priority reason based on center type
            if center.center_type == 'FCI':
                reason = "Food Corporation of India center - guaranteed MSP payment"
            elif center.center_type == 'State Agency':
                reason = "State government procurement center offering MSP"
            elif center.center_type == 'Cooperative':
                reason = "Cooperative society procurement center with MSP rates"
            else:
                reason = "Government procurement center offering MSP"
            
            suggestion = AlternativeSuggestion(
                commodity=violation.commodity,
                original_location=f"{violation.district}, {violation.state}",
                suggested_center_id=center.id,
                suggested_center_name=center.name,
                suggested_location=f"{center.district}, {center.state}",
                distance_km=distance_km,
                price_offered=violation.msp_price,  # Government pays MSP
                price_advantage=violation.msp_price - violation.market_price,
                transportation_cost=transport_cost,
                net_benefit=net_benefit,
                contact_info={
                    'phone': center.phone_number,
                    'email': center.email,
                    'address': center.address,
                    'contact_person': center.contact_person,
                    'center_type': center.center_type,
                    'operating_hours': center.operating_hours,
                    'storage_capacity': center.storage_capacity,
                    'current_stock': center.current_stock
                },
                directions=directions,
                estimated_travel_time=travel_time_str,
                suggestion_reason=reason,
                confidence_score=0.95  # High confidence for government centers
            )
            
            return suggestion
            
        except Exception as e:
            logger.error("Error creating procurement suggestion", error=str(e))
            return None
    
    def _generate_procurement_center_directions(self, center: ProcurementCenter, distance_km: float, violation: MSPViolation) -> str:
        """Generate detailed directions for procurement center"""
        directions = f"📍 {center.name} ({center.center_type})\n"
        directions += f"📧 Address: {center.address}\n"
        
        if center.phone_number:
            directions += f"📞 Phone: {center.phone_number}\n"
        
        if center.contact_person:
            directions += f"👤 Contact Person: {center.contact_person}\n"
        
        if center.operating_hours:
            directions += f"🕒 Operating Hours: {center.operating_hours}\n"
        else:
            directions += f"🕒 Operating Hours: 9:00 AM - 5:00 PM (typical)\n"
        
        directions += f"🚛 Distance: {distance_km:.1f} km\n"
        
        if center.storage_capacity:
            directions += f"🏪 Storage Capacity: {center.storage_capacity:,.0f} quintals\n"
        
        # Add commodity-specific information
        if center.commodities_accepted:
            directions += f"🌾 Accepts: {', '.join(center.commodities_accepted)}\n"
        
        directions += f"💰 Guaranteed MSP Payment: ₹{violation.msp_price:.2f}/quintal\n"
        directions += f"⚠️ Required: Valid farmer ID, land records, quality certificate"
        
        return directions
    
    async def _create_mandi_suggestion(
        self, 
        violation: MSPViolation, 
        mandi_data: Dict[str, Any]
    ) -> Optional[AlternativeSuggestion]:
        """Create suggestion for alternative mandi"""
        try:
            distance_km = mandi_data.get('distance_km', 0)
            better_price = mandi_data.get('price', violation.market_price)
            
            # Estimate transportation cost
            transport_cost = distance_km * 2.0
            
            # Net benefit
            net_benefit = better_price - transport_cost - violation.market_price
            
            # Only suggest if there's actual benefit
            if net_benefit <= 0:
                return None
            
            suggestion = AlternativeSuggestion(
                commodity=violation.commodity,
                original_location=f"{violation.district}, {violation.state}",
                suggested_center_id=mandi_data.get('mandi_id', ''),
                suggested_center_name=mandi_data.get('mandi_name', ''),
                suggested_location=mandi_data.get('location', ''),
                distance_km=distance_km,
                price_offered=better_price,
                price_advantage=better_price - violation.market_price,
                transportation_cost=transport_cost,
                net_benefit=net_benefit,
                suggestion_reason="Better market price available",
                confidence_score=mandi_data.get('confidence', 0.8)
            )
            
            return suggestion
            
        except Exception as e:
            logger.error("Error creating mandi suggestion", error=str(e))
            return None
    
    async def _create_fpo_suggestion(
        self, 
        violation: MSPViolation, 
        fpo_data: Dict[str, Any]
    ) -> Optional[AlternativeSuggestion]:
        """Create suggestion for FPO center"""
        try:
            distance_km = fpo_data.get('distance_km', 0)
            fpo_price = fpo_data.get('price_offered', violation.market_price)
            
            # Estimate transportation cost (lower for FPOs due to collective transport)
            transport_cost = distance_km * 1.5
            
            # Net benefit
            net_benefit = fpo_price - transport_cost - violation.market_price
            
            # FPOs provide additional benefits beyond price
            if net_benefit <= 0:
                net_benefit = 50  # Minimum benefit for FPO membership advantages
            
            # Generate directions
            directions = f"Contact {fpo_data.get('name')} at {fpo_data.get('contact_phone')}. " \
                        f"FPO has {fpo_data.get('member_count', 0)} members and storage capacity of " \
                        f"{fpo_data.get('storage_capacity', 0)} quintals."
            
            suggestion = AlternativeSuggestion(
                commodity=violation.commodity,
                original_location=f"{violation.district}, {violation.state}",
                suggested_center_id=fpo_data.get('id', ''),
                suggested_center_name=fpo_data.get('name', ''),
                suggested_location=fpo_data.get('location', ''),
                distance_km=distance_km,
                price_offered=fpo_price,
                price_advantage=fpo_price - violation.market_price,
                transportation_cost=transport_cost,
                net_benefit=net_benefit,
                contact_info={
                    'phone': fpo_data.get('contact_phone'),
                    'member_count': fpo_data.get('member_count'),
                    'storage_capacity': fpo_data.get('storage_capacity')
                },
                directions=directions,
                suggestion_reason="Farmer Producer Organization with collective benefits",
                confidence_score=fpo_data.get('confidence', 0.85)
            )
            
            return suggestion
            
        except Exception as e:
            logger.error("Error creating FPO suggestion", error=str(e))
            return None
    
    async def _create_private_buyer_suggestion(
        self, 
        violation: MSPViolation, 
        buyer_data: Dict[str, Any]
    ) -> Optional[AlternativeSuggestion]:
        """Create suggestion for private buyer"""
        try:
            distance_km = buyer_data.get('distance_km', 0)
            buyer_price = buyer_data.get('price_offered', violation.market_price)
            
            # Estimate transportation cost
            transport_cost = distance_km * 2.0
            
            # Net benefit
            net_benefit = buyer_price - transport_cost - violation.market_price
            
            # Only suggest if there's actual benefit
            if net_benefit <= 0:
                return None
            
            # Generate directions with buyer details
            directions = f"Contact {buyer_data.get('name')} at {buyer_data.get('contact_phone')}. " \
                        f"Payment terms: {buyer_data.get('payment_terms', 'Standard')}. " \
                        f"Quality requirements: {buyer_data.get('quality_requirements', 'As per standards')}."
            
            suggestion = AlternativeSuggestion(
                commodity=violation.commodity,
                original_location=f"{violation.district}, {violation.state}",
                suggested_center_id=buyer_data.get('id', ''),
                suggested_center_name=buyer_data.get('name', ''),
                suggested_location=buyer_data.get('location', ''),
                distance_km=distance_km,
                price_offered=buyer_price,
                price_advantage=buyer_price - violation.market_price,
                transportation_cost=transport_cost,
                net_benefit=net_benefit,
                contact_info={
                    'phone': buyer_data.get('contact_phone'),
                    'buyer_type': buyer_data.get('buyer_type'),
                    'payment_terms': buyer_data.get('payment_terms'),
                    'quality_requirements': buyer_data.get('quality_requirements')
                },
                directions=directions,
                suggestion_reason=f"Private {buyer_data.get('buyer_type', 'buyer')} offering competitive price",
                confidence_score=buyer_data.get('confidence', 0.75)
            )
            
            return suggestion
            
        except Exception as e:
            logger.error("Error creating private buyer suggestion", error=str(e))
            return None
    
    async def _calculate_distance(
        self, 
        from_district: str, from_state: str,
        to_district: str, to_state: str
    ) -> float:
        """Calculate approximate distance between locations"""
        # Simplified distance calculation
        # In production, would use actual geolocation APIs
        
        if from_state == to_state:
            if from_district == to_district:
                return 10.0  # Same district
            else:
                return 150.0  # Different district, same state
        else:
            # Different states - estimate based on state proximity
            state_distances = {
                ('Punjab', 'Haryana'): 200,
                ('Punjab', 'Rajasthan'): 400,
                ('Haryana', 'Uttar Pradesh'): 300,
                ('Maharashtra', 'Gujarat'): 350,
                ('Karnataka', 'Tamil Nadu'): 400,
                ('Andhra Pradesh', 'Telangana'): 250,
            }
            
            key1 = (from_state, to_state)
            key2 = (to_state, from_state)
            
            return state_distances.get(key1, state_distances.get(key2, 500.0))
    
    async def _create_alternative_alert(
        self, 
        violation: MSPViolation, 
        alternatives: List[AlternativeSuggestion]
    ) -> Optional[MSPAlert]:
        """Create alert with alternative suggestions"""
        try:
            if not alternatives:
                return None
            
            # Categorize alternatives
            govt_centers = [alt for alt in alternatives if 'government' in alt.suggestion_reason.lower() or 'msp' in alt.suggestion_reason.lower()]
            fpo_centers = [alt for alt in alternatives if 'fpo' in alt.suggestion_reason.lower() or 'producer' in alt.suggestion_reason.lower()]
            private_buyers = [alt for alt in alternatives if 'private' in alt.suggestion_reason.lower() or 'buyer' in alt.suggestion_reason.lower()]
            other_mandis = [alt for alt in alternatives if alt not in govt_centers + fpo_centers + private_buyers]
            
            # Get best alternative overall
            best_alt = max(alternatives, key=lambda x: x.net_benefit or 0)
            
            # Create comprehensive title and message
            title = f"💡 {len(alternatives)} Better Options Found - {violation.commodity}"
            
            message = f"🎯 BETTER ALTERNATIVES AVAILABLE 🎯\n\n"
            
            # Add government centers first (highest priority)
            if govt_centers:
                message += f"🏛️ GOVERNMENT CENTERS ({len(govt_centers)}):\n"
                for i, center in enumerate(govt_centers[:2], 1):  # Show top 2
                    message += f"{i}. {center.suggested_center_name}\n"
                    message += f"   💰 Price: ₹{center.price_offered:.2f} (MSP guaranteed)\n"
                    message += f"   📍 Distance: {center.distance_km:.0f}km\n"
                    message += f"   💵 Net benefit: ₹{center.net_benefit:.2f}/quintal\n\n"
            
            # Add FPO centers
            if fpo_centers:
                message += f"🤝 FARMER ORGANIZATIONS ({len(fpo_centers)}):\n"
                for i, fpo in enumerate(fpo_centers[:2], 1):  # Show top 2
                    message += f"{i}. {fpo.suggested_center_name}\n"
                    message += f"   💰 Price: ₹{fpo.price_offered:.2f}\n"
                    message += f"   📍 Distance: {fpo.distance_km:.0f}km\n"
                    message += f"   💵 Net benefit: ₹{fpo.net_benefit:.2f}/quintal\n\n"
            
            # Add private buyers
            if private_buyers:
                message += f"🏢 PRIVATE BUYERS ({len(private_buyers)}):\n"
                for i, buyer in enumerate(private_buyers[:1], 1):  # Show top 1
                    message += f"{i}. {buyer.suggested_center_name}\n"
                    message += f"   💰 Price: ₹{buyer.price_offered:.2f}\n"
                    message += f"   📍 Distance: {buyer.distance_km:.0f}km\n"
                    message += f"   💵 Net benefit: ₹{buyer.net_benefit:.2f}/quintal\n\n"
            
            # Add other mandis
            if other_mandis:
                message += f"🏪 OTHER MARKETS ({len(other_mandis)}):\n"
                for i, mandi in enumerate(other_mandis[:1], 1):  # Show top 1
                    message += f"{i}. {mandi.suggested_center_name}\n"
                    message += f"   💰 Price: ₹{mandi.price_offered:.2f}\n"
                    message += f"   📍 Distance: {mandi.distance_km:.0f}km\n"
                    message += f"   💵 Net benefit: ₹{mandi.net_benefit:.2f}/quintal\n\n"
            
            # Add best option summary
            message += f"🏆 BEST OPTION: {best_alt.suggested_center_name}\n"
            message += f"💰 Offering: ₹{best_alt.price_offered:.2f}/quintal\n"
            message += f"💵 Total benefit: ₹{best_alt.net_benefit:.2f}/quintal\n"
            message += f"📍 Distance: {best_alt.distance_km:.0f}km"
            
            if best_alt.estimated_travel_time:
                message += f" ({best_alt.estimated_travel_time})"
            
            # Generate comprehensive suggested actions
            suggested_actions = [
                f"🏆 PRIORITY: Contact {best_alt.suggested_center_name}",
                "📋 PREPARE: Required documents (farmer ID, land records)",
                "🚛 ARRANGE: Transportation and logistics",
                "📞 CALL: Verify current prices and availability",
                "⏰ ACT FAST: Prices and availability may change",
                "📊 COMPARE: Calculate total costs including transport"
            ]
            
            # Add specific actions based on best alternative type
            if govt_centers and best_alt in govt_centers:
                suggested_actions.insert(1, "🏛️ GOVERNMENT CENTER: MSP guaranteed, bring quality certificate")
            elif fpo_centers and best_alt in fpo_centers:
                suggested_actions.insert(1, "🤝 FPO CENTER: Consider membership benefits")
            elif private_buyers and best_alt in private_buyers:
                suggested_actions.insert(1, "🏢 PRIVATE BUYER: Confirm payment terms and quality requirements")
            
            alternative_centers = [alt.suggested_center_id for alt in alternatives]
            
            alert = MSPAlert(
                violation_id=violation.id,
                title=title,
                message=message,
                severity=AlertSeverity.MEDIUM,  # Alternative alerts are informational
                commodity=violation.commodity,
                location=f"{violation.district}, {violation.state}",
                suggested_actions=suggested_actions,
                alternative_centers=alternative_centers
            )
            
            # Store alternative suggestions
            for alt in alternatives:
                await store_alternative_suggestion(alt)
            
            return alert
            
        except Exception as e:
            logger.error("Error creating alternative alert", error=str(e))
            return None
    
    async def _send_notification(self, alert: MSPAlert):
        """Send notification through various channels"""
        try:
            # In production, this would integrate with:
            # - SMS gateway for text messages
            # - Push notification service for mobile apps
            # - Email service for email notifications
            # - Voice calling service for urgent alerts
            
            logger.info(
                "Sending MSP alert notification",
                alert_id=alert.id,
                severity=alert.severity.value,
                commodity=alert.commodity,
                location=alert.location
            )
            
            # Simulate notification sending
            if alert.severity == AlertSeverity.CRITICAL:
                # Send via all channels for critical alerts
                await self._send_sms_notification(alert)
                await self._send_push_notification(alert)
                await self._send_voice_notification(alert)
            elif alert.severity == AlertSeverity.HIGH:
                # Send via SMS and push for high severity
                await self._send_sms_notification(alert)
                await self._send_push_notification(alert)
            else:
                # Send via push notification for medium/low severity
                await self._send_push_notification(alert)
            
        except Exception as e:
            logger.error("Error sending notification", alert_id=alert.id, error=str(e))
    
    async def _send_sms_notification(self, alert: MSPAlert):
        """Send SMS notification"""
        # Simulate SMS sending
        logger.info("SMS notification sent", alert_id=alert.id)
    
    async def _send_push_notification(self, alert: MSPAlert):
        """Send push notification"""
        # Simulate push notification
        logger.info("Push notification sent", alert_id=alert.id)
    
    async def _send_voice_notification(self, alert: MSPAlert):
        """Send voice notification for critical alerts"""
        # Simulate voice call
        logger.info("Voice notification sent", alert_id=alert.id)
    
    async def get_alerts_for_farmer(self, farmer_id: str, unread_only: bool = False) -> List[MSPAlert]:
        """Get alerts for a specific farmer"""
        # This would query the database for farmer-specific alerts
        # For now, return empty list
        return []
    
    async def mark_alert_read(self, alert_id: str, farmer_id: str) -> bool:
        """Mark an alert as read"""
        try:
            # Update alert in database
            # Implementation would depend on database layer
            logger.info("Alert marked as read", alert_id=alert_id, farmer_id=farmer_id)
            return True
        except Exception as e:
            logger.error("Error marking alert as read", alert_id=alert_id, error=str(e))
            return False
    
    async def acknowledge_alert(self, alert_id: str, farmer_id: str) -> bool:
        """Mark an alert as acknowledged"""
        try:
            # Update alert in database
            logger.info("Alert acknowledged", alert_id=alert_id, farmer_id=farmer_id)
            return True
        except Exception as e:
            logger.error("Error acknowledging alert", alert_id=alert_id, error=str(e))
            return False