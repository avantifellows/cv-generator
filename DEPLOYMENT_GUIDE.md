
# Guide: Deploying the CV Generator to AWS Lambda

This guide provides step-by-step instructions for deploying the CV Generator application to AWS Lambda using Terraform and GitHub Actions. This document is intended for a non-developer who is being assisted by an AI pair programmer.

## Table of Contents

1.  [Introduction: What We Are Building](#introduction-what-we-are-building)
2.  [Prerequisites: Tools You Need](#prerequisites-tools-you-need)
3.  [Step 1: Configure Your AWS Account](#step-1-configure-your-aws-account)
4.  [Step 2: Prepare the Application for Lambda](#step-2-prepare-the-application-for-lambda)
5.  [Step 3: Set Up Infrastructure with Terraform](#step-3-set-up-infrastructure-with-terraform)
6.  [Step 4: Build and Push a Docker Image](#step-4-build-and-push-a-docker-image)
7.  [Step 5: Deploy the Application](#step-5-deploy-the-application)
8.  [Step 6: Set Up Automated Deployment with GitHub Actions](#step-6-set-up-automated-deployment-with-github-actions)
9.  [Conclusion](#conclusion)

---

## Introduction: What We Are Building

We are going to take the "CV Generator" Python application and deploy it to the cloud. This will make it accessible to anyone with a web browser. We will use **AWS Lambda**, which is a "serverless" computing service. This means we can run our code without having to manage servers.

Here's a high-level overview of our plan:

*   **Package the app**: We will package our Python application into a Docker container. A container is like a self-contained box that has everything our application needs to run.
*   **Define Infrastructure as Code**: We will use a tool called **Terraform** to define all the AWS resources we need (like the Lambda function itself, an API endpoint, etc.). This is great because our entire infrastructure is defined in code, making it repeatable and easy to manage.
*   **Automate Deployments**: We will set up a **GitHub Actions workflow**. This will automatically update our application on AWS whenever we push new code to our main branch on GitHub.

By the end of this guide, you will have a fully functional, auto-deploying application running on AWS!

---

## Prerequisites: Tools You Need

Before we start, you need to have a few tools installed on your computer.

1.  **AWS CLI**: This is the command-line interface for Amazon Web Services. We'll use it to configure our credentials.
    *   **Installation**: Follow the official instructions for your operating system: [Installing the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html).

2.  **Terraform**: This is the tool we'll use to create and manage our cloud infrastructure.
    *   **Installation**: Follow the official HashiCorp instructions: [Install Terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli).

3.  **Docker Desktop**: This will let us build our application container locally before we send it to AWS.
    *   **Installation**: Download and install Docker Desktop from the official website: [Docker Desktop](https://www.docker.com/products/docker-desktop).

---

## Step 1: Configure Your AWS Account

Before we can deploy anything to AWS, we need to securely tell our computer how to access your AWS account. You should have been provided with an `Access Key ID` and a `Secret Access Key`.

1.  **Open your terminal** (on macOS, you can find it in `Applications/Utilities/Terminal.app`).

2.  **Run the AWS configure command**:
    ```bash
    aws configure
    ```

3.  **Enter your credentials**. The command will prompt you for four pieces of information.
    *   `AWS Access Key ID`: Paste the Access Key ID and press Enter.
    *   `AWS Secret Access Key`: Paste the Secret Access Key and press Enter.
    *   `Default region name`: Type `us-east-1` and press Enter. This is a popular default region, but you can choose another one if you prefer.
    *   `Default output format`: You can just press Enter to leave this blank.

You've now securely stored your AWS credentials. Your computer can now communicate with AWS on your behalf.

---

## Step 2: Prepare the Application for Lambda

Our FastAPI application needs a small modification to work with AWS Lambda. We'll use a library called **Mangum**. Mangum acts as a bridge between AWS Lambda's expected input and what our FastAPI application understands.

### 2.1 Install Mangum

First, let's add `mangum` to our project's dependencies.

1.  Open the `requirements.txt` file in your code editor.
2.  Add this line to the end of the file:
    ```
    mangum
    ```
3.  Save the file.

### 2.2 Refactor the Application

Now, we'll modify `main.py` to make it compatible with AWS Lambda using `Mangum`. This requires two small code changes. You can ask your AI assistant to help you apply them.

**1. Import `Mangum`**

At the top of `main.py`, where the other packages are imported, add this line:

```python
from mangum import Mangum
```

**2. Create the Lambda Handler**

Scroll to the very bottom of `main.py`. After the last function, add this line:

```python
handler = Mangum(app)
```

This line wraps your FastAPI application and exposes it in a way that AWS Lambda can understand.

Now that the application is ready, the next step is to define the infrastructure on AWS using Terraform.

---

## Step 3: Set Up Infrastructure with Terraform

Now for the exciting part! We will define all the AWS resources our application needs using **Terraform**. This approach is called **Infrastructure as Code (IaC)**, and it allows us to manage our infrastructure in a predictable and repeatable way.

You will create a single file named `main.tf` in the root of your project. The following sections will explain each part of the configuration. You will add all these code blocks sequentially into that one `main.tf` file. You can ask your AI assistant to help you put it all together.

### 3.1 Configure the AWS Provider and Variables

First, we need to tell Terraform that we're working with AWS and define some variables for easy configuration.

*   `provider "aws"`: Specifies that we are using the Amazon Web Services provider.
*   `variable "aws_region"`: A variable for the AWS region where we'll deploy our app (e.g., `us-east-1`).
*   `variable "project_name"`: A variable for our project's name, which helps keep our resources organized.

Add the following code to your `main.tf` file:
```terraform
# main.tf

# Configure the AWS provider
provider "aws" {
  region = var.aws_region
}

# Variables for our configuration
variable "aws_region" {
  description = "The AWS region to deploy resources in."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "The name of the project, used for naming resources."
  type        = string
  default     = "cv-generator"
}
```

### 3.2 Set Up the Terraform Backend for State Locking

Terraform keeps track of the infrastructure it manages in a special file called a **state file**. To work safely, especially in a team, we'll store this file remotely in an **S3 bucket**. We'll also use a **DynamoDB table** to "lock" the state file when someone is making changes, which prevents conflicts.

Add this configuration to your `main.tf` file:
```terraform
# S3 bucket for storing Terraform state
# Note: The S3 bucket must be created manually before you run `terraform init`.
terraform {
  backend "s3" {
    # This bucket name must be globally unique. You will create it manually.
    # We will provide instructions on this shortly.
    bucket         = "cv-generator-terraform-state-locking-bucket"
    key            = "global/s3/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
  }
}

# A DynamoDB table for state locking
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}
```

#### **Important Manual Step: Create the S3 Bucket**

Because S3 bucket names must be **globally unique**, you have to create this one manually before running Terraform.

1.  **Choose a unique bucket name**. A great way to ensure uniqueness is to prefix the name with your AWS Account ID (you can find this in the top-right corner of your AWS Console). For example: `123456789012-cv-generator-tf-state`.
2.  **Go to the S3 service in your AWS Console** and create a new bucket with that exact name.
3.  **Update `main.tf`**. In the `terraform` block you just added, change the `bucket` value from `"cv-generator-terraform-state-locking-bucket"` to the unique name you just created.

### 3.3 Create a Container Registry (ECR)

We need a place to store our application's Docker image. **Amazon Elastic Container Registry (ECR)** is a private Docker registry where we can securely keep our images.

Add this to your `main.tf` file:
```terraform
# ECR (Elastic Container Registry) to store our Docker image
resource "aws_ecr_repository" "cv_generator_repo" {
  name                 = "${var.project_name}-repo"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}
```

### 3.4 Create an IAM Role for the Lambda Function

Our Lambda function needs permission to run and to write logs to AWS CloudWatch for debugging. An **IAM Role** is a secure way to grant those permissions without hardcoding any credentials.

Add the following to your `main.tf` file:
```terraform
# IAM Role that our Lambda function will use
resource "aws_iam_role" "lambda_exec_role" {
  name = "${var.project_name}-lambda-exec-role"

  assume_role_policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRole",
      Effect    = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Attach the basic Lambda execution policy to the role
resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
```

### 3.5 Define the Lambda Function

This is the core of our serverless application. This resource tells AWS to create a Lambda function, connects it to the IAM role we just made, and, most importantly, specifies that its source code comes from the Docker image in our ECR repository.

Add this block to your `main.tf` file:
```terraform
# The Lambda function itself
resource "aws_lambda_function" "cv_generator_lambda" {
  function_name = "${var.project_name}-lambda"
  role          = aws_iam_role.lambda_exec_role.arn
  package_type  = "Image"
  timeout       = 30 # seconds

  # The image URI is now dynamically updated by our build resource
  image_uri = null_resource.docker_build_and_push.triggers.image_uri

  # This ensures the Lambda function is only updated after a new image is pushed
  depends_on = [null_resource.docker_build_and_push]
}
```

### 3.6 Automate Docker Image Building and Pushing

Instead of manually building and pushing the Docker image, we can have Terraform do it for us automatically! We'll use a `null_resource` with a `local-exec` provisioner. This will only run when it detects changes in our application code.

First, we need to create a "hash" of our source code files. This hash will change whenever we edit a file, which will trigger our resource.

Add the following to `main.tf`:
```terraform
# Create a hash of all application files to use as a trigger
data "archive_file" "source_code" {
  type        = "zip"
  source_dir  = "${path.module}/app"
  output_path = "${path.module}/source.zip"
}
```

Now, add the `null_resource` which will run the Docker commands. This is the magic that automates the build and push process.

```terraform
# This resource builds and pushes the Docker image when source code changes
resource "null_resource" "docker_build_and_push" {
  # This trigger ensures the resource re-runs when our code changes
  triggers = {
    source_hash = data.archive_file.source_code.output_sha
    image_uri   = "${aws_ecr_repository.cv_generator_repo.repository_url}:latest"
  }

  # This provisioner runs the actual shell commands
  provisioner "local-exec" {
    command = <<-EOT
      aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${aws_ecr_repository.cv_generator_repo.repository_url}
      docker build -t ${self.triggers.image_uri} .
      docker push ${self.triggers.image_uri}
    EOT
  }

  # This makes sure the ECR repo exists before we try to push to it
  depends_on = [aws_ecr_repository.cv_generator_repo]
}
```

### 3.7 Create an API Gateway to Expose the Lambda

Our Lambda function is created, but it's not accessible from the internet yet. We need an **API Gateway** to create a public HTTP endpoint (a URL) that, when visited, will trigger our Lambda function.

Add the final resources to your `main.tf` file:
```terraform
# API Gateway to create a public URL for our Lambda
resource "aws_apigatewayv2_api" "lambda_api" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"
  target        = aws_lambda_function.cv_generator_lambda.arn
}

# Grant API Gateway permission to invoke our Lambda function
resource "aws_lambda_permission" "api_gw_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cv_generator_lambda.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.lambda_api.execution_arn}/*/*"
}
```

### 3.8 Define an Output for the URL

Finally, we want Terraform to tell us the URL of our application after it's deployed. An `output` block is used for this.

Add this to the end of your `main.tf` file:
```terraform
# Output the URL of our deployed application
output "api_url" {
  description = "The URL of the API Gateway endpoint."
  value       = aws_apigatewayv2_api.lambda_api.api_endpoint
}
```

With all these pieces in your `main.tf` file, you have a complete, production-ready, and automated infrastructure definition for your application!

We are now ready to move on to packaging our application.

---

## Step 4: Create the Dockerfile

Our application will run inside a **Docker container** on AWS Lambda. The `Dockerfile` is the recipe for building that container. Even though Terraform will now automate the *building* and *pushing* of the image, we still need to provide this `Dockerfile`.

### 4.1 Create the Dockerfile

1.  In the root directory of your project, create a new file named `Dockerfile`.
2.  Copy and paste the following content into your `Dockerfile`:

```dockerfile
# Dockerfile

# Use the official AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.9

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
```

---

## Step 5: Deploy the Application

It's time to bring everything together! Thanks to our Terraform setup, the entire deployment process is now automated with a single command.

### 5.1 Initialize Terraform

Before you can use Terraform for the first time in a project, you need to initialize it. This command downloads the necessary provider plugins and sets up the S3 backend we configured. You only need to do this once.

1.  **Open your terminal** in the root directory of your project.
2.  **Run the init command**:
    ```bash
    terraform init
    ```
    If successful, you will see a message "Terraform has been successfully initialized!".

### 5.2 Apply the Terraform Configuration

Now, we'll tell Terraform to create (or update) all the resources defined in `main.tf`. This one command will now also build your Docker image and push it to ECR automatically.

1.  **Run the apply command**:
    ```bash
    terraform apply
    ```
2.  **Review the plan**. Terraform will show you a plan of all the resources it's going to create or change.
3.  **Confirm the plan**. If everything looks correct, type `yes` and press Enter.

Terraform will now create all the necessary AWS resources. If it detects a change in your source code, it will automatically rebuild and push your Docker image before updating the Lambda function. This might take a few minutes.

When it's finished, Terraform will print the `api_url` in your terminal. This is the public URL for your application!

### 5.3 Test Your Application

1.  **Find your API URL** by running `terraform output api_url`.
2.  **Open the URL** in your web browser. You should see the CV Generator form.

Congratulations! You have successfully deployed your application to AWS Lambda with a fully automated build and deployment process.

---

## Step 6: Set Up Automated Deployment with GitHub Actions

Manually building and pushing the Docker image every time you make a change is tedious. We can automate this entire process using **GitHub Actions**. We will create a workflow that automatically deploys your application whenever you push code to the `main` branch.

### 6.1 Create the GitHub Actions Workflow File

GitHub Actions workflows are defined in YAML files inside the `.github/workflows` directory.

1.  In your project's root directory, create a new directory named `.github`.
2.  Inside the `.github` directory, create another directory named `workflows`.
3.  Inside the `workflows` directory, create a new file named `deploy.yml`.

So, the final path will be `.github/workflows/deploy.yml`.

4.  Copy and paste the following code into your `deploy.yml` file:

```yaml
# .github/workflows/deploy.yml

name: Deploy CV Generator to AWS Lambda

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Set up Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_wrapper: false

      - name: Terraform Init
        id: init
        env:
            # this is needed to init the s3 backend
            AWS_BUCKET_NAME: ${{ secrets.AWS_BUCKET_NAME }}
        run: |
         sed -i 's/cv-generator-terraform-state-locking-bucket/${AWS_BUCKET_NAME}/' main.tf
         terraform init
      
      - name: Terraform Apply
        id: apply
        run: terraform apply -auto-approve

```

### 6.2 Add Secrets to Your GitHub Repository

Our workflow needs access to our AWS credentials to deploy on our behalf. It's very important to **never** store these secrets directly in your code. Instead, we use GitHub's encrypted secrets.

1.  Go to your GitHub repository in your browser.
2.  Click on the **Settings** tab.
3.  In the left sidebar, click on **Secrets and variables**, then **Actions**.
4.  Click the **New repository secret** button for each of the secrets below:
    *   `AWS_ACCESS_KEY_ID`: Your AWS Access Key ID.
    *   `AWS_SECRET_ACCESS_KEY`: Your AWS Secret Access Key.
    *   `AWS_BUCKET_NAME`: The name of the S3 bucket you created manually for terraform state locking.

### 6.3 How it Works

Now, whenever you push a change to your `main` branch on GitHub, this workflow will automatically:

1.  Check out your code.
2.  Configure AWS credentials.
3.  Initialize Terraform with the correct S3 backend.
4.  Run `terraform apply`. Terraform will see that the code has changed, build the new Docker image, push it to ECR, and update the Lambda function to use the new image, all in one step.

---

## Conclusion

You have successfully deployed a Python web application to AWS Lambda and set up a fully automated CI/CD pipeline. You can now make changes to your application, push them to GitHub, and watch as they are automatically deployed to the cloud.

This is a powerful setup that gives you a scalable, cost-effective, and easy-to-manage application. Congratulations on this achievement! 