import pandas as pd
import model_to_flex.component_library as components
from model_to_flex.core.Model import model
from model_to_flex.core.enums import VariableType
from typing import Dict, Any

chp1 = components.CHP("chp1")
chp2 = components.CHP("chp2")


splitter1 = components.Splitter("splitter1", 3)
splitter2 = components.Splitter("splitter2", 2)
splitter3 = components.Splitter("splitter3", 2)

s1 = components.Summation("s1", 2)
s2 = components.Summation("s2", 2)
s3 = components.Summation("s3", 2)

balloon = components.Storage("balloon")
balloon.vars["charge"].type = VariableType.PARAM
heat_onsite_demand = components.Demand("heat_demand")
electricity_onsite_demand = components.Demand("electricity_demand")

electricity_offtake = components.Market(
    "Electricity offtake", quantities_lbounds=0, quantities_ubounds=10000
)
electricity_offtake.vars["quantities"].type = VariableType.VARIABLE
electricity_injection = components.Market("Electricity injection", quantities_lbounds=0)
electricity_injection.vars["quantities"].type = VariableType.VARIABLE



# Adding the components to the model
m = model.Model()
m.add(chp1)
m.add(chp2)
m.add(splitter1)
m.add(splitter2)
m.add(splitter3)
m.add(s1)
m.add(s2)
m.add(s3)
m.add(balloon)
m.add(heat_onsite_demand)
m.add(electricity_onsite_demand)
m.add(electricity_offtake)
m.add(electricity_injection)

# Defining the relations between the components
m.connect(balloon.vars["discharge"], splitter1.vars["input"])
m.connect(splitter1.vars["output0"], chp1.vars["gas_in"])
m.connect(splitter1.vars["output1"], chp2.vars["gas_in"])
# m.connect(splitter1.vars["output2"], balloon.vars["charge"]) #Flare is not used

m.connect(chp1.vars["electricity_output"], s1.vars["input0"])
m.connect(chp2.vars["electricity_output"], s1.vars["input1"])
m.connect(s1.vars["output"], splitter2.vars["input"])
m.connect(splitter2.vars["output0"], s2.vars["input0"])
m.connect(splitter2.vars["output1"], electricity_injection.vars["quantities"])
m.connect(electricity_offtake.vars["quantities"], s2.vars["input1"])
m.connect(s2.vars["output"], electricity_onsite_demand.vars["supply"])

m.connect(chp1.vars["thermal_output"], s3.vars["input0"])
m.connect(chp2.vars["thermal_output"], s3.vars["input1"])
m.connect(s3.vars["output"], splitter3.vars["input"])
m.connect(splitter3.vars["output0"], heat_onsite_demand.vars["supply"])

# chp.vars['is_starting_up']
# chp.vars['is_on']
# chp.vars['is_shutting_down']
# chp.vars['is_off']
# chp.vars['gas_to_turbine']
# chp.vars['gas_to_aux_firing']
#

def set_data(model: model.Model, df: pd.DataFrame):
    if "electricity_offtake_price" in df.columns:
        model.get_component("Electricity offtake").vars["prices"].set_values(
            df["electricity_offtake_price"].to_list()
        )
    if "electricity_injection_price" in df.columns:
        model.get_component("Electricity injection").vars["prices"].set_values(
            df["electricity_injection_price"].to_list()
        )
    if "heat_demand" in df.columns:
        model.get_component("heat_demand").vars["demand"].set_values(
            df["heat_demand"].to_list()
        )
    if "electricity_demand" in df.columns:
        model.get_component("electricity_demand").vars["demand"].set_values(
            df["electricity_demand"].to_list()
        )
    if "charging_rate" in df.columns:
        model.get_component("balloon").vars["charge"].set_values(
            df["charging_rate"].to_list()
        )
   
    # chps
    if "gas_turbine_minload_electricity_capacity" in df.columns:
        model.get_component("chp1").set_values(
            "min_electricity_output",
            df["gas_turbine_minload_electricity_capacity"].to_list(),
        )
    if "gas_turbine_maxload_electricity_capacity" in df.columns:
            model.get_component("chp1").set_values(
                "max_electricity_output",
                df["gas_turbine_maxload_electricity_capacity"].to_list(),
            )

    if "pc_max_gas" in df.columns:
        model.get_component("chp1").set_bounds(
            "gas_to_aux_firing", ubound=df["pc_max_gas"].to_list()
        )
      
    if "gas_turbine_minload_electricity_capacity" in df.columns:
        model.get_component("chp2").set_values(
            "min_electricity_output",
            df["gas_turbine_minload_electricity_capacity"].to_list(),
        )
    if "gas_turbine_maxload_electricity_capacity" in df.columns:
            model.get_component("chp2").set_values(
                "max_electricity_output",
                df["gas_turbine_maxload_electricity_capacity"].to_list(),
            )

    if "pc_max_gas" in df.columns:
        model.get_component("chp2").set_bounds(
            "gas_to_aux_firing", ubound=df["pc_max_gas"].to_list()
        )
          

def set_parameters(model: model.Model, params: Dict[str, Any]):
    if "gas_turbine_heat_efficiency" in params:
        model.get_component("chp1").set_values(
            "thermal_efficiency", params["gas_turbine_minload_heat_efficiency"]
        )
    
    if "gas_turbine_electricity_efficiency" in params:
        model.get_component("chp1").set_values(
            "electricity_efficiency", params["gas_turbine_minload_electricity_efficiency"]
        )

    if "hrsg_efficiency" in params:
        model.get_component("chp1").set_values(
            "aux_firing_efficiency", params["hrsg_efficiency"]
        )
    if "gas_turbine_heat_efficiency" in params:
        model.get_component("chp2").set_values(
            "thermal_efficiency", params["gas_turbine_minload_heat_efficiency"]
        )
    
    if "gas_turbine_electricity_efficiency" in params:
        model.get_component("chp2").set_values(
            "electricity_efficiency", params["gas_turbine_minload_electricity_efficiency"]
        )

    if "hrsg_efficiency" in params:
        model.get_component("chp2").set_values(
            "aux_firing_efficiency", params["hrsg_efficiency"]
        )
        
    if "maximum capacity of balloon" in params:
        model.get_component("balloon").set_max_charge(
            params["maximum capacity of balloon"]
        )
    
# Bind methods to the model instance
m.set_set_data_method(set_data)
m.set_set_parameters_method(set_parameters)


def get_model():
    return m
