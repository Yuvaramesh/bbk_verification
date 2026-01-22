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
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = Config.EMAIL_USER
            msg['To'] = recipient
            
            if plain_text:
                part1 = MIMEText(plain_text, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(Config.EMAIL_HOST, Config.EMAIL_PORT) as server:
                server.starttls()
                server.login(Config.EMAIL_USER, Config.EMAIL_PASSWORD)
                server.sendmail(Config.EMAIL_USER, recipient, msg.as_string())
            
            # Log email
            email_logs = db.get_email_logs_collection()
            email_logs.insert_one({
                'recipient': recipient,
                'subject': subject,
                'sent_at': datetime.utcnow(),
                'status': 'sent'
            })
            
            return True
        except Exception as e:
            print(f"Error sending email to {recipient}: {str(e)}")
            email_logs = db.get_email_logs_collection()
            email_logs.insert_one({
                'recipient': recipient,
                'subject': subject,
                'sent_at': datetime.utcnow(),
                'status': 'failed',
                'error': str(e)
            })
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
        """Send email to admin team about new verification"""
        subject = f"New Verification Request - {verification_id}"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>New Verification Request</h2>
                <p>A new verification request has been submitted.</p>
                <p><strong>Verification ID:</strong> {verification_id}</p>
                <p><strong>User Email:</strong> {user_email}</p>
                <p><strong>Documents:</strong></p>
                <ul>
                    {''.join([f"<li>{doc['type']}</li>" for doc in documents])}
                </ul>
                <p>
                    <a href="http://localhost:5000/admin/dashboard" 
                       style="background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        Review in Dashboard
                    </a>
                </p>
            </body>
        </html>
        """
        
        for admin_email in Config.ADMIN_EMAILS:
            EmailService.send_email(admin_email, subject, html_content)
    
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
