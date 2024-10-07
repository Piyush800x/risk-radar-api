import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from mongodb import client, vendors_collection
from datetime import datetime

log_file = open("log.txt", "at")
log_file.write(f"{datetime.now()}\n")
# logger.setLevel(logging.DEBUG)


VENDOR_CAPS = ["D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U"
               "V", "W", "X", "Y", "Z"]


def scrape(driver: webdriver.Chrome):
    global VENDOR_CAPS, product_count

    for caps in VENDOR_CAPS:
        page_count_1: int = 1
        active_4: bool = True
        while active_4:
            try:
                # This loop is for example: A has 1--100 pages
                table_row_count: int = 1  # Reset the table_row_count for each new page
                main_vendor_url: str = f"https://www.cvedetails.com/vendor/firstchar-{caps}/{page_count_1}/?sha=7ffe6d499472dec0d84de30f031c4ee7be715225&trc=2560&order=1"
                # main_vendor_url: str = f"https://www.cvedetails.com/vendor-search.php?search=Adobe"
                # driver.get(main_vendor_url)
                active_2: bool = True
                while active_2:
                    driver.get(main_vendor_url)
                    try:
                        print("Finding...")
                        vendor_name = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/"
                                                                      "div/div[2]/div"
                                                                      "/main/div[5]/table"
                                                                      f"/tbody/tr[{table_row_count}]/"
                                                                      "td[1]/a"))).text

                        # # Test
                        # vendor_name = WebDriverWait(driver, 10).until(
                        #     EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[2]/div/main/div[2]/table/tbody/tr[2]/td[1]"))).text

                        print("---------------------------------------------------")
                        print(f"Vendor Name: {vendor_name}")
                        try:
                            products_url = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,
                                                                                                           f"/html/body/div[1]/div/div[2]/div/main/div[5]/table/tbody/tr[{table_row_count}]/td[2]/a"))).get_attribute(
                                "href")

                            # # Test
                            # products_url = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,
                            #                                                                                f"/html/body/div[1]/div/div[2]/div/main/div[2]/table/tbody/tr[2]/td[2]/a"))).get_attribute(
                            #     "href")
                            print(f"Products Urls: {products_url}")

                            # Initialize the product page counter
                            products_counter = 1
                            active_products_page = True

                            # Loop to handle multiple product pages
                            while active_products_page:
                                # Get the current product page URL
                                current_products_url = products_url if products_counter == 1 else f"{products_url}/page-{products_counter}"
                                driver.get(current_products_url)

                                active: bool = True
                                product_count = 1
                                while active:
                                    driver.get(current_products_url)
                                    try:
                                        product_name_ele = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located((By.XPATH,
                                                                            f"/html/body/div[1]/div/div[2]/div/main/div[5]/table/tbody/tr[{product_count}]/td[1]/a")))

                                        product_name = product_name_ele.text
                                        product_ver_url = product_name_ele.get_attribute("href")

                                        print(f"Product Name: {product_name}")
                                        print(f"Product ver urls: {product_ver_url}")

                                        product_versions = []
                                        active_3: bool = True
                                        version_row_count: int = 1

                                        while active_3:
                                            try:
                                                driver.get(product_ver_url)
                                                version = WebDriverWait(driver, 10).until(
                                                    EC.presence_of_element_located((By.XPATH,
                                                                                    f"/html/body/div[1]/div/div[2]/div/main/div[5]/table/tbody/tr[{version_row_count}]/td[1]"))).text
                                                product_versions.append(version)
                                                version_row_count += 1
                                            except TimeoutException:
                                                version_row_count = 1
                                                active_3 = False

                                        print(f"Product Versions: {product_versions}")
                                        # Insert/update the vendor and product versions in the database
                                        vendor = vendors_collection.find_one({"vendorName": vendor_name.replace(".",
                                                                                                                "-")})

                                        if vendor:
                                            # Vendor exists, update the product's versions
                                            vendors_collection.update_one(
                                                {"vendorName": vendor_name.replace(".", "-")},  # Match the vendor
                                                {"$set": {f"Products.{product_name.replace('.', '-')}": product_versions}}
                                                # Update product's versions
                                            )
                                        else:
                                            # Vendor doesn't exist, insert new data
                                            vendors_collection.insert_one({
                                                "vendorName": vendor_name.replace(".", "-"),
                                                "Products": {product_name.replace(".", "-"): product_versions}
                                            })
                                        print("Data insert done")
                                        product_count += 1  # Increment count for next product row

                                    except TimeoutException:
                                        # No more products on the current page
                                        active = False
                                        print(
                                            f"Finished scraping products on page {products_counter} for vendor: {vendor_name}")
                                        pass

                                # Try to move to the next page of products if exists
                                try:
                                    driver.get(current_products_url)
                                    next_page_link = driver.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/div/main/div[4]/a[2]")
                                    products_counter += 1  # Increment the product page counter
                                    product_count = 1
                                    print(f"Moving to page {products_counter} of products for vendor: {vendor_name}")
                                except NoSuchElementException:
                                    # No more product pages, stop the loop
                                    active_products_page = False
                                    table_row_count += 1
                                    print(f"Finished scraping all product pages for vendor: {vendor_name}")

                        except TimeoutException:
                            pass
                    except TimeoutException:
                        # Move to the next row (increment the table_row_count)
                        # table_row_count += 1
                        if table_row_count > 50:  # Adjust this number if there are fewer rows per page
                            active_2 = False
                            table_row_count = 1  # Reset for the next page
                            page_count_1 += 1  # Increment page count
                            print(f"Moving to page {page_count_1} for letter {caps}")

            except TimeoutException:
                log_file.writelines(f"Letter {caps} Page {page_count_1} Done\n")
                log_file.flush()
                active_4 = False  # Stop if no more pages


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

    scrape(c_driver)


if __name__ == '__main__':
    main()
