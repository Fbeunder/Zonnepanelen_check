"""
Configuration management module for the Zonnepanelen_check application.

This module handles storing, retrieving, and managing user settings
and configuration options for the application.
"""
import os
import yaml
import json
import logging
from typing import Dict, Any, Optional, Union, List, Type, TypeVar, cast
import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type variable for type hints
T = TypeVar('T')

class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails."""
    pass

class ConfigManager:
    """
    Class for managing application configuration and user settings.
    
    This class provides functionality to:
    - Load and save configuration from/to a file
    - Access and update configuration values
    - Validate configuration
    - Handle configuration sections
    - Provide default values
    """
    
    def __init__(self, config_file: str = "config.yaml"):
        """
        Initialize the ConfigManager with the specified config file.
        
        Args:
            config_file: Path to the configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()
        
        # Set default values if configuration is empty or missing sections
        if not self.config:
            self.config = self._get_default_config()
            self.save_config()
        else:
            # Ensure all default sections exist
            default_config = self._get_default_config()
            for section, values in default_config.items():
                if section not in self.config:
                    self.config[section] = values
                    logger.info(f"Added missing section '{section}' with default values")
            self.save_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Returns:
            Dictionary containing configuration values
        """
        if not os.path.exists(self.config_file):
            logger.info(f"Configuration file not found at '{self.config_file}'. Will create with defaults.")
            return {}
        
        try:
            file_extension = Path(self.config_file).suffix.lower()
            
            with open(self.config_file, 'r', encoding='utf-8') as file:
                if file_extension == '.yaml' or file_extension == '.yml':
                    config = yaml.safe_load(file)
                elif file_extension == '.json':
                    config = json.load(file)
                else:
                    logger.error(f"Unsupported configuration file format: {file_extension}")
                    return {}
                
                return config if config else {}
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return {}
    
    def save_config(self) -> bool:
        """
        Save current configuration to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            file_extension = Path(self.config_file).suffix.lower()
            
            with open(self.config_file, 'w', encoding='utf-8') as file:
                if file_extension == '.yaml' or file_extension == '.yml':
                    yaml.dump(self.config, file, default_flow_style=False)
                elif file_extension == '.json':
                    json.dump(self.config, file, indent=4)
                else:
                    logger.error(f"Unsupported configuration file format: {file_extension}")
                    return False
                    
            logger.info(f"Configuration saved to '{self.config_file}'")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
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
                'theme': 'light',
                'language': 'nl',
            },
            'economic': {
                'electricity_price': 0.22,  # €/kWh
                'gas_price': 0.80,  # €/m³
                'feed_in_tariff': 0.09,  # €/kWh
                'currency': 'EUR',
            },
            'data_processor': {
                'anomaly_detection': True,
                'anomaly_threshold': 3.0,  # Standard deviations
                'fill_missing_values': True,
                'interpolation_method': 'linear',
            },
            'boiler': {
                'capacity': 80,  # Liter
                'efficiency': 0.9,  # 90%
                'water_temperature_rise': 35,  # °C (from 15°C to 50°C)
                'daily_hot_water_usage': 120,  # Liter
                'installation_cost': 1200,  # €
                'maintenance_cost_yearly': 50,  # €
                'expected_lifetime': 15,  # years
            },
            'battery': {
                'capacity': 10,  # kWh
                'efficiency': 0.9,  # 90% round-trip efficiency
                'max_charge_rate': 3.6,  # kW
                'max_discharge_rate': 3.6,  # kW
                'min_soc': 10,  # %
                'max_soc': 90,  # %
                'installation_cost': 5000,  # €
                'expected_lifetime': 10,  # years
                'expected_cycles': 3650,  # cycles
            },
            'visualization': {
                'default_chart_type': 'line',
                'primary_color': '#1f77b4',
                'secondary_color': '#ff7f0e',
                'show_grid': True,
                'font_size': 12,
                'export_format': 'png',
            }
        }
    
    def get(self, section: str, key: str, default: Optional[T] = None) -> Union[T, Any]:
        """
        Get a specific configuration value.
        
        Args:
            section: Section name (e.g. 'economic', 'boiler')
            key: Configuration key to retrieve
            default: Default value to return if the key doesn't exist
            
        Returns:
            Configuration value, or default if not found
        """
        if section not in self.config:
            logger.debug(f"Section '{section}' not found in configuration")
            return default
        
        if key not in self.config[section]:
            logger.debug(f"Key '{key}' not found in section '{section}'")
            return default
        
        return self.config[section][key]
    
    def set(self, section: str, key: str, value: Any) -> bool:
        """
        Set a specific configuration value.
        
        Args:
            section: Section name (e.g. 'economic', 'boiler')
            key: Configuration key to update
            value: New value to set
            
        Returns:
            True if successful, False otherwise
        """
        if section not in self.config:
            self.config[section] = {}
            logger.info(f"Created new configuration section '{section}'")
        
        # Check if the value is changing
        old_value = self.config[section].get(key)
        if old_value != value:
            self.config[section][key] = value
            logger.info(f"Updated configuration '{section}.{key}': {old_value} -> {value}")
            return self.save_config()
        
        return True  # No changes needed
    
    def has(self, section: str, key: str) -> bool:
        """
        Check if a specific configuration key exists.
        
        Args:
            section: Section name
            key: Configuration key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        return section in self.config and key in self.config[section]
    
    def get_section(self, section: str, create_if_missing: bool = False) -> Dict[str, Any]:
        """
        Get all configuration values for a specific section.
        
        Args:
            section: Section name to retrieve
            create_if_missing: Whether to create the section if it doesn't exist
            
        Returns:
            Dictionary with section configuration values
        """
        if section not in self.config and create_if_missing:
            self.config[section] = {}
            logger.info(f"Created new empty configuration section '{section}'")
            self.save_config()
        
        return self.config.get(section, {})
    
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
            logger.info(f"Created new configuration section '{section}'")
        
        # Check which values are actually changing
        changed = False
        for key, value in values.items():
            if key not in self.config[section] or self.config[section][key] != value:
                self.config[section][key] = value
                changed = True
        
        if changed:
            logger.info(f"Updated multiple values in section '{section}'")
            return self.save_config()
        
        return True  # No changes needed
    
    def delete(self, section: str, key: str) -> bool:
        """
        Delete a specific configuration value.
        
        Args:
            section: Section name
            key: Configuration key to delete
            
        Returns:
            True if successful, False otherwise
        """
        if section in self.config and key in self.config[section]:
            del self.config[section][key]
            logger.info(f"Deleted configuration key '{section}.{key}'")
            return self.save_config()
        
        return True  # Key doesn't exist, so no action needed
    
    def delete_section(self, section: str) -> bool:
        """
        Delete an entire configuration section.
        
        Args:
            section: Section name to delete
            
        Returns:
            True if successful, False otherwise
        """
        if section in self.config:
            del self.config[section]
            logger.info(f"Deleted configuration section '{section}'")
            return self.save_config()
        
        return True  # Section doesn't exist, so no action needed
    
    def validate_value(self, section: str, key: str, value_type: Type, 
                      min_value: Optional[float] = None, 
                      max_value: Optional[float] = None,
                      allowed_values: Optional[List[Any]] = None) -> bool:
        """
        Validate a configuration value against constraints.
        
        Args:
            section: Section name
            key: Configuration key
            value_type: Expected type of the value
            min_value: Minimum allowed value (for numeric types)
            max_value: Maximum allowed value (for numeric types)
            allowed_values: List of allowed values
            
        Returns:
            True if valid, False otherwise
        
        Raises:
            ConfigValidationError: If validation fails
        """
        if not self.has(section, key):
            raise ConfigValidationError(f"Configuration '{section}.{key}' does not exist")
        
        value = self.get(section, key)
        
        # Check type
        if not isinstance(value, value_type):
            raise ConfigValidationError(
                f"Configuration '{section}.{key}' has incorrect type. "
                f"Expected {value_type.__name__}, got {type(value).__name__}"
            )
        
        # For numeric types, check min/max constraints
        if (min_value is not None or max_value is not None) and isinstance(value, (int, float)):
            if min_value is not None and value < min_value:
                raise ConfigValidationError(
                    f"Configuration '{section}.{key}' value {value} is below minimum {min_value}"
                )
            if max_value is not None and value > max_value:
                raise ConfigValidationError(
                    f"Configuration '{section}.{key}' value {value} is above maximum {max_value}"
                )
        
        # Check allowed values
        if allowed_values is not None and value not in allowed_values:
            raise ConfigValidationError(
                f"Configuration '{section}.{key}' value '{value}' is not in allowed values: {allowed_values}"
            )
        
        return True
    
    def get_typed(self, section: str, key: str, value_type: Type[T], 
                default: Optional[T] = None) -> T:
        """
        Get a configuration value with type checking.
        
        Args:
            section: Section name
            key: Configuration key
            value_type: Expected type of the value
            default: Default value if not found or wrong type
            
        Returns:
            Configuration value cast to the specified type, or default
        """
        value = self.get(section, key, default)
        
        if value is None:
            return cast(T, default)
        
        if not isinstance(value, value_type):
            logger.warning(
                f"Configuration '{section}.{key}' has incorrect type. "
                f"Expected {value_type.__name__}, got {type(value).__name__}"
            )
            return cast(T, default)
        
        return cast(T, value)
    
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
        logger.info(f"Updated last used file to '{file_path}'")
        return self.save_config()
    
    def get_last_used_file(self) -> str:
        """
        Get the path to the last used data file.
        
        Returns:
            File path as string, or empty string if not set
        """
        return self.get('general', 'last_used_file', '')
    
    def reset_to_defaults(self) -> bool:
        """
        Reset all configuration to default values.
        
        Returns:
            True if successful, False otherwise
        """
        self.config = self._get_default_config()
        logger.info("Reset configuration to default values")
        return self.save_config()
    
    def backup_config(self, backup_path: Optional[str] = None) -> bool:
        """
        Create a backup of the current configuration.
        
        Args:
            backup_path: Path for the backup file. If None, uses config_file with timestamp.
            
        Returns:
            True if successful, False otherwise
        """
        if not backup_path:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = Path(self.config_file)
            backup_path = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            
            logger.info(f"Created configuration backup at '{backup_path}'")
            return True
        except Exception as e:
            logger.error(f"Error creating configuration backup: {str(e)}")
            return False
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """
        Restore configuration from a backup file.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(backup_path):
            logger.error(f"Backup file not found at '{backup_path}'")
            return False
        
        try:
            with open(backup_path, 'r', encoding='utf-8') as src:
                with open(self.config_file, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            
            # Reload configuration
            self.config = self._load_config()
            logger.info(f"Restored configuration from backup at '{backup_path}'")
            return True
        except Exception as e:
            logger.error(f"Error restoring configuration from backup: {str(e)}")
            return False
