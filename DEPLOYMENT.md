# BBK Verification System - Deployment Guide

## Production Deployment

### Pre-Deployment Checklist

- [ ] MongoDB production instance set up (Atlas or self-managed)
- [ ] Gmail account configured with app password
- [ ] All environment variables defined
- [ ] Database backups configured
- [ ] SSL/TLS certificate obtained
- [ ] Domain name configured
- [ ] Admin emails verified
- [ ] CEO email verified
- [ ] Firewall rules configured
- [ ] Monitoring/logging setup

## Production Environment Setup

### 1. Server Requirements

**Minimum specs:**
- 2GB RAM
- 20GB storage (adjust based on upload volume)
- Ubuntu 20.04 or CentOS 8+
- Python 3.8+

**Recommended:**
- 4GB+ RAM
- 50GB+ storage
- Load balancer (Nginx)
- Separate database server

### 2. MongoDB Production Setup

**Option A: MongoDB Atlas (Recommended)**

```bash
1. Create account at https://www.mongodb.com/cloud/atlas
2. Create M2 or larger cluster
3. Configure IP whitelist
4. Create database user
5. Get connection string
6. Add to environment: MONGODB_URI=mongodb+srv://user:pass@cluster...
```

**Option B: Self-Managed MongoDB**

```bash
# Install MongoDB on Ubuntu
curl https://www.mongodb.org/static/pgp/server-5.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/5.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-5.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Create admin user
mongosh
> use admin
> db.createUser({user: "admin", pwd: "strongpassword", roles: ["root"]})
> exit

# Enable authentication in /etc/mongod.conf
# security:
#   authorization: enabled

# Restart
sudo systemctl restart mongod

# Connection string:
# MONGODB_URI=mongodb://admin:strongpassword@localhost:27017/?authSource=admin
```

### 3. Application Server Setup

```bash
# Create app user
sudo useradd -m -s /bin/bash bbk-app
sudo su - bbk-app

# Clone repository
git clone <repo-url> /home/bbk-app/bbk-verification
cd /home/bbk-app/bbk-verification

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Exit back to root
exit
```

### 4. Systemd Service Setup

Create `/etc/systemd/system/bbk-verification.service`:

```ini
[Unit]
Description=BBK Verification System
After=network.target mongodb.service

[Service]
User=bbk-app
WorkingDirectory=/home/bbk-app/bbk-verification
Environment="PATH=/home/bbk-app/bbk-verification/venv/bin"
Environment="FLASK_ENV=production"
EnvironmentFile=/home/bbk-app/bbk-verification/.env
ExecStart=/home/bbk-app/bbk-verification/venv/bin/gunicorn \
    --workers 4 \
    --worker-class sync \
    --bind 127.0.0.1:5000 \
    --timeout 120 \
    --access-logfile /var/log/bbk-verification/access.log \
    --error-logfile /var/log/bbk-verification/error.log \
    app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable bbk-verification
sudo systemctl start bbk-verification
sudo systemctl status bbk-verification
```

### 5. Nginx Reverse Proxy Setup

Create `/etc/nginx/sites-available/bbk-verification`:

```nginx
upstream bbk_app {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy settings
    client_max_body_size 16M;
    
    location / {
        proxy_pass http://bbk_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_connect_timeout 120;
        proxy_send_timeout 120;
        proxy_read_timeout 120;
    }
    
    # Static files caching
    location ~* ^/static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/bbk-verification /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. SSL Certificate Setup

Using Let's Encrypt:
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com
```

### 7. Production Environment Variables

Create `/home/bbk-app/bbk-verification/.env`:

```
FLASK_ENV=production
SECRET_KEY=generate-strong-random-key
DEBUG=False

# MongoDB
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=bbk

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-production-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Admin Configuration
ADMIN_EMAILS=admin1@company.com,admin2@company.com
CEO_EMAIL=ceo@company.com

# FirmCheck
FIRMCHECK_API_KEY=your-real-api-key
FIRMCHECK_API_URL=https://api.firmcheck.com/verify

# API Security
API_KEY=generate-strong-api-key
```

### 8. Logging and Monitoring

Create log directory:
```bash
sudo mkdir -p /var/log/bbk-verification
sudo chown bbk-app:bbk-app /var/log/bbk-verification
```

Configure log rotation `/etc/logrotate.d/bbk-verification`:
```
/var/log/bbk-verification/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 bbk-app bbk-app
    sharedscripts
    postrotate
        systemctl reload bbk-verification > /dev/null 2>&1 || true
    endscript
}
```

