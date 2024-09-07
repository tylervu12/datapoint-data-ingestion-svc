import json
import boto3
import csv
import os
from urllib.parse import unquote_plus
import re

# Improved website formatting function
def format_websites(url):
    # Remove protocols, 'www.', and anything after the domain (e.g., /path)
    stripped_url = re.sub(r"^(https?://)?(www\.)?", "", url).split('/')[0]

    # If the domain ends with a slash, remove it
    if stripped_url.endswith('/'):
        stripped_url = stripped_url[:-1]

    # Return the properly formatted URL
    return f"https://www.{stripped_url}"

# Employee size bucket mapping function
def format_employee_size(employee_size):
    # Predefined employee size buckets
    valid_buckets = ['1-10', '11-50', '51-200', '201-500', '500+']

    # Check if employee_size is already in the correct format
    if employee_size in valid_buckets:
        return employee_size
    
    # Try to convert the value to a number and bucket it
    try:
        employee_size_int = int(employee_size)
        if employee_size_int <= 10:
            return '1-10'
        elif employee_size_int <= 50:
            return '11-50'
        elif employee_size_int <= 200:
            return '51-200'
        elif employee_size_int <= 500:
            return '201-500'
        else:
            return '500+'
    except ValueError:
        # If the value is not numeric or valid, return 'NA'
        return 'NA'

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
        # Format the website field
        formatted_website = format_websites(row['company_website'])

        # Format the employee size field
        formatted_employee_size = format_employee_size(row['employee_size'])

        # Check if the location is empty, set to 'NA' if it is
        location = row['location'] if row['location'] else 'NA'

        # Send each company’s data to SQS with the formatted website, employee size, and location
        message = {
            'company_name': row['company_name'],
            'company_website': formatted_website,
            'employee_size': formatted_employee_size,
            'location': location
        }
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message)
        )

    return {
        'statusCode': 200,
        'body': json.dumps('CSV file processed successfully!')
    }
