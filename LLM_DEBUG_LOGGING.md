# LLM Debug Logging

This feature adds comprehensive logging of all inputs and outputs to/from the LLM for debugging purposes.

## Configuration

Add the following setting to your `.env` file:

```bash
LLM_DEBUG_LOGGING=false
```

Set to `true` to enable debug logging, or `false` (default) to disable it.

## What Gets Logged

When `LLM_DEBUG_LOGGING=true`, the following information is logged to the console with clear formatting:

1. **Task Instructions**: The full instructions sent to the LLM
2. **Messages Sent**: All messages (system prompt + user prompt) with their roles and content
3. **Request JSON**: The complete JSON payload sent to the LLM API
4. **Response JSON**: The complete JSON response from the LLM API
5. **Extracted Content**: The extracted content from the LLM response
6. **Final Response**: The final response after all processing

## Example Output Format

```
================================================================================
LLM MESSAGES SENT
================================================================================
Role: system
Content:
You are an expert coding assistant...

Role: user
Content:
INSTRUCTIONS:
Create a new file...

================================================================================

================================================================================
LLM REQUEST JSON
================================================================================
{
  "messages": [...],
  "max_tokens": 262144,
  "temperature": 0.7
}

================================================================================

================================================================================
LLM RESPONSE JSON
================================================================================
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "..."
      }
    }
  ]
}

================================================================================

================================================================================
LLM EXTRACTED CONTENT
================================================================================
Here is the response from the LLM...

================================================================================
```

## Usage

1. Edit your `.env` file and set `LLM_DEBUG_LOGGING=true`
2. Restart your application or reload the configuration
3. Send a test email with instructions
4. Check the console output for detailed logs

## Performance Note

Debug logging adds overhead due to:
- JSON serialization of messages
- Console I/O operations
- String formatting

For production use, keep this disabled (`false`) to maintain optimal performance.
