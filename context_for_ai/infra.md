# CV Generator Infrastructure Documentation

## **Overview**

The CV Generator application is deployed on AWS using **Infrastructure as Code (IaC)** principles with Terraform. The infrastructure creates a complete, production-ready environment with automated application setup, domain management, and monitoring capabilities.

## **Architecture**

```
Internet
    │
    ▼
[Cloudflare DNS] ─── cv-generator.avantifellows.org
    │
    ▼
[AWS Elastic IP] ─── Static IP Address
    │
    ▼
[Security Group] ─── Firewall Rules
    │
    ▼
[EC2 Instance] ─── Ubuntu 22.04 LTS (t3.small)
    │
    ├── [Nginx] ─── HTTP→HTTPS redirect; Reverse Proxy (Port 443 → 8000)
    │
    └── [FastAPI App] ─── CV Generator Application (Port 8000)
         └── [S3 Bucket] ─── Resume draft storage (JSON objects)
```

## **Provider Configuration**

### **Terraform Requirements**
```hcl
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
}
```

### **Provider Setup**
- **AWS Provider**: Configured with region variable (default: ap-south-1)
- **Cloudflare Provider**: Configured with email and API key for DNS management

### **Remote Backend (Terraform State)**
- **S3 Backend**: Remote state stored in an S3 bucket with server-side encryption
- **DynamoDB Locking**: State locking via DynamoDB table
- The Terraform configuration uses a remote backend in the `terraform` block. Supporting resources are provisioned in `terraform/backend.tf` (S3 bucket with versioning and DynamoDB lock table).
```hcl
terraform {
  backend "s3" {
    bucket         = "cv-generator-terraform-state-moh8l579"
    key            = "terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "cv-generator-terraform-locks"
    encrypt        = true
  }
}
```

#### Backend bootstrap workflow
- Run `terraform apply` in `terraform/` with `backend.tf` present to provision the state bucket and lock table (it uses a random suffix for uniqueness).
- Copy the outputs into `terraform/backend-config.txt` (already included) or pass them via CLI flags.
- Initialize Terraform with the remote backend using one of:
  - `terraform init -backend-config=backend-config.txt`
  - or `terraform init -backend-config="bucket=<bucket>" -backend-config="region=<region>" -backend-config="dynamodb_table=<table>"`
- The repo currently includes an explicit `backend` block in `main.tf` pointing to the existing bucket.

## **Variables Configuration**

### **AWS Configuration Variables**
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `aws_region` | string | "ap-south-1" | AWS region for resource deployment |
| `project_name` | string | "cv-generator" | Project name for resource naming |
| `instance_type` | string | "t3.small" | EC2 instance type (minimum for Playwright) |
| `key_pair_name` | string | "AvantiFellows" | Existing AWS key pair name |

### **Application Variables**
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `repo_url` | string | "https://github.com/your-username/cv-generator.git" | Git repository URL to clone |
| `app_s3_bucket_name` | string | (required) | S3 bucket for resume drafts |
| `app_s3_prefix` | string | "" | Optional S3 key prefix (e.g., `prod/`) |
| `share_token_key` | string | (required, sensitive) | Secret used to generate reversible, tokenized share URLs |

### **Cloudflare Variables**
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `cloudflare_email` | string | (required) | Cloudflare account email |
| `cloudflare_api_key` | string | (required, sensitive) | Cloudflare API key |
| `cloudflare_zone_name` | string | "avantifellows.org" | Domain zone name |
| `domain` | string | "cv-generator" | Subdomain for the application |

## **Data Sources**

### **Ubuntu AMI**
```hcl
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}
```
- **Purpose**: Automatically selects the latest Ubuntu 22.04 LTS AMI
- **Owner**: Canonical (official Ubuntu images)
- **Type**: HVM virtualization for modern EC2 instances

### **Existing Key Pair**
```hcl
data "aws_key_pair" "existing_key" {
  key_name = var.key_pair_name
}
```
- **Purpose**: References existing AWS key pair for SSH access
- **Requirement**: Key pair must exist in the AWS account before deployment

### **Cloudflare Zone**
```hcl
data "cloudflare_zone" "main" {
  name = var.cloudflare_zone_name
}
```
- **Purpose**: Gets zone ID for DNS record creation
- **Requirement**: Domain must be managed by Cloudflare

## **Security Group Configuration**

### **Ingress Rules (Inbound Traffic)**
| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 22 | TCP | 0.0.0.0/0 | SSH access for administration |
| 80 | TCP | 0.0.0.0/0 | HTTP traffic (redirects to HTTPS) |
| 443 | TCP | 0.0.0.0/0 | HTTPS traffic (SSL/TLS encrypted) |
| 8000 | TCP | 0.0.0.0/0 | FastAPI direct access (debugging) |

