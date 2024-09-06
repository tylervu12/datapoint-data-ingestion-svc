import unittest
from unittest import mock
from moto import mock_aws
import boto3
import os
import json
from src.lambda_functions.get_texts.get_texts import lambda_handler

class TestGetTextsLambda(unittest.TestCase):

    @mock_aws
    def test_lambda_handler_sends_to_embedding_queue(self):
        # Mock SQS setup
        sqs = boto3.client('sqs', region_name='us-west-2')
        queue_url = sqs.create_queue(QueueName='mock-embedding-queue')['QueueUrl']

        # Debugging statement to print SQS URL
        print(f"Test SQS Queue URL: {queue_url}")

        # Mock environment variable for EMBEDDING_QUEUE_URL
        with mock.patch.dict(os.environ, {'EMBEDDING_QUEUE_URL': queue_url}):
            # Mock the requests.get call
            with mock.patch('requests.get') as mock_requests_get:
                # Simulate a successful website scrape
                mock_requests_get.return_value.status_code = 200
                mock_requests_get.return_value.text = "<html><body>Leadbird website content</body></html>"

                # Sample event to simulate SQS trigger
                event = {
                    "Records": [
                        {
                            "body": json.dumps({
                                "company_name": "Leadbird",
                                "company_website": "https://leadbird.io",
                                "employee_size": "10",
                                "location": "San Francisco, USA"
                            })
                        }
                    ]
                }

                # Call the Lambda handler
                lambda_handler(event, None)

                # Debugging statement to check messages
                print("Checking messages in SQS")

                # Check if the message was sent to SQS
                messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10)
                print(f"Received messages: {messages}")

                # Assert that a message was received
                self.assertEqual(len(messages.get('Messages', [])), 1)

                # Validate the content of the sent message
                sent_message = json.loads(messages['Messages'][0]['Body'])
                print(f"Sent message content: {sent_message}")
                self.assertEqual(sent_message['company_name'], 'Leadbird')
                self.assertEqual(sent_message['company_website'], 'https://leadbird.io')
                self.assertEqual(sent_message['employee_size'], '10')
                self.assertEqual(sent_message['location'], 'San Francisco, USA')
                self.assertIn('scraped_text', sent_message)

if __name__ == '__main__':
    unittest.main()
