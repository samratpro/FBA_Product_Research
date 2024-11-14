from time import sleep
from playwright.sync_api import sync_playwright
import os
import csv
import json
import re



args=[
     '--disable-blink-features=AutomationControlled',
     '--start-maximized',
     '--disable-infobars',
     '--no-sandbox',
     '--disable-dev-shm-usage',
     '--disable-extensions',
     '--remote-debugging-port=0',
     '--disable-web-security',
     '--enable-features=WebRTCPeerConnectionWithBlockIceAddresses',
     '--force-webrtc-ip-handling-policy=disable_non_proxied_udp',
 ]

chrome_path = os.path.join(os.getcwd(), "chrome-win/chrome.exe")
# Define a function that opens the browser and returns the browser and contex
storage_state_file = os.path.join(os.getcwd(), "storage_state.json")
def is_storage_state_valid(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return bool(data)  # true false depend data exist
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return False
    else:
        open(file_path, 'w').close()  # Create an empty file
        return False

def cookie_save():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=str(chrome_path),
            headless=False,
            args=args,
        )
        if is_storage_state_valid(storage_state_file):
            context = browser.new_context(storage_state=storage_state_file, no_viewport=True)
        else:
            context = browser.new_context(no_viewport=True)

        page = context.new_page()
        page.goto("https://www.amazon.com/")

        input("Press Enter to save data: ")

        # Save the storage state (including cookies)
        context.storage_state(path=storage_state_file)
        print("Data saved...")
        browser.close()



if not is_storage_state_valid(storage_state_file):
    cookie_save()

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        executable_path=str(chrome_path),
        headless=False,
        args=args,
    )
    context = browser.new_context(storage_state=storage_state_file, no_viewport=True)
    page = context.new_page()
    page.goto(f"https://www.amazon.com/JENN-ARDOR-Pointed-Backless-Numeric_6/dp/B08KG9CSKX")

    dicts = {}

    def insert_at_position(d, key, value, position):
        items = list(d.items())
        items.insert(position, (key, value))
        return dict(items)
    fields_mapping = {
        "Product Dimensions": 0,
        "Item model number": 1,
        "Department": 2,
        "Date First Available": 3,
        "Manufacturer": 4,
        "ASIN": 5,
        "Rank": 6,
        "Reviews": 7
    }
    product_des = page.locator("//div[@id='detailBulletsWrapper_feature_div']//ul//span[@class='a-list-item']")
    if product_des.count() > 0:
        for pd in product_des.element_handles():
            line = pd.inner_text()

            for key, index in fields_mapping.items():
                if key in line:
                    _, value = line.split(":", 1)
                    dicts = insert_at_position(dicts, key, value.replace('\u200e',''), index)
                    break

    print(dicts)



    input("Enter to close:")





    browser.close()