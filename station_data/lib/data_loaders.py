import requests
import pandas as pd


def request_HADS(year, siteid, network="HADS"):
    """get HADS met data from Iowa Environmental Mesonet API

    :param (int) year: year in YYYY
    :param (str) siteid: site id
    :param (str) network: one of "HADS", "CA_DCP", "CA_ASOS" 
    :returns (pd.DataFrame): df of all available vars for site
    """
    URL = f"https://mesonet.agron.iastate.edu/cgi-bin/request/hads.py?network={network}&sts={year}-01-01T00:00:00Z&ets={year+1}-12-31T23:00:00Z&stations={siteid}&format=csv"
    
    try:
        response = requests.get(URL)
        if response.status_code == 200:            

            headers = response.text.splitlines()[0].split(",")
            data = response.text.splitlines()[1:]

            data = [item.split(',') for item in data]
            df = pd.DataFrame(data, columns=headers)
            df.index = pd.to_datetime(df['utc_valid'])

            # for numeric dtypes cast to float or int, ignore str cols
            cols = df.columns.drop(['station', 'utc_valid'])
            df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
            
            return df
        else:
            print("Error: Failed to fetch or parse data to DF. Status code:", response.status_code)
            return None
    except Exception as e:
        print("Error:", e)
        return None
    

def request_dendra(api_url, credentials):
    """
    Request data from an API with proper authentication handling.

    Parameters:
    api_url (str): The URL of the API endpoint.
    credentials (dict): A dictionary containing authentication credentials.

    Returns:
    dict: The JSON response from the API if the request is successful.
    None: If the request fails or authentication is unsuccessful.
    """
    url = 'https://api.dendra.science/v2/'  
    headers = {"Content-Type":"application/json"}


    auth_url = credentials.get('auth_url')
    auth_payload = {
        'username': credentials.get('username'),
        'password': credentials.get('password')
    }

    # Authenticate and obtain a token
    try:
        auth_response = requests.post(auth_url, data=auth_payload)
        auth_response.raise_for_status()  # Raise an error for bad status codes
        auth_data = auth_response.json()
        token = auth_data.get('token')

        if not token:
            print("Authentication failed: No token received.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Authentication request failed: {e}")
        return None

    # Use the token to request data from the API
    headers = {'Authorization': f'Bearer {token}'}
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Data request failed: {e}")
        return None