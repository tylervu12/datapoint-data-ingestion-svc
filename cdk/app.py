#!/usr/bin/env python3
import os
import aws_cdk as cdk
from cdk.lambda_layers_stack import LambdaLayersStack

app = cdk.App()
LambdaLayersStack(app, "LambdaLayersStack",
    env=cdk.Environment(account='891376972161', region='us-east-1'),
)

app.synth()