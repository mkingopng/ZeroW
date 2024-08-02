"""
pipeline to programmatically update the data files for the dashboard
"""
import requests
import pandas as pd
from io import StringIO
from dotenv import load_dotenv
import os

# load environment variables from .env file
load_dotenv()

# get the API token from the environment
api_token = os.getenv('API_TOKEN')

# define API endpoints
data_urls = {
    'southside': 'https://api.paypaplane.com/data/account1',
    'brisbane': 'https://api.paypaplane.com/data/account2'
}


def fetch_data(url, token):
    """
    fetch data from the API
    :param url:
    :param token:
    :return:
    """
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return pd.read_csv(StringIO(response.text))


if __name__ == '__main__':
    for account, url in data_urls.items():
        data = fetch_data(url, api_token)
        filename = f'{account}.csv'
        data.to_csv(filename, index=False)
        print(f'Saved data to {filename}')


# todo: get this to work for my strength book
# todo: then paypa plane
# todo: then Billy Cart
