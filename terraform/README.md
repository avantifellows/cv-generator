# CV Generator EC2 Deployment

This terraform configuration deploys the CV Generator FastAPI application on a single EC2 instance with nginx reverse proxy.

## Architecture

- **EC2 Instance**: t3.small Ubuntu 22.04 LTS
- **Elastic IP**: Static IP address for the instance
- **Security Group**: Allows SSH (22), HTTP (80), HTTPS (443), and FastAPI (8000)
- **Nginx**: Reverse proxy from port 80 to FastAPI on port 8000
- **SystemD**: Service management for FastAPI application
- **Cloudflare DNS**: A record pointing to the Elastic IP

## Prerequisites

1. **AWS CLI configured** with your credentials
2. **AWS Key Pair**: Existing key pair "AvantiFellows" in your AWS account
3. **Cloudflare API Key**: For DNS management
4. **Git Repository**: Your CV generator code should be accessible via git clone

## Setup Instructions

### 1. Configure Variables

Copy the example variables file and fill in your values:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```bash
# AWS Configuration
aws_region = "ap-south-1"
project_name = "cv-generator"
instance_type = "t3.small"

# AWS Key Pair Name (existing key pair in your AWS account)
key_pair_name = "AvantiFellows"

# Git Repository URL
repo_url = "https://github.com/your-username/cv-generator.git"

# Cloudflare Configuration
cloudflare_email = "your-email@domain.com"
cloudflare_api_key = "your-cloudflare-api-key"
cloudflare_zone_name = "avantifellows.org"
domain = "cv-generator"
```

### 2. Ensure SSH Key Access

Make sure you have the private key file for the "AvantiFellows" key pair:
- The private key should be at `~/.ssh/AvantiFellows.pem`
- Set proper permissions: `chmod 400 ~/.ssh/AvantiFellows.pem`

### 3. Deploy Infrastructure

```bash
# Initialize terraform
terraform init

# Plan the deployment
terraform plan

# Apply the changes
terraform apply
```

### 4. Access Your Application

After deployment completes, terraform will output:

- **instance_public_ip**: The Elastic IP address
- **ssh_command**: Command to SSH into the instance
- **application_url**: Direct IP access URL
- **custom_domain_url**: Your custom domain URL

Example output:
```
instance_public_ip = "13.127.XXX.XXX"
ssh_command = "ssh -i ~/.ssh/AvantiFellows.pem ubuntu@13.127.XXX.XXX"
application_url = "http://13.127.XXX.XXX"
custom_domain_url = "http://cv-generator.avantifellows.org"
```

## Instance Setup Details

The EC2 instance is automatically configured with:

1. **System packages**: Python 3.11, nginx, git, Node.js
2. **Application setup**: 
   - Clones your repository to `/home/cvapp/app`
   - Creates Python virtual environment
   - Installs dependencies from requirements.txt
   - Installs Playwright with Chromium browser
3. **Service configuration**:
   - SystemD service for FastAPI app
   - Nginx reverse proxy configuration
4. **Health monitoring**: Health check script at `/home/cvapp/health-check.sh`

## Monitoring and Troubleshooting

### SSH into the instance:

```bash
ssh -i ~/.ssh/AvantiFellows.pem ubuntu@<ELASTIC_IP>
```

### Check service status:

```bash
# Check FastAPI service
sudo systemctl status cv-generator

# Check nginx
sudo systemctl status nginx

# Run health check
sudo -u cvapp /home/cvapp/health-check.sh
```

### View logs:

```bash
# FastAPI application logs
sudo journalctl -u cv-generator -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# User data script logs (setup process)
sudo tail -f /var/log/user-data.log
```

### Restart services:

```bash
# Restart FastAPI app
sudo systemctl restart cv-generator

# Restart nginx
sudo systemctl restart nginx
```

## Manual Updates

To update the application code:

```bash
# SSH into the instance
ssh -i ~/.ssh/AvantiFellows.pem ubuntu@<ELASTIC_IP>

# Switch to app user and update code
sudo su - cvapp
cd /home/cvapp/app
git pull origin main

# Install any new dependencies
./venv/bin/pip install -r requirements.txt

# Restart the service
sudo systemctl restart cv-generator
```

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

## Security Notes

- The security group allows access from all IPs (0.0.0.0/0) for HTTP and SSH
- Consider restricting SSH access to your IP address only
- The FastAPI port 8000 is also exposed for debugging; remove if not needed
- Consider setting up HTTPS with Let's Encrypt (certbot is pre-installed)

## Cost Estimate

- **t3.small instance**: ~$15-20/month
- **Elastic IP**: $0 (while attached to running instance)
- **EBS storage**: ~$2/month for 20GB

Total: ~$17-22/month 