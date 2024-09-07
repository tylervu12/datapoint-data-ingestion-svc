import json
import os
import boto3
from openai import OpenAI  
import numpy as np
import tiktoken

# Initialize SQS client
sqs = boto3.client('sqs')

# Function to normalize the embedding vector using L2 normalization
def normalize_l2(x):
    x = np.array(x)
    norm = np.linalg.norm(x)
    if norm == 0:
        return x
    return x / norm

def get_openai_client():
    # Initialize OpenAI client with max_retries set to 3
    return OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),  
        max_retries=3
    )

def lambda_handler(event, context):
    # Extract environment variables
    PINECONE_QUEUE_URL = os.environ.get('PINECONE_QUEUE_URL')  # For the next SQS queue

    # Set the maximum token length and encoding for the model
    max_tokens = 8000
    embedding_encoding = "cl100k_base"
    encoding = tiktoken.get_encoding(embedding_encoding)

    # Initialize OpenAI client once before processing
    client = get_openai_client()

    # Extract and process SQS messages (which come in batches)
    for record in event['Records']:
        message_body = json.loads(record['body'])
        company_name = message_body['company_name']
        company_website = message_body['company_website']
        employee_size = message_body['employee_size']
        location = message_body['location']
        scraped_text = message_body['scraped_text']

        print(f"Processing embedding for {company_name} - {company_website}")

        # Ensure the text is within the max token limit
        n_tokens = len(encoding.encode(scraped_text))
        if n_tokens > max_tokens:
            print(f"Text exceeds {max_tokens} tokens, truncating.")
            truncated_text = encoding.decode(encoding.encode(scraped_text)[:max_tokens])
        else:
            truncated_text = scraped_text

        # Get embeddings from OpenAI API
        embeddings = get_openai_embedding(truncated_text, client)

        if embeddings:
            print(f"Successfully generated embeddings for {company_name}")

            # Reduce embeddings to 256 dimensions and normalize using L2 normalization
            reduced_embedding = normalize_l2(embeddings[:256])

            # Prepare message for the next queue (to push to Pinecone)
            message = {
                'company_name': company_name,
                'company_website': company_website,
                'employee_size': employee_size,
                'location': location,
                'embeddings': reduced_embedding.tolist()  # Convert to list for JSON serialization
            }

            # Send embeddings to the Pinecone queue
            send_to_pinecone_queue(message, PINECONE_QUEUE_URL)
        else:
            print(f"Failed to generate embeddings for {company_name} - {company_website}")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Embedding processing completed')
    }

def get_openai_embedding(text, client):
    """Generate embeddings using the OpenAI API."""
    try:
        # Call OpenAI API to generate embeddings
        response = client.embeddings.create(
            input=[text],
            model="text-embedding-3-small"
        )

        # Debugging: Print out the response structure
        print(f"OpenAI response: {response}")

        if hasattr(response, 'data'):
            embedding = response.data[0].embedding
            return embedding
        else:
            print("No 'data' field in the OpenAI response.")
            return None

    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        return None


def send_to_pinecone_queue(message, queue_url):
    """Send the embeddings and metadata to the Pinecone queue."""
    try:
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message)
        )
        print(f"Sent message to Pinecone queue: {response['MessageId']}")
    except Exception as e:
        print(f"Failed to send message to Pinecone queue: {str(e)}")
