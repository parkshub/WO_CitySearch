# https://stackoverflow.com/questions/47316810/unable-to-locate-elements-on-webpage-with-headless-chrome
# "https://stackoverflow.com/questions/25491872/request-geturl-returns-empty-content"
# "https://stackoverflow.com/questions/60416507/python-requests-not-getting-full-page"

# test cases
# https://www.citysearch.com/profile/16919645 link does not work

#todo try headless mode for new york

import re
import time
import asyncio
import pandas as pd
from bs4 import BeautifulSoup
from requests_html import AsyncHTMLSession

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, StaleElementReferenceException

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
# pattern = "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
# states_of_interest = ["California", "New Jersey", "New York", "Texas"]
states_of_interest = ["New Jersey", "New York", "Texas"]
# states_of_interest = ["California"]


def switch(el):
    pos1, pos2 = el.split("/")
    return pos2 + ",%20" + pos1


# def business_details_to_dict(driver, business_details, industry):
def business_details_to_dict(driver, industry):
    business_details_dict = {'industry': industry}

    try:
        print('looking for business details')
        business_details = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.business-details > *")))

        # business_details = driver.find_elements(By.CSS_SELECTOR, 'div.business-details > *')

    except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
        print("Timed out waiting for business details to load")
        return {"business-name": "", "address": "", "external-links-container": "", "phone-trigger": "", "industry": "",
                "additional_info": "", "emails": []}


    for entry in business_details:
        try:
            class_name = entry.get_attribute("class")

            if class_name == "external-links-container":
                try:
                    print('looking for external links')

                    elem = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.external-links-container a")))

                    business_details_dict[class_name] = elem.get_attribute("href")

                except (NoSuchElementException, TimeoutException):
                    print("Timed out waiting for external link: No link to website")
                    business_details_dict[class_name] = ""

            else:
                business_details_dict[class_name] = entry.text

        except StaleElementReferenceException: #https://www.citysearch.com/profile/16919645
            print("Stale reference exception")

    return business_details_dict


async def html_to_string(url):

    session = AsyncHTMLSession()

    # todo try adding a try catch here if it fails again

    try:
        r = await session.get(url, verify=False)
        soup = BeautifulSoup(r.html.raw_html, "html.parser")
        body = soup.find('body')
        return body.get_text(separator=" ").strip()

    except:
        print("Error: Website does not exist")
        return None


# def wait_for_page(driver):
#     try:
#         elem = WebDriverWait(driver, 100).until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, "div.business-details")))
#     except TimeoutException:
#         print("Timed out waiting for page to load")
#     finally:
#         return


async def get_email(url, email_set):
    # print("getting emails")
    # # todo try running with pattern in this function
    # pattern = "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    # body = await html_to_string(url)
    # return re.findall(pattern, body)

    print("getting emails")
    # todo try running with pattern in this function
    pattern = "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    body = await html_to_string(url)

    if body is None:
        return

    emails = re.findall(pattern, body)
    print("these were emails found: ", emails)
    email_set.update(emails)

    # await get_email_from_contact(driver, url, email_set)


async def get_email_from_contact(driver, url, email_set):
    try:
        print('looking for email from contact')
        driver.get(url)

        contact_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "a[href*='contact'], a[href*='Contact'], a[href*='CONTACT']")))

        driver.get(contact_button.get_attribute("href"))
        url_to_scrape = driver.current_url

        await get_email(url_to_scrape, email_set)

    except (NoSuchElementException, TimeoutException, WebDriverException):
        print("No contact page")
        # return []


def get_job_cards_links(driver):
    try:
        print('looking for job card list')

        job_cards = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.list-container > div.card > a")))

        # job_cards = driver.find_elements(By.CSS_SELECTOR, "div.list-container > div.card > a")
        job_cards_links = [job.get_attribute("href") for job in job_cards]

    except (NoSuchElementException, TimeoutException):
        print("Timed out waiting for page to load: Most likely no job listing in this category")
        job_cards_links = []

    return job_cards_links


def save_to_csv(business_list, where_param):
    df = pd.DataFrame.from_dict(business_list)

    df.rename(columns={
        "business-name": "business name",
        "external-links-container": "external link",
        "phone-trigger": "phone number",
        "business-hours": "business hours"
    }, inplace=True)

    df.to_csv(f'./{where_param.replace(",%20", "_").replace("%20", "_")}.csv', index=False)


