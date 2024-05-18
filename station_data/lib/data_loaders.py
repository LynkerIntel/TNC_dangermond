import requests
import pandas as pd


class Dendra:
    def __init__(self, email, password, strategy="local"):
        """
        Initialize the APIClient with authentication details and retrieve the token.

        Parameters:
        auth_url (str): The URL for the authentication endpoint.
        username (str): The username for authentication.
        password (str): The password for authentication.
        """
        self.email = email
        self.password = password
        self.strategy = strategy

        self.authenticate()

    def authenticate(self):
        """
        Authenticate with the API and retrieve the token.

        Returns:
        str: The authentication token if successful, None otherwise.
        """
        url = "https://api.dendra.science/v2/"
        auth_url = url + "authentication"
        headers = {"Content-Type": "application/json"}

        # auth_url = credentials.get("auth_url")

        creds = {
            "email": self.email,
            "strategy": self.strategy,
            "password": self.password,
        }

        # Authenticate and obtain a token
        try:
            auth_response = requests.post(auth_url, json=creds)
            auth_response.raise_for_status()  # Raise an error for bad status codes
            auth_data = auth_response.json()
            token = auth_data.get("accessToken")

            if not token:
                print("Authentication failed: No token received.")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Authentication request failed: {e}")
            return None

        # Use the token to request data from the API
        # headers = {"Authorization": f"Bearer {token}"}
        headers["Authorization"] = token
        self.headers = headers
        print("successfully authenticated")

    def get_data(self):
        """request data"""
        # raise NotImplementedError

        # Use the token to request data from the API
        # headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()  # Raise an error for bad status codes
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Data request failed: {e}")
            return None


def request_HADS(year, siteid, network="HADS"):
    """get HADS met data from Iowa Environmental Mesonet API

    :param (int) year: year in YYYY
    :param (str) siteid: site id
    :param (str) network: one of "HADS", "CA_DCP", "CA_ASOS"
    :returns (pd.DataFrame): df of all available vars for site
    """
    URL = f"https://mesonet.agron.iastate.edu/cgi-bin/request/hads.py?network={network}&sts={year}-01-01T00:00:00Z&ets={year+1}-12-31T23:00:00Z&stations={siteid}&format=csv"

    try:
        response = requests.get(URL, timeout=120)
        if response.status_code == 200:

            headers = response.text.splitlines()[0].split(",")
            data = response.text.splitlines()[1:]

            data = [item.split(",") for item in data]
            df = pd.DataFrame(data, columns=headers)
            df.index = pd.to_datetime(df["utc_valid"])

            # for numeric dtypes cast to float or int, ignore str cols
            cols = df.columns.drop(["station", "utc_valid"])
            df[cols] = df[cols].apply(pd.to_numeric, errors="coerce")

            return df
        else:
            print(
                "Error: Failed to fetch or parse data to DF. Status code:",
                response.status_code,
            )
            return None

    except Exception as e:
        print("Error:", e)
        return None
