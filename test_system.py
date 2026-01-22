#!/usr/bin/env python3
"""
Test script to verify the verification system functionality
"""

from database import db
from verification_service import VerificationService
from email_service import EmailService
from document_processor import DocumentProcessor
from datetime import datetime
import json

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_database():
    """Test database connection"""
    print_section("Testing Database Connection")
    try:
        verifications = db.get_verifications_collection()
        count = verifications.count_documents({})
        print(f"✓ Database connected successfully")
        print(f"  Total verifications: {count}")
        return True
    except Exception as e:
        print(f"✗ Database error: {str(e)}")
        return False

def test_verification_creation():
    """Test creating a verification"""
    print_section("Testing Verification Creation")
    try:
        verification_id = VerificationService.create_verification(
            'test@example.com',
            'Test User',
            ['license', 'id']
        )
        print(f"✓ Verification created successfully")
        print(f"  ID: {verification_id}")
        
        # Retrieve and display
        verification = VerificationService.get_verification(verification_id)
        print(f"  Status: {verification['status']}")
        print(f"  Documents: {', '.join(verification['documents'])}")
        
        return verification_id
    except Exception as e:
        print(f"✗ Error creating verification: {str(e)}")
        return None

def test_document_processing():
    """Test document processing"""
    print_section("Testing Document Processing")
    try:
        # Test extracting from license
        result = DocumentProcessor._mock_extract_fields('license')
        print(f"✓ License data extraction successful")
        print(f"  Name: {result.get('holder_name')}")
        print(f"  License #: {result.get('document_number')}")
        print(f"  Expiry: {result.get('expiry_date')}")
        
        # Test other document types
        document_types = ['id', 'proof_of_address', 'bank_statement', 'utility_bill', 'passport']
        print(f"\n  Other document types:")
        for doc_type in document_types:
            data = DocumentProcessor._mock_extract_fields(doc_type)
            print(f"    - {doc_type}: {list(data.keys())[:3]}...")
        
        return True
    except Exception as e:
        print(f"✗ Error processing documents: {str(e)}")
        return False

def test_approval_workflow(verification_id):
    """Test approval workflow"""
    print_section("Testing Approval Workflow")
    try:
        # Test admin approval
        print("1. Admin Review & Approval")
        VerificationService.approve_by_admin(
            verification_id,
            'admin@company.com',
            'Documents look good. Forwarding to CEO.'
        )
        print(f"   ✓ Admin approved")
        
        verification = VerificationService.get_verification(verification_id)
        print(f"   Status: {verification['status']}")
        print(f"   Admin Approved: {verification['admin_approved']}")
        
        # Test CEO approval
        print("\n2. CEO Final Review & Approval")
        VerificationService.approve_by_ceo(
            verification_id,
            'ceo@company.com',
            'All verified. Cleared for processing.'
        )
        print(f"   ✓ CEO approved and cleared")
        
        verification = VerificationService.get_verification(verification_id)
        print(f"   Status: {verification['status']}")
        print(f"   CEO Approved: {verification['ceo_approved']}")
        print(f"   Cleared: {verification['cleared']}")
        
        return True
    except Exception as e:
        print(f"✗ Error in approval workflow: {str(e)}")
        return False

def test_statistics():
    """Test statistics generation"""
    print_section("Testing Statistics Generation")
    try:
        stats = VerificationService.get_today_stats()
        print(f"✓ Statistics generated successfully")
        print(f"  Total today: {stats['total_emails']}")
        print(f"  Pending: {stats['pending']}")
        print(f"  Admin approved: {stats['admin_approved']}")
        print(f"  CEO approved: {stats['ceo_approved']}")
        print(f"  Cleared: {stats['cleared']}")
        print(f"  Remaining: {stats['remaining']}")
        return True
    except Exception as e:
        print(f"✗ Error generating statistics: {str(e)}")
        return False

def test_database_collections():
    """Test all database collections"""
    print_section("Testing Database Collections")
    try:
        collections = {
            'verifications': db.get_verifications_collection(),
            'documents': db.get_documents_collection(),
            'approvals': db.get_approvals_collection(),
            'email_logs': db.get_email_logs_collection()
        }
        
        for name, collection in collections.items():
            count = collection.count_documents({})
            print(f"✓ {name}: {count} records")
        
        return True
    except Exception as e:
        print(f"✗ Error accessing collections: {str(e)}")
        return False

def run_full_test():
    """Run all tests"""
    print("\n" + "="*60)
    print("  BBK Verification System - Test Suite")
    print("="*60)
    
    results = {
        'Database Connection': test_database(),
        'Database Collections': test_database_collections(),
        'Document Processing': test_document_processing(),
        'Statistics': test_statistics(),
    }
    
    # Create test verification
    verification_id = test_verification_creation()
    if verification_id:
        results['Approval Workflow'] = test_approval_workflow(verification_id)
    
    # Print summary
    print_section("Test Summary")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} - {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! System is ready.")
        return True
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please review.")
        return False

if __name__ == '__main__':
    import sys
    success = run_full_test()
    sys.exit(0 if success else 1)
