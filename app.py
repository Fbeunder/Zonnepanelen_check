"""
Main application module for the Zonnepanelen_check application.

This module contains the Streamlit application that provides the user interface
for analyzing solar panel surplus energy storage options.
"""
import streamlit as st
import pandas as pd
import numpy as np
import os
import tempfile
import datetime
from typing import Dict, List, Tuple, Union, Optional, Any
import plotly.graph_objects as go
import base64
import io
import pathlib

# Import application modules
import utils
from data_processor import DataProcessor
from config_manager import ConfigManager
from boiler_module import BoilerCalculator
from battery_module import BatteryCalculator
import visualization as viz


def main():
    """Main function to run the Streamlit application."""
    # Set page config
    st.set_page_config(
        page_title="Zonnepanelen Check",
        page_icon="☀️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state for data and calculations
    if 'data_processor' not in st.session_state:
        st.session_state.data_processor = DataProcessor()
    
    if 'config_manager' not in st.session_state:
        st.session_state.config_manager = ConfigManager()
    
    if 'active_page' not in st.session_state:
        st.session_state.active_page = "Home"
    
    # Get reference to session objects
    data_processor = st.session_state.data_processor
    config_manager = st.session_state.config_manager
    
    # Application title and header
    st.title("Zonnepanelen Check")
    st.subheader("Analyse van opslag-opties voor overschot zonne-energie")
    
    # Sidebar navigation
    with st.sidebar:
        st.header("Navigatie")
        
        # Navigation buttons
        nav_options = [
            "Home", 
            "Data Upload", 
            "Warmwaterboiler", 
            "Accu", 
            "Visualisatie", 
            "Configuratie"
        ]
        
        for nav_option in nav_options:
            if st.button(
                nav_option, 
                use_container_width=True,
                type="primary" if st.session_state.active_page == nav_option else "secondary"
            ):
                st.session_state.active_page = nav_option
                st.experimental_rerun()
        
        # Show data status
        if data_processor.data is not None:
            st.success("✓ Data geladen")
            
            # Display file info
            file_info = data_processor.get_file_info()
            if file_info:
                with st.expander("Gegevens bestand"):
                    st.write(f"Bestand: {file_info.get('file_name', 'Onbekend')}")
                    st.write(f"Datapunten: {file_info.get('record_count', 0):,}")
                    st.write(f"Interval: {file_info.get('time_interval_minutes', 0)} minuten")
                    st.write(f"Periode: {file_info.get('first_record', '')} - {file_info.get('last_record', '')}")
        else:
            st.info("Geen data geladen")
    
    # Main content area - show different pages based on navigation
    if st.session_state.active_page == "Home":
        show_home_page()
    
    elif st.session_state.active_page == "Data Upload":
        show_data_upload_page(data_processor, config_manager)
    
    elif st.session_state.active_page == "Warmwaterboiler":
        show_boiler_page(data_processor, config_manager)
    
    elif st.session_state.active_page == "Accu":
        show_battery_page(data_processor, config_manager)
    
    elif st.session_state.active_page == "Visualisatie":
        show_visualization_page(data_processor, config_manager)
    
    elif st.session_state.active_page == "Configuratie":
        show_configuration_page(config_manager)


def show_home_page():
    """Display the home page with application overview."""
    st.header("Welkom bij Zonnepanelen Check!")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## Over deze applicatie
        
        Deze applicatie helpt u bij het analyseren van mogelijke opties voor 
        het opslaan van overschot zonne-energie en berekent de potentiële besparingen.
        
        ### Wat kunt u doen?
        
        1. **Upload uw energiedata**: Laad uw CSV-bestand met productie- en verbruiksgegevens
        2. **Analyseer warmwaterboiler-optie**: Bereken hoeveel gas u kunt besparen door overproductie 
        te gebruiken voor het verwarmen van water
        3. **Analyseer accu-optie**: Bereken hoeveel u kunt besparen door overproductie op te slaan in een accu
        4. **Visualiseer resultaten**: Bekijk grafieken en vergelijk de verschillende opties
        5. **Pas configuratie aan**: Personaliseer de berekeningen op basis van uw specifieke situatie
        
        ### Aan de slag:
        
        Klik op "Data Upload" in het navigatiemenu om te beginnen.
        """)
    
    with col2:
        st.markdown("""
        ### CSV-formaat
        
        Uw CSV-bestand moet de volgende kolommen bevatten:
        
        ```
        Date/Time,Energy Produced (Wh),Energy Consumed (Wh),Exported to Grid (Wh),Imported from Grid (Wh)
        03/01/2024 00:00,0,81,0,81
        03/01/2024 00:15,0,68,0,68
        ...
        ```
        
        De laatste twee kolommen zijn optioneel.
        """)
        
        # Show dummy example chart
        st.markdown("### Voorbeeld visualisatie")
        
        # Create a simple example chart with dummy data
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        production = np.random.normal(loc=15, scale=5, size=len(dates))
        consumption = np.random.normal(loc=12, scale=3, size=len(dates))
        
        # Create example chart
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=dates,
            y=production,
            name='Productie',
            marker_color='rgba(50, 171, 96, 0.7)'
        ))
        fig.add_trace(go.Bar(
            x=dates,
            y=consumption,
            name='Verbruik',
            marker_color='rgba(219, 64, 82, 0.7)'
        ))
        fig.update_layout(barmode='group', height=250)
        st.plotly_chart(fig, use_container_width=True)


def show_data_upload_page(data_processor, config_manager):
    """Display the data upload page."""
    st.header("Data Upload")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        Upload hier uw CSV-bestand met energiegegevens. Het bestand moet in het juiste formaat zijn
        met minimaal de kolommen Date/Time, Energy Produced (Wh) en Energy Consumed (Wh).
        """)
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Upload CSV bestand met productie- en verbruiksgegevens",
            type="csv"
        )
        
        # Use example data option
        use_example = st.checkbox("Voorbeeld data gebruiken")
        
        # Process data button
        process_data = st.button("Data inladen en verwerken", type="primary")
        
        if process_data:
            if uploaded_file:
                # Show spinner during processing
                with st.spinner("Bezig met verwerken van de data..."):
                    # Save uploaded file to temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        temp_path = tmp_file.name
                    
                    # Load data from the temp file
                    success = data_processor.load_data(temp_path)
                    
                    # Clean up
                    os.unlink(temp_path)
                    
                    if success:
                        st.session_state['data_loaded'] = True
                        st.success("Data succesvol ingeladen en verwerkt!")
                        # Update last used file in config
                        config_manager.update_last_used_file(uploaded_file.name)
                    else:
                        st.error("Fout bij het inladen van de data. Controleer het CSV-bestand format.")
                        
            elif use_example:
                with st.spinner("Bezig met laden van voorbeelddata..."):
                    # Get path to sample data file
                    sample_file_path = os.path.join(
                        pathlib.Path(__file__).parent, 
                        "examples", 
                        "sample_energy_data.csv"
                    )
                    
                    # Check if sample file exists
                    if os.path.exists(sample_file_path):
                        # Load data from the sample file
                        success = data_processor.load_data(sample_file_path)
                        
                        if success:
                            st.session_state['data_loaded'] = True
                            st.success("Voorbeelddata succesvol ingeladen!")
                            # Update last used file in config
                            config_manager.update_last_used_file("sample_energy_data.csv")
                        else:
                            st.error("Fout bij het inladen van de voorbeelddata.")
                    else:
                        st.error(f"Voorbeeldbestand niet gevonden. Pad: {sample_file_path}")
            else:
                st.warning("Upload een CSV-bestand of gebruik de voorbeeld data.")
    
    with col2:
        st.markdown("### Vereist formaat")
        st.code("""
Date/Time,Energy Produced (Wh),Energy Consumed (Wh),Exported to Grid (Wh),Imported from Grid (Wh)
03/01/2024 00:00,0,81,0,81
03/01/2024 00:15,0,68,0,68
03/01/2024 00:30,0,66,0,66
...
        """)
        
        st.markdown("""
        ### Ondersteunde datums
        
        De volgende datum formaten worden ondersteund:
        - DD/MM/YYYY HH:MM
        - YYYY-MM-DD HH:MM:SS  
        - MM/DD/YYYY HH:MM
        """)
    
    # Show data preview if data is loaded
    if data_processor.data is not None:
        st.header("Data Preview")
        
        # Display data summary
        summary = data_processor.get_data_summary()
        
        if summary:
            cols = st.columns(4)
            with cols[0]:
                st.metric("Totaal geproduceerd", f"{summary.get('total_produced_kwh', 0):.1f} kWh")
            with cols[1]:
                st.metric("Totaal verbruikt", f"{summary.get('total_consumed_kwh', 0):.1f} kWh")
            with cols[2]:
                st.metric("Zelfvoorziening", f"{summary.get('self_sufficiency_percent', 0):.1f}%")
            with cols[3]:
                st.metric("Surplus energie", f"{summary.get('surplus_energy_kwh', 0):.1f} kWh")
        
        # Show data table
        st.subheader("Geïmporteerde data")
        st.dataframe(data_processor.data.head(100), use_container_width=True)
        
        # Show production & consumption chart
        st.subheader("Productie & Verbruik (Dagelijks)")
        if data_processor.daily_data is not None:
            fig = viz.plot_energy_production_consumption(data_processor.data, period='daily')
            st.plotly_chart(fig, use_container_width=True)


