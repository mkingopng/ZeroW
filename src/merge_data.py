import pandas as pd
from datetime import datetime, timedelta

# Load all CSV files
files = [
    './../data/paypa_plane/ZeroW_Sunshine_Coast_Agreements_2024-07-21.csv',
    './../data/paypa_plane/Cairns_Agreements-2024-06-21.csv',
    './../data/paypa_plane/Cairns_Customer_Details_Report_2024-07-21.csv',
    './../data/paypa_plane/ZeroW_Arundel members 2024-07-01.csv',
    './../data/paypa_plane/ZeroW_Brisbane-Agreements-2024-06-21.csv',
    './../data/paypa_plane/ZeroW_Gold_Coast_Agreements-2024-07-01.csv',
    './../data/paypa_plane/ZeroW_SouthSide_Agreements-2024-06-21.csv'
]

# Combine all CSV files into a single DataFrame
combined_df = pd.concat([pd.read_csv(file) for file in files])

# Convert date columns to datetime
combined_df['AGREED_DATE'] = pd.to_datetime(combined_df['AGREED_DATE'], errors='coerce')
combined_df['CANCEL_DATE'] = pd.to_datetime(combined_df['CANCEL_DATE'], errors='coerce')

# Calculate net movement in the last week
one_week_ago = datetime.now() - timedelta(weeks=1)
new_members_last_week = combined_df[(combined_df['AGREED_DATE'] >= one_week_ago)].shape[0]
cancelled_members_last_week = combined_df[(combined_df['CANCEL_DATE'] >= one_week_ago)].shape[0]
net_movement_last_week = new_members_last_week - cancelled_members_last_week

# Save the combined DataFrame for future use
combined_file_path = './../data/paypa_plane/Combined_Members_Data.csv'  # Update this with the desired save path
combined_df.to_csv(combined_file_path, index=False)

print(f"Combined data saved to: {combined_file_path}")
print(f"New members in the last week: {new_members_last_week}")
print(f"Cancelled members in the last week: {cancelled_members_last_week}")
print(f"Net movement in the last week: {net_movement_last_week}")
