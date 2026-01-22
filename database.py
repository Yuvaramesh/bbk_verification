from pymongo import MongoClient
from datetime import datetime
from config import Config

class Database:
    """MongoDB connection and collection management"""
    
    def __init__(self):
        self.client = MongoClient(Config.MONGODB_URI)
        self.db = self.client[Config.MONGODB_DB]
        self._init_collections()
    
    def _init_collections(self):
        """Initialize collections if they don't exist"""
        if 'verifications' not in self.db.list_collection_names():
            self.db.create_collection('verifications')
            self.db['verifications'].create_index('user_id')
            self.db['verifications'].create_index('status')
            self.db['verifications'].create_index('created_at')
        
        if 'documents' not in self.db.list_collection_names():
            self.db.create_collection('documents')
            self.db['documents'].create_index('verification_id')
            self.db['documents'].create_index('document_type')
        
        if 'approvals' not in self.db.list_collection_names():
            self.db.create_collection('approvals')
            self.db['approvals'].create_index('verification_id')
            self.db['approvals'].create_index('approver_type')
        
        if 'email_logs' not in self.db.list_collection_names():
            self.db.create_collection('email_logs')
            self.db['email_logs'].create_index('recipient')
            self.db['email_logs'].create_index('sent_at')
    
    def get_verifications_collection(self):
        return self.db['verifications']
    
    def get_documents_collection(self):
        return self.db['documents']
    
    def get_approvals_collection(self):
        return self.db['approvals']
    
    def get_email_logs_collection(self):
        return self.db['email_logs']
    
    def close(self):
        self.client.close()

# Initialize database
db = Database()
