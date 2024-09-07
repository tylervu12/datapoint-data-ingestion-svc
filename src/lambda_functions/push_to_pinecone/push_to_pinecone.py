import json
import os
import boto3
import hashlib 
import numpy as np
from pinecone import Pinecone

# Initialize SQS client
sqs = boto3.client('sqs')

def get_pinecone_client():
    # Initialize Pinecone client
    return Pinecone(
        api_key=os.environ.get("PINECONE_API_KEY")  # Pinecone API Key
    )

def generate_unique_id(company_website):
    """Generate a unique ID using SHA-256 hash of the company website."""
    return hashlib.sha256(company_website.encode('utf-8')).hexdigest()

def lambda_handler(event, context):
    # Extract environment variables
    PINECONE_INDEX_NAME = os.environ.get('PINECONE_INDEX_NAME')  
    DYNAMO_SQS_QUEUE_URL = os.environ.get('DYNAMO_SQS_QUEUE_URL')  # Second SQS queue URL for metadata storage

    # Initialize Pinecone client and connect to the index
    pinecone_client = get_pinecone_client()
    index = pinecone_client.Index(PINECONE_INDEX_NAME)

    # Extract and process SQS messages (which come in batches)
    for record in event['Records']:
        message_body = json.loads(record['body'])

        company_name = message_body['company_name']
        company_website = message_body['company_website']
        employee_size = message_body['employee_size']
        location = message_body['location']
        embeddings = message_body['embeddings']

        # Generate a unique ID based on the company website
        unique_id = generate_unique_id(company_website)

        print(f"Upserting embedding for {company_name} - {company_website} with ID: {unique_id}")

        # Upsert embeddings to Pinecone with metadata
        upsert_to_pinecone(index, unique_id, embeddings, company_name, company_website, employee_size, location)

        # Send the unique ID and metadata to the second SQS queue for DynamoDB
        send_to_dynamo_sqs(unique_id, company_name, company_website, employee_size, location, DYNAMO_SQS_QUEUE_URL)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Embeddings upserted into Pinecone and metadata sent to DynamoDB SQS')
    }

def upsert_to_pinecone(index, unique_id, embedding, company_name, company_website, employee_size, location):
    """Upsert the embedding and metadata to Pinecone."""
    try:
        response = index.upsert(vectors=[{
            "id": unique_id,  # Unique identifier generated from company website
            "values": embedding,  # Embedding vector
            "metadata": {
                "company_name": company_name,
                "company_website": company_website,
                "employee_size": employee_size,
                "location": location
            }
        }])
        print(f"Successfully upserted data to Pinecone: {response}")
    except Exception as e:
        print(f"Error upserting to Pinecone: {str(e)}")

def send_to_dynamo_sqs(unique_id, company_name, company_website, employee_size, location, queue_url):
    """Send the unique ID and metadata to another SQS queue for DynamoDB."""
    try:
        message = {
            'id': unique_id,
            'company_name': company_name,
            'company_website': company_website,
            'employee_size': employee_size,
            'location': location
        }
        
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message)
        )
        print(f"Sent metadata to DynamoDB SQS queue: {response['MessageId']}")
    except Exception as e:
        print(f"Failed to send metadata to DynamoDB SQS queue: {str(e)}")
