import boto3
import sagemaker
from sagemaker.huggingface import HuggingFaceModel
from sagemaker.serverless import ServerlessInferenceConfig  # Import the correct class

# Initialize boto3 session
boto3_session = boto3.Session(region_name='us-west-2')  # Change to your region
sagemaker_client = boto3_session.client('sagemaker')
sagemaker_runtime_client = boto3_session.client('sagemaker-runtime')
sagemaker_session = sagemaker.Session(boto_session=boto3_session)

# Specify IAM role
role = 'arn:aws:iam::891376972161:role/service-role/AmazonSageMaker-ExecutionRole-20240502T105629'

# Define model configuration
hub = {
    'HF_MODEL_ID':'sentence-transformers/all-MiniLM-L6-v2',
    'HF_TASK':'feature-extraction'
}

# Create HuggingFaceModel
huggingface_model = HuggingFaceModel(
    transformers_version='4.17',
    pytorch_version='1.10',
    py_version='py38',  # Use Python 3.8 for compatibility
    env=hub,
    role=role,
    sagemaker_session=sagemaker_session
)

# Configure serverless inference
serverless_config = ServerlessInferenceConfig(
    memory_size_in_mb=2048,
    max_concurrency=5
)

# Deploy the model using Serverless Inference
predictor = huggingface_model.deploy(
    serverless_inference_config=serverless_config,
    endpoint_name='miniLM-endpoint',
)
