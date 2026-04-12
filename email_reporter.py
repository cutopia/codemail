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
        
        # Import whitelist here to avoid circular imports
        from whitelist import get_email_whitelist
        self.whitelist = get_email_whitelist()
        
    def _is_recipient_whitelisted(self, recipient: str) -> bool:
        """
        Check if the recipient email is whitelisted.
        
        Args:
            recipient: Email address to check
            
        Returns:
            True if whitelisted or whitelist not configured, False otherwise
        """
        # If no whitelist is configured, allow all (backward compatibility)
        if self.whitelist is None:
            logger.debug("No whitelist configured - allowing all recipients")
            return True
        
        logger.debug(f"Checking if recipient '{recipient}' is whitelisted...")
        
        # Check if recipient is whitelisted
        is_whitelisted = self.whitelist.is_recipient_whitelisted(recipient)
        
        if not is_whitelisted:
            logger.warning(f"Recipient '{recipient}' is not in the email whitelist - report will be blocked")
        else:
            logger.debug(f"Recipient '{recipient}' is whitelisted")
        
        return is_whitelisted
    
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
        # Check if recipient is whitelisted before attempting to send
        if not self._is_recipient_whitelisted(recipient):
            logger.error(f"Cannot send report to non-whitelisted recipient: {recipient}")
            return False
        
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
            logger.debug(f"Email details: subject={msg['Subject']}, from={msg['From']}, to={msg['To']}")
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
        logger.info(f"Preparing to send task report to {recipient} (task_id: {task_id})")
        
        # Check whitelist before formatting and sending
        if not self._is_recipient_whitelisted(recipient):
            logger.error(f"Cannot send task report to non-whitelisted recipient: {recipient}")
            return False
        
        logger.debug(f"Recipient {recipient} is whitelisted, proceeding with report")
        
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
                
                # Include bash command results if available in task_data
                bash_results = task_data.get("bash_results", [])
                if bash_results:
                    report_lines.append("\n## Bash Command Results:")
                    for j, result in enumerate(bash_results, 1):
                        cmd = result.get("command", "")
                        res = result.get("result", {})
                        stdout = res.get("stdout", "").strip()
                        stderr = res.get("stderr", "").strip()
                        returncode = res.get("returncode", -1)
                        
                        report_lines.append(f"\n### Command {j}: `{cmd}`")
                        if returncode == 0:
                            report_lines.append("**Output:**")
                            # Show full output (not truncated like in step summaries)
                            if stdout:
                                report_lines.append(f"```\n{stdout}\n```")
                            else:
                                report_lines.append("(no output)")
                        else:
                            report_lines.append("**Error:**")
                            if stderr:
                                report_lines.append(f"```\n{stderr}\n```")
                            else:
                                report_lines.append("(no error message)")
                
                report_lines.extend([
                    "",
                    "## Results:",
                    output
                ])
                
                # Add file verification information if available
                step_summaries = task_data.get("step_summaries", [])
                if step_summaries:
                    last_summary = step_summaries[-1] if step_summaries else None
                    summary_text = last_summary.get("summary", "") if last_summary else ""
                    
                    # Check if any files were mentioned in the final summary
                    import re
                    file_mentions = re.findall(r'`?([A-Za-z_]+\.(?:md|txt|py|json))`?', summary_text)
                    if file_mentions:
                        report_lines.append("\n## Files Created/Modified:")
                        for filename in set(file_mentions):
                            report_lines.append(f"- {filename}")
                
                if iterations > 0:
                    report_lines.append(f"\nIterations: {iterations}")
                    
            elif status == "failed":
                report_lines.extend([
                    "",
                    "Task failed to complete.",
                    "",
                    "## Error:",
                    error or "Unknown error occurred",
                    "",
                    "## Diagnostic Information:"
                ])
                
                # Add diagnostic information if available
                if output:
                    # Check if output contains detailed error information (from our enhanced reporting)
                    if "File Verification Details:" in output or "Bash Command" in output:
                        report_lines.append("\n### Execution Details:")
                        # Extract and format the key diagnostic sections
                        import re
                        
                        # Try to extract file verification details
                        file_verification_match = re.search(r'## File Verification Details:(.*?)(?=##|$)', output, re.DOTALL)
                        if file_verification_match:
                            report_lines.append("\n**File Status:**")
                            report_lines.append(file_verification_match.group(1).strip())
                        
                        # Try to extract bash command results
                        bash_results_match = re.search(r'## All Bash Commands Executed:(.*?)(?=##|$)', output, re.DOTALL)
                        if bash_results_match:
                            report_lines.append("\n**Bash Command Results:**")
                            report_lines.append(bash_results_match.group(1).strip())
                        
                        # Try to extract LLM response
                        llm_response_match = re.search(r'## Full LLM Response:(.*?)(?=##|$)', output, re.DOTALL)
                        if llm_response_match:
                            report_lines.append("\n**LLM Response Preview:**")
                            report_lines.append(llm_response_match.group(1).strip())
                    else:
                        # Fallback: show output as-is
                        report_lines.append(f"\n**Output:**\n```\n{output[:500]}\n```")  # Truncate long output
                else:
                    report_lines.append("No additional diagnostic information available.")
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
        # Check whitelist before sending error report
        if not self._is_recipient_whitelisted(recipient):
            logger.error(f"Cannot send error report to non-whitelisted recipient: {recipient}")
            return False
        
        subject = f"[Codemail] ⚠️ Error Notification - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        body = f"An error occurred in the Codemail system:\n\n{error_message}"
        
        return self.send_report(recipient, subject, body)


def create_email_reporter():
    """Factory function to create email reporter with validation."""
    try:
        email_config.validate()
        
        # Validate whitelist configuration if set
        is_valid, error_msg = email_config.validate_whitelist()
        if not is_valid:
            logger.warning(f"Whitelist configuration warning: {error_msg}")
        
        return EmailReporter()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
