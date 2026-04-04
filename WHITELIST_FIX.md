# Email Whitelist Extraction Fix

## Problem

The whitelist was comparing an entire "From" line to the whitelist instead of just the email address. For example, `"Suzanne <cutopia@gmail.com>"` caused a rejection even though `cutopia@gmail.com` was on the whitelist.

## Root Cause

The email extraction logic used regex patterns that had several issues:

1. **Incorrect handling of plus addresses**: `user+tag@example.com` was incorrectly parsed as `tag@example.com`
2. **Fragile pattern matching**: The regex `[\w\.-]+@[\w\.-]+\.\w+` doesn't handle all RFC-compliant email formats
3. **No fallback for edge cases**: When the regex failed, it would return the entire "From" field

## Solution

Replaced the regex-based extraction with Python's built-in `email.utils.parseaddr()` function, which:

- Handles all RFC-compliant email address formats
- Correctly extracts email addresses from "Name <email>" format
- Properly handles edge cases like plus addresses, quoted names, etc.
- Is more reliable and maintainable

## Changes Made

### 1. `email_monitor.py`
- Added import: `from email.utils import parseaddr`
- Replaced `_extract_email_address()` method to use `parseaddr()`

### 2. `whitelist.py`
- Removed regex import
- Added import: `from email.utils import parseaddr`
- Updated `_extract_email_address()` method to use `parseaddr()`

### 3. `test_whitelist.py`
- Added test case for the specific issue: `"Suzanne <cutopia@gmail.com>"`
- Added test case for plus addresses
- All existing tests continue to pass

## Testing

All tests pass, including:
- Empty whitelist (allows all)
- Single email whitelist
- Multiple emails whitelist
- Case insensitivity
- Domain wildcard matching
- Email extraction from various formats
- Whitespace handling
- Plus-address handling (new)

## Example

Before fix:
```
From: "Suzanne <cutopia@gmail.com>"
Extracted: "Suzanne <cutopia@gmail.com>"  ❌ (incorrect)
Result: Rejected by whitelist
```

After fix:
```
From: "Suzanne <cutopia@gmail.com>"
Extracted: "cutopia@gmail.com"  ✅ (correct)
Result: Whitelisted successfully
```

## Benefits

1. **More reliable**: Handles all RFC-compliant email formats
2. **Better edge case handling**: Plus addresses, quoted names, etc.
3. **Simpler code**: Uses standard library instead of custom regex
4. **Maintainable**: Less complex logic is easier to understand and modify
