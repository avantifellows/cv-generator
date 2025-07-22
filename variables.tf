variable "cloudflare_email" {
  description = "Cloudflare account email"
  type        = string
  # Set via environment variable CLOUDFLARE_EMAIL or terraform.tfvars
}

variable "cloudflare_api_key" {
  description = "Cloudflare API key"
  type        = string
  sensitive   = true
  # Set via environment variable CLOUDFLARE_API_KEY or terraform.tfvars
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

variable "acm_certificate_arn" {
  description = "ARN of the existing ACM certificate for *.avantifellows.org"
  type        = string
  default     = "arn:aws:acm:ap-south-1:111766607077:certificate/9a8f45c3-e386-4ef7-bf4b-659180eb638f"
} 