def show_boiler_page(data_processor, config_manager):
    """Display the water boiler analysis page."""
    st.header("Warmwaterboiler Analyse")
    
    # Check if data is loaded
    if data_processor.data is None:
        st.warning("Geen data geladen. Ga naar de 'Data Upload' pagina om data te laden.")
        st.button("Naar Data Upload", on_click=lambda: setattr(st.session_state, 'active_page', 'Data Upload'))
        return
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Boiler Instellingen")
        
        # Get boiler configuration
        boiler_config = config_manager.get_config('boiler')
        economic_config = config_manager.get_config('economic')
        
        # Boiler settings
        boiler_capacity = st.number_input(
            "Boiler capaciteit (Liter)",
            min_value=10,
            max_value=500,
            value=int(boiler_config.get('capacity', 80)),
            step=10
        )
        
        boiler_efficiency = st.slider(
            "Boiler efficiëntie (%)",
            min_value=50,
            max_value=100,
            value=int(boiler_config.get('efficiency', 0.9) * 100),
            step=5
        ) / 100
        
        daily_hot_water = st.number_input(
            "Dagelijks warmwaterverbruik (Liter)",
            min_value=10,
            max_value=500,
            value=int(boiler_config.get('daily_hot_water_usage', 120)),
            step=10
        )
        
        water_temp_rise = st.number_input(
            "Temperatuurstijging (°C)",
            min_value=10,
            max_value=70,
            value=int(boiler_config.get('water_temperature_rise', 35)),
            step=5,
            help="Temperatuurverschil tussen koud en warm water"
        )
        
        gas_price = st.number_input(
            "Gasprijs (€/m³)",
            min_value=0.01,
            max_value=5.0,
            value=float(economic_config.get('gas_price', 0.80)),
            step=0.01
        )
        
        # Update configuration
        config_manager.update_section('boiler', {
            'capacity': boiler_capacity,
            'efficiency': boiler_efficiency,
            'daily_hot_water_usage': daily_hot_water,
            'water_temperature_rise': water_temp_rise
        })
        
        config_manager.update_section('economic', {
            'gas_price': gas_price
        })
        
        # Calculate button
        calculate_button = st.button("Berekenen", type="primary")
    
    with col2:
        st.subheader("Beschrijving")
        st.markdown("""
        De warmwaterboiler module berekent hoeveel gas u kunt besparen door overtollige
        energie van uw zonnepanelen te gebruiken voor het verwarmen van water.
        
        ### Hoe werkt het?
        
        1. De applicatie analyseert de momenten waarop uw productie hoger is dan uw verbruik
        2. Deze surplus energie kan worden gebruikt om water te verwarmen in plaats van teruggeleverd aan het net
        3. De berekening houdt rekening met uw dagelijkse warmwaterverbruik en de capaciteit van de boiler
        4. De besparing wordt uitgedrukt in kubieke meters gas en financiële besparing
        
        ### Parameters
        
        - **Boiler capaciteit**: Totale capaciteit van de warmwaterboiler in liters
        - **Boiler efficiëntie**: Hoeveel energie effectief wordt omgezet in warmte
        - **Dagelijks warmwaterverbruik**: Gemiddeld dagelijks warmwaterverbruik in liters
        - **Temperatuurstijging**: Verschil tussen inkomend koud water en gewenst warm water
        - **Gasprijs**: Actuele gasprijs per kubieke meter
        """)
    
    # Run calculation if button is pressed or previous results exist
    if calculate_button or 'boiler_results' in st.session_state:
        st.divider()
        
        # Only calculate if button is pressed (to avoid recalculating on page navigation)
        if calculate_button:
            with st.spinner("Bezig met berekenen..."):
                # Create configuration for calculation
                config = {
                    'boiler': config_manager.get_config('boiler'),
                    'economic': config_manager.get_config('economic')
                }
                
                # Create calculator and run calculation
                boiler_calculator = BoilerCalculator(data_processor.data, config)
                results = boiler_calculator.calculate()
                
                # Store in session state
                st.session_state['boiler_results'] = results
                
                # Show success message
                st.success("Berekening voltooid!")
        
        # Display results from session state
        if 'boiler_results' in st.session_state:
            results = st.session_state['boiler_results']
            
            if results:
                # Display key metrics
                cols = st.columns(4)
                with cols[0]:
                    st.metric("Gas besparing", f"{results.get('total_gas_saved_m3', 0):.1f} m³")
                with cols[1]:
                    st.metric("Financiële besparing", f"€ {results.get('total_financial_savings', 0):.2f}")
                with cols[2]:
                    st.metric("Energie benut", f"{results.get('total_energy_used_kwh', 0):.1f} kWh")
                with cols[3]:
                    st.metric("Benutting surplus", f"{results.get('surplus_utilization_percent', 0):.1f}%")
                
                # Show boiler energy usage chart
                st.subheader("Boiler Energiegebruik en Gasbesparing")
                fig = viz.plot_boiler_energy_usage(results)
                st.plotly_chart(fig, use_container_width=True)
                
                # Show detailed results
                with st.expander("Gedetailleerde resultaten"):
                    result_df = results.get('result_df')
                    if result_df is not None:
                        st.dataframe(result_df, use_container_width=True)


