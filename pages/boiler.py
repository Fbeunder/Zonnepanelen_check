"""
Boiler page module for the Zonnepanelen_check application.

This module contains the water boiler analysis page functionality.
"""
import streamlit as st
from boiler_module import BoilerCalculator
import visualization as viz
from components.data_display import show_storage_results


def show_boiler_page(data_processor, config_manager):
    """
    Display the water boiler analysis page.
    
    Args:
        data_processor: Instance of DataProcessor
        config_manager: Instance of ConfigManager
    """
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
        boiler_config = config_manager.get_section('boiler')
        economic_config = config_manager.get_section('economic')
        
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
                    'boiler': config_manager.get_section('boiler'),
                    'economic': config_manager.get_section('economic')
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
                show_storage_results('boiler', results)
                
                # Show boiler energy usage chart
                st.subheader("Boiler Energiegebruik en Gasbesparing")
                fig = viz.plot_boiler_energy_usage(results)
                st.plotly_chart(fig, use_container_width=True)