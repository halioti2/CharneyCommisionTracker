"""
Integration tests for the complete email-to-database pipeline.

These tests verify that all components work together correctly.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch

from src.database.models import DatabaseManager
from src.database.repository import CommissionRepository
from src.parsers.email_parser import AIEmailParser
from src.models.commission import CommissionData, CommissionSplitData


@pytest.fixture
def test_db():
    """Create a test database"""
    db_manager = DatabaseManager("sqlite:///:memory:")
    db_manager.create_tables()
    return db_manager


@pytest.fixture
def repository(test_db):
    """Create a repository with test database"""
    return CommissionRepository(test_db)


@pytest.fixture
def sample_email():
    """Sample commission email"""
    return """
    COMMISSION STATEMENT
    
    Transaction: TXN-INT-TEST-001
    Property: 123 Integration Test Lane, Test City, CA 90210
    
    Sale Price: $500,000.00
    Commission Rate: 6%
    Total Commission: $30,000.00
    
    Commission Split:
    - Agent A: 50% = $15,000.00
    - Agent B: 50% = $15,000.00
    
    Closing Date: 2024-01-20
    
    From: escrow@test.com
    """


class TestEndToEndPipeline:
    """Test the complete pipeline from email to database"""
    
    @pytest.mark.integration
    def test_complete_pipeline_with_mock_parser(self, repository, sample_email):
        """Test complete pipeline with mocked AI parser"""
        
        # Create mock commission data (simulating AI parser output)
        commission_data = CommissionData(
            transaction_id="TXN-INT-TEST-001",
            property_address="123 Integration Test Lane, Test City, CA 90210",
            sale_amount=Decimal("500000.00"),
            commission_rate=0.06,
            total_commission=Decimal("30000.00"),
            closing_date=datetime(2024, 1, 20),
            email_source="escrow@test.com",
            email_subject="Commission Statement",
            raw_email_content=sample_email,
            confidence_score=0.95,
            status="pending",
            splits=[
                CommissionSplitData(
                    agent_name="Agent A",
                    percentage=0.50,
                    amount=Decimal("15000.00"),
                    role="listing_agent"
                ),
                CommissionSplitData(
                    agent_name="Agent B",
                    percentage=0.50,
                    amount=Decimal("15000.00"),
                    role="buyer_agent"
                )
            ]
        )
        
        # Save to database
        commission = repository.save_commission(commission_data)
        
        # Verify commission was saved
        assert commission.id is not None
        assert commission.transaction_id == "TXN-INT-TEST-001"
        
        # Retrieve from database
        retrieved = repository.get_commission_by_id(commission.id)
        assert retrieved is not None
        assert retrieved.transaction_id == "TXN-INT-TEST-001"
        assert len(retrieved.splits) == 2
        
        # Verify splits
        split_names = [s.agent_name for s in retrieved.splits]
        assert "Agent A" in split_names
        assert "Agent B" in split_names
        
        # Query by agent
        agent_a_commissions = repository.get_agent_commissions("Agent A")
        assert len(agent_a_commissions) == 1
        assert agent_a_commissions[0]['split']['amount'] == 15000.00
        
        # Update status
        success = repository.update_commission_status(
            commission.id,
            "verified",
            "Integration test verification"
        )
        assert success is True
        
        # Verify status update
        updated = repository.get_commission_by_id(commission.id)
        assert updated.status == "verified"
        assert updated.notes == "Integration test verification"


class TestMultipleCommissions:
    """Test handling multiple commissions"""
    
    @pytest.mark.integration
    def test_multiple_commissions_workflow(self, repository):
        """Test creating and querying multiple commissions"""
        
        # Create multiple commissions
        commissions_data = []
        for i in range(5):
            data = CommissionData(
                transaction_id=f"TXN-MULTI-{i:03d}",
                property_address=f"{i} Test Street",
                sale_amount=Decimal(f"{(i+1) * 100000}.00"),
                commission_rate=0.06,
                total_commission=Decimal(f"{(i+1) * 6000}.00"),
                closing_date=datetime(2024, 1, i+1),
                email_source="test@example.com",
                status="pending" if i % 2 == 0 else "verified",
                splits=[
                    CommissionSplitData(
                        agent_name=f"Agent {i % 2}",
                        percentage=1.0,
                        amount=Decimal(f"{(i+1) * 6000}.00")
                    )
                ]
            )
            commission = repository.save_commission(data)
            commissions_data.append(commission)
        
        # Verify all were saved
        assert len(commissions_data) == 5
        
        # Query all
        all_commissions = repository.query_commissions()
        assert len(all_commissions) == 5
        
        # Query by status
        pending = repository.query_commissions(status="pending")
        verified = repository.query_commissions(status="verified")
        assert len(pending) == 3  # 0, 2, 4
        assert len(verified) == 2  # 1, 3
        
        # Query by date range
        jan_1_to_3 = repository.query_commissions(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 3)
        )
        assert len(jan_1_to_3) == 3
        
        # Get agent summary
        summary = repository.get_total_commissions_by_agent()
        assert len(summary) == 2  # Agent 0 and Agent 1
        
        # Verify totals
        agent_0_total = next(s for s in summary if s['agent_name'] == 'Agent 0')
        agent_1_total = next(s for s in summary if s['agent_name'] == 'Agent 1')
        
        # Agent 0: commissions 0, 2, 4 = 6000 + 18000 + 30000 = 54000
        assert agent_0_total['total_amount'] == 54000.00
        assert agent_0_total['transaction_count'] == 3
        
        # Agent 1: commissions 1, 3 = 12000 + 24000 = 36000
        assert agent_1_total['total_amount'] == 36000.00
        assert agent_1_total['transaction_count'] == 2


class TestDataIntegrity:
    """Test data integrity and validation throughout the pipeline"""
    
    @pytest.mark.integration
    def test_duplicate_transaction_id_prevention(self, repository):
        """Test that duplicate transaction IDs are prevented"""
        
        data = CommissionData(
            transaction_id="TXN-DUPLICATE-TEST",
            property_address="123 Test St",
            sale_amount=Decimal("450000.00"),
            commission_rate=0.06,
            total_commission=Decimal("27000.00"),
            closing_date=datetime(2024, 1, 15),
            email_source="test@example.com",
            splits=[]
        )
        
        # Save first time - should succeed
        commission1 = repository.save_commission(data)
        assert commission1.id is not None
        
        # Try to save again - should fail
        with pytest.raises(ValueError) as exc_info:
            repository.save_commission(data)
        
        assert "already exists" in str(exc_info.value)
    
    @pytest.mark.integration
    def test_cascade_delete(self, repository):
        """Test that deleting a commission also deletes its splits"""
        
        data = CommissionData(
            transaction_id="TXN-CASCADE-TEST",
            property_address="123 Test St",
            sale_amount=Decimal("450000.00"),
            commission_rate=0.06,
            total_commission=Decimal("27000.00"),
            closing_date=datetime(2024, 1, 15),
            email_source="test@example.com",
            splits=[
                CommissionSplitData(
                    agent_name="Test Agent",
                    percentage=1.0,
                    amount=Decimal("27000.00")
                )
            ]
        )
        
        # Save commission with split
        commission = repository.save_commission(data)
        assert len(commission.splits) == 1
        
        # Delete commission
        success = repository.delete_commission(commission.id)
        assert success is True
        
        # Verify it's deleted
        retrieved = repository.get_commission_by_id(commission.id)
        assert retrieved is None


class TestComplexQueries:
    """Test complex query scenarios"""
    
    @pytest.mark.integration
    def test_complex_filtering(self, repository):
        """Test combining multiple filters"""
        
        # Create diverse set of commissions
        test_data = [
            {
                "transaction_id": "TXN-COMPLEX-001",
                "amount": Decimal("500000.00"),
                "commission": Decimal("30000.00"),
                "date": datetime(2024, 1, 15),
                "status": "verified",
                "agent": "John Smith"
            },
            {
                "transaction_id": "TXN-COMPLEX-002",
                "amount": Decimal("300000.00"),
                "commission": Decimal("18000.00"),
                "date": datetime(2024, 2, 20),
                "status": "pending",
                "agent": "Jane Doe"
            },
            {
                "transaction_id": "TXN-COMPLEX-003",
                "amount": Decimal("750000.00"),
                "commission": Decimal("45000.00"),
                "date": datetime(2024, 3, 10),
                "status": "verified",
                "agent": "John Smith"
            }
        ]
        
        for item in test_data:
            data = CommissionData(
                transaction_id=item["transaction_id"],
                property_address="Test Address",
                sale_amount=item["amount"],
                commission_rate=0.06,
                total_commission=item["commission"],
                closing_date=item["date"],
                email_source="test@example.com",
                status=item["status"],
                splits=[
                    CommissionSplitData(
                        agent_name=item["agent"],
                        percentage=1.0,
                        amount=item["commission"]
                    )
                ]
            )
            repository.save_commission(data)
        
        # Test: Verified commissions for John Smith
        results = repository.query_commissions(
            status="verified",
            agent_name="John Smith"
        )
        assert len(results) == 2
        
        # Test: High-value commissions (>$25k)
        results = repository.query_commissions(
            min_amount=Decimal("25000.00")
        )
        assert len(results) == 2  # TXN-001 and TXN-003
        
        # Test: Date range + status
        results = repository.query_commissions(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 2, 28),
            status="verified"
        )
        assert len(results) == 1  # Only TXN-001
        
        # Test: Pagination
        page1 = repository.query_commissions(limit=2, offset=0)
        page2 = repository.query_commissions(limit=2, offset=2)
        assert len(page1) == 2
        assert len(page2) == 1
        assert page1[0].id != page2[0].id


@pytest.mark.integration
@pytest.mark.slow
class TestPerformance:
    """Test performance with larger datasets"""
    
    def test_bulk_insert_performance(self, repository):
        """Test inserting many commissions"""
        
        # Create 50 commissions
        for i in range(50):
            data = CommissionData(
                transaction_id=f"TXN-PERF-{i:04d}",
                property_address=f"{i} Performance Test St",
                sale_amount=Decimal("450000.00"),
                commission_rate=0.06,
                total_commission=Decimal("27000.00"),
                closing_date=datetime(2024, 1, 1),
                email_source="test@example.com",
                splits=[]
            )
            repository.save_commission(data)
        
        # Verify all were saved
        all_commissions = repository.query_commissions(limit=100)
        assert len(all_commissions) >= 50
    
    def test_query_performance(self, repository):
        """Test query performance with many records"""
        
        # Query should complete quickly even with many records
        results = repository.query_commissions(limit=100)
        assert isinstance(results, list)

