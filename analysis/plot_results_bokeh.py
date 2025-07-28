import pandas as pd
import glob
import os
from pathlib import Path
from bokeh.plotting import figure, show, save
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem, BoxZoomTool
from bokeh.palettes import Category10
from bokeh.io import output_notebook, output_file
from bokeh.resources import CDN
from bokeh.embed import file_html
import numpy as np

os.chdir(Path(__file__).parent.parent)
print(f"Working directory: {os.getcwd()}")

# Define custom colors (same as matplotlib version)
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


def create_step_data(df, column):
    """Create step data for Bokeh plotting (equivalent to matplotlib's steps-post)"""
    # Use numeric indices (0 to len-1) instead of datetime
    x = list(range(len(df)))

    # Handle both column names and pandas Series
    if isinstance(column, str):
        y = df[column].tolist()
    else:
        # Assume it's a pandas Series
        y = column.tolist()

    # For step plot, we need to duplicate x values and shift y values
    step_x = []
    step_y = []

    for i in range(len(x)):
        if i == 0:
            step_x.append(x[i])
            step_y.append(y[i])
        else:
            step_x.append(x[i])
            step_y.append(y[i - 1])  # Use previous y value
        step_x.append(x[i])
        step_y.append(y[i])

    return step_x, step_y


def create_fill_data(df, y1_col, y2_col=None, base=0):
    """Create fill data for area plots"""
    # Use numeric indices (0 to len-1) instead of datetime
    x = list(range(len(df)))

    # Handle y1_col (can be column name or Series)
    if isinstance(y1_col, str):
        y1 = df[y1_col].tolist()
    else:
        y1 = y1_col.tolist()

    if y2_col is not None:
        # Handle y2_col (can be column name or Series)
        if isinstance(y2_col, str):
            y2_col_data = df[y2_col].tolist()
        else:
            y2_col_data = y2_col.tolist()
        y2 = [y1[i] + y2_col_data[i] for i in range(len(y1))]
    else:
        y2 = [base] * len(y1)

    # Create step data for fill
    step_x, step_y1 = create_step_data(df, y1_col)
    if y2_col is not None:
        step_y2 = []
        for i in range(len(df)):
            if i == 0:
                step_y2.append(y2[i])
            else:
                step_y2.append(y2[i - 1])
            step_y2.append(y2[i])
    else:
        step_y2 = [base] * len(step_x)

    return step_x, step_y1, step_y2


