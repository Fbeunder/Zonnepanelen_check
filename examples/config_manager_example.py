"""
Example usage of the ConfigManager module.

This script demonstrates how to use the ConfigManager for
storing and retrieving application configuration.
"""
import os
import sys
import time

# Add the parent directory to the path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_manager import ConfigManager, ConfigValidationError

def main():
    """Demonstrate the ConfigManager functionality."""
    print("ConfigManager Example")
    print("=====================")
    
    # Initialize the configuration manager
    # This will create a config.yaml file in the current directory if it doesn't exist
    config = ConfigManager()
    
    print("\n1. Getting basic configuration values")
    print("--------------------------------------")
    # Get a basic configuration value with a default
    electricity_price = config.get('economic', 'electricity_price', default=0.22)
    gas_price = config.get('economic', 'gas_price', default=0.80)
    feed_in_tariff = config.get('economic', 'feed_in_tariff', default=0.09)
    
    print(f"Electricity Price: €{electricity_price}/kWh")
    print(f"Gas Price: €{gas_price}/m³")
    print(f"Feed-in Tariff: €{feed_in_tariff}/kWh")
    
    # Get a value using typed access
    battery_capacity = config.get_typed('battery', 'capacity', float, default=10.0)
    battery_efficiency = config.get_typed('battery', 'efficiency', float, default=0.9)
    
    print(f"Battery Capacity: {battery_capacity} kWh")
    print(f"Battery Efficiency: {battery_efficiency * 100:.1f}%")
    
    print("\n2. Updating configuration values")
    print("---------------------------------")
    # Update a single value
    new_electricity_price = 0.25
    print(f"Updating electricity price to €{new_electricity_price}/kWh")
    config.set('economic', 'electricity_price', new_electricity_price)
    
    # Update multiple values at once in a section
    print("Updating battery parameters...")
    config.update_section('battery', {
        'capacity': 12.0,
        'max_charge_rate': 4.0,
        'max_discharge_rate': 4.0
    })
    
    # Verify the updates
    updated_electricity_price = config.get('economic', 'electricity_price')
    updated_battery_capacity = config.get('battery', 'capacity')
    updated_charge_rate = config.get('battery', 'max_charge_rate')
    
    print(f"Updated Electricity Price: €{updated_electricity_price}/kWh")
    print(f"Updated Battery Capacity: {updated_battery_capacity} kWh")
    print(f"Updated Max Charge Rate: {updated_charge_rate} kW")
    
    print("\n3. Checking if values exist")
    print("---------------------------")
    has_visualization = config.has('visualization', 'default_chart_type')
    has_nonexistent = config.has('nonexistent', 'value')
    
    print(f"Has visualization.default_chart_type: {has_visualization}")
    print(f"Has nonexistent.value: {has_nonexistent}")
    
    print("\n4. Working with user preferences")
    print("--------------------------------")
    # If we don't have user preferences section yet, create it
    if not config.has('user_preferences', 'theme'):
        print("Setting up user preferences for the first time...")
        config.update_section('user_preferences', {
            'theme': 'dark',
            'language': 'nl',
            'show_tooltips': True,
            'auto_save': True
        })
    
    # Read user preferences
    user_theme = config.get('user_preferences', 'theme', 'light')
    user_language = config.get('user_preferences', 'language', 'nl')
    
    print(f"User Theme: {user_theme}")
    print(f"User Language: {user_language}")
    
    print("\n5. Validating configuration values")
    print("----------------------------------")
    try:
        # Validate the electricity price (must be a float between 0.05 and 1.0)
        config.validate_value('economic', 'electricity_price', float, 
                            min_value=0.05, max_value=1.0)
        print("Electricity price is valid")
        
        # Validate the battery efficiency (must be a float between 0 and 1)
        config.validate_value('battery', 'efficiency', float, 
                            min_value=0, max_value=1)
        print("Battery efficiency is valid")
        
        # Try to validate something that should fail
        config.set('battery', 'test_efficiency', 1.2)  # Invalid value (> 1.0)
        config.validate_value('battery', 'test_efficiency', float, 
                            min_value=0, max_value=1)
        
    except ConfigValidationError as e:
        print(f"Validation error: {e}")
        # Clean up the test value
        config.delete('battery', 'test_efficiency')
    
    print("\n6. Backing up and restoring configuration")
    print("-----------------------------------------")
    # Back up the current configuration
    backup_filename = "config_backup.yaml"
    print(f"Creating backup to {backup_filename}...")
    config.backup_config(backup_filename)
    
    # Make a change
    print("Changing theme to 'light'...")
    original_theme = config.get('user_preferences', 'theme')
    config.set('user_preferences', 'theme', 'light')
    
    # Verify the change
    current_theme = config.get('user_preferences', 'theme')
    print(f"Current theme: {current_theme}")
    
    # Restore from backup
    print(f"Restoring from backup {backup_filename}...")
    config.restore_from_backup(backup_filename)
    
    # Verify the restoration
    restored_theme = config.get('user_preferences', 'theme')
    print(f"Restored theme: {restored_theme}")
    
    # Clean up
    if os.path.exists(backup_filename):
        os.remove(backup_filename)
        print(f"Removed backup file {backup_filename}")
    
    print("\n7. Getting a whole configuration section")
    print("----------------------------------------")
    economic_section = config.get_section('economic')
    print("Economic section:")
    for key, value in economic_section.items():
        print(f"  {key}: {value}")
    
    print("\nExample completed successfully.")


if __name__ == "__main__":
    main()
