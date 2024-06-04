import requests
import pandas as pd


class Dendra:
    def __init__(self, email, password, strategy="local"):
        """
        Initialize the API Client with authentication details and retrieve the token.

        This class is based off of the "Dendra API query" module, the UC Berekely
        python wrapper. This is preferable to use due to newer package captibility
        and some bugfixes. Not all functionality has been carried over due to time
        constraints.

        Parameters:
        email (str): dendra user email
        password (str): The dendra password for authentication.
        strategy (str): leaving as default for now
        """
        self.email = email
        self.password = password
        self.strategy = strategy
        self.url = "https://api.dendra.science/v2/"
        self._authenticate()

    def _authenticate(self):
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
            auth_response = requests.post(auth_url, json=creds, timeout=120)
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

    def get_datastream_id(self, datastream_name, station_id=""):
        """request datastream id"""
        datastreams_url = self.url + "datastreams"

        params = {
            "station_id": station_id,
        }

        try:
            response = requests.get(
                datastreams_url, headers=self.headers, params=params, timeout=120
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

    def get_meta_station_by_id(self, station_id, query_add=""):
        """
        Request station metadata by station id
        """
        stations_url = self.url + "stations"

        if type(station_id) is not str:
            return "INVALID station_id (bad type)"
        if len(station_id) != 24:
            return "INVALID station_id (wrong length)"
        query = {"_id": station_id}
        if query_add != "":
            query.update(query_add)

        try:
            r = requests.get(
                stations_url, headers=self.headers, params=query, timeout=120
            )
            r.raise_for_status()  # Raise an error for bad status codes
            rjson = r.json()
            return rjson["data"][0]

        except requests.exceptions.RequestException as e:
            print(f"Datapoints request failed: {e}")
            return None

    def get_meta_datastream_by_id(self, datastream_id, query_add=""):
        """
        Request metadata with *datastream* id
        """
        datastreams_url = self.url + "datastreams"

        if type(datastream_id) is not str:
            return "INVALID DATASTREAM_ID (bad type)"
        if len(datastream_id) != 24:
            return "INVALID DATASTREAM_ID (wrong length)"
        query = {"_id": datastream_id}
        if query_add != "":
            query.update(query_add)

        try:
            r = requests.get(
                datastreams_url, headers=self.headers, params=query, timeout=120
            )
            r.raise_for_status()  # Raise an error for bad status codes
            rjson = r.json()
            return rjson["data"][0]

        except requests.exceptions.RequestException as e:
            print(f"Datapoints request failed: {e}")
            return None

    def list_datastreams_by_measurement(
        self, measurement="", aggregate="", station_id=[], orgslug="", query_add=""
    ):
        # parameters: measurements and aggregates are spelled out and capitalized
        # measurement: see dendra.science for list. No spaces. (AirTemperature, VolumetricWaterContent, RainfallCumulative, etc.
        # aggregate: Minimum, Average, Maximum, Cumulative
        # station_id: MongoID
        # orgslug: shortname (currently erczo, ucnrs, chi, ucanr, tnc, pepperwood)
        # query_add: JSON query please see documentation https://dendrascience.github.io/dendra-json-schema/
        datastreams_url = self.url + "datastreams"

        query = {"$sort[name]": 1, "$select[name]": 1, "$limit": 2016}
        if measurement != "":
            query.update(
                {"terms_info.class_tags[$all][0]": "dq_Measurement_" + measurement}
            )
        if aggregate != "":
            query.update(
                {"terms_info.class_tags[$all][2]": "ds_Aggregate_" + aggregate}
            )
        if station_id != []:
            query.update({"station_id": station_id})
        if orgslug != "":
            orgid = self.get_organization_id(orgslug)
            query.update({"organization_id": orgid})

        if query_add != "":
            query.update(query_add)

        try:
            r = requests.get(
                datastreams_url, headers=self.headers, params=query, timeout=120
            )
            r.raise_for_status()  # Raise an error for bad status codes
            rjson = r.json()
            return rjson["data"]

        except requests.exceptions.RequestException as e:
            print(f"Datastreams request failed: {e}")
            return None

    def get_organization_id(self, orgslug):
        """
        # orgslug: the short name for an organization. can be found in the url on the dendra.science site.
        # examples: 'erczo','ucnrs','chi','ucanr','tnc','pepperwood', 'cdfw' (may change in future)
        """
        query = {"$select[_id]": 1, "slug": orgslug}
        r = requests.get(self.url + "organizations", headers=self.headers, params=query)
        assert r.status_code == 200
        rjson = r.json()
        return rjson["data"][0]["_id"]

    def get_datapoints(
        self,
        datastream_id,
        begins_at,
        ends_before,
        time_type="local",
        name="default",
    ):
        """Refactored from Berekely code

        GET Datapoints returns actual datavalues for only one datastream.
        Returns a Pandas DataFrame columns. Both local and UTC time will be returned.
        Parameters: ends_before is optional. Defaults to now. time_type is optional default 'local', either 'utc' or 'local'
        if you choose 'utc', timestamps must have 'Z' at the end to indicate UTC time.
        """
        datapoints_url = self.url + "datapoints"

        if type(datastream_id) is not str:
            return "INVALID DATASTREAM_ID (bad type)"
        if len(datastream_id) != 24:
            return "INVALID DATASTREAM_ID (wrong length)"
        if time_type == "utc" and ends_before[-1] != "Z":
            ends_before += "Z"

        query = {
            "datastream_id": datastream_id,
            "time[$gte]": begins_at,
            "time[$lt]": ends_before,
            "$sort[time]": "1",
            "$limit": "2016",  # DR: limit is 2000 in API docs...
        }
        if time_type == "utc":
            time_col = "t"
        else:
            query.update({"time_local": "true"})
            time_col = "lt"

        # Dendra requires paging of 2,000 records maximum at a time.
        # To get around this, we loop through multiple requests and append
        # the results into a single dataset.
        # DR notes to self: this needs to broken out into a function
        try:
            r = requests.get(
                datapoints_url, headers=self.headers, params=query, timeout=120
            )
            assert r.status_code == 200
        except:
            # return r.status_code
            return None, None

        rjson = r.json()
        bigjson = rjson
        while len(rjson["data"]) > 0:
            df = pd.DataFrame.from_records(bigjson["data"])
            time_last = df[time_col].max()  # issue#1 miguel
            query["time[$gt]"] = time_last
            r = requests.get(
                datapoints_url, headers=self.headers, params=query, timeout=120
            )
            assert r.status_code == 200
            rjson = r.json()
            bigjson["data"].extend(rjson["data"])

        # Create Pandas DataFrame and set time as index
        # If the datastream has data for the time period, populate DataFrame
        if len(bigjson["data"]) > 0:
            df = pd.DataFrame.from_records(bigjson["data"])
        else:
            df = pd.DataFrame(columns=["lt", "t", "v"])

        # Get human readable name for data column
        if name == "default":
            datastream_name = name
        else:
            # raise NotImplementedError
            # need to refactor this def
            datastream_meta = self.get_meta_datastream_by_id(
                datastream_id, {"$select[name]": 1, "$select[station_id]": 1}
            )
            station_meta = self.get_meta_station_by_id(
                datastream_meta["station_id"], {"$select[slug]": 1}
            )
            stn = station_meta["slug"].replace("-", " ").title().replace(" ", "")
            datastream_name = stn + "_" + datastream_meta["name"].replace(" ", "_")

        # Rename columns
        df.rename(
            columns={
                "lt": "timestamp_local",
                "t": "timestamp_utc",
                "v": datastream_name,
            },
            inplace=True,
        )

        # Convert timestamp columns from 'object' to dt.datetime
        df.timestamp_local = pd.to_datetime(df.timestamp_local)
        df.timestamp_utc = pd.to_datetime(df.timestamp_utc, utc=True)

        # Set index to timestamp local or utc
        if time_type == "utc":
            df.set_index("timestamp_utc", inplace=True, drop=True)
        else:
            df.set_index("timestamp_local", inplace=True, drop=True)

        # Return DataFrame
        return df, datastream_name

    def list_organizations(self, orgslug="all"):
        """options: 'erczo','ucnrs','chi','tnc','ucanr','pepperwood'"""
        query = {"$sort[name]": 1, "$select[name]": 1, "$select[slug]": 1}
        if orgslug != "all":
            query["slug"] = orgslug

        r = requests.get(self.url + "organizations", headers=self.headers, params=query)
        assert r.status_code == 200
        rjson = r.json()
        return rjson["data"]

    def list_stations(self, orgslug="all", query_add="none"):
        """
        orgslug examples: 'erczo','ucnrs','chi'
        NOTE: can either do all orgs or one org. No option to list some,
            unless you custom add to the query.
        """
        stations_url = self.url + "stations"
        query = {
            "$sort[name]": 1,
            "$select[name]": 1,
            "$select[slug]": 1,
            "$limit": 2016,
        }

        # Narrow query to one organization
        if orgslug != "all":
            org_list = self.list_organizations(orgslug)
            if len(org_list) == 0:
                return "ERROR: no organizations found with that acronym."
            orgid = org_list[0]["_id"]
            query["organization_id"] = orgid

        # Modify query adding custom elements
        if query_add != "none":
            for element in query_add:
                query[element] = query_add[element]

        # Request JSON from Dendra
        r = requests.get(stations_url, headers=self.headers, params=query, timeout=120)
        assert r.status_code == 200
        rjson = r.json()
        return rjson["data"]

    def list_datastreams_by_station_id(self, station_id, query_add=""):
        query = {
            "$sort[name]": 1,
            "$select[name]": 1,
            "station_id": station_id,
            "$limit": 2016,
        }
        if query_add != "":
            query.update(query_add)

        # Request JSON from Dendra
        r = requests.get(self.url + "datastreams", headers=self.headers, params=query)
        assert r.status_code == 200
        rjson = r.json()
        return rjson["data"]

    def list_datastreams_by_medium_variable(
        self,
        medium="",
        variable="",
        aggregate="",
        station_id="",
        orgslug="",
        query_add="",
    ):
        """
        parameters:
        medium: Air, Water, Soil, etc
        variable: Temperature, Moisture, Radiation, etc
        aggregate: Minimum, Average, Maximum, Cumulative
        station_id: MongoID
        orgslug: shortname (currently erczo, ucnrs, chi, ucanr, tnc, pepperwood)
        query_add: JSON query please see documentation https://dendrascience.github.io/dendra-json-schema/
        """
        query = {"$sort[name]": 1, "$select[name]": 1, "$limit": 2016}
        if medium != "":
            query.update({"terms_info.class_tags[$all][0]": "ds_Medium_" + medium})
        if variable != "":
            query.update({"terms_info.class_tags[$all][1]": "ds_Variable_" + variable})
        if aggregate != "":
            query.update(
                {"terms_info.class_tags[$all][2]": "ds_Aggregate_" + aggregate}
            )
        if station_id != "":
            query.update({"station_id": station_id})
        if orgslug != "":
            orgid = self.get_organization_id(orgslug)
            query.update({"organization_id": orgid})
        if query_add != "":
            query.update(query_add)

        # Request JSON from Dendra
        r = requests.get(self.url + "datastreams", headers=self.headers, params=query)
        assert r.status_code == 200
        rjson = r.json()

        return rjson["data"]


# End Dendra code ->


def request_HADS(year, siteid, network="HADS"):
    """get HADS met data from Iowa Environmental Mesonet API
    TODO: make robust with proper request methods

    :param (int) year: year in YYYY
    :param (str) siteid: site id
    :param (str) network: one of "HADS", "CA_DCP", "CA_ASOS"
    :returns (pd.DataFrame): df of all available vars for site
    """
    URL = f"https://mesonet.agron.iastate.edu/cgi-bin/request/hads.py?network={network}&var=max_temp_f&var=min_temp_f&var=max_dewpoint_f&var=min_dewpoint_f&var=precip_in&var=avg_wind_speed_kts&var=avg_wind_drct&var=min_rh&var=avg_rh&var=max_rh&var=climo_high_f&var=climo_low_f&var=climo_precip_in&var=snow_in&var=snowd_in&var=min_feel&var=avg_feel&var=max_feel&var=max_wind_speed_kts&var=max_wind_gust_kts&var=srad_mj&na=None&sts={year}-01-01T00:00:00Z&ets={year+1}-12-31T23:00:00Z&stations={siteid}&format=csv"

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
