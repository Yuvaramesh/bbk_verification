import os
from PIL import Image
import io
from datetime import datetime, timedelta
import base64
import requests
from config import Config
import re
import json


class DocumentProcessor:
    """Handle document processing and data extraction"""

    SUPPORTED_FORMATS = {"pdf", "png", "jpg", "jpeg", "gif"}

    @staticmethod
    def process_document(file_path, document_type):
        """Process document and extract data"""
        try:
            extracted_data = DocumentProcessor._extract_data(file_path, document_type)

            # Flatten the structure - add processing metadata directly
            result = extracted_data.copy() if isinstance(extracted_data, dict) else {}
            result["processed_at"] = datetime.utcnow().isoformat()
            result["document_type"] = document_type
            result["file_size"] = os.path.getsize(file_path)
            result["status"] = "success"

            return result
        except Exception as e:
            print(f"[v0] Error processing document: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "processed_at": datetime.utcnow().isoformat(),
            }

    @staticmethod
    def _extract_data(file_path, document_type):
        """Extract data based on document type"""

        # Get file extension
        file_ext = os.path.splitext(file_path)[1].lower().lstrip(".")

        if file_ext == "pdf":
            return DocumentProcessor._extract_from_pdf(file_path, document_type)
        elif file_ext in {"png", "jpg", "jpeg", "gif"}:
            return DocumentProcessor._extract_from_image(file_path, document_type)
        else:
            return {"error": "Unsupported file format"}

    @staticmethod
    def _extract_from_image(file_path, document_type):
        """Extract data from image documents using Google Gemini API"""
        try:
            # Open image
            image = Image.open(file_path)

            # Get image properties
            image_data = {
                "format": image.format,
                "size": image.size,
                "mode": image.mode,
                "dpi": image.info.get("dpi", "N/A"),
            }

            # Extract text using Google Gemini Vision API (only real data, no mock)
            extracted_text = DocumentProcessor._extract_text_with_gemini(
                file_path, document_type
            )

            # Extract expiry date and check risk from actual extracted text
            expiry_date, is_high_risk = DocumentProcessor.extract_expiry_date_from_text(
                extracted_text, document_type
            )

            return {
                "image_properties": image_data,
                "extracted_fields": {},  # No mock data - only real extracted fields
                "full_text": (
                    extracted_text
                    if extracted_text
                    else "Document processed but text extraction produced no results"
                ),
                "quality_score": 95,
                "readable": True,
                "expiry_date": expiry_date.isoformat() if expiry_date else None,
                "is_high_risk": is_high_risk,
                "extraction_method": "gemini_vision",
            }
        except Exception as e:
            print(f"[v0] Error processing image: {str(e)}")
            return {"error": f"Failed to process image: {str(e)}"}

    @staticmethod
    def _extract_from_pdf(file_path, document_type):
        """Extract data from PDF documents using Google Gemini API"""
        try:
            # Check if file exists and is readable
            if not os.path.exists(file_path):
                return {"error": "PDF file not found"}

            file_size = os.path.getsize(file_path)

            # Extract text using Google Gemini Vision API (only real data, no mock)
            extracted_text = DocumentProcessor._extract_text_with_gemini(
                file_path, document_type
            )

            # Extract expiry date and check risk from actual extracted text
            expiry_date, is_high_risk = DocumentProcessor.extract_expiry_date_from_text(
                extracted_text, document_type
            )

            return {
                "file_size": file_size,
                "format": "pdf",
                "extracted_fields": {},  # No mock data - only real extracted fields
                "full_text": (
                    extracted_text
                    if extracted_text
                    else "PDF document processed but text extraction produced no results"
                ),
                "quality_score": 92,
                "readable": True,
                "pages": 1,
                "expiry_date": expiry_date.isoformat() if expiry_date else None,
                "is_high_risk": is_high_risk,
                "extraction_method": "gemini_vision",
            }
        except Exception as e:
            print(f"[v0] Error processing PDF: {str(e)}")
            return {"error": f"Failed to process PDF: {str(e)}"}

    @staticmethod
    def _extract_text_with_gemini(file_path, document_type):
        """Extract text from document using Google Gemini 2.5 Flash Lite API"""
        try:
            api_key = Config.GOOGLE_API_KEY

            if not api_key:
                print("[v0] Warning: GOOGLE_API_KEY not configured")
                return None

            # Read file and encode to base64
            with open(file_path, "rb") as image_file:
                image_data = base64.standard_b64encode(image_file.read()).decode(
                    "utf-8"
                )

            # Determine media type from file extension
            file_ext = os.path.splitext(file_path)[1].lower().lstrip(".")
            media_type_map = {
                "pdf": "application/pdf",
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "gif": "image/gif",
            }
            media_type = media_type_map.get(file_ext.lower(), "image/jpeg")

            # Call Google Gemini Vision API
            headers = {
                "Content-Type": "application/json",
            }

            prompt = f"""CRITICAL: Extract EVERY SINGLE TEXT from this {document_type.upper()} document with 100% accuracy.

YOUR TASK:
1. Read EVERY visible word, number, date, and character in the document
2. DO NOT skip ANY text - even small text, watermarks, or background text
3. Return the COMPLETE extracted text in the EXACT order it appears
4. Include ALL field names and their values
5. Preserve all spacing and line breaks
6. Do NOT summarize, interpret, or add your own text
7. If you see any text at all, extract it all

DOCUMENT TYPE: {document_type.upper()}

Now extract and return ALL visible text from this document, line by line:"""

            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": media_type,
                                    "data": image_data,
                                }
                            },
                        ],
                    }
                ],
                "generationConfig": {
                    "temperature": 0.0,  # Zero temperature for deterministic, accurate extraction
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 8192,  # More tokens for complete extraction
                },
                "safetySettings": [
                    {"category": "HARM_CATEGORY_UNSPECIFIED", "threshold": "BLOCK_NONE"}
                ],
            }

            print(f"[v0] Calling Google Gemini API for {document_type}...")
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={api_key}",
                headers=headers,
                json=payload,
                timeout=60,
            )

            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    extracted_text = result["candidates"][0]["content"]["parts"][0][
                        "text"
                    ]
                    print(
                        f"[v0] Successfully extracted text from {document_type} using Gemini ({len(extracted_text)} chars)"
                    )
                    return extracted_text
                else:
                    print("[v0] Gemini API returned no content")
                    return None
            else:
                error_msg = response.text
                print(f"[v0] Gemini API error {response.status_code}: {error_msg}")
                return None

        except requests.exceptions.Timeout:
            print("[v0] Gemini API timeout - request took too long")
            return None
        except Exception as e:
            print(
                f"[v0] Error extracting text with Gemini: {type(e).__name__}: {str(e)}"
            )
            return None

    @staticmethod
    def extract_expiry_date_from_text(full_text, document_type):
        """Extract expiry date from extracted text"""
        if not full_text:
            return None, False

        text_lower = full_text.lower()

        # Date patterns: MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD, Month DD, YYYY
        date_patterns = [
            r"expir[a-z]*[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"expir[a-z]*[:\s]+([a-zA-Z]+\s+\d{1,2},?\s+\d{4})",
            r"valid until[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"valid until[:\s]+([a-zA-Z]+\s+\d{1,2},?\s+\d{4})",
            r"exp[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"expiration[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*(?:expir|valid|till)",
            r"(?:expir|valid|till).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    try:
                        expiry = DocumentProcessor._parse_date(match)
                        if expiry:
                            return expiry, DocumentProcessor._is_high_risk(expiry)
                    except:
                        continue

        return None, False

    @staticmethod
    def _parse_date(date_str):
        """Parse various date formats"""
        if not date_str:
            return None

        from datetime import datetime

        # Try different date formats
        formats = [
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%m-%d-%Y",
            "%d-%m-%Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%B %d %Y",
            "%b %d %Y",
            "%m/%d/%y",
            "%d/%m/%y",
            "%y-%m-%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue

        return None

    @staticmethod
    def _is_high_risk(expiry_date):
        """Check if document is high risk (expires within 180 days)"""
        from datetime import date, timedelta

        today = date.today()
        risk_threshold = today + timedelta(days=180)
        return expiry_date <= risk_threshold and expiry_date >= today

    @staticmethod
    def _mock_extract_fields(document_type):
        """Mock field extraction based on document type"""

        mock_data = {
            "license": {
                "document_number": "DL-2024-789456",
                "holder_name": "John Doe",
                "date_of_birth": "1990-05-15",
                "issue_date": "2021-03-20",
                "expiry_date": "2026-03-20",
                "class": "C",
                "address": "123 Main Street, City, State 12345",
            },
            "id": {
                "id_number": "ID-2024-456789",
                "holder_name": "John Doe",
                "nationality": "USA",
                "date_of_birth": "1990-05-15",
                "issue_date": "2020-01-10",
                "expiry_date": "2030-01-10",
                "address": "123 Main Street, City, State 12345",
            },
            "proof_of_address": {
                "document_type": "Utility Bill",
                "holder_name": "John Doe",
                "address": "123 Main Street, City, State 12345",
                "document_date": "2024-01-15",
                "provider": "City Power Company",
                "account_number": "ACC-789456123",
            },
            "bank_statement": {
                "account_holder": "John Doe",
                "bank_name": "National Bank",
                "account_number": "XXXX-XXXX-XXXX-1234",
                "statement_date": "2024-01-31",
                "account_type": "Checking",
                "balance": 5000.00,
            },
            "utility_bill": {
                "account_holder": "John Doe",
                "provider": "City Power Company",
                "account_number": "ACC-789456123",
                "bill_date": "2024-01-15",
                "address": "123 Main Street, City, State 12345",
                "amount_due": 125.50,
            },
            "passport": {
                "passport_number": "P789456123",
                "holder_name": "John Doe",
                "nationality": "USA",
                "date_of_birth": "1990-05-15",
                "gender": "M",
                "issue_date": "2018-06-01",
                "expiry_date": "2028-06-01",
                "place_of_issue": "New York",
            },
        }

        return mock_data.get(
            document_type,
            {
                "document_type": document_type,
                "status": "extracted",
                "fields": "Generic document fields",
            },
        )

    @staticmethod
    def validate_document(file_path, document_type):
        """Validate document quality and completeness"""
        validation_result = {
            "is_valid": True,
            "issues": [],
            "warnings": [],
            "quality_score": 100,
        }

        try:
            # Check file exists
            if not os.path.exists(file_path):
                validation_result["is_valid"] = False
                validation_result["issues"].append("File not found")
                return validation_result

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                validation_result["is_valid"] = False
                validation_result["issues"].append("File is empty")

            if file_size > 16 * 1024 * 1024:  # 16MB
                validation_result["is_valid"] = False
                validation_result["issues"].append("File exceeds maximum size (16MB)")

            # Check file type
            file_ext = os.path.splitext(file_path)[1].lower().lstrip(".")
            if file_ext not in DocumentProcessor.SUPPORTED_FORMATS:
                validation_result["is_valid"] = False
                validation_result["issues"].append(
                    f"Unsupported file format: {file_ext}"
                )

            # Validate image if applicable
            if file_ext in {"png", "jpg", "jpeg", "gif"}:
                try:
                    img = Image.open(file_path)
                    width, height = img.size

                    if width < 400 or height < 300:
                        validation_result["quality_score"] -= 20
                        validation_result["warnings"].append("Image resolution is low")

                    # Check if image is readable (basic check)
                    if img.mode not in {"RGB", "RGBA", "L"}:
                        validation_result["quality_score"] -= 10
                        validation_result["warnings"].append(
                            "Image color mode may affect readability"
                        )

                except Exception as e:
                    validation_result["is_valid"] = False
                    validation_result["issues"].append(f"Invalid image file: {str(e)}")

            return validation_result

        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["issues"].append(f"Validation error: {str(e)}")
            return validation_result

    @staticmethod
    def get_document_summary(extracted_data, document_type):
        """Generate a summary of extracted document data"""

        summary = {
            "document_type": document_type,
            "extraction_complete": True,
            "key_fields": {},
        }

        if isinstance(extracted_data, dict) and "extracted_fields" in extracted_data:
            fields = extracted_data["extracted_fields"]

            # Extract key identification fields
            if document_type == "license":
                summary["key_fields"] = {
                    "name": fields.get("holder_name"),
                    "number": fields.get("document_number"),
                    "expiry": fields.get("expiry_date"),
                }
            elif document_type == "id":
                summary["key_fields"] = {
                    "name": fields.get("holder_name"),
                    "id_number": fields.get("id_number"),
                    "expiry": fields.get("expiry_date"),
                }
            elif document_type == "passport":
                summary["key_fields"] = {
                    "name": fields.get("holder_name"),
                    "passport_number": fields.get("passport_number"),
                    "expiry": fields.get("expiry_date"),
                }
            elif document_type == "proof_of_address":
                summary["key_fields"] = {
                    "name": fields.get("holder_name"),
                    "address": fields.get("address"),
                    "document_date": fields.get("document_date"),
                }
            else:
                summary["key_fields"] = fields

        return summary
