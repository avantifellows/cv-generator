# Dockerfile

# Use the official AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.11

# Copy the application code and other necessary files
COPY app/ ./app/
COPY main.py .
COPY requirements.txt .
COPY templates/ ./templates/
COPY test_data_structured.json .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the command to run when the container starts.
# This tells Lambda to use the "handler" object in our "main.py" file.
CMD ["main.handler"]