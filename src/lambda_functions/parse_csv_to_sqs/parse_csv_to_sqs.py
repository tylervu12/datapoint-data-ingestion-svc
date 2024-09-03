import json
import boto3
import csv
import os
from urllib.parse import unquote_plus

def lambda_handler(event, context):
    # Initialize the SQS client
    sqs = boto3.client('sqs')

    # Environment variable for the SQS queue URL
    QUEUE_URL = os.environ.get('QUEUE_URL')

    # Log the entire event object
    print(f"Received event: {json.dumps(event, indent=2)}")
    
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # URL-decode the key to handle special characters
    key = unquote_plus(key)
    
    print(f"Bucket: {bucket}, Key: {key}")
    
    # Download the CSV file from S3
    s3 = boto3.client('s3')
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
    except Exception as e:
        print(f"Error getting object {key} from bucket {bucket}. Error: {str(e)}")
        raise e
    
    content = response['Body'].read().decode('utf-8').splitlines()

    # Parse the CSV file
    csv_reader = csv.DictReader(content)
    for row in csv_reader:
        # Send each company’s data to SQS
        message = {
            'company_name': row['company_name'],
            'company_website': row['company_website'],
            'employee_size': row['employee_size'],
            'location': row['location']
        }
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message)
        )

    return {
        'statusCode': 200,
        'body': json.dumps('CSV file processed successfully!')
    }
