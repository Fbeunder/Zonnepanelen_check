"""
Battery plots module for the Zonnepanelen_check application.

This module contains visualization functions for battery simulation and analysis.
"""
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from typing import Dict, Any, Optional


def plot_battery_state(battery_results: Dict[str, Any]) -> go.Figure:
    """
    Plot battery state of charge over time.
    
    Args:
        battery_results: Dictionary with battery calculation results
        
    Returns:
        Plotly figure object
    """
    if not battery_results or 'result_df' not in battery_results:
        return go.Figure()
    
    # Get the result dataframe
    df = battery_results['result_df']
    
    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Create figure
    fig = go.Figure()
    
    # Add battery state of charge
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['battery_kwh'],
        name='Battery Charge Level',
        line=dict(color='rgba(31, 119, 180, 1)', width=2),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.2)'
    ))
    
    # Customize layout
    fig.update_layout(
        title='Battery State of Charge',
        xaxis_title='Time',
        yaxis_title='Energy (kWh)',
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


def plot_battery_daily_flows(battery_results: Dict[str, Any]) -> go.Figure:
    """
    Plot daily energy flows for battery (charged, discharged).
    
    Args:
        battery_results: Dictionary with battery calculation results
        
    Returns:
        Plotly figure object
    """
    if not battery_results or 'daily_agg' not in battery_results:
        return go.Figure()
    
    # Get daily aggregated data
    df = battery_results['daily_agg']
    
    # Ensure period is datetime
    if not pd.api.types.is_datetime64_dtype(df['period']):
        df['period'] = pd.to_datetime(df['period'])
    
    # Create figure
    fig = go.Figure()
    
    # Add charged energy
    fig.add_trace(go.Bar(
        x=df['period'],
        y=df['charged_kwh'],
        name='Charged (kWh)',
        marker_color='rgba(50, 171, 96, 0.7)'
    ))
    
    # Add discharged energy
    fig.add_trace(go.Bar(
        x=df['period'],
        y=df['discharged_kwh'],
        name='Discharged (kWh)',
        marker_color='rgba(219, 64, 82, 0.7)'
    ))
    
    # Add financial savings line on secondary y-axis
    fig.add_trace(go.Scatter(
        x=df['period'],
        y=df['total_savings_eur'],
        name='Financial Savings (€)',
        line=dict(color='rgba(148, 103, 189, 1)', width=2),
        yaxis="y2"
    ))
    
    # Customize layout
    fig.update_layout(
        title='Daily Battery Energy Flows and Financial Savings',
        xaxis_title='Date',
        yaxis_title='Energy (kWh)',
        yaxis2=dict(
            title='Savings (€)',
            titlefont=dict(color='rgba(148, 103, 189, 1)'),
            tickfont=dict(color='rgba(148, 103, 189, 1)'),
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
    Plot monthly battery performance metrics.
    
    Args:
        battery_results: Dictionary with battery calculation results
        
    Returns:
        Plotly figure object
    """
    if not battery_results or 'monthly_agg' not in battery_results:
        return go.Figure()
    
    # Get monthly aggregated data
    df = battery_results['monthly_agg']
    
    # Ensure period is datetime
    if not pd.api.types.is_datetime64_dtype(df['period']):
        df['period'] = pd.to_datetime(df['period'])
    
    # Format month labels
    month_labels = df['period'].dt.strftime('%Y-%m')
    
    # Create figure
    fig = go.Figure()
    
    # Add charged energy
    fig.add_trace(go.Bar(
        x=month_labels,
        y=df['charged_kwh'],
        name='Charged (kWh)',
        marker_color='rgba(50, 171, 96, 0.7)'
    ))
    
    # Add discharged energy
    fig.add_trace(go.Bar(
        x=month_labels,
        y=df['discharged_kwh'],
        name='Discharged (kWh)',
        marker_color='rgba(219, 64, 82, 0.7)'
    ))
    
    # Add storage utilization line on secondary y-axis
    fig.add_trace(go.Scatter(
        x=month_labels,
        y=df['storage_utilization'],
        name='Storage Utilization (%)',
        line=dict(color='rgba(148, 103, 189, 1)', width=2),
        yaxis="y2"
    ))
    
    # Customize layout
    fig.update_layout(
        title='Monthly Battery Performance',
        xaxis_title='Month',
        yaxis_title='Energy (kWh)',
        yaxis2=dict(
            title='Utilization (%)',
            titlefont=dict(color='rgba(148, 103, 189, 1)'),
            tickfont=dict(color='rgba(148, 103, 189, 1)'),
            overlaying='y',
            side='right',
            range=[0, 100]
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


def plot_battery_grid_impact(battery_results: Dict[str, Any]) -> go.Figure:
    """
    Plot the impact of battery on grid interactions (import/export).
    
    Args:
        battery_results: Dictionary with battery calculation results
        
    Returns:
        Plotly figure object
    """
    if not battery_results or 'daily_agg' not in battery_results:
        return go.Figure()
    
    # Get daily aggregated data
    df = battery_results['daily_agg']
    
    # Ensure period is datetime
    if not pd.api.types.is_datetime64_dtype(df['period']):
        df['period'] = pd.to_datetime(df['period'])
    
    # Create figure
    fig = go.Figure()
    
    # Add import without battery
    if 'grid_import_without_battery_kwh' in df.columns:
        fig.add_trace(go.Bar(
            x=df['period'],
            y=df['grid_import_without_battery_kwh'],
            name='Grid Import Without Battery',
            marker_color='rgba(219, 64, 82, 0.4)'
        ))
    
    # Add import with battery
    if 'grid_import_with_battery_kwh' in df.columns:
        fig.add_trace(go.Bar(
            x=df['period'],
            y=df['grid_import_with_battery_kwh'],
            name='Grid Import With Battery',
            marker_color='rgba(219, 64, 82, 0.8)'
        ))
    
    # Add export without battery
    if 'grid_export_without_battery_kwh' in df.columns:
        fig.add_trace(go.Bar(
            x=df['period'],
            y=df['grid_export_without_battery_kwh'],
            name='Grid Export Without Battery',
            marker_color='rgba(50, 171, 96, 0.4)'
        ))
    
    # Add export with battery
    if 'grid_export_with_battery_kwh' in df.columns:
        fig.add_trace(go.Bar(
            x=df['period'],
            y=df['grid_export_with_battery_kwh'],
            name='Grid Export With Battery',
            marker_color='rgba(50, 171, 96, 0.8)'
        ))
    
    # Customize layout
    fig.update_layout(
        title='Daily Grid Interaction With and Without Battery',
        xaxis_title='Date',
        yaxis_title='Energy (kWh)',
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


def plot_battery_simulation_detail(battery_results: Dict[str, Any]) -> go.Figure:
    """
    Plot detailed battery simulation for a sample day.
    
    Args:
        battery_results: Dictionary with battery calculation results
        
    Returns:
        Plotly figure object
    """
    if not battery_results or 'result_df' not in battery_results:
        return go.Figure()
    
    # Get a sample day from the data
    all_df = battery_results['result_df'].copy()
    
    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_dtype(all_df['timestamp']):
        all_df['timestamp'] = pd.to_datetime(all_df['timestamp'])
    
    # Get a day with significant battery activity
    all_df['date'] = all_df['timestamp'].dt.date
    daily_activity = all_df.groupby('date')['charged_kwh'].sum()
    
    if len(daily_activity) > 0:
        # Get a day with high charging (in top 25%)
        top_days = daily_activity.sort_values(ascending=False).head(max(1, len(daily_activity) // 4))
        sample_date = top_days.index[min(1, len(top_days) - 1)]
        
        # Filter for the sample date
        sample_df = all_df[all_df['date'] == sample_date].copy()
        
        # Create figure with multiple y-axes
        fig = go.Figure()
        
        # Add battery state
        fig.add_trace(go.Scatter(
            x=sample_df['timestamp'],
            y=sample_df['battery_kwh'],
            name='Battery Charge (kWh)',
            line=dict(color='rgba(31, 119, 180, 1)', width=2),
            fill='tozeroy',
            fillcolor='rgba(31, 119, 180, 0.2)'
        ))
        
        # Add surplus energy
        fig.add_trace(go.Bar(
            x=sample_df['timestamp'],
            y=sample_df['surplus_energy_kwh'],
            name='Surplus Energy (kWh)',
            marker_color='rgba(50, 171, 96, 0.7)',
            yaxis="y2"
        ))
        
        # Add charged energy
        fig.add_trace(go.Bar(
            x=sample_df['timestamp'],
            y=sample_df['charged_kwh'],
            name='Charged Energy (kWh)',
            marker_color='rgba(44, 160, 44, 0.7)',
            yaxis="y2"
        ))
        
        # Add discharged energy
        fig.add_trace(go.Bar(
            x=sample_df['timestamp'],
            y=sample_df['discharged_kwh'],
            name='Discharged Energy (kWh)',
            marker_color='rgba(214, 39, 40, 0.7)',
            yaxis="y2"
        ))
        
        # Customize layout
        fig.update_layout(
            title=f'Battery Simulation Detail for {sample_date}',
            xaxis_title='Time',
            yaxis=dict(
                title='Battery Charge (kWh)',
                titlefont=dict(color='rgba(31, 119, 180, 1)'),
                tickfont=dict(color='rgba(31, 119, 180, 1)')
            ),
            yaxis2=dict(
                title='Energy Flow (kWh)',
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
            )
        )
        
        return fig
    
    # Return empty figure if no suitable data is found
    return go.Figure()
