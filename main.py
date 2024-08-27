from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time
import re

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
industries = [{"Construction": ["Carpentry", "Plumbing", "Electrical work"]},
{"Manufacturing": ["Welding", "Machine operation", "Assembly line work"]},
{"Transportation and Logistics": ["Truck driving", "Warehouse operations", "Forklift operation"]},
{"Automotive": ["Automotive repair", "Auto maintenance", "Auto Bodywork", "Tire services"]},
{"Maintenance and Repair": ["HVAC", "Appliance repair", "General maintenance"]},
{"Retail": ["Boutiques", "Specialty stores", "Online shops"]},
{"Food and Beverage": ["Restaurants", "Cafes", "Food trucks"]},
{"Personal Services": ["Hair salons", "Barber shops"]}]
states_of_interest = ["California", "New Jersey", "New York", "Texas"]

# https://www.citysearch.com/profile/21109923 #todo use this for website link scraping

def switch(el):
    pos1, pos2 = el.split("/")
    return pos2 + ",%20" + pos1


# old
# business_details_dict = {
#     entry.get_attribute("class"): entry.text
#     for entry in business_details
# }
# business_details_dict["industry"] = industry
def business_details_to_dict(business_details):
    business_details_dict = {}

    for entry in business_details:
        class_name = entry.get_attribute("class")

        if (class_name == "external-links-container"):
            try:
                elem = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.external-links-container a")))
                business_details_dict[class_name] = elem.get_attribute("href")

            except TimeoutException:
                print("Timed out waiting for page to load: No link to website")
                business_details_dict[class_name] = ""

        else:
            business_details_dict[class_name] = entry.text

    return business_details_dict

#######################
# testing
#######################
df = pd.read_excel("google_maps_keywords.xlsx")
df.loc[:, ["Country", "State"]] = df.loc[:, ["Country", "State"]].ffill()

########################
# navigating to the front page of CitySearch
########################

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)
# driver = webdriver.Chrome()
driver.get("https://www.citysearch.com/")

########################
# extracting the links to individual cities
########################
container = driver.find_element(By.CSS_SELECTOR, "div.cities-container")
cities = container.find_elements(By.CSS_SELECTOR, "li:not([class*='state']) > a")
city_links = [city.get_attribute("href") for city in cities]


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
test = []

for state in states: # full state name

    # todo need to edit this part
    #   instead of getting city keys from groups, simply get all the links of the cities within that state from city links
    # old
    # state_cities = grouped_states.get_group(state)["City"]
    # new
    pattern = re.compile(f".*/{us_state_to_abbrev[state]}/.*", re.IGNORECASE)
    where_params = [switch(param) for param in [link.replace("https://www.citysearch.com/", "") for link in city_links if bool(pattern.match(link))]]

    print("------------state----------------")
    print(state)
    print(where_params)


    # todo need to edit this part
    #   instead of doing industry for each state/city, just use the same industry each time
    #   also I don't think I need this part anymore
    # state_industries = grouped_states.get_group(state)["Industry"]
    # state_abbrev = us_state_to_abbrev[state]

    # for city in state_cities:
    for where_param in where_params[0:2]:

        business_list = []

        for industry in [list(industry.keys())[0] for industry in industries]: # todo change this for full implementation
            print(where_param, state, industry)
            url = f"https://www.citysearch.com/results?term={industry.strip().replace(' ', '%20')}&where={where_param}"
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

                # todo don't really think I need this try except block
                try:
                    elem = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.business-details")))
                except TimeoutException:
                    print("Timed out waiting for page to load")

                # not sure if all business have all their contact info so creating a dictionary based on the class name and value
                business_details = driver.find_elements(By.CSS_SELECTOR, 'div.business-details > *')

                # todo do an if else statement...if class not external-links-container then normal else find a tag and get href
                #   you will need to make a function actually, since not all external-links-containers have a tags
                #   so I need to do try except find a and get href

                # old
                # business_details_dict = {
                #     entry.get_attribute("class"): entry.text
                #     for entry in business_details
                # }
                # business_details_dict["industry"] = industry

                # new
                business_details_dict = business_details_to_dict(business_details)
                business_details_dict["industry"] = industry

                # rest
                business_list.append(business_details_dict)
                time.sleep(3)

        df = pd.DataFrame.from_dict(business_list)

        df.rename(columns={
            "business-name": "business name",
            "external-links-container": "external link",
            "phone-trigger": "phone number",
            "business-hours": "business hours"
        }, inplace=True)

        df.to_csv(f'./{where_param.replace(",%20","_").replace("%20", "_")}.csv', index=False)

driver.quit()