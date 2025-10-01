"""
Sample usage examples for the Charney Commission Tracker.

This script demonstrates how to use the various components of the system.
"""

import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.models import DatabaseManager
from src.database.repository import CommissionRepository
from src.models.commission import CommissionData, CommissionSplitData
from config.config import config


def example_1_create_commission_manually():
    """Example 1: Create a commission record manually"""
    print("\n=== Example 1: Create Commission Manually ===\n")
    
    # Initialize database and repository
    db_manager = DatabaseManager()
    db_manager.create_tables()
    repository = CommissionRepository(db_manager)
    
    # Create commission data
    commission_data = CommissionData(
        transaction_id="TXN-EXAMPLE-001",
        property_address="456 Oak Avenue, Springfield, CA 90210",
        sale_amount=Decimal("550000.00"),
        commission_rate=0.05,
        total_commission=Decimal("27500.00"),
        closing_date=datetime(2024, 2, 15),
        email_source="manual@example.com",
        email_subject="Manual Entry",
        confidence_score=1.0,
        status="verified",
        notes="Manually entered for demonstration",
        splits=[
            CommissionSplitData(
                agent_name="Alice Johnson",
                agent_email="alice@realty.com",
                percentage=0.55,
                amount=Decimal("15125.00"),
                role="listing_agent"
            ),
            CommissionSplitData(
                agent_name="Bob Williams",
                agent_email="bob@realty.com",
                percentage=0.45,
                amount=Decimal("12375.00"),
                role="buyer_agent"
            )
        ]
    )
    
    # Save to database
    commission = repository.save_commission(commission_data)
    
    print(f"✓ Created commission: {commission.transaction_id}")
    print(f"  Property: {commission.property_address}")
    print(f"  Total: ${commission.total_commission}")
    print(f"  Splits: {len(commission.splits)}")
    for split in commission.splits:
        print(f"    - {split.agent_name}: ${split.amount} ({split.percentage * 100}%)")


def example_2_query_commissions():
    """Example 2: Query commissions with filters"""
    print("\n=== Example 2: Query Commissions ===\n")
    
    repository = CommissionRepository()
    
    # Query all commissions
    all_commissions = repository.query_commissions(limit=10)
    print(f"Total commissions in database: {len(all_commissions)}")
    
    # Query by status
    verified = repository.query_commissions(status="verified")
    print(f"Verified commissions: {len(verified)}")
    
    # Query by date range
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    year_commissions = repository.query_commissions(
        start_date=start_date,
        end_date=end_date
    )
    print(f"Commissions in 2024: {len(year_commissions)}")
    
    # Query by amount range
    high_value = repository.query_commissions(
        min_amount=Decimal("20000.00")
    )
    print(f"High-value commissions (>$20k): {len(high_value)}")


def example_3_agent_summary():
    """Example 3: Get agent commission summary"""
    print("\n=== Example 3: Agent Commission Summary ===\n")
    
    repository = CommissionRepository()
    
    # Get summary for all agents
    summary = repository.get_total_commissions_by_agent()
    
    print("Agent Commission Summary:")
    print("-" * 60)
    for agent in summary:
        print(f"{agent['agent_name']:30} ${agent['total_amount']:>12,.2f}  ({agent['transaction_count']} transactions)")


def example_4_update_status():
    """Example 4: Update commission status"""
    print("\n=== Example 4: Update Commission Status ===\n")
    
    repository = CommissionRepository()
    
    # Get a commission
    commissions = repository.query_commissions(limit=1)
    if commissions:
        commission = commissions[0]
        print(f"Commission: {commission.transaction_id}")
        print(f"Current status: {commission.status}")
        
        # Update status
        success = repository.update_commission_status(
            commission.id,
            "paid",
            "Payment processed on " + datetime.now().strftime("%Y-%m-%d")
        )
        
        if success:
            print("✓ Status updated to 'paid'")
        else:
            print("✗ Failed to update status")
    else:
        print("No commissions found in database")


def example_5_parse_email_sample():
    """Example 5: Parse a sample email (requires OpenAI API key)"""
    print("\n=== Example 5: Parse Sample Email ===\n")
    
    if not config.OPENAI_API_KEY:
        print("⚠ OPENAI_API_KEY not configured. Skipping this example.")
        return
    
    from src.parsers.email_parser import AIEmailParser
    
    # Sample email content
    sample_email = """
    COMMISSION STATEMENT
    
    Transaction ID: MLS-2024-789456
    Property Address: 789 Maple Drive, Riverside, CA 92501
    
    Sale Details:
    - Sale Price: $625,000.00
    - Commission Rate: 5.5%
    - Total Commission: $34,375.00
    
    Commission Split:
    - Sarah Martinez (Listing Agent): 60% = $20,625.00
    - Michael Chen (Buyer Agent): 40% = $13,750.00
    
    Closing Date: March 1, 2024
    
    Please confirm receipt of this statement.
    
    Best regards,
    Escrow Department
    escrow@titlecompany.com
    """
    
    # Initialize parser
    parser = AIEmailParser(api_key=config.OPENAI_API_KEY)
    
    try:
        # Parse email
        print("Parsing email with AI...")
        commission_data = parser.parse_commission_email(
            email_content=sample_email,
            email_subject="Commission Statement - 789 Maple Drive",
            email_source="escrow@titlecompany.com"
        )
        
        # Validate
        validation = parser.validate_extraction(commission_data)
        
        print(f"✓ Parsing complete!")
        print(f"  Transaction ID: {commission_data.transaction_id}")
        print(f"  Property: {commission_data.property_address}")
        print(f"  Total Commission: ${commission_data.total_commission}")
        print(f"  Confidence Score: {commission_data.confidence_score}")
        print(f"  Validation: {'✓ Valid' if validation['valid'] else '✗ Invalid'}")
        
        if validation['warnings']:
            print(f"  Warnings: {', '.join(validation['warnings'])}")
        
        # Save to database
        repository = CommissionRepository()
        commission = repository.save_commission(commission_data)
        print(f"✓ Saved to database with ID: {commission.id}")
        
    except Exception as e:
        print(f"✗ Error: {e}")


def example_6_api_usage():
    """Example 6: Using the API with requests"""
    print("\n=== Example 6: API Usage Example ===\n")
    
    print("To use the API, first start the server:")
    print("  python src/api/app.py")
    print()
    print("Then you can make requests using curl or any HTTP client:")
    print()
    print("# Parse an email")
    print('curl -X POST http://localhost:5000/api/v1/parse \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"email_content": "Commission Statement..."}\'')
    print()
    print("# Get all commissions")
    print('curl http://localhost:5000/api/v1/commissions')
    print()
    print("# Get agent summary")
    print('curl http://localhost:5000/api/v1/agents/summary')


def main():
    """Run all examples"""
    print("=" * 70)
    print("Charney Commission Tracker - Usage Examples")
    print("=" * 70)
    
    try:
        example_1_create_commission_manually()
        example_2_query_commissions()
        example_3_agent_summary()
        example_4_update_status()
        example_5_parse_email_sample()
        example_6_api_usage()
        
        print("\n" + "=" * 70)
        print("All examples completed!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

