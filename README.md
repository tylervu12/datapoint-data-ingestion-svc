# Datapoint Data Ingestion Service

## Overview

`datapoint-data-ingestion-svc` is a scalable data ingestion pipeline designed to handle large datasets of company information. The pipeline processes CSV files, scrapes company websites, converts the text into embeddings using OpenAI's embeddings API, and stores both the embeddings and associated metadata in Pinecone for fast similarity search. Metadata is also stored in DynamoDB for efficient querying and management.

The pipeline leverages AWS services such as Lambda, S3, SQS, Step Functions, and Pinecone to ensure scalability, cost-efficiency, and reliability.

### Key Features
- **CSV Ingestion**: Process CSV files containing company data (company name, website, employee size, location) from an S3 bucket.
- **Website Scraping**: Scrape company websites for text content.
- **Embeddings Generation**: Convert scraped text into embeddings using OpenAI API and upsert them into Pinecone with metadata.
- **Retry Logic**: Built-in retry mechanisms for handling timeouts and errors in scraping, embedding generation, and upsertion.
  
## Project Structure

## Project Structure

```bash
datapoint-data-ingestion-svc/
│
├── README.md                # Project documentation
├── requirements.txt         # Python dependencies
├── cdk/                     # AWS CDK stack 
├── src/                     # Source code for Lambda functions
├── tests/                   # Unit tests for Lambda functions
├── lambda_layers/           # Custom built Lambda layers
└── venv/                    # Python virtual environment
```

## Prerequisites

- Python 3.8+
- AWS CLI installed and configured
- Node.js for AWS CDK
- AWS account with access to services like S3, Lambda, SQS, and Pinecone

## Deployment Instructions

Follow these steps to deploy the `datapoint-data-ingestion-svc` pipeline:

### Step 1: Clone the Repository

```bash
git clone https://github.com/tylervu12/datapoint-data-ingestion-svc.git
cd datapoint-data-ingestion-svc
```

### Step 2: Set Up Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 3: Configure AWS Credentials

Make sure your AWS CLI is configured with the necessary credentials and region:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 4: Deploy the AWS Infrastructure

This project uses AWS CDK to define and deploy the infrastructure. Run the following commands to deploy:

1. Install AWS CDK if not already installed:

```bash
npm install -g aws-cdk
```

2. Bootstrap your AWS environment for CDK:

```bash
cdk bootstrap
```

3. Deploy the stack:

```bash
cdk deploy
```

## Step 5: Testing the Lambda Functions

You can invoke Lambda functions manually by uploading a test CSV file to the specified S3 bucket. Use the AWS Console or AWS CLI to trigger the functions with a test event.

#### Running Unit Tests

To run the unit tests in the `tests` directory using `unittest`, by making sure you are in the root directory of the project and running the following command:

```bash
python -m unittest discover -s tests
```
