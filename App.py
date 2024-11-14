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


def find_price(text):
    # Regex to match 2-3 digit numbers with optional decimal part
    pattern = r"\b\d{2,3}(?:\.\d{1,2})?\b"
    match = re.search(pattern, text)
    if match:
        return float(match.group())
    else:
        return 0.0

def find_amazon(text):
    pattern = r"a\s*m\s*a\s*z\s*o\s*n"
    matches = re.findall(pattern, text, re.IGNORECASE)
    if matches:
        return True
    else:
        return False

def insert_at_position(d, key, value, position):
    items = list(d.items())
    items.insert(position, (key, value))
    return dict(items)

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

            print(f'>> Scrapping category:- "{category}", search result pages..')
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
                    product_url = page.locator(f"(//a[@class='a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal'])[{str(p_i)}]")
                    delivery = page.locator(f"(//div[@data-cy='delivery-recipe'])[{str(p_i)}]")
                    prime = page.locator(f"(//div[@data-component-type='s-search-result'])[{str(p_i)}]//i[@aria-label='Amazon Prime']")
                    if not product_url.count() > 0:
                        break
                        # when no product url found in search page then break
                    if delivery.count() > 0:
                        if not find_amazon(delivery.inner_text()) and prime.count() == 0:
                            url = product_url.get_attribute("href")
                            link_list.append("https://www.amazon.com" + url)

                    p_i += 1
                i += 1



            all_data = []
            i = 0
            print(f"For Ctegory : {category} initially founded : {str(len(link_list))} products..\n")
            for product_link in link_list:
                print(f'Found No. {str(i)}. {product_link.split('ref')[0]}')
                try:
                    page.goto(product_link)
                    shipping_card = page.locator("(//div[@id='buybox'])[1]")
                    if shipping_card.count() > 0:
                        skip = False
                        if not find_amazon(shipping_card.inner_text()):
                            product_price = page.locator("(//div[@id='corePriceDisplay_desktop_feature_div']//span[@class='a-price-whole'])[1]")
                            price = find_price(product_price.inner_text()) if product_price.count() > 0 else 0
                            more_element = page.locator("//div[@id='dynamic-aod-ingress-box']//a[@class='a-link-normal']")
                            price_list = [0]
                            if more_element.count() > 0:
                                more_element.click()
                                sleep(3)
                                price_i = 1
                                while True:
                                    temp_price = page.locator(f"(//div[@id='aod-offer']//span[@class='a-price-whole'])[{str(price_i)}]")
                                    if temp_price.count() == 0:
                                        break
                                    ship_ele = page.locator(f"(//div[@id='aod-offer']//div[@id='aod-offer-shipsFrom'])[{str(price_i)}]")
                                    if ship_ele.count() > 0:
                                        if find_amazon(ship_ele.inner_text()):
                                            skip = True
                                            break
                                        else:
                                            price_list.append(find_price(temp_price.inner_text()))
                                    price_i += 1
                                price_list.sort()
                                print('price_list : ', price_list)

                            if not skip:
                                low_price = price_list[0]
                                high_price = price_list[-1]
                                dicts = {
                                    'url': product_link,
                                    'price': price,
                                    'low_price': low_price,
                                    'high_price': high_price
                                 }
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
                                                dicts = insert_at_position(dicts, key, value.replace('\u200e', ''),index)
                                                break
                                all_data.append(dicts)
                                header = ['url','price','low_price','high_price',
                                          "Product Dimensions",
                                          "Item model number",
                                          "Department",
                                          "Date First Available",
                                          "Manufacturer",
                                          "ASIN",
                                          "Rank",
                                          "Reviews"]
                                if not os.path.exists('data'):
                                    os.mkdir('data')
                                with open(f'data/{category}.csv', 'w', newline='', encoding='utf-8') as file:
                                    writer = csv.DictWriter(file, fieldnames=header)
                                    writer.writeheader()
                                    writer.writerows(all_data)
                            else:
                                print(f'No. {str(i)}. product is not FBM so skipped after check other sellers.. \n')
                        else:
                            print(f'No. {str(i)}. product is not FBM so skipped after visit product page.. \n')
                    else:
                        print(f'No. {str(i)}. buybox HTML Section did not detected..  \n')
                except Exception as ops:
                    print(f'Found No. {str(i)} : {ops}')
                    pass
                i += 1
            browser.close()
