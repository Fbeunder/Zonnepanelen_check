"""
Energy calculation utility functions for the Zonnepanelen_check application.

This module contains utility functions for various energy calculations.
"""
import pandas as pd
import numpy as np


def calculate_surplus_energy(df):
    """
    Calculate surplus energy (production - consumption) for each time interval.
    
    Args:
        df: DataFrame with 'Energy Produced (Wh)' and 'Energy Consumed (Wh)' columns
        
    Returns:
        DataFrame with added 'surplus_energy' column (in Wh)
    """
    # Make a copy to avoid modifying the original DataFrame
    result_df = df.copy()
    
    # Check if required columns exist
    if 'Energy Produced (Wh)' not in result_df.columns or 'Energy Consumed (Wh)' not in result_df.columns:
        raise ValueError("Required columns 'Energy Produced (Wh)' and 'Energy Consumed (Wh)' not found in DataFrame")
    
    # Calculate surplus energy (positive when production > consumption)
    result_df['surplus_energy'] = result_df['Energy Produced (Wh)'] - result_df['Energy Consumed (Wh)']
    
    return result_df


def convert_wh_to_kwh(wh_values):
    """
    Convert Watt-hour (Wh) values to Kilowatt-hour (kWh).
    
    Args:
        wh_values: Series or value in Watt-hours
        
    Returns:
        Series or value in Kilowatt-hours
    """
    return wh_values / 1000
