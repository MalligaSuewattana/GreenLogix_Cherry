"""
Data generator module for energy system modeling.

This module provides functions to generate time series data for energy system modeling,
including price data (electricity, gas, CO2), demand data (heat, electricity), and temperature data.
All timestamps are handled in CET timezone.

Temperature data can be fetched from the Open-Meteo API or read from a local CSV file
for faster access and offline use.

Example:
    >>> df = get_data(
    ...     price_starttime="2022-01-01",
    ...     demand_starttime="2022-01-01",
    ...     length=24,
    ...     freq="H",
    ...     save_to_csv=True,
    ...     use_local_data=True  # Use local temperature data instead of API
    ... )
"""

import pandas as pd
import os
import pytz
import requests
from io import StringIO
from datetime import timedelta
from entras_data.spot_price import get_spot_price
from entras_data.gas_price import get_ttf_price
from entras_data.market_data import get_market_data
import numpy as np


def get_prices(starttime: str, endtime: str, freq: str = "h") -> pd.DataFrame:
    """
    Get price data for energy system modeling.

    Retrieves and processes price data for electricity (EPEX spot), gas, and CO2 emissions.
    All timestamps are converted to CET timezone.

    Args:
        starttime (str): Start date for the time series (format: 'YYYY-MM-DD')
        endtime (str): End date for the time series (format: 'YYYY-MM-DD')
        freq (str, optional): Frequency of the time series. Defaults to "h" (hourly).
            Other options: "D" (daily), "15T" (15 minutes), etc.

    Returns:
        pd.DataFrame: DataFrame with datetime index in CET containing:
            - epexspot: Electricity spot prices (€/MWh)
            - gas_prices: Natural gas prices (€/MWh)
            - co2_prices: CO2 emission prices (€/ton)
    """
    # Create date range
    start = pd.Timestamp(starttime).tz_localize("CET")
    end = pd.Timestamp(endtime).tz_localize("CET")
    date_range = pd.date_range(start=start, end=end, freq=freq, tz="CET")[:-1]

    # Get market data
    epexspot_df = get_spot_price(
        starttime=starttime,
        endtime=endtime,
        select={"timestamp": "timestamp", "da_price": "price"},
    )
    # epexspot_df["injection_price"] = 10 - epexspot_df["offtake_price"]

    gas_prices_df = get_market_data(
        "ttf_da_eod",
        starttime=starttime,
        endtime=endtime,
        select={"timestamp": "timestamp", "gas_price": "price"},
    )
    co2_prices_df = get_market_data(
        "eua_spot_realto",
        starttime=starttime,
        endtime=endtime,
        select={"timestamp": "datetime", "co2_price": "price"},
    )

    # Create empty DataFrame with date_range index
    result_df = pd.DataFrame(index=date_range)

    # Process each price series
    for price_df, col_name in [
        (epexspot_df, "da_price"),
        (gas_prices_df, "gas_price"),
        (co2_prices_df, "co2_price"),
    ]:
        # Convert timestamps to datetime and set as index
        price_df["timestamp"] = pd.to_datetime(price_df["timestamp"])
        price_df = price_df.set_index("timestamp")

        # Reindex to date_range and forward fill
        result_df[col_name] = price_df[col_name].reindex(date_range).ffill()

    # Fill any remaining NaN values
    result_df = result_df.ffill().bfill()

    return result_df


get_prices("2024-01-01", "2024-01-02", "h")


