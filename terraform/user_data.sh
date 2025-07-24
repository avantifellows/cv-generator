Content-Type: multipart/mixed; boundary="//"
MIME-Version: 1.0

--//
Content-Type: text/cloud-config; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Content-Disposition: attachment; filename="cloud-config.txt"

#cloud-config
cloud_final_modules:
- [scripts-user, always]

--//
Content-Type: text/x-shellscript; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Content-Disposition: attachment; filename="userdata.txt"

#!/bin/bash

# Exit on any error
set -e

# Log everything
exec > >(tee /var/log/user-data.log) 2>&1
echo "Starting user data script at $(date)"

# Update system (always safe to run)
apt-get update
apt-get upgrade -y

# Install required packages (idempotent)
apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    nginx \
    git \
    curl \
    unzip \
    software-properties-common \
    supervisor \
    certbot \
    python3-certbot-nginx \
    build-essential \
    libffi-dev \
    libssl-dev

# Install Node.js (check if already installed)
if ! command -v node &> /dev/null; then
    echo "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    apt-get install -y nodejs
else
    echo "Node.js already installed: $(node --version)"
fi

# Create application user (idempotent)
if ! id "cvapp" &>/dev/null; then
    echo "Creating cvapp user..."
    useradd -m -s /bin/bash cvapp
    usermod -aG sudo cvapp
else
    echo "cvapp user already exists"
fi

# Create application directory (idempotent)
mkdir -p /home/cvapp/app
chown cvapp:cvapp /home/cvapp/app

# Clone/update the repository
if [ ! -d "/home/cvapp/app/.git" ]; then
    echo "Cloning repository..."
    cd /home/cvapp
    sudo -u cvapp git clone ${repo_url} app
    cd /home/cvapp/app
    sudo -u cvapp git checkout new-feature-branch
else
    echo "Repository exists, updating..."
    cd /home/cvapp/app
    # Stash any uncommitted changes
    sudo -u cvapp git stash
    # Checkout the specific branch
    sudo -u cvapp git checkout new-feature-branch
    # Pull the latest changes from the branch
    sudo -u cvapp git pull origin new-feature-branch
fi

cd /home/cvapp/app

# Set up Python virtual environment (idempotent)
if [ ! -d "/home/cvapp/app/venv" ]; then
    echo "Creating Python virtual environment..."
    sudo -u cvapp python3.11 -m venv venv
fi
sudo -u cvapp /home/cvapp/app/venv/bin/pip install --upgrade pip

# Install Python dependencies (always update)
echo "Installing/updating Python dependencies..."
sudo -u cvapp /home/cvapp/app/venv/bin/pip install -r requirements.txt

# Install Playwright browser dependencies (idempotent)
echo "Installing Playwright dependencies..."
/home/cvapp/app/venv/bin/python -m playwright install-deps chromium

# Install Playwright browsers (idempotent)
sudo -u cvapp /home/cvapp/app/venv/bin/playwright install chromium

# Ensure proper permissions for Playwright cache
chown -R cvapp:cvapp /home/cvapp/.cache/ 2>/dev/null || true

# Create directories for generated files (idempotent)
sudo -u cvapp mkdir -p /home/cvapp/app/generated
sudo -u cvapp mkdir -p /home/cvapp/app/static

# Set proper permissions
chown -R cvapp:cvapp /home/cvapp/app

# Create systemd service for FastAPI (check if exists)
if [ ! -f /etc/systemd/system/cv-generator.service ]; then
    echo "Creating systemd service..."
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
ExecStart=/home/cvapp/app/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOL
else
    echo "systemd service already exists"
fi

# Configure nginx (always update configuration)
echo "Configuring Nginx..."
cat > /etc/nginx/sites-available/cv-generator << 'EOL'
server {
    listen 80;
    server_name ${domain} _;

    # Redirect all HTTP traffic to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ${domain} _;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/${domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${domain}/privkey.pem;
    
    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA:ECDHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES256-SHA256:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:DES-CBC3-SHA;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
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

# Enable the site (idempotent)
ln -sf /etc/nginx/sites-available/cv-generator /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Start and enable services
systemctl daemon-reload
systemctl enable nginx
systemctl enable cv-generator

systemctl restart nginx
systemctl restart cv-generator

# Wait a moment for services to start
sleep 5

# Check service status
systemctl status nginx --no-pager
systemctl status cv-generator --no-pager

# Obtain SSL certificate (only if not exists)
if [ ! -f "/etc/letsencrypt/live/${domain}/fullchain.pem" ]; then
    echo "Obtaining SSL certificate..."
    certbot --nginx -d ${domain} --non-interactive --agree-tos --email admin@${domain} --redirect
    
    # Set up automatic certificate renewal
    echo "Setting up automatic certificate renewal..."
    systemctl enable certbot.timer
    systemctl start certbot.timer
    
    # Test certificate renewal
    certbot renew --dry-run
else
    echo "SSL certificate already exists for ${domain}"
    # Ensure certbot timer is enabled
    systemctl enable certbot.timer
    systemctl start certbot.timer
fi

echo "Setup completed at $(date)"
echo "FastAPI app should be running on http://localhost:8000"
echo "Nginx should be proxying on port 80 and redirecting to HTTPS on port 443"
echo "SSL certificate configured for ${domain}"

# Create a simple health check script (always update)
cat > /home/cvapp/health-check.sh << 'EOL'
#!/bin/bash
echo "=== Health Check ==="
echo "Nginx status:"
systemctl is-active nginx
echo "CV Generator status:"
systemctl is-active cv-generator
echo "Port 8000 check:"
curl -s http://localhost:8000/health || echo "FastAPI not responding"
echo "Port 80 check:"
curl -s http://localhost/health || echo "Nginx proxy not working"
echo "HTTPS check:"
curl -s https://localhost/health || echo "HTTPS not working"
EOL

chmod +x /home/cvapp/health-check.sh
chown cvapp:cvapp /home/cvapp/health-check.sh

echo "Health check script created at /home/cvapp/health-check.sh"
echo "Run it as: sudo -u cvapp /home/cvapp/health-check.sh"

--// 