### **Egress Rules (Outbound Traffic)**
- **All traffic**: 0.0.0.0/0 on all ports and protocols
- **Purpose**: Downloads, updates, API calls, etc.

### **Security Considerations**
- ⚠️ **SSH Access**: Currently open to all IPs (consider restricting to specific IPs)
- ⚠️ **Port 8000**: Exposed for debugging (consider removing in production)
- ✅ **Standard Ports**: HTTP/HTTPS properly configured with SSL termination
- ✅ **SSL/TLS**: Let's Encrypt certificates with automatic renewal

## **IAM Configuration**

### **EC2 IAM Role**
```hcl
resource "aws_iam_role" "ec2_role" {
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}
```

### **Instance Profile**
- **Purpose**: Allows EC2 instance to assume the IAM role
- **Current Permissions**: S3 access for resume storage + EC2 assume role

### **Application S3 Access Policy**
The instance role is granted restricted access to the application bucket:
```hcl
data "aws_iam_policy_document" "app_s3_access" {
  statement {
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.app_bucket.arn]
  }

  statement {
    actions = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = [
      "${aws_s3_bucket.app_bucket.arn}/${var.app_s3_prefix}/resumes/*",
      "${aws_s3_bucket.app_bucket.arn}/${var.app_s3_prefix}/metadata/*"
    ]
  }
}
```
Notes:
- Bucket versioning and AES-256 server-side encryption are enabled.
- Public access is fully blocked on the application bucket.

## **EC2 Instance Configuration**

### **Instance Specifications**
- **AMI**: Latest Ubuntu 22.04 LTS (dynamic selection)
- **Instance Type**: t3.small (2 vCPU, 2 GB RAM)
- **Key Pair**: Existing key pair for SSH access
- **Security Group**: Custom security group with defined rules
- **IAM Profile**: Attached instance profile for future AWS integrations

### **Storage Configuration**
- **Volume Type**: GP3 SSD (latest generation)
- **Volume Size**: 20 GB
- **Encryption**: Enabled for data security
- **Performance**: Baseline 3,000 IOPS, 125 MB/s throughput

### **User Data Script**
- **Purpose**: Automated application setup on instance launch
- **Format**: Multipart MIME for complex initialization
- **Logging**: Complete setup process logged to `/var/log/user-data.log`
- **Idempotent**: Can run multiple times safely without completion markers
- **SSL Automation**: Automatic Let's Encrypt certificate generation and renewal
- **Environment Variables**: Injects `RESUME_STORAGE_TYPE=s3`, `S3_BUCKET_NAME`, `S3_PREFIX`, `AWS_REGION`, `SHARE_TOKEN_KEY` into systemd service

## **Elastic IP Configuration**

### **Static IP Assignment**
```hcl
resource "aws_eip" "cv_generator_eip" {
  instance = aws_instance.cv_generator.id
  domain   = "vpc"
}
```

### **Benefits**
- **Static IP**: IP address persists through instance stops/starts
- **DNS Stability**: Consistent IP for DNS records
- **Cost**: Free while attached to running instance

## **DNS Configuration**

### **Cloudflare DNS Record**
```hcl
resource "cloudflare_record" "cv_generator_dns" {
  zone_id = data.cloudflare_zone.main.id
  name    = var.domain
  content = aws_eip.cv_generator_eip.public_ip
  type    = "A"
  ttl     = 300
}
```

### **DNS Settings**
- **Record Type**: A record (IPv4 address)
- **TTL**: 300 seconds (5 minutes) for quick updates
- **Dynamic**: Automatically points to Elastic IP
- **Proxying**: Record is DNS-only by default (not proxied). Enable Cloudflare proxying if desired for additional features.
- **Result**: `cv-generator.avantifellows.org` → Elastic IP

## **SSL Certificate Configuration**

### **Let's Encrypt Integration**
```bash
# Automated certificate generation
certbot --nginx -d ${domain} --non-interactive --agree-tos --email admin@${domain} --redirect
```

### **Certificate Management**
- **Certificate Authority**: Let's Encrypt
- **Certificate Path**: `/etc/letsencrypt/live/${domain}/fullchain.pem`
- **Private Key Path**: `/etc/letsencrypt/live/${domain}/privkey.pem`
- **Validity**: 90 days with automatic renewal
- **Auto-Renewal**: systemd timer runs `certbot renew` (enabled via `certbot.timer`)
- **Deployment**: Automatic Nginx configuration with SSL termination and HTTP→HTTPS redirect

