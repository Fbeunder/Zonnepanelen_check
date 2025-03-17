"""
Boiler plots module for the Zonnepanelen_check application.

This module contains visualization functions for boiler simulation and analysis.
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from typing import Dict, Any, Optional


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
    
    # Customize layout with simplified configuration
    layout_config = {
        'title': 'Boiler Energy Usage and Gas Savings',
        'xaxis_title': 'Time',
        'yaxis_title': 'Energy (kWh)',
        'yaxis2': {
            'title': 'Gas Saved (m³)',
            'overlaying': 'y',
            'side': 'right'
        },
        'template': 'plotly_white',
        'legend': {
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'right',
            'x': 1
        }
    }
    
    # Update layout with a try-except to handle potential configuration errors
    try:
        fig.update_layout(**layout_config)
    except Exception as e:
        print(f"Error updating layout: {e}")
        # Fallback to minimal configuration if detailed config fails
        fig.update_layout(title='Boiler Energy Usage and Gas Savings')
    
    return fig


def plot_boiler_daily_performance(boiler_results: Dict[str, Any]) -> go.Figure:
    """
    Plot daily boiler performance metrics.
    
    Args:
        boiler_results: Dictionary with boiler calculation results
        
    Returns:
        Plotly figure object
    """
    if not boiler_results or 'daily_agg' not in boiler_results:
        return go.Figure()
    
    # Get daily aggregated data
    df = boiler_results['daily_agg']
    
    # Ensure period is properly formatted
    if not pd.api.types.is_datetime64_dtype(df['period']):
        df['period'] = pd.to_datetime(df['period'])
    
    # Create figure
    fig = go.Figure()
    
    # Add gas needed trace
    fig.add_trace(go.Bar(
        x=df['period'],
        y=df['gas_needed_m3'],
        name='Gas Needed (without solar)',
        marker_color='rgba(220, 220, 220, 0.7)'
    ))
    
    # Add gas saved trace
    fig.add_trace(go.Bar(
        x=df['period'],
        y=df['gas_saved_m3'],
        name='Gas Saved (with solar)',
        marker_color='rgba(50, 171, 96, 0.7)'
    ))
    
    # Add heating coverage line on secondary y-axis
    if 'heating_coverage' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['period'],
            y=df['heating_coverage'],
            name='Heating Coverage (%)',
            line=dict(color='rgba(219, 64, 82, 1)', width=2),
            yaxis="y2"
        ))
    
    # Customize layout
    fig.update_layout(
        title='Daily Boiler Performance',
        xaxis_title='Date',
        yaxis_title='Gas (m³)',
        yaxis2=dict(
            title='Coverage (%)',
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
    Plot monthly boiler performance metrics.
    
    Args:
        boiler_results: Dictionary with boiler calculation results
        
    Returns:
        Plotly figure object
    """
    if not boiler_results or 'monthly_agg' not in boiler_results:
        return go.Figure()
    
    # Get monthly aggregated data
    df = boiler_results['monthly_agg']
    
    # Ensure period is properly formatted
    if not pd.api.types.is_datetime64_dtype(df['period']):
        df['period'] = pd.to_datetime(df['period'])
    
    # Format month labels
    month_labels = df['period'].dt.strftime('%Y-%m')
    
    # Create figure
    fig = go.Figure()
    
    # Add financial savings
    fig.add_trace(go.Bar(
        x=month_labels,
        y=df['financial_savings'],
        name='Financial Savings (€)',
        marker_color='rgba(50, 171, 96, 0.7)'
    ))
    
    # Add utilization percentage line on secondary y-axis
    if 'surplus_utilization' in df.columns:
        fig.add_trace(go.Scatter(
            x=month_labels,
            y=df['surplus_utilization'],
            name='Utilization (%)',
            line=dict(color='rgba(219, 64, 82, 1)', width=2),
            yaxis="y2"
        ))
    
    # Customize layout
    fig.update_layout(
        title='Monthly Financial Savings and Utilization',
        xaxis_title='Month',
        yaxis_title='Savings (€)',
        yaxis2=dict(
            title='Utilization (%)',
            titlefont=dict(color='rgba(219, 64, 82, 1)'),
            tickfont=dict(color='rgba(219, 64, 82, 1)'),
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


def plot_boiler_simulation_detail(boiler_results: Dict[str, Any]) -> go.Figure:
    """
    Plot detailed boiler simulation for a sample day.
    
    Args:
        boiler_results: Dictionary with boiler calculation results
        
    Returns:
        Plotly figure object
    """
    if not boiler_results or 'result_df' not in boiler_results:
        return go.Figure()
    
    # Get a sample day from the data
    all_df = boiler_results['result_df'].copy()
    
    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_dtype(all_df['timestamp']):
        all_df['timestamp'] = pd.to_datetime(all_df['timestamp'])
    
    # Find a day with significant solar surplus
    all_df['date'] = all_df['timestamp'].dt.date
    daily_usage = all_df.groupby('date')['energy_used_kwh'].sum()
    
    if len(daily_usage) > 0:
        # Get a day with high energy usage (in top 25%)
        top_days = daily_usage.sort_values(ascending=False).head(max(1, len(daily_usage) // 4))
        sample_date = top_days.index[min(1, len(top_days) - 1)]
        
        # Filter for the sample date
        sample_df = all_df[all_df['date'] == sample_date].copy()
        
        # Create figure with multiple y-axes
        fig = go.Figure()
        
        # Add water temperature
        if 'water_temp' in sample_df.columns:
            fig.add_trace(go.Scatter(
                x=sample_df['timestamp'],
                y=sample_df['water_temp'],
                name='Water Temperature (°C)',
                line=dict(color='rgba(31, 119, 180, 1)', width=2)
            ))
        
        # Add surplus energy
        if 'surplus_energy_kwh' in sample_df.columns:
            fig.add_trace(go.Bar(
                x=sample_df['timestamp'],
                y=sample_df['surplus_energy_kwh'],
                name='Surplus Energy (kWh)',
                marker_color='rgba(50, 171, 96, 0.7)',
                yaxis="y2"
            ))
        
        # Add used energy
        if 'energy_used_kwh' in sample_df.columns:
            fig.add_trace(go.Bar(
                x=sample_df['timestamp'],
                y=sample_df['energy_used_kwh'],
                name='Energy Used (kWh)',
                marker_color='rgba(219, 64, 82, 0.7)',
                yaxis="y2"
            ))
        
        # Add hot water demand
        if 'hot_water_demand_l' in sample_df.columns:
            fig.add_trace(go.Scatter(
                x=sample_df['timestamp'],
                y=sample_df['hot_water_demand_l'],
                name='Hot Water Demand (L)',
                line=dict(color='rgba(148, 103, 189, 1)', width=2, dash='dot'),
                yaxis="y3"
            ))
        
        # Customize layout
        fig.update_layout(
            title=f'Boiler Simulation Detail for {sample_date}',
            xaxis_title='Time',
            yaxis=dict(
                title='Temperature (°C)',
                titlefont=dict(color='rgba(31, 119, 180, 1)'),
                tickfont=dict(color='rgba(31, 119, 180, 1)')
            ),
            yaxis2=dict(
                title='Energy (kWh)',
                titlefont=dict(color='rgba(50, 171, 96, 1)'),
                tickfont=dict(color='rgba(50, 171, 96, 1)'),
                overlaying='y',
                side='right'
            ),
            yaxis3=dict(
                title='Water (L)',
                titlefont=dict(color='rgba(148, 103, 189, 1)'),
                tickfont=dict(color='rgba(148, 103, 189, 1)'),
                overlaying='y',
                anchor='free',
                side='right',
                position=0.95
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
    
    # Return empty figure if no suitable data is found
    return go.Figure()


def plot_boiler_usage_profile(hourly_profile: Dict[int, float]) -> go.Figure:
    """
    Plot boiler hot water usage profile.
    
    Args:
        hourly_profile: Dictionary with hour (0-23) as key and usage percentage as value
        
    Returns:
        Plotly figure object
    """
    if not hourly_profile:
        return go.Figure()
    
    # Convert profile to dataframe
    hours = sorted(hourly_profile.keys())
    percentages = [hourly_profile[hour] * 100 for hour in hours]
    
    # Create dataframe
    df = pd.DataFrame({
        'Hour': [f"{h}:00" for h in hours],
        'Percentage': percentages
    })
    
    # Create bar chart
    fig = px.bar(
        df,
        x='Hour',
        y='Percentage',
        labels={'Hour': 'Hour of Day', 'Percentage': 'Usage (%)'},
        title='Hot Water Usage Profile'
    )
    
    # Customize layout
    fig.update_layout(
        xaxis_title='Hour of Day',
        yaxis_title='Usage (%)',
        template='plotly_white',
        yaxis=dict(range=[0, max(percentages) * 1.1])  # Add 10% headroom
    )
    
    return fig
