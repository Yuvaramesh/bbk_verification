# BBK Verification System - API Documentation

## Overview

Complete REST API documentation for the BBK Verification System. All endpoints require authentication unless otherwise specified.

## Authentication

### Login
```
POST /login
Content-Type: application/x-www-form-urlencoded

email=user@example.com
password=password
role=user|admin|ceo
```

**Response:**
- Sets session cookie
- Redirects to appropriate dashboard

### Logout
```
GET /logout
```

**Response:**
- Clears session
- Redirects to login

## User Endpoints

### Get User Dashboard
```
GET /dashboard
```

**Authentication:** Required (User role)

**Response:** HTML page with user's verifications

**Status Codes:**
- 200: Success
- 302: Redirect to login if not authenticated

---

### Get Document Submission Form
```
GET /submit
```

**Authentication:** Required (User role)

**Response:** HTML form with document type options

---

### Submit Documents
```
POST /submit
Content-Type: multipart/form-data

name: "John Doe"
document_types: ["license", "id"]
files: [file1, file2, ...]
```

**Authentication:** Required (User role)

**Parameters:**
- `name` (string, required): User's full name
- `document_types` (array, required): Selected document types
- `files` (multipart, required): Document files to upload

**Supported Document Types:**
- license
- id
- passport
- proof_of_address
- bank_statement
- utility_bill

**Supported File Types:**
- PDF (application/pdf)
- PNG (image/png)
- JPEG (image/jpeg)
- GIF (image/gif)
- Max size: 16MB per file

**Response:**
```json
{
  "success": true,
  "verification_id": "507f1f77bcf86cd799439011",
  "status": "pending"
}
```

**Status Codes:**
- 302: Redirect on success
- 400: Invalid input
- 413: File too large
- 415: Unsupported file type

---

### Get Verification Details
```
GET /verification/<verification_id>
```

**Authentication:** Required

**Parameters:**
- `verification_id` (path, required): ObjectId of verification

**Response:** HTML page with verification details

**Status Codes:**
- 200: Success
- 404: Verification not found

---

### Get User Verifications (API)
```
GET /api/verifications
Accept: application/json
```

**Authentication:** Required

**Response:**
```json
[
  {
    "_id": "507f1f77bcf86cd799439011",
    "user_email": "user@example.com",
    "user_name": "John Doe",
    "status": "pending",
    "documents": ["license", "id"],
    "firmcheck_verified": false,
    "admin_approved": false,
    "ceo_approved": false,
    "cleared": false,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

**Status Codes:**
- 200: Success
- 401: Unauthorized

## Admin Endpoints

### Get Admin Dashboard
```
GET /admin/dashboard
```

**Authentication:** Required (Admin role)

**Response:** HTML page with pending verifications

---

### Approve Verification
```
POST /admin/approve/<verification_id>
Content-Type: application/json
Accept: application/json

{
  "notes": "Documents look good. Forwarding to CEO."
}
```

**Authentication:** Required (Admin role)

**Parameters:**
- `verification_id` (path, required): ObjectId of verification
- `notes` (body, optional): Review notes

**Response:**
```json
{
  "success": true,
  "message": "Verification approved by admin"
}
```

**Status Codes:**
- 200: Success
- 400: Verification not found or invalid documents
- 401: Unauthorized

---

### Reject Verification
```
POST /admin/reject/<verification_id>
Content-Type: application/json
Accept: application/json

{
  "reason": "Document quality is too low. Please resubmit."
}
```

**Authentication:** Required (Admin role)

**Parameters:**
- `verification_id` (path, required): ObjectId of verification
- `reason` (body, required): Rejection reason

**Response:**
```json
{
  "success": true,
  "message": "Verification rejected"
}
```

**Status Codes:**
- 200: Success
- 400: Verification not found
- 401: Unauthorized

## CEO Endpoints

### Get CEO Dashboard
```
GET /ceo/dashboard
```

**Authentication:** Required (CEO role)

**Response:** HTML page with admin-approved verifications

---

### Approve & Clear Verification
```
POST /ceo/approve/<verification_id>
Content-Type: application/json
Accept: application/json

