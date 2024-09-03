#!/usr/bin/env python3
import os
import aws_cdk as cdk
from lib.cdk_stack import DataIngestionStack  # Adjusted import to match your file structure

app = cdk.App()

# Instantiate the DataIngestionStack
DataIngestionStack(app, "DataIngestionStack", 
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION') or 'us-west-2')
)

app.synth()
