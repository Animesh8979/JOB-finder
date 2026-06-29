import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Listen for console events
        def log_console(msg):
            print(f"BROWSER CONSOLE: {msg.type}: {msg.text}")
            
        page.on("console", log_console)
        page.on("pageerror", lambda err: print(f"BROWSER ERROR: {err}"))
        
        try:
            # We will run npm run dev in the background and hit 5173
            await page.goto("http://localhost:5173", timeout=10000)
            await asyncio.sleep(2)
        except Exception as e:
            print(f"Failed to load: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
