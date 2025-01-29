import re
import secrets
import hashlib
import logging
from typing import Any, Dict, Union, List
import html
import unicodedata
import urllib.parse

class SecurityUtils:
    """
    Comprehensive security utility for input sanitization, validation, and protection.
    """
    
    _logger = logging.getLogger(__name__)
    
    @staticmethod
    def sanitize_input(input_data: Any) -> Any:
        """
        Advanced input sanitization to prevent injection and ensure safety.
        
        Args:
            input_data: Input to be sanitized
        
        Returns:
            Sanitized input
        """
        try:
            if isinstance(input_data, str):
                # HTML escape
                sanitized = html.escape(input_data)
                
                # URL decode to handle encoded attacks
                sanitized = urllib.parse.unquote(sanitized)
                
                # Remove control characters
                sanitized = re.sub(r'[\x00-\x1F\x7F]', '', sanitized)
                
                # Normalize unicode to prevent homograph attacks
                sanitized = unicodedata.normalize('NFKC', sanitized)
                
                # Remove potentially dangerous characters and scripts
                sanitized = re.sub(r'<script.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
                sanitized = re.sub(r'[<>&\'"()]', '', sanitized)
                
                # Limit input length
                return sanitized[:1000]
            
            if isinstance(input_data, dict):
                return {
                    SecurityUtils.sanitize_input(k): SecurityUtils.sanitize_input(v) 
                    for k, v in input_data.items()
                }
            
            if isinstance(input_data, list):
                return [SecurityUtils.sanitize_input(item) for item in input_data]
            
            return input_data
        except Exception as e:
            SecurityUtils._logger.error(f"Sanitization error: {e}")
            return input_data
    
    @staticmethod
    def generate_security_hash(data: Dict[str, Any], salt: str = None) -> str:
        """
        Generate a secure, salted hash for tracking and integrity verification.
        
        Args:
            data: Dictionary of data to hash
            salt: Optional salt for additional security
        
        Returns:
            Secure hash string
        """
        try:
            # Convert data to a consistent, sorted string representation
            data_str = str(sorted(data.items()))
            
            # Use a cryptographically secure salt
            salt = salt or secrets.token_hex(16)
            
            # Use SHA-256 with salt for hashing
            return hashlib.sha256(
                (data_str + salt).encode()
            ).hexdigest()
        except Exception as e:
            SecurityUtils._logger.error(f"Hash generation error: {e}")
            return ""
    
    @staticmethod
    def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Advanced masking of sensitive information in a dictionary.
        
        Args:
            data: Dictionary potentially containing sensitive data
        
        Returns:
            Dictionary with sensitive data masked
        """
        try:
            masked_data = data.copy()
            sensitive_patterns = [
                'api_key', 'password', 'token', 'secret', 
                'credentials', 'access_token', 'refresh_token'
            ]
            
            for key, value in list(masked_data.items()):
                # Check if key matches sensitive patterns
                if any(pattern in key.lower() for pattern in sensitive_patterns):
                    # Mask entire value
                    masked_data[key] = '*' * min(len(str(value)), 16)
                
                # Recursively mask nested dictionaries
                elif isinstance(value, dict):
                    masked_data[key] = SecurityUtils.mask_sensitive_data(value)
                
                # Mask list contents if they might contain sensitive data
                elif isinstance(value, list):
                    masked_data[key] = [
                        '*' * min(len(str(item)), 16) if len(str(item)) > 4 else item 
                        for item in value
                    ]
            
            return masked_data
        except Exception as e:
            SecurityUtils._logger.error(f"Sensitive data masking error: {e}")
            return data
    
    @staticmethod
    def validate_input(
        input_data: Union[str, Dict, List], 
        validators: Dict[str, callable] = None
    ) -> bool:
        """
        Validate input against a set of custom validation rules.
        
        Args:
            input_data: Input to validate
            validators: Dictionary of validation functions
        
        Returns:
            Boolean indicating if input passes all validations
        """
        try:
            # Default validators
            default_validators = {
                'length': lambda x: 0 < len(str(x)) <= 1000,
                'no_special_chars': lambda x: re.match(r'^[a-zA-Z0-9\s]+$', str(x)) is not None
            }
            
            validators = validators or {}
            all_validators = {**default_validators, **validators}
            
            # Apply validators based on input type
            if isinstance(input_data, str):
                return all(validator(input_data) for validator in all_validators.values())
            
            if isinstance(input_data, dict):
                return all(
                    all(validator(value) for validator in all_validators.values())
                    for value in input_data.values()
                )
            
            if isinstance(input_data, list):
                return all(
                    all(validator(item) for validator in all_validators.values())
                    for item in input_data
                )
            
            return True
        except Exception as e:
            SecurityUtils._logger.error(f"Input validation error: {e}")
            return False

# Convenience functions for easier import
sanitize_input = SecurityUtils.sanitize_input
generate_security_hash = SecurityUtils.generate_security_hash
mask_sensitive_data = SecurityUtils.mask_sensitive_data
validate_input = SecurityUtils.validate_input
