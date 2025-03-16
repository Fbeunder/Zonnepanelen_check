"""
Main application module for the Zonnepanelen_check application.

This module contains the Streamlit application that provides the user interface
for analyzing solar panel surplus energy storage options.

The application is structured in modules:
- app_pages/: Contains the individual page implementations
- components/: Contains reusable UI components
- utils/: Contains utility functions
"""
import streamlit as st

# Import application modules
from data_processor import DataProcessor
from config_manager import ConfigManager
import utils

# Import page modules
from app_pages.home import show_home_page
from app_pages.data_upload import show_data_upload_page
from app_pages.boiler import show_boiler_page
from app_pages.battery import show_battery_page
from app_pages.visualization import show_visualization_page
from app_pages.configuration import show_configuration_page

# Import components
from components.sidebar import show_sidebar


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
    show_sidebar(data_processor)
    
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


if __name__ == "__main__":
    main()
