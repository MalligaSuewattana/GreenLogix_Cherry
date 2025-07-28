import pandas as pd
import os
from pathlib import Path
from typing import Optional, List, Dict

# Set pandas display options
pd.set_option("display.float_format", lambda x: "%.2f" % x)
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)


def read_results_file(
    scenario_name: str, file_name: Optional[str] = None
) -> pd.DataFrame:
    """
    Read a results file from the specified scenario into a pandas DataFrame.
    Can handle both scenario-based results and explicit file paths.

    Args:
        scenario_name (str): Either a scenario name (e.g., 'base_case', 'Flex_1') or a full path to a results file
        file_name (str, optional): Specific file name to read. If None, reads the most recent file.
            Only used when scenario_name is a scenario directory.

    Returns:
        pd.DataFrame: The results data
    """
    # Check if scenario_name is actually a full path to a file
    if os.path.isfile(scenario_name):
        return pd.read_excel(scenario_name)

    # If not a file, treat as scenario directory
    workspace_root = Path.cwd()
    results_dir = workspace_root / "results" / scenario_name

    if not results_dir.exists():
        raise ValueError(f"Scenario directory not found: {scenario_name}")

    if file_name is None:
        # Get the most recent file if no specific file is provided
        files = list(results_dir.glob("results_*.xlsx"))
        if not files:
            raise ValueError(f"No results files found in {scenario_name}")
        file_path = max(files, key=lambda x: x.stat().st_mtime)
    else:
        file_path = results_dir / file_name
        if not file_path.exists():
            raise ValueError(f"File not found: {file_name}")

    # Read the Excel file
    df = pd.read_excel(file_path)
    return df


