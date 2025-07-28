import os
import sys
from pathlib import Path
import pandas as pd
from simulation.scenarios import Scenario, ScenarioManager


def define_scenarios():
    # Create a scenario manager
    manager = ScenarioManager()

    # Read scenarios from Excel
    excel_path = Path("simulation/Scenarios.xlsx")
    df = pd.read_excel(excel_path, sheet_name=0)

    # For each row, create a Scenario and add to manager
    for _, row in df.iterrows():
        scenario = Scenario(
            name=row["Name"],
            description=row["description"],
            price_starttime=row["price_starttime"],
            demand_starttime=row["demand_starttime"],
            length=int(row["length"]),
            gas_turbine_minload_electricity_capacity=float(
                row["gas_turbine_minload_electricity_capacity"]
            ),
            gas_turbine_maxload_electricity_capacity=float(
                row["gas_turbine_maxload_electricity_capacity"]
            ),
            gas_turbine_minload_electricity_efficiency=float(
                row["gas_turbine_minload_electricity_efficiency"]
            ),
            gas_turbine_maxload_electricity_efficiency=float(
                row["gas_turbine_maxload_electricity_efficiency"]
            ),
            gas_turbine_minload_heat_efficiency=float(
                row["gas_turbine_minload_heat_efficiency"]
            ),
            gas_turbine_maxload_heat_efficiency=float(
                row["gas_turbine_maxload_heat_efficiency"]
            ),
            gas_boiler_efficiency=float(row["gas_boiler_efficiency"]),
            gas_boiler_capacity=int(row["gas_boiler_capacity"]),
            e_boiler_efficiency=float(row["e_boiler_efficiency"]),
            e_boiler_capacity=int(row["e_boiler_capacity"]),
            hrsg_efficiency=int(row["hrsg_efficiency"]),
            hrsg_capacity=int(row["hrsg_capacity"]),
            elec_offtake_contract_param_a=float(row["elec_offtake_contract_param_a"]),
            elec_offtake_contract_param_b=float(row["elec_offtake_contract_param_b"]),
            elec_injection_contract_param_a=int(row["elec_injection_contract_param_a"]),
            elec_injection_contract_param_b=float(
                row["elec_injection_contract_param_b"]
            ),
            elec_grid_cost_energy=float(row["elec_grid_cost_energy"]),
            elec_grid_cost_power_peak=float(row["elec_grid_cost_power_peak"]),
            elec_grid_cost_power_fixed=float(row["elec_grid_cost_power_fixed"]),
            elec_grid_cost_max_tariff=float(row["elec_grid_cost_max_tariff"]),
            elec_offtake_tax_energy=float(row["elec_offtake_tax_energy"]),
            gas_offtake_contract_param_a=int(row["gas_offtake_contract_param_a"]),
            gas_offtake_contract_param_b=float(row["gas_offtake_contract_param_b"]),
            gas_grid_cost_energy=int(row["gas_grid_cost_energy"]),
        )
        manager.add_scenario(scenario)

    # Print all defined scenarios
    print("\nDefined scenarios:")
    for name, description in manager.list_scenarios().items():
        print(f"- {name}: {description}")

    return manager


if __name__ == "__main__":
    # Check if running in Jupyter notebook
    is_notebook = "ipykernel" in sys.modules

    if is_notebook:
        # In Jupyter, just define scenarios and return the manager
        manager = define_scenarios()
    else:
        # In command line, just define scenarios
        define_scenarios()
