"""
Utility functions for the Zonnepanelen_check application.

This module contains common helper functions used across various modules
in the application.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Union, Optional


def convert_wh_to_kwh(value: Union[float, pd.Series]) -> Union[float, pd.Series]:
    """
    Convert Watt-hour (Wh) values to Kilowatt-hour (kWh).
    
    Args:
        value: A single value or a pandas Series containing Wh values
        
    Returns:
        The value(s) converted to kWh
    """
    return value / 1000


def calculate_daily_totals(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    Calculate daily totals for a specific column in the dataframe.
    
    Args:
        df: DataFrame containing timestamped energy data
        column: The column name to sum by day
        
    Returns:
        DataFrame with daily totals for the specified column
    """
    # Ensure the Date/Time column is treated as datetime
    if 'Date/Time' in df.columns:
        df = df.copy()
        df['date'] = pd.to_datetime(df['Date/Time']).dt.date
        return df.groupby('date')[column].sum().reset_index()
    return pd.DataFrame()


def calculate_monthly_totals(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    Calculate monthly totals for a specific column in the dataframe.
    
    Args:
        df: DataFrame containing timestamped energy data
        column: The column name to sum by month
        
    Returns:
        DataFrame with monthly totals for the specified column
    """
    # Ensure the Date/Time column is treated as datetime
    if 'Date/Time' in df.columns:
        df = df.copy()
        df['date'] = pd.to_datetime(df['Date/Time'])
        df['month'] = df['date'].dt.to_period('M')
        return df.groupby('month')[column].sum().reset_index()
    return pd.DataFrame()


def calculate_surplus_energy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the surplus energy (production - consumption).
    
    Args:
        df: DataFrame containing energy production and consumption data
        
    Returns:
        DataFrame with added 'surplus_energy' column
    """
    if 'Energy Produced (Wh)' in df.columns and 'Energy Consumed (Wh)' in df.columns:
        df = df.copy()
        df['surplus_energy'] = df['Energy Produced (Wh)'] - df['Energy Consumed (Wh)']
        return df
    return df


def format_currency(value: float, currency: str = "€") -> str:
    """
    Format a value as currency with the appropriate symbol.
    
    Args:
        value: The value to format
        currency: The currency symbol to use, defaults to Euro
        
    Returns:
        Formatted currency string
    """
    return f"{currency} {value:.2f}"
