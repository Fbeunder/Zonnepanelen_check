"""
Configuration page module for the Zonnepanelen_check application.

This module contains the configuration page functionality.
"""
import streamlit as st
import datetime
import base64


def show_configuration_page(config_manager):
    """
    Display the configuration page.
    
    Args:
        config_manager: Instance of ConfigManager
    """
    st.header("Configuratie")
    
    tab1, tab2, tab3 = st.tabs(["Economische parameters", "Technische parameters", "Opslag/Backup"])
    
    # Economic parameters tab
    with tab1:
        st.subheader("Economische Parameters")
        
        # Get current economic config
        economic_config = config_manager.get_section('economic')
        
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
            boiler_config = config_manager.get_section('boiler')
            
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
            battery_config = config_manager.get_section('battery')
            
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
                config_manager.reset_to_defaults()
                st.success("Configuratie gereset naar standaardwaarden!")
                st.rerun()