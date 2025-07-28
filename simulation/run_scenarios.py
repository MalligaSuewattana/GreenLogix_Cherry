import os

os.chdir(Path(__file__).parent.parent)
print(f"Working directory: {os.getcwd()}")

from datetime import datetime
from simulation.scenarios import Scenario, ScenarioManager
from simulation.define_scenarios import define_scenarios
from core.data_generator import get_data
from core.model_bis import get_model

# import kronos
from model_to_flex.core.dispatch import dispatch
from model_to_flex.core.io_utils.save_results import save_results


def run_scenario(scenario_name: str):
    """Run a specific scenario"""
    # Load scenario
    manager = ScenarioManager()
    scenario = manager.get_scenario(scenario_name)

    if scenario is None:
        print(f"Scenario '{scenario_name}' not found!")
        return

    print(f"Running scenario: {scenario.name}")
    print(f"Description: {scenario.description}")

    # Generate data
    print("Generating data...")
    data = get_data(
        price_starttime=scenario.price_starttime,
        demand_starttime=scenario.demand_starttime,
        length=scenario.length,
        freq=scenario.freq,
        save_to_csv=False,
        use_local_data=True,
    )
    print("Data generated")

    # pring all scenario attributes
    for k, v in scenario.__dict__.items():
        print(f"{k}: {v}")

    data["electricity_offtake_price"] = (
        (
            scenario.elec_offtake_contract_param_a * data["da_price"]
            + scenario.elec_offtake_contract_param_b
        )
        + scenario.elec_grid_cost_energy
        + scenario.elec_offtake_tax_energy
        # + scenario.elec_grid_cost_max_tariff
    )
    data["electricity_injection_price"] = -(
        scenario.elec_injection_contract_param_a * data["da_price"]
        - scenario.elec_injection_contract_param_b
    )
    data["gas_price"] = (
        scenario.gas_offtake_contract_param_a * data["gas_price"]
        + scenario.gas_offtake_contract_param_b
    ) + scenario.gas_grid_cost_energy

    # Load model
    print("Loading model...")
    model = get_model()
    print("Model loaded")

    # Prepare dispatch options
    print("Preparing dispatch options...")
    dispatch_opts = {
        "optimizer_type": scenario.optimizer_type,
        "builder_type": scenario.builder_type,
        "solver": scenario.solver,
        "dispatch_type": scenario.dispatch_type,
        "pred_hor": scenario.pred_hor,
        "contr_hor": scenario.contr_hor,
    }
    print("Dispatch options prepared")

    # Prepare parameters
    print("Preparing parameters...")
    params = {
        "gas_turbine_minload_heat_efficiency": scenario.gas_turbine_minload_heat_efficiency,
        "gas_turbine_maxload_heat_efficiency": scenario.gas_turbine_maxload_heat_efficiency,
        "gas_boiler_efficiency": scenario.gas_boiler_efficiency,
        "gas_boiler_capacity": scenario.gas_boiler_capacity,
        "e_boiler_efficiency": scenario.e_boiler_efficiency,
        "e_boiler_capacity": scenario.e_boiler_capacity,
        "hrsg_efficiency": scenario.hrsg_efficiency,
        "elec_grid_cost_power_peak": scenario.elec_grid_cost_power_peak,
    }

    # Calculate temperature scaling and low demand conditions

    temperature_scaling = (6.550 - 0.045 * (data["temperature"])) / 6.550

    # low_electricity_demand = (
    #     data["electricity_demand"] < scenario.gas_turbine_minload_electricity_capacity
    # )
    low_heat_demand = (
        data["heat_demand"]
        < scenario.gas_turbine_minload_electricity_capacity
        / scenario.gas_turbine_minload_electricity_efficiency
        * scenario.gas_turbine_minload_heat_efficiency
    )
    # low_demand = low_electricity_demand | low_heat_demand
    low_demand = low_heat_demand

    data["low_demand"] = low_demand

    # Set temperature dependent efficiencies
    data["gas_turbine_minload_electricity_efficiency"] = (
        scenario.gas_turbine_minload_electricity_efficiency
    )
    data["gas_turbine_maxload_electricity_efficiency"] = (
        scenario.gas_turbine_maxload_electricity_efficiency
    )

    # Set capacities with temperature scaling and low demand conditions
    data["gas_turbine_minload_electricity_capacity"] = (
        scenario.gas_turbine_minload_electricity_capacity
        # * (~low_demand)
        * temperature_scaling
    )
    data["gas_turbine_maxload_electricity_capacity"] = (
        scenario.gas_turbine_maxload_electricity_capacity
        # * (~low_demand)
        * temperature_scaling
    )
    # data["hrsg_capacity"] = scenario.hrsg_capacity * (~low_demand)
    data["hrsg_capacity"] = scenario.hrsg_capacity
    data["max_gas_to_aux_firing"] = data["hrsg_capacity"] / scenario.hrsg_efficiency

    # (
    #     (
    #         scenario.hrsg_capacity
    #         + (
    #             data["gas_turbine_minload_electricity_capacity"]
    #             + data["gas_turbine_maxload_electricity_capacity"]
    #         )
    #         / data["gas_turbine_maxload_electricity_efficiency"]
    #     )
    #     / scenario.hrsg_efficiency
    # ) - (
    #     (
    #         data["gas_turbine_minload_electricity_capacity"]
    #         + data["gas_turbine_maxload_electricity_capacity"]
    #     )
    #     / data["gas_turbine_maxload_electricity_efficiency"] * params["gas_turbine_maxload_heat_efficiency"]
    # )

    # penalty to prevent the CHP to be used
    if scenario.name in [
        "Flex_0",
        "Flex_4",
        "Flex_5.1",
        "Flex_5.11",
        "Flex_5.2",
        "Flex_5.3",
    ]:
        params["penalty_for_gas_to_turbine"] = -100000
    else:
        params["penalty_for_gas_to_turbine"] = 0

    # penalty to prevent the CHP from shutting down; only modulation possible.
    if scenario.name in [
        "Flex_0",
        "Flex_1.1",
        "Flex_1.2",
        "Flex_1.3",
        "Flex_1.4",
        "Flex_1.5",
    ]:
        params["penalty_turbine_no_shutdown"] = -100000
    else:
        params["penalty_turbine_no_shutdown"] = 0

    # Run dispatch
    solved_model = dispatch(
        model,
        params,
        data,
        **dispatch_opts,
    )

    kpis = solved_model.KPIs
    results = solved_model.results

    # Add low demand data to results
    results["low_demand"] = data["low_demand"]

    # Create timestamp for results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = os.path.join("results", scenario.name)
    os.makedirs(results_dir, exist_ok=True)

    # Save results
    results_path = os.path.join(results_dir, f"results_{timestamp}")
    save_results(
        results=results,
        path=results_dir,
        filename=f"results_{timestamp}",
        sheetnames=["Timeseries"],
        overwrite=True,
    )

    # Update scenario with results path
    manager.update_scenario(scenario.name, results_path=results_path)

    print(f"Scenario completed. Results saved to: {results_path}")
    return kpis, results


