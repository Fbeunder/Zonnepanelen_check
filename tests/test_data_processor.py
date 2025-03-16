"""
Unit tests for the DataProcessor class.

This module contains comprehensive tests for the DataProcessor module,
covering data loading, processing, and calculations.
"""
import unittest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path
import sys
from datetime import datetime, timedelta

# Add parent directory to path to be able to import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_processor import DataProcessor
import utils


class TestDataProcessor(unittest.TestCase):
    """Test suite for DataProcessor class."""

    def setUp(self):
        """Set up test environment before each test method."""
        self.processor = DataProcessor()
        
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a sample CSV file for testing
        self.create_sample_csv()
    
    def tearDown(self):
        """Clean up after each test method."""
        # Clean up the temporary directory
        self.temp_dir.cleanup()
    
    def create_sample_csv(self):
        """Create a sample CSV file with test data."""
        # Create a DataFrame with sample data
        start_date = datetime(2024, 1, 1)
        dates = [start_date + timedelta(minutes=15 * i) for i in range(96)]  # 24 hours worth of 15-min data
        
        data = {
            'Date/Time': [d.strftime('%d/%m/%Y %H:%M') for d in dates],
            'Energy Produced (Wh)': [0] * 32 + list(range(0, 100, 4)) + list(range(100, 0, -4)) + [0] * 32,
            'Energy Consumed (Wh)': [50 + np.random.randint(-10, 10) for _ in range(96)],
            'Exported to Grid (Wh)': [0] * 32 + [max(0, (i // 4) - 50) for i in range(32)] + [max(0, (100 - i) // 4 - 50) for i in range(32)] + [0],
            'Imported from Grid (Wh)': [50 + np.random.randint(-10, 10) for _ in range(40)] + [0] * 16 + [np.random.randint(0, 10) for _ in range(40)]
        }
        
        df = pd.DataFrame(data)
        
        # Save to a CSV file
        self.csv_path = os.path.join(self.temp_dir.name, 'test_data.csv')
        df.to_csv(self.csv_path, index=False)
        
        # Create an invalid CSV file (missing required columns)
        invalid_data = {
            'Date': [d.strftime('%d/%m/%Y') for d in dates],
            'Time': [d.strftime('%H:%M') for d in dates],
            'Production': [0] * 32 + list(range(0, 100, 4)) + list(range(100, 0, -4)) + [0] * 32
        }
        
        invalid_df = pd.DataFrame(invalid_data)
        self.invalid_csv_path = os.path.join(self.temp_dir.name, 'invalid_data.csv')
        invalid_df.to_csv(self.invalid_csv_path, index=False)
    
    def test_load_data_success(self):
        """Test loading data from a valid CSV file."""
        success = self.processor.load_data(self.csv_path)
        self.assertTrue(success)
        self.assertIsNotNone(self.processor.data)
        self.assertEqual(len(self.processor.data), 96)  # 24 hours x 4 (15-min intervals)
    
    def test_load_data_invalid_file(self):
        """Test loading data from an invalid CSV file."""
        # Test with non-existent file
        success = self.processor.load_data('non_existent_file.csv')
        self.assertFalse(success)
        
        # Test with invalid file (missing required columns)
        with self.assertRaises(ValueError):
            self.processor.load_data(self.invalid_csv_path)
    
    def test_time_interval_detection(self):
        """Test detection of time intervals between records."""
        self.processor.load_data(self.csv_path)
        self.assertEqual(self.processor.time_interval, 15)  # Should detect 15-minute intervals
    
    def test_process_data(self):
        """Test data processing functionality."""
        self.processor.load_data(self.csv_path)
        
        # Check that daily, weekly, and monthly data are created
        self.assertIsNotNone(self.processor.daily_data)
        self.assertIsNotNone(self.processor.weekly_data)
        self.assertIsNotNone(self.processor.monthly_data)
        
        # Check that surplus energy is calculated
        self.assertIn('surplus_energy', self.processor.data.columns)
    
    def test_daily_totals_calculation(self):
        """Test calculation of daily energy totals."""
        self.processor.load_data(self.csv_path)
        
        # Since our test data spans one day, we should have one row in daily_data
        self.assertEqual(len(self.processor.daily_data), 1)
        
        # Check if kWh conversion is done
        self.assertIn('Energy Produced (kWh)', self.processor.daily_data.columns)
        
        # Total energy produced should match sum of 15-minute values
        expected_total = sum([0] * 32 + list(range(0, 100, 4)) + list(range(100, 0, -4)) + [0] * 32) / 1000  # Convert to kWh
        self.assertAlmostEqual(self.processor.daily_data['Energy Produced (kWh)'].iloc[0], expected_total, places=2)
    
    def test_get_data_summary(self):
        """Test generation of data summary statistics."""
        self.processor.load_data(self.csv_path)
        summary = self.processor.get_data_summary()
        
        # Check that summary contains expected keys
        expected_keys = [
            'total_produced_kwh', 'total_consumed_kwh', 'total_exported_kwh', 
            'total_imported_kwh', 'self_consumed_kwh', 'self_sufficiency_percent'
        ]
        
        for key in expected_keys:
            self.assertIn(key, summary)
        
        # Verify some of the calculations
        self.assertAlmostEqual(
            summary['total_produced_kwh'], 
            sum([0] * 32 + list(range(0, 100, 4)) + list(range(100, 0, -4)) + [0] * 32) / 1000,
            places=2
        )
    
    def test_get_file_info(self):
        """Test retrieval of file information."""
        self.processor.load_data(self.csv_path)
        file_info = self.processor.get_file_info()
        
        # Check that file info contains expected keys
        expected_keys = ['file_name', 'file_size_kb', 'record_count', 'column_count', 'time_interval_minutes']
        
        for key in expected_keys:
            self.assertIn(key, file_info)
        
        # Verify some information
        self.assertEqual(file_info['file_name'], 'test_data.csv')
        self.assertEqual(file_info['record_count'], 96)
        self.assertEqual(file_info['time_interval_minutes'], 15)
    
    def test_get_hourly_averages(self):
        """Test calculation of hourly averages."""
        self.processor.load_data(self.csv_path)
        hourly_avg = self.processor.get_hourly_averages()
        
        # There should be 24 rows, one for each hour
        expected_hours = len(set([d.hour for d in [datetime(2024, 1, 1) + timedelta(minutes=15 * i) for i in range(96)]]))
        self.assertEqual(len(hourly_avg), expected_hours)
    
    def test_detect_anomalies(self):
        """Test anomaly detection in energy data."""
        # Load the standard data
        self.processor.load_data(self.csv_path)
        
        # Create some anomalies in the data
        self.processor.data.loc[10, 'Energy Produced (Wh)'] = 1000  # Very high production
        self.processor.data.loc[20, 'Energy Consumed (Wh)'] = -50   # Negative consumption (impossible)
        
        # Detect anomalies
        anomalies = self.processor.detect_anomalies(std_dev_threshold=2.0)
        
        # We should have anomalies in at least Energy Produced and Energy Consumed
        self.assertIn('Energy Produced (Wh)', anomalies)
        self.assertIn('Energy Consumed (Wh)', anomalies)
        
        # The anomaly records should be in the respective DataFrames
        self.assertIn(10, anomalies['Energy Produced (Wh)'].index)
        self.assertIn(20, anomalies['Energy Consumed (Wh)'].index)


if __name__ == '__main__':
    unittest.main()
