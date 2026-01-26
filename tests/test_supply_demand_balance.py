"""
Property-based tests for supply-demand balance calculation

**Feature: mandi-ear, Property 17: Supply-Demand Balance Calculation**
**Validates: Requirements 7.5**

Property 17: Supply-Demand Balance Calculation
*For any* commodity and region combination, the system should provide accurate supply-demand balance indicators
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime, timedelta
import asyncio
from typing import Dict, Any, List

# Import the system under test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services', 'anti-hoarding-service'))

from supply_demand_analyzer import SupplyDemandAnalyzer
from models import SupplyDemandBalance

class TestSupplyDemandBalanceCalculation:
    """Property-based tests for supply-demand balance calculation"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = SupplyDemandAnalyzer()
    
    @given(
        commodity=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        variety=st.one_of(st.none(), st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
        region=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        price_data_size=st.integers(min_value=1, max_value=50),
        inventory_data_size=st.integers(min_value=1, max_value=50),
        base_price=st.floats(min_value=100.0, max_value=5000.0),
        base_inventory=st.floats(min_value=10.0, max_value=10000.0),
        base_quantity=st.floats(min_value=1.0, max_value=1000.0)
    )
    @settings(max_examples=100, deadline=10000)
    def test_supply_demand_balance_calculation_completeness(
        self, 
        commodity: str, 
        variety: str, 
        region: str,
        price_data_size: int,
        inventory_data_size: int,
        base_price: float,
        base_inventory: float,
        base_quantity: float
    ):
        """
        **Validates: Requirements 7.5**
        
        Property: For any commodity and region combination with valid data,
        the system should provide complete supply-demand balance indicators
        """
        # Generate realistic test data
        price_data = self._generate_price_data(
            commodity, variety, region, price_data_size, base_price, base_quantity
        )
        inventory_data = self._generate_inventory_data(
            commodity, variety, region, inventory_data_size, base_inventory
        )
        
        # Calculate supply-demand balance
        balance = asyncio.run(
            self.analyzer.calculate_supply_demand_balance(
                commodity=commodity,
                variety=variety,
                region=region,
                price_data=price_data,
                inventory_data=inventory_data
            )
        )
        
        # Property: Balance object should be complete and valid
        assert isinstance(balance, SupplyDemandBalance)
        assert balance.commodity == commodity
        assert balance.variety == variety
        assert balance.region == region
        
        # Property: All required numeric fields should be non-negative
        assert balance.total_supply >= 0
        assert balance.available_supply >= 0
        assert balance.reserved_supply >= 0
        assert balance.estimated_demand >= 0
        assert balance.actual_consumption >= 0
        
        # Property: Supply-demand ratio should be calculated correctly
        if balance.estimated_demand > 0:
            expected_ratio = balance.available_supply / balance.estimated_demand
            assert abs(balance.supply_demand_ratio - expected_ratio) < 0.001
        else:
            assert balance.supply_demand_ratio == 0.0
        
        # Property: Balance score should be in valid range [-1, 1]
        assert -1.0 <= balance.balance_score <= 1.0
        
        # Property: Balance status should be valid
        valid_statuses = ["surplus", "balanced", "deficit", "critical_shortage", "unknown"]
        assert balance.balance_status in valid_statuses
        
        # Property: Confidence score should be in valid range [0, 1]
        assert 0.0 <= balance.confidence_score <= 1.0
        
        # Property: Data freshness should be non-negative
        assert balance.data_freshness_hours >= 0.0
        
        # Property: Trend indicators should be valid
        valid_trends = ["increasing", "decreasing", "stable"]
        assert balance.supply_trend in valid_trends
        assert balance.demand_trend in valid_trends
        
        # Property: Price pressure should be valid
        valid_pressures = ["upward", "downward", "neutral"]
        assert balance.price_pressure_indicator in valid_pressures
        
        # Property: Volatility risk should be valid
        valid_risks = ["low", "medium", "high"]
        assert balance.volatility_risk in valid_risks
    
    @given(
        commodity=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        region=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        supply_level=st.floats(min_value=100.0, max_value=10000.0),
        demand_level=st.floats(min_value=100.0, max_value=10000.0)
    )
    @settings(max_examples=100, deadline=10000)
    def test_supply_demand_ratio_consistency(
        self,
        commodity: str,
        region: str,
        supply_level: float,
        demand_level: float
    ):
        """
        **Validates: Requirements 7.5**
        
        Property: Supply-demand ratio should be mathematically consistent
        and balance status should align with the ratio
        """
        # Create test data with controlled supply and demand levels
        price_data = self._generate_controlled_price_data(commodity, region, demand_level)
        inventory_data = self._generate_controlled_inventory_data(commodity, region, supply_level)
        
        balance = asyncio.run(
            self.analyzer.calculate_supply_demand_balance(
                commodity=commodity,
                variety=None,
                region=region,
                price_data=price_data,
                inventory_data=inventory_data
            )
        )
        
        # Property: Ratio calculation should be mathematically correct
        if balance.estimated_demand > 0:
            expected_ratio = balance.available_supply / balance.estimated_demand
            assert abs(balance.supply_demand_ratio - expected_ratio) < 0.01
            
            # Property: Balance status should align with ratio
            if expected_ratio >= 1.5:
                assert balance.balance_status == "surplus"
                assert balance.balance_score > 0
            elif expected_ratio >= 0.9:
                assert balance.balance_status == "balanced"
                assert -0.2 <= balance.balance_score <= 0.2
            elif expected_ratio >= 0.6:
                assert balance.balance_status == "deficit"
                assert balance.balance_score < 0
            else:
                assert balance.balance_status == "critical_shortage"
                assert balance.balance_score < -0.5
    
    @given(
        commodity=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        region=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        data_points=st.integers(min_value=5, max_value=100)
    )
    @settings(max_examples=50, deadline=10000)
    def test_confidence_score_correlation(
        self,
        commodity: str,
        region: str,
        data_points: int
    ):
        """
        **Validates: Requirements 7.5**
        
        Property: Confidence score should correlate with data quality and quantity
        """
        # Generate data with varying quality
        price_data = self._generate_price_data(commodity, None, region, data_points, 2000.0, 50.0)
        inventory_data = self._generate_inventory_data(commodity, None, region, data_points, 1000.0)
        
        balance = asyncio.run(
            self.analyzer.calculate_supply_demand_balance(
                commodity=commodity,
                variety=None,
                region=region,
                price_data=price_data,
                inventory_data=inventory_data
            )
        )
        
        # Property: More data points should generally lead to higher confidence
        # (with some tolerance for other factors)
        total_data_points = len(price_data) + len(inventory_data)
        if total_data_points >= 50:
            assert balance.confidence_score >= 0.3  # Should have reasonable confidence
        
        # Property: Confidence should never exceed 1.0 or be below 0.0
        assert 0.0 <= balance.confidence_score <= 1.0
        
        # Property: Fresh data should contribute to higher confidence
        assert balance.data_freshness_hours >= 0.0
    
    @given(
        commodity=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        regions=st.lists(
            st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
            min_size=1, max_size=5, unique=True
        )
    )
    @settings(max_examples=50, deadline=15000)
    def test_regional_consistency(
        self,
        commodity: str,
        regions: List[str]
    ):
        """
        **Validates: Requirements 7.5**
        
        Property: Balance calculations should be consistent across different regions
        for the same commodity
        """
        balances = []
        
        for region in regions:
            price_data = self._generate_price_data(commodity, None, region, 20, 2000.0, 50.0)
            inventory_data = self._generate_inventory_data(commodity, None, region, 20, 1000.0)
            
            balance = asyncio.run(
                self.analyzer.calculate_supply_demand_balance(
                    commodity=commodity,
                    variety=None,
                    region=region,
                    price_data=price_data,
                    inventory_data=inventory_data
                )
            )
            balances.append(balance)
        
        # Property: All balances should have the same commodity
        for balance in balances:
            assert balance.commodity == commodity
        
        # Property: Each balance should have valid indicators
        for balance in balances:
            assert balance.balance_status in ["surplus", "balanced", "deficit", "critical_shortage", "unknown"]
            assert -1.0 <= balance.balance_score <= 1.0
            assert 0.0 <= balance.confidence_score <= 1.0
        
        # Property: Regional differences should be reflected in different regions
        if len(balances) > 1:
            regions_set = set(balance.region for balance in balances)
            assert len(regions_set) == len(balances)  # Each balance should have unique region
    
    def _generate_price_data(
        self, 
        commodity: str, 
        variety: str, 
        region: str, 
        size: int, 
        base_price: float, 
        base_quantity: float
    ) -> List[Dict[str, Any]]:
        """Generate realistic price data for testing"""
        price_data = []
        current_time = datetime.utcnow()
        
        for i in range(size):
            # Add some realistic variation
            price_variation = 1.0 + (i % 10 - 5) * 0.05  # ±25% variation
            quantity_variation = 1.0 + (i % 8 - 4) * 0.1  # ±40% variation
            
            price_data.append({
                "commodity": commodity,
                "variety": variety,
                "price": base_price * price_variation,
                "quantity": base_quantity * quantity_variation,
                "mandi_id": f"mandi_{i % 5 + 1}",
                "mandi_name": f"Test Mandi {i % 5 + 1}",
                "district": f"District_{region}",
                "state": region,
                "timestamp": current_time - timedelta(hours=i),
                "confidence": 0.8 + (i % 3) * 0.05
            })
        
        return price_data
    
    def _generate_inventory_data(
        self, 
        commodity: str, 
        variety: str, 
        region: str, 
        size: int, 
        base_inventory: float
    ) -> List[Dict[str, Any]]:
        """Generate realistic inventory data for testing"""
        inventory_data = []
        current_time = datetime.utcnow()
        
        for i in range(size):
            # Add some realistic variation
            inventory_variation = 1.0 + (i % 12 - 6) * 0.08  # ±48% variation
            
            inventory_data.append({
                "commodity": commodity,
                "variety": variety,
                "inventory_level": base_inventory * inventory_variation,
                "mandi_id": f"mandi_{i % 5 + 1}",
                "mandi_name": f"Test Mandi {i % 5 + 1}",
                "district": f"District_{region}",
                "state": region,
                "timestamp": current_time - timedelta(hours=i * 2),
                "storage_capacity": base_inventory * inventory_variation * 1.5
            })
        
        return inventory_data
    
    def _generate_controlled_price_data(
        self, 
        commodity: str, 
        region: str, 
        demand_level: float
    ) -> List[Dict[str, Any]]:
        """Generate price data with controlled demand level"""
        return [{
            "commodity": commodity,
            "variety": None,
            "price": 2000.0,
            "quantity": demand_level / 30,  # Monthly demand spread over days
            "mandi_id": "test_mandi",
            "mandi_name": "Test Mandi",
            "district": f"District_{region}",
            "state": region,
            "timestamp": datetime.utcnow() - timedelta(hours=i),
            "confidence": 0.9
        } for i in range(10)]
    
    def _generate_controlled_inventory_data(
        self, 
        commodity: str, 
        region: str, 
        supply_level: float
    ) -> List[Dict[str, Any]]:
        """Generate inventory data with controlled supply level"""
        return [{
            "commodity": commodity,
            "variety": None,
            "inventory_level": supply_level / 5,  # Distributed across mandis
            "mandi_id": f"test_mandi_{i}",
            "mandi_name": f"Test Mandi {i}",
            "district": f"District_{region}",
            "state": region,
            "timestamp": datetime.utcnow() - timedelta(hours=i * 2),
            "storage_capacity": supply_level / 5 * 1.5
        } for i in range(5)]

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])