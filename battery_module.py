"""
Battery module for the Zonnepanelen_check application.

This module provides functionality for simulating and calculating
energy savings by using surplus solar energy for battery storage.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Union, Optional, Any
import utils
from utils.energy_calculations import convert_wh_to_kwh
from storage_calculator import StorageCalculator, StorageSimulation


class BatteryCalculator(StorageCalculator):
    """
    Class for calculating energy savings using surplus solar energy for battery storage.
    
    This class simulates a home battery system that stores surplus solar energy
    and uses it when needed, calculating the resulting electricity and financial savings.
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
        self.capacity = self.battery_config.get('capacity', 10.0)  # kWh
        self.efficiency = self.battery_config.get('efficiency', 0.9)  # 90%
        self.max_charge_rate = self.battery_config.get('max_charge_rate', 3.6)  # kW
        self.max_discharge_rate = self.battery_config.get('max_discharge_rate', 3.6)  # kW
        self.min_soc = self.battery_config.get('min_soc', 10)  # %
        self.max_soc = self.battery_config.get('max_soc', 90)  # %
        self.installation_cost = self.battery_config.get('installation_cost', 5000)  # €
        self.expected_lifetime = self.battery_config.get('expected_lifetime', 10)  # years
        self.expected_cycles = self.battery_config.get('expected_cycles', 3650)  # cycles
        
        # Get economic parameters
        self.electricity_price = self.economic_config.get('electricity_price', 0.22)  # €/kWh
        self.feed_in_tariff = self.economic_config.get('feed_in_tariff', 0.09)  # €/kWh
        
        # Initialize results
        self.results = None
    
    def calculate(self) -> Dict[str, Any]:
        """
        Perform battery calculations and return results.
        
        This method simulates the battery usage throughout the provided data timeline,
        accounting for battery constraints, charging and discharging patterns,
        and financial savings.
        
        Returns:
            Dictionary containing calculation results
        """
        if self.data is None or len(self.data) == 0:
            return {}
        
        # Get surplus energy
        surplus_energy = self.get_surplus_energy()
        
        # Get the time interval of the data
        interval_hours = self._get_data_interval_hours()
        
        # Initialize battery simulation
        battery_sim = StorageSimulation(
            capacity_kwh=self.capacity,
            efficiency=self.efficiency,
            max_charge_rate=self.max_charge_rate,
            max_discharge_rate=self.max_discharge_rate,
            min_soc_percent=self.min_soc,
            max_soc_percent=self.max_soc
        )
        
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
        result_df['battery_state_kwh'] = np.nan
        result_df['charged_kwh'] = 0.0
        result_df['discharged_kwh'] = 0.0
        result_df['wasted_kwh'] = 0.0
        result_df['grid_import_kwh'] = 0.0
        result_df['grid_export_kwh'] = 0.0
        result_df['savings_import_eur'] = 0.0
        result_df['savings_export_eur'] = 0.0
        result_df['total_savings_eur'] = 0.0
        
        # Keep track of the number of cycles
        cycle_count = 0
        total_discharged = 0
        
        # Iterate through each time interval
        for i in range(len(result_df)):
            # Simulate one timestep of the battery
            surplus_kwh = result_df.loc[i, 'surplus_energy_kwh']
            
            # Run simulation step
            sim_result = battery_sim.simulate_timestep(
                surplus_energy_wh=surplus_kwh * 1000,  # Convert back to Wh
                time_interval_hours=interval_hours
            )
            
            # Store simulation results in the result dataframe
            result_df.loc[i, 'battery_state_kwh'] = sim_result['state_of_charge']
            result_df.loc[i, 'charged_kwh'] = sim_result['charged_kwh']
            result_df.loc[i, 'discharged_kwh'] = sim_result['discharged_kwh']
            result_df.loc[i, 'wasted_kwh'] = sim_result['wasted_kwh']
            
            # Calculate grid interactions
            if surplus_kwh > 0:
                # Excess production: export what couldn't be stored
                result_df.loc[i, 'grid_export_kwh'] = sim_result['wasted_kwh']
                result_df.loc[i, 'grid_import_kwh'] = 0
            else:
                # Energy deficit: import what couldn't be discharged
                deficit_kwh = abs(surplus_kwh)
                discharged_kwh = sim_result['discharged_kwh']
                result_df.loc[i, 'grid_import_kwh'] = deficit_kwh - discharged_kwh
                result_df.loc[i, 'grid_export_kwh'] = 0
            
            # Calculate financial savings
            # 1. Savings from reduced imports
            result_df.loc[i, 'savings_import_eur'] = sim_result['discharged_kwh'] * self.electricity_price
            
            # 2. Lost feed-in tariff for stored energy
            # (We're storing energy instead of exporting it, so we "lose" the feed-in tariff on that energy)
            result_df.loc[i, 'savings_export_eur'] = -sim_result['charged_kwh'] * self.feed_in_tariff
            
            # 3. Total savings (imports savings - export losses)
            result_df.loc[i, 'total_savings_eur'] = (
                result_df.loc[i, 'savings_import_eur'] + 
                result_df.loc[i, 'savings_export_eur']
            )
            
            # Track battery cycles
            total_discharged += sim_result['discharged_kwh']
            cycle_count = total_discharged / self.capacity
        
        # Get final simulation results
        sim_results = battery_sim.get_results()
        
        # Calculate total values and other metrics
        total_surplus_kwh = result_df['surplus_energy_kwh'].sum()
        total_charged_kwh = sim_results['total_charged_kwh']
        total_discharged_kwh = sim_results['total_discharged_kwh']
        total_wasted_kwh = sim_results['total_wasted_kwh']
        total_import_savings = result_df['savings_import_eur'].sum()
        total_export_losses = result_df['savings_export_eur'].sum()
        total_savings = result_df['total_savings_eur'].sum()
        
        # Calculate utilization percentage and efficiency metrics
        if total_surplus_kwh > 0:
            storage_utilization = (total_charged_kwh / total_surplus_kwh) * 100
        else:
            storage_utilization = 0
            
        # Calculate self-consumption metrics
        # (how much of home consumption is covered by solar + battery)
        total_consumption_kwh = 0
        total_production_kwh = 0
        
        if 'Energy Consumed (Wh)' in self.data.columns and 'Energy Produced (Wh)' in self.data.columns:
            total_consumption_kwh = self.data['Energy Consumed (Wh)'].sum() / 1000
            total_production_kwh = self.data['Energy Produced (Wh)'].sum() / 1000
            
            # Calculate what would be imported without battery
            would_be_imported = result_df['grid_import_kwh'].sum() + total_discharged_kwh
            
            # Calculate self-consumption percentage with and without battery
            self_consumption_with_battery = ((total_consumption_kwh - result_df['grid_import_kwh'].sum()) / 
                                            total_consumption_kwh) * 100
            self_consumption_without_battery = ((total_consumption_kwh - would_be_imported) / 
                                               total_consumption_kwh) * 100
        else:
            self_consumption_with_battery = 0
            self_consumption_without_battery = 0
            would_be_imported = 0
        
        # Create daily, weekly, and monthly aggregations
        daily_agg = self._create_time_aggregation(result_df, 'daily')
        weekly_agg = self._create_time_aggregation(result_df, 'weekly')
        monthly_agg = self._create_time_aggregation(result_df, 'monthly')
        
        # Calculate ROI and payback period
        data_days = (timestamps.max() - timestamps.min()).days
        if data_days > 0:
            annual_savings = total_savings * (365 / data_days)
            payback_years = self.installation_cost / annual_savings if annual_savings > 0 else float('inf')
            roi_percent = (annual_savings / self.installation_cost) * 100 if self.installation_cost > 0 else 0
        else:
            annual_savings = 0
            payback_years = float('inf')
            roi_percent = 0
            
        # Calculate battery degradation metrics
        # Estimate lifetime in years based on cycles
        if self.expected_cycles > 0:
            # Calculate daily cycles
            daily_cycles = cycle_count / data_days if data_days > 0 else 0
            # Estimate years until cycle limit is reached
            years_to_cycle_limit = self.expected_cycles / (daily_cycles * 365) if daily_cycles > 0 else float('inf')
            # Battery lifetime is the minimum of cycle-based limit and calendar life
            estimated_lifetime = min(years_to_cycle_limit, self.expected_lifetime)
        else:
            daily_cycles = 0
            years_to_cycle_limit = float('inf')
            estimated_lifetime = self.expected_lifetime
        
        # Store results
        self.results = {
            'result_df': result_df,
            'daily_agg': daily_agg,
            'weekly_agg': weekly_agg,
            'monthly_agg': monthly_agg,
            'total_surplus_kwh': total_surplus_kwh,
            'total_charged_kwh': total_charged_kwh,
            'total_discharged_kwh': total_discharged_kwh,
            'total_wasted_kwh': total_wasted_kwh,
            'import_savings_eur': total_import_savings,
            'export_losses_eur': total_export_losses,
            'total_savings_eur': total_savings,
            'storage_utilization_percent': storage_utilization,
            'self_consumption_with_battery_percent': self_consumption_with_battery,
            'self_consumption_without_battery_percent': self_consumption_without_battery,
            'final_soc_percent': sim_results['final_soc_percent'],
            'cycle_count': cycle_count,
            'electricity_price': self.electricity_price,
            'feed_in_tariff': self.feed_in_tariff,
            'roi_metrics': {
                'daily_savings_eur': total_savings / data_days if data_days > 0 else 0,
                'annual_savings_eur': annual_savings,
                'installation_cost_eur': self.installation_cost,
                'payback_years': payback_years,
                'roi_percent': roi_percent,
                'estimated_lifetime_years': estimated_lifetime,
                'daily_cycles': daily_cycles
            },
            'annual_projection': {
                'charged_kwh': total_charged_kwh * (365 / data_days) if data_days > 0 else 0,
                'discharged_kwh': total_discharged_kwh * (365 / data_days) if data_days > 0 else 0,
                'financial_savings_eur': annual_savings
            }
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
    
    def _create_time_aggregation(self, df: pd.DataFrame, period: str) -> pd.DataFrame:
        """
        Create time-based aggregations of battery data.
        
        Args:
            df: DataFrame with battery simulation results
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
            'charged_kwh', 
            'discharged_kwh', 
            'wasted_kwh',
            'grid_import_kwh', 
            'grid_export_kwh', 
            'savings_import_eur',
            'savings_export_eur',
            'total_savings_eur'
        ]
        
        # Aggregate the data
        agg_df = df.groupby('period')[agg_columns].sum().reset_index()
        
        # Calculate additional metrics
        # Storage utilization: percentage of surplus energy that was stored
        agg_df['storage_utilization'] = (agg_df['charged_kwh'] / agg_df['surplus_energy_kwh'] * 100).replace([np.inf, -np.inf], 0).fillna(0)
        
        # Round-trip efficiency: ratio of discharged to charged energy
        agg_df['round_trip_efficiency'] = (agg_df['discharged_kwh'] / agg_df['charged_kwh'] * 100).replace([np.inf, -np.inf], 0).fillna(0)
        
        return agg_df
    
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
        formatted_savings = utils.format_currency(
            self.results['total_savings_eur']
        )
        
        # Format annual projection
        annual_discharged = self.results['annual_projection']['discharged_kwh']
        annual_savings = utils.format_currency(
            self.results['annual_projection']['financial_savings_eur']
        )
        
        # Format ROI metrics
        payback_years = self.results['roi_metrics']['payback_years']
        payback_str = f"{payback_years:.1f} jaar" if payback_years < float('inf') else "n.v.t."
        
        return {
            'battery_capacity': f"{self.capacity:.1f} kWh",
            'battery_efficiency': f"{self.efficiency * 100:.0f}%",
            'total_surplus_energy': f"{self.results['total_surplus_kwh']:.2f} kWh",
            'total_stored_energy': f"{self.results['total_charged_kwh']:.2f} kWh",
            'total_used_from_battery': f"{self.results['total_discharged_kwh']:.2f} kWh",
            'storage_utilization': f"{self.results['storage_utilization_percent']:.1f}%",
            'self_consumption_with_battery': f"{self.results['self_consumption_with_battery_percent']:.1f}%",
            'self_consumption_without_battery': f"{self.results['self_consumption_without_battery_percent']:.1f}%",
            'financial_savings': formatted_savings,
            'cycle_count': f"{self.results['cycle_count']:.2f}",
            'payback_period': payback_str,
            'roi_percent': f"{self.results['roi_metrics']['roi_percent']:.1f}%",
            'projected_annual_used_from_battery': f"{annual_discharged:.2f} kWh",
            'projected_annual_savings': annual_savings,
        }
