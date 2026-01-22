# BBK Verification System - Quick Start Guide

## Getting Started

### 1. Initial Setup

```bash
# Clone repository
git clone <repo-url>
cd bbk-verification

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. MongoDB Setup

**Local MongoDB:**
```bash
# Install MongoDB Community Edition
# https://docs.mongodb.com/manual/installation/

# Start MongoDB
mongod
```

**Cloud MongoDB (MongoDB Atlas):**
1. Create account at https://www.mongodb.com/cloud/atlas
2. Create a cluster
3. Get connection string
4. Add to `.env`: `MONGODB_URI=mongodb+srv://...`

### 3. Gmail Configuration

To use email notifications:

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password:**
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer"
   - Copy the generated password
3. **Update `.env` file:**
   ```
   EMAIL_USER=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password
   ```

### 4. Environment Setup

```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

**Minimum required variables:**
```
FLASK_ENV=development
SECRET_KEY=your-secret-key
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=bbk
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
ADMIN_EMAILS=admin@company.com
CEO_EMAIL=ceo@company.com
```

### 5. Start the Application

```bash
# Run Flask development server
python app.py

# Application will be available at http://localhost:5000
```

## Login Credentials (Demo)

Use these for testing:

| Role | Email | Password |
|------|-------|----------|
| User | user@example.com | password |
| Admin | admin@example.com | password |
| CEO | ceo@example.com | password |

## Testing the System

### Run Tests
```bash
python test_system.py
```

This will verify:
- Database connection
- Document processing
- Verification creation
- Approval workflow
- Statistics generation

### Manual Testing

1. **User Workflow:**
   - Login as user@example.com
   - Click "Submit Documents"
   - Select document types (License, ID, etc.)
   - Upload sample documents
   - View verification status

2. **Admin Workflow:**
   - Login as admin@example.com
   - Go to Admin Dashboard
   - Review pending verifications
   - Click "Approve" or "Reject"
   - Add notes if needed

3. **CEO Workflow:**
   - Login as ceo@example.com
   - Go to CEO Dashboard
   - Review admin-approved verifications
   - "Clear" or reject with notes
   - User receives notification

## Using the Scheduler

The system includes automated scheduled tasks:

### Run Scheduler
```bash
python scheduler.py
```

### Run Individual Tasks
```bash
# Send CEO daily summary
python scheduler.py ceo_summary

# Notify admin of pending items
python scheduler.py admin_notification

# Clean up old files
python scheduler.py cleanup

# Check for expiring documents
python scheduler.py check_expiry

# Archive old verifications
python scheduler.py archive
```

## Dashboard Routes

| Route | Purpose | Access |
|-------|---------|--------|
| `/` | Home | All |
| `/dashboard` | User verification status | Users |
| `/submit` | Upload documents | Users |
| `/admin/dashboard` | Manage pending verifications | Admin |
| `/ceo/dashboard` | Final approval & clearance | CEO |
| `/analytics` | System analytics & overview | All (authenticated) |
| `/verification/<id>` | Verification details | All (authenticated) |

## API Endpoints

### Public (requires authentication)
- `GET /api/stats` - Today's statistics
- `GET /api/verifications` - User's verifications (or role-based)
- `GET /api/workflow-stats` - Overall workflow statistics
- `GET /api/dashboard-data` - Complete dashboard data

### Admin/CEO Actions
- `POST /admin/approve/<id>` - Approve verification
- `POST /admin/reject/<id>` - Reject verification
- `POST /ceo/approve/<id>` - Clear verification
- `POST /ceo/reject/<id>` - Reject verification

### Scheduler
- `POST /api/send-daily-summary` - Trigger CEO summary (requires API_KEY)

## File Structure

```
bbk-verification/
├── app.py                    # Main Flask application
├── config.py                 # Configuration
├── database.py               # MongoDB setup
├── email_service.py          # Email notifications
├── verification_service.py   # Verification logic
├── firmcheck_service.py      # FirmCheck integration
├── document_processor.py     # Document handling
├── approval_service.py       # Approval workflow
├── scheduler.py              # Automated tasks
├── test_system.py            # Testing suite
├── requirements.txt          # Python dependencies
├── README.md                 # Full documentation
├── QUICKSTART.md            # This file
├── .env.example             # Environment template
└── templates/
    ├── base.html            # Base template
    ├── login.html           # Login page
    ├── user_dashboard.html  # User dashboard
    ├── submit_documents.html # Document submission
    ├── admin_dashboard.html # Admin interface
    ├── ceo_dashboard.html   # CEO interface
    ├── verification_detail.html # Verification details
    └── analytics_dashboard.html # Analytics view
```

## Troubleshooting

### MongoDB Connection Error
```
Error: Could not connect to MongoDB
```
**Solution:** 
- Ensure MongoDB is running: `mongod`
- Check MONGODB_URI in .env
- Verify connection string format

### Email Not Sending
```
Error: Failed to send email
```
**Solution:**
- Enable 2-FA on Gmail
- Generate app password (not regular password)
- Check EMAIL_USER and EMAIL_PASSWORD in .env
- Verify account hasn't been flagged

### Port Already in Use
```
Error: Address already in use (port 5000)
```
**Solution:**
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :5000   # Windows
```

### Document Upload Issues
- Check `uploads/` folder exists
- Verify file size < 16MB
- Ensure file type is supported (PDF, PNG, JPG, GIF)

## Next Steps

1. **Configure Real FirmCheck API**
   - Update FIRMCHECK_API_KEY in .env
   - Modify firmcheck_service.py to call real API

2. **Deploy to Production**
   - Use Gunicorn/uWSGI
   - Set up HTTPS/SSL
   - Configure proper database backups
   - Set FLASK_ENV=production

3. **Setup Database Backups**
   - Configure MongoDB Atlas backups
   - Set up regular export schedule

4. **Integrate with Existing Systems**
   - Connect to user management system
   - Integrate with CRM/ERP
   - Setup data export pipelines

## Support & Documentation

- Full documentation: See README.md
- API details: Check app.py route comments
- Database schema: Check database.py
- Email templates: Check email_service.py

## License

Proprietary - BBK Verification System
