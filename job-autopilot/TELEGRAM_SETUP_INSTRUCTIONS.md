# Telegram Setup Instructions

## Problem Found
Your Telegram configuration has empty values for:
- `TELEGRAM_API_HASH` - Empty
- `TELEGRAM_READER_SESSION` - Empty

Without these credentials, the system cannot connect to Telegram to fetch vacancies from channels.

## Solution Steps

### Step 1: Get API ID and API Hash
1. Go to https://my.telegram.org/apps
2. Login with your phone number
3. Click "Create application" (or use existing)
4. Copy **API ID** (e.g., `123456`)
5. Copy **API Hash** (e.g., `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`)

### Step 2: Generate Session String
1. Edit the file `generate_session.py` in the project root
2. Replace `API_ID` and `API_HASH` with your real credentials
3. Run: `python3 generate_session.py`
4. Follow prompts to login with your phone number
5. Copy the generated session string

### Step 3: Configure in UI
1. Open Job Autopilot UI
2. Go to Settings page
3. Enter in Telegram Configuration section:
   - **API ID**: Your API ID from step 1
   - **API Hash**: Your API Hash from step 1
   - **Reader Session**: The session string from step 2
4. Click "Save Settings"

### Step 4: Test
1. Go to Dashboard
2. Click "Run Telegram Monitor"
3. Check logs and events for results

## Files Modified
- `/app/sources/telegram_channels.py` - Added full Telegram fetch implementation
- `/app/services/vacancy_service.py` - Fixed channel_id reference
- `generate_session.py` - Helper script created

## What Was Fixed
1. ✅ Implemented full Telegram fetch logic with Telethon
2. ✅ Added proper error handling and logging
3. ✅ Fixed bug in vacancy_service.py (channel vs channel_id)
4. ✅ Added detailed error messages for missing credentials
5. ✅ Created helper script for session generation
6. ✅ .gitignore already includes `data/*.sqlite`

## Next Steps
After entering valid credentials, the system will:
- Connect to your Telegram account
- Read messages from enabled channels
- Parse vacancy posts using LLM
- Create vacancies and extract contacts
- Track processed messages to avoid duplicates

---

## LLM Configuration for Google AI Studio (Gemini)

### Current Configuration (Updated 2026-08-09)

The system now supports **Google AI Studio** with Gemini models as an alternative to OpenAI.

#### Default Settings:
- **Base URL**: `https://generativelanguage.googleapis.com/v1beta/openai/`
- **Model**: `gemini-1.5-flash` (free tier available)
- **API Key**: Get from https://aistudio.google.com/app/apikey

#### How to Configure:

1. **Get Google AI Studio API Key**:
   - Go to https://aistudio.google.com/app/apikey
   - Click "Create API Key"
   - Copy the key (starts with `AIza...`)

2. **Update Settings in UI**:
   - Go to Settings page
   - In LLM Configuration section:
     - **API Key**: Paste your Google AI Studio API key
     - **Base URL**: `https://generativelanguage.googleapis.com/v1beta/openai/`
     - **Model**: `gemini-1.5-flash`
   - Click "Save Settings"

#### Compatibility:

The LLM service automatically detects which provider you're using based on the `base_url`:

| Provider | Base URL | Model Examples | JSON Format |
|----------|----------|----------------|-------------|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o`, `gpt-4-turbo` | `response_format: {type: "json_object"}` |
| Google AI Studio | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-1.5-flash`, `gemini-1.5-pro` | `response_mime_type: "application/json"` |
| OpenRouter | `https://openrouter.ai/api/v1` | Various | `response_format: {type: "json_object"}` |
| Custom | Any custom URL | Any compatible model | Auto-detected |

#### Testing Your Configuration:

After saving settings, test the connection:

```bash
cd /workspace/job-autopilot
python3 -c "
from app.services.llm_service import LLMService
import asyncio

llm = LLMService()
print(f'Configured: {llm.is_configured()}')
print(f'Base URL: {llm.base_url}')
print(f'Model: {llm.model}')

async def test():
    result = await llm.generate_text(
        system_prompt='You are a helpful assistant.',
        user_prompt='Say hello in one sentence.'
    )
    print(f'Response: {result}')

asyncio.run(test())
"
```

#### Troubleshooting:

**Error 400 Bad Request**:
- Check that `base_url` ends with `/` for Google AI Studio
- Verify API key is valid and not expired
- Ensure model name is correct (`gemini-1.5-flash`)

**Error 403 Forbidden**:
- API key may be invalid or revoked
- Check quota limits in Google AI Studio console

**Error 429 Too Many Requests**:
- You've hit rate limits
- Free tier has limits: ~15 requests per minute for gemini-1.5-flash
- Wait and retry, or upgrade to paid tier

**Empty Responses**:
- Check LLM logs for detailed error messages
- Verify the prompt is not too long (max 1M tokens for Gemini)
- Try with simpler prompts first
