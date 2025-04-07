import pandas as pd
import xarray as xr
from pathlib import Path
import requests


def ngen_csv_to_df(
    path: str,
) -> tuple[list[pd.DataFrame], list[str]]:
    """
    Loads NGen CSV outputs.

    Args:
        path (str, optional): Location of NGen output with catchment .csv files.

    Returns:
        tuple: List of DataFrames and list of catchment names.
    """
    cat_paths = list(Path(path).glob("cat-*.csv"))
    catchments = [p.stem for p in cat_paths]
    df_lst = [pd.read_csv(p, index_col=["Time"], parse_dates=["Time"]) for p in cat_paths]

    return df_lst, catchments


def ngen_csv_to_xr(
    path: str,
) -> xr.Dataset | tuple[xr.Dataset, list]:
    """
    Parses NGen model outputs into an xarray Dataset.

    Args:
        path (str, optional): Path to NGen output CSV files.

    Returns:
        Dataset or tuple: xarray Dataset (and catchment names if cats_out is True).
    """
    df_lst, cats = ngen_csv_to_df(path)
    data_vars = {}

    for df in df_lst:
        for column in df.columns:
            if column not in data_vars:
                data_vars[column] = []
            data_vars[column].append(
                xr.DataArray(
                    df[column].values,
                    dims=["Time"],
                    coords={"Time": df.index},
                )
            )

    # concatenate each var's DataArrays along the 'catchment' dimension
    for var in data_vars:
        data_vars[var] = xr.concat(data_vars[var], dim=pd.Index(cats, name="catchment"))

    return xr.Dataset(data_vars)


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
        response = requests.get(URL, timeout=240)
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
