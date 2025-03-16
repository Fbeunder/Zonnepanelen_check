"""
Data processing module for the Zonnepanelen_check application.

This module handles all data loading, processing, and manipulation
for the energy production and consumption data.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Union, Optional
import utils


class DataProcessor:
    """
    Class for processing energy production and consumption data.
    """
    
    def __init__(self):
        """Initialize the DataProcessor with empty data."""
        self.data = None
        self.daily_data = None
        self.monthly_data = None
        self.file_path = None
    
    def load_data(self, file_path: str) -> bool:
        """
        Load data from a CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            bool: True if loading was successful, False otherwise
        """
        try:
            # Attempt to load the CSV file
            df = pd.read_csv(file_path)
            
            # Check if required columns exist
            required_cols = ['Date/Time', 'Energy Produced (Wh)', 'Energy Consumed (Wh)']
            if not all(col in df.columns for col in required_cols):
                print(f"Error: Required columns {required_cols} not found in the CSV file.")
                return False
            
            # Convert Date/Time to datetime
            df['Date/Time'] = pd.to_datetime(df['Date/Time'], format='%d/%m/%Y %H:%M', errors='coerce')
            
            # Check for parsing errors
            if df['Date/Time'].isna().any():
                print("Warning: Some date/time values could not be parsed.")
                
            # Store the data
            self.data = df
            self.file_path = file_path
            
            # Process the data
            self.process_data()
            
            return True
            
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return False
    
    def process_data(self) -> None:
        """
        Process the loaded data to create derived datasets.
        """
        if self.data is None:
            return
        
        # Calculate surplus energy
        self.data = utils.calculate_surplus_energy(self.data)
        
        # Calculate daily totals
        self.daily_data = self._calculate_daily_totals()
        
        # Calculate monthly totals
        self.monthly_data = self._calculate_monthly_totals()
    
    def _calculate_daily_totals(self) -> pd.DataFrame:
        """
        Calculate daily totals for energy metrics.
        
        Returns:
            DataFrame with daily energy totals
        """
        if self.data is None:
            return pd.DataFrame()
        
        # Create a copy of data with date only
        df = self.data.copy()
        df['date'] = df['Date/Time'].dt.date
        
        # Group by date and sum energy columns
        energy_cols = [col for col in df.columns if 'Energy' in col or 'surplus_energy' in col]
        daily = df.groupby('date')[energy_cols].sum().reset_index()
        
        # Convert to more readable units (kWh)
        for col in energy_cols:
            daily[col.replace('(Wh)', '(kWh)')] = utils.convert_wh_to_kwh(daily[col])
            
        return daily
    
    def _calculate_monthly_totals(self) -> pd.DataFrame:
        """
        Calculate monthly totals for energy metrics.
        
        Returns:
            DataFrame with monthly energy totals
        """
        if self.data is None:
            return pd.DataFrame()
        
        # Create a copy of data with month info
        df = self.data.copy()
        df['year_month'] = df['Date/Time'].dt.to_period('M')
        
        # Group by month and sum energy columns
        energy_cols = [col for col in df.columns if 'Energy' in col or 'surplus_energy' in col]
        monthly = df.groupby('year_month')[energy_cols].sum().reset_index()
        
        # Convert to more readable units (kWh)
        for col in energy_cols:
            monthly[col.replace('(Wh)', '(kWh)')] = utils.convert_wh_to_kwh(monthly[col])
            
        return monthly
    
    def get_data_summary(self) -> Dict[str, float]:
        """
        Get summary statistics for the loaded data.
        
        Returns:
            Dictionary containing summary statistics
        """
        if self.data is None:
            return {}
        
        # Calculate total production and consumption
        total_produced = self.data['Energy Produced (Wh)'].sum() / 1000  # kWh
        total_consumed = self.data['Energy Consumed (Wh)'].sum() / 1000  # kWh
        
        # Calculate grid imports and exports if available
        total_exported = 0
        total_imported = 0
        if 'Exported to Grid (Wh)' in self.data.columns:
            total_exported = self.data['Exported to Grid (Wh)'].sum() / 1000  # kWh
        if 'Imported from Grid (Wh)' in self.data.columns:
            total_imported = self.data['Imported from Grid (Wh)'].sum() / 1000  # kWh
        
        # Calculate self-consumption
        self_consumed = total_produced - total_exported if 'Exported to Grid (Wh)' in self.data.columns else 0
        
        # Calculate self-sufficiency
        self_sufficiency = (self_consumed / total_consumed * 100) if total_consumed > 0 else 0
            
        # Return the summary
        return {
            'total_produced_kwh': total_produced,
            'total_consumed_kwh': total_consumed,
            'total_exported_kwh': total_exported,
            'total_imported_kwh': total_imported,
            'self_consumed_kwh': self_consumed,
            'self_sufficiency_percent': self_sufficiency
        }
