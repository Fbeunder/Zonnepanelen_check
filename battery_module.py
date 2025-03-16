"""
Battery module for the Zonnepanelen_check application.

This module provides functionality for simulating and calculating
energy savings by using a battery storage system for surplus solar energy.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Union, Optional, Any
import utils
from storage_calculator import StorageCalculator, StorageSimulation


class BatteryCalculator(StorageCalculator):
    """
    Class for calculating energy savings by using a battery storage system.
    """
    
    def __init__(self, data: pd.DataFrame, config: Dict[str, Any]):
        """
        Initialize the battery calculator with data and configuration.
        
        Args:
            data: DataFrame containing energy production and consumption data
            config: Dictionary with configuration parameters
        """
        super().__init__(data, config)
        
        # Extract battery-specific configuration
        self.battery_config = self.config.get('battery', {})
        self.economic_config = self.config.get('economic', {})
        
        # Set default values if not provided
        self.capacity = self.battery_config.get('capacity', 10)  # kWh
        self.efficiency = self.battery_config.get('efficiency', 0.9)  # 90%
        self.max_charge_rate = self.battery_config.get('max_charge_rate', 3.6)  # kW
        self.max_discharge_rate = self.battery_config.get('max_discharge_rate', 3.6)  # kW
        self.min_soc = self.battery_config.get('min_soc', 10)  # %
        self.max_soc = self.battery_config.get('max_soc', 90)  # %
        
        # Get economic parameters
        self.electricity_price = self.economic_config.get('electricity_price', 0.22)  # €/kWh
        self.feed_in_tariff = self.economic_config.get('feed_in_tariff', 0.09)  # €/kWh
        
        # Initialize results
        self.results = None
        
        # Create battery simulation
        self.simulation = StorageSimulation(
            capacity_kwh=self.capacity,
            efficiency=self.efficiency,
            max_charge_rate=self.max_charge_rate,
            max_discharge_rate=self.max_discharge_rate,
            min_soc_percent=self.min_soc,
            max_soc_percent=self.max_soc
        )
    
    def calculate(self) -> Dict[str, Any]:
        """
        Perform battery calculations and return results.
        
        Returns:
            Dictionary containing calculation results
        """
        if self.data is None or len(self.data) == 0:
            return {}
        
        # Reset simulation
        self.simulation.reset()
        
        # Get surplus energy
        surplus_energy = self.get_surplus_energy()
        
        # Determine the time interval
        interval_hours = self._get_data_interval_hours()
        
        # Create a DataFrame to track battery state
        result_df = pd.DataFrame({
            'timestamp': self.data['Date/Time'] if 'Date/Time' in self.data.columns else self.data.index,
            'surplus_energy_wh': surplus_energy
        })
        
        # Initialize additional columns
        result_df['battery_state_kwh'] = 0.0
        result_df['charged_kwh'] = 0.0
        result_df['discharged_kwh'] = 0.0
        result_df['wasted_kwh'] = 0.0
        
        # Simulate battery operation for each time step
        for idx, row in result_df.iterrows():
            # Simulate this timestep
            sim_result = self.simulation.simulate_timestep(
                row['surplus_energy_wh'], 
                interval_hours
            )
            
            # Store results
            result_df.at[idx, 'battery_state_kwh'] = sim_result['state_of_charge']
            result_df.at[idx, 'charged_kwh'] = sim_result['charged_kwh']
            result_df.at[idx, 'discharged_kwh'] = sim_result['discharged_kwh']
            result_df.at[idx, 'wasted_kwh'] = sim_result['wasted_kwh']
        
        # Calculate without battery scenario
        result_df['grid_import_without_battery_kwh'] = result_df['surplus_energy_wh'].apply(
            lambda x: abs(x) / 1000 if x < 0 else 0
        )
        result_df['grid_export_without_battery_kwh'] = result_df['surplus_energy_wh'].apply(
            lambda x: x / 1000 if x > 0 else 0
        )
        
        # Calculate with battery scenario
        result_df['grid_import_with_battery_kwh'] = (
            result_df['surplus_energy_wh'] / 1000 + result_df['discharged_kwh']
        ).apply(lambda x: abs(x) if x < 0 else 0)
        
        result_df['grid_export_with_battery_kwh'] = result_df['wasted_kwh']
        
        # Calculate financial impact
        result_df['savings_import_eur'] = (
            result_df['grid_import_without_battery_kwh'] - result_df['grid_import_with_battery_kwh']
        ) * self.electricity_price
        
        result_df['loss_export_eur'] = (
            result_df['grid_export_without_battery_kwh'] - result_df['grid_export_with_battery_kwh']
        ) * self.feed_in_tariff
        
        result_df['net_financial_benefit_eur'] = result_df['savings_import_eur'] - result_df['loss_export_eur']
        
        # Get simulation totals
        sim_results = self.simulation.get_results()
        
        # Calculate total financial impact
        total_import_savings = result_df['savings_import_eur'].sum()
        total_export_loss = result_df['loss_export_eur'].sum()
        total_financial_benefit = result_df['net_financial_benefit_eur'].sum()
        
        # Calculate reduction in grid dependency
        grid_import_without_battery = result_df['grid_import_without_battery_kwh'].sum()
        grid_import_with_battery = result_df['grid_import_with_battery_kwh'].sum()
        grid_import_reduction = (
            (grid_import_without_battery - grid_import_with_battery) / grid_import_without_battery * 100
        ) if grid_import_without_battery > 0 else 0
        
        # Store results
        self.results = {
            'result_df': result_df,
            'battery_capacity_kwh': self.capacity,
            'battery_efficiency': self.efficiency,
            'total_charged_kwh': sim_results['total_charged_kwh'],
            'total_discharged_kwh': sim_results['total_discharged_kwh'],
            'total_wasted_kwh': sim_results['total_wasted_kwh'],
            'final_soc_kwh': sim_results['final_soc_kwh'],
            'final_soc_percent': sim_results['final_soc_percent'],
            'total_import_savings_eur': total_import_savings,
            'total_export_loss_eur': total_export_loss,
            'total_financial_benefit_eur': total_financial_benefit,
            'grid_import_without_battery_kwh': grid_import_without_battery,
            'grid_import_with_battery_kwh': grid_import_with_battery,
            'grid_import_reduction_percent': grid_import_reduction
        }
        
        return self.results
    
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
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of battery calculation results.
        
        Returns:
            Dictionary with summary metrics
        """
        if self.results is None:
            self.calculate()
            
        if self.results is None:
            return {}
        
        # Format currency values
        formatted_benefit = utils.format_currency(
            self.results['total_financial_benefit_eur']
        )
        formatted_import_savings = utils.format_currency(
            self.results['total_import_savings_eur']
        )
        formatted_export_loss = utils.format_currency(
            self.results['total_export_loss_eur']
        )
        
        return {
            'battery_capacity': f"{self.capacity} kWh",
            'battery_efficiency': f"{self.efficiency * 100:.0f}%",
            'total_energy_charged': f"{self.results['total_charged_kwh']:.2f} kWh",
            'total_energy_discharged': f"{self.results['total_discharged_kwh']:.2f} kWh",
            'total_energy_wasted': f"{self.results['total_wasted_kwh']:.2f} kWh",
            'grid_import_reduction': f"{self.results['grid_import_reduction_percent']:.1f}%",
            'savings_from_reduced_imports': formatted_import_savings,
            'loss_from_reduced_exports': formatted_export_loss,
            'net_financial_benefit': formatted_benefit,
        }
