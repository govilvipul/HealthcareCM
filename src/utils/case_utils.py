import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
import logging
from decimal import Decimal
import json

logger = logging.getLogger(__name__)

class CaseManager:
    def __init__(self, aws_client):
        self.aws_client = aws_client
        self.table_name = 'HealthCareCases'
    
    def get_all_cases(self) -> List[Dict[str, Any]]:
        """Get all cases from DynamoDB and convert Decimal to float/int"""
        try:
            table = self.aws_client.get_table(self.table_name)
            response = table.scan()
            cases = response.get('Items', [])
            
            # Convert Decimal objects to native Python types
            converted_cases = []
            for case in cases:
                converted_case = self._convert_decimals(case)
                converted_cases.append(converted_case)
            
            return converted_cases
        except Exception as e:
            logger.error(f"Error fetching cases: {str(e)}")
            return []
    
    def _convert_decimals(self, obj):
        """Recursively convert Decimal objects to float or int"""
        if isinstance(obj, Decimal):
            return float(obj) if obj % 1 != 0 else int(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimals(v) for v in obj]
        else:
            return obj
    
    def filter_cases(self, cases: List[Dict], filters: Dict) -> List[Dict]:
        """Filter cases based on criteria"""
        filtered = cases
        
        if filters.get('status'):
            filtered = [c for c in filtered if c.get('status') in filters['status']]
        
        if filters.get('document_type'):
            filtered = [c for c in filtered if c.get('documentType') in filters['document_type']]
        
        if filters.get('priority'):
            filtered = [c for c in filtered if c.get('priority') in filters['priority']]
        
        if filters.get('search_term'):
            search_term = filters['search_term'].lower()
            filtered = [c for c in filtered if self._case_matches_search(c, search_term)]
        
        return filtered
    
    def _case_matches_search(self, case: Dict, search_term: str) -> bool:
        """Check if case matches search term"""
        search_fields = ['patientName', 'fileName', 'documentType', 'caseSummary', 'diagnosisDescription']
        return any(search_term in str(case.get(field, '')).lower() for field in search_fields)
    
    def update_case_status(self, case_id: str, new_status: str) -> bool:
        """Update case status in DynamoDB"""
        try:
            table = self.aws_client.get_table(self.table_name)
            table.update_item(
                Key={'caseID': case_id},
                UpdateExpression='SET #status = :new_status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':new_status': new_status}
            )
            logger.info(f"Case {case_id} updated to {new_status}")
            return True
        except Exception as e:
            logger.error(f"Error updating case {case_id}: {str(e)}")
            return False
    
    def get_case_metrics(self, cases: List[Dict]) -> Dict:
        """Calculate case metrics"""
        total_cases = len(cases)
        pending_cases = len([c for c in cases if c.get('status') == 'PENDING_REVIEW'])
        high_priority = len([c for c in cases if c.get('priority') == 'HIGH'])
        approved_cases = len([c for c in cases if c.get('status') == 'APPROVED'])
        
        return {
            'total_cases': total_cases,
            'pending_cases': pending_cases,
            'high_priority': high_priority,
            'approved_cases': approved_cases
        }