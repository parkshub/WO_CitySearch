import os
import re
import functools as ft
import pandas as pd
import numpy as np


#################################
#------getting CA zipcodes------#

ca_zip_df = pd.read_csv('assets/ca_zip-codes-data.csv', header=0)
ca_zip_df.sort_values(by='zip', inplace=True)
ca_zip_df.rename(columns={'zip': 'zip_code'}, inplace=True)
ca_zip_df = ca_zip_df.astype({'zip_code': str})

ca_zip_df2 = pd.read_excel('assets/california-zip-codes.xlsx', header=None)
ca_zip_df2.columns = ['zip_code', 'city', 'county']
ca_zip_df2 = ca_zip_df2.astype({'zip_code': str})

#####################################
#------combining state results------#

path = './results'
os.listdir(path)
csv_list = [file for file in os.listdir(path) if file.endswith("_ca.csv")]
state_dfs = [pd.read_csv(path + '/' + csv_name) for csv_name in csv_list if os.stat(path + '/' + csv_name).st_size > 2]
state_df = pd.concat(state_dfs) #1329
state_df.reset_index(drop=True ,inplace=True)
state_df.drop('teaser', inplace=True, axis=1)
state_df.dropna(subset=['business name', 'phone number'], how='all', inplace=True)


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


#################################
#------merging by zip code------#

merge_list = [state_df, ca_zip_df, ca_zip_df2]
df_final = ft.reduce(lambda left, right: pd.merge(left, right, on='zip_code'), merge_list)


###################################
#------cleaning up dataframe------#

for idx, row in df_final.iterrows():
    if (pd.isna(row['city_x'])):
        df_final.loc[idx, 'city'] = row['city_y']
        df_final.loc[idx, 'county'] = row['county_y'] + 'county'

    if (pd.isna(row['city_y'])):
        df_final.loc[idx, 'city'] = row['city_x']
        df_final.loc[idx, 'county'] = row['county_x']
    else:
        df_final.loc[idx, 'city'] = row['city_x']
        df_final.loc[idx, 'county'] = row['county_x']

np.where(df_final['city'].isna()) # checking if there are still na values

df_final.columns.str.endswith('_x')
df_final = df_final.loc[:,~df_final.columns.str.endswith('_x')]
df_final = df_final.loc[:,~df_final.columns.str.endswith('_y')]

df_final['county'] = df_final['county'].str.replace(' County', '')

df_final['city'].unique()


########################################
#------getting population by_city_results------#

df_by_pop = ca_zip_df.groupby('city').agg({'population': 'sum'})
df_by_pop.sort_values(by='population', inplace=True, ascending=False)

df_by_pop = df_by_pop[df_by_pop['population'] >= 100000]
major_city_list = list(df_by_pop['population'].index)


#################################
#------filter major cities------#

# Testing numbers for city group
# df_final_filtered = df_final[df_final['city'].isin(major_city_list)]
# city_group = df_final_filtered.groupby('city')


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

# Apply the highlighting function to the DataFrame
df_final.sort_values(by='address', inplace=True)
styled_df = df_final.style.apply(highlight_high_score, axis=1)
styled_df.to_excel('ca_final.xlsx', engine='openpyxl', index=False)