### **SSL Security Features**
- **Protocols**: TLS 1.2 and TLS 1.3 only
- **Ciphers**: Modern ECDHE and AES cipher suites
- **HSTS**: Strict-Transport-Security header (1 year)
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, X-XSS-Protection
- **HTTP Redirect**: All HTTP traffic automatically redirects to HTTPS (301)

## **User Data Script Analysis**

### **Script Structure**
The user data script is a **multipart MIME document** with two sections:
1. **Cloud-config**: Sets up cloud-final modules
2. **Shell script**: Main installation and configuration

### **Installation Process**

#### **1. System Preparation**
```bash
# System updates
apt-get update && apt-get upgrade -y

# Core packages installation
apt-get install -y python3.11 python3.11-venv python3-pip nginx git curl \
                   unzip software-properties-common supervisor certbot \
                   python3-certbot-nginx build-essential libffi-dev libssl-dev
```

#### **2. Node.js Installation**
```bash
# Node.js 18.x for Playwright dependencies
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
apt-get install -y nodejs
```

#### **2.5. AWS CLI Installation**
```bash
# AWS CLI v2 for S3-backed draft storage and future operations (idempotent)
if ! command -v aws &> /dev/null; then
  cd /tmp
  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
  unzip -q awscliv2.zip
  ./aws/install
  rm -rf awscliv2.zip aws/
fi
```

#### **3. Application User Setup**
```bash
# Create dedicated application user
useradd -m -s /bin/bash cvapp
usermod -aG sudo cvapp

# Application directory
mkdir -p /home/cvapp/app
chown cvapp:cvapp /home/cvapp/app
```

#### **4. Application Deployment**
```bash
# Git repository cloning with branch management
if [ ! -d "/home/cvapp/app/.git" ]; then
    sudo -u cvapp git clone ${repo_url} app
    sudo -u cvapp git checkout new-feature-branch
else
    # Handle existing repository
    sudo -u cvapp git stash
    sudo -u cvapp git checkout new-feature-branch
    sudo -u cvapp git pull origin new-feature-branch
fi
```

#### **5. Python Environment Setup**
```bash
# Virtual environment creation
sudo -u cvapp python3.11 -m venv venv
sudo -u cvapp /home/cvapp/app/venv/bin/pip install --upgrade pip

# Dependencies installation
sudo -u cvapp /home/cvapp/app/venv/bin/pip install -r requirements.txt
```

#### **6. Playwright Installation**
```bash
# System-level browser dependencies
/home/cvapp/app/venv/bin/python -m playwright install-deps chromium

# Browser installation for application user
sudo -u cvapp /home/cvapp/app/venv/bin/playwright install chromium

# Permissions setup
chown -R cvapp:cvapp /home/cvapp/.cache/
```

#### **7. SystemD Service Configuration**
```bash
# FastAPI service definition
cat > /etc/systemd/system/cv-generator.service << 'EOL'
[Unit]
Description=CV Generator FastAPI application
After=network.target

[Service]
Type=simple
User=cvapp
Group=cvapp
WorkingDirectory=/home/cvapp/app
Environment=PATH=/home/cvapp/app/venv/bin
Environment=PYTHONPATH=/home/cvapp/app
Environment=RESUME_STORAGE_TYPE=s3
Environment=S3_BUCKET_NAME=${app_s3_bucket_name}
Environment=S3_PREFIX=${app_s3_prefix}
Environment=AWS_REGION=${aws_region}
Environment=SHARE_TOKEN_KEY=${share_token_key}
ExecStart=/home/cvapp/app/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOL
```

#### **8. Nginx Configuration**
 - Conditional setup: If no SSL certificate exists on first boot, Nginx starts in HTTP-only mode. After Certbot obtains a certificate, the configuration is updated to HTTPS with HTTP→HTTPS redirection.
```bash
# HTTP→HTTPS redirect and HTTPS reverse proxy configuration
cat > /etc/nginx/sites-available/cv-generator << 'EOL'
server {
    listen 80;
    server_name ${domain} _;

    # Redirect all HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ${domain} _;

    # SSL
    ssl_certificate /etc/letsencrypt/live/${domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${domain}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    location /static/ {
        alias /home/cvapp/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOL
```
Additional details:
- Static assets are served from `/home/cvapp/app/static/` with long-lived caching headers.
- `client_max_body_size 50M` allows larger form submissions if needed.

