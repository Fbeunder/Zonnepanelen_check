"""
Example demonstrating how to use the DataProcessor class.

This script shows how to load data, process it, and retrieve various statistics
and aggregated views using the DataProcessor module.
"""
import sys
import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_processor import DataProcessor


def main():
    """Run the example data processor demonstration."""
    # Create a DataProcessor instance
    processor = DataProcessor()
    
    # Replace with your actual CSV file path
    csv_path = "path/to/your/solar_data.csv"
    
    # Check if the file exists
    if not os.path.exists(csv_path):
        print(f"ERROR: File not found: {csv_path}")
        print("Please replace with a valid CSV path in the script.")
        return
    
    # Load the CSV data
    print(f"Loading data from: {csv_path}")
    success = processor.load_data(csv_path)
    
    if not success:
        print("Failed to load data. Check the file format and try again.")
        return
    
    # Print file information
    file_info = processor.get_file_info()
    print("\n--- File Information ---")
    for key, value in file_info.items():
        print(f"{key}: {value}")
    
    # Print data summary
    summary = processor.get_data_summary()
    print("\n--- Data Summary ---")
    for key, value in summary.items():
        # Format numeric values to 2 decimal places
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")
    
    # Access the processed data
    print("\n--- Data Overview ---")
    print(f"Raw data shape: {processor.data.shape}")
    print(f"Daily data shape: {processor.daily_data.shape}")
    print(f"Weekly data shape: {processor.weekly_data.shape}")
    print(f"Monthly data shape: {processor.monthly_data.shape}")
    
    # Example: Print the first few rows of daily data
    print("\n--- Daily Data Sample ---")
    print(processor.daily_data.head())
    
    # Example: Get hourly averages
    hourly_avg = processor.get_hourly_averages()
    print("\n--- Hourly Averages Sample ---")
    print(hourly_avg.head())
    
    # Example: Get seasonal averages
    seasonal_avg = processor.get_seasonal_averages()
    print("\n--- Seasonal Averages ---")
    print(seasonal_avg)
    
    # Example: Plot daily production and consumption
    print("\n--- Creating Sample Plot ---")
    try:
        # If we have at least a week of data, plot it
        if len(processor.daily_data) >= 7:
            plt.figure(figsize=(12, 6))
            
            # Plot production and consumption
            plt.plot(
                processor.daily_data['date'], 
                processor.daily_data['Energy Produced (kWh)'], 
                'g-', 
                label='Production (kWh)'
            )
            plt.plot(
                processor.daily_data['date'], 
                processor.daily_data['Energy Consumed (kWh)'], 
                'r-', 
                label='Consumption (kWh)'
            )
            
            plt.title('Daily Energy Production and Consumption')
            plt.xlabel('Date')
            plt.ylabel('Energy (kWh)')
            plt.legend()
            plt.grid(True)
            
            # Rotate date labels for better readability
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Create output directory if it doesn't exist
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            # Save the plot
            plt.savefig(output_dir / "daily_energy.png")
            print(f"Plot saved to {output_dir / 'daily_energy.png'}")
        else:
            print("Not enough daily data for plotting (need at least 7 days)")
    
    except Exception as e:
        print(f"Error creating plot: {str(e)}")
    
    print("\nExample completed successfully!")


if __name__ == "__main__":
    main()
