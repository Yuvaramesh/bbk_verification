"""
Scheduler for automated tasks
Can be run separately or integrated with APScheduler
"""

from datetime import datetime, time
from email_service import EmailService
from verification_service import VerificationService
from approval_service import ApprovalService
import schedule
import time as time_module

class TaskScheduler:
    """Handle scheduled tasks"""
    
    @staticmethod
    def send_daily_ceo_summary():
        """Send daily summary email to CEO"""
        print(f"[{datetime.utcnow()}] Running daily CEO summary task...")
        
        try:
            stats = VerificationService.get_today_stats()
            EmailService.send_ceo_summary(stats)
            print("✓ CEO summary sent successfully")
            return True
        except Exception as e:
            print(f"✗ Error sending CEO summary: {str(e)}")
            return False
    
    @staticmethod
    def send_admin_pending_notification():
        """Send notification to admin about pending verifications"""
        print(f"[{datetime.utcnow()}] Running admin notification task...")
        
        try:
            pending = ApprovalService.get_pending_for_admin()
            
            if not pending:
                print("✓ No pending verifications - all clear")
                return True
            
            # Send notification
            from config import Config
            message = f"""
            <p>You have {len(pending)} pending verification(s) requiring review:</p>
            <ul>
                {''.join([f"<li>{v['user_email']} - {v['user_name']}</li>" for v in pending[:10]])}
                {f"<li>... and {len(pending) - 10} more</li>" if len(pending) > 10 else ""}
            </ul>
            <p><a href="http://localhost:5000/admin/dashboard">Review in Dashboard</a></p>
            """
            
            for admin_email in Config.ADMIN_EMAILS:
                EmailService.send_email(
                    admin_email,
                    f"Action Required: {len(pending)} Verifications Pending Review",
                    message
                )
            
            print(f"✓ Admin notifications sent for {len(pending)} pending items")
            return True
        
        except Exception as e:
            print(f"✗ Error sending admin notification: {str(e)}")
            return False
    
    @staticmethod
    def cleanup_old_files():
        """Clean up old uploaded files"""
        print(f"[{datetime.utcnow()}] Running cleanup task...")
        
        try:
            import os
            from datetime import datetime, timedelta
            from config import Config
            
            upload_dir = Config.UPLOAD_FOLDER
            if not os.path.exists(upload_dir):
                print("✓ Upload directory doesn't exist - nothing to clean")
                return True
            
            # Delete files older than 30 days
            cutoff_time = datetime.utcnow() - timedelta(days=30)
            deleted_count = 0
            
            for filename in os.listdir(upload_dir):
                file_path = os.path.join(upload_dir, filename)
                
                if os.path.isfile(file_path):
                    file_time = datetime.utcfromtimestamp(os.path.getmtime(file_path))
                    
                    if file_time < cutoff_time:
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                        except Exception as e:
                            print(f"  Warning: Could not delete {filename}: {str(e)}")
            
            print(f"✓ Cleanup complete - {deleted_count} old files deleted")
            return True
        
        except Exception as e:
            print(f"✗ Error during cleanup: {str(e)}")
            return False
    
    @staticmethod
    def check_expired_documents():
        """Check for expired documents and notify users"""
        print(f"[{datetime.utcnow()}] Checking for expired documents...")
        
        try:
            from database import db
            from datetime import datetime, timedelta
            
            documents = db.get_documents_collection()
            verifications = db.get_verifications_collection()
            
            # Find documents with expired dates
            thirty_days_later = datetime.utcnow() + timedelta(days=30)
            
            expired_docs = list(documents.find({
                'firmcheck_result.details.expiry_date': {
                    '$lt': thirty_days_later.isoformat()
                }
            }))
            
            if not expired_docs:
                print("✓ No documents expiring soon")
                return True
            
            # Group by verification and notify users
            notifications_sent = 0
            
            for doc in expired_docs:
                verification = verifications.find_one({
                    '_id': doc['verification_id']
                })
                
                if verification:
                    expiry_date = doc.get('firmcheck_result', {}).get('details', {}).get('expiry_date')
                    
                    message = f"""
                    <p>Dear {verification.get('user_name')},</p>
                    <p>Your {doc.get('document_type')} will expire on {expiry_date}.</p>
                    <p>Please renew your documents to maintain your verification status.</p>
                    """
                    
                    EmailService.send_email(
                        verification['user_email'],
                        f"Document Expiration Notice - {doc.get('document_type')}",
                        message
                    )
                    
                    notifications_sent += 1
            
            print(f"✓ Expiration notifications sent: {notifications_sent}")
            return True
        
        except Exception as e:
            print(f"✗ Error checking expired documents: {str(e)}")
            return False
    
    @staticmethod
    def archive_old_verifications():
        """Archive verifications older than 1 year"""
        print(f"[{datetime.utcnow()}] Running archive task...")
        
        try:
            from database import db
            from datetime import datetime, timedelta
            
            verifications = db.get_verifications_collection()
            
            # Find verifications older than 1 year
            cutoff_date = datetime.utcnow() - timedelta(days=365)
            
            result = verifications.update_many(
                {
                    'created_at': {'$lt': cutoff_date},
                    'archived': {'$exists': False}
                },
                {
                    '$set': {
                        'archived': True,
                        'archived_at': datetime.utcnow()
                    }
                }
            )
            
            print(f"✓ Archive complete - {result.modified_count} verifications archived")
            return True
        
        except Exception as e:
            print(f"✗ Error during archiving: {str(e)}")
            return False
    
    @staticmethod
    def setup_schedule():
        """Setup all scheduled tasks using schedule library"""
        print("Setting up scheduled tasks...")
        
        # Daily CEO summary at 5 PM
        schedule.every().day.at("17:00").do(TaskScheduler.send_daily_ceo_summary)
        
        # Admin notifications every 2 hours
        schedule.every(2).hours.do(TaskScheduler.send_admin_pending_notification)
        
        # Check expired documents daily at 8 AM
        schedule.every().day.at("08:00").do(TaskScheduler.check_expired_documents)
        
        # Cleanup every week on Sunday at 2 AM
        schedule.every().sunday.at("02:00").do(TaskScheduler.cleanup_old_files)
        
        # Archive every month on the 1st at 3 AM
        schedule.every().month.do(TaskScheduler.archive_old_verifications)
        
        print("✓ All scheduled tasks configured")
    
    @staticmethod
    def run_scheduler():
        """Run the scheduler (blocking)"""
        print("Starting scheduler...")
        TaskScheduler.setup_schedule()
        
        try:
            while True:
                schedule.run_pending()
                time_module.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\nScheduler stopped")

def run_single_task(task_name):
    """Run a single task by name"""
    tasks = {
        'ceo_summary': TaskScheduler.send_daily_ceo_summary,
        'admin_notification': TaskScheduler.send_admin_pending_notification,
        'cleanup': TaskScheduler.cleanup_old_files,
        'check_expiry': TaskScheduler.check_expired_documents,
        'archive': TaskScheduler.archive_old_verifications,
    }
    
    if task_name in tasks:
        print(f"Running task: {task_name}")
        tasks[task_name]()
    else:
        print(f"Unknown task: {task_name}")
        print(f"Available tasks: {', '.join(tasks.keys())}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        run_single_task(sys.argv[1])
    else:
        TaskScheduler.run_scheduler()