#### **9. Service Management**
```bash
# Enable and start services
systemctl daemon-reload
systemctl enable nginx cv-generator
systemctl restart nginx cv-generator

# Enable certbot timer for auto-renewal
systemctl enable certbot.timer
systemctl start certbot.timer

# Health verification
systemctl status nginx --no-pager
systemctl status cv-generator --no-pager
```

#### **10. Health Check Script**
```bash
# Automated health monitoring
cat > /home/cvapp/health-check.sh << 'EOL'
#!/bin/bash
echo "=== Health Check ==="
echo "Nginx status:" && systemctl is-active nginx
echo "CV Generator status:" && systemctl is-active cv-generator
echo "Port 8000 check:" && curl -s http://localhost:8000/health
echo "Port 80 check:" && curl -s http://localhost/health
echo "HTTPS check:" && curl -s https://localhost/health || echo "HTTPS check may require domain SNI; test https://<your-domain>/health"
EOL
```

### **Script Features**
- **Idempotency**: Can be run multiple times safely without completion markers
- **Error Handling**: Exits on any error (`set -e`)
- **Logging**: Complete process logged for debugging
- **Conditional Logic**: Checks existing installations before proceeding
- **Health Monitoring**: Built-in health check capabilities
- **SSL Automation**: Automatic Let's Encrypt certificate generation and renewal

### **Idempotent Operations**
- **Package Installation**: Uses apt's idempotent nature
- **User Creation**: Checks if `cvapp` user exists before creating
- **Repository Management**: Updates existing repo instead of re-cloning
- **SSL Certificates**: Detects existing certificates, skips if valid
- **Service Configuration**: Always updates configs, restarts services safely
- **Node.js Installation**: Checks if already installed before proceeding

## **Terraform Outputs**

### **Instance Information**
| Output | Description | Example Value |
|--------|-------------|---------------|
| `instance_id` | EC2 instance ID | `i-0123456789abcdef0` |
| `instance_public_ip` | Elastic IP address | `13.127.123.456` |
| `instance_public_dns` | AWS public DNS | `ec2-13-127-123-456.ap-south-1.compute.amazonaws.com` |

### **Access Information**
| Output | Description | Example Value |
|--------|-------------|---------------|
| `ssh_command` | Ready-to-use SSH command | `ssh -i ~/.ssh/AvantiFellows.pem ubuntu@13.127.123.456` |
| `application_url` | HTTPS IP access | `https://13.127.123.456` |
| `custom_domain_url` | HTTPS custom domain | `https://cv-generator.avantifellows.org` |
| `http_redirect_url` | HTTP URL that redirects to HTTPS | `http://cv-generator.avantifellows.org` |
| `app_s3_bucket_name` | Application S3 bucket name | `avantifellows-cv-generator-storage` |
| `app_s3_bucket_arn` | Application S3 bucket ARN | `arn:aws:s3:::avantifellows-cv-generator-storage` |

## **Deployment Process**

### **Prerequisites**
1. **AWS CLI** configured with appropriate credentials
2. **Terraform** installed (>= 1.0)
3. **AWS Key Pair** "AvantiFellows" exists in target region
4. **Cloudflare Account** with API access to target domain
5. **Git Repository** accessible for cloning

### **Configuration Steps**
```bash
# 1. Copy and configure variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# 2. Initialize Terraform
terraform init

# 3. Plan deployment
terraform plan

# 4. Apply infrastructure
terraform apply
```

### **Post-Deployment Verification**
```bash
# 1. SSH into instance
ssh -i ~/.ssh/AvantiFellows.pem ubuntu@<ELASTIC_IP>

# 2. Check service status
sudo systemctl status cv-generator nginx

# 3. Run health check
sudo -u cvapp /home/cvapp/health-check.sh

# 4. Test application
curl http://localhost:8000/health
curl http://localhost/health
```

## **Monitoring and Troubleshooting**

### **Log Locations**
| Component | Log Location | Purpose |
|-----------|--------------|---------|
| User Data | `/var/log/user-data.log` | Initial setup process |
| FastAPI | `journalctl -u cv-generator` | Application logs |
| Nginx | `/var/log/nginx/access.log` | HTTP access logs |
| Nginx Errors | `/var/log/nginx/error.log` | Nginx error logs |

### **Service Management Commands**
```bash
# Service status
sudo systemctl status cv-generator
sudo systemctl status nginx

# Service control
sudo systemctl restart cv-generator
sudo systemctl restart nginx
sudo systemctl reload nginx

# Log monitoring
sudo journalctl -u cv-generator -f
sudo tail -f /var/log/nginx/access.log
```

### **Common Issues and Solutions**

