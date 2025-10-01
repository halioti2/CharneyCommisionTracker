"""
Unit tests for Flask API endpoints.
"""

import pytest
import json
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.app import app
from src.models.commission import CommissionData, CommissionSplitData


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_email_request():
    """Sample email parse request"""
    return {
        "email_content": """
            Commission Statement
            Transaction: TXN-2024-001
            Property: 123 Main St, Anytown, CA 90210
            Sale Price: $450,000
            Commission: 6% = $27,000
            
            Split:
            - John Smith: 60% = $16,200
            - Jane Doe: 40% = $10,800
            
            Closing: 2024-01-15
        """,
        "email_subject": "Commission Statement",
        "email_source": "escrow@example.com"
    }


@pytest.fixture
def sample_commission_data():
    """Sample commission data"""
    return CommissionData(
        transaction_id="TXN-TEST-001",
        property_address="123 Test St",
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


class TestHealthEndpoint:
    """Tests for health check endpoint"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/api/v1/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'app' in data
        assert 'version' in data


class TestConfigEndpoint:
    """Tests for configuration endpoint"""
    
    def test_get_config(self, client):
        """Test configuration endpoint"""
        response = client.get('/api/v1/config')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'APP_NAME' in data
        assert 'ENVIRONMENT' in data


class TestParseEndpoint:
    """Tests for email parsing endpoint"""
    
    @patch('src.api.app.parser')
    @patch('src.api.app.repository')
    def test_parse_email_success(self, mock_repo, mock_parser, client, sample_email_request, sample_commission_data):
        """Test successful email parsing"""
        # Mock parser response
        mock_parser.parse_commission_email.return_value = sample_commission_data
        mock_parser.validate_extraction.return_value = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "confidence_score": 0.95
        }
        
        # Mock repository response
        mock_commission = Mock()
        mock_commission.to_dict.return_value = {
            "id": 1,
            "transaction_id": "TXN-TEST-001",
            "total_commission": 27000.00
        }
        mock_repo.save_commission.return_value = mock_commission
        
        response = client.post(
            '/api/v1/parse',
            data=json.dumps(sample_email_request),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert 'validation' in data
    
    def test_parse_email_missing_content(self, client):
        """Test parsing without email content"""
        response = client.post(
            '/api/v1/parse',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'email_content' in data['error']
    
    @patch('src.api.app.parser')
    def test_parse_email_validation_error(self, mock_parser, client, sample_email_request):
        """Test parsing with validation error"""
        mock_parser.parse_commission_email.side_effect = ValueError("Invalid data")
        
        response = client.post(
            '/api/v1/parse',
            data=json.dumps(sample_email_request),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False


class TestCommissionsEndpoint:
    """Tests for commissions query endpoint"""
    
    @patch('src.api.app.repository')
    def test_get_commissions(self, mock_repo, client):
        """Test getting all commissions"""
        mock_commission = Mock()
        mock_commission.to_dict.return_value = {
            "id": 1,
            "transaction_id": "TXN-TEST-001"
        }
        mock_repo.query_commissions.return_value = [mock_commission]
        
        response = client.get('/api/v1/commissions')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
    
    @patch('src.api.app.repository')
    def test_get_commissions_with_filters(self, mock_repo, client):
        """Test getting commissions with filters"""
        mock_repo.query_commissions.return_value = []
        
        response = client.get('/api/v1/commissions?status=verified&limit=50')
        
        assert response.status_code == 200
        mock_repo.query_commissions.assert_called_once()
        call_kwargs = mock_repo.query_commissions.call_args[1]
        assert call_kwargs['status'] == 'verified'
        assert call_kwargs['limit'] == 50
    
    @patch('src.api.app.repository')
    def test_get_single_commission(self, mock_repo, client):
        """Test getting a single commission by ID"""
        mock_commission = Mock()
        mock_commission.to_dict.return_value = {
            "id": 1,
            "transaction_id": "TXN-TEST-001"
        }
        mock_repo.get_commission_by_id.return_value = mock_commission
        
        response = client.get('/api/v1/commissions/1')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['id'] == 1
    
    @patch('src.api.app.repository')
    def test_get_nonexistent_commission(self, mock_repo, client):
        """Test getting a non-existent commission"""
        mock_repo.get_commission_by_id.return_value = None
        
        response = client.get('/api/v1/commissions/99999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False


class TestUpdateStatusEndpoint:
    """Tests for commission status update endpoint"""
    
    @patch('src.api.app.repository')
    def test_update_status_success(self, mock_repo, client):
        """Test successful status update"""
        mock_repo.update_commission_status.return_value = True
        
        response = client.patch(
            '/api/v1/commissions/1/status',
            data=json.dumps({"status": "verified", "notes": "Approved"}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    @patch('src.api.app.repository')
    def test_update_status_not_found(self, mock_repo, client):
        """Test updating status of non-existent commission"""
        mock_repo.update_commission_status.return_value = False
        
        response = client.patch(
            '/api/v1/commissions/99999/status',
            data=json.dumps({"status": "verified"}),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_update_status_missing_field(self, client):
        """Test updating status without required field"""
        response = client.patch(
            '/api/v1/commissions/1/status',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False


class TestAgentEndpoints:
    """Tests for agent-specific endpoints"""
    
    @patch('src.api.app.repository')
    def test_get_agent_commissions(self, mock_repo, client):
        """Test getting commissions for a specific agent"""
        mock_repo.get_agent_commissions.return_value = [
            {
                "commission": {"id": 1},
                "split": {"agent_name": "John Smith", "amount": 16200.00}
            }
        ]
        
        response = client.get('/api/v1/agents/John%20Smith/commissions')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['agent_name'] == 'John Smith'
    
    @patch('src.api.app.repository')
    def test_get_agent_summary(self, mock_repo, client):
        """Test getting agent summary"""
        mock_repo.get_total_commissions_by_agent.return_value = [
            {
                "agent_name": "John Smith",
                "total_amount": 50000.00,
                "transaction_count": 3
            }
        ]
        
        response = client.get('/api/v1/agents/summary')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1


class TestDeleteEndpoint:
    """Tests for commission deletion endpoint"""
    
    @patch('src.api.app.repository')
    def test_delete_commission_success(self, mock_repo, client):
        """Test successful commission deletion"""
        mock_repo.delete_commission.return_value = True
        
        response = client.delete('/api/v1/commissions/1')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    @patch('src.api.app.repository')
    def test_delete_commission_not_found(self, mock_repo, client):
        """Test deleting non-existent commission"""
        mock_repo.delete_commission.return_value = False
        
        response = client.delete('/api/v1/commissions/99999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False