def get_demands(starttime: str, endtime: str, freq: str = "h") -> pd.DataFrame:
    """
    Get demand data for energy system modeling.

    Reads and processes demand data from CSV file, handling timezone conversions
    and ensuring continuous time series. All timestamps are in CET timezone.

    Args:
        starttime (str): Start date for the time series (format: 'YYYY-MM-DD')
        endtime (str): End date for the time series (format: 'YYYY-MM-DD')
        freq (str, optional): Frequency of the time series. Defaults to "h" (hourly).
            Other options: "D" (daily), "15T" (15 minutes), etc.

    Returns:
        pd.DataFrame: DataFrame with datetime index in CET containing:
            - heat_demand: Steam demand (ton/hr)
            - electricity_demand: Electricity consumption (kWh)

    Note:
        - Handles duplicate timestamps by taking the last value
        - Fills missing values using forward and backward fill
        - Adjusts out-of-order timestamps
    """

    # Create date range with timezone information and remove the last element
    start = pd.Timestamp(starttime).tz_localize("CET")
    end = pd.Timestamp(endtime).tz_localize("CET")
    date_range = pd.date_range(start=start, end=end, freq=freq, tz="CET")[:-1]

    # Read demand data from CSV
    demand_df = pd.read_csv(
        "data/2022-2023 KRONOS data analyse.csv", encoding="latin-1"
    )

    # Convert timestamps to datetime and handle timezone
    # Adjust timestamps if they're out of order
    timestamps_list = pd.to_datetime(demand_df["DatumTijd"].values, utc=True).tolist()
    for i in range(1, len(timestamps_list)):
        if timestamps_list[i] < timestamps_list[i - 1]:
            timestamps_list[i] = timestamps_list[i - 1] + pd.Timedelta(hours=1)

    # Convert list back to DatetimeIndex
    timestamps = pd.DatetimeIndex(timestamps_list).tz_convert("CET")

    # Assign to DataFrame
    demand_df["process_timestamp"] = timestamps

    # Select only the required columns
    demand_df = demand_df[
        ["process_timestamp", "STOOM_21 barg_21 barg TOT_ton/hr", "ELEC_verbruik_kWh"]
    ]

    # Rename columns to match the expected output
    demand_df.columns = ["process_timestamp", "heat_demand", "electricity_demand"]

    # Convert electricity demand from kWh to MW
    demand_df["electricity_demand"] = (
        demand_df["electricity_demand"] / 1000
    )  # Convert kWh to MW

    # Find and print duplicate timestamps
    duplicates = demand_df[
        demand_df.duplicated(subset=["process_timestamp"], keep=False)
    ]
    if not duplicates.empty:
        print("\nDuplicate timestamps found:")
        print(duplicates.sort_values("process_timestamp"))

    # Create a new DataFrame with date_range as index
    result_df = pd.DataFrame(index=date_range)

    # For each timestamp in date_range, find matching values in demand_df
    for idx in date_range:
        matching_rows = demand_df[demand_df["process_timestamp"] == idx]
        if not matching_rows.empty:
            result_df.loc[idx, "heat_demand"] = matching_rows["heat_demand"].iloc[-1]
            result_df.loc[idx, "electricity_demand"] = matching_rows[
                "electricity_demand"
            ].iloc[-1]

    # Fill NaN values
    result_df = result_df.ffill().bfill()

    return result_df


