from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_sqs as sqs,
    aws_s3_notifications as s3n,
    aws_iam as iam,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
)
from constructs import Construct

class DataIngestionStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define the S3 bucket where the CSV files will be uploaded
        csv_data_bucket = s3.Bucket(self, "CSVDataBucket")

        # Define the SQS queue for processing company data
        company_data_queue = sqs.Queue(
            self, 
            "CompanyDataQueue",
            queue_name="CompanyDataQueue"
        )

        # Define the Lambda function to parse the CSV and push messages to SQS
        parse_csv_to_sqs_lambda = _lambda.Function(
            self, "ParseCsvToSqsLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="parse_csv_to_sqs.lambda_handler",
            code=_lambda.Code.from_asset("../src/lambda_functions/parse_csv_to_sqs"),  
            environment={
                'QUEUE_URL': company_data_queue.queue_url
            }
        )

        # Grant the Lambda function permissions to interact with SQS and S3
        company_data_queue.grant_send_messages(parse_csv_to_sqs_lambda)
        csv_data_bucket.grant_read(parse_csv_to_sqs_lambda)

        # Add S3 event notification to trigger the Lambda function when a CSV file is uploaded
        csv_data_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(parse_csv_to_sqs_lambda),  
            s3.NotificationKeyFilter(suffix=".csv")
        )

""" import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))

PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
SAGEMAKER_ENDPOINT_NAME = os.getenv('SAGEMAKER_ENDPOINT_NAME')
SCRAPINGBEE_API_KEY = os.getenv('SCRAPINGBEE_API_KEY')
 """

""" 
        # Define the Lambda layer (push_embeddings_layer) created via Docker
        embeddings_layer = _lambda.LayerVersion(
            self, "EmbeddingsLayer",
            code=_lambda.Code.from_asset("../lambda_layers/push_embeddings_layer/layer.zip"),  # Path to the zip file
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_8, _lambda.Runtime.PYTHON_3_9, _lambda.Runtime.PYTHON_3_10]
        )

        ### Define the new Lambda function to handle SQS messages and process the embeddings
        process_embeddings_lambda = _lambda.Function(
            self, "ProcessEmbeddingsLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="process_embeddings.lambda_handler",  # Adjust this to the correct handler
            code=_lambda.Code.from_asset("../src/lambda_functions/process_embeddings"),  # Path to the new Lambda code
            layers=[
                _lambda.LayerVersion.from_layer_version_arn(
                    self, 'NumpySciPyLayer',
                    'arn:aws:lambda:us-west-2:420165488524:layer:AWSLambda-Python38-SciPy1x:107'  # ARN for the AWS Lambda layer with numpy and scipy
                ),
                embeddings_layer  
            ],  
            environment={
                'PINECONE_API_KEY': os.environ.get('PINECONE_API_KEY'),
                'SAGEMAKER_ENDPOINT_NAME': os.environ.get('SAGEMAKER_ENDPOINT_NAME'),
                'SCRAPINGBEE_API_KEY': os.environ.get('SCRAPINGBEE_API_KEY'),
                'QUEUE_URL': company_data_queue.queue_url
            },
            timeout=Duration.seconds(60)  # Set the timeout to 1 minute (60 seconds)
        )

        # Grant necessary permissions to interact with Sagemaker, Pinecone, and SQS
        process_embeddings_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "sagemaker:InvokeEndpoint",  # Allow invoking SageMaker endpoint
                    "sqs:ReceiveMessage",        # Allow reading from SQS
                    "sqs:DeleteMessage",
                    "sqs:GetQueueAttributes"
                ],
                resources=["*"]  # Restrict this to specific resources if needed
            )
        )

        # Add SQS as an event source to trigger the Lambda function
        process_embeddings_lambda.add_event_source(
            lambda_event_sources.SqsEventSource(company_data_queue)
        )
 """