{
  "notes": "All verified. Cleared for processing."
}
```

**Authentication:** Required (CEO role)

**Parameters:**
- `verification_id` (path, required): ObjectId of verification
- `notes` (body, optional): Approval notes

**Response:**
```json
{
  "success": true,
  "message": "Verification approved by CEO"
}
```

**Status Codes:**
- 200: Success
- 400: Verification not found
- 401: Unauthorized

---

### Reject Verification (CEO)
```
POST /ceo/reject/<verification_id>
Content-Type: application/json
Accept: application/json

{
  "reason": "Requires additional documentation."
}
```

**Authentication:** Required (CEO role)

**Parameters:**
- `verification_id` (path, required): ObjectId of verification
- `reason` (body, required): Rejection reason

**Response:**
```json
{
  "success": true,
  "message": "Verification rejected"
}
```

**Status Codes:**
- 200: Success
- 400: Verification not found
- 401: Unauthorized

## Analytics & Statistics Endpoints

### Get Today's Statistics
```
GET /api/stats
Accept: application/json
```

**Authentication:** Required

**Response:**
```json
{
  "total_emails": 10,
  "pending": 3,
  "under_review": 2,
  "approved": 4,
  "admin_approved": 6,
  "ceo_approved": 4,
  "cleared": 4,
  "remaining": 6
}
```

**Includes:**
- Total submissions today
- Breakdown by status
- Approval counts
- Remaining items

**Status Codes:**
- 200: Success
- 401: Unauthorized

---

### Get Workflow Statistics
```
GET /api/workflow-stats
Accept: application/json
```

**Authentication:** Required

**Response:**
```json
{
  "total_verifications": 150,
  "status_breakdown": {
    "pending": 5,
    "under_review": 8,
    "ceo_review": 12,
    "approved": 120,
    "rejected": 5
  },
  "approval_counts": {
    "admin_approved": 132,
    "ceo_approved": 120,
    "cleared": 120
  },
  "avg_time_to_admin_review_hours": 2.5,
  "avg_time_to_ceo_review_hours": 1.2,
  "approval_rate": 80.0,
  "rejection_rate": 3.33
}
```

**Includes:**
- Total verification counts
- Status distribution
- Approval counts
- Processing time metrics
- Success rates

**Status Codes:**
- 200: Success
- 401: Unauthorized

---

### Get Complete Dashboard Data
```
GET /api/dashboard-data
Accept: application/json
```

**Authentication:** Required

**Response:**
```json
{
  "today_stats": { ...today_stats... },
  "workflow_stats": { ...workflow_stats... },
  "role": "admin",
  "pending_verifications": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "user_email": "user@example.com",
      ...verification_data...
    }
  ]
}
```

**Data Varies by Role:**
- User: Personal verifications
- Admin: Pending admin reviews
- CEO: Pending CEO reviews

**Status Codes:**
- 200: Success
- 401: Unauthorized

## Scheduler Endpoints

### Send Daily CEO Summary
```
POST /api/send-daily-summary
X-API-KEY: your-api-key
```

**Authentication:** Required (API_KEY header)

**Parameters:**
- `X-API-KEY` (header, required): API key from environment

**Response:**
```json
{
  "success": true,
  "summary_sent": true
}
```

**Status Codes:**
- 200: Success
- 401: Invalid API key

## Error Responses

### Standard Error Format
```json
{
  "error": "Error message",
  "status": "failed",
  "details": {}
}
```

### Common Error Codes

| Code | Message | Cause |
|------|---------|-------|
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Missing/invalid authentication |
| 404 | Not Found | Resource doesn't exist |
| 413 | File Too Large | File exceeds 16MB limit |
| 415 | Unsupported File Type | Invalid file format |
| 500 | Server Error | Internal server error |

## Rate Limiting

Currently no rate limiting. Production deployment should implement:
- IP-based rate limiting (requests per minute)
- User-based rate limiting
- File upload quotas

## Webhooks (Future)

Not yet implemented, but ready for:
- Verification status changes
- Document expiration notifications
- Approval reminders
- Admin alerts

## Response Headers

All responses include:
```
Content-Type: application/json
X-Powered-By: BBK Verification System
```

## Pagination

Not yet implemented. Available for:
- Verification listings
- Approval history
- Statistics by date range

## Filtering

Not yet implemented. Ready for:
- Filter verifications by status
- Filter by date range
- Filter by user
- Filter by document type

## Sorting

Not yet implemented. Ready for:
- Sort by creation date
- Sort by update date
- Sort by status
- Custom field sorting

## Examples

### Example: User Submitting Documents

```bash
# 1. Login
curl -X POST http://localhost:5000/login \
  -d "email=user@example.com&password=password&role=user" \
  -c cookies.txt

