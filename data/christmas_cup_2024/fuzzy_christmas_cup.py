import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re


# Function to remove '#' and numbers from strings
def clean_full_name(name):
	if isinstance(name, str):
		cleaned_name = re.sub(r'[#\d]', '', name).strip()
		return cleaned_name if cleaned_name else None
	else:
		return None


# Function to apply fuzzy matching and merge data
def fuzzy_merge(df_1, df_2, key1, key2, threshold=80, limit=2):
	"""
	Fuzzy merge two DataFrames based on the similarity of values in the specified columns.

	:param df_1: First DataFrame
	:param df_2: Second DataFrame
	:param key1: Column name in the first DataFrame
	:param key2: Column name in the second DataFrame
	:param threshold: Minimum similarity score to consider a match
	:param limit: Maximum number of closest matches to consider
	:return: Merged DataFrame with fuzzy matched values
	"""
	# Filter out rows where key1 is None (i.e., where clean_full_name returned None)
	df_1 = df_1[df_1[key1].notna()]

	s = df_2[key2].tolist()

	matches = df_1[key1].apply(
		lambda x: process.extractOne(x, s, scorer=fuzz.token_sort_ratio))

	df_1['best_match'] = matches.apply(
		lambda x: x[0] if x[1] >= threshold else None)
	df_1['match_score'] = matches.apply(
		lambda x: x[1] if x[1] >= threshold else None)

	return pd.merge(df_1, df_2, left_on='best_match', right_on=key2,
					how='left').drop(columns=['best_match', 'match_score'])


# Load membership data
members_df = pd.read_csv(
	'apl_untested_2024_files/members-list.csv')
members_df = members_df[['first_name', 'last_name', 'email']]
members_df['full_name'] = members_df['first_name'] + ' ' + members_df[
	'last_name']
members_df['full_name'] = members_df['full_name'].str.lower().apply(
	clean_full_name)

# Load and filter powerlifting data
df = pd.read_csv('./../data/open-powerlifting-australia.csv', low_memory=False)
filtered_df = df[df['Date'] >= '2023-09-01']
filtered_df = filtered_df[
	filtered_df['Federation'] == 'AusPL'].drop_duplicates('Name')
filtered_df['full_name'] = filtered_df['Name'].str.lower().apply(
	clean_full_name)

# Separate male and female lifters and apply Dots score filters
df_male = filtered_df[filtered_df['Sex'] == 'M']
df_female = filtered_df[filtered_df['Sex'] == 'F']

df_male_filtered = df_male[df_male['Dots'] >= 400]
df_female_filtered = df_female[df_female['Dots'] >= 340]

# Fuzzy merge membership data with filtered male lifters
df_male_filtered = fuzzy_merge(members_df, df_male_filtered, 'full_name',
							   'full_name', threshold=80)
df_female_filtered = fuzzy_merge(members_df, df_female_filtered, 'full_name',
								 'full_name', threshold=80)

# Count and print the number of missing email addresses
missing_male = df_male_filtered['email'].isna().sum()
print(
	f'The number of missing email addresses in the male list is {missing_male}')

missing_female = df_female_filtered['email'].isna().sum()
print(
	f'The number of missing email addresses in the female list is {missing_female}')

# Save filtered data to Excel
with pd.ExcelWriter('fuzzy_christmas_cup.xlsx', engine='xlsxwriter') as writer:
	filtered_df.to_excel(writer, sheet_name='all_lifters', index=False)
	df_male_filtered.to_excel(writer, sheet_name='male', index=False)
	df_female_filtered.to_excel(writer, sheet_name='female', index=False)
