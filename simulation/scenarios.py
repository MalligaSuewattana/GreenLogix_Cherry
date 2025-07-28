from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
import json
import os
from model_to_flex.core.enums import BuilderType, SolverType, DispatchType


@dataclass
class Scenario:
    """Class to define a simulation scenario"""

    # Required parameters (no defaults)
    name: str
    description: str
    price_starttime: str
    demand_starttime: str
    length: int
    gas_turbine_minload_electricity_capacity: float
    gas_turbine_maxload_electricity_capacity: float
    gas_turbine_minload_electricity_efficiency: float
    gas_turbine_maxload_electricity_efficiency: float
    gas_turbine_minload_heat_efficiency: float
    gas_turbine_maxload_heat_efficiency: float
    gas_boiler_efficiency: float
    gas_boiler_capacity: int
    e_boiler_efficiency: float
    e_boiler_capacity: int
    hrsg_efficiency: int
    hrsg_capacity: int
    elec_offtake_contract_param_a: float
    elec_offtake_contract_param_b: float
    elec_injection_contract_param_a: float
    elec_injection_contract_param_b: float
    elec_grid_cost_energy: float
    elec_grid_cost_power_peak: float
    elec_grid_cost_power_fixed: float
    elec_grid_cost_max_tariff: float
    elec_offtake_tax_energy: float
    gas_offtake_contract_param_a: float
    gas_offtake_contract_param_b: float
    gas_grid_cost_energy: float

    # Optional parameters (with defaults)
    freq: str = "h"
    optimizer_type: str = "default"
    builder_type: BuilderType = BuilderType.PYOMO
    solver: SolverType = SolverType.CBC
    dispatch_type: DispatchType = DispatchType.MONTHLY
    pred_hor: int = 24 * 32
    contr_hor: int = 24 * 32
    created_at: str = None
    results_path: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario to dictionary for saving"""
        return {
            "name": self.name,
            "description": self.description,
            "price_starttime": self.price_starttime,
            "demand_starttime": self.demand_starttime,
            "length": self.length,
            "freq": self.freq,
            "gas_turbine_minload_electricity_capacity": self.gas_turbine_minload_electricity_capacity,
            "gas_turbine_maxload_electricity_capacity": self.gas_turbine_maxload_electricity_capacity,
            "gas_turbine_minload_electricity_efficiency": self.gas_turbine_minload_electricity_efficiency,
            "gas_turbine_maxload_electricity_efficiency": self.gas_turbine_maxload_electricity_efficiency,
            "gas_turbine_minload_heat_efficiency": self.gas_turbine_minload_heat_efficiency,
            "gas_turbine_maxload_heat_efficiency": self.gas_turbine_maxload_heat_efficiency,
            "gas_boiler_efficiency": self.gas_boiler_efficiency,
            "gas_boiler_capacity": self.gas_boiler_capacity,
            "e_boiler_efficiency": self.e_boiler_efficiency,
            "e_boiler_capacity": self.e_boiler_capacity,
            "hrsg_efficiency": self.hrsg_efficiency,
            "hrsg_capacity": self.hrsg_capacity,
            "elec_offtake_contract_param_a": self.elec_offtake_contract_param_a,
            "elec_offtake_contract_param_b": self.elec_offtake_contract_param_b,
            "elec_injection_contract_param_a": self.elec_injection_contract_param_a,
            "elec_injection_contract_param_b": self.elec_injection_contract_param_b,
            "elec_grid_cost_energy": self.elec_grid_cost_energy,
            "elec_grid_cost_power_peak": self.elec_grid_cost_power_peak,
            "elec_grid_cost_power_fixed": self.elec_grid_cost_power_fixed,
            "elec_grid_cost_max_tariff": self.elec_grid_cost_max_tariff,
            "elec_offtake_tax_energy": self.elec_offtake_tax_energy,
            "gas_offtake_contract_param_a": self.gas_offtake_contract_param_a,
            "gas_offtake_contract_param_b": self.gas_offtake_contract_param_b,
            "gas_grid_cost_energy": self.gas_grid_cost_energy,
            "dispatch_options": {
                "optimizer_type": self.optimizer_type,
                "builder_type": self.builder_type.value,
                "solver": self.solver.value,
                "dispatch_type": self.dispatch_type.value,
                "pred_hor": self.pred_hor,
                "contr_hor": self.contr_hor,
            },
            "metadata": {
                "created_at": self.created_at,
                "results_path": self.results_path,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scenario":
        """Create a scenario from a dictionary"""
        dispatch_options = data.pop("dispatch_options", {})
        metadata = data.pop("metadata", {})

        # Handle old structure with equipment_params
        equipment_params = data.pop("equipment_params", {})
        if equipment_params:
            # Migrate old structure to new flat structure
            data.update(equipment_params)

        # Convert enum strings back to enum values
        dispatch_options["builder_type"] = BuilderType(dispatch_options["builder_type"])
        dispatch_options["solver"] = SolverType(dispatch_options["solver"])
        dispatch_options["dispatch_type"] = DispatchType(
            dispatch_options["dispatch_type"]
        )

        # Add default values for new required parameters if they don't exist
        defaults = {
            "elec_offtake_contract_param_a": 1.0,
            "elec_offtake_contract_param_b": 0.0,
            "elec_injection_contract_param_a": 1.0,
            "elec_injection_contract_param_b": 0.0,
            "elec_grid_cost_energy": 0.0,
            "elec_grid_cost_power_peak": 0.0,
            "elec_grid_cost_power_fixed": 0.0,
            "elec_grid_cost_max_tariff": 0.0,
            "elec_offtake_tax_energy": 0.0,
            "gas_offtake_contract_param_a": 1.0,
            "gas_offtake_contract_param_b": 0.0,
            "gas_grid_cost_energy": 0.0,
        }

        # Update data with defaults for missing keys
        for key, default_value in defaults.items():
            if key not in data:
                data[key] = default_value

        # Create scenario with all parameters
        return cls(**data, **dispatch_options, **metadata)


class ScenarioManager:
    """Class to manage simulation scenarios"""

    def __init__(self, scenarios_file: str = "simulation/scenarios.json"):
        self.scenarios_file = scenarios_file
        self.scenarios: Dict[str, Scenario] = {}
        self.load_scenarios()

    def load_scenarios(self):
        """Load scenarios from file"""
        if os.path.exists(self.scenarios_file):
            with open(self.scenarios_file, "r") as f:
                data = json.load(f)
                self.scenarios = {
                    name: Scenario.from_dict(scenario_data)
                    for name, scenario_data in data.items()
                }

    def save_scenarios(self):
        """Save scenarios to file"""
        data = {name: scenario.to_dict() for name, scenario in self.scenarios.items()}
        with open(self.scenarios_file, "w") as f:
            json.dump(data, f, indent=2)

    def add_scenario(self, scenario: Scenario):
        """Add a new scenario"""
        self.scenarios[scenario.name] = scenario
        self.save_scenarios()

    def get_scenario(self, name: str) -> Optional[Scenario]:
        """Get a scenario by name"""
        return self.scenarios.get(name)

    def list_scenarios(self) -> Dict[str, str]:
        """List all scenarios with their descriptions"""
        return {name: scenario.description for name, scenario in self.scenarios.items()}

    def update_scenario(self, name: str, **kwargs):
        """Update an existing scenario"""
        if name in self.scenarios:
            scenario = self.scenarios[name]
            for key, value in kwargs.items():
                setattr(scenario, key, value)
            self.save_scenarios()

    def delete_scenario(self, name: str):
        """Delete a scenario"""
        if name in self.scenarios:
            del self.scenarios[name]
            self.save_scenarios()


# Example usage:
if __name__ == "__main__":
    # Create a scenario manager
    manager = ScenarioManager()

    # Define a base scenario
    base_scenario = Scenario(
        name="base_case",
        description="Base case scenario with current equipment parameters",
        price_starttime="2025-01-01",
        demand_starttime="2022-01-01",
        length=24 * 30,
        gas_turbine_minload_electricity_capacity=6.55 / 2,
        gas_turbine_maxload_electricity_capacity=6.55 / 2,
        gas_turbine_minload_electricity_efficiency=0.31,
        gas_turbine_maxload_electricity_efficiency=0.31,
        gas_turbine_minload_heat_efficiency=0.46,
        gas_turbine_maxload_heat_efficiency=0.46,
        gas_boiler_efficiency=0.85,
        gas_boiler_capacity=26,
        e_boiler_efficiency=1.0,
        e_boiler_capacity=10,
        hrsg_efficiency=1.0,
        hrsg_capacity=10,
        elec_offtake_contract_param_a=0.0,
        elec_offtake_contract_param_b=0.0,
        elec_injection_contract_param_a=0,
        elec_injection_contract_param_b=0.0,
        elec_grid_cost_energy=0.0,
        elec_grid_cost_power_peak=0.0,
        elec_grid_cost_power_fixed=0.0,
        elec_grid_cost_max_tariff=0.0,
        elec_offtake_tax_energy=0.0,
        gas_offtake_contract_param_a=0,
        gas_offtake_contract_param_b=0.0,
        gas_grid_cost_energy=0,
    )

    # Add the scenario
    manager.add_scenario(base_scenario)

    # List all scenarios
    print("Available scenarios:")
    for name, description in manager.list_scenarios().items():
        print(f"- {name}: {description}")
