"""
Unit tests for the ConfigManager module.

This module contains tests for the configuration management functionality.
"""
import os
import unittest
import tempfile
import json
import yaml
import shutil
from datetime import datetime
from pathlib import Path

import sys
# Add the parent directory to the path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_manager import ConfigManager, ConfigValidationError


class TestConfigManager(unittest.TestCase):
    """Test case for the ConfigManager class."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.yaml_config_path = os.path.join(self.test_dir, "test_config.yaml")
        self.json_config_path = os.path.join(self.test_dir, "test_config.json")
        
        # Ensure the files don't exist yet
        for path in [self.yaml_config_path, self.json_config_path]:
            if os.path.exists(path):
                os.remove(path)
    
    def tearDown(self):
        """Clean up test environment after each test."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)
    
    def test_init_creates_default_config(self):
        """Test that init creates a default configuration when the file doesn't exist."""
        config = ConfigManager(self.yaml_config_path)
        
        # Verify the file was created
        self.assertTrue(os.path.exists(self.yaml_config_path))
        
        # Verify default values were set
        self.assertIn('general', config.config)
        self.assertIn('economic', config.config)
        self.assertIn('boiler', config.config)
        self.assertIn('battery', config.config)
    
    def test_load_and_save_yaml_config(self):
        """Test loading and saving YAML configuration."""
        # Create a config with some values
        config = ConfigManager(self.yaml_config_path)
        config.set('test_section', 'test_key', 'test_value')
        
        # Create a new config manager to load the file
        config2 = ConfigManager(self.yaml_config_path)
        
        # Verify the value was loaded correctly
        self.assertEqual(
            config2.get('test_section', 'test_key'), 
            'test_value'
        )
    
    def test_load_and_save_json_config(self):
        """Test loading and saving JSON configuration."""
        # Create a config with some values
        config = ConfigManager(self.json_config_path)
        config.set('test_section', 'test_key', 'test_value')
        
        # Create a new config manager to load the file
        config2 = ConfigManager(self.json_config_path)
        
        # Verify the value was loaded correctly
        self.assertEqual(
            config2.get('test_section', 'test_key'), 
            'test_value'
        )
    
    def test_get_with_default(self):
        """Test getting a value with a default."""
        config = ConfigManager(self.yaml_config_path)
        
        # Get a non-existent value with a default
        value = config.get('nonexistent_section', 'nonexistent_key', 'default_value')
        
        # Verify the default was returned
        self.assertEqual(value, 'default_value')
    
    def test_get_existing_value(self):
        """Test getting an existing value."""
        config = ConfigManager(self.yaml_config_path)
        
        # Set a value
        config.set('test_section', 'test_key', 'test_value')
        
        # Get the value
        value = config.get('test_section', 'test_key')
        
        # Verify the value was returned
        self.assertEqual(value, 'test_value')
    
    def test_set_and_update(self):
        """Test setting and updating a value."""
        config = ConfigManager(self.yaml_config_path)
        
        # Set a new value
        config.set('test_section', 'test_key', 'initial_value')
        
        # Verify the value was set
        self.assertEqual(
            config.get('test_section', 'test_key'), 
            'initial_value'
        )
        
        # Update the value
        config.set('test_section', 'test_key', 'updated_value')
        
        # Verify the value was updated
        self.assertEqual(
            config.get('test_section', 'test_key'), 
            'updated_value'
        )
    
    def test_has_key(self):
        """Test checking if a key exists."""
        config = ConfigManager(self.yaml_config_path)
        
        # Set a value
        config.set('test_section', 'test_key', 'test_value')
        
        # Check if keys exist
        self.assertTrue(config.has('test_section', 'test_key'))
        self.assertFalse(config.has('test_section', 'nonexistent_key'))
        self.assertFalse(config.has('nonexistent_section', 'test_key'))
    
    def test_get_section(self):
        """Test getting a section."""
        config = ConfigManager(self.yaml_config_path)
        
        # Set some values in a section
        config.set('test_section', 'key1', 'value1')
        config.set('test_section', 'key2', 'value2')
        
        # Get the section
        section = config.get_section('test_section')
        
        # Verify the section contains the expected keys and values
        self.assertEqual(section['key1'], 'value1')
        self.assertEqual(section['key2'], 'value2')
    
    def test_update_section(self):
        """Test updating multiple values in a section."""
        config = ConfigManager(self.yaml_config_path)
        
        # Set an initial value
        config.set('test_section', 'existing_key', 'initial_value')
        
        # Update multiple values
        config.update_section('test_section', {
            'existing_key': 'updated_value',
            'new_key': 'new_value'
        })
        
        # Verify the values were updated
        self.assertEqual(
            config.get('test_section', 'existing_key'), 
            'updated_value'
        )
        self.assertEqual(
            config.get('test_section', 'new_key'), 
            'new_value'
        )
    
    def test_delete_key(self):
        """Test deleting a key."""
        config = ConfigManager(self.yaml_config_path)
        
        # Set a value
        config.set('test_section', 'test_key', 'test_value')
        
        # Verify the key exists
        self.assertTrue(config.has('test_section', 'test_key'))
        
        # Delete the key
        config.delete('test_section', 'test_key')
        
        # Verify the key no longer exists
        self.assertFalse(config.has('test_section', 'test_key'))
    
    def test_delete_section(self):
        """Test deleting a section."""
        config = ConfigManager(self.yaml_config_path)
        
        # Set a value in a section
        config.set('test_section', 'test_key', 'test_value')
        
        # Verify the section exists
        self.assertIn('test_section', config.config)
        
        # Delete the section
        config.delete_section('test_section')
        
        # Verify the section no longer exists
        self.assertNotIn('test_section', config.config)
    
    def test_validate_value_type(self):
        """Test validating a value's type."""
        config = ConfigManager(self.yaml_config_path)
        
        # Set values of different types
        config.set('test_section', 'int_key', 123)
        config.set('test_section', 'str_key', 'abc')
        config.set('test_section', 'float_key', 3.14)
        config.set('test_section', 'bool_key', True)
        config.set('test_section', 'list_key', [1, 2, 3])
        
        # Validate correct types
        self.assertTrue(config.validate_value('test_section', 'int_key', int))
        self.assertTrue(config.validate_value('test_section', 'str_key', str))
        self.assertTrue(config.validate_value('test_section', 'float_key', float))
        self.assertTrue(config.validate_value('test_section', 'bool_key', bool))
        self.assertTrue(config.validate_value('test_section', 'list_key', list))
        
        # Validate incorrect types
        with self.assertRaises(ConfigValidationError):
            config.validate_value('test_section', 'int_key', str)
        with self.assertRaises(ConfigValidationError):
            config.validate_value('test_section', 'str_key', int)
    
    def test_validate_value_range(self):
        """Test validating a value's range."""
        config = ConfigManager(self.yaml_config_path)
        
        # Set numeric values
        config.set('test_section', 'int_key', 50)
        
        # Validate within range
        self.assertTrue(config.validate_value('test_section', 'int_key', int, min_value=0, max_value=100))
        
        # Validate outside range
        with self.assertRaises(ConfigValidationError):
            config.validate_value('test_section', 'int_key', int, min_value=75, max_value=100)
        with self.assertRaises(ConfigValidationError):
            config.validate_value('test_section', 'int_key', int, min_value=0, max_value=25)
    
    def test_validate_allowed_values(self):
        """Test validating a value against allowed values."""
        config = ConfigManager(self.yaml_config_path)
        
        # Set a value
        config.set('test_section', 'enum_key', 'option1')
        
        # Validate allowed values
        self.assertTrue(config.validate_value(
            'test_section', 'enum_key', str, 
            allowed_values=['option1', 'option2', 'option3']
        ))
        
        # Validate not allowed
        with self.assertRaises(ConfigValidationError):
            config.validate_value(
                'test_section', 'enum_key', str, 
                allowed_values=['option2', 'option3']
            )
    
    def test_get_typed(self):
        """Test getting a value with type checking."""
        config = ConfigManager(self.yaml_config_path)
        
        # Set values of different types
        config.set('test_section', 'int_key', 123)
        config.set('test_section', 'str_key', 'abc')
        
        # Get with correct type
        self.assertEqual(config.get_typed('test_section', 'int_key', int), 123)
        self.assertEqual(config.get_typed('test_section', 'str_key', str), 'abc')
        
        # Get with incorrect type should return default
        self.assertEqual(config.get_typed('test_section', 'int_key', str, 'default'), 'default')
        self.assertEqual(config.get_typed('test_section', 'str_key', int, 456), 456)
    
    def test_update_last_used_file(self):
        """Test updating the last used file."""
        config = ConfigManager(self.yaml_config_path)
        
        # Update the last used file
        file_path = '/path/to/data.csv'
        config.update_last_used_file(file_path)
        
        # Verify the last used file was updated
        self.assertEqual(config.get_last_used_file(), file_path)
        
        # Verify the last run timestamp was set
        self.assertIsNotNone(config.get('general', 'last_run'))
    
    def test_reset_to_defaults(self):
        """Test resetting to default values."""
        config = ConfigManager(self.yaml_config_path)
        
        # Set a custom value
        config.set('test_section', 'test_key', 'test_value')
        
        # Reset to defaults
        config.reset_to_defaults()
        
        # Verify the custom section was removed
        self.assertNotIn('test_section', config.config)
        
        # Verify the default sections are present
        self.assertIn('general', config.config)
        self.assertIn('economic', config.config)
        self.assertIn('boiler', config.config)
        self.assertIn('battery', config.config)
    
    def test_backup_and_restore(self):
        """Test backup and restore functionality."""
        config = ConfigManager(self.yaml_config_path)
        
        # Set a custom value
        config.set('test_section', 'test_key', 'test_value')
        
        # Create a backup
        backup_path = os.path.join(self.test_dir, 'backup.yaml')
        config.backup_config(backup_path)
        
        # Verify the backup file exists
        self.assertTrue(os.path.exists(backup_path))
        
        # Reset to defaults
        config.reset_to_defaults()
        
        # Verify the custom section was removed
        self.assertNotIn('test_section', config.config)
        
        # Restore from backup
        config.restore_from_backup(backup_path)
        
        # Verify the custom section was restored
        self.assertIn('test_section', config.config)
        self.assertEqual(
            config.get('test_section', 'test_key'), 
            'test_value'
        )
    
    def test_backup_with_auto_filename(self):
        """Test backup with automatic filename generation."""
        config = ConfigManager(self.yaml_config_path)
        
        # Set a custom value to ensure the config is saved
        config.set('test_section', 'test_key', 'test_value')
        
        # Create a backup with auto-generated filename
        result = config.backup_config()
        
        # Verify the backup was successful
        self.assertTrue(result)
        
        # Find the backup file by listing directory contents
        files = os.listdir(self.test_dir)
        backup_files = [f for f in files if f.startswith('test_config_') and f.endswith('.yaml')]
        
        # Verify at least one backup file was created
        self.assertGreaterEqual(len(backup_files), 1)
    
    def test_integration_with_example_usage(self):
        """Test integration with the example usage from the issue description."""
        config = ConfigManager(self.yaml_config_path)
        
        # Example usage from the issue description
        file_path = config.get("general", "last_used_file_path", default="")
        boiler_efficiency = config.get("boiler", "efficiency", default=0.9)
        
        # Set values
        config.set("general", "last_used_file_path", "/path/to/my/data.csv")
        config.set("battery", "capacity_kwh", 5.0)
        
        # Check existence
        if config.has("visualization", "chart_type"):
            chart_type = config.get("visualization", "chart_type")
        
        # Verify the values were set correctly
        self.assertEqual(
            config.get("general", "last_used_file_path"), 
            "/path/to/my/data.csv"
        )
        self.assertEqual(
            config.get("battery", "capacity_kwh"), 
            5.0
        )


if __name__ == '__main__':
    unittest.main()
