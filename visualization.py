# Oorspronkelijke content van visualization.py blijft ongewijzigd

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
