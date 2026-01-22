import os
from PIL import Image
import io
from datetime import datetime

class DocumentProcessor:
    """Handle document processing and data extraction"""
    
    SUPPORTED_FORMATS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}
    
    @staticmethod
    def process_document(file_path, document_type):
        """Process document and extract data"""
        try:
            extracted_data = DocumentProcessor._extract_data(file_path, document_type)
            
            return {
                'status': 'success',
                'extracted_data': extracted_data,
                'processed_at': datetime.utcnow().isoformat(),
                'document_type': document_type,
                'file_size': os.path.getsize(file_path)
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'processed_at': datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def _extract_data(file_path, document_type):
        """Extract data based on document type"""
        
        # Get file extension
        file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        
        if file_ext == 'pdf':
            return DocumentProcessor._extract_from_pdf(file_path, document_type)
        elif file_ext in {'png', 'jpg', 'jpeg', 'gif'}:
            return DocumentProcessor._extract_from_image(file_path, document_type)
        else:
            return {'error': 'Unsupported file format'}
    
    @staticmethod
    def _extract_from_image(file_path, document_type):
        """Extract data from image documents"""
        try:
            # Open image
            image = Image.open(file_path)
            
            # Get image properties
            image_data = {
                'format': image.format,
                'size': image.size,
                'mode': image.mode,
                'dpi': image.info.get('dpi', 'N/A')
            }
            
            # Mock OCR/data extraction
            extracted_fields = DocumentProcessor._mock_extract_fields(document_type)
            
            return {
                'image_properties': image_data,
                'extracted_fields': extracted_fields,
                'full_text': 'Document processed and verified',
                'quality_score': 95,
                'readable': True
            }
        except Exception as e:
            return {'error': f'Failed to process image: {str(e)}'}
    
    @staticmethod
    def _extract_from_pdf(file_path, document_type):
        """Extract data from PDF documents"""
        try:
            # Check if file exists and is readable
            if not os.path.exists(file_path):
                return {'error': 'PDF file not found'}
            
            file_size = os.path.getsize(file_path)
            
            # Mock PDF extraction (in production, use PyPDF2 or pdfplumber)
            extracted_fields = DocumentProcessor._mock_extract_fields(document_type)
            
            return {
                'file_size': file_size,
                'format': 'pdf',
                'extracted_fields': extracted_fields,
                'full_text': 'PDF document processed and analyzed',
                'quality_score': 92,
                'readable': True,
                'pages': 1
            }
        except Exception as e:
            return {'error': f'Failed to process PDF: {str(e)}'}
    
    @staticmethod
    def _mock_extract_fields(document_type):
        """Mock field extraction based on document type"""
        
        mock_data = {
            'license': {
                'document_number': 'DL-2024-789456',
                'holder_name': 'John Doe',
                'date_of_birth': '1990-05-15',
                'issue_date': '2021-03-20',
                'expiry_date': '2026-03-20',
                'class': 'C',
                'address': '123 Main Street, City, State 12345'
            },
            'id': {
                'id_number': 'ID-2024-456789',
                'holder_name': 'John Doe',
                'nationality': 'USA',
                'date_of_birth': '1990-05-15',
                'issue_date': '2020-01-10',
                'expiry_date': '2030-01-10',
                'address': '123 Main Street, City, State 12345'
            },
            'proof_of_address': {
                'document_type': 'Utility Bill',
                'holder_name': 'John Doe',
                'address': '123 Main Street, City, State 12345',
                'document_date': '2024-01-15',
                'provider': 'City Power Company',
                'account_number': 'ACC-789456123'
            },
            'bank_statement': {
                'account_holder': 'John Doe',
                'bank_name': 'National Bank',
                'account_number': 'XXXX-XXXX-XXXX-1234',
                'statement_date': '2024-01-31',
                'account_type': 'Checking',
                'balance': 5000.00
            },
            'utility_bill': {
                'account_holder': 'John Doe',
                'provider': 'City Power Company',
                'account_number': 'ACC-789456123',
                'bill_date': '2024-01-15',
                'address': '123 Main Street, City, State 12345',
                'amount_due': 125.50
            },
            'passport': {
                'passport_number': 'P789456123',
                'holder_name': 'John Doe',
                'nationality': 'USA',
                'date_of_birth': '1990-05-15',
                'gender': 'M',
                'issue_date': '2018-06-01',
                'expiry_date': '2028-06-01',
                'place_of_issue': 'New York'
            }
        }
        
        return mock_data.get(document_type, {
            'document_type': document_type,
            'status': 'extracted',
            'fields': 'Generic document fields'
        })
    
    @staticmethod
    def validate_document(file_path, document_type):
        """Validate document quality and completeness"""
        validation_result = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'quality_score': 100
        }
        
        try:
            # Check file exists
            if not os.path.exists(file_path):
                validation_result['is_valid'] = False
                validation_result['issues'].append('File not found')
                return validation_result
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                validation_result['is_valid'] = False
                validation_result['issues'].append('File is empty')
            
            if file_size > 16 * 1024 * 1024:  # 16MB
                validation_result['is_valid'] = False
                validation_result['issues'].append('File exceeds maximum size (16MB)')
            
            # Check file type
            file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
            if file_ext not in DocumentProcessor.SUPPORTED_FORMATS:
                validation_result['is_valid'] = False
                validation_result['issues'].append(f'Unsupported file format: {file_ext}')
            
            # Validate image if applicable
            if file_ext in {'png', 'jpg', 'jpeg', 'gif'}:
                try:
                    img = Image.open(file_path)
                    width, height = img.size
                    
                    if width < 400 or height < 300:
                        validation_result['quality_score'] -= 20
                        validation_result['warnings'].append('Image resolution is low')
                    
                    # Check if image is readable (basic check)
                    if img.mode not in {'RGB', 'RGBA', 'L'}:
                        validation_result['quality_score'] -= 10
                        validation_result['warnings'].append('Image color mode may affect readability')
                
                except Exception as e:
                    validation_result['is_valid'] = False
                    validation_result['issues'].append(f'Invalid image file: {str(e)}')
            
            return validation_result
        
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['issues'].append(f'Validation error: {str(e)}')
            return validation_result
    
    @staticmethod
    def get_document_summary(extracted_data, document_type):
        """Generate a summary of extracted document data"""
        
        summary = {
            'document_type': document_type,
            'extraction_complete': True,
            'key_fields': {}
        }
        
        if isinstance(extracted_data, dict) and 'extracted_fields' in extracted_data:
            fields = extracted_data['extracted_fields']
            
            # Extract key identification fields
            if document_type == 'license':
                summary['key_fields'] = {
                    'name': fields.get('holder_name'),
                    'number': fields.get('document_number'),
                    'expiry': fields.get('expiry_date')
                }
            elif document_type == 'id':
                summary['key_fields'] = {
                    'name': fields.get('holder_name'),
                    'id_number': fields.get('id_number'),
                    'expiry': fields.get('expiry_date')
                }
            elif document_type == 'passport':
                summary['key_fields'] = {
                    'name': fields.get('holder_name'),
                    'passport_number': fields.get('passport_number'),
                    'expiry': fields.get('expiry_date')
                }
            elif document_type == 'proof_of_address':
                summary['key_fields'] = {
                    'name': fields.get('holder_name'),
                    'address': fields.get('address'),
                    'document_date': fields.get('document_date')
                }
            else:
                summary['key_fields'] = fields
        
        return summary
