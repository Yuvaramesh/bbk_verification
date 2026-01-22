from datetime import datetime, timedelta
from bson.objectid import ObjectId
from database import db
from firmcheck_service import FirmCheckService

class ApprovalService:
    """Handle approval workflow management"""
    
    @staticmethod
    def get_pending_for_admin():
        """Get all verifications pending admin review"""
        verifications = db.get_verifications_collection()
        
        pending = list(verifications.find({
            'status': {'$in': ['pending', 'under_review']}
        }).sort('created_at', -1))
        
        for v in pending:
            v['_id'] = str(v['_id'])
        
        return pending
    
    @staticmethod
    def get_pending_for_ceo():
        """Get all verifications pending CEO review"""
        verifications = db.get_verifications_collection()
        
        pending = list(verifications.find({
            'status': 'ceo_review',
            'admin_approved': True
        }).sort('created_at', -1))
        
        for v in pending:
            v['_id'] = str(v['_id'])
        
        return pending
    
    @staticmethod
    def get_approval_history(verification_id):
        """Get approval history for a verification"""
        approvals = db.get_approvals_collection()
        
        history = list(approvals.find({
            'verification_id': ObjectId(verification_id)
        }).sort('approved_at', 1))
        
        for h in history:
            h['_id'] = str(h['_id'])
            h['verification_id'] = str(h['verification_id'])
        
        return history
    
    @staticmethod
    def get_verification_with_documents(verification_id):
        """Get verification with all associated documents and their verification status"""
        verifications = db.get_verifications_collection()
        documents = db.get_documents_collection()
        
        verification = verifications.find_one({'_id': ObjectId(verification_id)})
        
        if not verification:
            return None
        
        verification['_id'] = str(verification['_id'])
        
        # Get documents
        docs = list(documents.find({'verification_id': ObjectId(verification_id)}))
        
        verification['documents_detail'] = []
        for doc in docs:
            doc['_id'] = str(doc['_id'])
            doc['verification_id'] = str(doc['verification_id'])
            verification['documents_detail'].append(doc)
        
        # Calculate overall verification status
        all_verified = all(
            doc.get('firmcheck_status') == 'verified' 
            for doc in verification['documents_detail']
        )
        
        verification['all_documents_verified'] = all_verified
        
        return verification
    
    @staticmethod
    def admin_review(verification_id, admin_email, approval_status, notes=''):
        """Process admin review"""
        verifications = db.get_verifications_collection()
        approvals = db.get_approvals_collection()
        
        verification = verifications.find_one({'_id': ObjectId(verification_id)})
        
        if not verification:
            return {'error': 'Verification not found'}
        
        if approval_status == 'approve':
            # Check if all documents are verified by FirmCheck
            documents = db.get_documents_collection()
            all_verified = all(
                doc.get('firmcheck_status') == 'verified'
                for doc in documents.find({'verification_id': ObjectId(verification_id)})
            )
            
            if not all_verified:
                return {
                    'error': 'Cannot approve: Not all documents are verified by FirmCheck',
                    'status': 'failed'
                }
            
            # Update verification
            verifications.update_one(
                {'_id': ObjectId(verification_id)},
                {
                    '$set': {
                        'admin_approved': True,
                        'admin_notes': notes,
                        'status': 'ceo_review',
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            result_status = 'approved'
        
        elif approval_status == 'reject':
            # Update verification
            verifications.update_one(
                {'_id': ObjectId(verification_id)},
                {
                    '$set': {
                        'admin_approved': False,
                        'admin_notes': notes,
                        'status': 'rejected',
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            result_status = 'rejected'
        
        else:
            return {'error': 'Invalid approval status'}
        
        # Log approval
        approvals.insert_one({
            'verification_id': ObjectId(verification_id),
            'approver_type': 'admin',
            'approver_email': admin_email,
            'approval_status': result_status,
            'notes': notes,
            'approved_at': datetime.utcnow()
        })
        
        return {
            'success': True,
            'status': result_status,
            'message': f'Verification {result_status} by admin'
        }
    
    @staticmethod
    def ceo_review(verification_id, ceo_email, approval_status, notes=''):
        """Process CEO review"""
        verifications = db.get_verifications_collection()
        approvals = db.get_approvals_collection()
        
        verification = verifications.find_one({'_id': ObjectId(verification_id)})
        
        if not verification:
            return {'error': 'Verification not found'}
        
        if approval_status == 'approve':
            # Update verification
            verifications.update_one(
                {'_id': ObjectId(verification_id)},
                {
                    '$set': {
                        'ceo_approved': True,
                        'ceo_notes': notes,
                        'status': 'approved',
                        'cleared': True,
                        'cleared_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            result_status = 'approved'
        
        elif approval_status == 'reject':
            # Update verification
            verifications.update_one(
                {'_id': ObjectId(verification_id)},
                {
                    '$set': {
                        'ceo_approved': False,
                        'ceo_notes': notes,
                        'status': 'rejected',
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            result_status = 'rejected'
        
        else:
            return {'error': 'Invalid approval status'}
        
        # Log approval
        approvals.insert_one({
            'verification_id': ObjectId(verification_id),
            'approver_type': 'ceo',
            'approver_email': ceo_email,
            'approval_status': result_status,
            'notes': notes,
            'approved_at': datetime.utcnow()
        })
        
        return {
            'success': True,
            'status': result_status,
            'message': f'Verification {result_status} by CEO'
        }
    
    @staticmethod
    def get_workflow_statistics():
        """Get overall workflow statistics"""
        verifications = db.get_verifications_collection()
        approvals = db.get_approvals_collection()
        
        total = verifications.count_documents({})
        
        statuses = {
            'pending': verifications.count_documents({'status': 'pending'}),
            'under_review': verifications.count_documents({'status': 'under_review'}),
            'ceo_review': verifications.count_documents({'status': 'ceo_review'}),
            'approved': verifications.count_documents({'status': 'approved'}),
            'rejected': verifications.count_documents({'status': 'rejected'})
        }
        
        approval_counts = {
            'admin_approved': verifications.count_documents({'admin_approved': True}),
            'ceo_approved': verifications.count_documents({'ceo_approved': True}),
            'cleared': verifications.count_documents({'cleared': True})
        }
        
        # Get average approval times
        recent_approvals = list(approvals.find().sort('approved_at', -1).limit(100))
        
        avg_time_to_admin = 0
        avg_time_to_ceo = 0
        
        if recent_approvals:
            times_to_admin = []
            times_to_ceo = []
            
            for approval in recent_approvals:
                verification = verifications.find_one({
                    '_id': approval['verification_id']
                })
                
                if verification and approval['approver_type'] == 'admin':
                    delta = approval['approved_at'] - verification['created_at']
                    times_to_admin.append(delta.total_seconds() / 3600)  # Convert to hours
                
                elif verification and approval['approver_type'] == 'ceo':
                    # Find admin approval time
                    admin_approval = approvals.find_one({
                        'verification_id': approval['verification_id'],
                        'approver_type': 'admin'
                    })
                    
                    if admin_approval:
                        delta = approval['approved_at'] - admin_approval['approved_at']
                        times_to_ceo.append(delta.total_seconds() / 3600)  # Convert to hours
            
            if times_to_admin:
                avg_time_to_admin = sum(times_to_admin) / len(times_to_admin)
            
            if times_to_ceo:
                avg_time_to_ceo = sum(times_to_ceo) / len(times_to_ceo)
        
        return {
            'total_verifications': total,
            'status_breakdown': statuses,
            'approval_counts': approval_counts,
            'avg_time_to_admin_review_hours': round(avg_time_to_admin, 2),
            'avg_time_to_ceo_review_hours': round(avg_time_to_ceo, 2),
            'approval_rate': round((statuses['approved'] / total * 100) if total > 0 else 0, 2),
            'rejection_rate': round((statuses['rejected'] / total * 100) if total > 0 else 0, 2)
        }
    
    @staticmethod
    def get_verifications_by_status(status):
        """Get all verifications with a specific status"""
        verifications = db.get_verifications_collection()
        
        items = list(verifications.find({'status': status}).sort('created_at', -1))
        
        for item in items:
            item['_id'] = str(item['_id'])
        
        return items
    
    @staticmethod
    def bulk_update_status(verification_ids, new_status):
        """Update status for multiple verifications"""
        verifications = db.get_verifications_collection()
        
        object_ids = [ObjectId(vid) for vid in verification_ids]
        
        result = verifications.update_many(
            {'_id': {'$in': object_ids}},
            {
                '$set': {
                    'status': new_status,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        return {
            'matched_count': result.matched_count,
            'modified_count': result.modified_count
        }
