"""
Reusable data display components for the Zonnepanelen_check application.

This module contains components for displaying data in a consistent way throughout the app.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.ui_helpers import format_number


def show_data_metrics(summary):
    """
    Display key metrics from data summary.
    
    Args:
        summary: Dictionary with summary data
    """
    if not summary:
        return
    
    cols = st.columns(4)
    with cols[0]:
        st.metric("Totaal geproduceerd", f"{summary.get('total_produced_kwh', 0):.1f} kWh")
    with cols[1]:
        st.metric("Totaal verbruikt", f"{summary.get('total_consumed_kwh', 0):.1f} kWh")
    with cols[2]:
        st.metric("Zelfvoorziening", f"{summary.get('self_sufficiency_percent', 0):.1f}%")
    with cols[3]:
        st.metric("Surplus energie", f"{summary.get('surplus_energy_kwh', 0):.1f} kWh")


def show_energy_chart(data, period='daily'):
    """
    Display an energy production and consumption chart.
    
    Args:
        data: DataFrame with energy data
        period: Period for data aggregation ('daily', 'weekly', 'monthly')
    """
    if data is None or data.empty:
        st.info("Geen data beschikbaar voor visualisatie.")
        return

    # Debug info - uncomment if needed to diagnose issues
    # st.write("Debug: Beschikbare kolommen in data", list(data.columns))
    
    # Determine the appropriate date column based on period
    if period == 'daily':
        if 'date' in data.columns:
            x_values = data['date']
        else:
            # Try to find alternative column names
            alternative_columns = ['day', 'Date', 'datum']
            for col in alternative_columns:
                if col in data.columns:
                    x_values = data[col]
                    break
            else:
                # If no match is found, use the index as a last resort
                st.warning(f"Geen datumkolom gevonden voor {period} periode. Gebruik index voor visualisatie.")
                x_values = data.index
        title = 'Dagelijkse Energieproductie en -verbruik'
        
    elif period == 'weekly':
        if 'week_start' in data.columns:
            x_values = data['week_start']
        elif 'year_week' in data.columns:
            x_values = data['year_week']
        else:
            st.warning(f"Geen weekkolom gevonden voor {period} periode.")
            return
        title = 'Wekelijkse Energieproductie en -verbruik'
        
    elif period == 'monthly':
        if 'month_start' in data.columns:
            x_values = data['month_start']
        elif 'year_month' in data.columns:
            x_values = data['year_month']
        else:
            st.warning(f"Geen maandkolom gevonden voor {period} periode.")
            return
        title = 'Maandelijkse Energieproductie en -verbruik'
        
    else:
        st.warning(f"Onbekende periode: {period}")
        return
    
    # Create figure
    fig = go.Figure()
    
    # Prioritize standardized column names first
    if 'energy_produced_kwh' in data.columns:
        fig.add_trace(go.Bar(
            x=x_values,
            y=data['energy_produced_kwh'],
            name='Productie',
            marker_color='rgba(50, 171, 96, 0.7)'
        ))
    # Fall back to alternative naming schemes if standardized names not found
    elif 'Energy Produced (kWh)' in data.columns:
        fig.add_trace(go.Bar(
            x=x_values,
            y=data['Energy Produced (kWh)'],
            name='Productie',
            marker_color='rgba(50, 171, 96, 0.7)'
        ))
    elif 'Energy Produced (Wh)_kWh' in data.columns:
        fig.add_trace(go.Bar(
            x=x_values,
            y=data['Energy Produced (Wh)_kWh'],
            name='Productie',
            marker_color='rgba(50, 171, 96, 0.7)'
        ))
    else:
        st.warning("Geen productiedata gevonden in het juiste formaat.")
    
    # Similar approach for consumption data
    if 'energy_consumed_kwh' in data.columns:
        fig.add_trace(go.Bar(
            x=x_values,
            y=data['energy_consumed_kwh'],
            name='Verbruik',
            marker_color='rgba(219, 64, 82, 0.7)'
        ))
    elif 'Energy Consumed (kWh)' in data.columns:
        fig.add_trace(go.Bar(
            x=x_values,
            y=data['Energy Consumed (kWh)'],
            name='Verbruik',
            marker_color='rgba(219, 64, 82, 0.7)'
        ))
    elif 'Energy Consumed (Wh)_kWh' in data.columns:
        fig.add_trace(go.Bar(
            x=x_values,
            y=data['Energy Consumed (Wh)_kWh'],
            name='Verbruik',
            marker_color='rgba(219, 64, 82, 0.7)'
        ))
    else:
        st.warning("Geen verbruiksdata gevonden in het juiste formaat.")
    
    # Customize layout
    fig.update_layout(
        title=title,
        xaxis_title='Periode',
        yaxis_title='Energie (kWh)',
        template='plotly_white',
        barmode='group',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def show_storage_results(storage_type, results):
    """
    Display storage calculation results consistently.
    
    Args:
        storage_type: Type of storage ('boiler' or 'battery')
        results: Dictionary with calculation results
    """
    if not results:
        st.info(f"Geen berekeningen beschikbaar voor {storage_type}.")
        return
    
    # Display different metrics based on storage type
    if storage_type == 'boiler':
        cols = st.columns(4)
        with cols[0]:
            st.metric("Gas besparing", f"{results.get('total_gas_saved_m3', 0):.1f} m³")
        with cols[1]:
            st.metric("Financiële besparing", f"€ {results.get('total_financial_savings', 0):.2f}")
        with cols[2]:
            st.metric("Energie benut", f"{results.get('total_energy_used_kwh', 0):.1f} kWh")
        with cols[3]:
            st.metric("Benutting surplus", f"{results.get('surplus_utilization_percent', 0):.1f}%")
    
    elif storage_type == 'battery':
        cols = st.columns(4)
        with cols[0]:
            st.metric("Financieel voordeel", f"€ {results.get('total_financial_benefit_eur', 0):.2f}")
        with cols[1]:
            st.metric("Geladen energie", f"{results.get('total_charged_kwh', 0):.1f} kWh")
        with cols[2]:
            st.metric("Gebruikte energie", f"{results.get('total_discharged_kwh', 0):.1f} kWh")
        with cols[3]:
            st.metric("Netafhankelijkheid ↓", f"{results.get('grid_import_reduction_percent', 0):.1f}%")
    
    # Show detailed results in expander
    with st.expander("Gedetailleerde resultaten"):
        result_df = results.get('result_df')
        if result_df is not None:
            st.dataframe(result_df, use_container_width=True)