import json
import requests
import os
import boto3
import time
from bs4 import BeautifulSoup

# Initialize SQS client
sqs = boto3.client('sqs')

def lambda_handler(event, context):

    # Environment variable for the next SQS queue (for embedding Lambda)
    EMBEDDING_QUEUE_URL = os.environ.get('EMBEDDING_QUEUE_URL')

    # Extract SQS messages (which come in batches)
    for record in event['Records']:
        message_body = json.loads(record['body'])
        company_website = message_body['company_website']
        company_name = message_body['company_name']
        employee_size = message_body['employee_size']
        location = message_body['location']

        # Scrape the website with retry logic
        scraped_text = scrape_website_with_retry(company_website)
        print(scraped_text)
        if scraped_text:
            print(f"Successfully scraped text for {company_name} - {company_website}")
            
            # Send scraped text to the next Lambda (via SQS)
            send_to_embedding_lambda({
                'company_name': company_name,
                'company_website': company_website,
                'employee_size': employee_size,
                'location': location,
                'scraped_text': scraped_text,
            })
        else:
            print(f"Failed to scrape text for {company_name} - {company_website}")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Scraping completed')
    }

def scrape_website_with_retry(url, max_retries=3, backoff_factor=2):
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url='https://app.scrapingbee.com/api/v1/',
                params={
                    'api_key': os.environ['SCRAPINGBEE_API_KEY'],
                    'url': url, 
                    'render_js': 'false'
                },
                timeout=30
            )
            if response.status_code == 200:
                # Parse the HTML content with BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")
                text = soup.get_text(separator=" ")
                return " ".join(text.split())  # Clean up the whitespace
            else:
                print(f"Failed to scrape {url}, status code: {response.status_code}")
        except requests.Timeout:
            print(f"Attempt {attempt + 1}: Request to scrape {url} timed out.")
        except Exception as e:
            print(f"Attempt {attempt + 1}: Error scraping {url}: {str(e)}")
        
        # Exponential backoff before retrying
        time.sleep(backoff_factor ** attempt)

    # Return None if all retries failed
    print(f"Failed to scrape {url} after {max_retries} attempts.")
    return None

def send_to_embedding_lambda(message):
    """Send the scraped text to the next Lambda for embedding conversion via SQS."""
    EMBEDDING_QUEUE_URL = os.environ.get('EMBEDDING_QUEUE_URL')  
    try:
        response = sqs.send_message(
            QueueUrl=EMBEDDING_QUEUE_URL,
            MessageBody=json.dumps(message)
        )
        print(f"Sent message to embedding Lambda SQS: {response['MessageId']}")
    except Exception as e:
        print(f"Failed to send message to embedding Lambda: {str(e)}")
