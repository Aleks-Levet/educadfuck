"""
EducadFuck - A tool for scraping Educadhoc manuals FOR EDUCATIONAL PURPOSES, FOR SCIENCE
Copyright (C) 2025 Aleks Levet

This program is free software under GNU GPL v3.
"""
import json, pathlib, time
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image

CONFIG_FILE = "config.json"
TEMP_FOLDER = Path("temp_pages")

# --- Load or initialize config ---
def load_config():
    if Path(CONFIG_FILE).exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

config = load_config()

reconfig = input("Reconfigure settings? [y/N]: ").lower() == "y" or not config
if reconfig:
    config["manual_url"] = input("Enter manual URL (Page_1): ").strip()
    config["output_pdf"] = input("Output PDF name: ").strip()
    config["page_count"] = int(input("Number of pages: ").strip())
    save_config(config)

# --- Temp folder management ---
if TEMP_FOLDER.exists():
    if input(f"Delete temp folder '{TEMP_FOLDER}'? [y/N]: ").lower() == "y":
        for f in TEMP_FOLDER.iterdir():
            f.unlink()
        TEMP_FOLDER.rmdir()
TEMP_FOLDER.mkdir(exist_ok=True)

# --- Playwright ---
with sync_playwright() as p:
    print("🚀 Launching headful Chrome...")
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(config["manual_url"])
    print("✅ Loaded first page, starting screenshots...")

    base_url = config["manual_url"].split("Page_")[0]
    total_pages = config["page_count"]

    for i in range(1, total_pages + 1):
        screenshot_file = TEMP_FOLDER / f"{i:03d}.png"
        if screenshot_file.exists():
            print(f"✅ Skipping page {i}, already captured.")
            continue

        page_url = f"{base_url}Page_{i}.html?interface=postMessage"
        print(f"📄 Loading page {i}: {page_url}")
        page.goto(page_url)
        time.sleep(1)  # allow JS/fade

        # Extreme zoom (4x)
        page.evaluate("document.querySelector('#page-container').style.zoom = 4.0")
        el = page.locator("#page-container").element_handle()
        print(f"📸 Capturing screenshot to {screenshot_file}")
        el.screenshot(path=str(screenshot_file))

    print("🎉 All pages captured!")
    browser.close()

# --- PDF creation ---
from fpdf import FPDF

print("📄 Creating PDF...")
images = sorted(TEMP_FOLDER.glob("*.png"))
pdf = FPDF(unit="pt", format=[2480, 3508])  # A4 4x zoom ~ 2480x3508

for img_path in images:
    print(f"➡ Adding {img_path}")
    pdf.add_page()
    pdf.image(str(img_path), x=0, y=0, w=2480, h=3508)

pdf.output(config["output_pdf"])
print(f"✅ PDF saved as {config['output_pdf']}")
