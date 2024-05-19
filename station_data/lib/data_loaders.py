import requests
import pandas as pd


class Dendra:
    def __init__(self, email, password, strategy="local"):
        """
        Initialize the API Client with authentication details and retrieve the token.

        Parameters:
        email (str): dendra user email
        password (str): The dendra password for authentication.
        strategy (str): leaving as default for now
        """
        self.email = email
        self.password = password
        self.strategy = strategy
        self.url = "https://api.dendra.science/v2/"
        self.authenticate()

    def authenticate(self):
        """
        Authenticate with the API and retrieve the token.

        Returns:
        str: The authentication token if successful, None otherwise.
        """
        auth_url = self.url + "authentication"
        headers = {"Content-Type": "application/json"}

        creds = {
            "email": self.email,
            "strategy": self.strategy,
            "password": self.password,
        }

        # Authenticate and obtain a token
        try:
            auth_response = requests.post(auth_url, json=creds, timeout=60)
            auth_response.raise_for_status()  # Raise an error for bad status codes
            auth_data = auth_response.json()
            token = auth_data.get("accessToken")

            if not token:
                print("Authentication failed: No token received.")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Authentication request failed: {e}")
            return None

        headers["Authorization"] = token
        self.headers = headers
        print("successfully authenticated")

    def _get_datastreams(self, datastream_name, station_id):
        """request datastream id"""
        datastreams_url = self.url + "datastreams"

        params = {
            "station_id": station_id,
        }

        try:
            response = requests.get(
                datastreams_url, headers=self.headers, params=params, timeout=60
            )
            response.raise_for_status()  # Raise an error for bad status codes
            datastream_id = [
                ds["_id"]
                for ds in response.json()["data"]
                if datastream_name in ds["name"]
            ][0]
            return datastream_id

        except requests.exceptions.RequestException as e:
            print(f"Datastream request failed: {e}")
            return None

    def get_datapoints(self, start, end, datastream_name, station_id):
        """request from datapoints endpoint

        TODO: figure out why timestap is duplicated in request data.

        Parameters:

        start (datetime): start date
        end (datetime); end date
        """
        datapoints_url = self.url + "datapoints"
        datastream_id = self._get_datastreams(datastream_name, station_id)

        # Get datapoints from datastream
        params = {
            "datastream_id": datastream_id,
            "time[$gte]": str(start).replace(" ", "T").replace(".000000000", "")
            + ".000Z",
            "time[$lt]": str(end).replace(" ", "T").replace(".000000000", "") + ".000Z",
            "$sort[time]": "1",
            "$limit": "2000",
            "time_local": False,
        }

        try:
            response = requests.get(
                datapoints_url, headers=self.headers, params=params, timeout=60
            )
            response.raise_for_status()  # Raise an error for bad status codes

            response_data = response.json()
            data = [(i["t"], i["v"]) for i in response_data["data"]]
            df = pd.DataFrame(data, columns=["datetime", "values"])
            df.index = pd.to_datetime(df["datetime"])
            df.drop(columns="datetime", inplace=True)
            return df

        except requests.exceptions.RequestException as e:
            print(f"Datapoints request failed: {e}")
            return None


def request_HADS(year, siteid, network="HADS"):
    """get HADS met data from Iowa Environmental Mesonet API
    TODO: make robust with proper request methods

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
