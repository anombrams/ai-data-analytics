#!/bin/bash

#############################################
# AI Data Portal - Automated Install Script
# Untuk Ubuntu 20.04 / 22.04
#############################################

set -e  # Exit on error

# Warna untuk output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fungsi print
print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[OK]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Banner
echo ""
echo "=============================================="
echo "   AI Data Portal - Installation Script"
echo "=============================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Script harus dijalankan sebagai root"
    echo "Jalankan: sudo bash install.sh"
    exit 1
fi

# Variables
APP_DIR="/var/www/ai_data_portal"
APP_USER="aiportal"
PYTHON_VERSION="python3"

# Step 1: Update system
print_status "Updating system packages..."
apt update && apt upgrade -y
print_success "System updated"

# Step 2: Install dependencies
print_status "Installing dependencies..."
apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    curl \
    htop \
    ufw
print_success "Dependencies installed"

# Step 3: Create app user
if id "$APP_USER" &>/dev/null; then
    print_warning "User $APP_USER already exists"
else
    print_status "Creating user $APP_USER..."
    useradd -m -s /bin/bash $APP_USER
    print_success "User $APP_USER created"
fi

# Step 4: Create app directory
print_status "Setting up application directory..."
mkdir -p $APP_DIR
chown -R $APP_USER:$APP_USER $APP_DIR
print_success "Directory $APP_DIR created"

# Step 5: Check if app files exist
if [ ! -f "$APP_DIR/app.py" ]; then
    print_warning "Application files not found in $APP_DIR"
    echo ""
    echo "Please upload your application files to $APP_DIR"
    echo "You can use SCP, SFTP, or Git to upload files"
    echo ""
    echo "Example with SCP (run from your local machine):"
    echo "  scp -r /path/to/ai_data_portal/* $APP_USER@YOUR_IP:$APP_DIR/"
    echo ""
    read -p "Press Enter after uploading files to continue, or Ctrl+C to exit..."
fi

# Step 6: Setup Python virtual environment
print_status "Setting up Python virtual environment..."
cd $APP_DIR
sudo -u $APP_USER $PYTHON_VERSION -m venv venv
sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip

if [ -f "$APP_DIR/requirements.txt" ]; then
    sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r requirements.txt
    print_success "Python packages installed"
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Step 7: Create .env file if not exists
if [ ! -f "$APP_DIR/.env" ]; then
    print_status "Creating .env file..."
    echo "# AI Data Portal Environment Variables" > $APP_DIR/.env
    echo "ANTHROPIC_API_KEY=your-api-key-here" >> $APP_DIR/.env
    chown $APP_USER:$APP_USER $APP_DIR/.env
    chmod 600 $APP_DIR/.env
    print_warning "Please edit $APP_DIR/.env and add your API key"
fi

# Step 8: Setup systemd service
print_status "Setting up systemd service..."
if [ -f "$APP_DIR/deploy/ai-data-portal.service" ]; then
    cp $APP_DIR/deploy/ai-data-portal.service /etc/systemd/system/
else
    # Create service file inline
    cat > /etc/systemd/system/ai-data-portal.service << 'EOF'
[Unit]
Description=AI Data Portal - Streamlit Application
After=network.target

[Service]
Type=simple
User=aiportal
Group=aiportal
WorkingDirectory=/var/www/ai_data_portal
Environment="PATH=/var/www/ai_data_portal/venv/bin"
EnvironmentFile=/var/www/ai_data_portal/.env
ExecStart=/var/www/ai_data_portal/venv/bin/python -m streamlit run app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true
Restart=always
RestartSec=10
NoNewPrivileges=true
PrivateTmp=true
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ai-data-portal

[Install]
WantedBy=multi-user.target
EOF
fi

systemctl daemon-reload
systemctl enable ai-data-portal
systemctl start ai-data-portal
print_success "Systemd service configured and started"

# Step 9: Setup Nginx
print_status "Setting up Nginx..."
if [ -f "$APP_DIR/deploy/nginx.conf" ]; then
    cp $APP_DIR/deploy/nginx.conf /etc/nginx/sites-available/ai-data-portal
else
    # Create nginx config inline
    cat > /etc/nginx/sites-available/ai-data-portal << 'EOF'
upstream ai_data_portal {
    server 127.0.0.1:8501;
}

server {
    listen 80;
    server_name _;

    client_max_body_size 100M;

    location / {
        proxy_pass http://ai_data_portal;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
        proxy_buffering off;
    }

    location /_stcore/stream {
        proxy_pass http://ai_data_portal/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
        proxy_buffering off;
    }
}
EOF
fi

# Enable site
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/ai-data-portal /etc/nginx/sites-enabled/

# Test and reload nginx
nginx -t && systemctl reload nginx
print_success "Nginx configured"

# Step 10: Setup firewall
print_status "Configuring firewall..."
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable
print_success "Firewall configured"

# Step 11: Verify installation
print_status "Verifying installation..."
sleep 3

if systemctl is-active --quiet ai-data-portal; then
    print_success "AI Data Portal service is running"
else
    print_error "AI Data Portal service failed to start"
    echo "Check logs with: journalctl -u ai-data-portal -f"
fi

if systemctl is-active --quiet nginx; then
    print_success "Nginx is running"
else
    print_error "Nginx failed to start"
fi

# Final message
echo ""
echo "=============================================="
echo "   Installation Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit your API key:"
echo "   nano $APP_DIR/.env"
echo ""
echo "2. (Optional) Setup domain and SSL:"
echo "   - Point your domain to this server's IP"
echo "   - Edit nginx config: nano /etc/nginx/sites-available/ai-data-portal"
echo "   - Replace 'server_name _;' with 'server_name your-domain.com;'"
echo "   - Run: certbot --nginx -d your-domain.com"
echo ""
echo "3. Access your app:"
echo "   http://$(curl -s ifconfig.me)"
echo ""
echo "Useful commands:"
echo "   Check status:  systemctl status ai-data-portal"
echo "   View logs:     journalctl -u ai-data-portal -f"
echo "   Restart app:   systemctl restart ai-data-portal"
echo ""
print_success "Happy analyzing!"
