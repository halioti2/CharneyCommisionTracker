"""
Unit tests for Pydantic data models.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from pydantic import ValidationError

from src.models.commission import CommissionData, CommissionSplitData


class TestCommissionSplitData:
    """Tests for CommissionSplitData model"""
    
    def test_valid_split(self):
        """Test creating a valid commission split"""
        split = CommissionSplitData(
            agent_name="John Smith",
            agent_email="john@example.com",
            percentage=0.60,
            amount=Decimal("16200.00"),
            role="listing_agent"
        )
        
        assert split.agent_name == "John Smith"
        assert split.percentage == 0.60
        assert split.amount == Decimal("16200.00")
    
    def test_invalid_percentage(self):
        """Test that invalid percentages are rejected"""
        with pytest.raises(ValidationError):
            CommissionSplitData(
                agent_name="John Smith",
                percentage=1.5,  # Invalid: > 1.0
                amount=Decimal("16200.00")
            )
    
    def test_negative_amount(self):
        """Test that negative amounts are rejected"""
        with pytest.raises(ValidationError):
            CommissionSplitData(
                agent_name="John Smith",
                percentage=0.60,
                amount=Decimal("-100.00")  # Invalid: negative
            )
    
    def test_amount_rounding(self):
        """Test that amounts are rounded to 2 decimal places"""
        split = CommissionSplitData(
            agent_name="John Smith",
            percentage=0.60,
            amount=Decimal("16200.999")
        )
        
        assert split.amount == Decimal("16201.00")


class TestCommissionData:
    """Tests for CommissionData model"""
    
    def test_valid_commission(self):
        """Test creating a valid commission"""
        commission = CommissionData(
            transaction_id="TXN-2024-001",
            property_address="123 Main St",
            sale_amount=Decimal("450000.00"),
            commission_rate=0.06,
            total_commission=Decimal("27000.00"),
            closing_date=datetime(2024, 1, 15),
            email_source="test@example.com",
            splits=[
                CommissionSplitData(
                    agent_name="John Smith",
                    percentage=0.60,
                    amount=Decimal("16200.00")
                ),
                CommissionSplitData(
                    agent_name="Jane Doe",
                    percentage=0.40,
                    amount=Decimal("10800.00")
                )
            ]
        )
        
        assert commission.transaction_id == "TXN-2024-001"
        assert len(commission.splits) == 2
        assert commission.total_commission == Decimal("27000.00")
    
    def test_splits_percentage_validation(self):
        """Test that split percentages must sum to 100%"""
        with pytest.raises(ValidationError) as exc_info:
            CommissionData(
                transaction_id="TXN-2024-001",
                property_address="123 Main St",
                sale_amount=Decimal("450000.00"),
                commission_rate=0.06,
                total_commission=Decimal("27000.00"),
                closing_date=datetime(2024, 1, 15),
                email_source="test@example.com",
                splits=[
                    CommissionSplitData(
                        agent_name="John Smith",
                        percentage=0.60,
                        amount=Decimal("16200.00")
                    ),
                    CommissionSplitData(
                        agent_name="Jane Doe",
                        percentage=0.30,  # Only 90% total
                        amount=Decimal("8100.00")
                    )
                ]
            )
        
        assert "must sum to 100%" in str(exc_info.value)
    
    def test_splits_amount_validation(self):
        """Test that split amounts must sum to total commission"""
        with pytest.raises(ValidationError) as exc_info:
            CommissionData(
                transaction_id="TXN-2024-001",
                property_address="123 Main St",
                sale_amount=Decimal("450000.00"),
                commission_rate=0.06,
                total_commission=Decimal("27000.00"),
                closing_date=datetime(2024, 1, 15),
                email_source="test@example.com",
                splits=[
                    CommissionSplitData(
                        agent_name="John Smith",
                        percentage=0.60,
                        amount=Decimal("16200.00")
                    ),
                    CommissionSplitData(
                        agent_name="Jane Doe",
                        percentage=0.40,
                        amount=Decimal("9000.00")  # Wrong amount
                    )
                ]
            )
        
        assert "must sum to total commission" in str(exc_info.value)
    
    def test_commission_calculation_validation(self):
        """Test that total commission matches sale_amount * rate"""
        with pytest.raises(ValidationError) as exc_info:
            CommissionData(
                transaction_id="TXN-2024-001",
                property_address="123 Main St",
                sale_amount=Decimal("450000.00"),
                commission_rate=0.06,
                total_commission=Decimal("30000.00"),  # Wrong: should be 27000
                closing_date=datetime(2024, 1, 15),
                email_source="test@example.com",
                splits=[]
            )
        
        assert "doesn't match sale_amount * rate" in str(exc_info.value)
    
    def test_empty_splits_allowed(self):
        """Test that commissions without splits are allowed"""
        commission = CommissionData(
            transaction_id="TXN-2024-001",
            property_address="123 Main St",
            sale_amount=Decimal("450000.00"),
            commission_rate=0.06,
            total_commission=Decimal("27000.00"),
            closing_date=datetime(2024, 1, 15),
            email_source="test@example.com",
            splits=[]
        )
        
        assert len(commission.splits) == 0
    
    def test_confidence_score_range(self):
        """Test that confidence score must be between 0 and 1"""
        with pytest.raises(ValidationError):
            CommissionData(
                transaction_id="TXN-2024-001",
                property_address="123 Main St",
                sale_amount=Decimal("450000.00"),
                commission_rate=0.06,
                total_commission=Decimal("27000.00"),
                closing_date=datetime(2024, 1, 15),
                email_source="test@example.com",
                confidence_score=1.5,  # Invalid: > 1.0
                splits=[]
            )
    
    def test_default_values(self):
        """Test that default values are set correctly"""
        commission = CommissionData(
            transaction_id="TXN-2024-001",
            property_address="123 Main St",
            sale_amount=Decimal("450000.00"),
            commission_rate=0.06,
            total_commission=Decimal("27000.00"),
            closing_date=datetime(2024, 1, 15),
            email_source="test@example.com"
        )
        
        assert commission.status == "pending"
        assert commission.confidence_score == 0.0
        assert commission.splits == []


class TestCommissionDataEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_very_large_sale_amount(self):
        """Test handling of very large sale amounts"""
        commission = CommissionData(
            transaction_id="TXN-2024-001",
            property_address="123 Main St",
            sale_amount=Decimal("99999999.99"),
            commission_rate=0.06,
            total_commission=Decimal("5999999.99"),
            closing_date=datetime(2024, 1, 15),
            email_source="test@example.com",
            splits=[]
        )
        
        assert commission.sale_amount == Decimal("99999999.99")
    
    def test_very_small_commission_rate(self):
        """Test handling of very small commission rates"""
        commission = CommissionData(
            transaction_id="TXN-2024-001",
            property_address="123 Main St",
            sale_amount=Decimal("450000.00"),
            commission_rate=0.01,  # 1%
            total_commission=Decimal("4500.00"),
            closing_date=datetime(2024, 1, 15),
            email_source="test@example.com",
            splits=[]
        )
        
        assert commission.commission_rate == 0.01
    
    def test_multiple_splits(self):
        """Test commission with many splits"""
        splits = [
            CommissionSplitData(
                agent_name=f"Agent {i}",
                percentage=0.25,
                amount=Decimal("6750.00")
            )
            for i in range(4)
        ]
        
        commission = CommissionData(
            transaction_id="TXN-2024-001",
            property_address="123 Main St",
            sale_amount=Decimal("450000.00"),
            commission_rate=0.06,
            total_commission=Decimal("27000.00"),
            closing_date=datetime(2024, 1, 15),
            email_source="test@example.com",
            splits=splits
        )
        
        assert len(commission.splits) == 4