def create_scenario_overview(
    scenario_name: str, file_name: Optional[str] = None
) -> Dict:
    """
    Create a comprehensive overview of simulation results for a specific scenario.

    Analyzes:
    - Total energy consumption per energy vector (gas, electricity) and per asset (CHP, gas boiler, e-boiler)
    - Total costs per energy vector and per asset

    Args:
        scenario_name (str): Scenario name to analyze
        file_name (str, optional): Specific file name to read. If None, reads the most recent file.

    Returns:
        Dict: Dictionary containing the overview data with energy consumption and costs breakdown
    """
    # Read the scenario data
    df = read_results_file(scenario_name, file_name)

    # Calculate totals for the entire period, excluding datetime column
    numeric_columns = df.select_dtypes(include=["number"]).columns
    totals = df[numeric_columns].sum()

    # Helper function to round values
    def round_value(value):
        if isinstance(value, (int, float)):
            if (
                pd.isna(value)
                or value != value
                or value == float("inf")
                or value == float("-inf")
            ):
                return 0
            return round(value)
        return value

    # Energy consumption analysis
    energy_consumption = {
        "per_energy_vector": {
            "Gas": {
                "Total": round_value(totals.get("Gas offtake_quantities", 0)),
                "Unit": "MWh",
            },
            "Electricity": {
                "Grid offtake": {
                    "Total offtake": round_value(
                        totals.get("Electricity offtake_quantities", 0)
                    ),
                    "Unit": "MWh",
                },
                "Grid injection": {
                    "Total injection": round_value(
                        totals.get("Electricity injection_quantities", 0)
                    ),
                    "Unit": "MWh",
                },
                "Consumption": {
                    "Total consumption": round_value(
                        totals.get("electricity_demand_demand", 0)
                        + totals.get("e_boiler_input", 0)
                    ),
                    "Unit": "MWh",
                },
                "Production": {
                    "Total production": round_value(
                        totals.get("chp_electricity_output", 0)
                    ),
                    "Unit": "MWh",
                },
            },
            "Heat": {
                "Total heat consumption": round_value(
                    totals.get("heat_demand_demand", 0)
                ),
                "Unit": "MWh",
            },
        },
        "per_asset": {
            "CHP": {
                "Gas": {
                    "Gas to turbine": round_value(totals.get("chp_gas_to_turbine", 0)),
                    "Gas to aux firing": round_value(
                        totals.get("chp_gas_to_aux_firing", 0)
                    ),
                    "Total gas consumption": round_value(
                        totals.get("chp_gas_to_turbine", 0)
                        + totals.get("chp_gas_to_aux_firing", 0)
                    ),
                    "Unit": "MWh",
                },
                "Electricity": {
                    "Electricity production": round_value(
                        totals.get("chp_electricity_output", 0)
                    ),
                    "Unit": "MWh",
                },
                "Heat": {
                    "Heat production": round_value(totals.get("chp_thermal_output", 0)),
                    "Unit": "MWh",
                },
            },
            "Gas Boiler": {
                "Gas": {
                    "Gas consumption": round_value(totals.get("gas_boiler_input", 0)),
                    "Unit": "MWh",
                },
                "Heat": {
                    "Heat production": round_value(totals.get("gas_boiler_output", 0)),
                    "Unit": "MWh",
                },
            },
            "E-Boiler": {
                "Electricity": {
                    "Electricity consumption": round_value(
                        totals.get("e_boiler_input", 0)
                    ),
                    "Unit": "MWh",
                },
                "Heat": {
                    "Heat production": round_value(totals.get("e_boiler_output", 0)),
                    "Unit": "MWh",
                },
            },
        },
    }

    co2_emissions = {
        "per_energy_vector": {
            "Gas": {
                "Total": round_value(totals.get("CO2 allowance_quantities", 0)),
                "Unit": "tonnes",
            },
        },
    }

    # Calculate 'toegangsvermogen' cost
    toegangsvermogen_cost = get_toegangsvermogen_cost(scenario_name)

    # Cost analysis
    costs = {
        "per_energy_vector": {
            "Gas": {
                "Total": round_value(totals.get("Gas offtake_costs", 0)),
                "Unit": "EUR",
            },
            "Electricity": {
                "Offtake": round_value(totals.get("Electricity offtake_costs", 0)),
                "Injection": round_value(totals.get("Electricity injection_costs", 0)),
                "Net": round_value(
                    totals.get("Electricity offtake_costs", 0)
                    + totals.get("Electricity injection_costs", 0)
                ),
                "Additional 'toegangsvermogen' costs": toegangsvermogen_cost,
                "Unit": "EUR",
            },
            "CO2 allowance": {
                "Total": round_value(totals.get("CO2 allowance_costs", 0)),
                "Unit": "EUR",
            },
        },
    }

    # Calculate total costs
    total_costs = round_value(
        costs["per_energy_vector"]["Gas"]["Total"]
        + costs["per_energy_vector"]["Electricity"]["Net"]
        + costs["per_energy_vector"]["Electricity"][
            "Additional 'toegangsvermogen' costs"
        ]
        + costs["per_energy_vector"]["CO2 allowance"]["Total"]
    )

    overview = {
        "scenario_name": scenario_name,
        "period": {
            "start": df.iloc[0, 0] if len(df) > 0 else None,
            "end": df.iloc[-1, 0] if len(df) > 0 else None,
            "total_hours": len(df),
        },
        "energy_consumption": energy_consumption,
        "co2_emissions": co2_emissions,
        "costs": costs,
        "total_costs": total_costs,
    }

    return overview


