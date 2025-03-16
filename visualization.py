"""
Visualization module for the Zonnepanelen_check application.

This module provides functions and classes for visualizing energy data,
storage calculations, and financial results using various plotting libraries.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Tuple, Union, Optional, Any
import io
import base64


def plot_energy_production_consumption(data: pd.DataFrame, period: str = 'daily') -> go.Figure:
    """
    Create a plot of energy production and consumption.
    
    Args:
        data: DataFrame containing energy data
        period: Time period for aggregation ('daily', 'weekly', 'monthly')
        
    Returns:
        Plotly figure object
    """
    if data is None or len(data) == 0:
        return go.Figure()
    
    # Ensure we have DateTime column
    if 'Date/Time' not in data.columns:
        return go.Figure()
    
    # Make a copy and convert to datetime
    df = data.copy()
    df['Date/Time'] = pd.to_datetime(df['Date/Time'])
    
    # Determine aggregation period
    if period == 'weekly':
        df['period'] = df['Date/Time'].dt.isocalendar().week
        period_name = 'Week'
    elif period == 'monthly':
        df['period'] = df['Date/Time'].dt.strftime('%Y-%m')
        period_name = 'Month'
    else:  # daily
        df['period'] = df['Date/Time'].dt.date
        period_name = 'Day'
        
    # Aggregate data
    agg_data = df.groupby('period').agg({
        'Energy Produced (Wh)': 'sum',
        'Energy Consumed (Wh)': 'sum'
    }).reset_index()
    
    # Convert to kWh
    agg_data['Energy Produced (kWh)'] = agg_data['Energy Produced (Wh)'] / 1000
    agg_data['Energy Consumed (kWh)'] = agg_data['Energy Consumed (Wh)'] / 1000
    
    # Create figure
    fig = go.Figure()
    
    # Add traces
    fig.add_trace(go.Bar(
        x=agg_data['period'],
        y=agg_data['Energy Produced (kWh)'],
        name='Production',
        marker_color='rgba(50, 171, 96, 0.7)'
    ))
    
    fig.add_trace(go.Bar(
        x=agg_data['period'],
        y=agg_data['Energy Consumed (kWh)'],
        name='Consumption',
        marker_color='rgba(219, 64, 82, 0.7)'
    ))
    
    # Customize layout
    fig.update_layout(
        title=f'Energy Production and Consumption by {period_name}',
        xaxis_title=period_name,
        yaxis_title='Energy (kWh)',
        barmode='group',
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def plot_surplus_energy(data: pd.DataFrame, period: str = 'daily') -> go.Figure:
    """
    Create a plot of surplus energy (production - consumption).
    
    Args:
        data: DataFrame containing energy data
        period: Time period for aggregation ('daily', 'weekly', 'monthly')
        
    Returns:
        Plotly figure object
    """
    if data is None or len(data) == 0:
        return go.Figure()
    
    # Ensure we have DateTime column
    if 'Date/Time' not in data.columns:
        return go.Figure()
    
    # Make a copy and convert to datetime
    df = data.copy()
    df['Date/Time'] = pd.to_datetime(df['Date/Time'])
    
    # Calculate surplus if not present
    if 'surplus_energy' not in df.columns:
        if 'Energy Produced (Wh)' in df.columns and 'Energy Consumed (Wh)' in df.columns:
            df['surplus_energy'] = df['Energy Produced (Wh)'] - df['Energy Consumed (Wh)']
        else:
            return go.Figure()
    
    # Determine aggregation period
    if period == 'weekly':
        df['period'] = df['Date/Time'].dt.isocalendar().week
        period_name = 'Week'
    elif period == 'monthly':
        df['period'] = df['Date/Time'].dt.strftime('%Y-%m')
        period_name = 'Month'
    else:  # daily
        df['period'] = df['Date/Time'].dt.date
        period_name = 'Day'
        
    # Aggregate data
    agg_data = df.groupby('period').agg({
        'surplus_energy': 'sum'
    }).reset_index()
    
    # Convert to kWh
    agg_data['surplus_energy_kwh'] = agg_data['surplus_energy'] / 1000
    
    # Create figure
    fig = go.Figure()
    
    # Add trace with positive and negative values in different colors
    fig.add_trace(go.Bar(
        x=agg_data['period'],
        y=agg_data['surplus_energy_kwh'],
        name='Surplus Energy',
        marker=dict(
            color=agg_data['surplus_energy_kwh'].apply(
                lambda x: 'rgba(50, 171, 96, 0.7)' if x >= 0 else 'rgba(219, 64, 82, 0.7)'
            )
        )
    ))
    
    # Customize layout
    fig.update_layout(
        title=f'Surplus Energy by {period_name}',
        xaxis_title=period_name,
        yaxis_title='Energy (kWh)',
        template='plotly_white'
    )
    
    return fig


def plot_battery_state(battery_results: Dict[str, Any]) -> go.Figure:
    """
    Plot battery state of charge and energy flows.
    
    Args:
        battery_results: Dictionary with battery calculation results
        
    Returns:
        Plotly figure object
    """
    if not battery_results or 'result_df' not in battery_results:
        return go.Figure()
    
    # Get the result dataframe
    df = battery_results['result_df']
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Add battery state of charge
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['battery_state_kwh'],
        name='Batterij Laadtoestand (kWh)',
        line=dict(color='rgb(31, 119, 180)', width=2)
    ))
    
    # Add charging events
    mask_charge = df['charged_kwh'] > 0
    fig.add_trace(go.Bar(
        x=df.loc[mask_charge, 'timestamp'],
        y=df.loc[mask_charge, 'charged_kwh'],
        name='Opgeladen Energie (kWh)',
        marker_color='rgba(50, 171, 96, 0.7)'
    ))
    
    # Add discharging events
    mask_discharge = df['discharged_kwh'] > 0
    fig.add_trace(go.Bar(
        x=df.loc[mask_discharge, 'timestamp'],
        y=df.loc[mask_discharge, 'discharged_kwh'],
        name='Ontladen Energie (kWh)',
        marker_color='rgba(219, 64, 82, 0.7)'
    ))
    
    # Customize layout
    fig.update_layout(
        title='Accu Laadtoestand en Energiestromen',
        xaxis_title='Tijd',
        yaxis_title='Energie (kWh)',
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        barmode='group'
    )
    
    return fig


def plot_battery_daily_flows(battery_results: Dict[str, Any]) -> go.Figure:
    """
    Plot daily battery energy flows and savings.
    
    Args:
        battery_results: Dictionary with battery calculation results
        
    Returns:
        Plotly figure object
    """
    if not battery_results or 'daily_agg' not in battery_results:
        return go.Figure()
    
    # Get the daily aggregated data
    daily_df = battery_results['daily_agg']
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Add charged energy
    fig.add_trace(go.Bar(
        x=daily_df['period'],
        y=daily_df['charged_kwh'],
        name='Opgeladen Energie (kWh)',
        marker_color='rgba(50, 171, 96, 0.7)'
    ))
    
    # Add discharged energy
    fig.add_trace(go.Bar(
        x=daily_df['period'],
        y=daily_df['discharged_kwh'],
        name='Ontladen Energie (kWh)',
        marker_color='rgba(219, 64, 82, 0.7)'
    ))
    
    # Add financial savings line
    fig.add_trace(go.Scatter(
        x=daily_df['period'],
        y=daily_df['total_savings_eur'],
        name='Financiële Besparing (€)',
        line=dict(color='rgba(255, 127, 14, 1)', width=2),
        yaxis="y2"
    ))
    
    # Customize layout
    fig.update_layout(
        title='Dagelijkse Batterij Energiestromen en Besparingen',
        xaxis_title='Datum',
        yaxis_title='Energie (kWh)',
        yaxis2=dict(
            title='Besparing (€)',
            titlefont=dict(color='rgba(255, 127, 14, 1)'),
            tickfont=dict(color='rgba(255, 127, 14, 1)'),
            overlaying='y',
            side='right'
        ),
        template='plotly_white',
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def plot_battery_monthly_performance(battery_results: Dict[str, Any]) -> go.Figure:
    """
    Plot monthly battery performance and savings.
    
    Args:
        battery_results: Dictionary with battery calculation results
        
    Returns:
        Plotly figure object
    """
    if not battery_results or 'monthly_agg' not in battery_results:
        return go.Figure()
    
    # Get the monthly aggregated data
    monthly_df = battery_results['monthly_agg']
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Add financial savings trace
    fig.add_trace(go.Bar(
        x=monthly_df['period'],
        y=monthly_df['total_savings_eur'],
        name='Financiële Besparing (€)',
        marker_color='rgba(255, 127, 14, 0.7)'
    ))
    
    # Add storage utilization trace
    fig.add_trace(go.Scatter(
        x=monthly_df['period'],
        y=monthly_df['storage_utilization'],
        name='Opslagbenutting (%)',
        line=dict(color='rgba(31, 119, 180, 1)', width=2),
        yaxis="y2"
    ))
    
    # Add round-trip efficiency trace
    fig.add_trace(go.Scatter(
        x=monthly_df['period'],
        y=monthly_df['round_trip_efficiency'],
        name='Laad/ontlaad Efficiëntie (%)',
        line=dict(color='rgba(50, 171, 96, 1)', width=2, dash='dot'),
        yaxis="y2"
    ))
    
    # Customize layout
    fig.update_layout(
        title='Maandelijkse Besparingen en Batterij Efficiëntie',
        xaxis_title='Maand',
        yaxis_title='Besparing (€)',
        yaxis2=dict(
            title='Percentage (%)',
            titlefont=dict(color='rgba(31, 119, 180, 1)'),
            tickfont=dict(color='rgba(31, 119, 180, 1)'),
            overlaying='y',
            side='right',
            range=[0, 100]
        ),
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def plot_battery_grid_impact(battery_results: Dict[str, Any]) -> go.Figure:
    """
    Plot the impact of battery storage on grid imports and exports.
    
    Args:
        battery_results: Dictionary with battery calculation results
        
    Returns:
        Plotly figure object
    """
    if not battery_results or 'daily_agg' not in battery_results:
        return go.Figure()
    
    # Get the daily aggregated data
    daily_df = battery_results['daily_agg']
    
    # Create figure
    fig = go.Figure()
    
    # Add grid import
    fig.add_trace(go.Bar(
        x=daily_df['period'],
        y=daily_df['grid_import_kwh'],
        name='Import van Net (kWh)',
        marker_color='rgba(219, 64, 82, 0.7)'
    ))
    
    # Add grid export
    fig.add_trace(go.Bar(
        x=daily_df['period'],
        y=daily_df['grid_export_kwh'],
        name='Export naar Net (kWh)',
        marker_color='rgba(50, 171, 96, 0.7)'
    ))
    
    # Customize layout
    fig.update_layout(
        title='Dagelijkse Netinteractie met Batterij',
        xaxis_title='Datum',
        yaxis_title='Energie (kWh)',
        template='plotly_white',
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def plot_battery_simulation_detail(battery_results: Dict[str, Any], sample_date=None) -> go.Figure:
    """
    Create a detailed plot of the battery simulation for a specific day.
    
    Args:
        battery_results: Dictionary with battery calculation results
        sample_date: Optional date to plot. If None, a representative date will be chosen.
        
    Returns:
        Plotly figure object
    """
    if not battery_results or 'result_df' not in battery_results:
        return go.Figure()
    
    # Get the result dataframe
    all_df = battery_results['result_df']
    
    # Convert to datetime if not already
    if not pd.api.types.is_datetime64_dtype(all_df['timestamp']):
        all_df['timestamp'] = pd.to_datetime(all_df['timestamp'])
    
    # If sample_date is not provided, find a representative date
    if sample_date is None:
        # Find a day with significant battery activity
        daily_discharged = all_df.groupby(all_df['timestamp'].dt.date)['discharged_kwh'].sum()
        if len(daily_discharged) > 0:
            # Get a day with high discharge (in top 25%)
            top_days = daily_discharged.sort_values(ascending=False).head(max(1, len(daily_discharged) // 4))
            sample_date = top_days.index[min(3, len(top_days) - 1)]
    
    # Filter for the sample date
    sample_df = all_df[all_df['timestamp'].dt.date == sample_date].copy() if sample_date else all_df.copy()
    
    if len(sample_df) == 0:
        return go.Figure()
    
    # Create figure with multiple y-axes
    fig = go.Figure()
    
    # Add battery state of charge
    fig.add_trace(go.Scatter(
        x=sample_df['timestamp'],
        y=sample_df['battery_state_kwh'],
        name='Batterij Laadtoestand (kWh)',
        line=dict(color='rgba(31, 119, 180, 1)', width=2)
    ))
    
    # Add surplus energy
    fig.add_trace(go.Bar(
        x=sample_df['timestamp'],
        y=sample_df['surplus_energy_kwh'],
        name='Surplus Energie (kWh)',
        marker_color='rgba(50, 171, 96, 0.4)',
        yaxis="y2"
    ))
    
    # Add charged energy
    fig.add_trace(go.Bar(
        x=sample_df['timestamp'],
        y=sample_df['charged_kwh'],
        name='Opgeladen Energie (kWh)',
        marker_color='rgba(50, 171, 96, 0.9)',
        yaxis="y2"
    ))
    
    # Add discharged energy
    fig.add_trace(go.Bar(
        x=sample_df['timestamp'],
        y=sample_df['discharged_kwh'],
        name='Ontladen Energie (kWh)',
        marker_color='rgba(219, 64, 82, 0.7)',
        yaxis="y2"
    ))
    
    # Format the date for the title
    date_str = sample_date.strftime('%d-%m-%Y') if hasattr(sample_date, 'strftime') else "sample period"
    
    # Customize layout
    fig.update_layout(
        title=f'Gedetailleerde Batterij Simulatie voor {date_str}',
        xaxis_title='Tijd',
        yaxis=dict(
            title='Batterij Laadtoestand (kWh)',
            titlefont=dict(color='rgba(31, 119, 180, 1)'),
            tickfont=dict(color='rgba(31, 119, 180, 1)')
        ),
        yaxis2=dict(
            title='Energie (kWh)',
            titlefont=dict(color='rgba(50, 171, 96, 1)'),
            tickfont=dict(color='rgba(50, 171, 96, 1)'),
            overlaying='y',
            side='right'
        ),
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        barmode='group'
    )
    
    return fig


def plot_boiler_energy_usage(boiler_results: Dict[str, Any]) -> go.Figure:
    """
    Plot boiler energy usage and gas savings.
    
    Args:
        boiler_results: Dictionary with boiler calculation results
        
    Returns:
        Plotly figure object
    """
    if not boiler_results or 'result_df' not in boiler_results:
        return go.Figure()
    
    # Get the result dataframe
    df = boiler_results['result_df']
    
    # If timestamps are too granular, aggregate by day
    if len(df) > 100:
        # Ensure timestamp is datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        # Aggregate by day
        daily_df = df.groupby('date').agg({
            'energy_needed_kwh': 'sum',
            'energy_used_kwh': 'sum',
            'gas_saved_m3': 'sum'
        }).reset_index()
        
        plot_df = daily_df
        x_col = 'date'
    else:
        plot_df = df
        x_col = 'timestamp'
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Add energy needed
    fig.add_trace(go.Scatter(
        x=plot_df[x_col],
        y=plot_df['energy_needed_kwh'],
        name='Energy Needed',
        line=dict(color='rgb(31, 119, 180)', width=2, dash='dash')
    ))
    
    # Add energy used from solar
    fig.add_trace(go.Bar(
        x=plot_df[x_col],
        y=plot_df['energy_used_kwh'],
        name='Solar Energy Used',
        marker_color='rgba(50, 171, 96, 0.7)'
    ))
    
    # Create a secondary axis for gas saved
    fig.add_trace(go.Scatter(
        x=plot_df[x_col],
        y=plot_df['gas_saved_m3'],
        name='Gas Saved',
        line=dict(color='rgba(219, 64, 82, 1)', width=2),
        yaxis="y2"
    ))
    
    # Customize layout
    fig.update_layout(
        title='Boiler Energy Usage and Gas Savings',
        xaxis_title='Time',
        yaxis_title='Energy (kWh)',
        yaxis2=dict(
            title='Gas Saved (m³)',
            titlefont=dict(color='rgba(219, 64, 82, 1)'),
            tickfont=dict(color='rgba(219, 64, 82, 1)'),
            overlaying='y',
            side='right'
        ),
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def plot_boiler_daily_performance(boiler_results: Dict[str, Any]) -> go.Figure:
    """
    Create a comprehensive daily performance plot for the boiler.
    
    Args:
        boiler_results: Dictionary with boiler calculation results
        
    Returns:
        Plotly figure object
    """
    if not boiler_results or 'daily_agg' not in boiler_results:
        return go.Figure()
    
    # Get the daily aggregated data
    daily_df = boiler_results['daily_agg']
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Add gas needed trace
    fig.add_trace(go.Bar(
        x=daily_df['period'],
        y=daily_df['gas_needed_m3'],
        name='Gas Nodig (zonder zonne-energie)',
        marker_color='rgba(220, 220, 220, 0.7)'
    ))
    
    # Add gas saved trace
    fig.add_trace(go.Bar(
        x=daily_df['period'],
        y=daily_df['gas_saved_m3'],
        name='Gas Bespaard (met zonne-energie)',
        marker_color='rgba(50, 171, 96, 0.7)'
    ))
    
    # Add coverage percentage line
    fig.add_trace(go.Scatter(
        x=daily_df['period'],
        y=daily_df['heating_coverage'],
        name='Dekkingspercentage',
        line=dict(color='rgba(219, 64, 82, 1)', width=2),
        yaxis="y2"
    ))
    
    # Customize layout
    fig.update_layout(
        title='Dagelijkse Gasbesparing en Verwarmingsdekking',
        xaxis_title='Datum',
        yaxis_title='Gas (m³)',
        yaxis2=dict(
            title='Dekking (%)',
            titlefont=dict(color='rgba(219, 64, 82, 1)'),
            tickfont=dict(color='rgba(219, 64, 82, 1)'),
            overlaying='y',
            side='right',
            range=[0, 100]
        ),
        template='plotly_white',
        barmode='overlay',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def plot_boiler_monthly_performance(boiler_results: Dict[str, Any]) -> go.Figure:
    """
    Create a comprehensive monthly performance plot for the boiler.
    
    Args:
        boiler_results: Dictionary with boiler calculation results
        
    Returns:
        Plotly figure object
    """
    if not boiler_results or 'monthly_agg' not in boiler_results:
        return go.Figure()
    
    # Get the monthly aggregated data
    monthly_df = boiler_results['monthly_agg']
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Add financial savings trace
    fig.add_trace(go.Bar(
        x=monthly_df['period'],
        y=monthly_df['financial_savings'],
        name='Financiële Besparing (€)',
        marker_color='rgba(50, 171, 96, 0.7)'
    ))
    
    # Add surplus utilization trace
    fig.add_trace(go.Scatter(
        x=monthly_df['period'],
        y=monthly_df['surplus_utilization'],
        name='Benuttingspercentage',
        line=dict(color='rgba(31, 119, 180, 1)', width=2),
        yaxis="y2"
    ))
    
    # Add heating coverage trace
    fig.add_trace(go.Scatter(
        x=monthly_df['period'],
        y=monthly_df['heating_coverage'],
        name='Verwarmingsdekking',
        line=dict(color='rgba(219, 64, 82, 1)', width=2, dash='dot'),
        yaxis="y2"
    ))
    
    # Customize layout
    fig.update_layout(
        title='Maandelijkse Financiële Besparing en Efficiëntie',
        xaxis_title='Maand',
        yaxis_title='Besparing (€)',
        yaxis2=dict(
            title='Percentage (%)',
            titlefont=dict(color='rgba(31, 119, 180, 1)'),
            tickfont=dict(color='rgba(31, 119, 180, 1)'),
            overlaying='y',
            side='right',
            range=[0, 100]
        ),
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def plot_boiler_simulation_detail(boiler_results: Dict[str, Any], sample_date=None) -> go.Figure:
    """
    Create a detailed plot of the boiler simulation for a specific day.
    
    Args:
        boiler_results: Dictionary with boiler calculation results
        sample_date: Optional date to plot. If None, a representative date will be chosen.
        
    Returns:
        Plotly figure object
    """
    if not boiler_results or 'result_df' not in boiler_results:
        return go.Figure()
    
    # Get the result dataframe
    all_df = boiler_results['result_df']
    
    # Convert to datetime if not already
    if not pd.api.types.is_datetime64_dtype(all_df['timestamp']):
        all_df['timestamp'] = pd.to_datetime(all_df['timestamp'])
    
    # If sample_date is not provided, find a representative date
    if sample_date is None:
        # Find a day with significant solar surplus
        daily_surplus = all_df.groupby(all_df['timestamp'].dt.date)['surplus_energy_kwh'].sum()
        if len(daily_surplus) > 0:
            # Get a day with high surplus (in top 25%)
            top_days = daily_surplus.sort_values(ascending=False).head(max(1, len(daily_surplus) // 4))
            sample_date = top_days.index[min(3, len(top_days) - 1)]
    
    # Filter for the sample date
    sample_df = all_df[all_df['timestamp'].dt.date == sample_date].copy() if sample_date else all_df.copy()
    
    if len(sample_df) == 0:
        return go.Figure()
    
    # Create figure with multiple y-axes
    fig = go.Figure()
    
    # Add water temperature
    fig.add_trace(go.Scatter(
        x=sample_df['timestamp'],
        y=sample_df['water_temp'],
        name='Watertemperatuur (°C)',
        line=dict(color='rgba(31, 119, 180, 1)', width=2)
    ))
    
    # Add heat energy in boiler
    fig.add_trace(go.Scatter(
        x=sample_df['timestamp'],
        y=sample_df['heat_energy_kwh'],
        name='Opgeslagen Warmte (kWh)',
        line=dict(color='rgba(255, 127, 14, 1)', width=2, dash='dot'),
        yaxis="y3"
    ))
    
    # Add surplus energy
    fig.add_trace(go.Bar(
        x=sample_df['timestamp'],
        y=sample_df['surplus_energy_kwh'],
        name='Surplus Energie (kWh)',
        marker_color='rgba(50, 171, 96, 0.4)',
        yaxis="y3"
    ))
    
    # Add used energy
    fig.add_trace(go.Bar(
        x=sample_df['timestamp'],
        y=sample_df['energy_used_kwh'],
        name='Gebruikte Energie (kWh)',
        marker_color='rgba(50, 171, 96, 0.9)',
        yaxis="y3"
    ))
    
    # Add hot water demand
    fig.add_trace(go.Scatter(
        x=sample_df['timestamp'],
        y=sample_df['hot_water_demand_l'],
        name='Warmwaterverbruik (L)',
        line=dict(color='rgba(148, 103, 189, 1)', width=2),
        yaxis="y2"
    ))
    
    # Add heat loss
    fig.add_trace(go.Scatter(
        x=sample_df['timestamp'],
        y=sample_df['heat_loss_kwh'],
        name='Warmteverlies (kWh)',
        line=dict(color='rgba(214, 39, 40, 1)', width=2, dash='dot'),
        yaxis="y3"
    ))
    
    # Format the date for the title
    date_str = sample_date.strftime('%d-%m-%Y') if hasattr(sample_date, 'strftime') else "sample period"
    
    # Customize layout
    fig.update_layout(
        title=f'Gedetailleerde Boiler Simulatie voor {date_str}',
        xaxis_title='Tijd',
        yaxis=dict(
            title='Temperatuur (°C)',
            titlefont=dict(color='rgba(31, 119, 180, 1)'),
            tickfont=dict(color='rgba(31, 119, 180, 1)'),
            domain=[0, 0.85]
        ),
        yaxis2=dict(
            title='Water (L)',
            titlefont=dict(color='rgba(148, 103, 189, 1)'),
            tickfont=dict(color='rgba(148, 103, 189, 1)'),
            overlaying='y',
            side='right',
            position=0.86
        ),
        yaxis3=dict(
            title='Energie (kWh)',
            titlefont=dict(color='rgba(50, 171, 96, 1)'),
            tickfont=dict(color='rgba(50, 171, 96, 1)'),
            anchor='free',
            overlaying='y',
            side='right',
            position=0.93
        ),
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def plot_boiler_usage_profile(hourly_profile: Dict[int, float]) -> go.Figure:
    """
    Create a bar chart of the hourly hot water usage profile.
    
    Args:
        hourly_profile: Dictionary mapping hour of day (0-23) to usage fraction
        
    Returns:
        Plotly figure object
    """
    # Convert profile to sorted list of tuples
    profile_items = sorted(hourly_profile.items())
    
    # Extract hours and percentages
    hours = [h for h, _ in profile_items]
    percentages = [p * 100 for _, p in profile_items]
    
    # Create figure
    fig = go.Figure()
    
    # Add bar chart
    fig.add_trace(go.Bar(
        x=[f"{h}:00" for h in hours],
        y=percentages,
        marker_color='rgba(50, 171, 96, 0.7)'
    ))
    
    # Customize layout
    fig.update_layout(
        title='Warmwaterverbruik Profiel',
        xaxis_title='Uur van de dag',
        yaxis_title='Percentage (%)',
        template='plotly_white'
    )
    
    return fig


def plot_comparison_chart(data: Dict[str, float], title: str) -> go.Figure:
    """
    Create a comparison bar chart for different scenarios.
    
    Args:
        data: Dictionary with labels as keys and values to plot
        title: Chart title
        
    Returns:
        Plotly figure object
    """
    # Convert dictionary to lists
    labels = list(data.keys())
    values = list(data.values())
    
    # Create figure
    fig = go.Figure(data=[
        go.Bar(
            x=labels,
            y=values,
            text=values,
            textposition='auto',
            marker_color=['rgba(50, 171, 96, 0.7)'] * len(values)
        )
    ])
    
    # Customize layout
    fig.update_layout(
        title=title,
        template='plotly_white'
    )
    
    return fig


def fig_to_base64(fig: go.Figure) -> str:
    """
    Convert a plotly figure to a base64 encoded string for embedding.
    
    Args:
        fig: Plotly figure object
        
    Returns:
        Base64 encoded string
    """
    img_bytes = fig.to_image(format="png")
    base64_str = base64.b64encode(img_bytes).decode('utf-8')
    return f"data:image/png;base64,{base64_str}"
