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
from selenium.common.exceptions import TimeoutException, NoSuchElementException


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
pattern = "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
# states_of_interest = ["California", "New Jersey", "New York", "Texas"]
# states_of_interest = ["California"]


def switch(el):
    pos1, pos2 = el.split("/")
    return pos2 + ",%20" + pos1


def business_details_to_dict(driver, business_details, industry):
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

    business_details_dict["industry"] = industry

    return business_details_dict


async def html_to_string(url):
    # todo erase
    # "https://stackoverflow.com/questions/25491872/request-geturl-returns-empty-content"
    # "https://stackoverflow.com/questions/60416507/python-requests-not-getting-full-page"

    session = AsyncHTMLSession()
    r = await session.get(url)
    soup = BeautifulSoup(r.html.raw_html, "html.parser")
    body = soup.find('body')
    return body.get_text(separator=" ").strip()


def wait_for_page(driver):
    try:
        elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.business-details")))
    except TimeoutException:
        print("Timed out waiting for page to load")


async def get_email(url):
    print("--------------getting emails--------------")
    body = await html_to_string(url)
    return re.findall(pattern, body)


async def get_email_from_contact(driver, external_link):
    try:
        driver.get(external_link)
        print("this is current url: ", driver.current_url)
        contact_button = driver.find_element(
            By.CSS_SELECTOR,
            "a[href*='contact'], a[href*='Contact'], a[href*='CONTACT']")

        driver.get(contact_button.get_attribute("href"))
        url_to_scrape = driver.current_url
        return await get_email(url_to_scrape)

    except NoSuchElementException:
        print("No contact page")
        return []


def get_job_cards_links(driver):
    try:
        elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.list-container > div.card > a")))

        job_cards = driver.find_elements(By.CSS_SELECTOR, "div.list-container > div.card > a")
        job_cards_links = [job.get_attribute("href") for job in job_cards]

    except TimeoutException:
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
    # using headless makes some sites not work
    # options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")
    # driver = webdriver.Chrome(options=options)
    driver = webdriver.Chrome()
    driver.get("https://www.citysearch.com/")

    ########################
    # extracting the links to individual cities
    ########################
    container = driver.find_element(By.CSS_SELECTOR, "div.cities-container")
    cities = container.find_elements(By.CSS_SELECTOR, "li:not([class*='state']) > a")
    city_links = [city.get_attribute("href") for city in cities]

    # todo erase below after testing
    # for state in states_of_interest:  # full state name
    for state in states:  # full state name
        pattern = re.compile(f".*/{us_state_to_abbrev[state]}/.*", re.IGNORECASE)
        where_params = [switch(param) for param in
                        [link.replace("https://www.citysearch.com/", "") for link in city_links if
                         bool(pattern.match(link))]]

        # todo erase below after testing
        # for where_param in where_params[0:2]:
        for where_param in where_params:
            business_list = []

            # todo uncomment and erase below after testing
            # for industry in [list(industry.keys())[0] for industry in industries]:
            for industry in industries[-1].keys():
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
                # for i in range(5):
                for i in range(len(job_cards_links)):
                    print(job_cards_links[i])
                    driver.get(job_cards_links[i])

                    wait_for_page(driver)
                    business_details = driver.find_elements(By.CSS_SELECTOR, 'div.business-details > *')
                    business_details_dict = business_details_to_dict(driver, business_details, industry)

                    additional_info = driver.find_element(By.CSS_SELECTOR, 'div.panel-container > div.panel-details')
                    business_details_dict['additional_info'] = additional_info.text

                    emails = set()

                    external_link = business_details_dict['external-links-container']

                    if external_link != '':
                        emails.update(await get_email(external_link))
                        emails.update(await get_email_from_contact(driver, external_link))
                        print("emails have been updated these are emails", emails)

                    business_details_dict['emails'] = str(list(emails))

                    print(business_details_dict)
                    business_list.append(business_details_dict)
                    time.sleep(3)

            save_to_csv(business_list, where_param)

    driver.quit()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()