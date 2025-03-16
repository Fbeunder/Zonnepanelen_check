"""
Sidebar component for the Zonnepanelen_check application.

This module handles the sidebar navigation and data status display.
"""
import streamlit as st


def show_sidebar(data_processor=None):
    """
    Display the sidebar with navigation and data status.
    
    Args:
        data_processor: Instance of DataProcessor containing the data
    """
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
                st.rerun()
        
        # Show data status if data_processor is provided
        if data_processor and data_processor.data is not None:
            st.success("✓ Data geladen")
            
            # Display file info
            file_info = data_processor.get_file_info()
            if file_info:
                with st.expander("Gegevens bestand"):
                    st.write(f"Bestand: {file_info.get('file_name', 'Onbekend')}")
                    st.write(f"Datapunten: {file_info.get('record_count', 0):,}")
                    st.write(f"Interval: {file_info.get('time_interval_minutes', 0)} minuten")
                    st.write(f"Periode: {file_info.get('first_record', '')} - {file_info.get('last_record', '')}")
        elif data_processor:
            st.info("Geen data geladen")