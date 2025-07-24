# Dockerfile

# Use Ubuntu as base for better GLIBC compatibility, then add Lambda runtime
FROM ubuntu:22.04

# Set timezone to avoid interactive prompt
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install AWS Lambda Runtime Interface Client
RUN apt-get update && \
    apt-get install -y \
        python3.11 \
        python3.11-venv \
        python3-pip \
        curl \
        unzip \
        software-properties-common \
        && rm -rf /var/lib/apt/lists/*

# Install AWS Lambda Runtime Interface Client
RUN pip3 install awslambdaric

# Set up Lambda environment
ENV LAMBDA_TASK_ROOT=/var/task
ENV LAMBDA_RUNTIME_DIR=/var/runtime

# Set up working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy the application code and other necessary files
COPY app/ ./app/
COPY main.py .
COPY requirements.txt .
COPY templates/ ./templates/
COPY test_data_structured.json .

# Install system dependencies for Playwright
RUN apt-get update && \
    apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    libnss3-dev \
    libatk-bridge2.0-dev \
    libdrm-dev \
    libxkbcommon-dev \
    libgtk-3-dev \
    libgbm-dev \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install the Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Install Playwright browsers with dependencies
RUN playwright install chromium && \
    playwright install-deps chromium

# Set the entry point for AWS Lambda
ENTRYPOINT ["/usr/local/bin/python", "-m", "awslambdaric"]
CMD ["main.handler"]