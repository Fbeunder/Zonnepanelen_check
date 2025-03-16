"""
Boiler page module for the Zonnepanelen_check application.

This module contains the water boiler analysis page functionality.
"""
import streamlit as st
import sys
import pathlib
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# Voeg de root directory toe aan het pad voor juiste imports
sys.path.append(str(pathlib.Path(__file__).parent.parent))
from boiler_module import BoilerCalculator
import visualization as viz
from components.data_display import show_storage_results
import utils.ui_helpers as ui_helpers


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
    
    # Create tabs for different sections
    tabs = st.tabs(["Instellingen & Resultaten", "Geavanceerde Instellingen", "Uitleg"])
    
    # Get boiler configuration
    boiler_config = config_manager.get_section('boiler')
    economic_config = config_manager.get_section('economic')
    
    # Basic settings tab
    with tabs[0]:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Boiler Basisinstellingen")
            
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
    
    # Advanced settings tab
    with tabs[1]:
        st.subheader("Geavanceerde Boiler Instellingen")
        
        col1, col2 = st.columns(2)
        
        with col1:
            cold_water_temp = st.number_input(
                "Temperatuur koud water (°C)",
                min_value=0,
                max_value=25,
                value=float(boiler_config.get('cold_water_temp', 10.0)),
                step=1.0,
                help="Gemiddelde temperatuur van inkomend koud water"
            )
            
            standby_loss = st.number_input(
                "Dagelijks warmteverlies (%)",
                min_value=0.0,
                max_value=10.0,
                value=float(boiler_config.get('standby_loss_percent', 0.5)),
                step=0.1,
                help="Percentage warmteverlies van de boiler per dag"
            )
            
            gas_energy_content = st.number_input(
                "Energie-inhoud gas (kWh/m³)",
                min_value=8.0,
                max_value=12.0,
                value=float(boiler_config.get('gas_energy_content', 9.77)),
                step=0.01,
                help="Energie-inhoud van aardgas in kWh per kubieke meter"
            )
        
        with col2:
            st.write("Warmwaterverbruik Profiel")
            st.write("Verdeel het dagelijkse warmwaterverbruik over de dag (percentages, totaal moet 100% zijn)")
            
            # Get default or saved profile
            default_profile = BoilerCalculator(pd.DataFrame(), {})._default_usage_profile()
            saved_profile = boiler_config.get('hourly_usage_profile', default_profile)
            
            # Convert to sorted list of tuples for UI
            profile_items = sorted(saved_profile.items())
            
            # UI for adjusting hourly profile
            hours = []
            percentages = []
            col_a, col_b = st.columns(2)
            
            with col_a:
                # Morning/Afternoon hours
                for hour, percentage in [item for item in profile_items if item[0] < 12]:
                    hours.append(hour)
                    percentages.append(
                        st.slider(
                            f"{hour}:00 - {hour+1}:00", 
                            0.0, 
                            40.0, 
                            float(percentage * 100),
                            1.0,
                            format="%.0f%%"
                        ) / 100
                    )
            
            with col_b:
                # Evening/Night hours
                for hour, percentage in [item for item in profile_items if item[0] >= 12]:
                    hours.append(hour)
                    percentages.append(
                        st.slider(
                            f"{hour}:00 - {hour+1}:00", 
                            0.0, 
                            40.0, 
                            float(percentage * 100),
                            1.0,
                            format="%.0f%%"
                        ) / 100
                    )
            
            # Calculate total and normalize if needed
            total_percentage = sum(percentages) * 100
            st.write(f"Totaal: {total_percentage:.1f}% (zou 100% moeten zijn)")
            
            if abs(total_percentage - 100) > 1:
                st.warning("Het totale percentage wijkt af van 100%. De waarden worden automatisch genormaliseerd.")
                if total_percentage > 0:
                    percentages = [p / (total_percentage / 100) for p in percentages]
            
            # Store profile in configuration
            hourly_profile = dict(zip(hours, percentages))
            
            # Update advanced configuration
            config_manager.update_section('boiler', {
                'cold_water_temp': cold_water_temp,
                'standby_loss_percent': standby_loss,
                'gas_energy_content': gas_energy_content,
                'hourly_usage_profile': hourly_profile
            })
            
            # Show profile chart
            fig = px.bar(
                x=[f"{h}:00" for h in hours], 
                y=[p * 100 for p in percentages],
                labels={"x": "Uur van de dag", "y": "Percentage (%)"},
                title="Warmwaterverbruik Profiel"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Explanation tab
    with tabs[2]:
        st.subheader("Gedetailleerde Uitleg Warmwaterboiler Berekeningen")
        
        st.markdown("""
        ### Hoe werkt de Warmwaterboiler Module?
        
        De boiler module simuleert een warmwaterboiler die overtollige zonne-energie gebruikt om water te verwarmen.
        Dit is een effectieve manier om overtollige energie op te slaan in de vorm van warm water, wat anders
        aan het net zou worden teruggeleverd.
        
        ### Simulatie Aanpak
        
        De module simuleert de volgende aspecten:
        
        1. **Warmwaterverbruik volgens dagelijks patroon**: Het warmwaterverbruik is verdeeld over de dag
           volgens een instelbaar profiel. Standaard is dit geconcentreerd rond ochtend- en avondtijden.
        
        2. **Warmteverlies**: De boiler verliest warmte aan de omgeving, wat wordt berekend op basis
           van het ingestelde dagelijkse warmteverliespercentage.
        
        3. **Temperatuurberekening**: De module berekent de watertemperatuur in de boiler op basis
           van energietoevoer, -afname en -verlies.
        
        4. **Energiebuffer**: Overtollige zonne-energie wordt gebruikt om de watertemperatuur te verhogen,
           waardoor een energiebuffer ontstaat.
        
        ### Formules en Berekeningen
        
        De volgende formules worden gebruikt:
        
        - **Benodigde energie voor waterverwarming**:  
          Energie (kWh) = Volume (L) × Soortelijke warmte water (0.00116 kWh/L/°C) × Temperatuursstijging (°C) / Efficiëntie
        
        - **Warmteverlies**:  
          Verlies (kWh) = Opgeslagen energie (kWh) × Dagelijks verliespercentage / 24 × Tijdsinterval (uur)
        
        - **Gasbesparing**:  
          Gasbesparing (m³) = Gebruikte energie (kWh) / Energie-inhoud gas (kWh/m³)
        
        - **Financiële besparing**:  
          Besparing (€) = Gasbesparing (m³) × Gasprijs (€/m³)
        
        ### Hoe het te gebruiken
        
        1. Stel de basisconfiguratie in op basis van uw boiler en warmwaterverbruik
        2. Pas indien gewenst de geavanceerde instellingen aan
        3. Klik op "Berekenen" om de analyse uit te voeren
        4. Bekijk de resultaten in de grafieken en overzichten
        
        ### Interpretatie van de Resultaten
        
        - **Gasbesparing**: Dit is de hoeveelheid gas die u bespaart door zonne-energie te gebruiken voor waterverwarming
        - **Financiële besparing**: De geldelijke besparing op basis van de huidige gasprijs
        - **Benuttingspercentage**: Percentage van het totale surplus dat wordt gebruikt voor waterverwarming
        - **Verwarmingsefficiëntie**: Percentage van de verwarmingsbehoefte dat wordt gedekt door zonne-energie
        
        De grafieken tonen gedetailleerde informatie over het energieverbruik, de temperatuurveranderingen en de gasbesparingen.
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
                st.subheader("Resultaten")
                
                # Display key metrics in multiple columns
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Totale Gasbesparing", f"{results['total_gas_saved_m3']:.2f} m³")
                    st.metric("Benuttingspercentage", f"{results['surplus_utilization_percent']:.1f}%", 
                             help="Percentage van het totale surplus dat wordt gebruikt voor waterverwarming")
                
                with col2:
                    st.metric("Financiële Besparing", utils.format_currency(results['total_financial_savings']))
                    st.metric("Verwarmingsefficiëntie", f"{results['heating_efficiency_percent']:.1f}%",
                             help="Percentage van de verwarmingsbehoefte dat wordt gedekt door zonne-energie")
                
                with col3:
                    st.metric("Jaarlijkse Gasbesparing (proj.)", f"{results['annual_projection']['gas_saved_m3']:.2f} m³")
                    st.metric("Jaarlijkse Financiële Besparing", 
                             utils.format_currency(results['annual_projection']['financial_savings']))
                
                # More detailed results
                with st.expander("Gedetailleerde Resultaten", expanded=False):
                    show_storage_results('boiler', results)
                
                # Results tabs
                result_tabs = st.tabs(["Dagelijkse Analyse", "Maandelijkse Analyse", "Simulatiegegevens"])
                
                # Daily results tab
                with result_tabs[0]:
                    st.subheader("Dagelijkse Gasbesparing")
                    
                    # Create daily gas savings chart
                    if 'daily_agg' in results:
                        daily_df = results['daily_agg']
                        
                        # Create figure
                        fig = go.Figure()
                        
                        # Add gas needed trace
                        fig.add_trace(go.Bar(
                            x=daily_df['period'],
                            y=daily_df['gas_needed_m3'],
                            name='Gas Nodig (zonder zonne-energie)',
                            marker_color='rgba(220, 220, 220, 0.7)'
                        ))
                        
                        # Add gas saved trace
                        fig.add_trace(go.Bar(
                            x=daily_df['period'],
                            y=daily_df['gas_saved_m3'],
                            name='Gas Bespaard (met zonne-energie)',
                            marker_color='rgba(50, 171, 96, 0.7)'
                        ))
                        
                        # Customize layout
                        fig.update_layout(
                            title='Dagelijkse Gasbesparing',
                            xaxis_title='Datum',
                            yaxis_title='Gas (m³)',
                            template='plotly_white',
                            barmode='overlay',
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            )
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Add heating coverage chart
                        st.subheader("Dagelijkse Zonne-aandeel in Waterverwarming")
                        
                        # Create heating coverage figure
                        fig2 = go.Figure()
                        
                        # Add energy needed trace
                        fig2.add_trace(go.Bar(
                            x=daily_df['period'],
                            y=daily_df['energy_needed_kwh'],
                            name='Totale Energiebehoefte',
                            marker_color='rgba(220, 220, 220, 0.7)'
                        ))
                        
                        # Add energy used from solar trace
                        fig2.add_trace(go.Bar(
                            x=daily_df['period'],
                            y=daily_df['energy_used_kwh'],
                            name='Gebruikt van Zonne-energie',
                            marker_color='rgba(50, 171, 96, 0.7)'
                        ))
                        
                        # Add coverage percentage line
                        fig2.add_trace(go.Scatter(
                            x=daily_df['period'],
                            y=daily_df['heating_coverage'],
                            name='Dekkingspercentage',
                            line=dict(color='rgba(219, 64, 82, 1)', width=2),
                            yaxis="y2"
                        ))
                        
                        # Customize layout
                        fig2.update_layout(
                            title='Dagelijkse Dekking Warmwaterbehoefte door Zonne-energie',
                            xaxis_title='Datum',
                            yaxis_title='Energie (kWh)',
                            yaxis2=dict(
                                title='Dekking (%)',
                                titlefont=dict(color='rgba(219, 64, 82, 1)'),
                                tickfont=dict(color='rgba(219, 64, 82, 1)'),
                                overlaying='y',
                                side='right',
                                range=[0, 100]
                            ),
                            template='plotly_white',
                            barmode='overlay',
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            )
                        )
                        
                        st.plotly_chart(fig2, use_container_width=True)
                
                # Monthly results tab
                with result_tabs[1]:
                    st.subheader("Maandelijkse Analyse")
                    
                    if 'monthly_agg' in results:
                        monthly_df = results['monthly_agg']
                        
                        # Create figure
                        fig = go.Figure()
                        
                        # Add financial savings trace
                        fig.add_trace(go.Bar(
                            x=monthly_df['period'],
                            y=monthly_df['financial_savings'],
                            name='Financiële Besparing (€)',
                            marker_color='rgba(50, 171, 96, 0.7)'
                        ))
                        
                        # Add utilization percentage line
                        fig.add_trace(go.Scatter(
                            x=monthly_df['period'],
                            y=monthly_df['surplus_utilization'],
                            name='Benuttingspercentage',
                            line=dict(color='rgba(219, 64, 82, 1)', width=2),
                            yaxis="y2"
                        ))
                        
                        # Customize layout
                        fig.update_layout(
                            title='Maandelijkse Financiële Besparing en Benuttingspercentage',
                            xaxis_title='Maand',
                            yaxis_title='Besparing (€)',
                            yaxis2=dict(
                                title='Benutting (%)',
                                titlefont=dict(color='rgba(219, 64, 82, 1)'),
                                tickfont=dict(color='rgba(219, 64, 82, 1)'),
                                overlaying='y',
                                side='right',
                                range=[0, 100]
                            ),
                            template='plotly_white',
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            )
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Add monthly gas savings chart
                        st.subheader("Maandelijkse Gasbesparing")
                        fig2 = go.Figure()
                        
                        # Add gas saved trace
                        fig2.add_trace(go.Bar(
                            x=monthly_df['period'],
                            y=monthly_df['gas_saved_m3'],
                            name='Gas Bespaard (m³)',
                            marker_color='rgba(50, 171, 96, 0.7)'
                        ))
                        
                        # Add heating coverage line
                        fig2.add_trace(go.Scatter(
                            x=monthly_df['period'],
                            y=monthly_df['heating_coverage'],
                            name='Verwarmingsdekking',
                            line=dict(color='rgba(219, 64, 82, 1)', width=2),
                            yaxis="y2"
                        ))
                        
                        # Customize layout
                        fig2.update_layout(
                            title='Maandelijkse Gasbesparing en Verwarmingsdekking',
                            xaxis_title='Maand',
                            yaxis_title='Gas (m³)',
                            yaxis2=dict(
                                title='Dekking (%)',
                                titlefont=dict(color='rgba(219, 64, 82, 1)'),
                                tickfont=dict(color='rgba(219, 64, 82, 1)'),
                                overlaying='y',
                                side='right',
                                range=[0, 100]
                            ),
                            template='plotly_white',
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            )
                        )
                        
                        st.plotly_chart(fig2, use_container_width=True)
                
                # Simulation data tab
                with result_tabs[2]:
                    st.subheader("Simulatiegegevens")
                    
                    # Explanation of the simulation
                    st.markdown("""
                    De onderstaande grafiek toont een voorbeeld van de simulatiegegevens voor een representatieve dag.
                    Hierin kunt u zien hoe de watertemperatuur en het energieverbruik variëren gedurende de dag.
                    """)
                    
                    if 'result_df' in results:
                        # Get a representative day from the data
                        all_df = results['result_df']
                        
                        # Convert to datetime if not already
                        if not pd.api.types.is_datetime64_dtype(all_df['timestamp']):
                            all_df['timestamp'] = pd.to_datetime(all_df['timestamp'])
                            
                        # Find a day with significant solar surplus
                        daily_surplus = all_df.groupby(all_df['timestamp'].dt.date)['surplus_energy_kwh'].sum()
                        if len(daily_surplus) > 0:
                            # Get a day with high surplus (in top 25%)
                            top_days = daily_surplus.sort_values(ascending=False).head(max(1, len(daily_surplus) // 4))
                            sample_date = top_days.index[min(3, len(top_days) - 1)]
                            
                            # Filter for the sample date
                            sample_df = all_df[all_df['timestamp'].dt.date == sample_date].copy()
                            
                            # Create detail plot
                            st.subheader(f"Gedetailleerde Simulatie voor {sample_date}")
                            
                            # Create figure with secondary y-axis
                            fig = go.Figure()
                            
                            # Add water temperature
                            fig.add_trace(go.Scatter(
                                x=sample_df['timestamp'],
                                y=sample_df['water_temp'],
                                name='Watertemperatuur (°C)',
                                line=dict(color='rgba(31, 119, 180, 1)', width=2)
                            ))
                            
                            # Add surplus energy
                            fig.add_trace(go.Bar(
                                x=sample_df['timestamp'],
                                y=sample_df['surplus_energy_kwh'],
                                name='Surplus Energie (kWh)',
                                marker_color='rgba(50, 171, 96, 0.7)',
                                yaxis="y2"
                            ))
                            
                            # Add used energy
                            fig.add_trace(go.Bar(
                                x=sample_df['timestamp'],
                                y=sample_df['energy_used_kwh'],
                                name='Gebruikte Energie (kWh)',
                                marker_color='rgba(219, 64, 82, 0.7)',
                                yaxis="y2"
                            ))
                            
                            # Add hot water demand
                            fig.add_trace(go.Scatter(
                                x=sample_df['timestamp'],
                                y=sample_df['hot_water_demand_l'],
                                name='Warmwaterverbruik (L)',
                                line=dict(color='rgba(148, 103, 189, 1)', width=2, dash='dot'),
                                yaxis="y3"
                            ))
                            
                            # Customize layout
                            fig.update_layout(
                                title=f'Boiler Simulatie voor {sample_date}',
                                xaxis_title='Tijd',
                                yaxis=dict(
                                    title='Temperatuur (°C)',
                                    titlefont=dict(color='rgba(31, 119, 180, 1)'),
                                    tickfont=dict(color='rgba(31, 119, 180, 1)')
                                ),
                                yaxis2=dict(
                                    title='Energie (kWh)',
                                    titlefont=dict(color='rgba(50, 171, 96, 1)'),
                                    tickfont=dict(color='rgba(50, 171, 96, 1)'),
                                    overlaying='y',
                                    side='right'
                                ),
                                yaxis3=dict(
                                    title='Water (L)',
                                    titlefont=dict(color='rgba(148, 103, 189, 1)'),
                                    tickfont=dict(color='rgba(148, 103, 189, 1)'),
                                    overlaying='y',
                                    anchor='free',
                                    side='right',
                                    position=0.95
                                ),
                                template='plotly_white',
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=1.02,
                                    xanchor="right",
                                    x=1
                                )
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            st.markdown("""
                            **Uitleg van de grafiek:**
                            
                            - **Watertemperatuur (°C)**: Toont de gesimuleerde temperatuur van het water in de boiler.
                            - **Surplus Energie (kWh)**: De beschikbare overtollige zonne-energie.
                            - **Gebruikte Energie (kWh)**: Hoeveel van de surplus energie daadwerkelijk is gebruikt voor waterverwarming.
                            - **Warmwaterverbruik (L)**: Het warmwaterverbruik volgens het ingestelde profiel.
                            
                            De temperatuur daalt wanneer warm water wordt gebruikt of door warmteverlies, en stijgt wanneer surplus energie wordt gebruikt voor verwarming.
                            """)
                
                # Export options
                st.subheader("Exporteren")
                export_cols = st.columns(3)
                
                with export_cols[0]:
                    # Download CSV button
                    if st.button("Exporteer Resultaten als CSV"):
                        if 'result_df' in results:
                            csv = results['result_df'].to_csv(index=False)
                            ui_helpers.download_link(csv, "boiler_resultaten.csv", "Klik hier om de CSV te downloaden")
                
                with export_cols[1]:
                    # Download daily results
                    if st.button("Exporteer Dagelijks Overzicht"):
                        if 'daily_agg' in results:
                            csv = results['daily_agg'].to_csv(index=False)
                            ui_helpers.download_link(csv, "boiler_dagelijks.csv", "Klik hier om de CSV te downloaden")
                
                with export_cols[2]:
                    # Download monthly results
                    if st.button("Exporteer Maandelijks Overzicht"):
                        if 'monthly_agg' in results:
                            csv = results['monthly_agg'].to_csv(index=False)
                            ui_helpers.download_link(csv, "boiler_maandelijks.csv", "Klik hier om de CSV te downloaden")