def plot_results_bokeh(
    results_df,
    scenario_name,
    file_datetime,
    singleplot=False,
    output_filename=None,
    scenario_description="",
):
    """
    Create Bokeh plots equivalent to the matplotlib version
    """
    title_info = f"Scenario: {scenario_name} | Generated: {file_datetime.strftime('%Y-%m-%d %H:%M:%S')}"

    # Create data source with numeric index
    df_with_index = results_df.reset_index()
    df_with_index["hour"] = range(len(df_with_index))
    source = ColumnDataSource(df_with_index)

    # Set up output with custom styling
    if output_filename:
        output_file(
            output_filename, title=f"Kronos Results - {scenario_name}", mode="cdn"
        )

    # Create plots
    plots = []

    # Plot 1: Electricity source
    p1 = figure(
        width=1000,
        height=200,
        title="",
        x_axis_type="linear",
        tools="pan,wheel_zoom,box_zoom,reset,save",
        active_scroll=None,
        sizing_mode="stretch_width",
    )

    # Total demand line - use simple line plot for better hover
    total_demand = results_df[["electricity_demand_demand", "e_boiler_input"]].sum(
        axis=1
    )
    step_x, step_y = create_step_data(results_df, total_demand)
    p1.step(step_x, step_y, color=colors["demand"], line_width=2, legend_label="Demand")

    # CHP fill
    step_x, step_y1, step_y2 = create_fill_data(results_df, "chp_electricity_output")
    chp_source = ColumnDataSource(data=dict(x=step_x, y1=step_y1, y2=step_y2))
    p1.varea(
        "x",
        "y1",
        "y2",
        source=chp_source,
        alpha=0.5,
        color=colors["chp"],
        legend_label="CHP (GT)",
    )

    # Electricity offtake fill
    step_x, step_y1, step_y2 = create_fill_data(
        results_df, "chp_electricity_output", "Electricity offtake_quantities"
    )
    offtake_source = ColumnDataSource(data=dict(x=step_x, y1=step_y1, y2=step_y2))
    p1.varea(
        "x",
        "y1",
        "y2",
        source=offtake_source,
        alpha=0.5,
        color=colors["offtake"],
        legend_label="Electricity offtake",
    )

    # Add hover data source for p1
    hours = list(range(len(results_df)))
    p1_hover_data = {
        "hours": hours,
        "total_demand": results_df[["electricity_demand_demand", "e_boiler_input"]]
        .sum(axis=1)
        .tolist(),
        "chp_output": results_df["chp_electricity_output"].tolist(),
        "offtake": results_df["Electricity offtake_quantities"].tolist(),
    }
    p1_hover_source = ColumnDataSource(data=p1_hover_data)
    p1.line("hours", "total_demand", source=p1_hover_source, alpha=0, line_width=0)

    p1.xaxis.axis_label = ""
    p1.yaxis.axis_label = "Electricity source [MW]"
    p1.legend.location = "top_left"
    plots.append(p1)

    # Plot 2: Electricity sink
    p2 = figure(
        width=1000,
        height=200,
        title="",
        x_axis_type="linear",
        tools="pan,wheel_zoom,box_zoom,reset,save",
        active_scroll=None,
        x_range=p1.x_range,  # Link x-axis
        sizing_mode="stretch_width",
    )

    # Total sink line
    total_sink = results_df[
        [
            "electricity_demand_demand",
            "e_boiler_input",
            "Electricity injection_quantities",
        ]
    ].sum(axis=1)
    step_x, step_y = create_step_data(results_df, total_sink)
    p2.step(step_x, step_y, color=colors["demand"], line_width=2, legend_label="Demand")

    # Base demand fill
    step_x, step_y1, step_y2 = create_fill_data(results_df, "electricity_demand_demand")
    p2.varea(
        step_x,
        step_y1,
        step_y2,
        alpha=0.5,
        color=colors["demand"],
        legend_label="Base demand",
    )

    # E-boiler fill
    step_x, step_y1, step_y2 = create_fill_data(
        results_df, "electricity_demand_demand", "e_boiler_input"
    )
    p2.varea(
        step_x,
        step_y1,
        step_y2,
        alpha=0.5,
        color=colors["eboiler"],
        legend_label="E-boiler",
    )

    # Electricity injection fill
    base_level = results_df["electricity_demand_demand"] + results_df["e_boiler_input"]
    step_x, step_y1, step_y2 = create_fill_data(
        results_df,
        base_level,
        "Electricity injection_quantities",
    )
    p2.varea(
        step_x,
        step_y1,
        step_y2,
        alpha=0.5,
        color=colors["injection"],
        legend_label="Electricity injection",
    )

    # Add hover data source for p2
    p2_hover_data = {
        "hours": hours,
        "base_demand": results_df["electricity_demand_demand"].tolist(),
        "eboiler": results_df["e_boiler_input"].tolist(),
        "injection": results_df["Electricity injection_quantities"].tolist(),
    }
    p2_hover_source = ColumnDataSource(data=p2_hover_data)
    p2.line("hours", "base_demand", source=p2_hover_source, alpha=0, line_width=0)

    p2.xaxis.axis_label = ""
    p2.yaxis.axis_label = "Electricity sink [MW]"
    p2.legend.location = "top_left"
    plots.append(p2)

    # Plot 3: Prices
    p3 = figure(
        width=1000,
        height=200,
        title="",
        x_axis_type="linear",
        tools="pan,wheel_zoom,box_zoom,reset,save",
        active_scroll=None,
        x_range=p1.x_range,  # Link x-axis
        sizing_mode="stretch_width",
    )

    # Electricity offtake prices
    step_x, step_y = create_step_data(results_df, "Electricity offtake_prices")
    p3.step(
        step_x,
        step_y,
        color=colors["offtake"],
        line_width=2,
        legend_label="Electricity offtake",
    )

    # Gas offtake prices
    step_x, step_y = create_step_data(results_df, "Gas offtake_prices")
    p3.step(
        step_x, step_y, color=colors["prices"], line_width=2, legend_label="Gas offtake"
    )

    # Electricity injection prices (negative)
    step_x, step_y = create_step_data(
        results_df, -results_df["Electricity injection_prices"]
    )
    p3.step(
        step_x,
        step_y,
        color=colors["injection"],
        line_width=2,
        legend_label="Electricity injection",
    )

    # Add hover data source for p3
    p3_hover_data = {
        "hours": hours,
        "elec_offtake_price": results_df["Electricity offtake_prices"].tolist(),
        "gas_offtake_price": results_df["Gas offtake_prices"].tolist(),
        "elec_injection_price": (-results_df["Electricity injection_prices"]).tolist(),
    }
    p3_hover_source = ColumnDataSource(data=p3_hover_data)
    p3.line(
        "hours", "elec_offtake_price", source=p3_hover_source, alpha=0, line_width=0
    )

    p3.xaxis.axis_label = ""
    p3.yaxis.axis_label = "Prices [EUR/MWh]"
    p3.legend.location = "top_left"
    plots.append(p3)

    if singleplot:
        # Plot 4: Heat source
        p4 = figure(
            width=1000,
            height=200,
            title="",
            x_axis_type="linear",
            tools="pan,wheel_zoom,box_zoom,reset,save",
            active_scroll=None,
            x_range=p1.x_range,  # Link x-axis
            sizing_mode="stretch_width",
        )

        # Heat demand line
        step_x, step_y = create_step_data(results_df, "heat_demand_demand")
        p4.step(
            step_x, step_y, color=colors["demand"], line_width=2, legend_label="Demand"
        )

        # CHP thermal fill
        step_x, step_y1, step_y2 = create_fill_data(results_df, "chp_thermal_output")
        p4.varea(
            step_x,
            step_y1,
            step_y2,
            alpha=0.5,
            color=colors["chp"],
            legend_label="CHP (HRSG)",
        )

        # Gas boiler fill
        step_x, step_y1, step_y2 = create_fill_data(
            results_df, "chp_thermal_output", "gas_boiler_output"
        )
        p4.varea(
            step_x,
            step_y1,
            step_y2,
            alpha=0.5,
            color=colors["gas_boiler"],
            legend_label="Gas boiler",
        )

        # E-boiler fill
        base_level = results_df["chp_thermal_output"] + results_df["gas_boiler_output"]
        step_x, step_y1, step_y2 = create_fill_data(
            results_df,
            base_level,
            "e_boiler_output",
        )
        p4.varea(
            step_x,
            step_y1,
            step_y2,
            alpha=0.5,
            color=colors["eboiler"],
            legend_label="E-boiler",
        )

        # Add hover data source for p4
        p4_hover_data = {
            "hours": hours,
            "heat_demand": results_df["heat_demand_demand"].tolist(),
            "chp_thermal": results_df["chp_thermal_output"].tolist(),
            "gas_boiler": results_df["gas_boiler_output"].tolist(),
            "eboiler_heat": results_df["e_boiler_output"].tolist(),
        }
        p4_hover_source = ColumnDataSource(data=p4_hover_data)
        p4.line("hours", "heat_demand", source=p4_hover_source, alpha=0, line_width=0)

        p4.xaxis.axis_label = ""
        p4.yaxis.axis_label = "Heat source [MW]"
        p4.legend.location = "top_left"
        plots.append(p4)

    # Create layout with header
    from bokeh.models import Div

    # Create header
    header = Div(
        text=f"""
        <div style="text-align: center; padding: 10px; background-color: #f8f9fa; border-bottom: 1px solid #dee2e6; margin-bottom: 10px;">
            <h1 style="color: #495057; margin: 0; font-size: 1.8em;">Kronos Energy System Analysis</h1>
            <p style="color: #6c757d; margin: 5px 0 0 0; font-size: 1em;">{title_info}</p>
            <p style="color: #495057; margin: 5px 0 0 0; font-size: 0.9em; font-style: italic;">{scenario_description}</p>
        </div>
        """,
        sizing_mode="stretch_width",
    )

    # Create layout
    if singleplot:
        layout = column(header, *plots, sizing_mode="stretch_width")
    else:
        layout = column(header, *plots[:3], sizing_mode="stretch_width")

        # Add hover tools and improve styling
    for p in plots:
        # Add hover tool specific to each plot
        if p == p1:  # Electricity source plot
            hover = HoverTool(
                tooltips=[
                    ("Hour", "@hours"),
                    ("Total Demand", "@total_demand{0.2f} MW"),
                    ("CHP Output", "@chp_output{0.2f} MW"),
                    ("Offtake", "@offtake{0.2f} MW"),
                ],
                mode="vline",
            )
        elif p == p2:  # Electricity sink plot
            hover = HoverTool(
                tooltips=[
                    ("Hour", "@hours"),
                    ("Base Demand", "@base_demand{0.2f} MW"),
                    ("E-boiler", "@eboiler{0.2f} MW"),
                    ("Injection", "@injection{0.2f} MW"),
                ],
                mode="vline",
            )
        elif p == p3:  # Prices plot
            hover = HoverTool(
                tooltips=[
                    ("Hour", "@hours"),
                    ("Elec Offtake Price", "@elec_offtake_price{0.2f} EUR/MWh"),
                    ("Gas Offtake Price", "@gas_offtake_price{0.2f} EUR/MWh"),
                    ("Elec Injection Price", "@elec_injection_price{0.2f} EUR/MWh"),
                ],
                mode="vline",
            )
        else:  # Heat source plot (p4)
            hover = HoverTool(
                tooltips=[
                    ("Hour", "@hours"),
                    ("Heat Demand", "@heat_demand{0.2f} MW"),
                    ("CHP Thermal", "@chp_thermal{0.2f} MW"),
                    ("Gas Boiler", "@gas_boiler{0.2f} MW"),
                    ("E-boiler", "@eboiler_heat{0.2f} MW"),
                ],
                mode="vline",
            )
        p.add_tools(hover)

        # Improve plot styling
        p.background_fill_color = "#f8f9fa"
        p.border_fill_color = "#ffffff"
        p.grid.grid_line_color = "#e9ecef"
        p.grid.grid_line_alpha = 0.7
        p.axis.axis_line_color = "#dee2e6"
        p.axis.major_tick_line_color = "#dee2e6"
        p.axis.minor_tick_line_color = "#e9ecef"
        p.axis.axis_label_text_font_size = "12pt"
        p.axis.major_label_text_font_size = "10pt"
        p.title.text_font_size = "14pt"
        p.title.text_font_style = "bold"

        # Set box zoom as the default active tool (disable wheel zoom)
        p.toolbar.active_scroll = None
        # Find and activate the BoxZoomTool instance
        for tool in p.tools:
            if isinstance(tool, BoxZoomTool):
                p.toolbar.active_drag = tool
                break

        # Enable interactive legend (click to hide/show glyphs)
        p.legend.click_policy = "hide"

    # Show or save the plot
    if output_filename:
        save(layout)
        print(f"Plot saved to {output_filename}")
    else:
        show(layout)

    return layout


