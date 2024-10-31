from time import sleep
from playwright.sync_api import sync_playwright
import os
import csv
import json





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

with open("input.txt") as file:
    categories = file.readlines()
    categories = [x.strip() for x in categories]
    for category in categories:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(chrome_path),
                headless=False,
                args=args,
            )
            context = browser.new_context(storage_state=storage_state_file, no_viewport=True)
            page = context.new_page()

            link_list = []
            i = 1
            while True:
                page.goto(f"https://www.amazon.com/s?k={category.replace(" ","+")}&page={str(i)}")
                pagination = page.locator("//span[@class='s-pagination-strip']")
                if pagination.count() == 0:
                    break
                    # break when no pagination found after search

                # Initial filter, AMZ, FBA
                card_list = page.query_selector_all('//div[@data-component-type="s-search-result"]')

                p_i = 1
                while True:
                    # Check if the delivery information exists and contains "by amazon"
                    prime = page.locator(f"(//i[@aria-label='Amazon Prime'])[{str(p_i)}]")
                    # if prime i button found means it is amazon's product
                    product_url = page.locator(f"(//div[@data-cy='title-recipe'])[{str(p_i)}]//h2//a")
                    delivery = page.locator(f"(//div[@data-cy='delivery-recipe'])[{str(p_i)}]")
                    if not product_url.count() > 0:
                        break
                        # when no product url found in search page then break

                    if delivery.count() > 0:
                        if "by amazon" not in delivery.inner_text().lower() and prime.count() == 0:
                            url = product_url.get_attribute("href")
                            link_list.append("https://www.amazon.com" + url)
                    p_i += 1
                i += 1

            all_data = []
            i = 0
            for product_link in link_list:
                try:
                    page.goto(product_link)
                    shipping_card = page.locator("//div[@id='offerDisplayFeatures_desktop']")
                    if shipping_card.count() > 0:
                        price = '0'
                        high_price = '0'
                        low_price = '0'
                        skip = False
                        if "amazon" not in shipping_card.inner_text().lower():
                            print(f'Found No. {str(i)}. {product_link}')
                            product_price = page.locator("(//div[@id='corePriceDisplay_desktop_feature_div']//span[@class='a-price-whole'])[1]")
                            price = product_price.inner_text() if product_price.count() > 0 else ''
                            more_element = page.locator("//div[@id='dynamic-aod-ingress-box']//a[@class='a-link-normal']")
                            if more_element.count() > 0:
                                more_element.click()
                                sleep(3)
                                price_list = []
                                price_i = 1
                                while True:
                                    temp_price = page.locator(f"(//div[@id='aod-offer']//span[@class='a-price-whole'])[{str(price_i)}]")
                                    if temp_price.count() == 0:
                                        break
                                    ship_ele = page.locator(f"(//div[@id='aod-offer']//div[@id='aod-offer-shipsFrom'])[{str(price_i)}]")
                                    if ship_ele.count() > 0:
                                        if "amazon" in ship_ele.inner_text().lower():
                                            skip = True
                                            price_list.append('0')
                                            break
                                        else:
                                            print("temp_price.inner_text() : ", temp_price.inner_text())
                                            price_list.append(temp_price.inner_text())
                                    price_i += 1
                                price_list.sort()
                                low_price = price_list[0]
                                high_price = price_list[-1]

                        if skip == False:
                            dicts = {
                                'url': product_link,
                                'price': price,
                                'low_price': low_price,
                                'high_price': high_price
                             }
                            all_data.append(dicts)
                            header = ['url','price','low_price','high_price']
                            if not os.path.exists(category):
                                os.mkdir(category)
                            with open(f'{category}/data.csv', 'w', newline='', encoding='utf-8') as file:
                                writer = csv.DictWriter(file, fieldnames=header)
                                writer.writeheader()
                                writer.writerows(all_data)
                        else:
                            print(f'Not FBM No. {str(i)}. {product_link}')
                except Exception as ops:
                    print(f'Found No. {str(i)} : {ops}')
                    pass
                i += 1
            browser.close()
