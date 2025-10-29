import pytest
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.case_utils import CaseManager

class MockAWSClient:
    """Mock AWS client for testing"""
    def get_table(self, table_name):
        return MockTable()

class MockTable:
    def scan(self):
        return {'Items': []}
    
    def update_item(self, **kwargs):
        return {}

def test_case_manager_initialization():
    """Test CaseManager initialization"""
    mock_client = MockAWSClient()
    manager = CaseManager(mock_client)
    assert manager.table_name == 'HealthCareCases'

def test_filter_cases():
    """Test case filtering"""
    mock_client = MockAWSClient()
    manager = CaseManager(mock_client)
    
    test_cases = [
        {'status': 'PENDING_REVIEW', 'documentType': 'pre-auth', 'priority': 'HIGH'},
        {'status': 'APPROVED', 'documentType': 'clinical-note', 'priority': 'MEDIUM'},
    ]
    
    # Test status filter
    filtered = manager.filter_cases(test_cases, {'status': ['PENDING_REVIEW']})
    assert len(filtered) == 1
    assert filtered[0]['status'] == 'PENDING_REVIEW'

if __name__ == '__main__':
    pytest.main([__file__])