# 2. Submit documents
curl -X POST http://localhost:5000/submit \
  -b cookies.txt \
  -F "name=John Doe" \
  -F "document_types=license" \
  -F "document_types=id" \
  -F "files=@/path/to/license.pdf" \
  -F "files=@/path/to/id.png"

# 3. Check status
curl -X GET http://localhost:5000/api/verifications \
  -b cookies.txt \
  -H "Accept: application/json"
```

### Example: Admin Approving Verification

```bash
# 1. Login
curl -X POST http://localhost:5000/login \
  -d "email=admin@example.com&password=password&role=admin" \
  -c cookies.txt

# 2. Get dashboard data
curl -X GET http://localhost:5000/api/dashboard-data \
  -b cookies.txt \
  -H "Accept: application/json"

# 3. Approve verification
curl -X POST http://localhost:5000/admin/approve/507f1f77bcf86cd799439011 \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"notes": "Good documentation"}'
```

### Example: Getting Statistics

```bash
# Login and get stats
curl -X POST http://localhost:5000/login \
  -d "email=admin@example.com&password=password&role=admin" \
  -c cookies.txt

curl -X GET http://localhost:5000/api/workflow-stats \
  -b cookies.txt \
  -H "Accept: application/json"
```

## Testing API

### Using Postman
1. Import endpoints from this documentation
2. Set up environment variables
3. Use pre-request scripts for authentication
4. Test each endpoint with provided examples

### Using cURL
See examples above

### Using Python
```python
import requests
import json

session = requests.Session()

# Login
session.post('http://localhost:5000/login', data={
    'email': 'user@example.com',
    'password': 'password',
    'role': 'user'
})

# Get statistics
resp = session.get('http://localhost:5000/api/stats')
print(json.dumps(resp.json(), indent=2))
```

## API Versioning

Current version: v1 (implicit)

Future versions will use:
- `GET /api/v2/stats`
- `GET /api/v2/verifications`

## CORS

Currently enabled for localhost. Production should configure:
```python
CORS(app, origins=["https://yourdomain.com"])
```

## Authentication Methods

Planned enhancements:
- API tokens for service-to-service
- OAuth2 for third-party integrations
- JWT tokens for stateless authentication

## Status Codes Reference

- 200: OK - Request successful
- 201: Created - Resource created
- 204: No Content - Success, no content to return
- 302: Found - Redirect
- 400: Bad Request - Invalid request
- 401: Unauthorized - Authentication required
- 403: Forbidden - Authenticated but not authorized
- 404: Not Found - Resource not found
- 413: Payload Too Large - File too large
- 415: Unsupported Media Type - Invalid file type
- 500: Internal Server Error - Server error
- 503: Service Unavailable - Service maintenance

## Support

For API issues:
- Check logs: `/var/log/bbk-verification/error.log`
- Verify authentication tokens
- Test with provided examples
- Contact development team