def run_all_scenarios():
    """Run all defined scenarios"""
    manager = ScenarioManager()
    scenarios = manager.list_scenarios()

    if not scenarios:
        print("No scenarios defined!")
        return

    print("Running all scenarios:")
    failed_scenarios = []

    for name in scenarios:
        print(f"\nRunning scenario: {name}")
        try:
            run_scenario(name)
            print(f"✓ Scenario '{name}' completed successfully")
        except Exception as e:
            print(f"✗ Scenario '{name}' failed with error: {str(e)}")
            failed_scenarios.append((name, str(e)))
            print(f"Continuing with remaining scenarios...")

    # Summary at the end
    print(f"\n{'=' * 50}")
    print("SCENARIO EXECUTION SUMMARY")
    print(f"{'=' * 50}")

    successful_count = len(scenarios) - len(failed_scenarios)
    print(f"Successfully completed: {successful_count}/{len(scenarios)} scenarios")

    if failed_scenarios:
        print(f"\nFailed scenarios:")
        for name, error in failed_scenarios:
            print(f"  - {name}: {error}")
    else:
        print("All scenarios completed successfully!")


if __name__ == "__main__":
    import sys

    # Check if running in Jupyter notebook
    is_notebook = "ipykernel" in sys.modules

    if is_notebook:
        run_all_scenarios()
        # run_scenario("Flex_1.1")
    else:
        # In command line, use argument parsing
        import argparse

        parser = argparse.ArgumentParser(description="Run simulation scenarios")
        parser.add_argument(
            "--scenario",
            type=str,
            help="Name of the scenario to run. If not provided, all scenarios will be run.",
        )
        args = parser.parse_args()

        if args.scenario:
            run_scenario(args.scenario)
        else:
            run_all_scenarios()