def show_battery_page(data_processor, config_manager):
    """Display the battery analysis page."""
    st.header("Accu Analyse")
    
    # Check if data is loaded
    if data_processor.data is None:
        st.warning("Geen data geladen. Ga naar de 'Data Upload' pagina om data te laden.")
        st.button("Naar Data Upload", on_click=lambda: setattr(st.session_state, 'active_page', 'Data Upload'))
        return
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Accu Instellingen")
        
        # Get battery configuration
        battery_config = config_manager.get_config('battery')
        economic_config = config_manager.get_config('economic')
        
        # Battery settings
        battery_capacity = st.number_input(
            "Accu capaciteit (kWh)",
            min_value=1.0,
            max_value=50.0,
            value=float(battery_config.get('capacity', 10.0)),
            step=0.5
        )
        
        battery_efficiency = st.slider(
            "Accu efficiëntie (%)",
            min_value=50,
            max_value=100,
            value=int(battery_config.get('efficiency', 0.9) * 100),
            step=5
        ) / 100
        
        max_charge_rate = st.number_input(
            "Max laadvermogen (kW)",
            min_value=1.0,
            max_value=20.0,
            value=float(battery_config.get('max_charge_rate', 3.6)),
            step=0.1
        )
        
        max_discharge_rate = st.number_input(
            "Max ontlaadvermogen (kW)",
            min_value=1.0,
            max_value=20.0,
            value=float(battery_config.get('max_discharge_rate', 3.6)),
            step=0.1
        )
        
        min_soc = st.slider(
            "Minimaal laadniveau (%)",
            min_value=0,
            max_value=50,
            value=int(battery_config.get('min_soc', 10)),
            step=5
        )
        
        max_soc = st.slider(
            "Maximaal laadniveau (%)",
            min_value=50,
            max_value=100,
            value=int(battery_config.get('max_soc', 90)),
            step=5
        )
        
        # Economic parameters
        electricity_price = st.number_input(
            "Stroomprijs (€/kWh)",
            min_value=0.01,
            max_value=1.0,
            value=float(economic_config.get('electricity_price', 0.22)),
            step=0.01
        )
        
        feed_in_tariff = st.number_input(
            "Terugleveringstarief (€/kWh)",
            min_value=0.0,
            max_value=1.0,
            value=float(economic_config.get('feed_in_tariff', 0.09)),
            step=0.01
        )
        
        # Update configuration
        config_manager.update_section('battery', {
            'capacity': battery_capacity,
            'efficiency': battery_efficiency,
            'max_charge_rate': max_charge_rate,
            'max_discharge_rate': max_discharge_rate,
            'min_soc': min_soc,
            'max_soc': max_soc
        })
        
        config_manager.update_section('economic', {
            'electricity_price': electricity_price,
            'feed_in_tariff': feed_in_tariff
        })
        
        # Calculate button
        calculate_button = st.button("Berekenen", type="primary")
    
    with col2:
        st.subheader("Beschrijving")
        st.markdown("""
        De accu module berekent hoeveel u kunt besparen door overtollige energie 
        van uw zonnepanelen op te slaan in een thuisbatterij en later te gebruiken.
        
        ### Hoe werkt het?
        
        1. De applicatie analyseert de momenten waarop uw productie hoger is dan uw verbruik
        2. Deze surplus energie wordt opgeslagen in de batterij tot het maximum is bereikt
        3. Wanneer het verbruik hoger is dan de productie, wordt energie uit de batterij gebruikt
        4. De besparing wordt berekend op basis van vermeden inkoop en verminderde teruglevering
        
        ### Parameters
        
        - **Accu capaciteit**: Totale opslagcapaciteit van de accu in kWh
        - **Accu efficiëntie**: Hoeveel procent van de opgeslagen energie weer beschikbaar is
        - **Max laadvermogen**: Maximale snelheid waarmee de accu kan opladen
        - **Max ontlaadvermogen**: Maximale snelheid waarmee energie uit de accu kan worden gehaald
        - **Min/max laadniveau**: Bereik waarbinnen de accu wordt gebruikt
        - **Stroomprijs**: Prijs per kWh voor inkoop van stroom
        - **Terugleveringstarief**: Vergoeding per kWh voor teruglevering aan het net
        """)
    
    # Run calculation if button is pressed or previous results exist
    if calculate_button or 'battery_results' in st.session_state:
        st.divider()
        
        # Only calculate if button is pressed (to avoid recalculating on page navigation)
        if calculate_button:
            with st.spinner("Bezig met berekenen..."):
                # Create configuration for calculation
                config = {
                    'battery': config_manager.get_config('battery'),
                    'economic': config_manager.get_config('economic')
                }
                
                # Create calculator and run calculation
                battery_calculator = BatteryCalculator(data_processor.data, config)
                results = battery_calculator.calculate()
                
                # Store in session state
                st.session_state['battery_results'] = results
                
                # Show success message
                st.success("Berekening voltooid!")
        
        # Display results from session state
        if 'battery_results' in st.session_state:
            results = st.session_state['battery_results']
            
            if results:
                # Display key metrics
                cols = st.columns(4)
                with cols[0]:
                    st.metric("Financieel voordeel", f"€ {results.get('total_financial_benefit_eur', 0):.2f}")
                with cols[1]:
                    st.metric("Geladen energie", f"{results.get('total_charged_kwh', 0):.1f} kWh")
                with cols[2]:
                    st.metric("Gebruikte energie", f"{results.get('total_discharged_kwh', 0):.1f} kWh")
                with cols[3]:
                    st.metric("Netafhankelijkheid ↓", f"{results.get('grid_import_reduction_percent', 0):.1f}%")
                
                # Show battery state chart
                st.subheader("Accu Laadtoestand en Energiestromen")
                fig = viz.plot_battery_state(results)
                st.plotly_chart(fig, use_container_width=True)
                
                # Show detailed results
                with st.expander("Gedetailleerde resultaten"):
                    result_df = results.get('result_df')
                    if result_df is not None:
                        st.dataframe(result_df, use_container_width=True)


