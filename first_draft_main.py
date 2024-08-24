from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time
import re
import openpyxl

########################
# navigating to the front page of CitySearch
########################
driver = webdriver.Chrome()
driver.get("https://www.citysearch.com/")


########################
# extracting the links to individual cities
########################
container = driver.find_element(By.CSS_SELECTOR, "div.cities-container")
cities = container.find_elements(By.CSS_SELECTOR, "li:not([class*='state']) > a")
city_links = [city.get_attribute("href") for city in cities]
state, city = re.search("(?<=\.com\/).*", city_links[0]).group().split("/")


########################
# navigating to a city link and gathering popular jobs
########################
# if we have keywords to use, we can use that to iterate over the positions
driver.get(city_links[0]) # as an example will be going through the jobs in first city
try:
    elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.categories-wrapper > ul > li > a")))
except TimeoutException:
    print("Timed out waiting for page to load")

popular_jobs = driver.find_elements(By.CSS_SELECTOR, 'div.categories-wrapper > ul > li > a')
popular_jobs_links = [job.get_attribute("href") for job in popular_jobs]


########################
# navigating to first popular job and extracting links to jobs
########################
driver.get(popular_jobs_links[0])

try:
    elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.list-container > div.card > a")))
except TimeoutException:
    print("Timed out waiting for page to load")

job_cards = driver.find_elements(By.CSS_SELECTOR, "div.list-container > div.card > a")
job_cards_links = [job.get_attribute("href") for job in job_cards]


########################
# scraping job description
########################
business_list = []

for i in range(0, 5): #5 should be job_cards_link's length when implemented fully

    driver.get(job_cards_links[i])

    try:
        elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.business-details")))
    except TimeoutException:
        print("Timed out waiting for page to load")

    # not sure if all business have all their contact info so creating a dictionary based on the class name and value
    business_details = driver.find_elements(By.CSS_SELECTOR, 'div.business-details > *')

    business_details_dict = {
        entry.get_attribute("class"): entry.text
        for entry in business_details
    }

    business_list.append(business_details_dict)
    time.sleep(3)


########################
# converting to dataframe, cleaning column names and exporting to csv
########################
df = pd.DataFrame.from_dict(business_list)

df.rename(columns={
    "business-name": "business name",
    "external-links-container": "external link",
    "phone-trigger": "phone number",
    "business-hours": "business hours"
}, inplace=True)

df.to_csv(f'./{state}_{city}.csv', index=False)

driver.quit()