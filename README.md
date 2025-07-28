# KRONOS System Documentation

![image](https://github.com/user-attachments/assets/e5759f82-251e-448e-baff-f5c6226fad97)

## Project Structure

```
Kronos/
├── core/                      # Core model and functionality
│   ├── model.py              # Core model definition
│   ├── data_generator.py     # Data generation utilities
│   └── optimization.py       # Real-time optimization code
│
├── simulation/               # Simulation-related code
│   ├── scenarios.py         # Scenario definitions
│   ├── define_scenarios.py  # Scenario creation
│   └── run_scenarios.py     # Scenario execution
│
├── analysis/               # Analysis and visualization
│   └── plot_results.py     # Results analysis and plotting
│
├── data/                   # Data storage
│   ├── marketdata.json
│   └── scenarios.json
│
└── results/               # Simulation results
```

## Installation

## System Parameters

| Component | Parameter | Value | Unit | Notes |
|-----------|-----------|-------|------|-------|
| Gas Turbine | Min Load Electricity Capacity | 3.275 | MW | Base capacity |
| Gas Turbine | Max Load Electricity Capacity | 3.275 | MW | Incremental capacity |
| Gas Turbine | Min Load Electricity Efficiency | 0.31 | - | Relative to gas HHV |
| Gas Turbine | Max Load Electricity Efficiency | 0.31 | - | Incremental efficiency |
| Gas Turbine | Min Load Heat Efficiency | 0.46 | - | Relative to gas HHV |
| Gas Turbine | Max Load Heat Efficiency | 0.46 | - | Incremental efficiency |
| Gas Boiler | Efficiency | 0.85 | - | Relative to gas HHV |
| Gas Boiler | Capacity | 26 | MW | 2 × 13 MW |
| Electric Boiler | Efficiency | 1.0 | - | - |
| Electric Boiler | Capacity | 10 | MW | - |
| HRSG | Efficiency | 1.0 | - | - |
| HRSG | Capacity | 10 | MW | - |

## Gas Turbine (GT) Specifications

- **Efficiency**: 
  - Datasheet: 32.9%
  - Actual: ~31%. This is the value we will use for now.
- **Temperature dependence**: see plots below and the analysis file in the code. We will use `Capacity ~ 6.55 - 0.045 * Temperature`

<p align="center">
  <img src="https://github.com/user-attachments/assets/3d1b13f6-26b5-4619-b2e3-ab25c3929fd1" alt="Image 1" width="250"/>
  <img src="https://github.com/user-attachments/assets/76da83cd-1422-43d7-ae5a-5638a9393cc9" alt="Image 1" width="250"/>
  <img src="https://github.com/user-attachments/assets/23dc5d01-8089-4077-a38a-b63fbd7a6cd5" alt="Image 1" width="250"/>
</p>

## Usage

### Running Simulations

To run simulations with predefined scenarios:

```python
from simulation.define_scenarios import define_scenarios
from simulation.run_scenarios import run_all_scenarios

# Define scenarios
manager = define_scenarios()

# Run all scenarios
run_all_scenarios()
```

### Real-time Optimization

To run real-time optimization:

```python
from core.optimization import run_optimization

# Run optimization
run_optimization()
```

### Analysis

To analyze and plot results:

```python
from analysis.plot_results import plot_results

# Plot results from a specific scenario
plot_results("results/scenario_name/results_timestamp")
```

## Steam Properties

| Pressure (bar) | Temperature (°C) | Enthalpy (kJ/kg) | Energy for Steam Generation (MWh/t) |
|----------------|------------------|------------------|-------------------------------------|
| 21             | 214              | 2,797            | 0.66                                |
| 9              | 175              | 2,773            | 0.65                                |
| 1              | 100              | 419              | -                                   |

## System Components

| Source        | Typical Production | Pressure | Gas Consumption | Efficiency | Power Output |
|--------------|-------------------|----------|-----------------|------------|--------------|
| WHB          | 4-5 t/hr         | 9 bar    | -              | -          | ~3 MW        |
| BUB          | 15-25 t/hr       | 21 bar   | 70 Nm³/t       | 85%        | 20-33 MW     |
| GT w/o HRSG  | 12.5-15 t/hr     | 21 bar   | 129 Nm³/t      | 46%        | 16-20 MW     |
| GT + HRSG    | 20-25 t/hr       | 21 bar   | 55 Nm³/t       | 100%       | 26-33 MW     |

## Key Conversions
- **Steam**: 1 MW ≈ 1.3 ton/hr (1 ton steam ≈ 0.77 MWh)
- **Gas**: 1 Nm³ = 11 kWh (HHV) or 1000 Nm³/hr ≈ 11 MW

> **Note**: Focus on 21 bar steam for primary operations.