### 9. Backup Strategy

**Database Backups:**

```bash
# MongoDB Atlas: Built-in backups
# - Configure automated snapshots
# - Retention: 14 days

# Self-managed: Create backup script
#!/bin/bash
BACKUP_DIR="/backups/mongodb"
DATE=$(date +%Y%m%d_%H%M%S)
mongodump --uri="mongodb://admin:password@localhost:27017/?authSource=admin" \
          --out=$BACKUP_DIR/backup_$DATE
# Keep only last 7 days
find $BACKUP_DIR -name "backup_*" -mtime +7 -exec rm -rf {} \;
```

**File Backups:**
```bash
# Backup uploads directory
tar czf /backups/uploads_$(date +%Y%m%d).tar.gz /home/bbk-app/bbk-verification/uploads
```

### 10. Scheduler Setup

Create `/etc/systemd/system/bbk-scheduler.service`:

```ini
[Unit]
Description=BBK Scheduler
After=network.target bbk-verification.service

[Service]
User=bbk-app
WorkingDirectory=/home/bbk-app/bbk-verification
Environment="PATH=/home/bbk-app/bbk-verification/venv/bin"
Environment="FLASK_ENV=production"
EnvironmentFile=/home/bbk-app/bbk-verification/.env
ExecStart=/home/bbk-app/bbk-verification/venv/bin/python scheduler.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable bbk-scheduler
sudo systemctl start bbk-scheduler
```

## Post-Deployment

### 1. Health Check

```bash
curl https://your-domain.com/login
# Should return login page

curl https://your-domain.com/api/stats -H "Cookie: session=..."
# Should return JSON stats (with valid session)
```

### 2. Email Testing

```bash
python scheduler.py admin_notification
# Check if test email arrives
```

### 3. Database Verification

```bash
mongosh --uri "mongodb+srv://user:pass@cluster.mongodb.net"
> use bbk
> db.verifications.count()
```

### 4. Monitor Services

```bash
# Check service status
sudo systemctl status bbk-verification
sudo systemctl status bbk-scheduler
sudo systemctl status nginx

# View logs
tail -f /var/log/bbk-verification/error.log
sudo tail -f /var/log/nginx/error.log
```

## Scaling Considerations

### Horizontal Scaling

1. **Load Balancer Setup**
   - Deploy application on multiple servers
   - Use load balancer (Nginx, HAProxy) to distribute traffic
   - Ensure sticky sessions or use external session store

2. **Database Scaling**
   - Use MongoDB replica sets for high availability
   - Configure sharding for large datasets

3. **Email Queue**
   - Implement job queue (Redis + Celery) for email sending
   - Prevents bottlenecks during high volume

### Performance Optimization

1. **Caching**
   - Implement Redis for session storage
   - Cache frequently accessed data

2. **Database Indexing**
   - Already configured in database.py
   - Monitor query performance

3. **CDN**
   - Serve static files via CDN
   - Reduces server load

## Troubleshooting Production Issues

### Application won't start
```bash
journalctl -u bbk-verification -n 50
# Check logs for specific errors
```

### MongoDB connection timeout
```bash
# Verify network connectivity
telnet mongodb-host 27017

# Check connection string format
# For Atlas: mongodb+srv://user:pass@cluster...
# For self-managed: mongodb://user:pass@host:27017/dbname?authSource=admin
```

### High memory usage
```bash
# Check process memory
ps aux | grep gunicorn

# Adjust worker count in service file
--workers 2  # Reduce if memory constrained
```

### Email delivery issues
```bash
# Test Gmail auth
python -c "
import smtplib
with smtplib.SMTP('smtp.gmail.com', 587) as server:
    server.starttls()
    server.login('email@gmail.com', 'app-password')
    print('Gmail auth OK')
"
```

## Security Hardening

1. **Firewall Rules**
```bash
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

2. **Fail2Ban**
```bash
sudo apt-get install fail2ban
# Configure to block brute-force attempts
```

3. **Regular Updates**
```bash
sudo apt-get update && sudo apt-get upgrade
```

4. **Secrets Management**
- Never commit .env to git
- Use environment variables only
- Rotate secrets regularly

5. **Database Security**
- Enable MongoDB authentication
- Use strong passwords
- Restrict network access
- Enable encryption at rest

## Support

For deployment issues, check:
- Application logs: `/var/log/bbk-verification/`
- Nginx logs: `/var/log/nginx/`
- Systemd journal: `journalctl -u bbk-verification`
