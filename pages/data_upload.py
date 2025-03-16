"""
Data Upload page module for the Zonnepanelen_check application.

This module contains the data upload page functionality.
"""
import streamlit as st
import os
import tempfile
import pathlib
from components.data_display import show_data_metrics, show_energy_chart
import visualization as viz


def show_data_upload_page(data_processor, config_manager):
    """
    Display the data upload page.
    
    Args:
        data_processor: Instance of DataProcessor
        config_manager: Instance of ConfigManager
    """
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
                        pathlib.Path(__file__).parent.parent, 
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
        show_data_metrics(data_processor.get_data_summary())
        
        # Show data table
        st.subheader("Geïmporteerde data")
        st.dataframe(data_processor.data.head(100), use_container_width=True)
        
        # Show production & consumption chart
        st.subheader("Productie & Verbruik (Dagelijks)")
        if data_processor.daily_data is not None:
            fig = viz.plot_energy_production_consumption(data_processor.data, period='daily')
            st.plotly_chart(fig, use_container_width=True)