def get_temperature(
    starttime: str, endtime: str, freq: str = "h", use_local_data: bool = False
) -> pd.DataFrame:
    """
    Get temperature data from Open-Meteo API or local file.

    Fetches historical temperature data for Ghent, Belgium (51.07°N, 3.71°E).
    All timestamps are in CET timezone.

    Args:
        starttime (str): Start date for the time series (format: 'YYYY-MM-DD')
        endtime (str): End date for the time series (format: 'YYYY-MM-DD')
        freq (str, optional): Frequency of the time series. Defaults to "h" (hourly).
            Other options: "D" (daily), "15T" (15 minutes), etc.
        use_local_data (bool, optional): Whether to use locally saved data instead of API.
            Defaults to False. If True, reads from 'data/open-meteo-51.07N3.71E13m.csv'.

    Returns:
        pd.DataFrame: DataFrame with datetime index in CET containing:
            - temperature: Air temperature at 2m height (°C)

    Note:
        - If use_local_data=True, data is read from local CSV file
        - If use_local_data=False, data is fetched from Open-Meteo's historical API
        - Missing values are interpolated linearly
        - All timestamps are in CET timezone
        - Local data covers 2022-01-01 to 2022-12-31
        - Fetched data is automatically saved to 'data/open-meteo-51.07N3.71E13m.csv' in the same format
    """
    # Define timezone
    tz = pytz.timezone("Europe/Brussels")

    # Convert and localize dates
    start_date = pd.to_datetime(starttime).tz_localize(tz)
    end_date = pd.to_datetime(endtime).tz_localize(tz)

    # Validate date range
    if start_date >= end_date:
        raise ValueError(f"starttime ({starttime}) must be before endtime ({endtime})")

    if use_local_data:
        # Read from local CSV file
        local_file_path = "data/open-meteo-51.07N3.71E13m_2024.csv"

        if not os.path.exists(local_file_path):
            raise FileNotFoundError(
                f"Local temperature data file not found: {local_file_path}"
            )

        # Read the CSV file, skipping the header rows
        temp = pd.read_csv(local_file_path, skiprows=2, encoding="latin1")

        # Process temperature data
        temp["time"] = (
            pd.to_datetime(temp["time"]).dt.tz_localize("UTC").dt.tz_convert(tz)
        )
        temp_series = pd.Series(temp["temperature_2m (°C)"].values, index=temp["time"])

        # Filter to requested date range
        temp_filtered = temp_series[
            (temp_series.index >= start_date) & (temp_series.index < end_date)
        ]

        # Resample to requested frequency
        temp_resampled = temp_filtered.resample(freq).interpolate(method="linear")

    else:
        # Get timeseries and calculate UTC date range for API
        ts = pd.date_range(start=start_date, end=end_date, freq="15min", tz=tz)
        start_date_utc = ts.min().tz_convert("UTC").strftime("%Y-%m-%d")
        end_date_utc = ts.max().tz_convert("UTC").strftime("%Y-%m-%d")

        # Fetch temperature data
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": 51.07,
            "longitude": 3.71,
            "start_date": start_date_utc,
            "end_date": end_date_utc,
            "hourly": "temperature_2m",
            "format": "csv",
        }
        response = requests.get(url, params=params)
        temp = pd.read_csv(StringIO(response.text), skiprows=2)

        # Process temperature data
        temp["time"] = (
            pd.to_datetime(temp["time"]).dt.tz_localize("UTC").dt.tz_convert(tz)
        )
        temp_series = pd.Series(temp["temperature_2m (°C)"].values, index=temp["time"])
        temp_resampled = temp_series.resample(freq).interpolate(method="linear")

        # Save the fetched data to CSV in the same format as the original file
        save_temperature_to_csv(temp_resampled, start_date_utc, end_date_utc)

    # Create DataFrame with temperature data
    df = pd.DataFrame({"temperature": temp_resampled})
    df.index = df.index.tz_convert("CET")
    df = df[(df.index >= start_date) & (df.index < end_date)]
    return df


def save_temperature_to_csv(temp_series: pd.Series, start_date: str, end_date: str):
    """
    Save temperature data to CSV file in the same format as open-meteo-51.07N3.71E13m.csv

    Args:
        temp_series (pd.Series): Temperature data series with datetime index
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
    """
    # Create the output file path
    output_file = "data/open-meteo-51.07N3.71E13m.csv"

    # Ensure the data directory exists
    os.makedirs("data", exist_ok=True)

    # Prepare the data for saving
    # Convert to UTC for saving (same as original format)
    temp_utc = temp_series.tz_convert("UTC")

    # Create DataFrame with the same format as the original file
    df_to_save = pd.DataFrame(
        {
            "time": temp_utc.index.strftime("%Y-%m-%dT%H:%M"),
            "temperature_2m (°C)": temp_utc.values,
        }
    )

    # Write the file with the same format as the original
    with open(output_file, "w", newline="") as f:
        # Write header metadata (same as original)
        f.write(
            "latitude,longitude,elevation,utc_offset_seconds,timezone,timezone_abbreviation\n"
        )
        f.write("51.072056,3.7096772,13.0,0,GMT,GMT\n")
        f.write("\n")  # Empty line

        # Write the data
        df_to_save.to_csv(f, index=False)

    print(
        f"Temperature data saved to {output_file} (period: {start_date} to {end_date})"
    )


