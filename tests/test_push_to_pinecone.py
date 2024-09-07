import unittest
from unittest.mock import patch
import boto3
from moto import mock_aws
import json
import os
from src.lambda_functions.push_to_pinecone.push_to_pinecone import lambda_handler  # Ensure correct path

class TestPushToPineconeLambda(unittest.TestCase):

    @mock_aws
    def test_lambda_handler(self):
        # Mock SQS and Pinecone client setup
        sqs = boto3.client('sqs', region_name='us-west-2')
        
        # Create a mock SQS queue for the second queue (DynamoDB metadata queue)
        dynamo_sqs_url = sqs.create_queue(QueueName='mock-dynamo-sqs')['QueueUrl']
        print(f"Mock SQS Queue URL for DynamoDB: {dynamo_sqs_url}")
        
        # Mock environment variables, including DYNAMO_SQS_QUEUE_URL
        with patch.dict(os.environ, {
            'DYNAMO_SQS_QUEUE_URL': dynamo_sqs_url,
            'PINECONE_INDEX_NAME': 'mock-index'
        }):
            # Mock Pinecone client
            with patch('src.lambda_functions.push_to_pinecone.push_to_pinecone.get_pinecone_client') as mock_pinecone_client:
                mock_pinecone_index = mock_pinecone_client.return_value.Index.return_value
                mock_pinecone_index.upsert.return_value = {'upserted': 1}  # Mock successful upsert

                # Simulate SQS event
                event = {
                    'Records': [
                        {
                            'body': json.dumps({
                                'company_name': 'Test Company',
                                'company_website': 'https://test.com',
                                'employee_size': '50',
                                'location': 'USA',
                                'embeddings': [0.1] * 1536
                            })
                        }
                    ]
                }

                # Mock SQS client for the second SQS (DynamoDB metadata queue)
                with patch('src.lambda_functions.push_to_pinecone.push_to_pinecone.sqs') as mock_sqs:
                    # Mock send_message to return a success message
                    mock_sqs.send_message.return_value = {'MessageId': 'mock-message-id'}

                    # Call the Lambda handler
                    response = lambda_handler(event, None)

                    # Assert the Lambda function executed successfully
                    self.assertEqual(response['statusCode'], 200)
                    self.assertEqual(json.loads(response['body']), 'Embeddings upserted into Pinecone and metadata sent to DynamoDB SQS')

                    # Assert Pinecone upsert was called with the correct arguments
                    mock_pinecone_index.upsert.assert_called_once()
                    upsert_call_args = mock_pinecone_index.upsert.call_args
                    upsert_vector = upsert_call_args[1]['vectors'][0]  # Extract the first vector from the upsert arguments
                    self.assertEqual(upsert_vector['id'], '396936bd0bf0603d6784b65d03e96dae90566c36b62661f28d4116c516524bcc')
                    self.assertEqual(upsert_vector['metadata']['company_name'], 'Test Company')

                    # Assert that send_message to DynamoDB queue was called
                    mock_sqs.send_message.assert_called_once_with(
                        QueueUrl=dynamo_sqs_url,
                        MessageBody=json.dumps({
                            'id': '396936bd0bf0603d6784b65d03e96dae90566c36b62661f28d4116c516524bcc',
                            'company_name': 'Test Company',
                            'company_website': 'https://test.com',
                            'employee_size': '50',
                            'location': 'USA'
                        })
                    )

if __name__ == '__main__':
    unittest.main()
