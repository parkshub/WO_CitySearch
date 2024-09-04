import os
import re
import functools as ft
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By


state_dict = {'California': 'ca', 'New Jersey': 'nj', 'New York': 'ny', 'Texas': 'tx'}

for state in state_dict.keys():
    #################################
    #------getting zipcodes------#
    driver = webdriver.Chrome()
    driver.get(f'https://www.zipcodestogo.com/{state}/')

    table_rows = driver.find_elements(By.CSS_SELECTOR, 'table.inner_table > tbody > tr')

    zip_list = []
    temp_key = {0: 'zip_code', 1: 'city', 2: 'county'}

    for row in table_rows:
        cols = row.find_elements(By.CSS_SELECTOR, 'td')
        zip_dict = {'zip_code':'', 'city':'', 'county':''}

        for idx, col in enumerate(cols[0:3]):
            zip_dict[temp_key[idx]] = col.text

        zip_list.append(zip_dict)

    ny_zip_df = pd.DataFrame.from_dict(zip_list)
    ny_zip_df = ny_zip_df.iloc[2:, :]
    ny_zip_df = ny_zip_df.astype({'zip_code': str})
    ny_zip_df.dtypes

    driver.close()


    #####################################
    #------combining state results------#
    # path = './results'
    path = './' #path to where .csv file separated by city are
    os.listdir(path)
    csv_list = [file for file in os.listdir(path) if file.endswith(f"_{state_dict[state]}.csv")]
    state_dfs = [pd.read_csv(path + '/' + csv_name) for csv_name in csv_list if os.stat(path + '/' + csv_name).st_size > 2]
    state_df = pd.concat(state_dfs) #1329
    state_df.reset_index(drop=True ,inplace=True)
    state_df = state_df[['industry', 'business name', 'address', 'external link', 'phone number', 'additional_info', 'emails', 'business hours']]
    state_df.dropna(subset=['business name', 'phone number'], how='all', inplace=True)
    state_df.dropna(subset=['address'], inplace=True)


    #################################
    #------extracting zip code------#
    zip_code_pattern = re.compile("\d{5}(-\d{4})?$")

    state_df['zip_code'] = state_df.apply(
        lambda row: str(re.search(zip_code_pattern, row['address']).group(0))
        if not pd.isna(row['address'])
        else row['address'], axis=1
    )

    state_df[~state_df['zip_code'].apply(
        lambda x: str(x).startswith('9') and len(str(x)) == 5
    )] # checking to see proper zip codes

    state_df = state_df.astype({'zip_code': str})
    state_df.dtypes
    state_df['zip_code'].isna().sum() # checking to see all zipcodes are accounted for


    #################################
    #------merging by zip code------#
    merge_list = [state_df, ny_zip_df]
    df_final = ft.reduce(lambda left, right: pd.merge(left, right, on='zip_code'), merge_list)


    ################################
    #------finding duplicates------#
    # finding duplicates
    df_final['address'].value_counts()
    rows = df_final.loc[df_final.duplicated(subset=['address'], keep=False)]
    # index of duplicates
    duplicates_mask = df_final['address'].duplicated(keep=False)
    # Get indexes of non-unique values
    non_unique_indexes = df_final[duplicates_mask].index.tolist()
    repeats = df_final.iloc[non_unique_indexes]

    def highlight_high_score(row):
        return ['background-color: yellow' if row.name in non_unique_indexes else '' for _ in row]

    # Highlighting non-unique addresses
    df_final.sort_values(by='address', inplace=True)
    styled_df = df_final.style.apply(highlight_high_score, axis=1)
    styled_df.to_excel(f'{state_dict[state]}_final.xlsx', engine='openpyxl', index=False)