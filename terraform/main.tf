# Terraform configuration
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
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
  required_version = ">= 1.0"
  
  # S3 Backend configuration
  # This will be uncommented after initial backend setup
  backend "s3" {
    bucket         = "cv-generator-terraform-state-moh8l579"
    key            = "terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "cv-generator-terraform-locks"
    encrypt        = true
  }
}

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

# Get the latest Ubuntu 22.04 LTS AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Use existing key pair
data "aws_key_pair" "existing_key" {
  key_name = var.key_pair_name
}

# Create security group
resource "aws_security_group" "cv_generator_sg" {
  name_prefix = "${var.project_name}-sg"
  description = "Security group for CV Generator EC2 instance"

  # SSH access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP access
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS access
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # FastAPI development port (optional, for direct access)
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-security-group"
  }
}

# Create IAM role for EC2 instance (if needed for future AWS services)
resource "aws_iam_role" "ec2_role" {
  name = "${var.project_name}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-ec2-role"
  }
}

# Create instance profile
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_name}-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

# User data script for setting up the application
locals {
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    repo_url = var.repo_url
    domain   = "${var.domain}.${var.cloudflare_zone_name}"
  }))
}

# Create EC2 instance
resource "aws_instance" "cv_generator" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name              = data.aws_key_pair.existing_key.key_name
  vpc_security_group_ids = [aws_security_group.cv_generator_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  user_data = local.user_data

  root_block_device {
    volume_type = "gp3"
    volume_size = 20
    encrypted   = true
  }

  tags = {
    Name = "${var.project_name}-instance"
  }
}

# Create Elastic IP
resource "aws_eip" "cv_generator_eip" {
  instance = aws_instance.cv_generator.id
  domain   = "vpc"

  tags = {
    Name = "${var.project_name}-eip"
  }

  depends_on = [aws_instance.cv_generator]
}

# Create DNS record in Cloudflare pointing to the Elastic IP
resource "cloudflare_record" "cv_generator_dns" {
  zone_id = data.cloudflare_zone.main.id
  name    = var.domain
  content = aws_eip.cv_generator_eip.public_ip
  type    = "A"
  ttl     = 300
}

# Output the instance details
output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.cv_generator.id
}

output "instance_public_ip" {
  description = "Public IP address of the instance"
  value       = aws_eip.cv_generator_eip.public_ip
}

output "instance_public_dns" {
  description = "Public DNS name of the instance"
  value       = aws_instance.cv_generator.public_dns
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ~/.ssh/${var.key_pair_name}.pem ubuntu@${aws_eip.cv_generator_eip.public_ip}"
}

output "application_url" {
  description = "URL to access the application"
  value       = "https://${aws_eip.cv_generator_eip.public_ip}"
}

output "custom_domain_url" {
  description = "URL of the custom domain"
  value       = "https://${var.domain}.${var.cloudflare_zone_name}"
}

output "http_redirect_url" {
  description = "HTTP URL that redirects to HTTPS"
  value       = "http://${var.domain}.${var.cloudflare_zone_name}"
} 