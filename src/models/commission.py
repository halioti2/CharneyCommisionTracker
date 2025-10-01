"""
Pydantic models for data validation and serialization.

These models define the structure and validation rules for commission data
as it flows through the system (from email parsing to database storage).
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


class CommissionSplitData(BaseModel):
    """
    Data model for a single commission split.
    
    Validates that split data is properly formatted and within acceptable ranges.
    """
    agent_name: str = Field(..., min_length=1, max_length=255, description="Full name of the agent")
    agent_email: Optional[EmailStr] = Field(None, description="Agent's email address")
    agent_id: Optional[str] = Field(None, max_length=100, description="Internal agent identifier")
    percentage: float = Field(..., ge=0.0, le=1.0, description="Split percentage as decimal (0.0-1.0)")
    amount: Decimal = Field(..., ge=0, description="Dollar amount of the split")
    role: Optional[str] = Field(None, max_length=100, description="Agent role (listing, buyer, referral)")
    notes: Optional[str] = Field(None, description="Additional notes about this split")
    
    @validator('amount')
    def validate_amount(cls, v):
        """Ensure amount has at most 2 decimal places"""
        if v is not None:
            return round(v, 2)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_name": "John Smith",
                "agent_email": "john.smith@realty.com",
                "percentage": 0.60,
                "amount": 16200.00,
                "role": "listing_agent"
            }
        }


class CommissionData(BaseModel):
    """
    Complete commission transaction data model.
    
    This is the primary data structure used throughout the application.
    It validates all commission data extracted from emails before database storage.
    """
    transaction_id: str = Field(..., min_length=1, max_length=100, description="Unique transaction identifier")
    property_address: str = Field(..., min_length=1, max_length=500, description="Property address")
    sale_amount: Decimal = Field(..., gt=0, description="Sale price of the property")
    commission_rate: float = Field(..., ge=0.0, le=1.0, description="Commission rate as decimal")
    total_commission: Decimal = Field(..., ge=0, description="Total commission amount")
    closing_date: datetime = Field(..., description="Transaction closing date")
    email_source: str = Field(..., min_length=1, max_length=255, description="Source email address")
    email_subject: Optional[str] = Field(None, max_length=500, description="Email subject line")
    raw_email_content: Optional[str] = Field(None, description="Full email content for audit trail")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="AI parsing confidence score")
    status: str = Field(default="pending", max_length=50, description="Transaction status")
    notes: Optional[str] = Field(None, description="Additional notes")
    splits: List[CommissionSplitData] = Field(default_factory=list, description="Commission splits")
    
    @validator('sale_amount', 'total_commission')
    def validate_currency(cls, v):
        """Ensure currency values have at most 2 decimal places"""
        if v is not None:
            return round(v, 2)
        return v
    
    @validator('splits')
    def validate_splits_sum(cls, v, values):
        """Validate that split percentages sum to approximately 100%"""
        if v and len(v) > 0:
            total_percentage = sum(split.percentage for split in v)
            # Allow for small floating point errors
            if not (0.99 <= total_percentage <= 1.01):
                raise ValueError(f"Split percentages must sum to 100%, got {total_percentage * 100}%")
            
            # Validate that split amounts sum to total commission
            if 'total_commission' in values:
                total_split_amount = sum(split.amount for split in v)
                expected_total = values['total_commission']
                # Allow for rounding differences up to $1
                if abs(total_split_amount - expected_total) > 1:
                    raise ValueError(
                        f"Split amounts (${total_split_amount}) must sum to total commission (${expected_total})"
                    )
        return v
    
    @validator('total_commission')
    def validate_commission_calculation(cls, v, values):
        """Validate that total commission matches sale_amount * commission_rate"""
        if 'sale_amount' in values and 'commission_rate' in values:
            expected = values['sale_amount'] * Decimal(str(values['commission_rate']))
            expected = round(expected, 2)
            # Allow for small rounding differences
            if abs(v - expected) > Decimal('1.00'):
                raise ValueError(
                    f"Total commission (${v}) doesn't match sale_amount * rate (${expected})"
                )
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "TXN-2024-001",
                "property_address": "123 Main St, Anytown, CA 90210",
                "sale_amount": 450000.00,
                "commission_rate": 0.06,
                "total_commission": 27000.00,
                "closing_date": "2024-01-15T00:00:00",
                "email_source": "escrow@titlecompany.com",
                "email_subject": "Commission Statement - 123 Main St",
                "confidence_score": 0.95,
                "status": "pending",
                "splits": [
                    {
                        "agent_name": "John Smith",
                        "percentage": 0.60,
                        "amount": 16200.00,
                        "role": "listing_agent"
                    },
                    {
                        "agent_name": "Jane Doe",
                        "percentage": 0.40,
                        "amount": 10800.00,
                        "role": "buyer_agent"
                    }
                ]
            }
        }


class EmailParseRequest(BaseModel):
    """Request model for email parsing API endpoint"""
    email_content: str = Field(..., min_length=1, description="Raw email content to parse")
    email_subject: Optional[str] = Field(None, description="Email subject line")
    email_source: Optional[str] = Field(None, description="Sender email address")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email_content": "Commission Statement\nTransaction: TXN-2024-001\n...",
                "email_subject": "Commission Statement",
                "email_source": "escrow@titlecompany.com"
            }
        }


class CommissionQueryParams(BaseModel):
    """Query parameters for filtering commission records"""
    start_date: Optional[datetime] = Field(None, description="Filter by closing date (start)")
    end_date: Optional[datetime] = Field(None, description="Filter by closing date (end)")
    status: Optional[str] = Field(None, description="Filter by status")
    agent_name: Optional[str] = Field(None, description="Filter by agent name")
    min_amount: Optional[Decimal] = Field(None, ge=0, description="Minimum commission amount")
    max_amount: Optional[Decimal] = Field(None, ge=0, description="Maximum commission amount")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")
    
    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2024-12-31T23:59:59",
                "status": "verified",
                "limit": 50,
                "offset": 0
            }
        }

