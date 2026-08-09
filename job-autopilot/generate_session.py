#!/usr/bin/env python3
"""
Script to generate Telegram session string.
Run this script with your API ID and API Hash to get a valid session string.
"""

import asyncio
from telethon.sync import TelegramClient

# Replace these with your actual credentials from my.telegram.org
API_ID = 123456  # Your API ID here
API_HASH = "your_api_hash_here"  # Your API Hash here

async def main():
    print("Telegram Session String Generator")
    print("=" * 40)
    print(f"Using API ID: {API_ID}")
    print(f"Using API Hash: {API_HASH[:10]}...")
    print()
    
    # Create client with memory session
    client = TelegramClient('temp_session', API_ID, API_HASH)
    
    await client.start()
    
    if await client.is_user_authorized():
        print("\n✓ Successfully authorized!")
        session_string = client.session.save()
        print("\nYour session string:")
        print("-" * 40)
        print(session_string)
        print("-" * 40)
        print("\nCopy this string and paste it into Settings > Reader Session")
    else:
        print("\n✗ Not authorized. Please run the script again and follow the prompts.")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
