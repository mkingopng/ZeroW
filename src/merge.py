import pandas as pd
import functools
import os

# get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# define file paths relative to the script directory
file_paths = {
    "brisbane": os.path.join(script_dir, "brisbane.csv"),
    "southside": os.path.join(script_dir, "southside.csv"),
    "wales": os.path.join(script_dir, "wales.csv"),
    "gc": os.path.join(script_dir, "gold_coast.csv"),
    "cairns": os.path.join(script_dir, "cairns.csv"),
    "sunshine_coast": os.path.join(script_dir, "sunshine_coast.csv")
}

# define locations corresponding to the file paths
locations = {
    "brisbane": "Brisbane",
    "southside": "South Side",
    "wales": "Wales",
    "gc": "Gold Coast",
    "cairns": "Cairns",
    "sunshine_coast": "Sunshine Coast"
}


def read_csv_with_error_handling(file_path, location):
    """
    read a CSV file with error handling and add a 'Location' column
    :param file_path:
    :param location:
    :return: df or error message
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found - {file_path}")
        return pd.DataFrame()  # return an empty df if the file is not found
    try:
        df = pd.read_csv(file_path)
        df['Location'] = location
        return df
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return pd.DataFrame()


# read the CSV files into DataFrames with location information
dfs = {name: read_csv_with_error_handling(path, locations[name]) for name, path in file_paths.items()}


def standardize_column_names(df, new_columns):
    """
    Standardize column names of a DataFrame
    :param df:
    :param new_columns:
    :return:
    """
    if not df.empty and len(df.columns) == len(new_columns):
        df.columns = new_columns
    else:
        print(f"""
        Warning: Column length mismatch. Expected {len(new_columns)} columns 
        but got {len(df.columns)}. Skipping renaming.
        """)
    return df


# Standardize column names using partial
standardize_columns = {
    "wales": ["CUSTOMER_NAME", "EMAIL", "PHONE", "INTERVAL", "AGREED_DATE", "START_DATE", "STATUS", "Location"],
    "gc": ["CUSTOMER_NAME", "EMAIL", "PHONE", "INTERVAL", "AGREED_DATE", "START_DATE", "STATUS", "Location"],
    "cairns": ["AGREED_DATE", "START_DATE", "TYPE", "STATUS", "METHOD", "MERCHANT", "CUSTOMER_NAME", "REFERENCE", "PAYMENT_REQUEST", "NEXT_PAYMENT", "NEXT_PAYMENT_ON", "PRICE", "LAST_PAYMENT_ON", "CANCEL_DATE", "COMMENCEMENT_DATE", "COMPLETION_DATE", "TOTAL_VALUE", "PAID", "REMAINING", "AGREEMENT_ID", "Location"],
    "sunshine_coast": ["AGREED_DATE", "START_DATE", "TYPE", "STATUS", "METHOD", "MERCHANT", "CUSTOMER_NAME", "REFERENCE", "PAYMENT_REQUEST", "NEXT_PAYMENT", "NEXT_PAYMENT_ON", "PRICE", "LAST_PAYMENT_ON", "CANCEL_DATE", "COMMENCEMENT_DATE", "COMPLETION_DATE", "TOTAL_VALUE", "PAID", "REMAINING", "AGREEMENT_ID", "Location"]
}

for key, new_columns in standardize_columns.items():
    dfs[key] = standardize_column_names(dfs[key], new_columns)

# rename 'LAST_PAYMENT' to 'PRICE' in all DataFrames
for df in dfs.values():
    if 'LAST_PAYMENT' in df.columns:
        df.rename(columns={'LAST_PAYMENT': 'PRICE'}, inplace=True)


def convert_date_columns(df, date_columns):
    """
    convert date columns to datetime objects
    :param df:
    :param date_columns:
    :return: df with correct datetime dtype
    """
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df


date_columns = [
    "AGREED_DATE", "START_DATE", "NEXT_PAYMENT_ON", "created",
    "current_period_start"
]

convert_date_columns_partial = functools.partial(
    convert_date_columns,
    date_columns=date_columns
)

dfs = {name: convert_date_columns_partial(df) for name, df in dfs.items()}
merged_df = pd.concat(dfs.values(), ignore_index=True)  # concatenate dfs

# drop unnecessary columns
columns_to_drop = [
    "EMAIL", "PHONE", "CITY", "STATE", "COUNTRY", "POSTCODE", "MOBILE",
    "AGREEMENT_ID"
]
merged_df.drop(
    columns=columns_to_drop,
    errors='ignore',
    inplace=True
)

# merge INTERVAL and REFERENCE into MEMBERSHIP_TYPE
if 'MEMBERSHIP_TYPE' not in merged_df.columns:
    merged_df['MEMBERSHIP_TYPE'] = pd.NA
merged_df['MEMBERSHIP_TYPE'] = merged_df['INTERVAL'].combine_first(merged_df['REFERENCE'].combine_first(merged_df['MEMBERSHIP_TYPE']))

# create a single CUSTOMER_NAME column
if 'FIRST_NAME' in merged_df.columns and 'LAST_NAME' in merged_df.columns:
    merged_df['CUSTOMER_NAME'] = merged_df[['FIRST_NAME', 'LAST_NAME']].fillna('').agg(' '.join, axis=1).str.strip().replace('', pd.NA)
else:
    merged_df['CUSTOMER_NAME'] = merged_df['CUSTOMER_NAME']

# ensure MEMBERSHIP_TYPE exists and initialise it with NaN
if 'MEMBERSHIP_TYPE' not in merged_df.columns:
    merged_df['MEMBERSHIP_TYPE'] = pd.NA

# remove any duplicate columns
merged_df = merged_df.loc[:, ~merged_df.columns.duplicated()]

# count empty cells in the MEMBERSHIP_TYPE column
empty_cells_count = merged_df['MEMBERSHIP_TYPE'].isna().sum()

# mapping of PRICE to MEMBERSHIP_TYPE
price_to_membership = {
    35: "Standard",
    50: "Silver",
    99: "Gold",
    179: "Platinum",
    70: "Standard Plus Nutrition",
    85: "Silver Plus Nutrition",
    134: "Gold Plus Nutrition",
    214: "Platinum Plus Nutrition"
}


def impute_membership_type(row, price_to_membership):
    """
    impute missing MEMBERSHIP_TYPE values based on PRICE
    :param row:
    :param price_to_membership:
    :return: membership_type
    """
    if pd.isna(row['MEMBERSHIP_TYPE']):
        price = row['PRICE'] if 'PRICE' in row else None
        return price_to_membership.get(price, "Other")
    return row['MEMBERSHIP_TYPE']


# impute missing MEMBERSHIP_TYPE
impute_membership_type_partial = functools.partial(
    impute_membership_type,
    price_to_membership=price_to_membership
)

merged_df['MEMBERSHIP_TYPE'] = merged_df.apply(
    impute_membership_type_partial,
    axis=1
)

# normalize MEMBERSHIP_TYPE values
membership_type_mapping = {
    "Gold": ["Gold", "GOLD", "Gold Membership", "ZeroW Gold"],
    "Platinum": ["PLATINUM", "Platinum", "Platinum Membership"],
    "Standard": ["STANDARD membership", "Standard ZeroW Membe", "Standard", "Standard Memberhip", "ZeroW Standard"],
    # Add other mappings as needed
}


def normalize_membership_type(membership_type, mapping):
    """
    clean up MEMBERSHIP_TYPE values
    :param membership_type:
    :param mapping:
    :return: membership_type
    """
    membership_type = membership_type.strip()
    for standard, variants in mapping.items():
        if membership_type in variants:
            return standard
    return membership_type


normalize_membership_type_partial = functools.partial(normalize_membership_type, mapping=membership_type_mapping)
merged_df['MEMBERSHIP_TYPE'] = merged_df['MEMBERSHIP_TYPE'].apply(normalize_membership_type_partial)

# normalize STATUS values
merged_df['STATUS'] = merged_df['STATUS'].str.strip().str.capitalize()

merged_df.drop(columns=['CUSTOMER_NAME', 'INTERVAL', 'MERCHANT', 'REFERENCE'], inplace=True)

# save the concatenated and imputed DataFrame to a new CSV file
merged_df.to_csv("merged_data.csv", index=False)

# display the concatenated DataFrame
print(merged_df.head())


# todo: upgrade to database to store data rather than csv
