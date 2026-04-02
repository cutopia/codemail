# Subject Validation in Codemail

## Overview

Codemail uses strict subject line validation to ensure that only emails intended for the codemail system are processed. This prevents accidental processing of regular emails and improves security.

## How It Works

### Subject Pattern

All valid codemail requests must follow this exact pattern:

```
codemail:[project-name] instructions
```

Where:
- `codemail:` - Required prefix (case-insensitive)
- `[project-name]` - Project name in square brackets
- `instructions` - Brief task description

### Validation Flow

1. **Email arrives** → IMAP monitor detects new email
2. **Subject check** → Validates against pattern
3. **Pattern match?**
   - ✅ Yes → Parse project name and instructions, create task
   - ❌ No → Ignore email, log warning

## Examples

### Valid Subject Lines (Will Be Processed)

| Subject | Project Name | Instructions |
|---------|--------------|--------------|
| `codemail:[my-project] Fix login bug` | my-project | Fix login bug |
| `CODEMAIL:[api-service] Add rate limiting` | api-service | Add rate limiting |
| `Codemail: [frontend-app] Update navigation` | frontend-app | Update navigation |
| `CoDeMaIl: [data-pipeline] Optimize ETL` | data-pipeline | Optimize ETL |

### Invalid Subject Lines (Will Be Ignored)

| Subject | Reason |
|---------|--------|
| `[my-project] Fix bug` | Missing required prefix |
| `codemail my-project Fix bug` | No brackets around project name |
| `codemail: Fix bug` | Missing project name in brackets |
| `RE: codemail:[project] Previous` | Pattern doesn't start subject |
| `Hello world` | No pattern at all |

## Configuration

### Custom Prefix

You can customize the prefix by setting the `CODEMAIL_PREFIX` environment variable:

```bash
export CODEMAIL_PREFIX="task:"
```

With this configuration:
- ✅ Valid: `task:[project-name] instructions`
- ❌ Invalid: `codemail:[project-name] instructions`

### Default Configuration

If no prefix is specified, the system uses:
```
CODEMAIL_PREFIX=codemail:
```

## Implementation Details

### SubjectValidator Class

The `SubjectValidator` class handles pattern matching:

```python
from subject_validator import create_subject_validator

validator = create_subject_validator()

# Check if email is a codemail request
if validator.is_codemail_request(subject):
    # Process the email
    result = validator.parse_codemail_subject(subject)
    project_name = result["project_name"]
    instructions = result["instructions"]
```

### Email Parser Integration

The `EmailParser` automatically validates subjects:

```python
from email_parser import create_email_parser

parser = create_email_parser()

# This will return None for invalid subjects
parsed_data = parser.parse_email(email_data)

if parsed_data is not None:
    # Valid codemail request
    project_name = parsed_data["project_name"]
else:
    # Invalid subject - email ignored
```

## Security Benefits

1. **Prevents Accidental Processing** - Regular emails won't trigger tasks
2. **Explicit Intent** - Users must use the correct pattern to trigger actions
3. **Reduced Attack Surface** - Only properly formatted requests are processed
4. **Clear Documentation** - Users know exactly what format to use

## Testing

Run the subject validation tests:

```bash
# Run all system tests (includes subject validation)
python test_system.py
```

## Migration Guide

### For Existing Users

If you have existing emails that don't follow the new pattern:

1. **Update your email templates** to use the new format
2. **Test with a sample email** before sending to production
3. **Check logs** for any ignored emails during transition

### Email Template Examples

#### Before (Old Format)
```
Subject: [my-project] Fix login bug
Body: Project: my-project\nPlease fix the login button.
```

#### After (New Format)
```
Subject: codemail:[my-project] Fix login bug
Body: Please fix the login button styling on the homepage.
```

## Troubleshooting

### Email Ignored But Should Be Processed

1. Check subject line format matches `codemail:[project-name] instructions`
2. Verify prefix is correct (default: `codemail:`)
3. Check logs for validation errors
4. Test with `python test_system.py`

### Custom Prefix Not Working

1. Set environment variable: `export CODEMAIL_PREFIX=your-prefix:`
2. Restart the codemail system
3. Use the new prefix in subject lines

## Best Practices

1. **Always use lowercase** for project names (automatically converted)
2. **Keep instructions concise** in subject line
3. **Add detailed context** in email body
4. **Test before sending** using the test scripts
5. **Document your format** for team members

## Future Enhancements

Potential improvements to consider:

- [ ] Multiple valid prefixes (e.g., both `codemail:` and `task:`)
- [ ] Regex-based pattern configuration
- [ ] Subject line length limits
- [ ] Project name validation (alphanumeric only, etc.)
