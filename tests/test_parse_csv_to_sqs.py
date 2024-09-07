import unittest
from unittest.mock import patch
import boto3
from moto import mock_aws
import json
import os
from src.lambda_functions.parse_csv_to_sqs.parse_csv_to_sqs import lambda_handler

class TestLambdaFunction(unittest.TestCase):

    @mock_aws
    def test_lambda_handler(self):
        # Set up the mocked S3 and SQS services
        s3 = boto3.client('s3', region_name='us-west-2')
        sqs = boto3.client('sqs', region_name='us-west-2')

        # Create a mock S3 bucket and object
        bucket_name = 'mock-bucket'
        file_key = 'mock.csv'
        s3.create_bucket(Bucket=bucket_name,
                         CreateBucketConfiguration={'LocationConstraint': 'us-west-2'})
        csv_content = "company_name,company_website,employee_size,location\n" \
                      "test1,test1.com,45,USA\n" \
                      "test2,test2.com,592,Canada\n"
        s3.put_object(Bucket=bucket_name, Key=file_key, Body=csv_content)

        # Create a mock SQS queue
        queue_url = sqs.create_queue(QueueName='mock-queue')['QueueUrl']
        print(f"Mock SQS Queue URL: {queue_url}")

        # Mock environment variables at the module level
        with patch.dict(os.environ, {'QUEUE_URL': queue_url}):
            # Simulate the S3 event that triggers the Lambda function
            event = {
                "Records": [
                    {
                        "s3": {
                            "bucket": {
                                "name": bucket_name
                            },
                            "object": {
                                "key": file_key
                            }
                        }
                    }
                ]
            }

            # Call the Lambda handler function with the event
            response = lambda_handler(event, None)

            # Assert the Lambda function executed successfully
            self.assertEqual(response['statusCode'], 200)

            # Check if messages were sent to SQS
            messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10)
            self.assertEqual(len(messages.get('Messages', [])), 2)

            # Validate message content
            first_message = json.loads(messages['Messages'][0]['Body'])
            self.assertEqual(first_message['company_name'], 'test1')
            self.assertEqual(first_message['company_website'], 'https://www.test1.com')
            self.assertEqual(first_message['employee_size'], '11-50')
            self.assertEqual(first_message['location'], 'USA')

if __name__ == '__main__':
    unittest.main()
