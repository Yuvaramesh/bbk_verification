import requests
import json
from datetime import datetime, timedelta
from config import Config
import random

class FirmCheckService:
    """Handle FirmCheck verification (Mock and Real integration)"""
    
    @staticmethod
    def verify_document(document_data, document_type):
        """Verify document using FirmCheck"""
        
        # Determine which verification method to use
        if Config.FIRMCHECK_API_KEY == 'mock-key':
            return FirmCheckService._mock_verify(document_data, document_type)
        else:
            return FirmCheckService._real_verify(document_data, document_type)
    
    @staticmethod
    def _mock_verify(document_data, document_type):
        """Mock FirmCheck verification"""
        
        verification_result = {
            'verified': True,
            'confidence': random.randint(85, 99),
            'document_type': document_type,
            'verification_method': 'mock',
            'checked_at': datetime.utcnow().isoformat(),
            'details': {}
        }
        
        # Type-specific verification logic
        if document_type == 'license':
            verification_result['details'] = FirmCheckService._verify_license(document_data)
        elif document_type == 'id':
            verification_result['details'] = FirmCheckService._verify_id(document_data)
        elif document_type == 'passport':
            verification_result['details'] = FirmCheckService._verify_passport(document_data)
        elif document_type == 'proof_of_address':
            verification_result['details'] = FirmCheckService._verify_proof_of_address(document_data)
        elif document_type in ['bank_statement', 'utility_bill']:
            verification_result['details'] = FirmCheckService._verify_financial_document(document_data)
        
        # Simulate occasional failures for realistic scenarios
        if random.random() < 0.05:  # 5% failure rate
            verification_result['verified'] = False
            verification_result['reason'] = 'Document verification failed: Unable to match data'
            verification_result['confidence'] = random.randint(30, 60)
        
        return verification_result
    
    @staticmethod
    def _real_verify(document_data, document_type):
        """Call real FirmCheck API"""
        try:
            headers = {
                'Authorization': f'Bearer {Config.FIRMCHECK_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'document_type': document_type,
                'document_data': document_data
            }
            
            response = requests.post(
                Config.FIRMCHECK_API_URL,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'verified': False,
                    'error': f'FirmCheck API error: {response.status_code}',
                    'confidence': 0
                }
        
        except requests.exceptions.RequestException as e:
            return {
                'verified': False,
                'error': f'FirmCheck API connection error: {str(e)}',
                'confidence': 0
            }
    
    @staticmethod
    def _verify_license(document_data):
        """Verify driver's license data"""
        checks = {
            'document_number_format': True,
            'issue_date_valid': True,
            'expiry_date_valid': True,
            'expiry_status': 'valid',
            'class_valid': True,
            'address_format': True
        }
        
        # Check expiry
        if 'expiry_date' in document_data:
            try:
                expiry = datetime.fromisoformat(document_data['expiry_date'])
                if expiry < datetime.utcnow():
                    checks['expiry_status'] = 'expired'
                    checks['expiry_date_valid'] = False
            except:
                pass
        
        return {
            'checks': checks,
            'summary': 'Driver license verified',
            'fields_verified': ['document_number', 'holder_name', 'expiry_date', 'class']
        }
    
    @staticmethod
    def _verify_id(document_data):
        """Verify national ID data"""
        checks = {
            'id_number_format': True,
            'issue_date_valid': True,
            'expiry_date_valid': True,
            'expiry_status': 'valid',
            'nationality_valid': True,
            'address_format': True
        }
        
        # Check expiry
        if 'expiry_date' in document_data:
            try:
                expiry = datetime.fromisoformat(document_data['expiry_date'])
                if expiry < datetime.utcnow():
                    checks['expiry_status'] = 'expired'
                    checks['expiry_date_valid'] = False
            except:
                pass
        
        return {
            'checks': checks,
            'summary': 'National ID verified',
            'fields_verified': ['id_number', 'holder_name', 'nationality', 'expiry_date']
        }
    
    @staticmethod
    def _verify_passport(document_data):
        """Verify passport data"""
        checks = {
            'passport_number_format': True,
            'issue_date_valid': True,
            'expiry_date_valid': True,
            'expiry_status': 'valid',
            'nationality_valid': True,
            'mrz_format': True
        }
        
        # Check expiry
        if 'expiry_date' in document_data:
            try:
                expiry = datetime.fromisoformat(document_data['expiry_date'])
                if expiry < datetime.utcnow():
                    checks['expiry_status'] = 'expired'
                    checks['expiry_date_valid'] = False
            except:
                pass
        
        return {
            'checks': checks,
            'summary': 'Passport verified',
            'fields_verified': ['passport_number', 'holder_name', 'nationality', 'expiry_date']
        }
    
    @staticmethod
    def _verify_proof_of_address(document_data):
        """Verify proof of address"""
        checks = {
            'address_format': True,
            'document_date_valid': True,
            'address_match': True,
            'provider_valid': True
        }
        
        # Check document date (should be recent - within 3 months)
        if 'document_date' in document_data:
            try:
                doc_date = datetime.fromisoformat(document_data['document_date'])
                three_months_ago = datetime.utcnow() - timedelta(days=90)
                if doc_date < three_months_ago:
                    checks['document_date_valid'] = False
                    checks['address_match'] = False
            except:
                pass
        
        return {
            'checks': checks,
            'summary': 'Proof of address verified',
            'fields_verified': ['address', 'holder_name', 'document_date']
        }
    
    @staticmethod
    def _verify_financial_document(document_data):
        """Verify bank statements and utility bills"""
        checks = {
            'document_date_valid': True,
            'account_format_valid': True,
            'amount_valid': True,
            'provider_valid': True
        }
        
        # Check document date (should be recent - within 6 months)
        if 'statement_date' in document_data or 'bill_date' in document_data:
            date_field = document_data.get('statement_date') or document_data.get('bill_date')
            try:
                doc_date = datetime.fromisoformat(date_field)
                six_months_ago = datetime.utcnow() - timedelta(days=180)
                if doc_date < six_months_ago:
                    checks['document_date_valid'] = False
            except:
                pass
        
        return {
            'checks': checks,
            'summary': 'Financial document verified',
            'fields_verified': ['account_holder', 'account_number', 'document_date']
        }
    
    @staticmethod
    def cross_reference_documents(verifications):
        """Cross-reference multiple documents for consistency"""
        
        if not verifications or len(verifications) < 2:
            return {
                'cross_reference_complete': True,
                'issues_found': 0,
                'warnings': []
            }
        
        result = {
            'cross_reference_complete': True,
            'issues_found': 0,
            'warnings': [],
            'checks': {}
        }
        
        # Extract names from all documents
        names = []
        for verification in verifications:
            if 'extracted_fields' in verification:
                name = verification['extracted_fields'].get('holder_name') or \
                       verification['extracted_fields'].get('account_holder')
                if name:
                    names.append(name)
        
        # Check name consistency
        if len(set(names)) > 1:
            result['issues_found'] += 1
            result['warnings'].append('Inconsistent names across documents')
            result['checks']['name_consistency'] = False
        else:
            result['checks']['name_consistency'] = True
        
        # Extract addresses
        addresses = []
        for verification in verifications:
            if 'extracted_fields' in verification:
                address = verification['extracted_fields'].get('address')
                if address:
                    addresses.append(address)
        
        # Check address consistency
        if len(set(addresses)) > 1:
            result['warnings'].append('Different addresses in documents')
        else:
            result['checks']['address_consistency'] = True
        
        return result
    
    @staticmethod
    def get_verification_score(verification_result):
        """Calculate overall verification score"""
        
        if not verification_result:
            return 0
        
        score = verification_result.get('confidence', 0)
        
        # Adjust score based on checks
        if 'details' in verification_result and 'checks' in verification_result['details']:
            checks = verification_result['details']['checks']
            passed_checks = sum(1 for v in checks.values() if v is True)
            total_checks = len(checks)
            
            if total_checks > 0:
                check_score = (passed_checks / total_checks) * 100
                score = (score + check_score) / 2
        
        return int(score)
    
    @staticmethod
    def generate_verification_report(verifications):
        """Generate comprehensive verification report"""
        
        report = {
            'total_documents': len(verifications),
            'verified_documents': 0,
            'failed_documents': 0,
            'overall_score': 0,
            'documents': [],
            'cross_reference': None,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        scores = []
        
        for verification in verifications:
            doc_report = {
                'document_type': verification.get('document_type'),
                'verified': verification.get('verified'),
                'score': FirmCheckService.get_verification_score(verification),
                'confidence': verification.get('confidence')
            }
            
            report['documents'].append(doc_report)
            scores.append(doc_report['score'])
            
            if verification.get('verified'):
                report['verified_documents'] += 1
            else:
                report['failed_documents'] += 1
        
        # Calculate overall score
        if scores:
            report['overall_score'] = int(sum(scores) / len(scores))
        
        # Cross-reference check
        if report['total_documents'] > 1:
            report['cross_reference'] = FirmCheckService.cross_reference_documents(verifications)
        
        return report
