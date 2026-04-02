"""
Email parsing module for Codemail system.
Extracts project name and instructions from email content.
"""

import re
import logging

logger = logging.getLogger("codemail.email_parser")


class EmailParser:
    """Parser for extracting task information from emails."""
    
    def __init__(self):
        # Default project name if not specified in email
        self.default_project = "default"
        
    def parse_email(self, email_data):
        """
        Parse email content to extract project name and instructions.
        
        Args:
            email_data: Dictionary with 'subject', 'body', 'from' keys
            
        Returns:
            Dictionary with 'project_name', 'instructions', 'raw_body'
        """
        try:
            subject = email_data.get("subject", "")
            body = email_data.get("body", "")
            
            # Extract project name from subject or body
            project_name = self._extract_project_name(subject, body)
            
            # Extract instructions (main content after any headers/commands)
            instructions = self._extract_instructions(body)
            
            return {
                "project_name": project_name,
                "instructions": instructions,
                "raw_body": body,
                "sender": email_data.get("from", "")
            }
            
        except Exception as e:
            logger.error(f"Error parsing email: {e}")
            return None
    
    def _extract_project_name(self, subject, body):
        """Extract project name from subject or body."""
        # Try to extract from subject first (format: "[project-name] instructions")
        subject_match = re.search(r'\[([^\]]+)\]', subject)
        if subject_match:
            return subject_match.group(1).strip().lower()
        
        # Try to extract from body (format: "Project: project-name" or "# Project: project-name")
        body_match = re.search(r'^(?:#)?\s*Project\s*[:\s]+(\S+)', body, re.MULTILINE | re.IGNORECASE)
        if body_match:
            return body_match.group(1).strip().lower()
        
        # Default to "default" if no project name found
        logger.info("No project name found in email, using 'default'")
        return self.default_project
    
    def _extract_instructions(self, body):
        """Extract instructions from email body."""
        lines = body.split('\n')
        instructions_lines = []
        
        skip_patterns = [
            r'^Project\s*[:\s]*',  # Project: project-name
            r'^#\s*Project\s*[:\s]*',  # # Project: project-name
            r'^From\s*[:\s]*',  # From: sender
            r'^Subject\s*[:\s]*',  # Subject: subject
            r'^To\s*[:\s]*',  # To: recipient
            r'^Date\s*[:\s]*',  # Date: timestamp
        ]
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and common email headers
            if not line:
                continue
            
            skip = False
            for pattern in skip_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    skip = True
                    break
            
            if not skip:
                instructions_lines.append(line)
        
        # Join remaining lines as instructions
        instructions = '\n'.join(instructions_lines).strip()
        
        # If no instructions found, use the entire body
        if not instructions:
            logger.warning("No clear instructions found in email body")
            return body.strip()
        
        return instructions
    
    def validate_task(self, parsed_data):
        """
        Validate that parsed task data is complete and valid.
        
        Args:
            parsed_data: Dictionary from parse_email
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not parsed_data:
            return False, "Parsed data is None"
        
        if not parsed_data.get("instructions"):
            return False, "No instructions found in email"
        
        if len(parsed_data["instructions"]) < 5:
            return False, "Instructions too short (minimum 5 characters)"
        
        return True, None


def create_email_parser():
    """Factory function to create email parser."""
    return EmailParser()
