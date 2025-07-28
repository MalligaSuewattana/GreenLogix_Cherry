import pandas as pd
import numpy as np
from model_biogas import get_model
from model_to_flex.core.dispatch import dispatch
from model_to_flex.core.enums import BuilderType, SolverType, DispatchType
from data_generator import get_data
from model_to_flex.core.io_utils.save_results import save_results
from model_to_flex.core.io_utils.plot_timeseries import main as plot_timeseries
from datetime import datetime
import matplotlib.pyplot as plt

# price starttime defines what market data is used. Includes gas prices, electricity spot prices, co2 prices and temperature.
# demand_starttime defines what (historical) demand data is used. Only period 2022-01-01 to 2022-12-31 is available.
# length defines the length of the period to be simulated

# problem: the first hours 2022-01-17 the head demand is low, such that GT should be switched off.
# price_starttime='2025-01-16', demand_starttime='2022-01-17', length=48: calculation fails
# price_starttime='2025-01-17', demand_starttime='2022-01-17', length=48: calculation succeeds
# What could be the reason for this?

# Generate data
data = get_data(
    price_starttime="2022-01-01",
    demand_starttime="2022-01-01",
    length=24*4,  # number of hours
    freq="15min",  # hourly data
    save_to_csv=False,
)

# Load model
model = get_model()

# Solver options
solver_options = {}  # Here you can define solver specific options (e.g. time limits, tolerances, etc.)
dispatch_opts = {
    "optimizer_type": "default",
    "builder_type": BuilderType.PYOMO,  # Currently only Pyomo is supported
    "solver": SolverType.CBC,
    "solver_options": solver_options,
    "dispatch_type": DispatchType.MONTHLY,
    # "pred_hor": 36,
    # "contr_hor": 24,
}

# efficiencies are relative to gas LHV
# capacities are in MW and MW_hhv
gas_turbine_minload_electricity_capacity = 7.5
gas_turbine_maxload_electricity_capacity = 1.5
gas_turbine_minload_electricity_efficiency = 0.40
gas_turbine_maxload_electricity_efficiency = 0.40  
gas_turbine_minload_heat_efficiency = 0.45
gas_turbine_maxload_heat_efficiency = 0.45 
hrsg_efficiency = 1.0
hrsg_capacity = 1.0  # in MW_LHV  ??? 
heat_demand = 0.1
electricity_demand = 0.125
maximum_capacity_of_balloon = 1500
minimum_gas_from_digester = 200
maximum_gas_from_digester = 340

data["gas_turbine_minload_electricity_efficiency"] = (
    gas_turbine_minload_electricity_efficiency
)
data["gas_turbine_maxload_electricity_efficiency"] = (
    gas_turbine_maxload_electricity_efficiency
)

data["gas_turbine_minload_electricity_capacity"] = (
    gas_turbine_minload_electricity_capacity 
)
data["gas_turbine_maxload_electricity_capacity"] = (
    gas_turbine_maxload_electricity_capacity 
)
data["hrsg_capacity"] = hrsg_capacity   
data["heat_demand"] = heat_demand
data["electricity_demand"] = electricity_demand
data["charging_rate"] = np.random.randint(minimum_gas_from_digester, 
                                          maximum_gas_from_digester,size=len(data))

# Create empty params dictionary
params = {
    "gas_turbine_minload_heat_efficiency": gas_turbine_minload_heat_efficiency,
    "gas_turbine_maxload_heat_efficiency": gas_turbine_maxload_heat_efficiency,
    "hrsg_efficiency": hrsg_efficiency,
    "maximum capacity of balloon": maximum_capacity_of_balloon,
}

# Dispatch the model
kpis, results = dispatch(
    model,
    params,
    data,
    **dispatch_opts,
)


# Create timestamp for filenames
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Save results with timestamp
save_results(
    results=results,
    path="results",
    filename=f"results_{timestamp}",
    sheetnames=["Timeseries"],
    overwrite=True,
)

# Plot timeseries
# plot_timeseries()
