#!/usr/bin/env python3
"""
Simple script to create test data for the BBK verification system
Run this to populate the database with test records
"""

from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["bbk"]

# Clear existing test data
verifications = db["verifications"]
verifications.delete_many({})

print("Creating test verification data...")

test_data = [
    {
        "user_email": "user1@example.com",
        "user_name": "John Doe",
        "status": "pending",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "documents": ["license", "id_proof"],
        "admin_approved": False,
        "admin_notes": "",
        "ceo_approved": False,
        "ceo_notes": "",
        "cleared": False,
        "cleared_at": None,
    },
    {
        "user_email": "user2@example.com",
        "user_name": "Jane Smith",
        "status": "pending",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "documents": ["passport", "address_proof"],
        "admin_approved": False,
        "admin_notes": "",
        "ceo_approved": False,
        "ceo_notes": "",
        "cleared": False,
        "cleared_at": None,
    },
    {
        "user_email": "user3@example.com",
        "user_name": "Bob Wilson",
        "status": "under_review",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "documents": ["license"],
        "admin_approved": True,
        "admin_notes": "Document looks valid",
        "ceo_approved": False,
        "ceo_notes": "",
        "cleared": False,
        "cleared_at": None,
    },
    {
        "user_email": "user4@example.com",
        "user_name": "Alice Johnson",
        "status": "ceo_review",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "documents": ["bank_statement", "utility_bill"],
        "admin_approved": True,
        "admin_notes": "All documents verified",
        "ceo_approved": False,
        "ceo_notes": "",
        "cleared": False,
        "cleared_at": None,
    },
    {
        "user_email": "user5@example.com",
        "user_name": "Charlie Brown",
        "status": "approved",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "documents": ["license", "id_proof", "address_proof"],
        "admin_approved": True,
        "admin_notes": "Approved by admin",
        "ceo_approved": True,
        "ceo_notes": "Final approval given",
        "cleared": True,
        "cleared_at": datetime.utcnow(),
    },
    {
        "user_email": "user6@example.com",
        "user_name": "Diana Prince",
        "status": "rejected",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "documents": ["invalid_doc"],
        "admin_approved": False,
        "admin_notes": "Document does not match",
        "ceo_approved": False,
        "ceo_notes": "",
        "cleared": False,
        "cleared_at": None,
    },
]

result = verifications.insert_many(test_data)

print(f"✓ Created {len(result.inserted_ids)} test verifications")
print(f"\nData breakdown:")
print(f"  - Pending: 2")
print(f"  - Under Review: 1")
print(f"  - CEO Review: 1")
print(f"  - Approved & Cleared: 1")
print(f"  - Rejected: 1")
print(f"\nTest data created successfully!")
print(f"Now visit:")
print(f"  - Admin Dashboard: http://localhost:5000/admin/dashboard")
print(f"  - CEO Dashboard: http://localhost:5000/ceo/dashboard")
