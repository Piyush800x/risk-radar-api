import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from mongodb import client

product_links = {
    "Google": {
        "Chrome": "https://www.cvedetails.com/version-list/1224/15031/1/Google-Chrome.html",
        "Android": "https://www.cvedetails.com/version-list/1224/19997/1/Google-Android.html",
    },
    "Microsoft": {
        "Windows 10 1803": "https://www.cvedetails.com/version-list/26/135432/1/Microsoft-Windows-10-1803.html",
        "Windows 10 1807": "https://www.cvedetails.com/version-list/26/135433/1/Microsoft-Windows-10-1807.html",
        "Windows 10 1809": "https://www.cvedetails.com/version-list/26/125373/1/Microsoft-Windows-10-1809.html",
        "Windows 10 1903": "https://www.cvedetails.com/version-list/26/135717/1/Microsoft-Windows-10-1903.html",
        "Windows 10 1909": "https://www.cvedetails.com/version-list/26/135429/1/Microsoft-Windows-10-1909.html",
        "Windows 10 2004": "https://www.cvedetails.com/version-list/26/135434/1/Microsoft-Windows-10-2004.html",
        "Windows 10 20H2": "https://www.cvedetails.com/version-list/26/125375/1/Microsoft-Windows-10-20h2.html",
        "Windows 10 21H1": "https://www.cvedetails.com/version-list/26/125372/1/Microsoft-Windows-10-21h1.html",
        "Windows 10 21H2": "https://www.cvedetails.com/version-list/26/125374/1/Microsoft-Windows-10-21h2.html",
        "Windows 10 22H1": "https://www.cvedetails.com/version-list/26/125376/1/Microsoft-Windows-10-22h2.html",
        "Windows 11 21H2": "https://www.cvedetails.com/version-list/26/125369/1/Microsoft-Windows-11-21h2.html",
        "Windows 11 22H2": "https://www.cvedetails.com/version-list/26/125370/1/Microsoft-Windows-11-22h2.html",
        "Windows 10 23H2": "https://www.cvedetails.com/version-list/26/164881/1/Microsoft-Windows-11-23h2.html",
        "Windows 10 24H2": "https://www.cvedetails.com/version-list/26/171299/1/Microsoft-Windows-11-24H2.html",
    }
}


def scrape_cve(driver: webdriver.Chrome, url, version) -> dict:
    month = datetime.now().date().month
    year = datetime.now().date().year
    print(f"{month} -- {year}")
    print(f"{version}")
    print(f"{url}")
    driver.get(f"{url}?page=1&cvssscoremin=7&year={year}&month={month}&order=1")
    # time.sleep(200)

    cve = {}

    # Scrape CVEs
    for i in range(1, 25):
        try:
            elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/"
                                                                                             "div[2]/div/main/div[4]/"
                                                                                             f"div[{i}]/div/div[1]/"
                                                                                             "div[1]/h3/a"))).text
            cve[version] = elem

        except TimeoutException:
            break

    return cve


# Cron Job
def scrape(driver: webdriver.Chrome, url):  # , vendor, product
    driver.get(url)
    urls = {}

    # Get 1st 15 versions
    for i in range(1, 16):
        # version
        elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"/html/body/div[1]/div/div[2]/"
                                                      f"div/main/div[5]/table/tbody/"
                                                      f"tr[{i}]/td[1]"))).text

        # a tag for href
        elem2 = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/"
                                                                                          "div[2]/div/main/div[5]/"
                                                                                          f"table/tbody/tr[{i}]/td[6]"
                                                                                          "/a"))).get_attribute("href")
        urls[elem] = elem2

    print(urls)
    with open("urls.txt", "w") as f:
        f.write(f"{urls}")

    version_cve = {}

    for item in urls:
        cve = scrape_cve(driver, urls[item], item)
        version_cve[item] = cve

    with open("cves.txt", "w") as f:
        f.write(f"{version_cve}")


def insert_db(vendor, product, version, cve):
    db = client["risk-radar"]
    collection = db["vendors"]

    query = {
        "vendorName": vendor,
        "products.productName": product
    }

    # Find the document
    existing_entry = collection.find_one(query)

    if existing_entry:
        # Vendor and product exist, update version and CVE
        update = {
            "$set": {
                "products.$.versions." + f"{version.replace('.', '_')}": {
                    "version": version,
                    "cve_id": cve
                }
            }
        }

        # collection.insert_one(data)
        collection.update_one(query, update, upsert=True)
    else:
        # Vendor or product does not exist, insert a new entry
        new_product = {
            "vendorName": vendor,
            "products": [
                {
                    "productName": product,
                    "versions": {
                        f"{version.replace('.', '_')}": {
                            "version": version,
                            "cve_id": cve
                        }
                    }
                }
            ]
        }
        collection.insert_one(new_product)


def test():
    insert_db("Google", "Chrome", "127.0.6533.99", "CVE-2024-2100")


def main():
    prefs = {"credentials_enable_service": False,
             "profile.password_manager_enabled": False}

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
    chrome_driver = webdriver.Chrome(service=service, options=options)
    chrome_driver.set_window_size(1920, 1080)

    # Process Start
    scrape(chrome_driver, product_links["Google"]["Chrome"])


if __name__ == "__main__":
    # main()
    test()
