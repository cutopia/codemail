# Email Whitelist Configuration

## Overview

Codemail includes an email whitelist system to enhance security by controlling which email addresses can:
1. Submit tasks (sender whitelist)
2. Receive task completion reports (recipient whitelist)

This prevents unauthorized users from submitting malicious instructions and protects against spoofed emails.

## Configuration

### Environment Variables

Add these variables to your `.env` file:

```bash
# Email Whitelist Configuration
EMAIL_WHITELIST_SENDERS="user1@example.com,user2@example.org"
EMAIL_WHITELIST_RECIPIENTS="user1@example.com,user2@example.org"
```

### Format

- **Multiple addresses**: Separate with commas (`,`)
- **Case insensitive**: `User@Example.COM` and `user@example.com` are treated the same
- **Whitespace handling**: Leading/trailing spaces are automatically trimmed

## Examples

### Single Email Address

```bash
EMAIL_WHITELIST_SENDERS="admin@example.com"
EMAIL_WHITELIST_RECIPIENTS="admin@example.com"
```

### Multiple Email Addresses

```bash
EMAIL_WHITELIST_SENDERS="user1@example.com,user2@example.org,team@company.net"
EMAIL_WHITELIST_RECIPIENTS="user1@example.com,user2@example.org,team@company.net"
```

### Domain-based Whitelisting

You can whitelist entire domains by using `@domain.com` format:

```bash
# Allow all emails from example.com
EMAIL_WHITELIST_SENDERS="@example.com"

# Allow multiple domains
EMAIL_WHITELIST_SENDERS="@example.com,@company.org"
```

## How It Works

### Sender Whitelist (Incoming Emails)

1. When an email arrives, Codemail extracts the sender's email address
2. The system checks if the sender is in the whitelist
3. If whitelisted: Email is processed normally
4. If not whitelisted: Email is skipped with a warning log message

### Recipient Whitelist (Outgoing Reports)

1. When a task completes, Codemail prepares a report
2. The system checks if the intended recipient is in the whitelist
3. If whitelisted: Report is sent via SMTP
4. If not whitelisted: Report is blocked and an error is logged

## Backward Compatibility

If no whitelist is configured (variables are empty or not set), Codemail will:
- Accept emails from any sender
- Send reports to any recipient

This maintains compatibility with existing installations.

## Security Benefits

1. **Prevents unauthorized task submission**: Only whitelisted senders can trigger code execution
2. **Protects against spoofing**: Reports only go to trusted recipients
3. **Domain-level control**: Whitelist entire domains for easier management
4. **Audit trail**: All non-whitelisted attempts are logged

## Troubleshooting

### Email Not Being Processed

1. Check the logs for "not in the email whitelist" messages
2. Verify the sender's email address is correctly formatted in `EMAIL_WHITELIST_SENDERS`
3. Ensure there are no typos or extra spaces in the configuration

### Report Not Being Sent

1. Check logs for "not in the email whitelist" warnings
2. Verify the recipient email matches exactly (case-insensitive)
3. Confirm `EMAIL_WHITELIST_RECIPIENTS` includes the target address

## Best Practices

1. **Use specific addresses**: Prefer individual emails over domain wildcards when possible
2. **Regular review**: Periodically audit your whitelist entries
3. **Separate senders and recipients**: You may want different lists for incoming vs outgoing
4. **Test configuration**: Send a test email before relying on the system

## Example .env File

```bash
# Email Server Configuration
IMAP_HOST=imap.gmail.com
SMTP_HOST=smtp.gmail.com
EMAIL_ADDRESS=codemail@yourdomain.com
EMAIL_PASSWORD=your_app_password

# Codemail Settings
CODEMAIL_PREFIX=codemail:

# Security - Whitelist Configuration
EMAIL_WHITELIST_SENDERS="admin@yourdomain.com,dev@yourdomain.com"
EMAIL_WHITELIST_RECIPIENTS="admin@yourdomain.com,devops@yourdomain.com"
```
