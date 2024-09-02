import unittest
import boto3
import json
import numpy as np

class TestEmbeddingModel(unittest.TestCase):

    def setUp(self):
        # Initialize boto3 client for SageMaker runtime
        self.sagemaker_runtime = boto3.client('sagemaker-runtime', region_name='us-west-2')  # Adjust the region if necessary

        # Define the name of your SageMaker endpoint
        self.endpoint_name = 'miniLM-endpoint'  # Ensure this matches your actual endpoint name

    def test_embedding_mean(self):
        # Sample input data for testing
        text = """This is a sample sentence for embedding. In my most recent role as the founder of Datapoint, 
        I spearheaded the development of an innovative company lookalike model that leveraged NLP and machine learning techniques, 
        such as embeddings and GPT. This model allowed users to discover similar businesses using a single reference website, 
        setting Datapoint apart in the B2B data industry and generating $1.2 million in annual revenue. Our success and unique 
        approach led to the acquisition of the startup. Additionally, I engineered a comprehensive system to scrape and process text 
        data from over 10.5 million websites, which greatly enhanced our model's training and recommendation accuracy."""

        # Format the input as a JSON dictionary
        input_data = {"inputs": text}

        # Invoke the SageMaker endpoint
        response = self.sagemaker_runtime.invoke_endpoint(
            EndpointName=self.endpoint_name,
            ContentType='application/json',
            Body=json.dumps(input_data)
        )

        # Parse the response
        result = json.loads(response['Body'].read().decode())

        # Check the type and length of the first element inside result[0]
        first_element = result[0]

        # Convert the list of embeddings into a numpy array
        embeddings = np.array(first_element)

        # Calculate the mean of the embeddings
        mean_embedding = np.mean(embeddings, axis=0)

        # Assert that the resulting mean embedding has the correct shape
        self.assertEqual(mean_embedding.shape[0], 384, "Expected the mean embedding to have 384 dimensions.")

        # For demonstration, print the first few elements of the mean embedding
        print(f"Mean embedding (first 5 dimensions): {mean_embedding[:5]}")

if __name__ == '__main__':
    unittest.main()
