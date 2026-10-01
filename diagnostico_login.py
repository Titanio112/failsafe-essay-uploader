# Adjusted diagnostic script to use existing Chromium 1228 binary
import sys
sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright
from config import Config

cfg = Config()
print(f"Using configured base URL: {cfg.base_url}")
print(f"Using configured login path: {cfg.login_path}")

# use an os environment override if we want to ensure correct path
# import os
# os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "C:\\Users\\%USERNAME%\\AppData\\Local\\ms-playwright"

with sync_playwright() as p:
    try:
        # will automatically pick up the browsers folder
        browser = p.chromium.launch(headless=True, slow_mo=0)
        page = browser.new_page()
        page.goto(f"{cfg.base_url}{cfg.login_path}")
        print("Page title after navigation:", page.title())
        browser.close()
    except Exception as e:
        print("Error during launch:", e)
        raise

print("Browser launch succeeded (headless), no UI. All good.")