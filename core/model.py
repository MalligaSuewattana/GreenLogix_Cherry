import pandas as pd
import model_to_flex.component_library as components
from model_to_flex.core.Model import model
from model_to_flex.core.enums import VariableType
from typing import Dict, Any

# gas turbine in min load is always running
gas_turbine_minload_electricity = components.Conversion(
    "gas_turbine_minload_electricity", conversion_factor=0.4
)
gas_turbine_minload_heat = components.Conversion(
    "gas_turbine_minload_heat", conversion_factor=0.6
)

# values for max load are differential to min load (eff = delta_output / delta_input)
gas_turbine_maxload_electricity = components.Conversion(
    "gas_turbine_maxload_electricity", conversion_factor=0.4
)
gas_turbine_maxload_heat = components.Conversion(
    "gas_turbine_maxload_heat", conversion_factor=0.6
)

gas_boiler = components.Conversion("gas_boiler", conversion_factor=1.0)
e_boiler = components.Conversion("e_boiler", conversion_factor=1.0)
hrsg = components.Conversion("hrsg", conversion_factor=1.0)

electricity_offtake = components.Market("Electricity offtake", quantities_lbounds=0)
electricity_offtake.vars["quantities"].type = VariableType.VARIABLE
electricity_injection = components.Market("Electricity injection", quantities_lbounds=0)
electricity_injection.vars["quantities"].type = VariableType.VARIABLE

gas_offtake = components.Market("Gas offtake", quantities_lbounds=0)
gas_offtake.vars["quantities"].type = VariableType.VARIABLE

CO2_allowance = components.Market("CO2 allowance", quantities_lbounds=0)
CO2_allowance.vars["quantities"].type = VariableType.VARIABLE

CO2_emission = components.Conversion("CO2_emission", conversion_factor=0.1824)

heat_demand = components.Demand("heat_demand")
electricity_demand = components.Demand("electricity_demand")

heat_supply = components.Summation("heat_supply", 5)
electricity_consumption = components.Summation("electricity_consumption", 3)
gas_consumption = components.Splitter("gas_consumption", 4)
electricity_supply = components.Splitter("electricity_supply", 3)

# Adding the components to the model
m = model.Model()
m.add(gas_turbine_minload_electricity)
m.add(gas_turbine_minload_heat)
m.add(gas_turbine_maxload_electricity)
m.add(gas_turbine_maxload_heat)
m.add(gas_boiler)
m.add(hrsg)
m.add(e_boiler)
m.add(electricity_offtake)
m.add(electricity_injection)
m.add(gas_offtake)
m.add(heat_demand)
m.add(electricity_demand)
m.add(heat_supply)
m.add(electricity_consumption)
m.add(gas_consumption)
m.add(electricity_supply)
m.add(CO2_allowance)
m.add(CO2_emission)


# Defining the relations between the components
m.connect(gas_offtake.vars["quantities"], gas_consumption.vars["input"])
m.connect(gas_consumption.vars["output0"], gas_boiler.vars["input"])
m.connect(
    gas_consumption.vars["output1"], gas_turbine_minload_electricity.vars["input"]
)
m.connect(gas_consumption.vars["output1"], gas_turbine_minload_heat.vars["input"])
m.connect(
    gas_consumption.vars["output2"], gas_turbine_maxload_electricity.vars["input"]
)
m.connect(gas_consumption.vars["output2"], gas_turbine_maxload_heat.vars["input"])
m.connect(gas_consumption.vars["output3"], hrsg.vars["input"])

m.connect(gas_offtake.vars["quantities"], CO2_emission.vars["input"])
m.connect(CO2_emission.vars["output"], CO2_allowance.vars["quantities"])

m.connect(gas_turbine_minload_heat.vars["output"], heat_supply.vars["input0"])
m.connect(gas_turbine_maxload_heat.vars["output"], heat_supply.vars["input1"])
m.connect(gas_boiler.vars["output"], heat_supply.vars["input2"])
m.connect(e_boiler.vars["output"], heat_supply.vars["input3"])
m.connect(hrsg.vars["output"], heat_supply.vars["input4"])
m.connect(heat_supply.vars["output"], heat_demand.vars["supply"])

