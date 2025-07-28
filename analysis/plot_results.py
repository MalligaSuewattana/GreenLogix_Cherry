import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
from pathlib import Path

%matplotlib qt

os.chdir(Path(__file__).parent.parent)
print(f"Working directory: {os.getcwd()}")

# Define custom colors
colors = {
    "demand": "#1f77b4",  # blue
    "chp": "#ff7f0e",  # orange
    "offtake": "#d62728",  # red
    "eboiler": "#9467bd",  # purple
    "hrsg": "#8c564b",  # brown
    "gas_boiler": "#e377c2",  # pink
    "prices": "#7f7f7f",  # gray
    "injection": "#17becf",  # cyan
    "b": "#ffd700",  # gold
    "c": "#98fb98",  # pale green
    "d": "#4169e1",  # royal blue
    "e": "#ff69b4",  # hot pink
    "f": "#228b22",  # forest green
    "g": "#cd853f",  # peru
    "h": "#20b2aa",  # light sea green
}


def load_results_df(scenario=None):
    """
    Load the most recent results file for a given scenario.
    If scenario is None, loads from the root results folder.
    Returns: df, scenario_name, file_datetime
    """
    if scenario:
        search_path = f"results/{scenario}/results_*.xlsx"
        scenario_name = scenario
    else:
        search_path = "results/results_*.xlsx"
        scenario_name = "default"
    results_files = glob.glob(search_path)
    if not results_files:
        raise FileNotFoundError(
            f"No results files found in {os.path.dirname(search_path)}"
        )
    latest_file = max(results_files, key=os.path.getctime)
    file_datetime = os.path.getctime(latest_file)
    file_datetime = pd.to_datetime(file_datetime, unit="s")
    print(f"Using results file: {latest_file}")
    df = pd.read_excel(latest_file, sheet_name="Timeseries")
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
    return df, scenario_name, file_datetime


