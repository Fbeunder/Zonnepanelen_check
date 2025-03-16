"""
Boiler module for the Zonnepanelen_check application.

This module provides functionality for simulating and calculating
energy savings by using surplus solar energy for water heating.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Union, Optional, Any
import utils
from utils.energy_calculations import convert_wh_to_kwh
from storage_calculator import StorageCalculator


class BoilerCalculator(StorageCalculator):
    """
    Class for calculating energy savings using surplus solar energy for water heating.
    
    This class simulates a hot water boiler that uses surplus solar energy to heat water,
    calculating the resulting gas and financial savings.
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
        self.standby_loss = self.boiler_config.get('standby_loss_percent', 0.5) / 100  # Daily % heat loss
        self.hourly_usage_profile = self.boiler_config.get('hourly_usage_profile', self._default_usage_profile())
        
        # Water properties
        self.specific_heat_capacity = 0.00116  # kWh/L/°C
        
        # Get economic parameters
        self.gas_price = self.economic_config.get('gas_price', 0.80)  # €/m³
        self.gas_energy_content = self.boiler_config.get('gas_energy_content', 9.77)  # kWh/m³
        
        # Initialize results
        self.results = None
    
    def calculate(self) -> Dict[str, Any]:
        """
        Perform boiler calculations and return results.
        
        This method simulates the boiler usage throughout the provided data timeline,
        accounting for varying hot water use, energy storage in the boiler, heat losses,
        and gas savings.
        
        Returns:
            Dictionary containing calculation results
        """
        if self.data is None or len(self.data) == 0:
            return {}
        
        # Get surplus energy
        surplus_energy = self.get_surplus_energy()
        
        # Get the time interval of the data
        interval_hours = self._get_data_interval_hours()
        
        # Initialize simulation state
        water_temp = self._get_cold_water_temp()  # Start with cold water
        max_temp = water_temp + self.water_temp_rise  # Maximum temperature
        water_volume = self.capacity  # Start with full volume
        
        # Get timestamps for time-of-day calculations
        timestamps = pd.to_datetime(self.data['Date/Time']) if 'Date/Time' in self.data.columns else pd.to_datetime(self.data.index)
        
        # Create a DataFrame to track energy use and simulation state
        result_df = pd.DataFrame({
            'timestamp': timestamps,
            'surplus_energy_wh': surplus_energy,
            'hour_of_day': timestamps.dt.hour,
            'day_of_week': timestamps.dt.dayofweek
        })
        
        # Convert surplus from Wh to kWh for calculations
        result_df['surplus_energy_kwh'] = result_df['surplus_energy_wh'] / 1000
        
        # Initialize result columns
        result_df['water_temp'] = np.nan
        result_df['water_volume'] = np.nan
        result_df['heat_energy_kwh'] = np.nan
        result_df['hot_water_demand_l'] = np.nan
        result_df['energy_needed_kwh'] = np.nan
        result_df['energy_used_kwh'] = np.nan
        result_df['heat_loss_kwh'] = np.nan
        result_df['gas_needed_m3'] = np.nan
        result_df['gas_saved_m3'] = np.nan
        result_df['financial_savings'] = np.nan
        
        # Iterate through each time interval
        for i in range(len(result_df)):
            # Current time information
            hour = result_df.loc[i, 'hour_of_day']
            
            # 1. Calculate hot water usage for this interval
            hot_water_usage = self._get_interval_hot_water_usage(hour, interval_hours)
            result_df.loc[i, 'hot_water_demand_l'] = hot_water_usage
            
            # 2. Calculate heat loss during this interval
            heat_loss_kwh = self._calculate_interval_heat_loss(water_temp, water_volume, interval_hours)
            result_df.loc[i, 'heat_loss_kwh'] = heat_loss_kwh
            
            # 3. Update water temperature due to heat loss
            if water_volume > 0:
                temp_drop = heat_loss_kwh / (water_volume * self.specific_heat_capacity)
                water_temp = max(water_temp - temp_drop, self._get_cold_water_temp())
            
            # 4. Calculate energy needed to maintain temperature with usage
            energy_needed = 0
            
            if hot_water_usage > 0:
                # Energy needed to heat replacement cold water
                energy_needed = hot_water_usage * self.specific_heat_capacity * (max_temp - self._get_cold_water_temp())
                
                # Apply efficiency factor
                energy_needed_with_efficiency = energy_needed / self.efficiency
                
                # Track energy needed
                result_df.loc[i, 'energy_needed_kwh'] = energy_needed_with_efficiency
                
                # Calculate how much gas would be needed without solar
                result_df.loc[i, 'gas_needed_m3'] = energy_needed_with_efficiency / self.gas_energy_content
            
            # 5. Use surplus energy if available
            surplus = result_df.loc[i, 'surplus_energy_kwh']
            energy_used = min(max(0, surplus), energy_needed_with_efficiency) if energy_needed > 0 else 0
            
            # If there's more surplus, use it to heat the existing water
            if surplus > energy_used and water_temp < max_temp:
                # Calculate energy needed to heat entire volume to max temp
                additional_heating = water_volume * self.specific_heat_capacity * (max_temp - water_temp)
                additional_energy_used = min(surplus - energy_used, additional_heating)
                
                # Update temperature
                if water_volume > 0:
                    temp_increase = additional_energy_used / (water_volume * self.specific_heat_capacity)
                    water_temp = min(water_temp + temp_increase, max_temp)
                
                energy_used += additional_energy_used
            
            # 6. Track energy used and gas saved
            result_df.loc[i, 'energy_used_kwh'] = energy_used
            result_df.loc[i, 'gas_saved_m3'] = energy_used / self.gas_energy_content
            result_df.loc[i, 'financial_savings'] = result_df.loc[i, 'gas_saved_m3'] * self.gas_price
            
            # 7. Update simulation state
            water_temp = max_temp if energy_used >= energy_needed_with_efficiency else water_temp
            result_df.loc[i, 'water_temp'] = water_temp
            result_df.loc[i, 'water_volume'] = water_volume
            result_df.loc[i, 'heat_energy_kwh'] = water_volume * self.specific_heat_capacity * (water_temp - self._get_cold_water_temp())
        
        # Calculate total values and other metrics
        total_surplus_kwh = result_df['surplus_energy_kwh'].sum()
        total_energy_used_kwh = result_df['energy_used_kwh'].sum()
        total_energy_needed_kwh = result_df['energy_needed_kwh'].sum()
        total_gas_needed_m3 = result_df['gas_needed_m3'].sum()
        total_gas_saved_m3 = result_df['gas_saved_m3'].sum()
        total_financial_savings = result_df['financial_savings'].sum()
        
        # Calculate utilization percentage and efficiency metrics
        surplus_utilization = (total_energy_used_kwh / total_surplus_kwh * 100) if total_surplus_kwh > 0 else 0
        heating_efficiency = (total_energy_used_kwh / total_energy_needed_kwh * 100) if total_energy_needed_kwh > 0 else 0
        
        # Create daily, weekly, and monthly aggregations
        daily_agg = self._create_time_aggregation(result_df, 'daily')
        weekly_agg = self._create_time_aggregation(result_df, 'weekly')
        monthly_agg = self._create_time_aggregation(result_df, 'monthly')
        
        # Store results
        self.results = {
            'result_df': result_df,
            'daily_agg': daily_agg,
            'weekly_agg': weekly_agg,
            'monthly_agg': monthly_agg,
            'total_surplus_kwh': total_surplus_kwh,
            'total_energy_used_kwh': total_energy_used_kwh,
            'total_energy_needed_kwh': total_energy_needed_kwh,
            'total_gas_needed_m3': total_gas_needed_m3,
            'total_gas_saved_m3': total_gas_saved_m3,
            'total_financial_savings': total_financial_savings,
            'surplus_utilization_percent': surplus_utilization,
            'heating_efficiency_percent': heating_efficiency,
            'daily_energy_needed_kwh': self._calculate_daily_water_heating_energy(),
            'gas_price': self.gas_price,
            'annual_projection': {
                'gas_saved_m3': total_gas_saved_m3 * (365 / len(daily_agg)),
                'financial_savings': total_financial_savings * (365 / len(daily_agg))
            }
        }
        
        return self.results
    
    def _calculate_daily_water_heating_energy(self) -> float:
        """
        Calculate the daily energy required for water heating.
        
        Returns:
            Energy required in kWh
        """
        # Energy needed without efficiency considerations
        energy_needed = self.daily_usage * self.specific_heat_capacity * self.water_temp_rise
        
        # Adjust for boiler efficiency
        energy_needed_with_efficiency = energy_needed / self.efficiency
        
        return energy_needed_with_efficiency
    
    def _get_interval_hot_water_usage(self, hour_of_day: int, interval_hours: float) -> float:
        """
        Calculate hot water usage for a specific time interval.
        
        Args:
            hour_of_day: Hour of the day (0-23)
            interval_hours: Length of the time interval in hours
        
        Returns:
            Hot water usage for this interval in liters
        """
        # Get usage percentage for this hour from the profile
        hourly_percentage = self.hourly_usage_profile.get(hour_of_day, 0.0)
        
        # Calculate daily usage portion for this time interval
        interval_usage = self.daily_usage * hourly_percentage * interval_hours
        
        return interval_usage
    
    def _calculate_interval_heat_loss(self, water_temp: float, water_volume: float, interval_hours: float) -> float:
        """
        Calculate heat loss for a specific time interval.
        
        Args:
            water_temp: Current water temperature in °C
            water_volume: Current water volume in liters
            interval_hours: Length of the time interval in hours
        
        Returns:
            Heat loss for this interval in kWh
        """
        if water_volume <= 0 or water_temp <= self._get_cold_water_temp():
            return 0.0
        
        # Calculate stored heat energy
        stored_heat = water_volume * self.specific_heat_capacity * (water_temp - self._get_cold_water_temp())
        
        # Calculate hourly heat loss rate (as a fraction of stored heat)
        hourly_loss_rate = self.standby_loss / 24
        
        # Calculate heat loss for this interval
        interval_loss = stored_heat * hourly_loss_rate * interval_hours
        
        return interval_loss
    
    def _get_cold_water_temp(self) -> float:
        """
        Get the cold water input temperature.
        
        Returns:
            Cold water temperature in °C
        """
        return self.boiler_config.get('cold_water_temp', 10.0)
    
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
    
    def _default_usage_profile(self) -> Dict[int, float]:
        """
        Get default hourly hot water usage profile.
        
        Returns:
            Dictionary mapping hour of day (0-23) to usage fraction
        """
        # Default hourly distribution percentages (must sum to 1.0)
        profile = {
            5: 0.05,   # 5 AM
            6: 0.15,   # 6 AM
            7: 0.20,   # 7 AM
            8: 0.10,   # 8 AM
            9: 0.05,   # 9 AM
            12: 0.05,  # 12 PM
            17: 0.05,  # 5 PM
            18: 0.05,  # 6 PM
            19: 0.05,  # 7 PM
            20: 0.10,  # 8 PM
            21: 0.10,  # 9 PM
            22: 0.05   # 10 PM
        }
        return profile
    
    def _create_time_aggregation(self, df: pd.DataFrame, period: str) -> pd.DataFrame:
        """
        Create time-based aggregations of boiler data.
        
        Args:
            df: DataFrame with boiler simulation results
            period: Aggregation period ('daily', 'weekly', 'monthly')
            
        Returns:
            Aggregated DataFrame
        """
        # Ensure timestamp is datetime
        if not pd.api.types.is_datetime64_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create aggregation column
        if period == 'daily':
            df['period'] = df['timestamp'].dt.date
        elif period == 'weekly':
            df['period'] = df['timestamp'].dt.to_period('W').dt.start_time
        elif period == 'monthly':
            df['period'] = df['timestamp'].dt.to_period('M').dt.start_time
        else:
            return pd.DataFrame()  # Return empty DataFrame for invalid period
        
        # Columns to aggregate
        agg_columns = [
            'surplus_energy_kwh', 
            'energy_needed_kwh', 
            'energy_used_kwh', 
            'heat_loss_kwh',
            'gas_needed_m3', 
            'gas_saved_m3', 
            'financial_savings'
        ]
        
        # Aggregate the data
        agg_df = df.groupby('period')[agg_columns].sum().reset_index()
        
        # Calculate additional metrics
        agg_df['surplus_utilization'] = (agg_df['energy_used_kwh'] / agg_df['surplus_energy_kwh'] * 100).replace([np.inf, -np.inf], 0).fillna(0)
        agg_df['heating_coverage'] = (agg_df['energy_used_kwh'] / agg_df['energy_needed_kwh'] * 100).replace([np.inf, -np.inf], 0).fillna(0)
        
        return agg_df
    
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
        
        # Format annual projection
        annual_gas_saved = self.results['annual_projection']['gas_saved_m3']
        annual_savings = utils.format_currency(
            self.results['annual_projection']['financial_savings']
        )
        
        return {
            'daily_hot_water_usage': f"{self.daily_usage} L",
            'daily_energy_needed': f"{self.results['daily_energy_needed_kwh']:.2f} kWh",
            'total_surplus_energy': f"{self.results['total_surplus_kwh']:.2f} kWh",
            'total_energy_used': f"{self.results['total_energy_used_kwh']:.2f} kWh",
            'surplus_utilization': f"{self.results['surplus_utilization_percent']:.1f}%",
            'heating_efficiency': f"{self.results['heating_efficiency_percent']:.1f}%",
            'gas_saved': f"{self.results['total_gas_saved_m3']:.2f} m³",
            'financial_savings': formatted_savings,
            'projected_annual_gas_saved': f"{annual_gas_saved:.2f} m³",
            'projected_annual_savings': annual_savings,
        }
    
    def get_hourly_usage_summary(self) -> Dict[str, float]:
        """
        Get a summary of hourly hot water usage distribution.
        
        Returns:
            Dictionary with hour (0-23) as key and percentage as value
        """
        return {f"{hour}:00": (percentage * 100) for hour, percentage in self.hourly_usage_profile.items()}
