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
