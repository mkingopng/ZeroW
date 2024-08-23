import pandas as pd
from fuzzywuzzy import fuzz
import re


# Function to remove '#' and numbers from strings
def clean_full_name(name):
    """

	:param name:
	:return:
	"""
    return re.sub(r'[#\d]', '', name).strip()

# Load membership data
members_df = pd.read_csv(
    'apl_untested_2024_files/members-list.csv')
members_df = members_df[['first_name', 'last_name', 'email']]
members_df['full_name'] = members_df['first_name'] + ' ' + members_df['last_name']
members_df['full_name'] = members_df['full_name'].str.lower()

# Load and filter powerlifting data
df = pd.read_csv('./../data/open-powerlifting-australia.csv', low_memory=False)
filtered_df = df[df['Date'] >= '2023-09-01']
filtered_df = filtered_df[filtered_df['Federation'] == 'AusPL'].drop_duplicates('Name')
filtered_df['full_name'] = filtered_df['Name'].str.lower()

# Separate male and female lifters and apply Dots score filters
df_male = filtered_df[filtered_df['Sex'] == 'M']
df_female = filtered_df[filtered_df['Sex'] == 'F']

df_male_filtered = df_male[df_male['Dots'] >= 400]
df_female_filtered = df_female[df_female['Dots'] >= 340]

# Merge membership data with filtered male lifters
df_male_filtered = pd.merge(members_df, df_male_filtered, on='full_name', how='right')
df_female_filtered = pd.merge(members_df, df_female_filtered, on='full_name', how='right')

# Count and print the number of missing email addresses
missing = df_male_filtered['email'].isna().sum()
print(f'The number of missing email addresses is {missing}')

missing = df_female_filtered['email'].isna().sum()
print(f'The number of missing email addresses is {missing}')


# Save filtered data to Excel
with pd.ExcelWriter('christmas_cup.xlsx', engine='xlsxwriter') as writer:
    filtered_df.to_excel(writer, sheet_name='all_lifters', index=False)
    df_male_filtered.to_excel(writer, sheet_name='male', index=False)
    df_female_filtered.to_excel(writer, sheet_name='female', index=False)