def print_scenario_overview(scenario_name: str, file_name: Optional[str] = None):
    """
    Print a formatted overview of simulation results for a specific scenario.

    Args:
        scenario_name (str): Scenario name to analyze
        file_name (str, optional): Specific file name to read. If None, reads the most recent file.
    """
    overview = create_scenario_overview(scenario_name, file_name)

    print(f"\n{'=' * 60}")
    print(f"SIMULATION OVERVIEW: {overview['scenario_name']}")
    print(f"{'=' * 60}")

    # Period information
    print(f"\nPeriod: {overview['period']['start']} to {overview['period']['end']}")
    print(f"Total hours: {overview['period']['total_hours']}")

    # Energy consumption
    print(f"\n{'ENERGY CONSUMPTION':^60}")
    print(f"{'-' * 60}")

    print(f"\nPer Energy Vector:")
    for vector, data in overview["energy_consumption"]["per_energy_vector"].items():
        if vector == "Electricity":
            print(f"  {vector}:")
            for subkey, subdata in data.items():
                if isinstance(subdata, dict):
                    for k, v in subdata.items():
                        if k != "Unit":
                            print(f"    {subkey}: {v:,} {subdata['Unit']}")
                else:
                    if subkey != "Unit":
                        print(f"    {subkey}: {subdata:,} {data['Unit']}")
        elif vector == "Heat":
            print(f"  {vector}:")
            for key, value in data.items():
                if key != "Unit":
                    print(f"    {key}: {value:,} {data['Unit']}")
        else:
            print(f"  {vector}: {data['Total']:,} {data['Unit']}")

    print(f"\nPer Asset:")
    for asset, data in overview["energy_consumption"]["per_asset"].items():
        print(f"  {asset}:")
        for energy_type, energy_data in data.items():
            print(f"    {energy_type}:")
            for key, value in energy_data.items():
                if key != "Unit":
                    print(f"      {key}: {value:,} {energy_data['Unit']}")

    # CO2 emissions
    print(f"\n{'CO2 EMISSIONS':^60}")
    print(f"{'-' * 60}")

    for vector, data in overview["co2_emissions"]["per_energy_vector"].items():
        print(f"  {vector}: {data['Total']:,} {data['Unit']}")

    # Costs
    print(f"\n{'COSTS':^60}")
    print(f"{'-' * 60}")

    print(f"\nPer Energy Vector:")
    for vector, data in overview["costs"]["per_energy_vector"].items():
        print(f"  {vector}:")
        for key, value in data.items():
            if key != "Unit":
                print(f"    {key}: {value:,} {data['Unit']}")

    print(f"\n{'SUMMARY':^60}")
    print(f"{'-' * 60}")
    print(f"Total Costs: {overview['total_costs']:,} EUR")
    print(f"{'=' * 60}")


def generate_all_scenario_overviews() -> Dict:
    """
    Generate overviews for all available simulation scenarios.

    Returns:
        Dict: Dictionary containing overviews for all scenarios
    """
    workspace_root = Path.cwd()
    results_dir = workspace_root / "results"

    if not results_dir.exists():
        raise ValueError(f"Results directory not found: {results_dir}")

    # Get all scenario directories
    scenario_dirs = [d for d in results_dir.iterdir() if d.is_dir()]
    scenario_names = [d.name for d in scenario_dirs]

    print(f"Found {len(scenario_names)} scenarios: {scenario_names}")

    all_overviews = {}

    for scenario_name in scenario_names:
        try:
            print(f"\nProcessing scenario: {scenario_name}")
            overview = create_scenario_overview(scenario_name)
            all_overviews[scenario_name] = overview
            print(f"✓ Successfully processed {scenario_name}")
        except Exception as e:
            print(f"✗ Error processing {scenario_name}: {e}")
            continue

    return all_overviews


def read_scenario_descriptions() -> Dict[str, str]:
    """
    Read scenario descriptions from the Scenarios.xlsx file.

    Returns:
        Dict[str, str]: Dictionary mapping scenario names to their descriptions
    """
    scenarios_file = Path("simulation/Scenarios.xlsx")

    if not scenarios_file.exists():
        print(f"Warning: Scenarios.xlsx not found at {scenarios_file}")
        return {}

    try:
        df = pd.read_excel(scenarios_file, sheet_name="Sheet1")

        # Create dictionary mapping scenario names to descriptions
        descriptions = {}
        for _, row in df.iterrows():
            scenario_name = row["Name"]
            description = row["description"] if pd.notna(row["description"]) else ""
            descriptions[scenario_name] = description

        print(f"Loaded descriptions for {len(descriptions)} scenarios")
        return descriptions

    except Exception as e:
        print(f"Error reading scenario descriptions: {e}")
        return {}


