import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Read the data
df1 = pd.read_csv(
    "data/open-meteo-51.07N3.71E13m_2022.csv", skiprows=2, encoding="latin-1"
)
df2 = pd.read_csv(
    "data/2022-2023 KRONOS data analyse.csv",
    usecols=["DatumTijd", "ELEC_FLUVIUS_GTprod_kWh"],
    encoding="latin-1",
)

df1["time"] = pd.to_datetime(df1["time"], utc=True).dt.tz_convert("CET")
df2["DatumTijd"] = pd.to_datetime(df2["DatumTijd"], utc=True).dt.tz_convert("CET")

df1 = df1.set_index("time")
df2 = df2.set_index("DatumTijd")

merged = pd.merge(df1, df2, left_index=True, right_index=True)
merged.columns = ["temperature", "production"]

# Plot temperature vs. production, with color representing month
merged["month"] = merged.index.month
plt.scatter(
    merged["temperature"],
    merged["production"],
    c=merged["month"],
    s=1,
    cmap="Paired",
    vmin=1,
    vmax=13,
)
cbar = plt.colorbar(label="Month", boundaries=np.arange(1, 14) - 0.5)
cbar.set_ticks(np.arange(1, 13))
cbar.set_ticklabels(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
)
plt.xlabel("Temperature")
plt.ylabel("Production")
plt.title("Temperature vs. Production")
plt.ylim(bottom=5000)
plt.show()

# Describe temperature dependence as a linear function
# Filter out the data for months with less than 5000kW production
slopes = []
intercepts = []
months = merged["month"].unique()
for month in months:
    filtered = merged[(merged["month"] == month) & (merged["production"] >= 5000)]
    slope, intercept = np.polyfit(filtered["temperature"], filtered["production"], 1)
    slopes.append(slope)
    intercepts.append(intercept)

# Plot the slope and intercept for each month, as obtained from the linear fit. The dashed line shows the average slope for months 4-12.
plt.scatter(months, slopes)
plt.xlabel("Month")
plt.ylabel("Slope (kW/°C)")
plt.title("Slope vs. Month")
plt.gca().invert_yaxis()
mean_slope = np.mean([slope for i, slope in enumerate(slopes) if i > 2])
plt.axhline(
    y=mean_slope, color="r", linestyle="--", label=f"Mean slope: {mean_slope:.2f} kW/°C"
)
plt.legend()
plt.show()

# Plot the intercept for each month, as obtained from the linear fit. The dashed line shows the average intercept for months 4-12.
plt.scatter(months, intercepts)
plt.xlabel("Month")
plt.ylabel("Intercept (kW)")
plt.title("Intercept vs. Month")
mean_intercept = np.mean([intercept for i, intercept in enumerate(intercepts) if i > 2])
plt.axhline(
    y=mean_intercept,
    color="r",
    linestyle="--",
    label=f"Mean intercept: {mean_intercept:.2f} kW",
)
plt.legend()
plt.show()
