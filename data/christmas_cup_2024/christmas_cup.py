#%%
import pandas as pd
#%%
membership_df = pd.read_csv(
    'apl_untested_2024_files/members-list.csv')
membership_df
#%%
df = pd.read_csv('./../data/open-powerlifting-australia.csv', low_memory=False)
df
#%%
filtered_df = df[df['Date'] >= '2023-09-01']
filtered_df.head()
#%%
filtered_df = filtered_df[filtered_df['Federation'] == 'AusPL'].drop_duplicates('Name')
filtered_df
#%%
df_male = filtered_df[filtered_df['Sex'] == 'M']
df_female = filtered_df[filtered_df['Sex'] == 'F']
#%%
df_male_filtered = df_male[df_male['Dots'] >= 400]
df_female_filtered = df_female[df_female['Dots'] >= 340]
#%%
df_female_filtered
#%%
df_male_filtered
#%%
# Create a new Excel file and write the DataFrames to separate sheets
with pd.ExcelWriter('christmas_cup.xlsx', engine='xlsxwriter') as writer:
    filtered_df.to_excel(writer, sheet_name='all_lifters', index=False)
    df_male_filtered.to_excel(writer, sheet_name='male', index=False)
    df_female_filtered.to_excel(writer, sheet_name='female', index=False)