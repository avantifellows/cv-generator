# main.tf

# Configure the AWS provider
provider "aws" {
  region = var.aws_region
}

# Configure the Cloudflare provider
provider "cloudflare" {
  email   = var.cloudflare_email
  api_key = var.cloudflare_api_key
}

# Get the Cloudflare zone
data "cloudflare_zone" "main" {
  name = var.cloudflare_zone_name
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

# S3 bucket for storing Terraform state
# Note: The S3 bucket must be created manually before you run `terraform init`.
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }

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
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# IAM Role that our Lambda function will use
resource "aws_iam_role" "lambda_exec_role" {
  name = "${var.project_name}-lambda-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
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
  image_uri = "${aws_ecr_repository.cv_generator_repo.repository_url}:${null_resource.docker_build_and_push.triggers.source_hash}"

  # This ensures the Lambda function is only updated after a new image is pushed
  depends_on = [null_resource.docker_build_and_push]
}

# Create a hash of all application files to use as a trigger
data "archive_file" "source_code" {
  type        = "zip"
  source_dir  = path.module
  output_path = "${path.module}/source.zip"
  excludes = toset([
    "main.tf",
    "source.zip",
    ".terraform",
    "terraform-backend",
    "*.tfstate*",
    ".terraform.lock.hcl",
    ".git",
    "terraform.tfvars"
  ])
}

# This resource builds and pushes the Docker image when source code changes
resource "null_resource" "docker_build_and_push" {
  # This trigger ensures the resource re-runs when our code changes
  triggers = {
    source_hash = data.archive_file.source_code.output_sha
  }

  # This provisioner runs the actual shell commands
  provisioner "local-exec" {
    command = <<-EOT
      aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${aws_ecr_repository.cv_generator_repo.repository_url}
      docker build --platform linux/amd64 -t ${aws_ecr_repository.cv_generator_repo.repository_url}:${self.triggers.source_hash} .
      docker push ${aws_ecr_repository.cv_generator_repo.repository_url}:${self.triggers.source_hash}
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

# Custom domain name for API Gateway using existing certificate
resource "aws_apigatewayv2_domain_name" "cv_generator_domain" {
  domain_name = "${var.domain}.${var.cloudflare_zone_name}"

  domain_name_configuration {
    certificate_arn = var.acm_certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
}

# Map the custom domain to the API Gateway
resource "aws_apigatewayv2_api_mapping" "cv_generator_mapping" {
  api_id      = aws_apigatewayv2_api.lambda_api.id
  domain_name = aws_apigatewayv2_domain_name.cv_generator_domain.id
  stage       = "$default"
}

# Create DNS record in Cloudflare pointing to the API Gateway domain
resource "cloudflare_record" "cv_generator_dns" {
  zone_id = data.cloudflare_zone.main.id
  name    = var.domain
  value   = aws_apigatewayv2_domain_name.cv_generator_domain.domain_name_configuration[0].target_domain_name
  type    = "CNAME"
  ttl     = 300
}

# Output the URL of our deployed application
output "api_url" {
  description = "The URL of the API Gateway endpoint."
  value       = aws_apigatewayv2_api.lambda_api.api_endpoint
}

output "custom_domain_url" {
  description = "The URL of the custom domain."
  value       = "https://${var.domain}.${var.cloudflare_zone_name}"
}