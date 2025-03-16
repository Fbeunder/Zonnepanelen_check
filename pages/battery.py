"""
Battery page module for the Zonnepanelen_check application.

This module contains the battery analysis page functionality.
"""
import streamlit as st
import sys
import pathlib

# Voeg de root directory toe aan het pad voor juiste imports
sys.path.append(str(pathlib.Path(__file__).parent.parent))
from battery_module import BatteryCalculator
import visualization as viz
from components.data_display import show_storage_results


def show_battery_page(data_processor, config_manager):
    """
    Display the battery analysis page.
    
    Args:
        data_processor: Instance of DataProcessor
        config_manager: Instance of ConfigManager
    """
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
        battery_config = config_manager.get_section('battery')
        economic_config = config_manager.get_section('economic')
        
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
                    'battery': config_manager.get_section('battery'),
                    'economic': config_manager.get_section('economic')
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
                show_storage_results('battery', results)
                
                # Show battery state chart
                st.subheader("Accu Laadtoestand en Energiestromen")
                fig = viz.plot_battery_state(results)
                st.plotly_chart(fig, use_container_width=True)