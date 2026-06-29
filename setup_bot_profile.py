import asyncio
from playwright.async_api import async_playwright
import os
from pathlib import Path

# Try to load config so we match the exact directory
try:
    from src import config
    bot_profile_dir = config.DATA_DIR / "bot_profile"
except ImportError:
    bot_profile_dir = Path("data") / "bot_profile"

async def main():
    bot_profile_dir.mkdir(parents=True, exist_ok=True)
    
    print("=========================================")
    print("🤖 Ai Job Finder - Bot Profile Setup 🤖")
    print("=========================================")
    print(f"Profile Directory: {bot_profile_dir.absolute()}")
    print("\nThis will open a visible Edge browser window using the dedicated bot profile.")
    print("Please log into LinkedIn or any other job boards you want the bot to use.")
    print("When you are finished logging in, close the browser window.")
    print("=========================================\n")
    
    async with async_playwright() as p:
        try:
            # Launch persistent context NOT headless so the user can login
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(bot_profile_dir),
                channel="msedge",
                headless=False, 
                args=["--disable-blink-features=AutomationControlled"]
            )
            
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto("https://www.linkedin.com/login")
            
            print("Browser launched! Please log in...")
            
            # Wait for the context to be closed by the user
            while len(context.pages) > 0:
                await asyncio.sleep(1)
                
            print("\nBrowser closed. Setup complete!")
            
        except Exception as e:
            print(f"\n❌ Failed to launch browser: {e}")
            print("Make sure no other instances of this bot profile are running.")

if __name__ == "__main__":
    asyncio.run(main())
