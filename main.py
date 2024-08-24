from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time
import re
import openpyxl

# todo move this dictionary to another script, importing not working for some reason
us_state_to_abbrev = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
    "District of Columbia": "DC",
    "American Samoa": "AS",
    "Guam": "GU",
    "Northern Mariana Islands": "MP",
    "Puerto Rico": "PR",
    "United States Minor Outlying Islands": "UM",
    "U.S. Virgin Islands": "VI",
}

#######################
# testing
#######################
df = pd.read_excel("google_maps_keywords.xlsx")
df.loc[:, ["Country", "State"]] = df.loc[:, ["Country", "State"]].ffill()

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
# grouping dataframe by country then by state
########################
grouped_df = df.groupby("Country")
grouped_countries = grouped_df.get_group("United States") #todo during implementation, instead of United States, it should be iterated
grouped_states = grouped_countries.groupby("State")

states = grouped_states.groups.keys()

########################
# iterating over all the states, then cities, then industries and scarping business information
########################
for state in states:
    state_cities = grouped_states.get_group(state)["City"]
    state_industries = grouped_states.get_group(state)["Industry"]
    state_abbrev = us_state_to_abbrev[state]

    for city in state_cities:
        business_list = []

        if (pd.isnull(city)): continue

        for industry in state_industries:
            if (pd.isnull(industry)): continue

            url = f"https://www.citysearch.com/results?term={industry.strip().replace(' ', '%20')}&where={city.replace(' ', '%20')},%20{state_abbrev}"
            print("-------------------------", url, "----------------------------")
            driver.get(url)

            # extracting all links to jobs in this category
            try:
                elem = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.list-container > div.card > a")))
            except TimeoutException:
                print("Timed out waiting for page to load: Most likely no job listing in this category")

            job_cards = driver.find_elements(By.CSS_SELECTOR, "div.list-container > div.card > a")
            job_cards_links = [job.get_attribute("href") for job in job_cards]

            # visiting each job link for the current industry and scraping information

            if (len(job_cards_links) == 0): continue

            # for i in range(len(job_cards_links)): # todo uncomment this when implementing fully
            for i in range(5):
                print(job_cards_links[i])
                driver.get(job_cards_links[i])

                try:
                    elem = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.business-details")))
                except TimeoutException:
                    print("Timed out waiting for page to load")

                # not sure if all business have all their contact info so creating a dictionary based on the class name and value
                business_details = driver.find_elements(By.CSS_SELECTOR, 'div.business-details > *')

                business_details_dict = {
                    entry.get_attribute("class"): entry.text
                    for entry in business_details
                }
                business_details_dict["industry"] = industry

                business_list.append(business_details_dict)
                time.sleep(3)

        df = pd.DataFrame.from_dict(business_list)

        df.rename(columns={
            "business-name": "business name",
            "external-links-container": "external link",
            "phone-trigger": "phone number",
            "business-hours": "business hours"
        }, inplace=True)

        df.to_csv(f'./{state_abbrev.lower()}_{city.lower()}.csv', index=False)

driver.quit()