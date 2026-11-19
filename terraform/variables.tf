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

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small" # Smallest that can handle Playwright
}

variable "key_pair_name" {
  description = "Name of existing AWS key pair for EC2 access"
  type        = string
  default     = "AvantiFellows"
}

variable "repo_url" {
  description = "Git repository URL to clone"
  type        = string
  default     = "https://github.com/your-username/cv-generator.git"
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token that can edit DNS of the zone only"
  type        = string
  sensitive   = true
  # No default on purpose: set via TF_VAR_cloudflare_api_token or terraform.tfvars
}

variable "cloudflare_zone_name" {
  description = "Cloudflare zone name (domain)"
  type        = string
  default     = "avantifellows.org"
}

variable "domain" {
  description = "Subdomain for cv generator"
  type        = string
  default     = "cv-generator"
}

variable "app_s3_bucket_name" {
  description = "S3 bucket name for application resume storage"
  type        = string
}

variable "app_s3_prefix" {
  description = "Optional S3 key prefix (e.g., env/)"
  type        = string
  default     = ""
}

variable "share_token_key" {
  description = "Secret key for share token encryption (keep private and stable)"
  type        = string
  sensitive   = true
}