"""
Utility plots module for the Zonnepanelen_check application.

This module contains general utility functions for plotting and visualization.
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import base64
import io
from typing import Dict, Any, List, Optional, Union


def plot_comparison_chart(comparison_data: Dict[str, float], title: str = "Comparison") -> go.Figure:
    """
    Plot a comparison bar chart for different options.
    
    Args:
        comparison_data: Dictionary mapping option names to values
        title: Title for the chart
        
    Returns:
        Plotly figure object
    """
    if not comparison_data:
        return go.Figure()
    
    # Sort data by value for better visualization
    sorted_data = sorted(comparison_data.items(), key=lambda x: x[1], reverse=True)
    options = [item[0] for item in sorted_data]
    values = [item[1] for item in sorted_data]
    
    # Create color scale based on values
    max_value = max(values) if values else 0
    colors = ['rgba(50, 171, 96, ' + str(0.4 + 0.6 * (value / max_value)) + ')' for value in values]
    
    # Create figure
    fig = go.Figure()
    
    # Add bars
    fig.add_trace(go.Bar(
        x=options,
        y=values,
        marker_color=colors,
        text=[f"€ {value:.2f}" for value in values],
        textposition='auto'
    ))
    
    # Customize layout
    fig.update_layout(
        title=title,
        xaxis_title="Options",
        yaxis_title="Value (€)",
        template='plotly_white',
        yaxis=dict(rangemode='nonnegative')
    )
    
    return fig


def fig_to_base64(fig: go.Figure) -> str:
    """
    Convert a plotly figure to a base64 string for embedding in HTML.
    
    Args:
        fig: Plotly figure object
        
    Returns:
        Base64 encoded string of the figure
    """
    # Create a buffer for the image
    buf = io.BytesIO()
    
    # Save the figure as PNG
    fig.write_image(buf, format='png', engine='kaleido')
    
    # Reset buffer position
    buf.seek(0)
    
    # Encode as base64
    encoded = base64.b64encode(buf.read()).decode('ascii')
    
    return f"data:image/png;base64,{encoded}"


def create_color_palette(n_colors: int, color_scale: str = 'Viridis') -> List[str]:
    """
    Create a color palette with the given number of colors.
    
    Args:
        n_colors: Number of colors to generate
        color_scale: Name of the color scale to use
        
    Returns:
        List of color strings in rgba or hex format
    """
    if n_colors <= 0:
        return []
    
    # Use plotly express to generate colors from a continuous scale
    colors = px.colors.sample_colorscale(
        color_scale, 
        [i / (n_colors - 1) for i in range(n_colors)] if n_colors > 1 else [0.5]
    )
    
    return colors


def format_figure_for_streamlit(fig: go.Figure, height: Optional[int] = None) -> go.Figure:
    """
    Format a plotly figure for optimal display in Streamlit.
    
    Args:
        fig: Plotly figure to format
        height: Optional height in pixels
        
    Returns:
        Formatted plotly figure
    """
    # Create a copy to avoid modifying the original
    fig_copy = go.Figure(fig)
    
    # Set a consistent theme
    fig_copy.update_layout(
        template='plotly_white',
        margin=dict(l=40, r=40, t=50, b=40),
    )
    
    # Set height if provided
    if height:
        fig_copy.update_layout(height=height)
    
    # Make legend more compact and positioned better for Streamlit
    fig_copy.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10)
        )
    )
    
    # Make all text a bit larger for better readability
    fig_copy.update_layout(
        title_font_size=16,
        xaxis_title_font_size=14,
        yaxis_title_font_size=14,
        font_size=12
    )
    
    return fig_copy
