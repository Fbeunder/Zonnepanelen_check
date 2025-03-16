"""
UI helper functions for Zonnepanelen_check application.

This module contains reusable UI utility functions that can be used across
the different pages of the application.
"""
import streamlit as st
import base64
import pandas as pd
import io


def create_download_link(data, filename, text="Download bestand"):
    """
    Create a download link for data (CSV, JSON, etc.)
    
    Args:
        data: Data to be downloaded (string or bytes)
        filename: Name of the file to be downloaded
        text: Text to display for the download link
        
    Returns:
        HTML code for the download link
    """
    if isinstance(data, pd.DataFrame):
        # Convert DataFrame to CSV
        data = data.to_csv(index=False).encode()
    elif not isinstance(data, bytes):
        # Convert string to bytes if not already bytes
        data = data.encode()
    
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{text}</a>'
    return href


def show_error_message(message):
    """
    Display a consistent error message with instructions.
    
    Args:
        message: Error message to display
    """
    st.error(f"Error: {message}")
    st.markdown("Probeer de volgende stappen:")
    st.markdown("1. Controleer de ingevoerde gegevens")
    st.markdown("2. Herlaad de pagina")
    st.markdown("3. Als het probleem aanhoudt, neem contact op met de ontwikkelaar")


def show_info_box(title, content):
    """
    Display a styled info box with a title and content.
    
    Args:
        title: Title of the info box
        content: Content of the info box (can be markdown)
    """
    st.markdown(f"""
    <div style="background-color:#e8f4f8; padding:10px; border-radius:5px; margin-bottom:10px">
        <h4 style="margin-top:0">{title}</h4>
        <div>{content}</div>
    </div>
    """, unsafe_allow_html=True)


def format_number(value, decimals=1, prefix="", suffix=""):
    """
    Format a number with thousand separators and fixed decimals.
    
    Args:
        value: The number to format
        decimals: Number of decimal places
        prefix: Prefix to add before the number (e.g., "€")
        suffix: Suffix to add after the number (e.g., " kWh")
        
    Returns:
        Formatted number as string
    """
    try:
        formatted = f"{prefix}{value:,.{decimals}f}{suffix}".replace(",", ".")
        # Replace the first dot with a comma for Dutch number format
        parts = formatted.split(".", 1)
        if len(parts) > 1:
            formatted = parts[0].replace(".", ",") + "." + parts[1]
        return formatted
    except (TypeError, ValueError):
        return f"{prefix}0{suffix}"
