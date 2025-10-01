"""
Unit tests for CommissionRepository.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from src.database.models import DatabaseManager, Commission, CommissionSplit
from src.database.repository import CommissionRepository
from src.models.commission import CommissionData, CommissionSplitData


@pytest.fixture
def db_manager():
    """Create a test database manager with in-memory SQLite"""
    manager = DatabaseManager("sqlite:///:memory:")
    manager.create_tables()
    return manager


@pytest.fixture
def repository(db_manager):
    """Create a repository with test database"""
    return CommissionRepository(db_manager)


@pytest.fixture
def sample_commission_data():
    """Create sample commission data for testing"""
    return CommissionData(
        transaction_id="TXN-TEST-001",
        property_address="123 Test St, Test City, CA 90210",
        sale_amount=Decimal("450000.00"),
        commission_rate=0.06,
        total_commission=Decimal("27000.00"),
        closing_date=datetime(2024, 1, 15),
        email_source="test@example.com",
        email_subject="Test Commission Statement",
        confidence_score=0.95,
        status="pending",
        splits=[
            CommissionSplitData(
                agent_name="John Smith",
                agent_email="john@example.com",
                percentage=0.60,
                amount=Decimal("16200.00"),
                role="listing_agent"
            ),
            CommissionSplitData(
                agent_name="Jane Doe",
                agent_email="jane@example.com",
                percentage=0.40,
                amount=Decimal("10800.00"),
                role="buyer_agent"
            )
        ]
    )


class TestCommissionRepository:
    """Tests for CommissionRepository"""
    
    def test_save_commission(self, repository, sample_commission_data):
        """Test saving a commission"""
        commission = repository.save_commission(sample_commission_data)
        
        assert commission.id is not None
        assert commission.transaction_id == "TXN-TEST-001"
        assert len(commission.splits) == 2
        assert commission.total_commission == Decimal("27000.00")
    
    def test_save_duplicate_transaction_id(self, repository, sample_commission_data):
        """Test that duplicate transaction IDs are rejected"""
        repository.save_commission(sample_commission_data)
        
        with pytest.raises(ValueError) as exc_info:
            repository.save_commission(sample_commission_data)
        
        assert "already exists" in str(exc_info.value)
    
    def test_get_commission_by_id(self, repository, sample_commission_data):
        """Test retrieving a commission by ID"""
        saved = repository.save_commission(sample_commission_data)
        
        retrieved = repository.get_commission_by_id(saved.id)
        
        assert retrieved is not None
        assert retrieved.id == saved.id
        assert retrieved.transaction_id == "TXN-TEST-001"
    
    def test_get_commission_by_transaction_id(self, repository, sample_commission_data):
        """Test retrieving a commission by transaction ID"""
        repository.save_commission(sample_commission_data)
        
        retrieved = repository.get_commission_by_transaction_id("TXN-TEST-001")
        
        assert retrieved is not None
        assert retrieved.transaction_id == "TXN-TEST-001"
    
    def test_get_nonexistent_commission(self, repository):
        """Test retrieving a non-existent commission"""
        result = repository.get_commission_by_id(99999)
        assert result is None
        
        result = repository.get_commission_by_transaction_id("NONEXISTENT")
        assert result is None
    
    def test_update_commission_status(self, repository, sample_commission_data):
        """Test updating commission status"""
        commission = repository.save_commission(sample_commission_data)
        
        success = repository.update_commission_status(
            commission.id,
            "verified",
            "Verified by admin"
        )
        
        assert success is True
        
        updated = repository.get_commission_by_id(commission.id)
        assert updated.status == "verified"
        assert updated.notes == "Verified by admin"
    
    def test_update_nonexistent_commission(self, repository):
        """Test updating a non-existent commission"""
        success = repository.update_commission_status(99999, "verified")
        assert success is False
    
    def test_delete_commission(self, repository, sample_commission_data):
        """Test deleting a commission"""
        commission = repository.save_commission(sample_commission_data)
        
        success = repository.delete_commission(commission.id)
        assert success is True
        
        # Verify it's deleted
        result = repository.get_commission_by_id(commission.id)
        assert result is None
    
    def test_delete_nonexistent_commission(self, repository):
        """Test deleting a non-existent commission"""
        success = repository.delete_commission(99999)
        assert success is False


class TestCommissionQueries:
    """Tests for commission query methods"""
    
    @pytest.fixture
    def populated_repository(self, repository):
        """Create a repository with multiple test records"""
        # Create commissions with different dates and amounts
        for i in range(5):
            data = CommissionData(
                transaction_id=f"TXN-TEST-{i:03d}",
                property_address=f"{i} Test St",
                sale_amount=Decimal(f"{(i+1) * 100000}.00"),
                commission_rate=0.06,
                total_commission=Decimal(f"{(i+1) * 6000}.00"),
                closing_date=datetime(2024, 1, 1) + timedelta(days=i*10),
                email_source="test@example.com",
                status="pending" if i % 2 == 0 else "verified",
                splits=[
                    CommissionSplitData(
                        agent_name="John Smith" if i % 2 == 0 else "Jane Doe",
                        percentage=1.0,
                        amount=Decimal(f"{(i+1) * 6000}.00")
                    )
                ]
            )
            repository.save_commission(data)
        
        return repository
    
    def test_query_all_commissions(self, populated_repository):
        """Test querying all commissions"""
        results = populated_repository.query_commissions()
        assert len(results) == 5
    
    def test_query_by_date_range(self, populated_repository):
        """Test querying by date range"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 20)
        
        results = populated_repository.query_commissions(
            start_date=start_date,
            end_date=end_date
        )
        
        assert len(results) == 2  # First two commissions
    
    def test_query_by_status(self, populated_repository):
        """Test querying by status"""
        results = populated_repository.query_commissions(status="verified")
        assert len(results) == 2  # Odd-indexed commissions
    
    def test_query_by_amount_range(self, populated_repository):
        """Test querying by amount range"""
        results = populated_repository.query_commissions(
            min_amount=Decimal("10000.00"),
            max_amount=Decimal("20000.00")
        )
        
        assert len(results) == 2
    
    def test_query_by_agent_name(self, populated_repository):
        """Test querying by agent name"""
        results = populated_repository.query_commissions(agent_name="John Smith")
        assert len(results) == 3  # Even-indexed commissions
    
    def test_query_with_pagination(self, populated_repository):
        """Test query pagination"""
        # Get first 2 results
        page1 = populated_repository.query_commissions(limit=2, offset=0)
        assert len(page1) == 2
        
        # Get next 2 results
        page2 = populated_repository.query_commissions(limit=2, offset=2)
        assert len(page2) == 2
        
        # Verify different results
        assert page1[0].id != page2[0].id
    
    def test_get_agent_commissions(self, populated_repository):
        """Test getting commissions for a specific agent"""
        results = populated_repository.get_agent_commissions("John Smith")
        
        assert len(results) == 3
        for result in results:
            assert result['split']['agent_name'] == "John Smith"
    
    def test_get_total_commissions_by_agent(self, populated_repository):
        """Test getting total commissions grouped by agent"""
        results = populated_repository.get_total_commissions_by_agent()
        
        assert len(results) == 2  # Two agents
        
        # Find John Smith's total
        john_total = next(r for r in results if r['agent_name'] == "John Smith")
        assert john_total['transaction_count'] == 3
        assert john_total['total_amount'] == 6000 + 18000 + 30000  # Sum of splits


class TestRepositoryEdgeCases:
    """Test edge cases and error handling"""
    
    def test_save_commission_without_splits(self, repository):
        """Test saving a commission without splits"""
        data = CommissionData(
            transaction_id="TXN-NO-SPLITS",
            property_address="123 Test St",
            sale_amount=Decimal("450000.00"),
            commission_rate=0.06,
            total_commission=Decimal("27000.00"),
            closing_date=datetime(2024, 1, 15),
            email_source="test@example.com",
            splits=[]
        )
        
        commission = repository.save_commission(data)
        assert commission.id is not None
        assert len(commission.splits) == 0
    
    def test_query_with_no_results(self, repository):
        """Test query that returns no results"""
        results = repository.query_commissions(
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31)
        )
        
        assert len(results) == 0
    
    def test_get_agent_commissions_no_results(self, repository):
        """Test getting commissions for non-existent agent"""
        results = repository.get_agent_commissions("Nonexistent Agent")
        assert len(results) == 0

