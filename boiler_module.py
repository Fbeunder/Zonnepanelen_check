"""
Boiler module for the Zonnepanelen_check application.

This module provides functionality for simulating and calculating
energy savings by using surplus solar energy for water heating.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Union, Optional, Any
import utils
from storage_calculator import StorageCalculator


class BoilerCalculator(StorageCalculator):
    """
    Class for calculating energy savings using surplus solar energy for water heating.
    """
    
    def __init__(self, data: pd.DataFrame, config: Dict[str, Any]):
        """
        Initialize the boiler calculator with data and configuration.
        
        Args:
            data: DataFrame containing energy production and consumption data
            config: Dictionary with configuration parameters
        """
        super().__init__(data, config)
        
        # Extract boiler-specific configuration
        self.boiler_config = self.config.get('boiler', {})
        self.economic_config = self.config.get('economic', {})
        
        # Set default values if not provided
        self.capacity = self.boiler_config.get('capacity', 80)  # Liter
        self.efficiency = self.boiler_config.get('efficiency', 0.9)  # 90%
        self.water_temp_rise = self.boiler_config.get('water_temperature_rise', 35)  # °C
        self.daily_usage = self.boiler_config.get('daily_hot_water_usage', 120)  # Liter
        
        # Get economic parameters
        self.gas_price = self.economic_config.get('gas_price', 0.80)  # €/m³
        
        # Initialize results
        self.results = None
    
    def calculate(self) -> Dict[str, Any]:
        """
        Perform boiler calculations and return results.
        
        Returns:
            Dictionary containing calculation results
        """
        if self.data is None or len(self.data) == 0:
            return {}
        
        # Get surplus energy
        surplus_energy = self.get_surplus_energy()
        
        # Calculate daily energy required for water heating
        daily_energy_needed_kwh = self._calculate_daily_water_heating_energy()
        
        # Convert to the same time interval as the data (typically 15 minutes)
        interval_hours = self._get_data_interval_hours()
        interval_energy_needed_kwh = daily_energy_needed_kwh * (interval_hours / 24)
        
        # Create a DataFrame to track energy use
        result_df = pd.DataFrame({
            'timestamp': self.data['Date/Time'] if 'Date/Time' in self.data.columns else self.data.index,
            'surplus_energy_wh': surplus_energy,
            'boiler_energy_needed_kwh': interval_energy_needed_kwh
        })
        
        # Convert surplus from Wh to kWh
        result_df['surplus_energy_kwh'] = result_df['surplus_energy_wh'] / 1000
        
        # Calculate how much energy can be used for water heating
        result_df['boiler_energy_used_kwh'] = result_df.apply(
            lambda row: min(
                max(0, row['surplus_energy_kwh']),  # Only use positive surplus
                row['boiler_energy_needed_kwh']     # Limited by what's needed
            ),
            axis=1
        )
        
        # Calculate how much gas is saved
        result_df['gas_saved_m3'] = result_df['boiler_energy_used_kwh'] / self._get_kwh_per_m3_gas()
        
        # Calculate financial savings
        result_df['financial_savings'] = result_df['gas_saved_m3'] * self.gas_price
        
        # Calculate total values
        total_surplus_kwh = result_df['surplus_energy_kwh'].sum()
        total_energy_used_kwh = result_df['boiler_energy_used_kwh'].sum()
        total_gas_saved_m3 = result_df['gas_saved_m3'].sum()
        total_financial_savings = result_df['financial_savings'].sum()
        
        # Calculate utilization percentage
        surplus_utilization = (total_energy_used_kwh / total_surplus_kwh * 100) if total_surplus_kwh > 0 else 0
        
        # Store results
        self.results = {
            'result_df': result_df,
            'total_surplus_kwh': total_surplus_kwh,
            'total_energy_used_kwh': total_energy_used_kwh,
            'total_gas_saved_m3': total_gas_saved_m3,
            'total_financial_savings': total_financial_savings,
            'surplus_utilization_percent': surplus_utilization,
            'daily_energy_needed_kwh': daily_energy_needed_kwh
        }
        
        return self.results
    
    def _calculate_daily_water_heating_energy(self) -> float:
        """
        Calculate the daily energy required for water heating.
        
        Returns:
            Energy required in kWh
        """
        # Energy (kWh) = Volume (L) * Specific Heat Capacity of Water (kWh/L/°C) * Temperature Rise (°C)
        # Specific heat capacity of water = 4.18 kJ/kg/°C = 0.00116 kWh/kg/°C
        # Assuming density of water = 1 kg/L
        
        specific_heat_capacity = 0.00116  # kWh/L/°C
        
        # Energy needed without efficiency considerations
        energy_needed = self.daily_usage * specific_heat_capacity * self.water_temp_rise
        
        # Adjust for boiler efficiency
        energy_needed_with_efficiency = energy_needed / self.efficiency
        
        return energy_needed_with_efficiency
    
    def _get_data_interval_hours(self) -> float:
        """
        Determine the time interval between data points in hours.
        
        Returns:
            Time interval in hours
        """
        if 'Date/Time' in self.data.columns and len(self.data) > 1:
            # Convert to datetime if not already
            if not pd.api.types.is_datetime64_dtype(self.data['Date/Time']):
                date_times = pd.to_datetime(self.data['Date/Time'])
            else:
                date_times = self.data['Date/Time']
                
            # Calculate the most common interval
            intervals = date_times.diff().dropna()
            if len(intervals) > 0:
                most_common_interval = intervals.mode()[0]
                return most_common_interval.total_seconds() / 3600  # Convert to hours
        
        # Default to 15 minutes if can't determine
        return 0.25
    
    def _get_kwh_per_m3_gas(self) -> float:
        """
        Get the energy content of natural gas in kWh per cubic meter.
        
        Returns:
            Energy content in kWh/m³
        """
        # Standard energy content of natural gas (can be adjusted in configuration)
        return self.boiler_config.get('gas_energy_content', 9.77)  # kWh/m³
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of boiler calculation results.
        
        Returns:
            Dictionary with summary metrics
        """
        if self.results is None:
            self.calculate()
            
        if self.results is None:
            return {}
        
        # Format currency values
        formatted_savings = utils.format_currency(
            self.results['total_financial_savings']
        )
        
        return {
            'daily_hot_water_usage': f"{self.daily_usage} L",
            'daily_energy_needed': f"{self.results['daily_energy_needed_kwh']:.2f} kWh",
            'total_surplus_energy': f"{self.results['total_surplus_kwh']:.2f} kWh",
            'total_energy_used': f"{self.results['total_energy_used_kwh']:.2f} kWh",
            'surplus_utilization': f"{self.results['surplus_utilization_percent']:.1f}%",
            'gas_saved': f"{self.results['total_gas_saved_m3']:.2f} m³",
            'financial_savings': formatted_savings,
        }
