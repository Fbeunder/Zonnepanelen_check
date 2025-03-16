"""
Storage calculator module for the Zonnepanelen_check application.

This module provides base classes and common functionality for
simulating and calculating energy storage options.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Union, Optional
from abc import ABC, abstractmethod
import utils


class StorageCalculator(ABC):
    """
    Abstract base class for energy storage calculators.
    
    This class defines the common interface and shared functionality
    for different energy storage options.
    """
    
    def __init__(self, data: pd.DataFrame, config: Dict[str, Any]):
        """
        Initialize the storage calculator with data and configuration.
        
        Args:
            data: DataFrame containing energy production and consumption data
            config: Dictionary with configuration parameters
        """
        self.data = data
        self.config = config
        self.results = None
        
    @abstractmethod
    def calculate(self) -> Dict[str, Any]:
        """
        Perform storage calculations and return results.
        
        This method must be implemented by all derived classes.
        
        Returns:
            Dictionary containing calculation results
        """
        pass
    
    def get_surplus_energy(self) -> pd.Series:
        """
        Get the surplus energy (production - consumption) from the data.
        
        Returns:
            Pandas Series with surplus energy values
        """
        if 'surplus_energy' in self.data.columns:
            return self.data['surplus_energy']
        
        elif ('Energy Produced (Wh)' in self.data.columns and 
              'Energy Consumed (Wh)' in self.data.columns):
            return self.data['Energy Produced (Wh)'] - self.data['Energy Consumed (Wh)']
        
        else:
            # Return a series of zeros with the same index as data
            return pd.Series(0, index=self.data.index)
    
    def get_potential_savings(self, stored_energy_kwh: float, price_per_kwh: float) -> float:
        """
        Calculate potential financial savings based on stored energy.
        
        Args:
            stored_energy_kwh: Amount of energy stored/utilized in kWh
            price_per_kwh: Price per kWh in Euro
            
        Returns:
            Financial savings in Euro
        """
        return stored_energy_kwh * price_per_kwh
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of storage calculation results.
        
        Returns:
            Dictionary with summary metrics
        """
        if self.results is None:
            return {}
        
        return self.results


class StorageSimulation:
    """
    Class for simulating energy storage with time-based constraints.
    
    This is a utility class that can be used by specific storage
    calculator implementations to simulate storage over time.
    """
    
    def __init__(self, capacity_kwh: float, efficiency: float, 
                 max_charge_rate: float, max_discharge_rate: float,
                 min_soc_percent: float = 0, max_soc_percent: float = 100):
        """
        Initialize the storage simulation with parameters.
        
        Args:
            capacity_kwh: Storage capacity in kWh
            efficiency: Round-trip efficiency (0-1)
            max_charge_rate: Maximum charge rate in kW
            max_discharge_rate: Maximum discharge rate in kW
            min_soc_percent: Minimum state of charge in percent
            max_soc_percent: Maximum state of charge in percent
        """
        self.capacity_kwh = capacity_kwh
        self.efficiency = efficiency
        self.max_charge_rate = max_charge_rate
        self.max_discharge_rate = max_discharge_rate
        self.min_soc_kwh = capacity_kwh * (min_soc_percent / 100)
        self.max_soc_kwh = capacity_kwh * (max_soc_percent / 100)
        
        # Initialize state
        self.state_of_charge = self.min_soc_kwh
        self.charged_energy = 0
        self.discharged_energy = 0
        self.wasted_energy = 0
    
    def simulate_timestep(self, surplus_energy_wh: float, 
                         time_interval_hours: float = 0.25) -> Dict[str, float]:
        """
        Simulate one timestep of the storage system.
        
        Args:
            surplus_energy_wh: Surplus energy in Wh (positive for excess, negative for deficit)
            time_interval_hours: Time interval in hours
            
        Returns:
            Dictionary with simulation results for this timestep
        """
        surplus_energy_kwh = surplus_energy_wh / 1000
        
        # Calculate charge and discharge limits for this timestep
        max_charge_this_step = min(
            self.max_charge_rate * time_interval_hours,  # Limited by charge rate
            self.max_soc_kwh - self.state_of_charge      # Limited by remaining capacity
        )
        
        max_discharge_this_step = min(
            self.max_discharge_rate * time_interval_hours,   # Limited by discharge rate
            self.state_of_charge - self.min_soc_kwh          # Limited by available energy
        )
        
        # Track energy flows for this timestep
        charged = 0
        discharged = 0
        wasted = 0
        
        if surplus_energy_kwh > 0:
            # We have excess energy to store
            charge_amount = min(surplus_energy_kwh, max_charge_this_step)
            actual_charge = charge_amount * self.efficiency  # Account for charging losses
            self.state_of_charge += actual_charge
            charged = charge_amount
            wasted = surplus_energy_kwh - charge_amount  # Excess that couldn't be stored
            
        elif surplus_energy_kwh < 0:
            # We need energy from storage
            energy_needed = abs(surplus_energy_kwh)
            discharge_amount = min(energy_needed, max_discharge_this_step)
            self.state_of_charge -= discharge_amount
            discharged = discharge_amount
            
        # Update cumulative totals
        self.charged_energy += charged
        self.discharged_energy += discharged
        self.wasted_energy += wasted
        
        return {
            'state_of_charge': self.state_of_charge,
            'charged_kwh': charged,
            'discharged_kwh': discharged,
            'wasted_kwh': wasted
        }
    
    def reset(self) -> None:
        """Reset the simulation to initial state."""
        self.state_of_charge = self.min_soc_kwh
        self.charged_energy = 0
        self.discharged_energy = 0
        self.wasted_energy = 0
    
    def get_results(self) -> Dict[str, float]:
        """
        Get the cumulative simulation results.
        
        Returns:
            Dictionary with simulation results
        """
        return {
            'total_charged_kwh': self.charged_energy,
            'total_discharged_kwh': self.discharged_energy,
            'total_wasted_kwh': self.wasted_energy,
            'final_soc_kwh': self.state_of_charge,
            'final_soc_percent': (self.state_of_charge / self.capacity_kwh) * 100
        }
