"""
Visualization module for the Zonnepanelen_check application.

This module provides backwards compatibility with the new modular visualization system.
All visualization functions are now split into individual modules under the visualization/ package:

- energy_plots.py: Functions for energy production and consumption visualization
- battery_plots.py: Functions for battery simulation and performance visualization
- boiler_plots.py: Functions for boiler simulation and performance visualization
- utility_plots.py: Utility functions for general plotting and visualization

All function calls are forwarded to the new implementation to maintain compatibility.
"""
import warnings
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional, Union

# Import all visualization functions from the modular implementation
from visualization import (
    # Energy plots
    plot_energy_production_consumption,
    plot_surplus_energy,
    
    # Battery plots
    plot_battery_state,
    plot_battery_daily_flows,
    plot_battery_monthly_performance,
    plot_battery_grid_impact,
    plot_battery_simulation_detail,
    
    # Boiler plots
    plot_boiler_energy_usage,
    plot_boiler_daily_performance,
    plot_boiler_monthly_performance,
    plot_boiler_simulation_detail,
    plot_boiler_usage_profile,
    
    # Utility plots
    plot_comparison_chart,
    fig_to_base64
)

# Show deprecation warning
warnings.warn(
    "Direct imports from visualization.py are deprecated. "
    "Please use the modular imports from the visualization/ package instead.",
    DeprecationWarning,
    stacklevel=2
)
