"""
Unit tests for the battery module of the Zonnepanelen_check application.
"""
import sys
import os
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to the path to import modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from battery_module import BatteryCalculator
from storage_calculator import StorageSimulation


class TestBatteryCalculator(unittest.TestCase):
    """Test cases for the BatteryCalculator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a simple DataFrame with 24 hours of data
        start_time = datetime(2024, 1, 1, 0, 0)
        times = [start_time + timedelta(hours=i) for i in range(24)]
        
        # Create alternating surplus and deficit
        # Morning: consumption > production
        # Midday: production > consumption (surplus)
        # Evening: consumption > production
        production = [0, 0, 0, 0, 0, 0, 100, 300, 700, 1000, 1200, 1300, 
                     1200, 1000, 800, 600, 300, 100, 0, 0, 0, 0, 0, 0]
        consumption = [200, 150, 100, 100, 150, 200, 300, 400, 500, 500, 500, 500, 
                      500, 500, 400, 400, 500, 600, 700, 600, 500, 400, 300, 250]
        
        # Create test data
        self.test_data = pd.DataFrame({
            'Date/Time': times,
            'Energy Produced (Wh)': production,
            'Energy Consumed (Wh)': consumption
        })
        
        # Set up default configuration
        self.config = {
            'battery': {
                'capacity': 5.0,  # kWh
                'efficiency': 0.9,  # 90%
                'max_charge_rate': 3.6,  # kW
                'max_discharge_rate': 3.6,  # kW
                'min_soc': 10,  # %
                'max_soc': 90,  # %
                'installation_cost': 5000,  # €
                'expected_lifetime': 10,  # years
                'expected_cycles': 3650  # cycles
            },
            'economic': {
                'electricity_price': 0.22,  # €/kWh
                'feed_in_tariff': 0.09,  # €/kWh
            }
        }
        
        # Create calculator instance
        self.calculator = BatteryCalculator(self.test_data, self.config)
    
    def test_initialization(self):
        """Test that the calculator initializes with correct configuration."""
        self.assertEqual(self.calculator.capacity, 5.0)
        self.assertEqual(self.calculator.efficiency, 0.9)
        self.assertEqual(self.calculator.max_charge_rate, 3.6)
        self.assertEqual(self.calculator.max_discharge_rate, 3.6)
        self.assertEqual(self.calculator.min_soc, 10)
        self.assertEqual(self.calculator.max_soc, 90)
        self.assertEqual(self.calculator.electricity_price, 0.22)
        self.assertEqual(self.calculator.feed_in_tariff, 0.09)
    
    def test_data_interval_detection(self):
        """Test that the data interval is correctly detected."""
        interval = self.calculator._get_data_interval_hours()
        self.assertEqual(interval, 1.0)  # 1 hour intervals
    
    def test_get_surplus_energy(self):
        """Test calculation of surplus energy."""
        surplus = self.calculator.get_surplus_energy()
        self.assertEqual(len(surplus), 24)
        # Check a few specific values
        self.assertEqual(surplus[0], -200)  # Consumption > Production
        self.assertEqual(surplus[11], 800)  # Production > Consumption
        self.assertEqual(surplus[20], -500)  # Consumption > Production
    
    def test_calculate_basic_results(self):
        """Test that basic calculation runs and returns expected result types."""
        results = self.calculator.calculate()
        
        # Check that key results are present
        self.assertIn('result_df', results)
        self.assertIn('daily_agg', results)
        self.assertIn('monthly_agg', results)
        self.assertIn('total_charged_kwh', results)
        self.assertIn('total_discharged_kwh', results)
        self.assertIn('total_savings_eur', results)
        
        # Check result DataFrame has expected columns
        result_df = results['result_df']
        expected_columns = [
            'timestamp', 'surplus_energy_wh', 'hour_of_day', 'day_of_week',
            'surplus_energy_kwh', 'battery_state_kwh', 'charged_kwh', 
            'discharged_kwh', 'wasted_kwh', 'grid_import_kwh', 
            'grid_export_kwh', 'savings_import_eur', 'savings_export_eur', 
            'total_savings_eur'
        ]
        for col in expected_columns:
            self.assertIn(col, result_df.columns)
    
    def test_storage_simulation_energy_balance(self):
        """Test energy balance in storage simulation."""
        # Create a simulation
        sim = StorageSimulation(
            capacity_kwh=5.0,
            efficiency=0.9,
            max_charge_rate=3.6,
            max_discharge_rate=3.6,
            min_soc_percent=10,
            max_soc_percent=90
        )
        
        # Simulate some charging and discharging
        # Charge with 1 kWh
        sim.simulate_timestep(surplus_energy_wh=1000, time_interval_hours=1.0)
        # Charge with another 1 kWh
        sim.simulate_timestep(surplus_energy_wh=1000, time_interval_hours=1.0)
        # Discharge with 0.5 kWh
        sim.simulate_timestep(surplus_energy_wh=-500, time_interval_hours=1.0)
        
        # Get results
        results = sim.get_results()
        
        # Check energy balance
        # Energy in = 2 kWh, with 90% efficiency = 1.8 kWh stored
        # Energy out = 0.5 kWh
        # Expected state of charge = 0.5 (min) + 1.8 - 0.5 = 1.8 kWh
        self.assertAlmostEqual(results['final_soc_kwh'], 1.8, places=2)
        self.assertAlmostEqual(results['total_charged_kwh'], 2.0, places=2)
        self.assertAlmostEqual(results['total_discharged_kwh'], 0.5, places=2)
    
    def test_financial_calculations(self):
        """Test financial calculations with controlled simulation."""
        # Create simplified test data with 3 intervals:
        # 1. Surplus of 1 kWh - should be charged
        # 2. Surplus of 2 kWh - should be charged up to battery limit
        # 3. Deficit of 0.5 kWh - should be discharged from battery
        test_times = [datetime(2024, 1, 1, i) for i in range(3)]
        test_df = pd.DataFrame({
            'Date/Time': test_times,
            'Energy Produced (Wh)': [1500, 2500, 0],
            'Energy Consumed (Wh)': [500, 500, 500]
        })
        
        # Create a calculator with a small battery to test limits
        test_config = self.config.copy()
        test_config['battery']['capacity'] = 1.5  # kWh
        test_config['battery']['max_charge_rate'] = 1.0  # kW
        
        calculator = BatteryCalculator(test_df, test_config)
        results = calculator.calculate()
        
        # Expected results:
        # 1st hour: 1kWh surplus, charge 1kWh (limited by charge rate), store 0.9kWh (due to efficiency)
        # 2nd hour: 2kWh surplus, charge remaining 0.5kWh to reach max capacity (1.35kWh), store 0.45kWh
        # 3rd hour: 0.5kWh deficit, discharge 0.5kWh
        
        # Charges: 1.0 + 0.5 = 1.5 kWh
        # Discharges: 0.5 kWh
        # Import savings: 0.5 kWh * 0.22 €/kWh = 0.11 €
        # Export losses: 1.5 kWh * 0.09 €/kWh = 0.135 €
        
        self.assertAlmostEqual(results['total_charged_kwh'], 1.5, places=2)
        self.assertAlmostEqual(results['total_discharged_kwh'], 0.5, places=2)
        self.assertAlmostEqual(results['import_savings_eur'], 0.11, places=2)
        self.assertAlmostEqual(results['export_losses_eur'], -0.135, places=2)
        self.assertAlmostEqual(results['total_savings_eur'], -0.025, places=3)  # Net loss
    
    def test_roi_metrics(self):
        """Test ROI metrics calculation."""
        # Calculate results
        results = self.calculator.calculate()
        
        # Test that ROI metrics are present
        roi_metrics = results['roi_metrics']
        self.assertIn('daily_savings_eur', roi_metrics)
        self.assertIn('annual_savings_eur', roi_metrics)
        self.assertIn('payback_years', roi_metrics)
        self.assertIn('roi_percent', roi_metrics)
        
        # Test formula relationships
        daily_savings = roi_metrics['daily_savings_eur']
        annual_savings = roi_metrics['annual_savings_eur']
        payback_years = roi_metrics['payback_years']
        roi_percent = roi_metrics['roi_percent']
        installation_cost = roi_metrics['installation_cost_eur']
        
        # Annual savings should be 365 * daily savings
        self.assertAlmostEqual(annual_savings, daily_savings * 365, places=2)
        
        # Payback years should be installation_cost / annual_savings
        if annual_savings > 0:
            self.assertAlmostEqual(payback_years, installation_cost / annual_savings, places=2)
        
        # ROI percent should be (annual_savings / installation_cost) * 100
        self.assertAlmostEqual(roi_percent, (annual_savings / installation_cost) * 100, places=2)
    
    def test_time_aggregation(self):
        """Test time-based aggregation functions."""
        # Get calculation results
        results = self.calculator.calculate()
        result_df = results['result_df']
        
        # Test daily aggregation
        daily_agg = self.calculator._create_time_aggregation(result_df, 'daily')
        
        # Should have 1 row for 1 day of data
        self.assertEqual(len(daily_agg), 1)
        
        # Test monthly aggregation
        monthly_agg = self.calculator._create_time_aggregation(result_df, 'monthly')
        
        # Should have 1 row for 1 month of data
        self.assertEqual(len(monthly_agg), 1)
        
        # Test invalid period
        invalid_agg = self.calculator._create_time_aggregation(result_df, 'invalid')
        self.assertEqual(len(invalid_agg), 0)  # Should return empty DataFrame
    
    def test_get_summary(self):
        """Test getting summary metrics."""
        # Ensure calculation has run
        self.calculator.calculate()
        
        # Get summary
        summary = self.calculator.get_summary()
        
        # Test that summary contains expected keys
        expected_keys = [
            'battery_capacity', 'battery_efficiency', 'total_surplus_energy',
            'total_stored_energy', 'total_used_from_battery', 'storage_utilization',
            'self_consumption_with_battery', 'financial_savings', 'payback_period'
        ]
        for key in expected_keys:
            self.assertIn(key, summary)


if __name__ == '__main__':
    unittest.main()
