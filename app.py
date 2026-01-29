from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import os
from config import Config
from database import db
from email_service import EmailService
from verification_service import VerificationService
from document_processor import DocumentProcessor
from approval_service import ApprovalService
from firmcheck_service import FirmCheckService
from bson.objectid import ObjectId
import json

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Create upload folder if it doesn't exist
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ==================== Helper Functions ====================


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


def extract_text_from_image(file_path, document_type):
    """Extract text from document image"""
    return DocumentProcessor.process_document(file_path, document_type)


def is_authenticated():
    return "user_email" in session


def get_user_role():
    return session.get("user_role", "user")


# ==================== Routes: Authentication ====================


@app.route("/")
def index():
    return redirect(url_for("user_dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user_role = request.form.get("role", "user")

        # Mock authentication
        if email and password:
            session["user_email"] = email
            session["user_role"] = user_role

            if user_role == "admin":
                return redirect(url_for("admin_dashboard"))
            elif user_role == "ceo":
                return redirect(url_for("ceo_dashboard"))
            else:
                return redirect(url_for("user_dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ==================== Routes: User ====================


@app.route("/dashboard")
def user_dashboard():
    if not is_authenticated():
        return redirect(url_for("login"))

    user_email = session.get("user_email")
    verifications = db.get_verifications_collection()

    user_verifications = list(verifications.find({"user_email": user_email}))
    for v in user_verifications:
        v["_id"] = str(v["_id"])

    return render_template("user_dashboard.html", verifications=user_verifications)


@app.route("/submit", methods=["GET", "POST"])
def submit_documents():
    if not is_authenticated():
        return redirect(url_for("login"))

    if request.method == "POST":
        user_email = session.get("user_email")
        user_name = request.form.get("name", "User")

        # Get selected document types
        doc_types = request.form.getlist("document_types")

        if not doc_types:
            return jsonify({"error": "Please select document types"}), 400

        # Create verification request
        verification_id = VerificationService.create_verification(
            user_email, user_name, doc_types
        )

        high_risk_documents = []

        # Handle file uploads
        if "files" in request.files:
            files = request.files.getlist("files")
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)

                    # Determine document type from selected options
                    doc_types_list = request.form.getlist("document_types")
                    doc_type = doc_types_list[0] if doc_types_list else "other"

                    # Save file
                    file_path = os.path.join(
                        app.config["UPLOAD_FOLDER"], f"{verification_id}_{filename}"
                    )
                    file.save(file_path)

                    # Validate document
                    validation = DocumentProcessor.validate_document(
                        file_path, doc_type
                    )

                    # Extract data with text extraction
                    print(f"[v0] Extracting text from {doc_type}...")
                    extracted_data = extract_text_from_image(file_path, doc_type)
                    print(
                        f"[v0] Extraction result: {extracted_data.get('status', 'unknown')}"
                    )

                    # Add to database
                    doc_id = VerificationService.add_document(
                        verification_id, doc_type, file_path, extracted_data
                    )

                    # Check if document is high risk
                    if extracted_data.get("is_high_risk", False):
                        high_risk_documents.append(
                            {
                                "document_type": doc_type,
                                "expiry_date": extracted_data.get(
                                    "expiry_date", "Unknown"
                                ),
                                "doc_id": doc_id,
                            }
                        )
                        print(
                            f"[v0] HIGH RISK document detected: {doc_type} expiring {extracted_data.get('expiry_date')}"
                        )

                    # Mock FirmCheck verification
                    VerificationService.verify_with_firmcheck(doc_id, extracted_data)

        # Send admin notification
        EmailService.send_admin_notification(
            verification_id, user_email, [{"type": dt} for dt in doc_types]
        )

        # Send high-risk warning email to user if any high-risk documents
        if high_risk_documents:
            print(f"[v0] Sending high-risk warning email to {user_email}")
            EmailService.send_high_risk_document_warning(
                user_email, user_name, high_risk_documents
            )

        return redirect(url_for("user_dashboard"))

    return render_template(
        "submit_documents.html", doc_types=VerificationService.DOCUMENT_TYPES
    )


@app.route("/verification/<verification_id>")
def verification_detail(verification_id):
    if not is_authenticated():
        return redirect(url_for("login"))

    verification = VerificationService.get_verification(verification_id)

    if not verification:
        return "Verification not found", 404

    return render_template("verification_detail.html", verification=verification)


# ==================== Routes: Admin ====================


@app.route("/admin/dashboard")
def admin_dashboard():
    if not is_authenticated() or get_user_role() != "admin":
        return redirect(url_for("login"))

    verifications = db.get_verifications_collection()

    # Get pending verifications
    pending = list(verifications.find({"status": {"$in": ["pending", "under_review"]}}))
    for v in pending:
        v["_id"] = str(v["_id"])

    # Get stats
    stats = VerificationService.get_today_stats()

    return render_template("admin_dashboard.html", verifications=pending, stats=stats)


@app.route("/admin/approve/<verification_id>", methods=["POST"])
def admin_approve(verification_id):
    if not is_authenticated() or get_user_role() != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    notes = data.get("notes", "")
    admin_email = session.get("user_email")

    VerificationService.approve_by_admin(verification_id, admin_email, notes)

    # Send email to user
    verifications = db.get_verifications_collection()
    verification = verifications.find_one({"_id": ObjectId(verification_id)})

    if verification:
        EmailService.send_email(
            verification["user_email"],
            "Your Verification Status Updated",
            f"<p>Your verification has been reviewed by our admin team. Pending CEO approval.</p>",
        )

    return jsonify({"success": True})


@app.route("/admin/reject/<verification_id>", methods=["POST"])
def admin_reject(verification_id):
    if not is_authenticated() or get_user_role() != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    reason = data.get("reason", "")

    verifications = db.get_verifications_collection()
    verifications.update_one(
        {"_id": ObjectId(verification_id)},
        {
            "$set": {
                "status": "rejected",
                "admin_notes": reason,
                "updated_at": datetime.utcnow(),
            }
        },
    )

    # Get verification for notification
    verification = verifications.find_one({"_id": ObjectId(verification_id)})
    if verification:
        missing = [doc for doc in verification["documents"]]
        EmailService.send_verification_reminder(
            verification["user_email"], verification_id, missing
        )

    return jsonify({"success": True})


# ==================== Routes: CEO ====================


@app.route("/analytics")
def analytics_dashboard():
    if not is_authenticated():
        return redirect(url_for("login"))

    return render_template("analytics_dashboard.html")


@app.route("/ceo/dashboard")
def ceo_dashboard():
    if not is_authenticated() or get_user_role() != "ceo":
        return redirect(url_for("login"))

    verifications = db.get_verifications_collection()

    # Get verifications pending CEO review
    pending = list(verifications.find({"status": "ceo_review"}))
    for v in pending:
        v["_id"] = str(v["_id"])

    # Get stats
    stats = VerificationService.get_today_stats()

    return render_template("ceo_dashboard.html", verifications=pending, stats=stats)


@app.route("/ceo/approve/<verification_id>", methods=["POST"])
def ceo_approve(verification_id):
    if not is_authenticated() or get_user_role() != "ceo":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    notes = data.get("notes", "")
    ceo_email = session.get("user_email")

    VerificationService.approve_by_ceo(verification_id, ceo_email, notes)

    # Send email to user
    verifications = db.get_verifications_collection()
    verification = verifications.find_one({"_id": ObjectId(verification_id)})

    if verification:
        EmailService.send_email(
            verification["user_email"],
            "Your Verification Approved",
            f"<p>Congratulations! Your verification has been approved by our CEO. Your documents are cleared.</p>",
        )

    return jsonify({"success": True})


@app.route("/ceo/reject/<verification_id>", methods=["POST"])
def ceo_reject(verification_id):
    if not is_authenticated() or get_user_role() != "ceo":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    reason = data.get("reason", "")

    verifications = db.get_verifications_collection()
    verifications.update_one(
        {"_id": ObjectId(verification_id)},
        {
            "$set": {
                "status": "rejected",
                "ceo_notes": reason,
                "updated_at": datetime.utcnow(),
            }
        },
    )

    # Get verification for notification
    verification = verifications.find_one({"_id": ObjectId(verification_id)})
    if verification:
        EmailService.send_email(
            verification["user_email"],
            "Verification Status",
            f"<p>Your verification was not approved. Reason: {reason}</p><p>Please resubmit with additional documentation.</p>",
        )

    return jsonify({"success": True})


# ==================== API Routes ====================


@app.route("/api/stats")
def api_stats():
    if not is_authenticated():
        return jsonify({"error": "Unauthorized"}), 401

    stats = VerificationService.get_today_stats()
    return jsonify(stats)


@app.route("/api/workflow-stats")
def api_workflow_stats():
    if not is_authenticated():
        return jsonify({"error": "Unauthorized"}), 401

    stats = ApprovalService.get_workflow_statistics()
    return jsonify(stats)


@app.route("/api/dashboard-data")
def api_dashboard_data():
    if not is_authenticated():
        return jsonify({"error": "Unauthorized"}), 401

    role = get_user_role()

    data = {
        "today_stats": VerificationService.get_today_stats(),
        "workflow_stats": ApprovalService.get_workflow_statistics(),
        "role": role,
    }

    if role == "admin":
        data["pending_verifications"] = ApprovalService.get_pending_for_admin()
    elif role == "ceo":
        data["pending_verifications"] = ApprovalService.get_pending_for_ceo()
    elif role == "user":
        user_email = session.get("user_email")
        verifications = db.get_verifications_collection()
        user_verifications = list(verifications.find({"user_email": user_email}))
        for v in user_verifications:
            v["_id"] = str(v["_id"])
        data["verifications"] = user_verifications

    return jsonify(data)


@app.route("/dev/create-test-data")
def create_test_data():
    """Create test verification data for development"""
    verifications = db.get_verifications_collection()
    approvals = db.get_approvals_collection()

    # Clear existing test data
    verifications.delete_many({"user_email": "test@example.com"})
    approvals.delete_many({})

    # Create test verifications
    test_verifs = [
        {
            "user_email": "test@example.com",
            "user_name": "Test User 1",
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "documents": ["license", "id"],
            "admin_approved": False,
            "admin_notes": "",
            "ceo_approved": False,
            "ceo_notes": "",
            "cleared": False,
            "cleared_at": None,
        },
        {
            "user_email": "test@example.com",
            "user_name": "Test User 2",
            "status": "ceo_review",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "documents": ["passport", "proof_of_address"],
            "admin_approved": True,
            "admin_notes": "Looks good",
            "ceo_approved": False,
            "ceo_notes": "",
            "cleared": False,
            "cleared_at": None,
        },
        {
            "user_email": "test@example.com",
            "user_name": "Test User 3",
            "status": "approved",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "documents": ["license"],
            "admin_approved": True,
            "admin_notes": "Approved by admin",
            "ceo_approved": True,
            "ceo_notes": "Approved by CEO",
            "cleared": True,
            "cleared_at": datetime.utcnow(),
        },
    ]

    result = verifications.insert_many(test_verifs)

    return jsonify(
        {
            "success": True,
            "message": f"Created {len(result.inserted_ids)} test verifications",
            "ids": [str(id) for id in result.inserted_ids],
        }
    )


@app.route("/api/verifications")
def api_verifications():
    if not is_authenticated():
        return jsonify({"error": "Unauthorized"}), 401

    role = get_user_role()
    verifications = db.get_verifications_collection()

    if role == "user":
        user_email = session.get("user_email")
        query = {"user_email": user_email}
    elif role == "admin":
        query = {"status": {"$in": ["pending", "under_review"]}}
    elif role == "ceo":
        query = {"status": "ceo_review"}
    else:
        return jsonify({"error": "Invalid role"}), 400

    items = list(verifications.find(query))
    for item in items:
        item["_id"] = str(item["_id"])
        item["created_at"] = item["created_at"].isoformat()
        item["updated_at"] = item["updated_at"].isoformat()

    return jsonify(items)


@app.route("/api/send-daily-summary", methods=["POST"])
def send_daily_summary():
    """Endpoint for scheduled task to send CEO daily summary"""
    if request.headers.get("X-API-KEY") != os.getenv("API_KEY", "secret"):
        return jsonify({"error": "Unauthorized"}), 401

    stats = VerificationService.get_today_stats()
    EmailService.send_ceo_summary(stats)

    return jsonify({"success": True, "summary_sent": True})


@app.route("/api/document/<document_id>/extracted-text")
def get_extracted_text(document_id):
    """Get extracted text content from a document"""
    if not is_authenticated():
        return jsonify({"error": "Unauthorized"}), 401

    try:
        documents = db.get_documents_collection()
        document = documents.find_one({"_id": ObjectId(document_id)})

        if not document:
            return jsonify({"error": "Document not found"}), 404

        # Get verification to check if user has access
        verification_id = document.get("verification_id")
        verifications = db.get_verifications_collection()
        verification = verifications.find_one({"_id": verification_id})

        if not verification:
            return jsonify({"error": "Verification not found"}), 404

        # Check authorization
        user_role = get_user_role()
        user_email = session.get("user_email")

        if user_role == "user" and verification["user_email"] != user_email:
            return jsonify({"error": "Unauthorized"}), 401

        # Extract text from document
        extracted_data = document.get("extracted_data", {})
        full_text = extracted_data.get("full_text", "No text extracted")
        extracted_fields = extracted_data.get("extracted_fields", {})

        return jsonify(
            {
                "success": True,
                "document_type": document.get("document_type"),
                "full_text": full_text,
                "extracted_fields": extracted_fields,
                "extracted_at": (
                    document.get("uploaded_at").isoformat()
                    if document.get("uploaded_at")
                    else None
                ),
            }
        )

    except Exception as e:
        return jsonify({"error": f"Error retrieving document: {str(e)}"}), 500


@app.route("/api/verification/<verification_id>/documents")
def get_verification_documents(verification_id):
    """Get all documents for a verification with extracted text and risk status"""
    if not is_authenticated():
        return jsonify({"error": "Unauthorized"}), 401

    try:
        verifications = db.get_verifications_collection()
        verification = verifications.find_one({"_id": ObjectId(verification_id)})

        if not verification:
            return jsonify({"error": "Verification not found"}), 404

        # Check authorization
        user_role = get_user_role()
        user_email = session.get("user_email")

        if user_role == "user" and verification["user_email"] != user_email:
            return jsonify({"error": "Unauthorized"}), 401

        # Get all documents for this verification
        documents = db.get_documents_collection()
        docs = list(documents.find({"verification_id": ObjectId(verification_id)}))

        docs_list = []
        for doc in docs:
            extracted_data = doc.get("extracted_data", {})
            docs_list.append(
                {
                    "id": str(doc["_id"]),
                    "document_type": doc.get("document_type"),
                    "full_text": extracted_data.get("full_text", "No text extracted"),
                    "extracted_fields": extracted_data.get("extracted_fields", {}),
                    "uploaded_at": (
                        doc.get("uploaded_at").isoformat()
                        if doc.get("uploaded_at")
                        else None
                    ),
                    "firmcheck_status": doc.get("firmcheck_status", "pending"),
                    "expiry_date": extracted_data.get("expiry_date", None),
                    "is_high_risk": extracted_data.get("is_high_risk", False),
                    "extraction_method": extracted_data.get(
                        "extraction_method", "unknown"
                    ),
                }
            )

        return jsonify(
            {
                "success": True,
                "verification_id": verification_id,
                "documents": docs_list,
            }
        )

    except Exception as e:
        return jsonify({"error": f"Error retrieving documents: {str(e)}"}), 500


# ==================== Error Handlers ====================


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500


# ==================== Main ====================

if __name__ == "__main__":
    app.run(debug=Config.DEBUG, host="0.0.0.0", port=5000)
