"""
Data processing module for the Zonnepanelen_check application.

This module handles all data loading, processing, and manipulation
for the energy production and consumption data.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Union, Optional
import logging
import os
from pathlib import Path
import utils

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Class for processing energy production and consumption data.
    
    This class handles loading, validation, processing, and aggregation of 
    energy data from CSV files, with specific focus on solar panel production
    and home energy consumption.
    """
    
    # Expected column names in standard format
    EXPECTED_COLUMNS = [
        'Date/Time', 
        'Energy Produced (Wh)', 
        'Energy Consumed (Wh)', 
        'Exported to Grid (Wh)', 
        'Imported from Grid (Wh)'
    ]
    
    def __init__(self):
        """Initialize the DataProcessor with empty data."""
        self.data = None
        self.daily_data = None
        self.weekly_data = None
        self.monthly_data = None
        self.file_path = None
        self.file_name = None  # We'll store the filename separately
        self.time_interval = None  # Will store detected time interval in minutes
    
    def load_data(self, file_path: str) -> bool:
        """
        Load data from a CSV file with error handling for different formats.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            bool: True if loading was successful, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return False
                
            # Check file extension
            if not file_path.lower().endswith('.csv'):
                logger.error(f"File is not a CSV: {file_path}")
                return False
            
            # Attempt to load the CSV file
            logger.info(f"Loading CSV file: {file_path}")
            df = pd.read_csv(file_path)
            
            # Check if required columns exist
            self._validate_columns(df)
            
            # Convert Date/Time to datetime
            self._convert_datetime(df)
            
            # Detect the time interval
            self._detect_time_interval(df)
            
            # Convert all energy columns to numeric values
            self._convert_energy_columns_to_numeric(df)
            
            # Handle missing values
            self._handle_missing_values(df)
            
            # Store the data
            self.data = df
            self.file_path = file_path
            # Save just the filename separate from the path
            self.file_name = os.path.basename(file_path)
            
            # Process the data
            self.process_data()
            
            logger.info(f"Successfully loaded and processed {len(df)} records from {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return False
    
    def _validate_columns(self, df: pd.DataFrame) -> None:
        """
        Validate that the dataframe has the required columns.
        
        Args:
            df: DataFrame to validate
            
        Raises:
            ValueError: If required columns are missing
        """
        # Check for required columns (at minimum we need date/time, production and consumption)
        required_cols = ['Date/Time', 'Energy Produced (Wh)', 'Energy Consumed (Wh)']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            error_msg = f"Required columns missing: {missing_cols}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Check if other expected columns are present, warn if not
        optional_cols = [col for col in self.EXPECTED_COLUMNS if col not in required_cols]
        missing_optional = [col for col in optional_cols if col not in df.columns]
        
        if missing_optional:
            logger.warning(f"Optional columns missing: {missing_optional}")
    
    def _convert_datetime(self, df: pd.DataFrame) -> None:
        """
        Convert Date/Time column to datetime format with error handling.
        
        Args:
            df: DataFrame with Date/Time column
            
        Raises:
            ValueError: If Date/Time column cannot be parsed
        """
        # Try different date formats
        date_formats = ['%d/%m/%Y %H:%M', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M']
        
        for date_format in date_formats:
            try:
                df['Date/Time'] = pd.to_datetime(df['Date/Time'], format=date_format)
                logger.info(f"Successfully parsed dates using format: {date_format}")
                break
            except ValueError:
                continue
        
        # Check if conversion was successful
        if pd.api.types.is_datetime64_dtype(df['Date/Time']):
            # Sort by date/time to ensure chronological order
            df.sort_values('Date/Time', inplace=True)
        else:
            # If all formats failed, try one last attempt with automatic detection
            try:
                df['Date/Time'] = pd.to_datetime(df['Date/Time'], errors='coerce')
                
                # Check for parsing errors
                na_dates = df['Date/Time'].isna().sum()
                if na_dates > 0:
                    logger.warning(f"{na_dates} date/time values could not be parsed and were set to NaT")
                
                # If too many dates are NaT, the parsing likely failed
                if na_dates > len(df) * 0.1:  # More than 10% failed
                    raise ValueError(f"Too many date parsing errors: {na_dates} out of {len(df)}")
                
                # Sort by date/time
                df.sort_values('Date/Time', inplace=True)
                df.reset_index(drop=True, inplace=True)
                
            except Exception as e:
                error_msg = f"Could not parse Date/Time column: {str(e)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
    
    def _detect_time_interval(self, df: pd.DataFrame) -> None:
        """
        Detect the time interval between records in the dataset.
        
        Args:
            df: DataFrame with properly formatted Date/Time column
        """
        if len(df) < 2:
            logger.warning("Not enough data points to detect time interval")
            self.time_interval = None
            return
        
        # Calculate differences between consecutive timestamps
        time_diffs = df['Date/Time'].diff().dropna()
        
        # Convert to minutes and find the most common interval
        minutes_diffs = time_diffs.dt.total_seconds() / 60
        
        # Get the most common interval, rounded to nearest minute
        if len(minutes_diffs) > 0:
            # Round to handle minor deviations
            rounded_diffs = minutes_diffs.round().astype(int)
            most_common = rounded_diffs.value_counts().idxmax()
            
            # Store the interval
            self.time_interval = most_common
            logger.info(f"Detected time interval: {most_common} minutes")
        else:
            self.time_interval = None
            logger.warning("Could not detect time interval")
    
    def _convert_energy_columns_to_numeric(self, df: pd.DataFrame) -> None:
        """
        Convert all energy columns to numeric values with error handling.
        
        Args:
            df: DataFrame with energy columns
        """
        # Get all energy columns (any column with 'Energy', 'Wh', 'kWh', etc.)
        energy_cols = [col for col in df.columns if any(
            keyword in col for keyword in ['Energy', 'Wh', 'kWh', 'Exported', 'Imported']
        )]
        
        for col in energy_cols:
            # Convert to numeric, forcing errors to NaN
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Check for conversion errors
            na_count = df[col].isna().sum()
            if na_count > 0:
                logger.warning(f"{na_count} values in {col} could not be converted to numeric")
        
        # Log summary of energy columns
        logger.info(f"Converted {len(energy_cols)} energy columns to numeric values")
    
    def _handle_missing_values(self, df: pd.DataFrame) -> None:
        """
        Handle missing values in the dataframe through interpolation.
        
        Args:
            df: DataFrame to process
        """
        # Check for missing values in energy columns
        energy_cols = [col for col in df.columns if any(
            keyword in col for keyword in ['Energy', 'Wh', 'kWh', 'Exported', 'Imported']
        )]
        
        na_counts = {col: df[col].isna().sum() for col in energy_cols}
        total_nas = sum(na_counts.values())
        
        if total_nas > 0:
            logger.warning(f"Found {total_nas} missing values across all energy columns")
            
            # For smaller gaps, use interpolation
            for col in energy_cols:
                if na_counts[col] > 0:
                    # Save original count of NaNs
                    original_nas = df[col].isna().sum()
                    
                    # Interpolate missing values
                    df[col] = df[col].interpolate(method='time')
                    
                    # For any remaining NaNs (at start/end), fill with nearest valid value
                    df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
                    
                    # Log results
                    remaining_nas = df[col].isna().sum()
                    filled_nas = original_nas - remaining_nas
                    
                    if filled_nas > 0:
                        logger.info(f"Interpolated {filled_nas} missing values in {col}")
                    
                    if remaining_nas > 0:
                        logger.warning(f"Could not interpolate {remaining_nas} values in {col}")
    
    def process_data(self) -> None:
        """
        Process the loaded data to create derived datasets and calculations.
        """
        if self.data is None:
            logger.warning("No data to process")
            return
        
        # Calculate surplus energy
        self.data = utils.calculate_surplus_energy(self.data)
        
        # Calculate daily totals
        self.daily_data = self._calculate_daily_totals()
        
        # Calculate weekly totals
        self.weekly_data = self._calculate_weekly_totals()
        
        # Calculate monthly totals
        self.monthly_data = self._calculate_monthly_totals()
        
        logger.info("Data processing complete")
    
    def _calculate_daily_totals(self) -> pd.DataFrame:
        """
        Calculate daily totals for energy metrics.
        
        Returns:
            DataFrame with daily energy totals
        """
        if self.data is None:
            return pd.DataFrame()
        
        # Create a copy of data with date only
        df = self.data.copy()
        df['date'] = df['Date/Time'].dt.date
        
        # Group by date and sum energy columns
        energy_cols = [col for col in df.columns if any(term in col for term in 
                      ['Energy', 'Exported', 'Imported', 'surplus_energy'])]
        
        daily = df.groupby('date')[energy_cols].sum().reset_index()
        
        # Convert 'date' to datetime for proper plotting
        daily['date'] = pd.to_datetime(daily['date'])
        
        # Convert to more readable units (kWh)
        for col in energy_cols:
            if 'Wh' in col:
                daily[col.replace('(Wh)', '(kWh)')] = utils.convert_wh_to_kwh(daily[col])
        
        # Also convert surplus_energy if it exists
        if 'surplus_energy' in energy_cols:
            daily['surplus_energy_kwh'] = utils.convert_wh_to_kwh(daily['surplus_energy'])
            
        return daily
    
    def _calculate_weekly_totals(self) -> pd.DataFrame:
        """
        Calculate weekly totals for energy metrics.
        
        Returns:
            DataFrame with weekly energy totals
        """
        if self.data is None:
            return pd.DataFrame()
        
        # Create a copy of data with week info
        df = self.data.copy()
        # Create year-week column (format: "2024-W01" for 1st week of 2024)
        df['year_week'] = df['Date/Time'].dt.strftime('%G-W%V')
        # Also add a week_start column for plotting
        df['week_start'] = df['Date/Time'].dt.to_period('W').dt.start_time
        
        # Group by week and sum energy columns
        energy_cols = [col for col in df.columns if any(term in col for term in 
                      ['Energy', 'Exported', 'Imported', 'surplus_energy'])]
        
        weekly = df.groupby(['year_week', 'week_start'])[energy_cols].sum().reset_index()
        
        # Convert to more readable units (kWh)
        for col in energy_cols:
            if 'Wh' in col:
                weekly[col.replace('(Wh)', '(kWh)')] = utils.convert_wh_to_kwh(weekly[col])
        
        # Also convert surplus_energy if it exists
        if 'surplus_energy' in energy_cols:
            weekly['surplus_energy_kwh'] = utils.convert_wh_to_kwh(weekly['surplus_energy'])
            
        return weekly
    
    def _calculate_monthly_totals(self) -> pd.DataFrame:
        """
        Calculate monthly totals for energy metrics.
        
        Returns:
            DataFrame with monthly energy totals
        """
        if self.data is None:
            return pd.DataFrame()
        
        # Create a copy of data with month info
        df = self.data.copy()
        # Create year-month column (format: "2024-01" for January 2024)
        df['year_month'] = df['Date/Time'].dt.strftime('%Y-%m')
        # Also add a month_start column for plotting
        df['month_start'] = df['Date/Time'].dt.to_period('M').dt.start_time
        
        # Group by month and sum energy columns
        energy_cols = [col for col in df.columns if any(term in col for term in 
                      ['Energy', 'Exported', 'Imported', 'surplus_energy'])]
        
        monthly = df.groupby(['year_month', 'month_start'])[energy_cols].sum().reset_index()
        
        # Convert to more readable units (kWh)
        for col in energy_cols:
            if 'Wh' in col:
                monthly[col.replace('(Wh)', '(kWh)')] = utils.convert_wh_to_kwh(monthly[col])
        
        # Also convert surplus_energy if it exists
        if 'surplus_energy' in energy_cols:
            monthly['surplus_energy_kwh'] = utils.convert_wh_to_kwh(monthly['surplus_energy'])
            
        return monthly
    
    def get_data_summary(self) -> Dict[str, float]:
        """
        Get summary statistics for the loaded data.
        
        Returns:
            Dictionary containing summary statistics
        """
        if self.data is None:
            return {}
        
        # Calculate total production and consumption
        total_produced = self.data['Energy Produced (Wh)'].sum() / 1000  # kWh
        total_consumed = self.data['Energy Consumed (Wh)'].sum() / 1000  # kWh
        
        # Calculate grid imports and exports if available
        total_exported = 0
        total_imported = 0
        if 'Exported to Grid (Wh)' in self.data.columns:
            total_exported = self.data['Exported to Grid (Wh)'].sum() / 1000  # kWh
        if 'Imported from Grid (Wh)' in self.data.columns:
            total_imported = self.data['Imported from Grid (Wh)'].sum() / 1000  # kWh
        
        # Calculate self-consumption
        self_consumed = total_produced - total_exported if 'Exported to Grid (Wh)' in self.data.columns else 0
        
        # Calculate self-sufficiency (percentage of consumption covered by own production)
        self_sufficiency = (self_consumed / total_consumed * 100) if total_consumed > 0 else 0
        
        # Calculate surplus energy
        surplus_energy = self.data['surplus_energy'].sum() / 1000 if 'surplus_energy' in self.data.columns else 0
        
        # Get date range
        start_date = self.data['Date/Time'].min().strftime('%Y-%m-%d')
        end_date = self.data['Date/Time'].max().strftime('%Y-%m-%d')
        days_covered = (self.data['Date/Time'].max() - self.data['Date/Time'].min()).days + 1
        
        # Calculate averages
        daily_avg_production = total_produced / days_covered if days_covered > 0 else 0
        daily_avg_consumption = total_consumed / days_covered if days_covered > 0 else 0
            
        # Return the summary
        return {
            'total_produced_kwh': total_produced,
            'total_consumed_kwh': total_consumed,
            'total_exported_kwh': total_exported,
            'total_imported_kwh': total_imported,
            'self_consumed_kwh': self_consumed,
            'self_sufficiency_percent': self_sufficiency,
            'surplus_energy_kwh': surplus_energy,
            'date_range_start': start_date,
            'date_range_end': end_date,
            'days_covered': days_covered,
            'daily_avg_production_kwh': daily_avg_production,
            'daily_avg_consumption_kwh': daily_avg_consumption,
            'time_interval_minutes': self.time_interval
        }
    
    def get_file_info(self) -> Dict[str, Union[str, int]]:
        """
        Get information about the loaded file.
        
        Returns:
            Dictionary with file information
        """
        if self.data is None:
            return {}
        
        # Basisinformatie verzamelen zonder afhankelijkheid van bestandspad
        info = {
            'file_name': self.file_name or "Onbekend",
            'record_count': len(self.data),
            'column_count': len(self.data.columns),
            'time_interval_minutes': self.time_interval,
            'first_record': self.data['Date/Time'].min().strftime('%Y-%m-%d %H:%M'),
            'last_record': self.data['Date/Time'].max().strftime('%Y-%m-%d %H:%M')
        }
        
        # Alleen bestandsgrootte bepalen als het bestand bestaat en toegankelijk is
        if self.file_path is not None:
            try:
                file_path = Path(self.file_path)
                if file_path.exists():
                    info['file_size_kb'] = round(file_path.stat().st_size / 1024, 2)
                else:
                    info['file_size_kb'] = 0
            except (FileNotFoundError, OSError):
                # Bestand bestaat niet meer of is niet toegankelijk
                info['file_size_kb'] = 0
        else:
            info['file_size_kb'] = 0
            
        return info
    
    def get_hourly_averages(self) -> pd.DataFrame:
        """
        Calculate hourly averages for energy metrics across the entire dataset.
        
        Returns:
            DataFrame with hourly averages
        """
        if self.data is None:
            return pd.DataFrame()
        
        # Extract hour from the datetime
        df = self.data.copy()
        df['hour'] = df['Date/Time'].dt.hour
        
        # Group by hour and calculate mean for energy columns
        energy_cols = [col for col in df.columns if any(term in col for term in 
                      ['Energy', 'Exported', 'Imported', 'surplus_energy'])]
        
        hourly_avg = df.groupby('hour')[energy_cols].mean().reset_index()
        
        # Convert to kWh
        for col in energy_cols:
            if 'Wh' in col:
                hourly_avg[col.replace('(Wh)', '(kWh)')] = utils.convert_wh_to_kwh(hourly_avg[col])
        
        # Also convert surplus_energy if it exists
        if 'surplus_energy' in energy_cols:
            hourly_avg['surplus_energy_kwh'] = utils.convert_wh_to_kwh(hourly_avg['surplus_energy'])
        
        return hourly_avg
    
    def get_seasonal_averages(self) -> pd.DataFrame:
        """
        Calculate seasonal averages for energy metrics.
        
        Returns:
            DataFrame with seasonal averages (Spring, Summer, Fall, Winter)
        """
        if self.data is None:
            return pd.DataFrame()
        
        # Define seasons
        def get_season(month):
            if month in [3, 4, 5]:
                return 'Spring'
            elif month in [6, 7, 8]:
                return 'Summer'
            elif month in [9, 10, 11]:
                return 'Fall'
            else:  # [12, 1, 2]
                return 'Winter'
        
        # Extract month and determine season
        df = self.data.copy()
        df['month'] = df['Date/Time'].dt.month
        df['season'] = df['month'].apply(get_season)
        
        # Group by season and calculate averages per day
        # First group by date to get daily totals
        df['date'] = df['Date/Time'].dt.date
        energy_cols = [col for col in df.columns if any(term in col for term in 
                      ['Energy', 'Exported', 'Imported', 'surplus_energy'])]
        
        daily = df.groupby(['date', 'season'])[energy_cols].sum().reset_index()
        
        # Then group by season to get seasonal averages
        seasonal_avg = daily.groupby('season')[energy_cols].mean().reset_index()
        
        # Add order column for correct plotting
        season_order = {'Winter': 0, 'Spring': 1, 'Summer': 2, 'Fall': 3}
        seasonal_avg['order'] = seasonal_avg['season'].map(season_order)
        seasonal_avg.sort_values('order', inplace=True)
        seasonal_avg.drop('order', axis=1, inplace=True)
        
        # Convert to kWh
        for col in energy_cols:
            if 'Wh' in col:
                seasonal_avg[col.replace('(Wh)', '(kWh)')] = utils.convert_wh_to_kwh(seasonal_avg[col])
        
        # Also convert surplus_energy if it exists
        if 'surplus_energy' in energy_cols:
            seasonal_avg['surplus_energy_kwh'] = utils.convert_wh_to_kwh(seasonal_avg['surplus_energy'])
        
        return seasonal_avg
    
    def detect_anomalies(self, std_dev_threshold: float = 3.0) -> Dict[str, pd.DataFrame]:
        """
        Detect anomalies in the energy data based on standard deviation.
        
        Args:
            std_dev_threshold: Number of standard deviations from mean to consider anomalous
            
        Returns:
            Dictionary with dataframes of anomalies for each energy metric
        """
        if self.data is None:
            return {}
        
        anomalies = {}
        
        # Check energy columns for anomalies
        energy_cols = [
            'Energy Produced (Wh)', 
            'Energy Consumed (Wh)', 
            'Exported to Grid (Wh)', 
            'Imported from Grid (Wh)'
        ]
        
        # Only check columns that exist in the data
        energy_cols = [col for col in energy_cols if col in self.data.columns]
        
        for col in energy_cols:
            # Calculate mean and standard deviation
            mean = self.data[col].mean()
            std = self.data[col].std()
            
            # Identify anomalies
            anomaly_high = self.data[self.data[col] > mean + std_dev_threshold * std].copy()
            anomaly_low = self.data[self.data[col] < mean - std_dev_threshold * std].copy()
            
            # Combine anomalies
            combined = pd.concat([anomaly_high, anomaly_low]).sort_values('Date/Time')
            
            if len(combined) > 0:
                anomalies[col] = combined
        
        return anomalies
