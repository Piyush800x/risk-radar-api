import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from mongodb import client, vendors_collection
from datetime import datetime

VENDOR_CAPS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U"
               "V", "W", "X", "Y", "Z"]


def scrape_versions(driver: webdriver.Chrome, vendor_name, product_name, product_versions_url):
    version_table_row_count: int = 1
    versions = []

    while True:
        driver.get(product_versions_url)
        try:
            for i in range(1, 51):
                version = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f"/html/body/div[1]/div/div[2]/div/main/div[5]/table/tbody/tr[{i}]/td[1]"))).text
                versions.append(version)
            break
        except TimeoutException:
            break

    print("--------------------------")
    print(vendor_name)
    print(product_name)
    print(versions)
    # Insert in db
    vendor = vendors_collection.find_one({"vendorName": vendor_name.replace(".", "-")})

    if vendor:
        # Vendor exists, update the product's versions
        vendors_collection.update_one(
            {"vendorName": vendor_name.replace('.', '-')},  # Match the vendor
            {"$set": {f"Products.{product_name.replace('.', '-')}": versions}}
            # Update product's versions
        )
    else:
        # Vendor doesn't exist, insert new data
        vendors_collection.insert_one({
            "vendorName": vendor_name.replace(".", "-"),
            "Products": {product_name.replace(".", "-"): versions}
        })
    print("Data insert done")


def scrape_products(driver: webdriver.Chrome, vendor_name, vendor_products_url):
    products_page_count: int = 1
    products_table_row_count: int = 1  # init: 1

    while True:
        driver.get(vendor_products_url + f"/page-{products_page_count}")
        try:
            product_elem = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, f"/html/body/div[1]/div/div[2]/div/main/div[5]/table/tbody/tr[{products_table_row_count}]/td[1]/a")))

            product_name = product_elem.text
            product_versions_url = product_elem.get_attribute("href")

            scrape_versions(driver, vendor_name, product_name, product_versions_url)
            products_table_row_count += 1

        except TimeoutException:
            if products_page_count >= 50:
                break
            if products_table_row_count > 50:
                products_page_count += 1
                products_table_row_count = 1
                continue
            else:
                products_table_row_count += 1
            break


def scrape_vendor(driver: webdriver.Chrome):
    global VENDOR_CAPS

    vendor_page_count: int = 1
    vendor_table_row_count: int = 1     # init: 1
    for caps in VENDOR_CAPS:
        vendor_url: str = f"https://www.cvedetails.com/vendor/firstchar-{caps}/{vendor_page_count}/?sha=7ffe6d499472dec0d84de30f031c4ee7be715225&trc=2560&order=1"
        active_vendor: bool = True
        # This loop is for to scrape maximum 100 pages for vendors of char "A", "B" ....
        while True:
            driver.get(vendor_url)
            try:
                vendor_name = WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.XPATH, f"/html/body/div[1]/div/div[2]/div/main/div[5]/table/tbody/tr[{vendor_table_row_count}]/td[1]/a"))).text
                vendor_products_url = WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.XPATH, f"/html/body/div[1]/div/div[2]/div/main/div[5]/table/tbody/tr[{vendor_table_row_count}]/td[2]/a"))).get_attribute("href")

                # Scrape Products
                scrape_products(driver, vendor_name, vendor_products_url)
                vendor_table_row_count += 1
            except TimeoutException:
                if vendor_page_count >= 100:
                    break
                if vendor_table_row_count > 50:
                    vendor_page_count += 1
                    vendor_table_row_count = 1
                    continue
                else:
                    vendor_table_row_count += 1
                break


def main():
    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }

    options = webdriver.ChromeOptions()
    options.binary_location = "C:\Program Files\Google\Chrome\Application\chrome.exe"
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")
    # NEW BELOW
    options.add_argument("--disable-cache")
    options.add_argument("--disk-cache-size=1")
    # options.add_argument("--incognito")
    # NEW
    # options.add_argument('--start-fullscreen')
    options.add_argument('--single-process')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("disable-infobars")
    # options.add_argument(f'user-agent={useragents[0]}')

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("prefs", prefs)
    # options.add_argument("--window-size=1440,900")  # TODO FOR HEADLESS
    # options.add_argument("--start-maximized")  # TODO FOR HEADLESS
    # options.add_argument("--headless=new")  # TODO FOR HEADLESS
    service = Service(executable_path=f"chromedriver.exe")  # WORKING HERE
    # webdriver.DesiredCapabilities.CHROME['acceptSslCerts'] = True
    c_driver = webdriver.Chrome(service=service, options=options)
    c_driver.set_window_size(1920, 1080)

    scrape_vendor(driver=c_driver)


if __name__ == '__main__':
    main()

