"""
Email reporter module for Codemail system.
Sends completion reports via SMTP.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from config import email_config

logger = logging.getLogger("codemail.email_reporter")


class EmailReporter:
    """SMTP email reporter for sending task completion reports."""
    
    def __init__(self):
        self.smtp_host = email_config.smtp_host
        self.smtp_port = email_config.smtp_port
        self.email_address = email_config.email_address
        self.email_password = email_config.email_password
        
    def send_report(self, recipient: str, subject: str, body: str) -> bool:
        """
        Send an email report.
        
        Args:
            recipient: Email address of the recipient
            subject: Email subject line
            body: HTML or plain text body content
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message container
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_address
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # Add body as HTML and plain text
            html_body = f"""
            <html>
              <body>
                <h2>{subject}</h2>
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <pre style="white-space: pre-wrap; font-family: monospace;">{body}</pre>
              </body>
            </html>
            """
            
            plain_body = body
            
            # Attach parts
            msg.attach(MIMEText(plain_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # Connect to SMTP server and send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # Secure the connection
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
                
            logger.info(f"Report sent successfully to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email report: {e}")
            return False
    
    def send_task_report(self, recipient: str, task_id: str, task_data: dict) -> bool:
        """
        Send a formatted task completion report.
        
        Args:
            recipient: Email address of the recipient
            task_id: Unique identifier for the task
            task_data: Dictionary containing task results
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Extract task information
            status = task_data.get("status", "unknown")
            output = task_data.get("output", "")
            error = task_data.get("error", "")
            iterations = task_data.get("iterations", 0)
            step_summaries = task_data.get("step_summaries", [])
            
            # Format report content
            report_lines = [
                f"Task ID: {task_id}",
                f"Status: {status.upper()}",
                f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "## Summary"
            ]
            
            if status == "completed":
                report_lines.extend([
                    "",
                    "Task completed successfully!",
                    "",
                    "## Steps Taken:"
                ])
                
                # Add step summaries if available
                if step_summaries:
                    for i, summary in enumerate(step_summaries, 1):
                        step_num = summary.get("step", i)
                        description = summary.get("description", f"Step {step_num}")
                        summary_text = summary.get("summary", "")
                        
                        report_lines.append(f"\n### Step {step_num}: {description}")
                        report_lines.append(summary_text)
                else:
                    # Fallback if no step summaries
                    report_lines.append("\nNo detailed step information available.")
                
                report_lines.extend([
                    "",
                    "## Results:",
                    output
                ])
                
                if iterations > 0:
                    report_lines.append(f"\nIterations: {iterations}")
                    
            elif status == "failed":
                report_lines.extend([
                    "",
                    "Task failed to complete.",
                    "",
                    "## Error:",
                    error or "Unknown error occurred"
                ])
            else:
                report_lines.extend([
                    "",
                    f"Task ended with unknown status: {status}"
                ])
            
            # Create subject line based on status
            status_emoji = "✅" if status == "completed" else "❌"
            subject = f"[Codemail] {status_emoji} Task {task_id[:8]} - {status.upper()}"
            
            body = "\n".join(report_lines)
            
            return self.send_report(recipient, subject, body)
            
        except Exception as e:
            logger.error(f"Error formatting task report: {e}")
            return False
    
    def send_error_report(self, recipient: str, error_message: str) -> bool:
        """
        Send an error notification email.
        
        Args:
            recipient: Email address of the recipient
            error_message: Description of the error
            
        Returns:
            True if email sent successfully, False otherwise
        """
        subject = f"[Codemail] ⚠️ Error Notification - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        body = f"An error occurred in the Codemail system:\n\n{error_message}"
        
        return self.send_report(recipient, subject, body)


def create_email_reporter():
    """Factory function to create email reporter with validation."""
    try:
        email_config.validate()
        return EmailReporter()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