########################
# iterating over all the states, then cities, then industries and scarping business information
########################
async def main():
    #######################
    # opening and cleaning xlsx file
    #######################
    df = pd.read_excel("google_maps_keywords.xlsx")
    df.loc[:, ["Country", "State"]] = df.loc[:, ["Country", "State"]].ffill()

    ########################
    # grouping dataframe by country then by state
    ########################
    grouped_df = df.groupby("Country")
    grouped_countries = grouped_df.get_group("United States")
    grouped_states = grouped_countries.groupby("State")
    states = grouped_states.groups.keys()

    ########################
    # navigating to the front page of CitySearch
    ########################
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--proxy-server='direct://'")
    chrome_options.add_argument("--proxy-bypass-list=*")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--ignore-certificate-errors')
    driver = webdriver.Chrome(options=chrome_options)
    # using headless makes some sites not work
    # options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")
    # driver = webdriver.Chrome(options=options)
    # driver = webdriver.Chrome()
    # driver.get("https://www.citysearch.com/")

    ########################
    # extracting the links to individual cities
    ########################
    container = driver.find_element(By.CSS_SELECTOR, "div.cities-container")
    cities = container.find_elements(By.CSS_SELECTOR, "li:not([class*='state']) > a")
    city_links = [city.get_attribute("href") for city in cities]

    # todo erase below after testing
    for state in states_of_interest:  # full state name
    # for state in states:  # full state name

        visited = set()

        pattern = re.compile(f".*/{us_state_to_abbrev[state]}/.*", re.IGNORECASE)
        where_params = [switch(param) for param in
                        [link.replace("https://www.citysearch.com/", "") for link in city_links if
                         bool(pattern.match(link))]]

        # todo erase below after testing
        # for where_param in where_params[0:2]:
        for where_param in where_params:

            business_list = []

            # todo uncomment and erase below after testing
            for industry in [list(industry.keys())[0] for industry in industries]:
            # for industry in ["Personal Services"]:
                # industry = "personal services"
                # for industry in industries[-1].keys():
                url = f"https://www.citysearch.com/results?term={industry.strip().replace(' ', '%20')}&where={where_param}"
                driver.get(url)

                print("--------------------state, params, industry--------------------")
                print("-------------------------", url, "----------------------------")
                print(state, where_param, industry)

                job_cards_links = get_job_cards_links(driver)

                if len(job_cards_links) == 0:
                    continue

                # visiting each job link for the current industry and scraping information
                # todo uncomment and erase below after testing
                # for i in range(821, len(job_cards_links)):
                for job_cards_link in job_cards_links:
                    # job_cards_link = "https://www.citysearch.com/profile/16012483"

                    # job_cards_link = job_cards_links[i]

                    if job_cards_link in visited:
                        print('already visited skipping')
                        continue

                    visited.add(job_cards_link)

                    print("------visiting profile: ", job_cards_link, "------")
                    driver.get(job_cards_link)

                    # todo made these changes, change back if broken
                    # wait_for_page(driver)
                    # business_details = driver.find_elements(By.CSS_SELECTOR, 'div.business-details > *')
                    # business_details_dict = business_details_to_dict(driver, business_details, industry)
                    business_details_dict = business_details_to_dict(driver, industry)

                    # todo when time, convert this to a function
                    try:
                        print('looking for additional details')
                        additional_info = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, 'div.panel-container > div.panel-details')))

                        # additional_info = driver.find_element(By.CSS_SELECTOR,
                        #                                       'div.panel-container > div.panel-details')
                        business_details_dict['additional_info'] = additional_info.text

                    except (NoSuchElementException, TimeoutException):
                        print("No additional info container")
                        print("stopped at: ", business_details_dict)
                        business_details_dict['additional_info'] = ''

                    emails = set()
                    # print(business_details_dict)

                    external_link = business_details_dict['external-links-container']
                    # external_link = "https://apis.elocal.com/tracker/track?q=d8b2073e7b1471400329f870bf5e8abfa67ab0a73cffcd3241a007e41001448de03a5fa30d333a4d5cc6b923de4b28c3a1b530fc93d694edc29dc8c687831d1021dfdd3ed166ca79e95a8a8c3132a89cebaf21996ea0219f080d2db5652596e898fb655f28e626e17fdad37b66e7fc7851a00f13141b6c8fbd41d3bf97551174cd79dee9029014f3678520623e6e6adc3f6ec6751faf793b63e1f941c10a8aa4ea18b77a3bc075b98f511ec52418cd612bbbe58db4c5cf12aa50bc9ee9d540c7c21796a177abaa01d8cb5e9e5cd945793ea5d6850405764e02fc26d3c4376cb15e1e019fcb5de8afb6350cfd9fa14fb48d252c09c726f445369d1dbf0c0b74d41270ed385633dc7dae6da02799ae133bf12aad5dd611971b63e836a27a9262ced40f33661c5a79c9385d44d2afd126aa7622247093f77748bb0f05c1c4ecba494f58b3ada7a7652b1af2c08d01cd5bc5bb2ff4bec08aac922e502d4690e35be407d2687902a4a5eec9926da3c3907542b1a1463105d51233fa448e1ec87ca53d217e3bbcb09b82cac1e77f1a6c275d45b09c3d5c078cefed20bb6e4b315ea03d351889fe5bce2f08ca0f381364001a0f5767faf667f0b23612d72c829cdbce5d6bb1892b1e0f26a979bfe147491a52e525bb94196d52acfdad350aa2bdd3f51f2af0e41ad9e7514487e8d67f22e96ca03ab06b057c16e3cc7c1cdc4fdfc8fe4264747105fc6d674c638d232dca0c1f30645cc7b7e9aaac7dbd83e9cedb8795a9ed1a5cf2dab709c9bba23be7d6c255d63d70967fc691a266b418a0a2ab95238081e165b13138aea38662ed197c76e5a79fd14ee7323b72186e0b90bdecdb052ad02b73143cd5c22b28be347b64890489503b60514648a4f5972005f7d3332c5328a41b81a3a41251cf1159b8023e13d6bd315ba1aeb83333031eb1bdea64194038c9ad190cc97b3da0ad7e55872f3b4bb15bc740ecce005afdc932e7d2d5a8c3"
                    if external_link != '':
                        await get_email(external_link, emails)
                        await get_email_from_contact(driver, external_link, emails)
                        print("emails have been updated these are emails", emails)

                    business_details_dict['emails'] = str(list(emails))

                    print(business_details_dict)
                    business_list.append(business_details_dict)
                    # time.sleep(3)

            save_to_csv(business_list, where_param)

    driver.quit()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()