"""
Energy plots module for the Zonnepanelen_check application.

This module contains visualization functions for energy production and consumption data.
"""
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any, Optional


def plot_energy_production_consumption(data: pd.DataFrame, period: str = 'daily') -> go.Figure:
    """
    Plot energy production and consumption over time.
    
    Args:
        data: DataFrame with energy data
        period: Aggregation period ('daily', 'weekly', or 'monthly')
        
    Returns:
        Plotly figure object
    """
    if data is None or data.empty:
        return go.Figure()
    
    # Make a copy to avoid modifying the original
    df = data.copy()
    
    # Ensure timestamp is datetime
    if 'timestamp' in df.columns and not pd.api.types.is_datetime64_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Determine time grouping
    if period == 'daily':
        df['period'] = df['timestamp'].dt.date
    elif period == 'weekly':
        df['period'] = df['timestamp'].dt.to_period('W').dt.start_time.dt.date
    elif period == 'monthly':
        df['period'] = df['timestamp'].dt.to_period('M').dt.start_time.dt.date
    else:
        df['period'] = df['timestamp'].dt.date  # Default to daily
    
    # Aggregate data
    agg_df = df.groupby('period').agg({
        'Energy Produced (Wh)': 'sum',
        'Energy Consumed (Wh)': 'sum'
    }).reset_index()
    
    # Convert Wh to kWh for better readability
    agg_df['Energy Produced (kWh)'] = agg_df['Energy Produced (Wh)'] / 1000
    agg_df['Energy Consumed (kWh)'] = agg_df['Energy Consumed (Wh)'] / 1000
    
    # Create figure
    fig = go.Figure()
    
    # Add production trace
    fig.add_trace(go.Bar(
        x=agg_df['period'],
        y=agg_df['Energy Produced (kWh)'],
        name='Productie',
        marker_color='rgba(50, 171, 96, 0.7)'
    ))
    
    # Add consumption trace
    fig.add_trace(go.Bar(
        x=agg_df['period'],
        y=agg_df['Energy Consumed (kWh)'],
        name='Verbruik',
        marker_color='rgba(219, 64, 82, 0.7)'
    ))
    
    # Period-specific title
    period_titles = {
        'daily': 'Dagelijkse',
        'weekly': 'Wekelijkse',
        'monthly': 'Maandelijkse'
    }
    title_prefix = period_titles.get(period, 'Dagelijkse')
    
    # Customize layout
    fig.update_layout(
        title=f'{title_prefix} Energieproductie en -verbruik',
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


def plot_surplus_energy(data: pd.DataFrame, period: str = 'daily') -> go.Figure:
    """
    Plot surplus energy (production minus consumption) over time.
    
    Args:
        data: DataFrame with energy data
        period: Aggregation period ('daily', 'weekly', or 'monthly')
        
    Returns:
        Plotly figure object
    """
    if data is None or data.empty:
        return go.Figure()
    
    # Make a copy to avoid modifying the original
    df = data.copy()
    
    # Ensure timestamp is datetime
    if 'timestamp' in df.columns and not pd.api.types.is_datetime64_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Calculate surplus energy if not already present
    if 'surplus_energy' not in df.columns:
        df['surplus_energy'] = df['Energy Produced (Wh)'] - df['Energy Consumed (Wh)']
    
    # Determine time grouping
    if period == 'daily':
        df['period'] = df['timestamp'].dt.date
    elif period == 'weekly':
        df['period'] = df['timestamp'].dt.to_period('W').dt.start_time.dt.date
    elif period == 'monthly':
        df['period'] = df['timestamp'].dt.to_period('M').dt.start_time.dt.date
    else:
        df['period'] = df['timestamp'].dt.date  # Default to daily
    
    # Aggregate data
    agg_df = df.groupby('period').agg({
        'surplus_energy': 'sum'
    }).reset_index()
    
    # Convert Wh to kWh for better readability
    agg_df['surplus_energy_kwh'] = agg_df['surplus_energy'] / 1000
    
    # Create figure
    fig = go.Figure()
    
    # Add surplus energy trace with color based on positive/negative
    surplus_color = agg_df['surplus_energy_kwh'].apply(
        lambda x: 'rgba(50, 171, 96, 0.7)' if x >= 0 else 'rgba(219, 64, 82, 0.7)'
    )
    
    fig.add_trace(go.Bar(
        x=agg_df['period'],
        y=agg_df['surplus_energy_kwh'],
        name='Surplus Energie',
        marker_color=surplus_color
    ))
    
    # Period-specific title
    period_titles = {
        'daily': 'Dagelijkse',
        'weekly': 'Wekelijkse',
        'monthly': 'Maandelijkse'
    }
    title_prefix = period_titles.get(period, 'Dagelijkse')
    
    # Customize layout
    fig.update_layout(
        title=f'{title_prefix} Surplus Energie',
        xaxis_title='Datum',
        yaxis_title='Surplus Energie (kWh)',
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Add zero line
    fig.add_hline(
        y=0, 
        line=dict(color='rgba(0, 0, 0, 0.3)', width=1, dash='dash'),
        annotation_text="Break-even",
        annotation_position="bottom right"
    )
    
    return fig
