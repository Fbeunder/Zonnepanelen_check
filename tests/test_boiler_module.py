"""
Unit tests for the boiler module.

This module contains tests for the boiler module functionality.
"""
import os
import sys
import pathlib
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(str(pathlib.Path(__file__).parent.parent))

from boiler_module import BoilerCalculator


class TestBoilerModule(unittest.TestCase):
    """Test cases for the BoilerCalculator class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create sample data with timestamps and surplus energy
        self.dates = [
            datetime(2023, 1, 1, 8, 0) + timedelta(hours=i)
            for i in range(24 * 7)  # One week of hourly data
        ]
        
        # Generate some realistic surplus energy values
        # Morning and evening: negative surplus (consumption > production)
        # Midday: positive surplus (production > consumption)
        surplus_energy = []
        for dt in self.dates:
            hour = dt.hour
            # Nighttime (0-6): small negative values
            if 0 <= hour < 6:
                surplus = -100 - np.random.randint(0, 50)
            # Morning (6-10): larger consumption, more negative
            elif 6 <= hour < 10:
                surplus = -200 - np.random.randint(0, 100)
            # Midday (10-16): solar production, positive values
            elif 10 <= hour < 16:
                surplus = 500 + np.random.randint(0, 500)
            # Evening (16-24): back to consumption
            else:
                surplus = -300 - np.random.randint(0, 200)
            
            # Add random variation by day of week (weekend vs weekday)
            if dt.weekday() >= 5:  # Weekend
                surplus = surplus * 1.2  # More consumption and production on weekends
            
            surplus_energy.append(surplus)
        
        # Create the DataFrame
        self.data = pd.DataFrame({
            'Date/Time': self.dates,
            'surplus_energy': surplus_energy
        })
        
        # Add energy production and consumption
        self.data['Energy Produced (Wh)'] = np.maximum(0, self.data['surplus_energy']) + 300
        self.data['Energy Consumed (Wh)'] = np.maximum(0, -self.data['surplus_energy']) + 300
        
        # Default configuration
        self.config = {
            'boiler': {
                'capacity': 120,
                'efficiency': 0.9,
                'daily_hot_water_usage': 150,
                'water_temperature_rise': 40,
                'cold_water_temp': 10,
                'standby_loss_percent': 0.5,
                'gas_energy_content': 9.77
            },
            'economic': {
                'gas_price': 0.85
            }
        }
        
        # Create calculator instance
        self.boiler_calculator = BoilerCalculator(self.data, self.config)

    def test_initialization(self):
        """Test proper initialization of the BoilerCalculator."""
        self.assertEqual(self.boiler_calculator.capacity, 120)
        self.assertEqual(self.boiler_calculator.efficiency, 0.9)
        self.assertEqual(self.boiler_calculator.water_temp_rise, 40)
        self.assertEqual(self.boiler_calculator.daily_usage, 150)
        self.assertEqual(self.boiler_calculator.gas_price, 0.85)
        
    def test_daily_energy_calculation(self):
        """Test calculation of daily energy needed for water heating."""
        daily_energy = self.boiler_calculator._calculate_daily_water_heating_energy()
        
        # Manual calculation to verify
        specific_heat_capacity = 0.00116  # kWh/L/°C
        expected_energy = 150 * specific_heat_capacity * 40 / 0.9
        
        self.assertAlmostEqual(daily_energy, expected_energy, places=3)
    
    def test_hourly_usage_profile(self):
        """Test the hourly hot water usage profile."""
        # Get default profile
        profile = self.boiler_calculator._default_usage_profile()
        
        # Check if it's a dict and values sum to approximately 1.0
        self.assertIsInstance(profile, dict)
        self.assertAlmostEqual(sum(profile.values()), 1.0, places=3)
        
        # Check that hours are in the valid range (0-23)
        for hour in profile.keys():
            self.assertTrue(0 <= hour <= 23)
    
    def test_interval_hot_water_usage(self):
        """Test calculation of hot water usage for a specific time interval."""
        # Test for peak hour (e.g., morning hour with high usage)
        morning_hour = 7  # Assuming hour 7 has higher usage in the profile
        
        # Calculate for a 1-hour interval
        usage_1hour = self.boiler_calculator._get_interval_hot_water_usage(morning_hour, 1.0)
        
        # Get the percentage from the profile for this hour
        profile = self.boiler_calculator._default_usage_profile()
        expected_percentage = profile.get(morning_hour, 0.0)
        
        # Expected usage = daily usage * percentage for this hour * time interval
        expected_usage = self.boiler_calculator.daily_usage * expected_percentage * 1.0
        
        self.assertAlmostEqual(usage_1hour, expected_usage, places=3)
        
        # Test for 15-minute interval (should be proportionally smaller)
        usage_15min = self.boiler_calculator._get_interval_hot_water_usage(morning_hour, 0.25)
        self.assertAlmostEqual(usage_15min, expected_usage * 0.25, places=3)
    
    def test_heat_loss_calculation(self):
        """Test calculation of heat loss for a specific time interval."""
        # Set up test parameters
        water_temp = 50.0  # °C
        water_volume = 120.0  # L
        interval_hours = 1.0
        
        # Calculate heat loss
        loss = self.boiler_calculator._calculate_interval_heat_loss(water_temp, water_volume, interval_hours)
        
        # Manual calculation to verify
        cold_water_temp = self.boiler_calculator._get_cold_water_temp()
        specific_heat_capacity = 0.00116  # kWh/L/°C
        stored_heat = water_volume * specific_heat_capacity * (water_temp - cold_water_temp)
        hourly_loss_rate = self.boiler_calculator.standby_loss / 24
        expected_loss = stored_heat * hourly_loss_rate * interval_hours
        
        self.assertAlmostEqual(loss, expected_loss, places=3)
        
        # Test edge cases
        # Zero volume should give zero heat loss
        self.assertEqual(self.boiler_calculator._calculate_interval_heat_loss(water_temp, 0, interval_hours), 0)
        
        # Temperature equal to cold water temp should give zero heat loss
        cold_temp = self.boiler_calculator._get_cold_water_temp()
        self.assertEqual(self.boiler_calculator._calculate_interval_heat_loss(cold_temp, water_volume, interval_hours), 0)
    
    def test_calculation_results(self):
        """Test the overall calculation results."""
        # Run the calculation
        results = self.boiler_calculator.calculate()
        
        # Check that the expected result keys exist
        expected_keys = [
            'result_df', 'daily_agg', 'weekly_agg', 'monthly_agg',
            'total_surplus_kwh', 'total_energy_used_kwh', 'total_energy_needed_kwh',
            'total_gas_needed_m3', 'total_gas_saved_m3', 'total_financial_savings',
            'surplus_utilization_percent', 'heating_efficiency_percent',
            'daily_energy_needed_kwh', 'gas_price', 'annual_projection'
        ]
        
        for key in expected_keys:
            self.assertIn(key, results)
        
        # Check that the result DataFrame has all expected columns
        result_df = results['result_df']
        expected_columns = [
            'timestamp', 'surplus_energy_wh', 'hour_of_day', 'day_of_week',
            'surplus_energy_kwh', 'water_temp', 'water_volume', 'heat_energy_kwh',
            'hot_water_demand_l', 'energy_needed_kwh', 'energy_used_kwh',
            'heat_loss_kwh', 'gas_needed_m3', 'gas_saved_m3', 'financial_savings'
        ]
        
        for col in expected_columns:
            self.assertIn(col, result_df.columns)
        
        # Basic sanity checks on results
        self.assertTrue(results['total_surplus_kwh'] > 0)
        self.assertTrue(results['total_energy_used_kwh'] > 0)
        self.assertTrue(results['total_gas_saved_m3'] > 0)
        self.assertTrue(results['total_financial_savings'] > 0)
        
        # Energy used should not exceed surplus energy
        self.assertLessEqual(results['total_energy_used_kwh'], results['total_surplus_kwh'])
        
        # Financial savings should match gas saved times gas price
        expected_savings = results['total_gas_saved_m3'] * self.boiler_calculator.gas_price
        self.assertAlmostEqual(results['total_financial_savings'], expected_savings, places=4)
    
    def test_gas_savings(self):
        """Test that gas savings are calculated correctly."""
        # Run the calculation
        results = self.boiler_calculator.calculate()
        
        # Check gas savings calculation in a sample of rows
        result_df = results['result_df']
        
        # Pick 5 random rows to verify
        for _ in range(5):
            idx = np.random.randint(0, len(result_df))
            row = result_df.iloc[idx]
            
            # Gas saved should be energy used divided by gas energy content
            expected_gas_saved = row['energy_used_kwh'] / self.boiler_calculator._get_kwh_per_m3_gas()
            self.assertAlmostEqual(row['gas_saved_m3'], expected_gas_saved, places=4)
            
            # Financial savings should be gas saved times gas price
            expected_savings = row['gas_saved_m3'] * self.boiler_calculator.gas_price
            self.assertAlmostEqual(row['financial_savings'], expected_savings, places=4)
    
    def test_daily_aggregation(self):
        """Test that daily aggregation works correctly."""
        # Run the calculation
        results = self.boiler_calculator.calculate()
        
        # Get the daily aggregation
        daily_agg = results['daily_agg']
        
        # Check that we have the expected number of days
        expected_days = len(set(date.date() for date in self.dates))
        self.assertEqual(len(daily_agg), expected_days)
        
        # Check that the values are aggregated correctly
        result_df = results['result_df']
        result_df['date'] = pd.to_datetime(result_df['timestamp']).dt.date
        
        # Check the first day as a sample
        first_day = min(result_df['date'])
        daily_sum = result_df[result_df['date'] == first_day].sum()
        
        # The daily aggregation should match the sum of values for that day
        first_day_agg = daily_agg[daily_agg['period'] == first_day]
        if not first_day_agg.empty:
            self.assertAlmostEqual(
                first_day_agg['energy_used_kwh'].values[0],
                daily_sum['energy_used_kwh'],
                places=3
            )
            self.assertAlmostEqual(
                first_day_agg['gas_saved_m3'].values[0],
                daily_sum['gas_saved_m3'],
                places=3
            )


if __name__ == '__main__':
    unittest.main()
