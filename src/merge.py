import pandas as pd
import functools
import os

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define file paths relative to the script directory
file_paths = {
    "brisbane": os.path.join(script_dir, "brisbane.csv"),
    "southside": os.path.join(script_dir, "southside.csv"),
    "wales": os.path.join(script_dir, "wales.csv"),
    "gc": os.path.join(script_dir, "gold_coast.csv"),
    "cairns": os.path.join(script_dir, "cairns.csv"),
    "sunshine_coast": os.path.join(script_dir, "sunshine_coast.csv")
}

# Define locations corresponding to the file paths
locations = {
    "brisbane": "Brisbane",
    "southside": "South Side",
    "wales": "Wales",
    "gc": "Gold Coast",
    "cairns": "Cairns",
    "sunshine_coast": "Sunshine Coast"
}

# Function to read CSV files with error handling and add 'Location' column
def read_csv_with_error_handling(file_path, location):
    if not os.path.exists(file_path):
        print(f"Error: File not found - {file_path}")
        return pd.DataFrame()  # Return an empty DataFrame if the file is not found
    try:
        df = pd.read_csv(file_path)
        df['Location'] = location
        return df
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return pd.DataFrame()

# Read the CSV files into DataFrames with location information
dfs = {name: read_csv_with_error_handling(path, locations[name]) for name, path in file_paths.items()}

# Function to standardize column names
def standardize_column_names(df, new_columns):
    if not df.empty and len(df.columns) == len(new_columns):
        df.columns = new_columns
    else:
        print(f"Warning: Column length mismatch. Expected {len(new_columns)} columns but got {len(df.columns)}. Skipping renaming.")
    return df

# Standardize column names using partial
standardize_columns = {
    "wales": ["CUSTOMER", "EMAIL", "PHONE", "INTERVAL", "AGREED_DATE", "START_DATE", "STATUS", "Location"],
    "gc": ["CUSTOMER", "EMAIL", "PHONE", "INTERVAL", "AGREED_DATE", "START_DATE", "STATUS", "Location"],
    "cairns": ["EMAIL", "FIRST_NAME", "LAST_NAME", "CITY", "STATE", "COUNTRY", "POSTCODE", "PHONE", "MOBILE", "REFERENCE", "STATUS", "Location"],
    "sunshine_coast": ["EMAIL", "FIRST_NAME", "LAST_NAME", "CITY", "STATE", "COUNTRY", "POSTCODE", "PHONE", "MOBILE", "REFERENCE", "STATUS", "Location"]
}

# Debugging: Print initial columns
for key, df in dfs.items():
    print(f"Initial columns for {key}: {df.columns.tolist()}")

for key, new_columns in standardize_columns.items():
    dfs[key] = standardize_column_names(dfs[key], new_columns)

# Debugging: Print columns after standardization
for key, df in dfs.items():
    print(f"Columns after standardization for {key}: {df.columns.tolist()}")

# Rename 'LAST_PAYMENT' to 'PRICE' in all DataFrames
for df in dfs.values():
    if 'LAST_PAYMENT' in df.columns:
        df.rename(columns={'LAST_PAYMENT': 'PRICE'}, inplace=True)

# Function to convert date columns to datetime objects
def convert_date_columns(df, date_columns):
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

# Convert date columns using partial
date_columns = ["AGREED_DATE", "START_DATE", "NEXT_PAYMENT_ON", "created", "current_period_start"]
convert_date_columns_partial = functools.partial(convert_date_columns, date_columns=date_columns)
dfs = {name: convert_date_columns_partial(df) for name, df in dfs.items()}

# Concatenate DataFrames
merged_df = pd.concat(dfs.values(), ignore_index=True)

# Remove any duplicate columns
merged_df = merged_df.loc[:, ~merged_df.columns.duplicated()]

# Debugging: Print merged_df columns
print(f"Merged DataFrame columns: {merged_df.columns.tolist()}")

# Ensure MEMBERSHIP_TYPE exists and initialize it with NaN
if 'MEMBERSHIP_TYPE' not in merged_df.columns:
    merged_df['MEMBERSHIP_TYPE'] = pd.NA

# Count empty cells in the MEMBERSHIP_TYPE column
empty_cells_count = merged_df['MEMBERSHIP_TYPE'].isna().sum()
print(f"Number of empty cells in MEMBERSHIP_TYPE: {empty_cells_count}")

# Debugging: Print the first few rows of merged_df before imputation
print("First few rows of merged_df before imputation:")
print(merged_df.head())

# Mapping of PRICE to MEMBERSHIP_TYPE
price_to_membership = {
    35: "Standard",
    50: "Silver",
    99: "GOLD",
    179: "PLATINUM",
    70: "Standard Plus Nutrition",
    85: "Silver Plus Nutrition",
    134: "Gold Plus Nutrition",
    214: "Platinum Plus Nutrition"
}

# Impute missing MEMBERSHIP_TYPE values using partial
def impute_membership_type(row, price_to_membership):
    # Debugging: Print row to check for MEMBERSHIP_TYPE
    print(f"Processing row: {row}")
    if pd.isna(row['MEMBERSHIP_TYPE']):
        price = row['PRICE'] if 'PRICE' in row else None
        return price_to_membership.get(price, "Other")
    return row['MEMBERSHIP_TYPE']

impute_membership_type_partial = functools.partial(impute_membership_type, price_to_membership=price_to_membership)
merged_df['MEMBERSHIP_TYPE'] = merged_df.apply(impute_membership_type_partial, axis=1)

# Save the concatenated and imputed DataFrame to a new CSV file
merged_df.to_csv("merged_data.csv", index=False)

# Display the concatenated DataFrame
print(merged_df.head())

# fix_me, something wrong with cairns and sunshine coast data
