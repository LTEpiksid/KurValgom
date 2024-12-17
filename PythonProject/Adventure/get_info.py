import logging
import functools
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

BLACKLIST_FILE = 'blacklist.txt'
restaurant_cache = {}

def verify_page(driver):
    try:
        driver.find_element(By.CSS_SELECTOR, "div.quick-info")
        return True
    except:
        return False

def add_to_blacklist(name):
    with open(BLACKLIST_FILE, 'a', encoding='utf-8') as file:
        file.write(name + '\n')

def is_blacklisted(name):
    try:
        with open(BLACKLIST_FILE, 'r', encoding='utf-8') as file:
            blacklisted = file.read().splitlines()
        return name in blacklisted
    except FileNotFoundError:
        return False

@functools.lru_cache(maxsize=100)
def get_cached_restaurant_info(name):
    return get_restaurant_info(name)

def get_restaurant_info(name):
    if name in restaurant_cache:
        logging.info(f"Using cached data for restaurant: {name}")
        return restaurant_cache[name]

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920x1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        formatted_name = name.lower().replace(' ', '-')
        urls = [
            f"https://www.meniu.lt/vieta/{formatted_name}-1",
            f"https://www.meniu.lt/vieta/{formatted_name}-vilnius-1",
            f"https://www.meniu.lt/vieta/{formatted_name}-vilnius",
            f"https://www.meniu.lt/vieta/{formatted_name}-vilnius-2",
            f"https://www.meniu.lt/vieta/{formatted_name}"
        ]

        logging.info(f"Generating restaurant: {name}")

        for url in urls:
            driver.get(url)
            logging.info(f"Attempted URL: {url}")
            if verify_page(driver):
                logging.info(f"Loaded valid URL: {driver.current_url}")
                description, image_urls, menu_pdfs, rating = extract_info(driver)
                restaurant_cache[name] = (description, image_urls, menu_pdfs, rating)
                return description, image_urls, menu_pdfs, rating

        logging.info(f"Failed to load a valid page for {name}")
        add_to_blacklist(name)
        return "No description available", ["https://via.placeholder.com/300.png?text=Restaurant+Image"], [], "No rating available"

    except Exception as e:
        logging.error(f"Failed to load page for restaurant: {name} - {str(e)}")
        return "No description available", ["https://via.placeholder.com/300.png?text=Restaurant+Image"], [], "No rating available"

    finally:
        driver.quit()

def extract_info(driver):
    try:
        quick_info_element = driver.find_element(By.CSS_SELECTOR, "div.quick-info")
        description = quick_info_element.text
        logging.info(f"Found Greita Informacija: {description}")
    except Exception as e:
        description = "No description available"
        logging.error(f"Failed to extract description: {str(e)}")

    try:
        image_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'swiper-slide') and @data-background-image]")
        image_urls = [element.get_attribute("data-background-image") for element in image_elements[:3]]
        logging.info(f"Found image URLs: {image_urls}")
    except Exception as e:
        image_urls = ["https://via.placeholder.com/300.png?text=Restaurant+Image"]
        logging.error(f"Failed to extract images: {str(e)}")

    try:
        menu_elements = driver.find_elements(By.CSS_SELECTOR, "div#r-menu a.wrapper")
        menu_pdfs = [element.get_attribute("href") for element in menu_elements]
        logging.info(f"Found menu PDFs: {menu_pdfs}")
    except Exception as e:
        menu_pdfs = []
        logging.error(f"Failed to extract menu PDFs: {str(e)}")

    try:
        # Extract the rating using the fork-overlay element
        fork_overlay_element = driver.find_element(By.CSS_SELECTOR, "div.fork-overlay")
        rating_element = fork_overlay_element.find_element(By.XPATH, "following-sibling::span")
        rating = rating_element.text.strip()
        logging.info(f"Found rating: {rating}")
    except Exception as e:
        rating = "No rating available"
        logging.error(f"Failed to extract rating: {str(e)}")

    return description, image_urls, menu_pdfs, rating