m.connect(
    electricity_offtake.vars["quantities"], electricity_consumption.vars["input0"]
)
m.connect(
    gas_turbine_minload_electricity.vars["output"],
    electricity_consumption.vars["input1"],
)
m.connect(
    gas_turbine_maxload_electricity.vars["output"],
    electricity_consumption.vars["input2"],
)
m.connect(electricity_consumption.vars["output"], electricity_supply.vars["input"])
m.connect(electricity_supply.vars["output0"], electricity_demand.vars["supply"])
m.connect(electricity_supply.vars["output1"], e_boiler.vars["input"])
m.connect(electricity_supply.vars["output2"], electricity_injection.vars["quantities"])


def set_data(model: model.Model, df: pd.DataFrame):
    if "offtake_price" in df.columns:
        model.get_component("Electricity offtake").vars["prices"].set_values(
            df["offtake_price"].to_list()
        )
    if "injection_price" in df.columns:
        model.get_component("Electricity injection").vars["prices"].set_values(
            df["injection_price"].to_list()
        )
    if "gas_price" in df.columns:
        model.get_component("Gas offtake").vars["prices"].set_values(
            df["gas_price"].to_list()
        )
    if "co2_price" in df.columns:
        model.get_component("CO2 allowance").vars["prices"].set_values(
            df["co2_price"].to_list()
        )
    if "heat_demand" in df.columns:
        model.get_component("heat_demand").vars["demand"].set_values(
            df["heat_demand"].to_list()
        )
    if "electricity_demand" in df.columns:
        model.get_component("electricity_demand").vars["demand"].set_values(
            df["electricity_demand"].to_list()
        )
    # Temperature dependent efficiencies
    if "gas_turbine_minload_electricity_efficiency" in df.columns:
        model.get_component("gas_turbine_minload_electricity").set_conversion_factor(
            df["gas_turbine_minload_electricity_efficiency"].to_list()
        )
    if "gas_turbine_maxload_electricity_efficiency" in df.columns:
        model.get_component("gas_turbine_maxload_electricity").set_conversion_factor(
            df["gas_turbine_maxload_electricity_efficiency"].to_list()
        )

    # Set turbine capacities
    if "gas_turbine_minload_electricity_capacity" in df.columns:
        model.get_component("gas_turbine_minload_electricity").set_bounds(
            "output",
            lbound=df["gas_turbine_minload_electricity_capacity"].to_list(),
            ubound=df["gas_turbine_minload_electricity_capacity"].to_list(),
        )
    if "gas_turbine_maxload_electricity_capacity" in df.columns:
        model.get_component("gas_turbine_maxload_electricity").set_bounds(
            "output",
            lbound=0,
            ubound=df["gas_turbine_maxload_electricity_capacity"].to_list(),
        )

    if "hrsg_capacity" in df.columns:
        model.get_component("hrsg").set_bounds(
            "output",
            lbound=0,
            ubound=df["hrsg_capacity"].to_list(),
        )


def set_parameters(model: model.Model, params: Dict[str, Any]):
    # gas turbine
    if "gas_turbine_minload_heat_efficiency" in params:
        model.get_component("gas_turbine_minload_heat").set_conversion_factor(
            params["gas_turbine_minload_heat_efficiency"]
        )
    if "gas_turbine_maxload_heat_efficiency" in params:
        model.get_component("gas_turbine_maxload_heat").set_conversion_factor(
            params["gas_turbine_maxload_heat_efficiency"]
        )

    # hrsg
    if "hrsg_efficiency" in params:
        model.get_component("hrsg").set_conversion_factor(params["hrsg_efficiency"])

    # gas boiler
    if "gas_boiler_efficiency" in params:
        model.get_component("gas_boiler").set_conversion_factor(
            params["gas_boiler_efficiency"]
        )
    if "gas_boiler_capacity" in params:
        model.get_component("gas_boiler").set_bounds(
            "output",
            lbound=0,
            ubound=params["gas_boiler_capacity"],
        )

    # e-boiler
    if "e_boiler_efficiency" in params:
        model.get_component("e_boiler").set_conversion_factor(
            params["e_boiler_efficiency"]
        )
    if "e_boiler_capacity" in params:
        model.get_component("e_boiler").set_bounds(
            "output",
            lbound=0,
            ubound=params["e_boiler_capacity"],
        )


# Bind methods to the model instance
m.set_set_data_method(set_data)
m.set_set_parameters_method(set_parameters)


def get_model():
    return m
