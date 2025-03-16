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
        name='Battery State of Charge',
        line=dict(color='rgb(31, 119, 180)', width=2)
    ))
    
    # Add charging events
    mask_charge = df['charged_kwh'] > 0
    fig.add_trace(go.Bar(
        x=df.loc[mask_charge, 'timestamp'],
        y=df.loc[mask_charge, 'charged_kwh'],
        name='Charged Energy',
        marker_color='rgba(50, 171, 96, 0.7)'
    ))
    
    # Add discharging events
    mask_discharge = df['discharged_kwh'] > 0
    fig.add_trace(go.Bar(
        x=df.loc[mask_discharge, 'timestamp'],
        y=df.loc[mask_discharge, 'discharged_kwh'],
        name='Discharged Energy',
        marker_color='rgba(219, 64, 82, 0.7)'
    ))
    
    # Customize layout
    fig.update_layout(
        title='Battery State of Charge and Energy Flows',
        xaxis_title='Time',
        yaxis_title='Energy (kWh)',
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
            'boiler_energy_needed_kwh': 'sum',
            'boiler_energy_used_kwh': 'sum',
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
        y=plot_df['boiler_energy_needed_kwh'],
        name='Energy Needed',
        line=dict(color='rgb(31, 119, 180)', width=2, dash='dash')
    ))
    
    # Add energy used from solar
    fig.add_trace(go.Bar(
        x=plot_df[x_col],
        y=plot_df['boiler_energy_used_kwh'],
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
