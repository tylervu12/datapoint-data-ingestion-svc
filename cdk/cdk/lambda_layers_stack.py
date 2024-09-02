from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
)
from constructs import Construct
import os

class LambdaLayersStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get the directory of the current file
        current_dir = os.path.dirname(os.path.realpath(__file__))

        # All-MiniLM-L6-v2 Layer
        all_minilm_l6_v2_layer_path = os.path.join(current_dir, "..", "..", "lambda_layers", "Modelall-MiniLM-L6-v2", "layer.zip")
        all_minilm_l6_v2_layer = lambda_.LayerVersion(
            self, "AllMiniLML6V2Layer",
            code=lambda_.Code.from_asset(all_minilm_l6_v2_layer_path),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_10],
            description="Layer containing all-MiniLM-L6-v2 model"
        )