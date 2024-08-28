from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from bs4 import BeautifulSoup

import pandas as pd
import time
import re
import asyncio
from requests_html import AsyncHTMLSession


external_link = "https://www.cornerstoneinsurance.org"  # contact-us
options = webdriver.ChromeOptions()
# options.add_argument("")
driver = webdriver.Chrome()
driver.get(external_link)

print("this is current url: ", driver.current_url)
# contact_button = driver.find_element(
#     By.CSS_SELECTOR,
#     "a[href*='contact'], a[href*='Contact'], a[href*='CONTACT'], a[href*='https://www.cornerstoneinsurance.org/contact-us']")

contact_button = driver.find_element(
    By.CSS_SELECTOR,
    "a[href='https://www.cornerstoneinsurance.org/contact-us']")

contact_button.get_attribute("href")

pattern2 = "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"