def plot_results(results_df, scenario_name, file_datetime, singleplot=False):
    title_info = f"Scenario: {scenario_name} | Generated: {file_datetime.strftime('%Y-%m-%d %H:%M:%S')}"
    if not singleplot:
        fig, (ax, ax1, ax2) = plt.subplots(3, 1, sharex=True, figsize=(12, 8))
    else:
        fig, (ax, ax1, ax2, ax3, ax5) = plt.subplots(
            5, 1, sharex=True, figsize=(12, 12)
        )

    results_df[["electricity_demand_demand", "e_boiler_input"]].sum(axis=1).plot(
        ax=ax, grid=True, drawstyle="steps-post", color=colors["demand"]
    )
    ax.fill_between(
        results_df.index,
        0,
        results_df["chp_electricity_output"],
        alpha=0.5,
        step="post",
        color=colors["chp"],
    )
    ax.fill_between(
        results_df.index,
        results_df["chp_electricity_output"],
        results_df["chp_electricity_output"]
        + results_df["Electricity offtake_quantities"],
        alpha=0.5,
        step="post",
        color=colors["offtake"],
    )
    ax.legend(
        ["Demand", "CHP (GT)", "Electricity offtake"],
        bbox_to_anchor=(1.05, 1),
        loc="upper left",
    )
    ax.set_ylabel("Electricity source [MW]")

    results_df[
        [
            "electricity_demand_demand",
            "e_boiler_input",
            "Electricity injection_quantities",
        ]
    ].sum(axis=1).plot(
        ax=ax1, grid=True, drawstyle="steps-post", color=colors["demand"]
    )
    ax1.set_ylabel("Electricity sink [MW]")

    ax1.fill_between(
        results_df.index,
        0,
        results_df["electricity_demand_demand"],
        alpha=0.5,
        step="post",
        color=colors["demand"],
    )
    ax1.fill_between(
        results_df.index,
        results_df["electricity_demand_demand"],
        results_df["electricity_demand_demand"] + results_df["e_boiler_input"],
        alpha=0.5,
        step="post",
        color=colors["eboiler"],
    )
    ax1.fill_between(
        results_df.index,
        results_df["electricity_demand_demand"] + results_df["e_boiler_input"],
        results_df["electricity_demand_demand"]
        + results_df["e_boiler_input"]
        + results_df["Electricity injection_quantities"],
        alpha=0.5,
        step="post",
        color=colors["injection"],
    )
    ax1.legend(
        ["Demand", "Base demand", "E-boiler", "Electricity injection"],
        bbox_to_anchor=(1.05, 1),
        loc="upper left",
    )

    results_df[
        [
            "Electricity offtake_prices",
            "Gas offtake_prices",
        ]
    ].plot(
        ax=ax2,
        grid=True,
        drawstyle="steps-post",
        color=[colors["offtake"], colors["prices"]],
    )
    (-results_df["Electricity injection_prices"]).plot(
        ax=ax2,
        grid=True,
        drawstyle="steps-post",
        color=colors["injection"],
    )
    ax2.set_ylabel("Prices [EUR/MWh]")
    ax2.legend(
        ["Electricity offtake", "Gas offtake", "Electricity injection"],
        bbox_to_anchor=(1.05, 1),
        loc="upper left",
    )

    if not singleplot:
        ax.set_title(f"Electricity\n{title_info}")
        plt.tight_layout()
        plt.get_current_fig_manager().window.showMaximized()
        plt.show()
    else:
        ax.set_title(f"{title_info}")

    if not singleplot:
        fig, (ax3, ax4, ax5) = plt.subplots(3, 1, sharex=True, figsize=(12, 8))

    results_df[["heat_demand_demand"]].plot(
        ax=ax3, grid=True, drawstyle="steps-post", color=colors["demand"]
    )
    ax3.fill_between(
        results_df.index,
        0,
        results_df["chp_thermal_output"],
        alpha=0.5,
        step="post",
        color=colors["chp"],
    )
    ax3.fill_between(
        results_df.index,
        results_df["chp_thermal_output"],
        results_df["chp_thermal_output"] + results_df["gas_boiler_output"],
        alpha=0.5,
        step="post",
        color=colors["gas_boiler"],
    )

    ax3.fill_between(
        results_df.index,
        results_df["chp_thermal_output"] + results_df["gas_boiler_output"],
        results_df["chp_thermal_output"]
        + results_df["gas_boiler_output"]
        + results_df["e_boiler_output"],
        alpha=0.5,
        step="post",
        color=colors["eboiler"],
    )
    ax3.legend(
        [
            "Demand",
            "CHP (HRSG)",
            "gas boiler",
            "eboiler",
        ],
        bbox_to_anchor=(1.05, 1),
        loc="upper left",
    )
    ax3.set_ylabel("Heat source [MW]")

    if not singleplot:
        results_df[
            [
                "Electricity offtake_prices",
                "Gas offtake_prices",
            ]
        ].plot(
            ax=ax4,
            grid=True,
            drawstyle="steps-post",
            color=[colors["offtake"], colors["prices"]],
        )
        ax4.set_ylabel("Prices [EUR/MWh]")
        ax4.legend(
            ["Electricity offtake", "Gas offtake"],
            bbox_to_anchor=(1.05, 1),
            loc="upper left",
        )
    df["low_demand"].astype(int).plot(
        ax=ax5, grid=True, drawstyle="steps-post", color=colors["demand"]
    )
    ax5.set_ylabel("Low demand [/]")

    if not singleplot:
        ax3.set_title(f"Heat\n{title_info}")
    plt.tight_layout()
    plt.get_current_fig_manager().window.showMaximized()
    plt.show()


def list_available_scenarios(results_dir="results"):
    scenarios = []
    if not os.path.isdir(results_dir):
        print(f"No '{results_dir}' directory found.")
        return scenarios

    # Check for results in the root results directory
    root_files = glob.glob(os.path.join(results_dir, "results_*.xlsx"))
    if root_files:
        scenarios.append("default")  # or "root"

    # Check subdirectories
    for entry in os.listdir(results_dir):
        scenario_path = os.path.join(results_dir, entry)
        if os.path.isdir(scenario_path):
            files = glob.glob(os.path.join(scenario_path, "results_*.xlsx"))
            if files:
                scenarios.append(entry)
    return scenarios


scenarios = list_available_scenarios()
print("Available scenarios:", scenarios)

# use to plot latest simulatin which is not in a scenario folder
# df, scenario, dt = load_results_df()
# plot_results(df, scenario, dt)

# use to plot latest simulation in a scenario folder
df, scenario, dt = load_results_df("Flex_1.1")
plot_results(df, scenario, dt, singleplot=True)

# df.columns
# fig,ax=plt.subplots()
# df[["chp_gas_to_aux_firing","chp_gas_to_turbine"]].plot(ax=ax)
# df["chp_aux_firing_efficiency"]
