"""
Visualization page module for the Zonnepanelen_check application.

This module contains the visualization and comparison page functionality.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import visualization as viz


def show_visualization_page(data_processor, config_manager):
    """
    Display the visualization page.
    
    Args:
        data_processor: Instance of DataProcessor
        config_manager: Instance of ConfigManager
    """
    st.header("Visualisatie en Vergelijking")
    
    # Check if data is loaded
    if data_processor.data is None:
        st.warning("Geen data geladen. Ga naar de 'Data Upload' pagina om data te laden.")
        st.button("Naar Data Upload", on_click=lambda: setattr(st.session_state, 'active_page', 'Data Upload'))
        return
    
    # Create tabs for different visualizations
    tabs = st.tabs([
        "Energieproductie & Verbruik", 
        "Surplus Energie", 
        "Vergelijking Opties",
        "Seizoensanalyse"
    ])
    
    # Energy production and consumption tab
    with tabs[0]:
        st.subheader("Energieproductie en -verbruik")
        
        # Period selector
        period = st.radio(
            "Periode",
            ["Dagelijks", "Wekelijks", "Maandelijks"],
            horizontal=True
        )
        
        period_map = {"Dagelijks": "daily", "Wekelijks": "weekly", "Maandelijks": "monthly"}
        selected_period = period_map[period]
        
        # Show production & consumption chart
        fig = viz.plot_energy_production_consumption(data_processor.data, period=selected_period)
        st.plotly_chart(fig, use_container_width=True)
        
        # Additional data table
        with st.expander("Toon data tabel"):
            if selected_period == "daily" and data_processor.daily_data is not None:
                st.dataframe(data_processor.daily_data)
            elif selected_period == "weekly" and data_processor.weekly_data is not None:
                st.dataframe(data_processor.weekly_data)
            elif selected_period == "monthly" and data_processor.monthly_data is not None:
                st.dataframe(data_processor.monthly_data)
    
    # Surplus energy tab
    with tabs[1]:
        st.subheader("Surplus Energie")
        
        # Period selector for surplus energy
        surplus_period = st.radio(
            "Periode",
            ["Dagelijks", "Wekelijks", "Maandelijks"],
            horizontal=True,
            key="surplus_period"
        )
        
        period_map = {"Dagelijks": "daily", "Wekelijks": "weekly", "Maandelijks": "monthly"}
        selected_surplus_period = period_map[surplus_period]
        
        # Show surplus energy chart
        fig = viz.plot_surplus_energy(data_processor.data, period=selected_surplus_period)
        st.plotly_chart(fig, use_container_width=True)
        
        # Show hourly averages
        st.subheader("Gemiddeld energieprofiel per uur")
        hourly_avg = data_processor.get_hourly_averages()
        
        if not hourly_avg.empty:
            # Create figure
            fig = go.Figure()
            
            # Add production
            if 'Energy Produced (kWh)' in hourly_avg.columns:
                fig.add_trace(go.Scatter(
                    x=hourly_avg['hour'],
                    y=hourly_avg['Energy Produced (kWh)'],
                    name='Productie',
                    line=dict(color='rgba(50, 171, 96, 1)', width=2)
                ))
            
            # Add consumption
            if 'Energy Consumed (kWh)' in hourly_avg.columns:
                fig.add_trace(go.Scatter(
                    x=hourly_avg['hour'],
                    y=hourly_avg['Energy Consumed (kWh)'],
                    name='Verbruik',
                    line=dict(color='rgba(219, 64, 82, 1)', width=2)
                ))
            
            # Customize layout
            fig.update_layout(
                title='Gemiddeld dagelijks energieprofiel per uur',
                xaxis_title='Uur van de dag',
                yaxis_title='Energie (kWh)',
                template='plotly_white',
                xaxis=dict(tickmode='array', tickvals=list(range(0,24))),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Comparison tab
    with tabs[2]:
        st.subheader("Vergelijking Opslagopties")
        
        # Check if calculations are available
        has_boiler_results = 'boiler_results' in st.session_state
        has_battery_results = 'battery_results' in st.session_state
        
        if not has_boiler_results and not has_battery_results:
            st.info("Geen berekeningen beschikbaar. Voer eerst berekeningen uit op de 'Warmwaterboiler' en 'Accu' pagina's.")
            
            # Quick links to calculation pages
            col1, col2 = st.columns(2)
            with col1:
                st.button("Naar Warmwaterboiler", on_click=lambda: setattr(st.session_state, 'active_page', 'Warmwaterboiler'))
            with col2:
                st.button("Naar Accu", on_click=lambda: setattr(st.session_state, 'active_page', 'Accu'))
        else:
            # Prepare comparison data
            comparison_data = {}
            
            economic_config = config_manager.get_section('economic')
            electricity_price = float(economic_config.get('electricity_price', 0.22))
            feed_in_tariff = float(economic_config.get('feed_in_tariff', 0.09))
            
            # Get total surplus energy
            total_surplus = 0
            if hasattr(data_processor, 'daily_data') and data_processor.daily_data is not None:
                if 'surplus_energy' in data_processor.daily_data.columns:
                    total_surplus = data_processor.daily_data['surplus_energy'].sum() / 1000  # convert to kWh
            
            # Calculate financial benefit of doing nothing (feed-in)
            feed_in_benefit = total_surplus * feed_in_tariff
            comparison_data["Terugleveren aan net"] = feed_in_benefit
            
            # Add boiler and battery results if available
            if has_boiler_results:
                boiler_results = st.session_state['boiler_results']
                comparison_data["Warmwaterboiler"] = boiler_results.get('total_financial_savings', 0)
            
            if has_battery_results:
                battery_results = st.session_state['battery_results']
                comparison_data["Accu"] = battery_results.get('total_financial_benefit_eur', 0)
            
            # Financial comparison chart
            st.subheader("Financiële vergelijking")
            fig = viz.plot_comparison_chart(comparison_data, "Financieel voordeel verschillende opties (€)")
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed comparison table
            st.subheader("Detailvergelijking")
            
            # Create comparison table
            comparison_table = {
                "Optie": [],
                "Financieel voordeel": [],
                "Energie benut (kWh)": [],
                "Benutting surplus (%)": []
            }
            
            # Feed-in data
            comparison_table["Optie"].append("Terugleveren aan net")
            comparison_table["Financieel voordeel"].append(f"€ {feed_in_benefit:.2f}")
            comparison_table["Energie benut (kWh)"].append(f"{total_surplus:.1f}")
            comparison_table["Benutting surplus (%)"].append("100%")
            
            # Boiler data
            if has_boiler_results:
                boiler_results = st.session_state['boiler_results']
                comparison_table["Optie"].append("Warmwaterboiler")
                comparison_table["Financieel voordeel"].append(f"€ {boiler_results.get('total_financial_savings', 0):.2f}")
                comparison_table["Energie benut (kWh)"].append(f"{boiler_results.get('total_energy_used_kwh', 0):.1f}")
                comparison_table["Benutting surplus (%)"].append(f"{boiler_results.get('surplus_utilization_percent', 0):.1f}%")
            
            # Battery data
            if has_battery_results:
                battery_results = st.session_state['battery_results']
                comparison_table["Optie"].append("Accu")
                comparison_table["Financieel voordeel"].append(f"€ {battery_results.get('total_financial_benefit_eur', 0):.2f}")
                comparison_table["Energie benut (kWh)"].append(f"{battery_results.get('total_discharged_kwh', 0):.1f}")
                energy_used = battery_results.get('total_discharged_kwh', 0)
                utilization = (energy_used / total_surplus * 100) if total_surplus > 0 else 0
                comparison_table["Benutting surplus (%)"].append(f"{utilization:.1f}%")
            
            # Show table
            st.table(pd.DataFrame(comparison_table))
            
            # Additional insights
            st.subheader("Inzichten")
            
            best_option = max(comparison_data.items(), key=lambda x: x[1])
            st.info(f"Op basis van de huidige gegevens levert **{best_option[0]}** het hoogste financiële voordeel op van **€ {best_option[1]:.2f}**.")
    
    # Seasonal analysis tab
    with tabs[3]:
        st.subheader("Seizoensanalyse")
        
        # Get seasonal data
        seasonal_avg = data_processor.get_seasonal_averages()
        
        if not seasonal_avg.empty:
            # Create figure for production and consumption
            fig = go.Figure()
            
            # Add production
            if 'Energy Produced (Wh)' in seasonal_avg.columns:
                fig.add_trace(go.Bar(
                    x=seasonal_avg['season'],
                    y=seasonal_avg['Energy Produced (Wh)'] / 1000,
                    name='Productie',
                    marker_color='rgba(50, 171, 96, 0.7)'
                ))
            
            # Add consumption
            if 'Energy Consumed (Wh)' in seasonal_avg.columns:
                fig.add_trace(go.Bar(
                    x=seasonal_avg['season'],
                    y=seasonal_avg['Energy Consumed (Wh)'] / 1000,
                    name='Verbruik',
                    marker_color='rgba(219, 64, 82, 0.7)'
                ))
            
            # Customize layout
            fig.update_layout(
                title='Seizoensgemiddelden: Productie en Verbruik',
                xaxis_title='Seizoen',
                yaxis_title='Energie (kWh/dag)',
                template='plotly_white',
                barmode='group',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Create figure for surplus energy
            if 'surplus_energy' in seasonal_avg.columns:
                fig2 = go.Figure()
                
                fig2.add_trace(go.Bar(
                    x=seasonal_avg['season'],
                    y=seasonal_avg['surplus_energy'] / 1000,
                    name='Surplus Energie',
                    marker=dict(
                        color=seasonal_avg['surplus_energy'].apply(
                            lambda x: 'rgba(50, 171, 96, 0.7)' if x >= 0 else 'rgba(219, 64, 82, 0.7)'
                        )
                    )
                ))
                
                # Customize layout
                fig2.update_layout(
                    title='Seizoensgemiddelden: Surplus Energie',
                    xaxis_title='Seizoen',
                    yaxis_title='Surplus Energie (kWh/dag)',
                    template='plotly_white'
                )
                
                st.plotly_chart(fig2, use_container_width=True)
            
            # Display table with seasonal data
            with st.expander("Toon seizoensdata"):
                display_seasonal = seasonal_avg.copy()
                
                # Convert Wh columns to kWh for display
                for col in display_seasonal.columns:
                    if 'Wh' in col:
                        display_seasonal[col.replace('(Wh)', '(kWh/dag)')] = display_seasonal[col] / 1000
                        display_seasonal.drop(col, axis=1, inplace=True)
                
                if 'surplus_energy' in display_seasonal.columns:
                    display_seasonal['surplus_energy_kwh_dag'] = display_seasonal['surplus_energy'] / 1000
                    display_seasonal.drop('surplus_energy', axis=1, inplace=True)
                
                st.dataframe(display_seasonal, use_container_width=True)