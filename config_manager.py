"""
Configuration management module for the Zonnepanelen_check application.

This module handles storing, retrieving, and managing user settings
and configuration options for the application.
"""
import os
import yaml
import json
from typing import Dict, Any, Optional
import datetime


class ConfigManager:
    """
    Class for managing application configuration and user settings.
    """
    
    def __init__(self, config_file: str = "config.yaml"):
        """
        Initialize the ConfigManager with the specified config file.
        
        Args:
            config_file: Path to the configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()
        
        # Set default values if configuration is empty
        if not self.config:
            self.config = self._get_default_config()
            self.save_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Returns:
            Dictionary containing configuration values
        """
        if not os.path.exists(self.config_file):
            return {}
        
        try:
            with open(self.config_file, 'r') as file:
                config = yaml.safe_load(file)
                return config if config else {}
        except Exception as e:
            print(f"Error loading configuration: {str(e)}")
            return {}
    
    def save_config(self) -> bool:
        """
        Save current configuration to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.config_file, 'w') as file:
                yaml.dump(self.config, file, default_flow_style=False)
            return True
        except Exception as e:
            print(f"Error saving configuration: {str(e)}")
            return False
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration values.
        
        Returns:
            Dictionary with default configuration
        """
        return {
            'general': {
                'last_used_file': '',
                'last_run': None,
            },
            'economic': {
                'electricity_price': 0.22,  # €/kWh
                'gas_price': 0.80,  # €/m³
                'feed_in_tariff': 0.09,  # €/kWh
            },
            'boiler': {
                'capacity': 80,  # Liter
                'efficiency': 0.9,  # 90%
                'water_temperature_rise': 35,  # °C (from 15°C to 50°C)
                'daily_hot_water_usage': 120,  # Liter
            },
            'battery': {
                'capacity': 10,  # kWh
                'efficiency': 0.9,  # 90% round-trip efficiency
                'max_charge_rate': 3.6,  # kW
                'max_discharge_rate': 3.6,  # kW
                'min_soc': 10,  # %
                'max_soc': 90,  # %
            }
        }
    
    def get_config(self, section: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration values, optionally for a specific section.
        
        Args:
            section: Section name to retrieve, or None for the entire config
            
        Returns:
            Dictionary with configuration values
        """
        if section is None:
            return self.config
        
        return self.config.get(section, {})
    
    def update_config(self, section: str, key: str, value: Any) -> bool:
        """
        Update a specific configuration value.
        
        Args:
            section: Section name (e.g. 'economic', 'boiler')
            key: Configuration key to update
            value: New value to set
            
        Returns:
            True if successful, False otherwise
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
        return self.save_config()
    
    def update_section(self, section: str, values: Dict[str, Any]) -> bool:
        """
        Update multiple values in a section at once.
        
        Args:
            section: Section name 
            values: Dictionary of key-value pairs to update
            
        Returns:
            True if successful, False otherwise
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section].update(values)
        return self.save_config()
    
    def update_last_used_file(self, file_path: str) -> bool:
        """
        Update the last used file path in the configuration.
        
        Args:
            file_path: Path to the last used data file
            
        Returns:
            True if successful, False otherwise
        """
        if 'general' not in self.config:
            self.config['general'] = {}
        
        self.config['general']['last_used_file'] = file_path
        self.config['general']['last_run'] = datetime.datetime.now().isoformat()
        return self.save_config()
    
    def get_last_used_file(self) -> str:
        """
        Get the path to the last used data file.
        
        Returns:
            File path as string, or empty string if not set
        """
        general = self.config.get('general', {})
        return general.get('last_used_file', '')
