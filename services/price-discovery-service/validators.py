"""
Data validation and quality checks for price discovery
"""

import re
import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import statistics

from models import ValidationResult, QualityGrade

logger = structlog.get_logger()

class PriceDataValidator:
    """Validates incoming price data for quality and consistency"""
    
    def __init__(self):
        self.commodity_patterns = self._load_commodity_patterns()
        self.price_ranges = self._load_price_ranges()
        self.state_districts = self._load_state_districts()
    
    def _load_commodity_patterns(self) -> Dict[str, List[str]]:
        """Load commodity name patterns for normalization"""
        return {
            "wheat": ["wheat", "gehun", "gahu", "triticum"],
            "rice": ["rice", "chawal", "dhan", "paddy", "oryza"],
            "maize": ["maize", "corn", "makka", "bhutta", "zea"],
            "onion": ["onion", "pyaz", "kanda", "vengayam"],
            "potato": ["potato", "aloo", "batata", "urulaikizhangu"],
            "tomato": ["tomato", "tamatar", "thakkali"],
            "cotton": ["cotton", "kapas", "ruyi", "patti"],
            "sugarcane": ["sugarcane", "ganna", "sherdi", "karumbu"]
        }
    
    def _load_price_ranges(self) -> Dict[str, Dict[str, float]]:
        """Load expected price ranges for commodities (per quintal)"""
        return {
            "wheat": {"min": 800, "max": 3000},
            "rice": {"min": 1000, "max": 4000},
            "maize": {"min": 600, "max": 2500},
            "onion": {"min": 500, "max": 8000},
            "potato": {"min": 300, "max": 3000},
            "tomato": {"min": 500, "max": 6000},
            "cotton": {"min": 3000, "max": 8000},
            "sugarcane": {"min": 200, "max": 500}
        }
    
    def _load_state_districts(self) -> Dict[str, List[str]]:
        """Load state-district mappings for location validation"""
        return {
            "Andhra Pradesh": ["Anantapur", "Chittoor", "East Godavari", "Guntur", "Krishna"],
            "Karnataka": ["Bangalore", "Mysore", "Hubli", "Belgaum", "Mangalore"],
            "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Salem", "Tiruchirappalli"],
            "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad"],
            "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar"],
            "Uttar Pradesh": ["Lucknow", "Kanpur", "Agra", "Varanasi", "Meerut"],
            "Punjab": ["Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda"],
            "Haryana": ["Gurgaon", "Faridabad", "Hisar", "Panipat", "Karnal"]
        }
    
    async def validate_price_data(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate a single price data record"""
        issues = []
        corrected_data = data.copy()
        confidence_score = 1.0
        
        # Validate required fields
        required_fields = ["commodity", "price", "timestamp"]
        for field in required_fields:
            if field not in data or data[field] is None:
                issues.append(f"Missing required field: {field}")
                confidence_score *= 0.5
        
        if issues:
            return ValidationResult(
                is_valid=False,
                confidence_score=confidence_score,
                issues=issues
            )
        
        # Validate and normalize commodity name
        commodity_result = self._validate_commodity(data["commodity"])
        if commodity_result["normalized"]:
            corrected_data["commodity"] = commodity_result["normalized"]
        if commodity_result["issues"]:
            issues.extend(commodity_result["issues"])
            confidence_score *= 0.9
        
        # Validate price
        price_result = self._validate_price(
            corrected_data["commodity"], 
            data["price"]
        )
        if price_result["issues"]:
            issues.extend(price_result["issues"])
            confidence_score *= price_result["confidence_factor"]
        
        # Validate timestamp
        timestamp_result = self._validate_timestamp(data["timestamp"])
        if timestamp_result["normalized"]:
            corrected_data["timestamp"] = timestamp_result["normalized"]
        if timestamp_result["issues"]:
            issues.extend(timestamp_result["issues"])
            confidence_score *= 0.8
        
        # Validate location if provided
        if "state" in data and "district" in data:
            location_result = self._validate_location(data["state"], data["district"])
            if location_result["issues"]:
                issues.extend(location_result["issues"])
                confidence_score *= 0.9
        
        # Validate quality grade
        if "quality" in data:
            quality_result = self._validate_quality(data["quality"])
            if quality_result["normalized"]:
                corrected_data["quality"] = quality_result["normalized"]
            if quality_result["issues"]:
                issues.extend(quality_result["issues"])
                confidence_score *= 0.95
        
        # Validate quantity if provided
        if "quantity" in data and data["quantity"] is not None:
            quantity_result = self._validate_quantity(data["quantity"])
            if quantity_result["issues"]:
                issues.extend(quantity_result["issues"])
                confidence_score *= 0.9
        
        # Overall validation
        is_valid = confidence_score >= 0.6 and len([i for i in issues if "Missing required field" in i]) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            confidence_score=max(0.0, confidence_score),
            issues=issues,
            corrected_data=corrected_data if corrected_data != data else None
        )
    
    def _validate_commodity(self, commodity: str) -> Dict[str, Any]:
        """Validate and normalize commodity name"""
        if not commodity or not isinstance(commodity, str):
            return {"normalized": None, "issues": ["Invalid commodity name"]}
        
        commodity_lower = commodity.lower().strip()
        
        # Try to find matching commodity
        for standard_name, patterns in self.commodity_patterns.items():
            for pattern in patterns:
                if pattern in commodity_lower or commodity_lower in pattern:
                    return {
                        "normalized": standard_name.title(),
                        "issues": [] if commodity.lower() == standard_name else [f"Commodity name normalized from '{commodity}' to '{standard_name.title()}'"]
                    }
        
        # If no match found, keep original but flag as unknown
        return {
            "normalized": commodity.title(),
            "issues": [f"Unknown commodity: {commodity}"]
        }
    
    def _validate_price(self, commodity: str, price: Any) -> Dict[str, Any]:
        """Validate price value"""
        issues = []
        confidence_factor = 1.0
        
        # Convert to float
        try:
            price_float = float(price)
        except (ValueError, TypeError):
            return {
                "issues": [f"Invalid price format: {price}"],
                "confidence_factor": 0.0
            }
        
        # Check if price is positive
        if price_float <= 0:
            issues.append(f"Price must be positive: {price_float}")
            confidence_factor = 0.0
        
        # Check against expected ranges
        commodity_lower = commodity.lower()
        if commodity_lower in self.price_ranges:
            price_range = self.price_ranges[commodity_lower]
            if price_float < price_range["min"]:
                issues.append(f"Price {price_float} below expected minimum {price_range['min']} for {commodity}")
                confidence_factor *= 0.7
            elif price_float > price_range["max"]:
                issues.append(f"Price {price_float} above expected maximum {price_range['max']} for {commodity}")
                confidence_factor *= 0.7
        
        return {
            "issues": issues,
            "confidence_factor": confidence_factor
        }
    
    def _validate_timestamp(self, timestamp: Any) -> Dict[str, Any]:
        """Validate and normalize timestamp"""
        issues = []
        normalized = None
        
        if isinstance(timestamp, datetime):
            normalized = timestamp
        elif isinstance(timestamp, str):
            try:
                # Try different timestamp formats
                formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%dT%H:%M:%SZ",
                    "%Y-%m-%d",
                    "%d/%m/%Y %H:%M:%S",
                    "%d-%m-%Y %H:%M:%S"
                ]
                
                for fmt in formats:
                    try:
                        normalized = datetime.strptime(timestamp, fmt)
                        break
                    except ValueError:
                        continue
                
                if not normalized:
                    issues.append(f"Unable to parse timestamp: {timestamp}")
            except Exception as e:
                issues.append(f"Timestamp parsing error: {str(e)}")
        else:
            issues.append(f"Invalid timestamp type: {type(timestamp)}")
        
        # Check if timestamp is reasonable (not too old or in future)
        if normalized:
            now = datetime.utcnow()
            if normalized > now + timedelta(hours=1):
                issues.append("Timestamp is in the future")
            elif normalized < now - timedelta(days=30):
                issues.append("Timestamp is more than 30 days old")
        
        return {
            "normalized": normalized,
            "issues": issues
        }
    
    def _validate_location(self, state: str, district: str) -> Dict[str, Any]:
        """Validate state and district combination"""
        issues = []
        
        if not state or not isinstance(state, str):
            issues.append("Invalid state")
            return {"issues": issues}
        
        if not district or not isinstance(district, str):
            issues.append("Invalid district")
            return {"issues": issues}
        
        # Check if state exists in our mapping
        state_clean = state.strip()
        if state_clean not in self.state_districts:
            # Try partial matching
            for known_state in self.state_districts.keys():
                if state_clean.lower() in known_state.lower() or known_state.lower() in state_clean.lower():
                    issues.append(f"State name normalized from '{state}' to '{known_state}'")
                    return {"issues": issues}
            
            issues.append(f"Unknown state: {state}")
        
        return {"issues": issues}
    
    def _validate_quality(self, quality: str) -> Dict[str, Any]:
        """Validate and normalize quality grade"""
        if not quality or not isinstance(quality, str):
            return {"normalized": "average", "issues": ["Invalid quality, defaulting to average"]}
        
        quality_lower = quality.lower().strip()
        quality_mapping = {
            "premium": ["premium", "super", "best", "top", "grade a", "a"],
            "good": ["good", "fine", "grade b", "b"],
            "average": ["average", "medium", "normal", "grade c", "c", "fair"],
            "below_average": ["below average", "poor", "low", "grade d", "d", "inferior"]
        }
        
        for standard_quality, patterns in quality_mapping.items():
            for pattern in patterns:
                if pattern in quality_lower or quality_lower in pattern:
                    return {
                        "normalized": standard_quality,
                        "issues": [] if quality_lower == standard_quality else [f"Quality normalized from '{quality}' to '{standard_quality}'"]
                    }
        
        return {
            "normalized": "average",
            "issues": [f"Unknown quality '{quality}', defaulting to average"]
        }
    
    def _validate_quantity(self, quantity: Any) -> Dict[str, Any]:
        """Validate quantity value"""
        issues = []
        
        try:
            quantity_float = float(quantity)
        except (ValueError, TypeError):
            return {"issues": [f"Invalid quantity format: {quantity}"]}
        
        if quantity_float <= 0:
            issues.append(f"Quantity must be positive: {quantity_float}")
        elif quantity_float > 10000:  # Unusually large quantity
            issues.append(f"Unusually large quantity: {quantity_float}")
        
        return {"issues": issues}
    
    async def validate_batch(self, data_batch: List[Dict[str, Any]]) -> List[ValidationResult]:
        """Validate a batch of price data records"""
        results = []
        for record in data_batch:
            result = await self.validate_price_data(record)
            results.append(result)
        
        return results