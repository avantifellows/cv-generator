# main.tf

# Configure the AWS provider
provider "aws" {
  region = var.aws_region
}

# Variables for our configuration
variable "aws_region" {
  description = "The AWS region to deploy resources in."
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "The name of the project, used for naming resources."
  type        = string
  default     = "cv-generator"
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

# S3 bucket for storing Terraform state
# Note: The S3 bucket must be created manually before you run `terraform init`.
terraform {
  backend "s3" {
    # This bucket name must be globally unique. You will create it manually.
    # We will provide instructions on this shortly.
    bucket         = "111766607077-cv-generator-tf-state-1"
    key            = "global/s3/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "terraform-locks"
  }
}




# ECR (Elastic Container Registry) to store our Docker image
resource "aws_ecr_repository" "cv_generator_repo" {
  name                 = "${var.project_name}-repo"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

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

# Create a hash of all application files to use as a trigger
data "archive_file" "source_code" {
  type        = "zip"
  source_dir  = "${path.module}/app"
  output_path = "${path.module}/source.zip"
}

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

# Output the URL of our deployed application
output "api_url" {
  description = "The URL of the API Gateway endpoint."
  value       = aws_apigatewayv2_api.lambda_api.api_endpoint
}