def get_data(
    price_starttime: str,
    demand_starttime: str,
    length: int,
    freq: str = "h",
    save_to_csv: bool = False,
    filename: str = "time_series_data.csv",
    use_local_data: bool = False,
) -> pd.DataFrame:
    """
    Generate time series data for energy system modeling.

    Combines price, demand, and temperature data into a single DataFrame.
    Price and temperature data are aligned to a common timestamp, while demand data
    maintains its original timestamps and process_timestamp column.

    Args:
        price_starttime (str): Start date for price data (format: 'YYYY-MM-DD')
        demand_starttime (str): Start date for demand data (format: 'YYYY-MM-DD')
        length (int): Number of periods to generate
        freq (str, optional): Frequency of the time series. Defaults to "h" (hourly).
            Other options: "D" (daily), "15T" (15 minutes), etc.
        save_to_csv (bool, optional): Whether to save the data to a CSV file. Defaults to False.
        filename (str, optional): Name of the CSV file to save to. Defaults to "time_series_data.csv".
            If file exists, a number will be appended to the filename.
        use_local_data (bool, optional): Whether to use locally saved temperature data instead of API.
            Defaults to False. If True, reads from 'data/open-meteo-51.07N3.71E13m.csv'.

    Returns:
        pd.DataFrame: DataFrame with datetime index (timestamp) containing:
            - process_timestamp: Original timestamp from demand data
            - epexspot: Electricity spot prices (€/MWh)
            - gas_prices: Natural gas prices (€/MWh)
            - co2_prices: CO2 emission prices (€/ton)
            - heat_demand: Steam demand (ton/hr)
            - electricity_demand: Electricity consumption (kWh)
            - temperature: Air temperature at 2m height (°C)

    Note:
        - All values are rounded to 2 decimal places
        - Files are saved in the 'data' directory
        - Existing files are not overwritten
        - Price and temperature data are aligned to common timestamps
        - Demand data maintains its original timestamps
        - DataFrame has timestamp as index and process_timestamp as column
        - If use_local_data=True, temperature data is read from local file instead of API
    """
    # Calculate endtimes based on length
    price_endtime = (
        pd.Timestamp(price_starttime) + pd.Timedelta(hours=length)
    ).strftime("%Y-%m-%d")
    demand_endtime = (
        pd.Timestamp(demand_starttime) + pd.Timedelta(hours=length)
    ).strftime("%Y-%m-%d")

    # Get price, demand, and temperature data
    prices_df = get_prices(price_starttime, price_endtime, freq)
    demands_df = get_demands(demand_starttime, demand_endtime, freq)
    temperature_df = get_temperature(
        price_starttime, price_endtime, freq, use_local_data
    )

    # Create a common date range for price and temperature data
    date_range = pd.date_range(
        start=pd.Timestamp(price_starttime).tz_localize("CET"),
        end=pd.Timestamp(price_endtime).tz_localize("CET"),
        freq=freq,
        tz="CET",
    )

    # Combine price and temperature data
    market_data = pd.concat([prices_df, temperature_df], axis=1)

    # Reset index of demands_df to make process_timestamp a column
    demands_df["timestamp"] = market_data.index
    demands_df = demands_df.reset_index()
    demands_df = demands_df.rename(columns={"index": "process_timestamp"})
    demands_df = demands_df.set_index("timestamp")

    # Combine all data
    df = pd.concat([demands_df, market_data], axis=1)

    # Save to CSV if requested
    if save_to_csv:
        # Ensure filename is in data folder
        if not filename.startswith("data/"):
            filename = f"data/{filename}"

        # Check if file exists and modify filename if needed
        base_name = filename[:-4]  # Remove .csv
        counter = 1
        while os.path.exists(filename):
            filename = f"{base_name}_{counter}.csv"
            counter += 1

        # Round numeric columns to 2 decimal places before saving
        df_rounded = df.copy()
        numeric_columns = df_rounded.select_dtypes(include=[np.number]).columns
        df_rounded[numeric_columns] = df_rounded[numeric_columns].round(2)

        df_rounded.to_csv(filename)
        print(f"Data has been saved to '{filename}'")

    return df
