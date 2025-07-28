# Bokeh Plotting for Kronos Results

This directory contains Bokeh versions of the plotting functionality for Kronos simulation results.

## Files

- `plot_results_bokeh.py` - Main Bokeh plotting script
- `test_bokeh_plot.py` - Test script to demonstrate functionality
- `plot_results.py` - Original matplotlib version (for reference)

## Features

The Bokeh version provides several advantages over the matplotlib version:

1. **Interactive plots** - Zoom, pan, hover tooltips, and more
2. **Better performance** - Handles large datasets more efficiently
3. **Web-based** - Can be embedded in web applications
4. **Linked axes** - All plots share the same time axis for easy comparison
5. **Export capabilities** - Save plots as HTML files

## Installation

Make sure you have Bokeh installed:

```bash
pip install bokeh==3.4.0
```

Or install from the requirements file:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from analysis.plot_results_bokeh import load_results_df, plot_results_bokeh

# Load data for a specific scenario
df, scenario_name, dt = load_results_df("Flex_0")

# Create interactive plot
plot_results_bokeh(df, scenario_name, dt, singleplot=True, output_filename="results.html")
```

### Test Script

Run the test script to see the functionality in action:

```bash
python analysis/test_bokeh_plot.py
```

This will:
1. Find available scenarios
2. Load the first available scenario
3. Create an interactive Bokeh plot
4. Save it as `test_kronos_results.html`

### Available Functions

#### `load_results_df(scenario=None)`
Loads the most recent results file for a given scenario.

**Parameters:**
- `scenario` (str, optional): Scenario name. If None, loads from root results folder.

**Returns:**
- `df`: Pandas DataFrame with the results
- `scenario_name`: Name of the scenario
- `file_datetime`: Timestamp when the file was created

#### `plot_results_bokeh(results_df, scenario_name, file_datetime, singleplot=False, output_filename=None)`
Creates interactive Bokeh plots.

**Parameters:**
- `results_df`: Pandas DataFrame with simulation results
- `scenario_name`: Name of the scenario
- `file_datetime`: Timestamp when the file was created
- `singleplot` (bool): If True, creates all 5 plots in one layout. If False, creates only the first 3 plots.
- `output_filename` (str, optional): If provided, saves the plot to this HTML file

**Returns:**
- Bokeh layout object

#### `list_available_scenarios(results_dir="results")`
Lists all available scenarios with results files.

**Parameters:**
- `results_dir` (str): Directory to search for results

**Returns:**
- List of scenario names

## Plot Types

The Bokeh version creates the same plots as the matplotlib version:

1. **Electricity Source** - Shows electricity demand and sources (CHP, offtake)
2. **Electricity Sink** - Shows electricity consumption (demand, e-boiler, injection)
3. **Prices** - Shows electricity and gas prices
4. **Heat Source** - Shows heat demand and sources (CHP, gas boiler, e-boiler) - only in singleplot mode
5. **Low Demand Indicator** - Shows low demand periods - only in singleplot mode

## Interactive Features

- **Box Zoom**: Click and drag to create a zoom box (default behavior)
- **Pan**: Use the pan tool in the toolbar to move around
- **Wheel Zoom**: Use the wheel zoom tool in the toolbar for mouse wheel zooming
- **Hover**: Hover over data points to see values
- **Reset**: Reset button to return to original view
- **Save**: Save button to export the plot
- **Linked axes**: All plots share the same time axis

## Output

The plots are saved as interactive HTML files that can be opened in any web browser. The HTML files are self-contained and include all necessary JavaScript and CSS.

## Comparison with Matplotlib

| Feature | Matplotlib | Bokeh |
|---------|------------|-------|
| Interactivity | Limited | Full (zoom, pan, hover) |
| Performance | Good for small datasets | Better for large datasets |
| Export | Static images | Interactive HTML |
| Web integration | Limited | Native |
| File size | Small | Larger (includes JS/CSS) |

## Troubleshooting

### Import Errors
Make sure Bokeh is installed:
```bash
pip install bokeh
```

### No Data Found
Make sure you have run simulations and have results files in the `results/` directory.

### Browser Issues
The HTML files require a modern web browser with JavaScript enabled.

### Performance Issues
For very large datasets, consider:
- Reducing the time range
- Downsampling the data
- Using the matplotlib version for static plots 