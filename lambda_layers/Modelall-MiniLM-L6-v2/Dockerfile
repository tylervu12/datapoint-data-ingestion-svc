# Set the image to Python 3.10 that is compatible with AWS
FROM public.ecr.aws/lambda/python:3.10

# Set the working directory
WORKDIR /lambda

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt -t python/ && \
    yum update -y && \
    yum install -y zip && \
    zip -r layer.zip python/ && \
    rm -rf python/ && \
    yum clean all
