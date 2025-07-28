import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.colors
import glob
import psycopg2
import sys
import pandas.io.sql as sqlio
import requests
import json
import os
import logging

# Configure logging to suppress matplotlib font manager debug messages
logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)

# Configure matplotlib to use Qt backend
plt.switch_backend("Qt5Agg")

from fluvius_captar import (
    calculate_current_month_captar_cost,
    calculate_grid_offtake_stats,
    load_grid_offtake_data,
    load_grid_tariffs,
    select_days_from_month,
)

# Entras colors:
EntrasC1 = "#A0CDD0"
EntrasC2 = "#1F9562"
EntrasC3 = "#483F5E"
# Set the default color cycle & create cmap with Entras colors
plt.rcParams["axes.prop_cycle"] = plt.cycler(
    color=[EntrasC3, EntrasC2, EntrasC1]
    + plt.rcParams["axes.prop_cycle"].by_key()["color"][3:]
)
cmap_entras = matplotlib.colors.LinearSegmentedColormap.from_list(
    "", [EntrasC3, EntrasC2, EntrasC1]
)

# Construct the full path to the Excel file
file_path = os.path.join("data", "2022-2023 KRONOS data analyse.xlsx")
# os.chdir("C:/github_projects/Kronos")
# os.getcwd()
# Read Excel file
df = pd.read_excel(file_path, sheet_name="SRC DATA", skiprows=18)

# Convert all columns except DatumTijd to numeric, replacing any non-numeric values with NaN
for column in df.columns:
    if column != "DatumTijd":
        df[column] = pd.to_numeric(df[column], errors="coerce")

df.set_index("DatumTijd", inplace=True)

# Print data types to verify conversion
print("Data types after conversion:")
print(df.dtypes)

# Print first few rows to check data
print("\nFirst few rows of data:")
print(df.head())

fig, ax = plt.subplots(figsize=(10, 5))
df[
    [
        "GAS_UTIL_Totaal_Nm³",
        "GAS_UTIL_Turbine_Nm³",
        "GAS_UTIL_HRSG_Nm³",
        "GAS_UTIL_BUB brander 1_Nm³",
        "GAS_UTIL_BUB brander 2_Nm³",
    ]
].plot(ax=ax, grid=True)
ax.set_ylabel("Gas utilisation [Nm³]")
ax.set_xlabel("Time")
ax.set_title("Gas utilisation")
plt.show()

fig, ax = plt.subplots(figsize=(10, 5))
df[["STOOM_UTIL_HRSG_ton/hr", "STOOM_UTIL_WHB_ton/hr", "STOOM_UTIL_BUB_ton/hr"]].plot(
    ax=ax, grid=True
)
ax.set_ylabel("Steam production [ton/h]")
ax.set_xlabel("Time")
ax.set_title("Steam production")
plt.show()

fig, ax = plt.subplots(figsize=(10, 5))
df[
    [
        "STOOM_21 barg_21 barg TOT_ton/hr",
        "STOOM_9 barg_9 barg TOT_ton/hr",
        "STOOM_9 barg_9 barg ONTG_ton/hr",
        "STOOM_9 barg_9 barg NB_ton/hr",
        "STOOM_9 barg_9 barg CP_ton/hr",
    ]
].plot(ax=ax, grid=True)
ax.set_ylabel("Steam consumption [ton/h]")
ax.set_xlabel("Time")
ax.set_title("Steam consumption")
plt.show()

fig, ax = plt.subplots(figsize=(10, 5))
df[
    [
        "ELEC_FLUVIUS_Afname_kWh",
        "ELEC_FLUVIUS_GTprod_kWh",
        "ELEC_FLUVIUS_Injectie_kWh",
        "ELEC_verbruik_kWh",
    ]
].plot(ax=ax, grid=True)
ax.set_ylabel("Elec (kWh)")
ax.set_xlabel("Time")
ax.set_title("electricity")
plt.show()

fig, ax = plt.subplots(figsize=(10, 5))
df[["GT_REND_%"]].plot(ax=ax, grid=True)
ax.set_ylabel("%")
ax.set_xlabel("Time")
ax.set_title("GT rendement")
plt.show()
