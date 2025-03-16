"""
Home page module for the Zonnepanelen_check application.

This module contains the home page content with application overview.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go


def show_home_page():
    """
    Display the home page with application overview.
    """
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