def show_visualization_page(data_processor, config_manager):
    """Display the visualization page."""
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
            
            economic_config = config_manager.get_config('economic')
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


def show_configuration_page(config_manager):
    """Display the configuration page."""
    st.header("Configuratie")
    
    tab1, tab2, tab3 = st.tabs(["Economische parameters", "Technische parameters", "Opslag/Backup"])
    
    # Economic parameters tab
    with tab1:
        st.subheader("Economische Parameters")
        
        # Get current economic config
        economic_config = config_manager.get_config('economic')
        
        # Create form for economic parameters
        with st.form("economic_form"):
            electricity_price = st.number_input(
                "Stroomprijs (€/kWh)",
                min_value=0.01,
                max_value=1.0,
                value=float(economic_config.get('electricity_price', 0.22)),
                step=0.01
            )
            
            feed_in_tariff = st.number_input(
                "Terugleveringstarief (€/kWh)",
                min_value=0.0,
                max_value=1.0,
                value=float(economic_config.get('feed_in_tariff', 0.09)),
                step=0.01
            )
            
            gas_price = st.number_input(
                "Gasprijs (€/m³)",
                min_value=0.01,
                max_value=5.0,
                value=float(economic_config.get('gas_price', 0.80)),
                step=0.01
            )
            
            save_economic = st.form_submit_button("Opslaan")
        
        if save_economic:
            # Update economic config
            config_manager.update_section('economic', {
                'electricity_price': electricity_price,
                'feed_in_tariff': feed_in_tariff,
                'gas_price': gas_price
            })
            st.success("Economische parameters opgeslagen!")
    
    # Technical parameters tab
    with tab2:
        st.subheader("Technische Parameters")
        
        # Create tabs for different modules
        mod_tab1, mod_tab2 = st.tabs(["Warmwaterboiler", "Accu"])
        
        # Boiler parameters
        with mod_tab1:
            # Get current boiler config
            boiler_config = config_manager.get_config('boiler')
            
            # Create form for boiler parameters
            with st.form("boiler_form"):
                boiler_capacity = st.number_input(
                    "Boiler capaciteit (Liter)",
                    min_value=10,
                    max_value=500,
                    value=int(boiler_config.get('capacity', 80)),
                    step=10
                )
                
                boiler_efficiency = st.slider(
                    "Boiler efficiëntie (%)",
                    min_value=50,
                    max_value=100,
                    value=int(boiler_config.get('efficiency', 0.9) * 100),
                    step=5
                ) / 100
                
                daily_hot_water = st.number_input(
                    "Dagelijks warmwaterverbruik (Liter)",
                    min_value=10,
                    max_value=500,
                    value=int(boiler_config.get('daily_hot_water_usage', 120)),
                    step=10
                )
                
                water_temp_rise = st.number_input(
                    "Temperatuurstijging (°C)",
                    min_value=10,
                    max_value=70,
                    value=int(boiler_config.get('water_temperature_rise', 35)),
                    step=5
                )
                
                gas_energy_content = st.number_input(
                    "Energie-inhoud gas (kWh/m³)",
                    min_value=8.0,
                    max_value=12.0,
                    value=float(boiler_config.get('gas_energy_content', 9.77)),
                    step=0.1
                )
                
                save_boiler = st.form_submit_button("Opslaan")
            
            if save_boiler:
                # Update boiler config
                config_manager.update_section('boiler', {
                    'capacity': boiler_capacity,
                    'efficiency': boiler_efficiency,
                    'daily_hot_water_usage': daily_hot_water,
                    'water_temperature_rise': water_temp_rise,
                    'gas_energy_content': gas_energy_content
                })
                st.success("Warmwaterboiler parameters opgeslagen!")
        
        # Battery parameters
        with mod_tab2:
            # Get current battery config
            battery_config = config_manager.get_config('battery')
            
            # Create form for battery parameters
            with st.form("battery_form"):
                battery_capacity = st.number_input(
                    "Accu capaciteit (kWh)",
                    min_value=1.0,
                    max_value=50.0,
                    value=float(battery_config.get('capacity', 10.0)),
                    step=0.5
                )
                
                battery_efficiency = st.slider(
                    "Accu efficiëntie (%)",
                    min_value=50,
                    max_value=100,
                    value=int(battery_config.get('efficiency', 0.9) * 100),
                    step=5
                ) / 100
                
                max_charge_rate = st.number_input(
                    "Max laadvermogen (kW)",
                    min_value=1.0,
                    max_value=20.0,
                    value=float(battery_config.get('max_charge_rate', 3.6)),
                    step=0.1
                )
                
                max_discharge_rate = st.number_input(
                    "Max ontlaadvermogen (kW)",
                    min_value=1.0,
                    max_value=20.0,
                    value=float(battery_config.get('max_discharge_rate', 3.6)),
                    step=0.1
                )
                
                min_soc = st.slider(
                    "Minimaal laadniveau (%)",
                    min_value=0,
                    max_value=50,
                    value=int(battery_config.get('min_soc', 10)),
                    step=5
                )
                
                max_soc = st.slider(
                    "Maximaal laadniveau (%)",
                    min_value=50,
                    max_value=100,
                    value=int(battery_config.get('max_soc', 90)),
                    step=5
                )
                
                save_battery = st.form_submit_button("Opslaan")
            
            if save_battery:
                # Update battery config
                config_manager.update_section('battery', {
                    'capacity': battery_capacity,
                    'efficiency': battery_efficiency,
                    'max_charge_rate': max_charge_rate,
                    'max_discharge_rate': max_discharge_rate,
                    'min_soc': min_soc,
                    'max_soc': max_soc
                })
                st.success("Accu parameters opgeslagen!")
    
    # Backup/import tab
    with tab3:
        st.subheader("Configuratie opslag/herstel")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Configuratie exporteren")
            st.write("Download de huidige configuratie als JSON-bestand:")
            
            # Export config button
            if st.button("Configuratie exporteren"):
                config_json = config_manager.export_config_json()
                
                # Create download link
                b64_config = base64.b64encode(config_json.encode()).decode()
                current_date = datetime.datetime.now().strftime("%Y%m%d")
                download_filename = f"zonnepanelen_config_{current_date}.json"
                
                href = f'<a href="data:application/json;base64,{b64_config}" download="{download_filename}">Klik hier om het bestand te downloaden</a>'
                st.markdown(href, unsafe_allow_html=True)
        
        with col2:
            st.markdown("### Configuratie importeren")
            st.write("Upload een eerder geëxporteerd configuratiebestand:")
            
            # Import config uploader
            uploaded_config = st.file_uploader("Selecteer configuratiebestand", type="json")
            
            if uploaded_config:
                if st.button("Configuratie importeren"):
                    try:
                        config_content = uploaded_config.read().decode()
                        success = config_manager.import_config_json(config_content)
                        
                        if success:
                            st.success("Configuratie succesvol geïmporteerd!")
                        else:
                            st.error("Er is een fout opgetreden bij het importeren van de configuratie.")
                    except Exception as e:
                        st.error(f"Fout bij het importeren: {str(e)}")
        
        # Reset config
        st.markdown("### Configuratie resetten")
        st.write("Reset alle instellingen naar de standaardwaarden:")
        
        if st.button("Reset configuratie", type="primary"):
            # Confirm reset
            confirmation = st.checkbox("Ik begrijp dat alle huidige instellingen verloren gaan")
            
            if confirmation:
                config_manager.reset_config()
                st.success("Configuratie gereset naar standaardwaarden!")
                st.experimental_rerun()


if __name__ == "__main__":
    main()