def read_scenario_descriptions():
    """Read scenario descriptions from the scenarios.json file."""
    import json

    scenarios_file = "simulation/scenarios.json"
    if not os.path.exists(scenarios_file):
        print(f"Warning: {scenarios_file} not found")
        return {}

    try:
        with open(scenarios_file, "r") as f:
            data = json.load(f)

        descriptions = {}
        for scenario_name, scenario_data in data.items():
            if isinstance(scenario_data, dict) and "description" in scenario_data:
                descriptions[scenario_name] = scenario_data["description"]

        return descriptions
    except Exception as e:
        print(f"Error reading scenario descriptions: {e}")
        return {}


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


# Main execution
if __name__ == "__main__":
    scenarios = list_available_scenarios()
    print("Available scenarios:", scenarios)

    # Read scenario descriptions
    scenario_descriptions = read_scenario_descriptions()
    print(f"Loaded descriptions for {len(scenario_descriptions)} scenarios")

    # Loop through each scenario and create HTML files
    for scenario_name in scenarios:
        try:
            print(f"\nProcessing scenario: {scenario_name}")

            # Load data for this scenario
            df, scenario, dt = load_results_df(scenario_name)

            # Get scenario description
            scenario_description = scenario_descriptions.get(
                scenario_name, "No description available"
            )

            # Create filename based on scenario name and save in scenario folder
            if scenario_name == "default":
                # For default scenario, save in root results folder
                filename = f"results/kronos_results_{scenario_name}.html"
            else:
                # For other scenarios, save in their respective folders
                filename = (
                    f"results/{scenario_name}/kronos_results_{scenario_name}.html"
                )

            # Create interactive Bokeh plot
            plot_results_bokeh(
                df,
                scenario,
                dt,
                singleplot=True,
                output_filename=filename,
                scenario_description=scenario_description,
            )

            print(f"Successfully created: {filename}")

        except Exception as e:
            print(f"Error processing scenario '{scenario_name}': {str(e)}")
            continue

    print(f"\nCompleted! Created HTML files for {len(scenarios)} scenarios.")

    # Alternative: show in browser without saving
    # plot_results_bokeh(df, scenario, dt, singleplot=True)
