import requests
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
import pandas as pd
import time
from geopy.geocoders import Nominatim
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

API_KEY = ""


def get_coordinates_google(address, api_key):
    return None
    # base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    # params = {"address": address, "key": api_key}
    #
    # response = requests.get(base_url, params=params)
    # data = response.json()
    #
    # if data["status"] == "OK":
    #     location = data["results"][0]["geometry"]["location"]
    #     return location["lat"], location["lng"]
    # else:
    #     print(f"Error: {data['status']}")
    #     return None


def get_coordinates(address):
    geolocator = Nominatim(user_agent="geo_locator")

    # Try multiple times in case of timeout
    for _ in range(3):
        try:
            location = geolocator.geocode(address)
            if location:
                return location.latitude, location.longitude
            else:
                return None
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)  # Avoid rate limiting

    return None


def get_selenium_soup(url, timeout=30):
    chrome_options = Options()
    #chrome_options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)

        # Wait until basic content is loaded
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Optionally scroll to help JS-triggered elements load
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(2)

        html = driver.page_source
        return BeautifulSoup(html, "html.parser")

    except TimeoutException:
        print("⏳ Timed out waiting for the page to load.")
        with open("failed_debug.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        raise

    finally:
        driver.quit()

# def get_selenium_soup(url, timeout=20):
#     chromedriver_autoinstaller.install()  # Auto-installs the correct ChromeDriver
#     options = Options()
#     options.add_argument("--headless")  # Run in headless mode (no browser window)
#     options.add_argument("--disable-gpu")
#     options.add_argument("--no-sandbox")
#
#     # Start WebDriver
#     driver = webdriver.Chrome(service=Service(), options=options)
#     driver.get(url)
#     # time.sleep(3)  # Wait for JavaScript to load
#     WebDriverWait(driver, timeout).until(
#         EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='cat-rescue-centres']"))
#     )
#
#     # Get page source after JavaScript executes
#     page_source = driver.page_source
#     driver.quit()  # Close browser
#
#     return BeautifulSoup(page_source, "html.parser")


def get_soup(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return BeautifulSoup(response.text, "html.parser")
    else:
        print(f"Failed to retrieve {url} - Status code: {response.status_code}")
        return None

def main():
    base_url = "https://www.catchat.org/index.php/cat-rescue-centres-uk-ireland"
    #main_soup = get_soup(base_url)
    main_soup = get_selenium_soup(base_url)

    regions = {}
    shelters = []
    for link in main_soup.find_all("a", href=True):
        href = link["href"]
        if "cat-rescue-centres" in href and href != "/index.php/cat-rescue-centres-uk-ireland":
            region_name = link.text.strip()
            region_url = "https://www.catchat.org" + href
            regions[region_name] = region_url

    address_keywords = ["Postal Address:", "Address:", "Tel:", "Email:", "Rehoming Shelter", "Shelter", "Rescue Centre:"]

    for region, url in regions.items():
        print(f"Processing region: {region} -> {url}")

        region_soup = get_selenium_soup(url)
        if not region_soup:
            continue

        long = None
        lat = None
        address_postal = None
        tel = None
        email = None
        website = None
        meta = None

        ps = region_soup.find_all("p")
        for i, p in enumerate(ps):
            text = p.get_text(separator=" ", strip=True)
            #text stores each shelter scrapped information

            if any(keyword in text for keyword in address_keywords):
                match = re.search(r"Postal Address:\s*(.*?)(Tel:|Email:|$)", text)
                if match:
                    address_postal = match.group(1).strip()

                if address_postal is None:
                    match = re.search(r"Rescue Centre:\s*(.*?)(Tel:|Email:|$)", text)
                    if match:
                        address_postal = match.group(1).strip()
                        address_postal = address_postal.split('(')[0].strip()

                if address_postal is None:
                    match = re.search(r"Rehoming Shelter:\s*(.*?)(Tel:|Email:|$)", text)
                    if match:
                        address_postal = match.group(1).strip()
                        address_postal = address_postal.split('(')[0].strip()

                match = re.search(r"Tel:\s*([\d\s\+\(\)-]+)", text)
                if match:
                    tel = match.group(1).strip()

                match = re.search(r"Email:\s*([\w\.-]+@[\w\.-]+\.\w+)", text)
                if match:
                    email = match.group(1).strip()

                match = re.search(r"(https?://[^\s]+|www\.[^\s]+)", text)
                if match:
                    website = match.group(1).strip()

            if not email:
                print("Email not found with BeautifulSoup, using Selenium...")
                region_soup = get_selenium_soup(url)
                for p in region_soup.find_all("p"):
                    text = p.get_text(separator=" ", strip=True)
                    match = re.search(r"Email:\s*([\w\.-]+@[\w\.-]+\.\w+)", text)
                    if match:
                        email = match.group(1).strip()
                        break

            # Print extracted details
            print(f"Region: {region}")
            if address_postal:
                print(f"Address: {address_postal}")
                #coordinates = get_coordinates(address_postal)
                coordinates = get_coordinates_google(address_postal, API_KEY)
                if coordinates is not None:
                    lat = coordinates[0]
                    long = coordinates[1]
            if tel:
                print(f"Phone: {tel}")
            if email:
                print(f"Email: {email}")
            if website:
                print(f"website: {website}")
            if long:
                print(f"long: {long}")
            if lat:
                print(f"lat: {lat}")

            print("-" * 40)
            time.sleep(1)
            shelter = {"region": region, "address": address_postal, "tel": tel, "email": email, "long": long, "lat": lat, "website": website, 'url': url, 'meta': text}
            shelters.append(shelter)

    df = pd.DataFrame(shelters)
    df.to_csv("shelters_all.csv", index=None)


if __name__ == "__main__":
    main()