def export_overview_summary_to_excel(
    all_overviews: Dict, filename: str = "scenario_overview_summary.xlsx"
):
    """
    Export a summary of all scenario overviews to an Excel file.

    Args:
        all_overviews (Dict): Dictionary containing overviews for all scenarios
        filename (str): Name of the Excel file to create
    """
    workspace_root = Path.cwd()
    results_dir = workspace_root / "results"

    # Read scenario descriptions
    scenario_descriptions = read_scenario_descriptions()

    # Create summary data
    summary_data = []

    for scenario_name, overview in all_overviews.items():
        # Get description for this scenario
        description = scenario_descriptions.get(scenario_name, "")

        # Energy consumption summary
        energy_summary = {
            "Scenario": scenario_name,
            "Description": description,
            "Period Start": overview["period"]["start"],
            "Period End": overview["period"]["end"],
            "Total Hours": overview["period"]["total_hours"],
            # Energy consumption per vector
            "Gas Consumption (MWh)": overview["energy_consumption"][
                "per_energy_vector"
            ]["Gas"]["Total"],
            "Electricity Offtake (MWh)": overview["energy_consumption"][
                "per_energy_vector"
            ]["Electricity"]["Grid offtake"]["Total offtake"],
            "Electricity Injection (MWh)": overview["energy_consumption"][
                "per_energy_vector"
            ]["Electricity"]["Grid injection"]["Total injection"],
            "Electricity Consumption (MWh)": overview["energy_consumption"][
                "per_energy_vector"
            ]["Electricity"]["Consumption"]["Total consumption"],
            "Electricity Production (MWh)": overview["energy_consumption"][
                "per_energy_vector"
            ]["Electricity"]["Production"]["Total production"],
            "Heat Consumption (MWh)": overview["energy_consumption"][
                "per_energy_vector"
            ]["Heat"]["Total heat consumption"],
            # Energy consumption per asset
            "CHP Gas to Turbine (MWh)": overview["energy_consumption"]["per_asset"][
                "CHP"
            ]["Gas"]["Gas to turbine"],
            "CHP Gas to Aux Firing (MWh)": overview["energy_consumption"]["per_asset"][
                "CHP"
            ]["Gas"]["Gas to aux firing"],
            "CHP Total Gas (MWh)": overview["energy_consumption"]["per_asset"]["CHP"][
                "Gas"
            ]["Total gas consumption"],
            "CHP Electricity Production (MWh)": overview["energy_consumption"][
                "per_asset"
            ]["CHP"]["Electricity"]["Electricity production"],
            "CHP Heat Production (MWh)": overview["energy_consumption"]["per_asset"][
                "CHP"
            ]["Heat"]["Heat production"],
            "Gas Boiler Gas Consumption (MWh)": overview["energy_consumption"][
                "per_asset"
            ]["Gas Boiler"]["Gas"]["Gas consumption"],
            "Gas Boiler Heat Production (MWh)": overview["energy_consumption"][
                "per_asset"
            ]["Gas Boiler"]["Heat"]["Heat production"],
            "E-Boiler Electricity Consumption (MWh)": overview["energy_consumption"][
                "per_asset"
            ]["E-Boiler"]["Electricity"]["Electricity consumption"],
            "E-Boiler Heat Production (MWh)": overview["energy_consumption"][
                "per_asset"
            ]["E-Boiler"]["Heat"]["Heat production"],
            # CO2 emissions
            "CO2 Emissions (tonnes)": overview["co2_emissions"]["per_energy_vector"][
                "Gas"
            ]["Total"],
            # Costs
            "Gas Costs (EUR)": overview["costs"]["per_energy_vector"]["Gas"]["Total"],
            "Electricity Offtake Costs (EUR)": overview["costs"]["per_energy_vector"][
                "Electricity"
            ]["Offtake"],
            "Electricity Injection Costs (EUR)": overview["costs"]["per_energy_vector"][
                "Electricity"
            ]["Injection"],
            "Electricity Net Costs (EUR)": overview["costs"]["per_energy_vector"][
                "Electricity"
            ]["Net"],
            "Additional toegangsvermogen Costs (EUR)": overview["costs"][
                "per_energy_vector"
            ]["Electricity"]["Additional 'toegangsvermogen' costs"],
            "CO2 Allowance Costs (EUR)": overview["costs"]["per_energy_vector"][
                "CO2 allowance"
            ]["Total"],
            "Total Costs (EUR)": overview["total_costs"],
        }

        summary_data.append(energy_summary)

    # Create DataFrame and export to Excel
    df_summary = pd.DataFrame(summary_data)

    # Sort by scenario name
    df_summary = df_summary.sort_values("Scenario")

    # Export to Excel
    output_path = results_dir / filename
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        # Export summary data
        df_summary.to_excel(writer, sheet_name="Summary", index=False)

        # Export scenarios data from Scenarios.xlsx
        scenarios_file = Path("simulation/Scenarios.xlsx")
        if scenarios_file.exists():
            try:
                df_scenarios = pd.read_excel(scenarios_file, sheet_name="Sheet1")
                df_scenarios.to_excel(writer, sheet_name="Scenarios", index=False)
                print(f"✓ Added Scenarios tab with {len(df_scenarios)} rows")
            except Exception as e:
                print(f"Warning: Could not add Scenarios tab: {e}")
        else:
            print("Warning: Scenarios.xlsx not found, skipping Scenarios tab")

        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets["Summary"]

        # Apply comma style to numeric columns in Summary sheet
        for col_num, column in enumerate(df_summary.columns):
            # Check if the column contains numeric data (excluding the first few columns)
            if (
                col_num > 2
            ):  # Skip Scenario, Description, Period Start, Period End, Total Hours
                # Apply comma style to the entire column (excluding header)
                for row_num in range(
                    1, len(df_summary) + 1
                ):  # Start from row 1 (skip header)
                    cell = worksheet.cell(
                        row=row_num + 1, column=col_num + 1
                    )  # +1 for 1-based indexing
                    if cell.value is not None and isinstance(cell.value, (int, float)):
                        cell.number_format = "#,##0"

        # Auto-adjust column widths for Summary sheet
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

        # Auto-adjust column widths for Scenarios sheet if it exists
        if "Scenarios" in writer.sheets:
            scenarios_worksheet = writer.sheets["Scenarios"]
            for column in scenarios_worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                scenarios_worksheet.column_dimensions[
                    column_letter
                ].width = adjusted_width

    print(f"\n✓ Summary exported to: {output_path}")
    return output_path


