from datetime import datetime
from bson.objectid import ObjectId
from database import db
from firmcheck_service import FirmCheckService
import random
import string


class VerificationService:
    """Handle document verification logic"""

    DOCUMENT_TYPES = [
        "license",
        "id",
        "proof_of_address",
        "bank_statement",
        "utility_bill",
        "passport",
    ]

    @staticmethod
    def create_verification(user_email, user_name, document_types):
        """Create a new verification request"""
        verifications = db.get_verifications_collection()

        verification = {
            "user_email": user_email,
            "user_name": user_name,
            "status": "pending",  # pending, under_review, admin_approved, ceo_review, approved, rejected
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "documents": document_types,
            "firmcheck_verified": False,
            "admin_approved": False,
            "admin_notes": "",
            "ceo_approved": False,
            "ceo_notes": "",
            "cleared": False,
            "cleared_at": None,
        }

        result = verifications.insert_one(verification)
        return str(result.inserted_id)

    @staticmethod
    def add_document(verification_id, document_type, file_path, extracted_data):
        """Add a document to verification"""
        documents = db.get_documents_collection()

        document = {
            "verification_id": ObjectId(verification_id),
            "document_type": document_type,
            "file_path": file_path,
            "extracted_data": extracted_data,
            "uploaded_at": datetime.utcnow(),
            "firmcheck_status": "pending",  # pending, verified, rejected
        }

        result = documents.insert_one(document)

        # Update verification status
        verifications = db.get_verifications_collection()
        verifications.update_one(
            {"_id": ObjectId(verification_id)},
            {"$set": {"updated_at": datetime.utcnow()}},
        )

        return str(result.inserted_id)

    @staticmethod
    def verify_with_firmcheck(document_id, document_data):
        """Verify document using FirmCheck"""
        documents = db.get_documents_collection()

        # Get the document to know its type
        doc = documents.find_one({"_id": ObjectId(document_id)})
        document_type = doc.get("document_type", "unknown")

        # Call FirmCheck verification
        verification_result = FirmCheckService.verify_document(
            document_data.get("extracted_fields", document_data), document_type
        )

        # Update document with verification result
        status = "verified" if verification_result.get("verified") else "rejected"

        documents.update_one(
            {"_id": ObjectId(document_id)},
            {
                "$set": {
                    "firmcheck_status": status,
                    "firmcheck_result": verification_result,
                    "verification_score": FirmCheckService.get_verification_score(
                        verification_result
                    ),
                    "verified_at": datetime.utcnow(),
                }
            },
        )

        return verification_result

    @staticmethod
    def get_verification(verification_id):
        """Get verification details"""
        verifications = db.get_verifications_collection()
        verification = verifications.find_one({"_id": ObjectId(verification_id)})

        if verification:
            verification["_id"] = str(verification["_id"])

            # Get associated documents
            documents = db.get_documents_collection()
            docs = list(documents.find({"verification_id": ObjectId(verification_id)}))
            verification["documents_info"] = [
                {
                    "_id": str(doc["_id"]),
                    "document_type": doc["document_type"],
                    "firmcheck_status": doc.get("firmcheck_status", "pending"),
                }
                for doc in docs
            ]

        return verification

    @staticmethod
    def update_verification_status(verification_id, status, updated_by="system"):
        """Update verification status"""
        verifications = db.get_verifications_collection()

        update_data = {"status": status, "updated_at": datetime.utcnow()}

        verifications.update_one(
            {"_id": ObjectId(verification_id)}, {"$set": update_data}
        )

    @staticmethod
    def approve_by_admin(verification_id, admin_email, notes=""):
        """Admin approval"""
        verifications = db.get_verifications_collection()
        approvals = db.get_approvals_collection()

        # Update verification
        verifications.update_one(
            {"_id": ObjectId(verification_id)},
            {
                "$set": {
                    "admin_approved": True,
                    "admin_notes": notes,
                    "status": "ceo_review",
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        # Log approval
        approvals.insert_one(
            {
                "verification_id": ObjectId(verification_id),
                "approver_type": "admin",
                "approver_email": admin_email,
                "notes": notes,
                "approved_at": datetime.utcnow(),
            }
        )

    @staticmethod
    def approve_by_ceo(verification_id, ceo_email, notes=""):
        """CEO approval"""
        verifications = db.get_verifications_collection()
        approvals = db.get_approvals_collection()

        # Update verification
        verifications.update_one(
            {"_id": ObjectId(verification_id)},
            {
                "$set": {
                    "ceo_approved": True,
                    "ceo_notes": notes,
                    "status": "approved",
                    "cleared": True,
                    "cleared_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        # Log approval
        approvals.insert_one(
            {
                "verification_id": ObjectId(verification_id),
                "approver_type": "ceo",
                "approver_email": ceo_email,
                "notes": notes,
                "approved_at": datetime.utcnow(),
            }
        )

    @staticmethod
    def get_today_stats():
        """Get today's verification statistics"""
        verifications = db.get_verifications_collection()
        from datetime import date, time, timedelta

        # Get all documents to count (no date filter for more reliable stats)
        # This ensures counts work regardless of timezone issues
        pending_count = verifications.count_documents({"status": "pending"})
        under_review_count = verifications.count_documents({"status": "under_review"})
        ceo_review_count = verifications.count_documents({"status": "ceo_review"})
        approved_count = verifications.count_documents({"status": "approved"})
        rejected_count = verifications.count_documents({"status": "rejected"})

        admin_approved_count = verifications.count_documents({"admin_approved": True})
        ceo_approved_count = verifications.count_documents({"ceo_approved": True})
        cleared_count = verifications.count_documents({"cleared": True})

        # Calculate totals
        total = (
            pending_count
            + under_review_count
            + ceo_review_count
            + approved_count
            + rejected_count
        )
        remaining = total - cleared_count

        return {
            "total_emails": total,
            "pending": pending_count,
            "under_review": under_review_count,
            "ceo_review": ceo_review_count,
            "approved": approved_count,
            "rejected": rejected_count,
            "admin_approved": admin_approved_count,
            "ceo_approved": ceo_approved_count,
            "cleared": cleared_count,
            "remaining": remaining,
        }
