#!/bin/bash
set -e

# ============================================
# AWS Launch Template User Data Script
# Django Application with Auto Scaling & Load Balancer
# ============================================

# Log all output to a file for debugging
exec > >(tee /var/log/user-data.log) 2>&1
echo "Starting deployment at $(date)"

# ============================================
# Configuration - Update these variables
# ============================================
APP_NAME="django-app"
APP_DIR="/opt/${APP_NAME}"
REPO_URL="https://github.com/your-username/your-repo.git"  # Update with your repo URL
BRANCH="main"

# Database Configuration (Use AWS Secrets Manager or Parameter Store in production)
export DB_NAME="your_db_name"
export DB_USER="your_db_user"
export DB_PASSWORD="your_db_password"
export DB_HOST="your-rds-endpoint.region.rds.amazonaws.com"  # Your RDS endpoint
export DB_PORT="5432"

# Django Configuration
export DEBUG="0"
export DJANGO_SECRET_KEY="your-production-secret-key-here"  # Generate a new secret key for production
export ALLOWED_HOSTS="*"  # Will be overridden in settings

# ============================================
# System Updates and Dependencies
# ============================================
echo "Updating system packages..."
apt-get update -y
apt-get upgrade -y

echo "Installing required packages..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    nginx \
    postgresql-client \
    supervisor \
    curl

# ============================================
# Application Setup
# ============================================
echo "Setting up application directory..."
mkdir -p ${APP_DIR}
cd ${APP_DIR}

# Clone or pull the repository
if [ -d "${APP_DIR}/.git" ]; then
    echo "Pulling latest code..."
    git pull origin ${BRANCH}
else
    echo "Cloning repository..."
    git clone -b ${BRANCH} ${REPO_URL} .
fi

# ============================================
# Python Virtual Environment
# ============================================
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# ============================================
# Django Setup
# ============================================
echo "Running Django migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# ============================================
# Create Superuser
# ============================================
echo "Creating superuser..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', '12345678')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
EOF

# ============================================
# Gunicorn Configuration
# ============================================
echo "Configuring Gunicorn..."
cat > /etc/supervisor/conf.d/gunicorn.conf << EOF
[program:gunicorn]
directory=${APP_DIR}
command=${APP_DIR}/venv/bin/gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3 --threads 2 --timeout 60
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/gunicorn/access.log
stderr_logfile=/var/log/gunicorn/error.log
environment=
    DB_NAME="${DB_NAME}",
    DB_USER="${DB_USER}",
    DB_PASSWORD="${DB_PASSWORD}",
    DB_HOST="${DB_HOST}",
    DB_PORT="${DB_PORT}",
    DEBUG="${DEBUG}",
    DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY}"
EOF

mkdir -p /var/log/gunicorn
chown -R www-data:www-data /var/log/gunicorn
chown -R www-data:www-data ${APP_DIR}

# ============================================
# Nginx Configuration
# ============================================
echo "Configuring Nginx..."
cat > /etc/nginx/sites-available/${APP_NAME} << EOF
upstream django {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name _;

    # Health check endpoint for ALB
    location /health/ {
        access_log off;
        return 200 'healthy';
        add_header Content-Type text/plain;
    }

    location /static/ {
        alias ${APP_DIR}/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias ${APP_DIR}/media/;
        expires 30d;
    }

    location / {
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Increase max upload size if needed
    client_max_body_size 10M;
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/${APP_NAME} /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# ============================================
# Start Services
# ============================================
echo "Starting services..."
supervisorctl reread
supervisorctl update
supervisorctl restart gunicorn

systemctl restart nginx
systemctl enable nginx

# ============================================
# Final Health Check
# ============================================
echo "Performing health check..."
sleep 5
if curl -s http://localhost/health/ | grep -q "healthy"; then
    echo "Application is healthy and running!"
else
    echo "WARNING: Health check failed!"
fi

echo "Deployment completed at $(date)"
