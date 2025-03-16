"""
Battery page module for the Zonnepanelen_check application.

This module contains the battery analysis page functionality.
"""
import streamlit as st
import sys
import pathlib
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Voeg de root directory toe aan het pad voor juiste imports
sys.path.append(str(pathlib.Path(__file__).parent.parent))
from battery_module import BatteryCalculator
import visualization as viz
from components.data_display import show_storage_results
import utils.ui_helpers as ui_helpers


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
    
    # Create tabs for different sections
    tabs = st.tabs(["Instellingen & Resultaten", "Geavanceerde Instellingen", "Uitleg"])
    
    # Get battery configuration
    battery_config = config_manager.get_section('battery')
    economic_config = config_manager.get_section('economic')
    
    # Basic settings tab
    with tabs[0]:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Accu Basisinstellingen")
            
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
                'max_discharge_rate': max_discharge_rate
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
            - **Stroomprijs**: Prijs per kWh voor inkoop van stroom
            - **Terugleveringstarief**: Vergoeding per kWh voor teruglevering aan het net
            """)
    
    # Advanced settings tab
    with tabs[1]:
        st.subheader("Geavanceerde Accu Instellingen")
        
        col1, col2 = st.columns(2)
        
        with col1:
            min_soc = st.slider(
                "Minimaal laadniveau (%)",
                min_value=0,
                max_value=50,
                value=int(battery_config.get('min_soc', 10)),
                step=5,
                help="Diepste ontlading van de accu (DoD). Hogere waarden verlengen de levensduur."
            )
            
            max_soc = st.slider(
                "Maximaal laadniveau (%)",
                min_value=50,
                max_value=100,
                value=int(battery_config.get('max_soc', 90)),
                step=5,
                help="Maximale laadtoestand. Sommige accu's worden beschermd door niet 100% te laden."
            )
            
            installation_cost = st.number_input(
                "Installatiekosten (€)",
                min_value=0,
                max_value=20000,
                value=int(battery_config.get('installation_cost', 5000)),
                step=100,
                help="Totale kosten van de accu inclusief installatie"
            )
            
            expected_lifetime = st.number_input(
                "Verwachte levensduur (jaren)",
                min_value=1,
                max_value=30,
                value=int(battery_config.get('expected_lifetime', 10)),
                step=1,
                help="Verwachte kalenderlevensduur van de accu"
            )
            
            expected_cycles = st.number_input(
                "Verwachte cycli",
                min_value=100,
                max_value=10000,
                value=int(battery_config.get('expected_cycles', 3650)),
                step=50,
                help="Verwacht aantal volledige laad/ontlaad cycli"
            )
            
            # Update advanced configuration
            config_manager.update_section('battery', {
                'min_soc': min_soc,
                'max_soc': max_soc,
                'installation_cost': installation_cost,
                'expected_lifetime': expected_lifetime,
                'expected_cycles': expected_cycles
            })
        
        with col2:
            st.write("#### Effectieve Capaciteit")
            usable_capacity = (battery_capacity * (max_soc - min_soc)) / 100
            usable_percent = (usable_capacity / battery_capacity) * 100
            
            st.info(f"""
            - Totale capaciteit: {battery_capacity:.1f} kWh
            - Bruikbare capaciteit: {usable_capacity:.1f} kWh ({usable_percent:.0f}%)
            - Minimale laadtoestand: {battery_capacity * min_soc / 100:.1f} kWh 
            - Maximale laadtoestand: {battery_capacity * max_soc / 100:.1f} kWh
            """)
            
            st.write("#### Terugverdientijd")
            # Simple ROI calculation
            annual_savings_estimate = 365 * usable_capacity * 0.5 * (electricity_price - feed_in_tariff)
            payback_years = installation_cost / annual_savings_estimate if annual_savings_estimate > 0 else float('inf')
            roi_percent = (annual_savings_estimate / installation_cost) * 100 if installation_cost > 0 else 0
            
            st.info(f"""
            Geschatte terugverdientijd: {payback_years:.1f} jaar
            Geschat rendement op investering: {roi_percent:.1f}% per jaar
            
            *Dit is een ruwe schatting. De werkelijke terugverdientijd hangt af van uw specifieke
            verbruiks- en productiepatroon.*
            """)
            
            st.write("#### Degradatie")
            daily_cycles_estimate = 0.8  # Assuming 0.8 cycles per day on average
            years_to_cycles = expected_cycles / (daily_cycles_estimate * 365)
            
            st.info(f"""
            - Verwachte levensduur op basis van jaren: {expected_lifetime} jaar
            - Verwachte levensduur op basis van cycli: {years_to_cycles:.1f} jaar
            - Beperkende factor: {"Cycli" if years_to_cycles < expected_lifetime else "Kalenderleeftijd"}
            
            *Na het bereiken van de levensduur zal de capaciteit afnemen tot ongeveer 70-80% van de oorspronkelijke capaciteit.*
            """)
    
    # Explanation tab
    with tabs[2]:
        st.subheader("Gedetailleerde Uitleg Accu Berekeningen")
        
        st.markdown("""
        ### Hoe werkt de Accu Module?
        
        De accu module simuleert een thuisbatterij die surplus zonne-energie opslaat en
        deze later gebruikt wanneer de vraag hoger is dan de productie. Dit vermindert
        zowel de inkoop van stroom als de teruglevering aan het net.
        
        ### Simulatie Aanpak
        
        De module simuleert de volgende aspecten:
        
        1. **Laad- en ontlaadcycli**: De simulatie volgt nauwkeurig het oplaad- en ontlaadgedrag
           van de batterij op basis van de gedefinieerde capaciteit en vermogenslimieten.
        
        2. **Efficiëntieverlies**: Bij het laden gaat een deel van de energie verloren door warmteontwikkeling
           en andere inefficiënties. Dit wordt meegenomen in de berekeningen.
        
        3. **Maximale laad- en ontlaadsnelheid**: De simulatie respecteert de limieten van
           hoe snel de batterij kan worden opgeladen en ontladen.
        
        4. **Diepte van ontlading (DoD)**: De batterij wordt niet verder ontladen dan het
           ingestelde minimale laadniveau om de levensduur te verlengen.
        
        ### Financiële Berekeningen
        
        De financiële analyse bestaat uit twee hoofdcomponenten:
        
        1. **Besparingen op inkoop**: Wanneer opgeslagen zonne-energie wordt gebruikt in plaats van
           stroom in te kopen, wordt geld bespaard tegen het stroomtarief.
           
           Besparing inkoop = Ontladen energie (kWh) × Stroomprijs (€/kWh)
        
        2. **Verlies aan terugleveringsinkomsten**: Door energie op te slaan in plaats van terug te leveren,
           wordt minder verdiend aan teruglevering.
           
           Verlies teruglevering = Opgeladen energie (kWh) × Terugleveringstarief (€/kWh)
        
        3. **Netto financiële besparing**:
           
           Netto besparing = Besparing inkoop − Verlies teruglevering
        
        ### Terugverdientijd en ROI
        
        De terugverdientijd wordt berekend door de installatiekosten te delen door de jaarlijkse besparingen:
        
        Terugverdientijd (jaren) = Installatiekosten (€) / Jaarlijkse besparing (€/jaar)
        
        Het rendement op investering (ROI) wordt berekend als:
        
        ROI (%) = (Jaarlijkse besparing / Installatiekosten) × 100%
        
        ### Levensduur en Degradatie
        
        De levensduur van een accu wordt bepaald door twee factoren:
        
        1. **Kalenderlevensduur**: Hoe lang de accu meegaat in jaren, ongeacht gebruik
        2. **Cyclische levensduur**: Hoeveel volledige laad-ontlaad cycli de accu kan doorstaan
        
        De werkelijke levensduur is de kortste van deze twee. De module schat het aantal
        cycli per dag op basis van de simulatie en berekent wanneer de limiet wordt bereikt.
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
                st.subheader("Resultaten")
                
                # Display key metrics in multiple columns
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Financiële Besparing", utils.format_currency(results['total_savings_eur']))
                    st.metric("Opslagbenutting", f"{results['storage_utilization_percent']:.1f}%", 
                             help="Percentage van het totale surplus dat werd opgeslagen in de accu")
                
                with col2:
                    st.metric("Terugverdientijd", f"{results['roi_metrics']['payback_years']:.1f} jaar")
                    st.metric("Zelfconsumptie met Accu", f"{results['self_consumption_with_battery_percent']:.1f}%",
                             help="Percentage van het verbruik dat wordt gedekt door zonnepanelen + accu")
                
                with col3:
                    st.metric("Jaarlijkse Besparing (proj.)", 
                             utils.format_currency(results['annual_projection']['financial_savings_eur']))
                    st.metric("Aantal Cycli", f"{results['cycle_count']:.1f}")
                
                # More detailed results
                with st.expander("Gedetailleerde Resultaten", expanded=False):
                    show_storage_results('battery', results)
                
                # Results tabs
                result_tabs = st.tabs(["Dagelijkse Analyse", "Maandelijkse Analyse", "Simulatiegegevens"])
                
                # Daily results tab
                with result_tabs[0]:
                    st.subheader("Dagelijkse Energiestromen en Besparingen")
                    
                    # Create daily energy flows chart
                    if 'daily_agg' in results:
                        # Daily energy flows
                        fig1 = viz.plot_battery_daily_flows(results)
                        st.plotly_chart(fig1, use_container_width=True)
                        
                        # Daily grid impact
                        st.subheader("Dagelijkse Netinteractie")
                        fig2 = viz.plot_battery_grid_impact(results)
                        st.plotly_chart(fig2, use_container_width=True)
                
                # Monthly results tab
                with result_tabs[1]:
                    st.subheader("Maandelijkse Analyse")
                    
                    if 'monthly_agg' in results:
                        # Monthly performance
                        fig = viz.plot_battery_monthly_performance(results)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Display monthly aggregated data
                        st.subheader("Maandelijks Overzicht")
                        monthly_df = results['monthly_agg'].copy()
                        
                        # Format columns for display
                        monthly_df['Maand'] = monthly_df['period'].dt.strftime('%Y-%m')
                        monthly_df['Opgeladen (kWh)'] = monthly_df['charged_kwh'].round(1)
                        monthly_df['Ontladen (kWh)'] = monthly_df['discharged_kwh'].round(1)
                        monthly_df['Besparing (€)'] = monthly_df['total_savings_eur'].round(2)
                        monthly_df['Opslagbenutting (%)'] = monthly_df['storage_utilization'].round(1)
                        
                        # Select and reorder columns
                        display_cols = ['Maand', 'Opgeladen (kWh)', 'Ontladen (kWh)', 
                                       'Besparing (€)', 'Opslagbenutting (%)']
                        st.dataframe(monthly_df[display_cols], use_container_width=True)
                
                # Simulation data tab
                with result_tabs[2]:
                    st.subheader("Simulatiegegevens")
                    
                    # Explanation of the simulation
                    st.markdown("""
                    De onderstaande grafiek toont een voorbeeld van de simulatiegegevens voor een representatieve dag.
                    Hierin kunt u zien hoe de accu wordt opgeladen en ontladen gedurende de dag.
                    """)
                    
                    if 'result_df' in results:
                        # Get detailed simulation plot
                        fig = viz.plot_battery_simulation_detail(results)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.markdown("""
                        **Uitleg van de grafiek:**
                        
                        - **Batterij Laadtoestand (kWh)**: De hoeveelheid energie die op elk moment in de accu is opgeslagen.
                        - **Surplus Energie (kWh)**: De overtollige energie van de zonnepanelen die potentieel kan worden opgeslagen.
                        - **Opgeladen Energie (kWh)**: De energie die daadwerkelijk in de accu is opgeslagen.
                        - **Ontladen Energie (kWh)**: De energie die uit de accu is gebruikt.
                        
                        De accu wordt opgeladen wanneer er een surplus is en ontladen wanneer er meer verbruik dan productie is.
                        """)
                
                # Export options
                st.subheader("Exporteren")
                export_cols = st.columns(3)
                
                with export_cols[0]:
                    # Download CSV button
                    if st.button("Exporteer Resultaten als CSV"):
                        if 'result_df' in results:
                            csv = results['result_df'].to_csv(index=False)
                            ui_helpers.download_link(csv, "accu_resultaten.csv", "Klik hier om de CSV te downloaden")
                
                with export_cols[1]:
                    # Download daily results
                    if st.button("Exporteer Dagelijks Overzicht"):
                        if 'daily_agg' in results:
                            csv = results['daily_agg'].to_csv(index=False)
                            ui_helpers.download_link(csv, "accu_dagelijks.csv", "Klik hier om de CSV te downloaden")
                
                with export_cols[2]:
                    # Download monthly results
                    if st.button("Exporteer Maandelijks Overzicht"):
                        if 'monthly_agg' in results:
                            csv = results['monthly_agg'].to_csv(index=False)
                            ui_helpers.download_link(csv, "accu_maandelijks.csv", "Klik hier om de CSV te downloaden")
