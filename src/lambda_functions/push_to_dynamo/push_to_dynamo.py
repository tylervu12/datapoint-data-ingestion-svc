import json
import os
import boto3
from boto3.dynamodb.conditions import Key

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')

# Initialize SQS client
sqs = boto3.client('sqs')

def lambda_handler(event, context):
    # Extract environment variables
    DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME')  # DynamoDB table name

    # Initialize DynamoDB Table
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)

    # Process each SQS message
    for record in event['Records']:
        message_body = json.loads(record['body'])

        # Extract metadata and unique ID from the message
        unique_id = message_body['id']
        company_name = message_body['company_name']
        company_website = message_body['company_website']
        employee_size = message_body['employee_size']
        location = message_body['location']

        # Create the item to insert into DynamoDB
        item = {
            'id': unique_id,  # Partition key
            'company_name': company_name,
            'company_website': company_website,
            'employee_size': employee_size,
            'location': location
        }

        # Insert the item into DynamoDB
        try:
            table.put_item(Item=item)
            print(f"Successfully inserted item into DynamoDB: {unique_id}")
        except Exception as e:
            print(f"Failed to insert item into DynamoDB: {str(e)}")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Metadata inserted into DynamoDB')
    }
