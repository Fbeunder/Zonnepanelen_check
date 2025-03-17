"""
Visualization module for the Zonnepanelen_check application.

This module contains visualization functions for energy production, consumption, 
and storage options analysis.
"""
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional, Union

# Import all visualization modules
from .energy_plots import (
    plot_energy_production_consumption,
    plot_surplus_energy
)

from .battery_plots import (
    plot_battery_state,
    plot_battery_daily_flows,
    plot_battery_monthly_performance,
    plot_battery_grid_impact,
    plot_battery_simulation_detail
)

from .boiler_plots import (
    plot_boiler_energy_usage,
    plot_boiler_daily_performance,
    plot_boiler_monthly_performance,
    plot_boiler_simulation_detail,
    plot_boiler_usage_profile
)

from .utility_plots import (
    plot_comparison_chart,
    fig_to_base64
)

# Export all functions for backward compatibility and ease of use
__all__ = [
    'plot_energy_production_consumption',
    'plot_surplus_energy',
    'plot_battery_state',
    'plot_battery_daily_flows',
    'plot_battery_monthly_performance',
    'plot_battery_grid_impact',
    'plot_battery_simulation_detail',
    'plot_boiler_energy_usage',
    'plot_boiler_daily_performance',
    'plot_boiler_monthly_performance',
    'plot_boiler_simulation_detail',
    'plot_boiler_usage_profile',
    'plot_comparison_chart',
    'fig_to_base64'
]