def print_all_scenario_overviews():
    """
    Print overviews for all available simulation scenarios.
    """
    all_overviews = generate_all_scenario_overviews()

    for scenario_name, overview in all_overviews.items():
        print_scenario_overview(scenario_name)

    return all_overviews


def get_toegangsvermogen_cost(scenario_name: str) -> int:
    """
    Calculate the additional 'toegangsvermogen' cost for a scenario by reading
    elec_grid_cost_power_fixed and e_boiler_capacity from Scenarios.xlsx.
    Returns 0 if not found or on error.
    """
    scenarios_file = Path("simulation/Scenarios.xlsx")
    if not scenarios_file.exists():
        return 0
    try:
        df = pd.read_excel(scenarios_file, sheet_name="Sheet1")
        row = df[df["Name"] == scenario_name]
        if row.empty:
            return 0
        elec_grid_cost_power_fixed = row.iloc[0].get("elec_grid_cost_power_fixed", 0)
        e_boiler_capacity = row.iloc[0].get("e_boiler_capacity", 0)
        if pd.isna(elec_grid_cost_power_fixed) or pd.isna(e_boiler_capacity):
            return 0
        return round(elec_grid_cost_power_fixed * e_boiler_capacity * 1000 * 12)
    except Exception:
        return 0


# Example usage
if __name__ == "__main__":
    # Generate overviews for all scenarios and export summary
    print("Generating overviews for all scenarios...")
    all_overviews = generate_all_scenario_overviews()

    if all_overviews:
        print(f"\nExporting summary to Excel...")
        export_overview_summary_to_excel(all_overviews)

        print(f"\nGenerated overviews for {len(all_overviews)} scenarios:")
        for scenario_name in all_overviews.keys():
            print(f"  - {scenario_name}")
    else:
        print("No scenarios were successfully processed.")
