from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_sqs as sqs,
    aws_s3_notifications as s3n,
    aws_lambda_event_sources as lambda_event_sources,  
    aws_dynamodb as dynamodb
)
from aws_cdk.aws_lambda import Architecture
from constructs import Construct
import os
from dotenv import load_dotenv

load_dotenv()

class DataIngestionStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define the S3 bucket where the CSV files will be uploaded
        csv_data_bucket = s3.Bucket(self, "CSVDataBucket")

        # Define the SQS queue for processing company data
        company_data_queue = sqs.Queue(
            self, 
            "CompanyDataQueue",
            queue_name="CompanyDataQueue",
            visibility_timeout=Duration.seconds(300) 
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

        # Define the Lambda Layer for the get_texts Lambda function
        get_texts_layer = _lambda.LayerVersion(
            self, "GetTextsLayer",
            code=_lambda.Code.from_asset("../lambda_layers/get_texts/layer.zip"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_8],
            description="Lambda layer containing libraries for get_texts Lambda"
        )

        # Define SQS for embedding generation
        embedding_queue = sqs.Queue(
            self, "EmbeddingQueue",
            queue_name="EmbeddingQueue",
            visibility_timeout=Duration.seconds(300) 
        )

        # Define the Lambda function to scrape websites and push results to the embedding queue
        get_texts_lambda = _lambda.Function(
            self, "get_texts",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="get_texts.lambda_handler",
            code=_lambda.Code.from_asset("../src/lambda_functions/get_texts"),  
            environment={
                'SCRAPINGBEE_API_KEY': os.environ['SCRAPINGBEE_API_KEY'],
                'EMBEDDING_QUEUE_URL': embedding_queue.queue_url
            },
            timeout=Duration.seconds(300),  # Adjust based on scraping needs
            memory_size=1024,  # Adjust based on expected load
            layers=[get_texts_layer]  # Attach the Lambda layer here
        )

        # Grant the scraping Lambda permissions to interact with SQS
        company_data_queue.grant_consume_messages(get_texts_lambda)
        embedding_queue.grant_send_messages(get_texts_lambda)

        # Trigger scraping Lambda when messages arrive in the company data SQS queue
        get_texts_lambda.add_event_source(
            lambda_event_sources.SqsEventSource(
                company_data_queue,
                batch_size=1  # Set batch size to scrape multiple websites at once
            )
        )

        # Define the SQS queue for Pinecone processing ---
        pinecone_queue = sqs.Queue(
            self, "PineconeQueue",
            queue_name="PineconeQueue",
            visibility_timeout=Duration.seconds(300)
        )

        # --- Define the Lambda Layer for the embedding to Pinecone Lambda function ---
        get_embeddings_layer = _lambda.LayerVersion(
            self, "GetEmbeddingsLayer",
            code=_lambda.Code.from_asset("../lambda_layers/get_embeddings/layer.zip"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_8],
            description="Lambda layer containing libraries for embedding processing"
        )

        # Define Lambda function for embedding processing (using OpenAI)
        get_embeddings_lambda = _lambda.Function(
            self, "EmbeddingToPineconeLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="get_embeddings.lambda_handler",
            code=_lambda.Code.from_asset("../src/lambda_functions/get_embeddings"),  
            environment={
                'OPENAI_API_KEY': os.environ['OPENAI_API_KEY'],  # OpenAI API Key
                'PINECONE_QUEUE_URL': pinecone_queue.queue_url   # Send to Pinecone queue after processing
            },
            timeout=Duration.seconds(300),  # Adjust timeout for long-running tasks
            memory_size=1024,  # Adjust memory based on the size of embeddings
            architecture=_lambda.Architecture.ARM_64,  # Use ARM architecture
            layers=[
                get_embeddings_layer, 
                _lambda.LayerVersion.from_layer_version_arn(
                    self, "AWSSDKPandasLayer",  # Updated the name of the layer reference
                    "arn:aws:lambda:us-west-2:336392948345:layer:AWSSDKPandas-Python38-Arm64:25"  # New AWS SDK Pandas layer ARN
                )
            ]
        )

        # Grant the embedding Lambda permissions to interact with SQS
        embedding_queue.grant_consume_messages(get_embeddings_lambda)
        pinecone_queue.grant_send_messages(get_embeddings_lambda)

        # Trigger the Lambda when messages arrive in the embedding SQS queue
        get_embeddings_lambda.add_event_source(
            lambda_event_sources.SqsEventSource(
                embedding_queue,
                batch_size=1  # Adjust batch size for embedding processing
            )
        )

        # --- Define the DynamoDB SQS queue ---
        dynamo_sqs_queue = sqs.Queue(
            self, "DynamoSQSQueue",
            queue_name="DynamoSQSQueue",
            visibility_timeout=Duration.seconds(300)  # Adjust based on processing needs
        )

        # --- Define the custom Lambda Layer for push_to_pinecone Lambda function ---
        push_to_pinecone_layer = _lambda.LayerVersion(
            self, "PushToPineconeLayer",
            code=_lambda.Code.from_asset("../lambda_layers/push_to_pinecone/layer.zip"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_8],
            description="Custom layer for push_to_pinecone Lambda"
        )

        # --- Define the new Lambda function for pushing to Pinecone and sending metadata ---
        push_to_pinecone_lambda = _lambda.Function(
            self, "PushToPineconeLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="push_to_pinecone.lambda_handler",
            code=_lambda.Code.from_asset("../src/lambda_functions/push_to_pinecone"),
            environment={
                'PINECONE_API_KEY': os.environ['PINECONE_API_KEY'],  # Pinecone API Key
                'PINECONE_INDEX_NAME': os.environ['PINECONE_INDEX_NAME'],  # Pinecone index name
                'DYNAMO_SQS_QUEUE_URL': dynamo_sqs_queue.queue_url  # Send metadata to Dynamo SQS queue
            },
            timeout=Duration.seconds(300),  # Adjust based on processing needs
            memory_size=1024,  # Adjust based on expected load
            layers=[
                push_to_pinecone_layer,  # Add custom layer
                _lambda.LayerVersion.from_layer_version_arn(
                    self, "SciPyLayer",  # Add the AWS SciPy layer
                    "arn:aws:lambda:us-west-2:420165488524:layer:AWSLambda-Python38-SciPy1x:107"
                )
            ]
        )

        # Grant permissions to push to the Dynamo SQS queue
        dynamo_sqs_queue.grant_send_messages(push_to_pinecone_lambda)

        # Trigger the new Lambda when messages arrive in the PineconeQueue
        push_to_pinecone_lambda.add_event_source(
            lambda_event_sources.SqsEventSource(
                pinecone_queue,
                batch_size=1  # Adjust batch size for processing needs
            )
        )

        # Define DynamoDB table
        dynamo_table = dynamodb.Table(
            self, "CompanyMetadataTable",
            table_name="CompanyMetadata",  # Name of the table
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY  # Change this if you don't want the table to be deleted when the stack is destroyed
        )

        # Define the Lambda function to send metadata to DynamoDB
        send_to_dynamo_lambda = _lambda.Function(
            self, "SendToDynamoLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="push_to_dynamo.lambda_handler",
            code=_lambda.Code.from_asset("../src/lambda_functions/push_to_dynamo"),
            environment={
                'DYNAMODB_TABLE_NAME': dynamo_table.table_name  
            },
            timeout=Duration.seconds(300),  # Adjust timeout if needed
            memory_size=1024  # Adjust memory as per requirements
        )

        # Grant permissions to the Lambda function to put items into DynamoDB
        dynamo_table.grant_write_data(send_to_dynamo_lambda)

        # Grant the Lambda function permissions to interact with the SQS queue
        dynamo_sqs_queue.grant_consume_messages(send_to_dynamo_lambda)

        # Trigger the Lambda when messages arrive in the Dynamo SQS queue
        send_to_dynamo_lambda.add_event_source(
            lambda_event_sources.SqsEventSource(
                dynamo_sqs_queue,
                batch_size=1  # Adjust batch size as needed
            )
        )
