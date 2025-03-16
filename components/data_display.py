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
    
    if period == 'daily' and 'date' in data.columns:
        x_values = data['date']
        title = 'Dagelijkse Energieproductie en -verbruik'
    elif period == 'weekly' and 'week' in data.columns:
        x_values = data['week']
        title = 'Wekelijkse Energieproductie en -verbruik'
    elif period == 'monthly' and 'month' in data.columns:
        x_values = data['month']
        title = 'Maandelijkse Energieproductie en -verbruik'
    else:
        st.warning(f"Kolommen voor periode '{period}' niet gevonden in data.")
        return
    
    # Create figure
    fig = go.Figure()
    
    # Add production if available
    if 'energy_produced_kwh' in data.columns:
        fig.add_trace(go.Bar(
            x=x_values,
            y=data['energy_produced_kwh'],
            name='Productie',
            marker_color='rgba(50, 171, 96, 0.7)'
        ))
    
    # Add consumption if available
    if 'energy_consumed_kwh' in data.columns:
        fig.add_trace(go.Bar(
            x=x_values,
            y=data['energy_consumed_kwh'],
            name='Verbruik',
            marker_color='rgba(219, 64, 82, 0.7)'
        ))
    
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