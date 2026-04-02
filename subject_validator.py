"""
Subject line validator for Codemail system.
Validates email subject lines to ensure they contain the proper codemail pattern.
"""

import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger("codemail.subject_validator")


class SubjectValidator:
    """Validates email subject lines for codemail requests."""
    
    def __init__(self, prefix: str = "codemail:"):
        # Default prefix for codemail subjects - can be overridden via config
        self.prefix = prefix
        
        # Pattern: [prefix][project-name] instructions
        # Example: "codemail:[my-project] Fix the login bug"
        self.subject_pattern = re.compile(
            r'^' + re.escape(self.prefix) + r'\s*\[([^\]]+)\]\s*(.+)$',
            re.IGNORECASE
        )
    
    def validate_subject(self, subject: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate email subject and extract project name.
        
        Args:
            subject: Email subject line
            
        Returns:
            Tuple of (is_valid, project_name, instructions)
            - is_valid: True if subject matches codemail pattern
            - project_name: Extracted project name if valid
            - instructions: Instructions part of subject if valid
        """
        try:
            # Try primary pattern with prefix (required for codemail requests)
            match = self.subject_pattern.match(subject.strip())
            if match:
                project_name = match.group(1).strip().lower()
                instructions = match.group(2).strip()
                
                logger.info(f"Valid codemail subject detected: project='{project_name}', instructions='{instructions[:50]}...'")
                
                return True, project_name, instructions
            
            # No match found - only accept subjects with the required prefix
            logger.debug(f"Subject does not match codemail pattern (missing '{self.prefix}' prefix): '{subject}'")
            return False, None, None
            
        except Exception as e:
            logger.error(f"Error validating subject line: {e}")
            return False, None, None
    
    def is_codemail_request(self, subject: str) -> bool:
        """
        Check if subject indicates a codemail request.
        
        Args:
            subject: Email subject line
            
        Returns:
            True if subject matches codemail pattern
        """
        is_valid, _, _ = self.validate_subject(subject)
        return is_valid
    
    def parse_codemail_subject(self, subject: str) -> Optional[dict]:
        """
        Parse a valid codemail subject into components.
        
        Args:
            subject: Email subject line
            
        Returns:
            Dictionary with 'project_name' and 'instructions', or None if invalid
        """
        is_valid, project_name, instructions = self.validate_subject(subject)
        
        if is_valid:
            return {
                "project_name": project_name,
                "instructions": instructions
            }
        
        return None


def create_subject_validator(prefix: str = "codemail:") -> SubjectValidator:
    """Factory function to create subject validator."""
    return SubjectValidator(prefix)
