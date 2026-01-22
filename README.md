# BBK Verification System

A comprehensive document verification system built with Flask and MongoDB. This system handles document submission, FirmCheck verification, and multi-level approval workflows for admin teams and CEOs.

## Features

- **User Document Submission**: Users can submit verification documents (License, ID, Proof, etc.)
- **FirmCheck Integration**: Mock FirmCheck verification for document validation
- **Admin Review Workflow**: Admin team reviews and approves/rejects verifications
- **CEO Approval**: Final CEO review for all verifications
- **Email Notifications**: Automated email alerts for users and admin team
- **Dynamic Dashboard**: Real-time tracking of verification status and statistics
- **Status Tracking**: Monitor daily email submissions and verification progress

## System Architecture

### Collections

1. **verifications**: Main verification records
   - user_email, user_name, status
   - document_types, firmcheck_verified
   - admin_approved, ceo_approved, cleared

2. **documents**: Individual document records
   - verification_id, document_type, file_path
   - extracted_data, firmcheck_status

3. **approvals**: Approval audit trail
   - verification_id, approver_type, approver_email
   - notes, approved_at

4. **email_logs**: Email notification history
   - recipient, subject, sent_at, status

### Workflow

```
User Submits Documents
       ↓
FirmCheck Verification (Mock)
       ↓
Admin Review & Approval
       ↓
CEO Final Review
       ↓
Cleared/Approved
```

## Installation

### Prerequisites

- Python 3.8+
- MongoDB
- Gmail account with app password

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd bbk-verification
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Setup environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Ensure MongoDB is running:
```bash
# For local MongoDB
mongod
```

6. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Environment Variables

```env
# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key

# MongoDB
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=bbk

# Email (Gmail SMTP)
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Admin Configuration
ADMIN_EMAILS=admin@company.com
CEO_EMAIL=ceo@company.com

# FirmCheck
FIRMCHECK_API_KEY=your-api-key
```

## Demo Credentials

- **User**: user@example.com / password
- **Admin**: admin@example.com / password
- **CEO**: ceo@example.com / password

## API Endpoints

### User Routes
- `GET /` - Redirect to dashboard
- `GET /dashboard` - User verification dashboard
- `GET /submit` - Submit documents page
- `POST /submit` - Submit documents
- `GET /verification/<id>` - Verification details

### Admin Routes
- `GET /admin/dashboard` - Admin dashboard
- `POST /admin/approve/<id>` - Approve verification
- `POST /admin/reject/<id>` - Reject verification

### CEO Routes
- `GET /ceo/dashboard` - CEO dashboard
- `POST /ceo/approve/<id>` - Approve verification
- `POST /ceo/reject/<id>` - Reject verification

### API Routes
- `GET /api/stats` - Today's statistics
- `GET /api/verifications` - List verifications
- `POST /api/send-daily-summary` - Send CEO summary (requires API_KEY)

## Verification Status

- **pending**: Awaiting document upload
- **under_review**: Admin is reviewing
- **ceo_review**: Pending CEO approval
- **approved**: Fully approved and cleared
- **rejected**: Rejected, user needs to resubmit

## Email Notifications

The system sends automated emails:

1. **User Submission Confirmation**: When documents are submitted
2. **Admin Notification**: When documents need review
3. **Status Updates**: When verification status changes
4. **Daily Summary**: CEO receives daily summary (can be scheduled)

## File Structure

```
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── database.py           # MongoDB connection
├── email_service.py      # Email handling
├── verification_service.py # Verification logic
├── requirements.txt      # Python dependencies
├── templates/            # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── user_dashboard.html
│   ├── admin_dashboard.html
│   ├── ceo_dashboard.html
│   └── ...
└── uploads/              # Document uploads (auto-created)
```

## Development

### Running Tests

```bash
# Create test documents
python -m pytest tests/
```

### Database Management

```bash
# Connect to MongoDB
mongo bbk

# View collections
db.getCollectionNames()

# Query verifications
db.verifications.find()
```

## Production Deployment

1. Set `FLASK_ENV=production`
2. Use a production WSGI server (Gunicorn, uWSGI)
3. Configure proper MongoDB authentication
4. Set up HTTPS/SSL
5. Use environment variables for sensitive data
6. Enable MongoDB backups

Example with Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## FirmCheck Integration

Currently using mock FirmCheck verification. To integrate real FirmCheck:

1. Get API credentials from FirmCheck
2. Update `FIRMCHECK_API_URL` and `FIRMCHECK_API_KEY`
3. Modify `verification_service.py` `verify_with_firmcheck()` method

## Troubleshooting

### MongoDB Connection Error
- Ensure MongoDB is running: `mongod`
- Check `MONGODB_URI` in `.env`

### Email Not Sending
- Enable "Less secure app access" in Gmail
- Generate app-specific password
- Check `EMAIL_USER` and `EMAIL_PASSWORD`

### File Upload Issues
- Check `uploads/` folder exists and has write permissions
- Verify `MAX_CONTENT_LENGTH` setting
- Check allowed file extensions

## Support

For issues or questions, contact the development team.

## License

Proprietary - BBK Verification System
