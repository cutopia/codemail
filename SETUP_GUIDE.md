# Codemail Setup Guide

## Quick Start (5 minutes)

### Step 1: Install Dependencies

```bash
./setup.sh
```

This will:
- Create a virtual environment
- Install all Python dependencies
- Set up the project structure

### Step 2: Configure Your Credentials

Edit `.env` with your email and LLM settings:

```env
# Email Configuration (Gmail example)
IMAP_HOST=imap.gmail.com
SMTP_HOST=smtp.gmail.com
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# LLM Configuration (LM Studio)
LLM_ENDPOINT=http://127.0.0.1:1234/v1/models
LLM_API_KEY=dummy_key
```

### Step 3: Start the System

```bash
source venv/bin/activate
python main.py
```

## Detailed Configuration

### Email Setup

#### For Gmail:
1. Enable 2-Factor Authentication on your Google Account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
3. Use the app password in your `.env` file (not your regular password)

#### For Other Email Providers:
- Outlook/Hotmail: `outlook.office365.com`
- Yahoo Mail: `imap.mail.yahoo.com`
- Custom IMAP server: Use your provider's settings

### LLM Setup

#### LM Studio (Recommended for Local Development)
1. Download and install [LM Studio](https://lmstudio.ai/)
2. Load a model (e.g., Llama 3, Mistral)
3. Start the local server on port 1234
4. The endpoint will be: `http://127.0.0.1:1234/v1/models`

#### Using a Remote API
If you prefer to use a remote API (OpenAI, etc.):

```env
LLM_ENDPOINT=https://api.openai.com/v1/chat/completions
LLM_API_KEY=sk-your-api-key-here
```

## Testing Your Setup

After configuration, run the test suite:

```bash
source venv/bin/activate
python test_system.py
```

This will verify:
- Email parser functionality
- Subject validation
- Task queue operations
- LLM interface connectivity

## Troubleshooting

### Email Not Being Received

1. Verify IMAP settings in `.env`
2. Check that app password is correct (not regular password)
3. Ensure IMAP is enabled in your email account settings
4. Check logs for connection errors

### LLM Connection Issues

1. Verify LM Studio server is running on port 1234
2. Test endpoint: `curl http://127.0.0.1:1234/v1/models`
3. Check `LLM_ENDPOINT` in `.env` matches your setup
4. For remote APIs, verify API key is correct

### Tasks Not Executing

1. Check agent loop is running (look for "Starting agent loop" in logs)
2. Verify task queue has pending tasks
3. Check LLM connection and response times
4. Review error messages in logs

## Next Steps

After setup is complete:
1. Send a test email with the correct subject format
2. Monitor logs for task processing
3. Review the generated reports
4. Customize configuration as needed
