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
from typing import Dict, List, Tuple, Union, Optional, Any

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
    
    # Application title
    st.title("Zonnepanelen Check")
    st.subheader("Analyse van opslag-opties voor overschot zonne-energie")
    
    # Initialize components
    config_manager = ConfigManager()
    data_processor = DataProcessor()
    
    # Show sidebar for data input and settings
    with st.sidebar:
        st.header("Data & Instellingen")
        
        # File uploader
        st.subheader("CSV Data")
        uploaded_file = st.file_uploader(
            "Upload CSV bestand met productie- en verbruiksgegevens",
            type="csv"
        )
        
        # Use example data button
        use_example = st.checkbox("Voorbeeld data gebruiken")
        
        # Load data section
        process_data = st.button("Data inladen")
        
        # Settings sections
        st.subheader("Economische parameters")
        
        economic_config = config_manager.get_config('economic')
        electricity_price = st.number_input(
            "Stroomprijs (€/kWh)",
            min_value=0.01,
            max_value=1.0,
            value=float(economic_config.get('electricity_price', 0.22)),
            step=0.01
        )
        
        gas_price = st.number_input(
            "Gasprijs (€/m³)",
            min_value=0.01,
            max_value=5.0,
            value=float(economic_config.get('gas_price', 0.80)),
            step=0.01
        )
        
        feed_in_tariff = st.number_input(
            "Terugleveringstarief (€/kWh)",
            min_value=0.0,
            max_value=1.0,
            value=float(economic_config.get('feed_in_tariff', 0.09)),
            step=0.01
        )
        
        # Update economic config
        config_manager.update_section('economic', {
            'electricity_price': electricity_price,
            'gas_price': gas_price,
            'feed_in_tariff': feed_in_tariff
        })
        
        # Boiler settings
        st.subheader("Warmwaterboiler parameters")
        
        boiler_config = config_manager.get_config('boiler')
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
        
        # Update boiler config
        config_manager.update_section('boiler', {
            'capacity': boiler_capacity,
            'efficiency': boiler_efficiency,
            'daily_hot_water_usage': daily_hot_water
        })
        
        # Battery settings
        st.subheader("Accu parameters")
        
        battery_config = config_manager.get_config('battery')
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
        
        # Update battery config
        config_manager.update_section('battery', {
            'capacity': battery_capacity,
            'efficiency': battery_efficiency
        })
    
    # Process data when button is clicked
    if process_data:
        if uploaded_file:
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
                st.success("Data succesvol ingeladen!")
                # Update last used file in config
                config_manager.update_last_used_file(uploaded_file.name)
            else:
                st.error("Fout bij het inladen van de data. Controleer het CSV-bestand.")
                
        elif use_example:
            # TODO: Add example data loading
            st.info("Voorbeeld data wordt nog toegevoegd in een toekomstige versie.")
            # For now, we'll just set a flag to continue with the app
            st.session_state['data_loaded'] = True
        else:
            st.warning("Upload een CSV-bestand of gebruik de voorbeeld data.")
    
    # Main content area - show only when data is loaded
    if 'data_loaded' in st.session_state and st.session_state['data_loaded']:
        # Create tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs([
            "Overzicht", 
            "Warmwaterboiler", 
            "Accu", 
            "Vergelijking"
        ])
        
        # Overview tab
        with tab1:
            st.header("Overzicht Energiegegevens")
            
            # Placeholder for summary
            st.subheader("Samenvatting")
            
            # Placeholder for charts
            st.subheader("Grafieken")
            
            # Production & Consumption chart
            # st.plotly_chart(
            #     viz.plot_energy_production_consumption(data_processor.data, period='daily'),
            #     use_container_width=True
            # )
            
            # Surplus energy chart
            # st.plotly_chart(
            #     viz.plot_surplus_energy(data_processor.data, period='daily'),
            #     use_container_width=True
            # )
        
        # Boiler tab
        with tab2:
            st.header("Warmwaterboiler Analyse")
            
            # Placeholder for boiler results
            st.info("Implementatie van warmwaterboiler-berekeningen volgt. De basisstructuur is aanwezig.")
            
            # Example of what will be shown:
            st.subheader("Invoerparameters")
            st.write(f"- Boiler capaciteit: {boiler_capacity} Liter")
            st.write(f"- Boiler efficiëntie: {boiler_efficiency * 100:.0f}%")
            st.write(f"- Dagelijks warmwaterverbruik: {daily_hot_water} Liter")
            st.write(f"- Gasprijs: € {gas_price} per m³")
            
        
        # Battery tab
        with tab3:
            st.header("Accu Analyse")
            
            # Placeholder for battery results
            st.info("Implementatie van accu-berekeningen volgt. De basisstructuur is aanwezig.")
            
            # Example of what will be shown:
            st.subheader("Invoerparameters")
            st.write(f"- Accu capaciteit: {battery_capacity} kWh")
            st.write(f"- Accu efficiëntie: {battery_efficiency * 100:.0f}%")
            st.write(f"- Stroomprijs: € {electricity_price} per kWh")
            st.write(f"- Terugleveringstarief: € {feed_in_tariff} per kWh")
        
        # Comparison tab
        with tab4:
            st.header("Vergelijking Opslagopties")
            
            # Placeholder for comparison results
            st.info("De vergelijking tussen opslagopties wordt geïmplementeerd zodra de individuele modules zijn voltooid.")
    else:
        # Show intro text when no data is loaded
        st.info("""
        ## Welkom bij de Zonnepanelen Check!
        
        Deze applicatie helpt u bij het analyseren van mogelijke opties voor 
        het opslaan van overschot zonne-energie en berekent de potentiële besparingen.
        
        ### Aan de slag:
        1. Upload een CSV-bestand met uw energiegegevens in het zijmenu
        2. Pas de economische en technische parameters aan uw situatie aan
        3. Klik op "Data inladen" om de analyse te starten
        
        ### CSV-formaat:
        Uw CSV-bestand moet de volgende kolommen bevatten:
        - Date/Time: datum en tijd (formaat: dd/mm/yyyy HH:MM)
        - Energy Produced (Wh): geproduceerde energie in Watt-uur
        - Energy Consumed (Wh): verbruikte energie in Watt-uur
        - Exported to Grid (Wh): naar het net geëxporteerde energie (optioneel)
        - Imported from Grid (Wh): van het net geïmporteerde energie (optioneel)
        """)


if __name__ == "__main__":
    main()
