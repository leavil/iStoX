import streamlit as st
import pandas as pd

def scrollable_table(df: pd.DataFrame, height: int = 300):
    """
    Muestra un dataframe con scroll vertical en Streamlit.
    """
    style = f"""
    <style>
    .scrollable-table {{
        height: {height}px;
        overflow-y: auto;
        border: 1px solid #ddd;
        padding: 10px;
        width: 100%;
        display: block;
    }}
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)

    # Convertimos el DataFrame a tabla HTML con la clase scrollable-table
    html_table = df.to_html(classes='scrollable-table', index=False)
    st.markdown(html_table, unsafe_allow_html=True)

def scrollable_container(content_function, height: int = 300):
    """
    Contenedor con scroll para cualquier contenido que se dibuje con la función content_function.
    content_function: función que recibe un objeto st.container() para dibujar dentro.
    """
    style = f"""
    <style>
    .scrollable-container {{
        height: {height}px;
        overflow-y: auto;
        border: 1px solid #ddd;
        padding: 10px;
    }}
    </style>
    """

    st.markdown(style, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="scrollable-container">', unsafe_allow_html=True)
        content_function()
        st.markdown('</div>', unsafe_allow_html=True)
