import unittest
from unittest.mock import patch
import boto3
from moto import mock_aws
import json
import os
from src.lambda_functions.get_embeddings.get_embeddings import lambda_handler, get_openai_embedding

class TestEmbeddingLambda(unittest.TestCase):

    @mock_aws
    @patch('src.lambda_functions.get_embeddings.get_embeddings.get_openai_embedding')  # Correct path
    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'mock-api-key',
    })
    def test_lambda_handler(self, mock_get_openai_embedding):
        # Mock SQS setup using boto3.client (following the same structure as the working test)
        sqs = boto3.client('sqs', region_name='us-west-2')
        queue_url = sqs.create_queue(QueueName='mock-embedding-queue')['QueueUrl']

        # Set the mock PINECONE_QUEUE_URL to the mock queue URL
        os.environ['PINECONE_QUEUE_URL'] = queue_url

        # Mock OpenAI embeddings response
        mock_get_openai_embedding.return_value = [0.1] * 1536  # A valid embedding of length 1536

        # Simulate an SQS event
        event = {
            'Records': [
                {
                    'body': json.dumps({
                        'company_name': 'Test Company',
                        'company_website': 'https://test.com',
                        'employee_size': '50',
                        'location': 'USA',
                        'scraped_text': 'Sample text for embedding generation.'
                    })
                }
            ]
        }

        # Call the Lambda handler
        response = lambda_handler(event, None)

        # Assert that the Lambda returns the correct response
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), 'Embedding processing completed')

        # Check if messages were sent to SQS
        messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10)
        self.assertEqual(len(messages.get('Messages', [])), 1)

        # Retrieve the actual message that was sent
        sent_message = json.loads(messages['Messages'][0]['Body'])
        self.assertEqual(sent_message['company_name'], 'Test Company')
        self.assertEqual(sent_message['company_website'], 'https://test.com')
        self.assertEqual(sent_message['employee_size'], '50')
        self.assertEqual(sent_message['location'], 'USA')
        self.assertEqual(len(sent_message['embeddings']), 256)  # The embedding should be reduced to 256 dimensions

if __name__ == '__main__':
    unittest.main()
