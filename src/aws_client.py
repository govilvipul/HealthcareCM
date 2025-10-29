import boto3
import os
import logging
import tempfile
from botocore.exceptions import ClientError
import json

logger = logging.getLogger(__name__)

class AWSClient:
    def __init__(self):
        self.region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        self._clients = {}
    
    def get_dynamodb_resource(self):
        """Get DynamoDB resource"""
        if 'dynamodb' not in self._clients:
            self._clients['dynamodb'] = boto3.resource('dynamodb', region_name=self.region)
        return self._clients['dynamodb']
    
    def get_s3_client(self):
        """Get S3 client"""
        if 's3' not in self._clients:
            self._clients['s3'] = boto3.client('s3', region_name=self.region)
        return self._clients['s3']
    
    def get_table(self, table_name):
        """Get DynamoDB table"""
        try:
            dynamodb = self.get_dynamodb_resource()
            table = dynamodb.Table(table_name)
            # Verify table exists
            table.table_status
            return table
        except ClientError as e:
            logger.error(f"Error accessing table {table_name}: {str(e)}")
            raise e
    
    def download_document(self, s3_location: str) -> str:
        """Download document from S3 and return local file path"""
        try:
            # Parse S3 location (format: s3://bucket-name/key/path)
            if s3_location.startswith('s3://'):
                s3_location = s3_location[5:]
            
            bucket, key = s3_location.split('/', 1)
            
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            local_filename = os.path.join(temp_dir, key.split('/')[-1])
            
            # Download file
            s3_client = self.get_s3_client()
            s3_client.download_file(bucket, key, local_filename)
            
            logger.info(f"Downloaded document to: {local_filename}")
            return local_filename
            
        except Exception as e:
            logger.error(f"Error downloading document {s3_location}: {str(e)}")
            return None
    
    def get_document_url(self, s3_location: str, expires_in=3600) -> str:
        """Generate presigned URL for S3 document"""
        try:
            if s3_location.startswith('s3://'):
                s3_location = s3_location[5:]
            
            bucket, key = s3_location.split('/', 1)
            
            s3_client = self.get_s3_client()
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            return None

# Global instance
aws_client = AWSClient()