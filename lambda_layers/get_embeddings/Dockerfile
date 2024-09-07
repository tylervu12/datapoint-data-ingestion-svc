# Set the image to Python 3.8 that is compatible with AWS
FROM public.ecr.aws/lambda/python:3.8-arm64

# Set the working directory
WORKDIR /lambda

# Copy the requirements file
COPY requirements.txt .

# Install dependencies and create the layer
RUN yum update -y && \
    yum install -y zip gcc make && \
    pip install --upgrade pip && \
    pip install -r requirements.txt -t python/ && \
    zip -r layer.zip python/ && \
    rm -rf python/ && \
    yum clean all

# Create a dummy handler function (required by the base image)
RUN echo "def handler(event, context):\n    pass" > lambda_function.py

# Set the CMD to simply keep the container running
CMD ["lambda_function.handler"]