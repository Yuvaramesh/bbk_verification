import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from config import Config
from database import db


class EmailService:
    """Handle email notifications"""

    @staticmethod
    def send_email(recipient, subject, html_content, plain_text=None):
        """Send email using Gmail SMTP"""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = Config.EMAIL_USER
            msg["To"] = recipient

            if plain_text:
                part1 = MIMEText(plain_text, "plain")
                msg.attach(part1)

            part2 = MIMEText(html_content, "html")
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(Config.EMAIL_HOST, Config.EMAIL_PORT) as server:
                server.starttls()
                server.login(Config.EMAIL_USER, Config.EMAIL_PASSWORD)
                server.sendmail(Config.EMAIL_USER, recipient, msg.as_string())

            # Log email
            email_logs = db.get_email_logs_collection()
            email_logs.insert_one(
                {
                    "recipient": recipient,
                    "subject": subject,
                    "sent_at": datetime.utcnow(),
                    "status": "sent",
                }
            )

            return True
        except Exception as e:
            print(f"Error sending email to {recipient}: {str(e)}")
            email_logs = db.get_email_logs_collection()
            email_logs.insert_one(
                {
                    "recipient": recipient,
                    "subject": subject,
                    "sent_at": datetime.utcnow(),
                    "status": "failed",
                    "error": str(e),
                }
            )
            return False

    @staticmethod
    def send_verification_reminder(user_email, verification_id, missing_docs):
        """Send email to user about pending verification"""
        subject = "Action Required: Complete Your Verification"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Verification Required</h2>
                <p>Dear User,</p>
                <p>Your document verification is incomplete. Please submit the following documents:</p>
                <ul>
                    {''.join([f"<li>{doc}</li>" for doc in missing_docs])}
                </ul>
                <p>
                    <a href="http://localhost:5000/submit?verification_id={verification_id}" 
                       style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        Complete Verification
                    </a>
                </p>
                <p>Best regards,<br>Verification Team</p>
            </body>
        </html>
        """

        plain_text = f"Please submit the following documents: {', '.join(missing_docs)}"

        return EmailService.send_email(user_email, subject, html_content, plain_text)

    @staticmethod
    def send_admin_notification(verification_id, user_email, documents):
        """Send email to admin team about new verification with extracted content"""
        from bson.objectid import ObjectId
        from datetime import datetime, timedelta

        subject = f"New Verification Request - {verification_id}"

        # Get extracted text from documents
        docs_collection = db.get_documents_collection()
        doc_records = list(
            docs_collection.find({"verification_id": ObjectId(verification_id)})
        )

        documents_info = ""
        high_risk_documents = []

        for doc in doc_records:
            extracted_data = doc.get("extracted_data", {})
            full_text = extracted_data.get("full_text", "No text extracted")
            doc_type = doc.get("document_type", "Unknown")
            is_high_risk = extracted_data.get("is_high_risk", False)
            expiry_date = extracted_data.get("expiry_date", None)

            # Truncate text for email readability
            text_preview = (
                full_text[:500] + "..." if len(full_text) > 500 else full_text
            )

            risk_badge = (
                '<span style="background-color: #dc2626; color: white; padding: 4px 8px; border-radius: 3px; font-size: 0.85rem;">⚠️ HIGH RISK - EXPIRING WITHIN 180 DAYS</span>'
                if is_high_risk
                else ""
            )

            documents_info += f"""
            <div style="margin: 1rem 0; padding: 1rem; background-color: {'#fef2f2' if is_high_risk else '#f3f4f6'}; border-left: 4px solid {'#dc2626' if is_high_risk else '#2196F3'};">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <h4 style="margin-top: 0;">{doc_type.upper()}</h4>
                    {risk_badge}
                </div>
                {f'<p><strong>Expiry Date:</strong> {expiry_date}</p>' if expiry_date else ''}
                <p><strong>Extracted Content (Preview):</strong></p>
                <p style="font-size: 0.9rem; color: #4b5563; white-space: pre-wrap;">{text_preview}</p>
                <p style="margin: 0.5rem 0 0 0;">
                    <a href="http://localhost:5000/admin/dashboard" 
                       style="color: #2196F3; text-decoration: none; font-size: 0.85rem;">
                        View Full Content in Dashboard →
                    </a>
                </p>
            </div>
            """

            if is_high_risk:
                high_risk_documents.append(
                    {"type": doc_type, "expiry_date": expiry_date}
                )

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>New Verification Request</h2>
                <p>A new verification request has been submitted.</p>
                <p><strong>Verification ID:</strong> {verification_id}</p>
                <p><strong>User Email:</strong> {user_email}</p>
                <p><strong>Documents Submitted:</strong></p>
                <ul>
                    {''.join([f"<li>{doc['type']}</li>" for doc in documents])}
                </ul>
                
                {f'<div style="background-color: #fee2e2; border-left: 4px solid #dc2626; padding: 1rem; margin: 1rem 0;"><strong style="color: #dc2626;">⚠️ ATTENTION: {len(high_risk_documents)} HIGH RISK DOCUMENT(S) DETECTED</strong><p>These documents are expiring within 180 days and require immediate review.</p></div>' if high_risk_documents else ''}
                
                <h3>Extracted Content from Documents:</h3>
                {documents_info}
                
                <p style="margin-top: 2rem;">
                    <a href="http://localhost:5000/admin/dashboard" 
                       style="background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        Review Full Verification in Dashboard
                    </a>
                </p>
            </body>
        </html>
        """

        for admin_email in Config.ADMIN_EMAILS:
            EmailService.send_email(admin_email, subject, html_content)

    @staticmethod
    def send_high_risk_document_warning(user_email, user_name, high_risk_docs):
        """Send email to user about high-risk documents expiring within 180 days"""
        subject = "⚠️ Action Required: Your Documents Are Expiring Soon"

        docs_list = ""
        for doc in high_risk_docs:
            docs_list += f"""
            <li>
                <strong>{doc['document_type'].upper()}</strong> - Expires on {doc['expiry_date']}
                <p style="margin: 5px 0; color: #666;">Please renew this document to continue verification.</p>
            </li>
            """

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2 style="color: #dc2626;">⚠️ Action Required: Renew Your Documents</h2>
                <p>Dear {user_name},</p>
                <p>We've detected that the following documents submitted for verification are expiring within 180 days:</p>
                
                <div style="background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 1rem; margin: 1rem 0;">
                    <ul style="margin: 0;">
                        {docs_list}
                    </ul>
                </div>
                
                <p><strong>What you need to do:</strong></p>
                <p>Please renew these documents and resubmit them for verification. Without renewal, your verification status may be affected.</p>
                
                <p style="margin-top: 2rem;">
                    <a href="http://localhost:5000/submit" 
                       style="background-color: #dc2626; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Resubmit Documents
                    </a>
                </p>
                
                <p style="margin-top: 2rem; font-size: 0.9rem; color: #666;">
                    If you have any questions, please contact our support team.<br>
                    Best regards,<br>
                    Verification Team
                </p>
            </body>
        </html>
        """

        return EmailService.send_email(user_email, subject, html_content)

    @staticmethod
    def send_ceo_summary(summary_data):
        """Send daily summary to CEO"""
        subject = "Daily Verification Summary"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Daily Verification Summary</h2>
                <p>Hello CEO,</p>
                <p><strong>Total Emails Today:</strong> {summary_data['total_emails']}</p>
                <p><strong>Pending Verifications:</strong> {summary_data['pending']}</p>
                <p><strong>Admin Approved:</strong> {summary_data['admin_approved']}</p>
                <p><strong>CEO Approved:</strong> {summary_data['ceo_approved']}</p>
                <p><strong>Cleared/Completed:</strong> {summary_data['cleared']}</p>
                <p><strong>Remaining to Review:</strong> {summary_data['remaining']}</p>
                <p>
                    <a href="http://localhost:5000/ceo/dashboard" 
                       style="background-color: #FF9800; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        View Full Dashboard
                    </a>
                </p>
            </body>
        </html>
        """

        EmailService.send_email(Config.CEO_EMAIL, subject, html_content)
