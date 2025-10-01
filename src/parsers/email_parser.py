"""
AI-powered email parser for commission data extraction.

This module uses OpenAI's GPT models to extract structured commission data
from unstructured email content. It handles various email formats and
provides confidence scoring for data quality monitoring.
"""

import json
import re
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
import openai
from openai import OpenAI

from ..models.commission import CommissionData, CommissionSplitData


class AIEmailParser:
    """
    AI-powered parser for extracting commission data from emails.
    
    Uses OpenAI's GPT models with carefully crafted prompts to extract
    structured data from various email formats (plain text, HTML, etc.).
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initialize the parser.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4 for best accuracy)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def parse_commission_email(
        self,
        email_content: str,
        email_subject: Optional[str] = None,
        email_source: Optional[str] = None
    ) -> CommissionData:
        """
        Parse commission data from email content.
        
        Args:
            email_content: Raw email content (text or HTML)
            email_subject: Email subject line (optional, helps with context)
            email_source: Sender email address (optional)
            
        Returns:
            CommissionData object with extracted and validated data
            
        Raises:
            ValueError: If parsing fails or data is invalid
            openai.OpenAIError: If API call fails
        """
        try:
            # Build the extraction prompt
            prompt = self._build_extraction_prompt(email_content, email_subject)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                response_format={"type": "json_object"}  # Ensure JSON response
            )
            
            # Extract and parse JSON response
            raw_response = response.choices[0].message.content
            extracted_data = json.loads(raw_response)
            
            # Add metadata
            if email_source and 'email_source' not in extracted_data:
                extracted_data['email_source'] = email_source
            
            if email_subject and 'email_subject' not in extracted_data:
                extracted_data['email_subject'] = email_subject
            
            extracted_data['raw_email_content'] = email_content
            
            # Convert to CommissionData (this validates the data)
            commission_data = self._convert_to_commission_data(extracted_data)
            
            return commission_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response as JSON: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse email: {e}")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt that defines the AI's role"""
        return """You are an expert data extraction assistant specializing in real estate commission statements.
Your task is to extract structured commission data from emails with high accuracy.

Key responsibilities:
1. Extract all relevant transaction details
2. Identify and parse commission splits among agents
3. Calculate percentages and amounts accurately
4. Assign a confidence score (0.0-1.0) based on data clarity
5. Return ONLY valid JSON - no additional text or explanations

If any required field is unclear or missing, use your best judgment and lower the confidence score accordingly."""
    
    def _build_extraction_prompt(self, email_content: str, email_subject: Optional[str] = None) -> str:
        """Build the extraction prompt with the email content"""
        
        subject_context = f"\n\nEmail Subject: {email_subject}" if email_subject else ""
        
        return f"""Extract commission data from this email and return it as JSON.{subject_context}

Email Content:
{email_content}

Required JSON format:
{{
    "transaction_id": "unique transaction identifier (e.g., TXN-2024-001, MLS#12345)",
    "property_address": "complete property address",
    "sale_amount": "sale price as number (e.g., 450000.00)",
    "commission_rate": "commission rate as decimal (e.g., 0.06 for 6%)",
    "total_commission": "total commission amount as number",
    "closing_date": "closing date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
    "email_source": "sender email address if available",
    "email_subject": "email subject if available",
    "confidence_score": "your confidence in the extraction (0.0-1.0)",
    "status": "pending",
    "notes": "any important notes or uncertainties",
    "splits": [
        {{
            "agent_name": "full agent name",
            "agent_email": "agent email if available",
            "percentage": "split percentage as decimal (e.g., 0.60 for 60%)",
            "amount": "split amount as number",
            "role": "agent role (listing_agent, buyer_agent, referral, etc.)"
        }}
    ]
}}

Important extraction rules:
1. Convert all percentages to decimals (6% → 0.06, 60% → 0.60)
2. Remove currency symbols and commas from amounts ($450,000 → 450000.00)
3. Ensure split percentages sum to 1.0 (100%)
4. Ensure split amounts sum to total_commission
5. Parse dates into ISO format
6. If transaction_id is not explicit, create one from available info (e.g., property address + date)
7. Set confidence_score based on data clarity:
   - 0.9-1.0: All data clear and explicit
   - 0.7-0.9: Most data clear, minor assumptions
   - 0.5-0.7: Significant assumptions or unclear data
   - Below 0.5: Major uncertainties

Return ONLY the JSON object, no additional text."""
    
    def _convert_to_commission_data(self, extracted_data: Dict[str, Any]) -> CommissionData:
        """
        Convert extracted dictionary to validated CommissionData object.
        
        Handles type conversions and data cleaning.
        """
        # Convert splits
        splits = []
        for split_dict in extracted_data.get('splits', []):
            split = CommissionSplitData(
                agent_name=split_dict['agent_name'],
                agent_email=split_dict.get('agent_email'),
                agent_id=split_dict.get('agent_id'),
                percentage=float(split_dict['percentage']),
                amount=Decimal(str(split_dict['amount'])),
                role=split_dict.get('role'),
                notes=split_dict.get('notes')
            )
            splits.append(split)
        
        # Parse closing date
        closing_date = extracted_data['closing_date']
        if isinstance(closing_date, str):
            # Try to parse various date formats
            closing_date = self._parse_date(closing_date)
        
        # Create CommissionData object (Pydantic will validate)
        commission_data = CommissionData(
            transaction_id=extracted_data['transaction_id'],
            property_address=extracted_data['property_address'],
            sale_amount=Decimal(str(extracted_data['sale_amount'])),
            commission_rate=float(extracted_data['commission_rate']),
            total_commission=Decimal(str(extracted_data['total_commission'])),
            closing_date=closing_date,
            email_source=extracted_data.get('email_source', 'unknown'),
            email_subject=extracted_data.get('email_subject'),
            raw_email_content=extracted_data.get('raw_email_content'),
            confidence_score=float(extracted_data.get('confidence_score', 0.0)),
            status=extracted_data.get('status', 'pending'),
            notes=extracted_data.get('notes'),
            splits=splits
        )
        
        return commission_data
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse date string into datetime object.
        
        Handles various date formats commonly found in emails.
        """
        # Try ISO format first
        for fmt in [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%m/%d/%Y',
            '%m-%d-%Y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y'
        ]:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # If all formats fail, raise error
        raise ValueError(f"Unable to parse date: {date_str}")
    
    def validate_extraction(self, commission_data: CommissionData) -> Dict[str, Any]:
        """
        Validate extracted data and return validation report.
        
        Args:
            commission_data: Extracted commission data
            
        Returns:
            Dictionary with validation results and warnings
        """
        warnings = []
        errors = []
        
        # Check confidence score
        if commission_data.confidence_score < 0.7:
            warnings.append(f"Low confidence score: {commission_data.confidence_score}")
        
        # Check if splits exist
        if not commission_data.splits:
            warnings.append("No commission splits found")
        
        # Check split percentages
        if commission_data.splits:
            total_pct = sum(s.percentage for s in commission_data.splits)
            if abs(total_pct - 1.0) > 0.01:
                errors.append(f"Split percentages sum to {total_pct * 100}%, expected 100%")
        
        # Check commission calculation
        expected_commission = commission_data.sale_amount * Decimal(str(commission_data.commission_rate))
        if abs(commission_data.total_commission - expected_commission) > Decimal('1.00'):
            warnings.append(
                f"Commission calculation mismatch: "
                f"expected ${expected_commission}, got ${commission_data.total_commission}"
            )
        
        return {
            "valid": len(errors) == 0,
            "warnings": warnings,
            "errors": errors,
            "confidence_score": commission_data.confidence_score
        }