#### **Application Not Starting**
```bash
# Check Python environment
sudo -u cvapp /home/cvapp/app/venv/bin/python --version

# Check dependencies
sudo -u cvapp /home/cvapp/app/venv/bin/pip list

# Manual start for debugging
sudo -u cvapp /home/cvapp/app/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
```

#### **Playwright Issues**
```bash
# Reinstall Playwright browsers
sudo -u cvapp /home/cvapp/app/venv/bin/playwright install chromium

# Check browser installation
sudo -u cvapp /home/cvapp/app/venv/bin/playwright install --dry-run
```

#### **Nginx Configuration Issues**
```bash
# Test configuration
sudo nginx -t

# Reload configuration
sudo systemctl reload nginx

# Check site configuration
cat /etc/nginx/sites-available/cv-generator
```

## **Security Considerations**

### **Current Security Measures**
- ✅ **Encrypted Storage**: EBS volumes encrypted at rest
- ✅ **IAM Roles**: Proper role-based access for EC2
- ✅ **Service User**: Application runs as non-root user
- ✅ **Firewall**: Security group controls network access
- ✅ **SSL/TLS**: HTTPS with Let's Encrypt certificates and automatic renewal
- ✅ **Security Headers**: HSTS, X-Frame-Options, XSS protection
- ✅ **HTTP Redirect**: All traffic forced to HTTPS with 301 redirects

### **Security Recommendations**
- 🔒 **SSH Access**: Restrict SSH to specific IP addresses
- 🔒 **Port 8000**: Remove direct FastAPI access in production
- 🔒 **Updates**: Regular system and dependency updates
- 🔒 **Monitoring**: Implement log monitoring and alerting
- 🔒 **Certificate Monitoring**: Monitor SSL certificate expiration (auto-renewal enabled)

## **Application Storage Topology**

- Resume drafts (in-progress data) are stored in the S3 application bucket under `${S3_PREFIX}resumes/` with metadata at `${S3_PREFIX}metadata/resume_metadata.json`.
- Generated CVs (`generated/{cv_id}.html`, `generated/{cv_id}_display.html`, `generated/{cv_id}_data.json`) are stored on the instance filesystem; PDFs are rendered on demand and not persisted.
- Environment variables for the service are injected via systemd: `RESUME_STORAGE_TYPE`, `S3_BUCKET_NAME`, `S3_PREFIX`, `AWS_REGION`, `SHARE_TOKEN_KEY`.

## **Cost Optimization**

### **Current Monthly Costs (Estimated)**
| Resource | Cost | Notes |
|----------|------|-------|
| t3.small instance | ~$15-20 | 24/7 operation |
| EBS storage (20GB) | ~$2 | GP3 SSD |
| Elastic IP | $0 | Free while attached |
| **Total** | **~$17-22** | Per month |

### **Cost Optimization Options**
- **Scheduled Shutdown**: Stop instance during low-usage periods
- **Reserved Instances**: 1-year commitment for ~40% savings
- **Spot Instances**: For development environments (not recommended for production)

## **Disaster Recovery**

### **Backup Strategy**
- **Infrastructure**: Terraform state provides infrastructure backup
- **Application Data**: Stored in `generated/` directory (consider S3 backup)
- **Configuration**: All configuration in version control

### **Recovery Process**
1. **Infrastructure Recovery**: `terraform apply` recreates entire infrastructure
2. **Data Recovery**: Restore from S3 backup (when implemented)
3. **DNS Recovery**: Automatic with Terraform-managed Cloudflare records

## **Future Enhancements**

### **Completed Infrastructure Improvements**
- ✅ **SSL/TLS**: Automated certificate management with Let's Encrypt
- ✅ **Security Headers**: HSTS, XSS protection, and content security
- ✅ **HTTPS Enforcement**: Automatic HTTP to HTTPS redirects
- ✅ **Idempotent Deployment**: Safe multi-run user data scripts
- ✅ **S3-backed Resume Storage**: Private bucket with versioning, SSE, and IAM role access; systemd service configured with S3 env vars

### **Planned Infrastructure Improvements**
- **S3 Integration**: Persistent storage for generated CVs (drafts done)
- **Load Balancer**: Multiple instance support
- **Auto Scaling**: Dynamic capacity management
- **CDN**: CloudFront for static asset delivery
- **Monitoring**: CloudWatch dashboards and alarms

### **Security Enhancements**
- **VPC**: Custom networking with private subnets
- **NAT Gateway**: Secure outbound internet access
- **WAF**: Web application firewall
- **Secrets Manager**: Secure credential storage

This infrastructure provides a robust, scalable foundation for the CV Generator application with automated deployment, monitoring capabilities, and room for future enhancements. 