import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import folium
import matplotlib.pyplot as plt
from streamlit_folium import folium_static
from PIL import Image

# ===========================
# Function
# ===========================
def clean_code( data ):
    # removing NA
    data = data.loc[(data['Delivery_person_Age'] != 'NaN '), :]
    data = data.loc[(data['City'] != 'NaN '), :]
    data = data.loc[(data['Road_traffic_density'] != 'NaN '), :]
    data = data.loc[(data['Festival'] != 'NaN '), :]
    data = data.loc[(data['multiple_deliveries'] != 'NaN '), :].copy()
    # converting data type
    data['Delivery_person_Ratings'] = data['Delivery_person_Ratings'].astype( float )
    data['Delivery_person_Age']     = data['Delivery_person_Age'].astype( int )
    data['Order_Date']              = pd.to_datetime( data['Order_Date'], format='%d-%m-%Y' )
    data['multiple_deliveries']     = data['multiple_deliveries'].astype( int )
    # removing espacos
    data.loc[:, 'ID'] = data.loc[:, 'ID'].str.strip()
    data.loc[:, 'Road_traffic_density'] = data.loc[:, 'Road_traffic_density'].str.strip()
    data.loc[:, 'Type_of_order'] = data.loc[:, 'Type_of_order'].str.strip()
    data.loc[:, 'Type_of_vehicle'] = data.loc[:, 'Type_of_vehicle'].str.strip()
    data.loc[:, 'City'] = data.loc[:, 'City'].str.strip()
    data.loc[:, 'Festival'] = data.loc[:, 'Festival'].str.strip()
    # cleaning coluna time taken
    data['Time_taken(min)'] = data['Time_taken(min)'].apply( lambda x: x.split( '(min) ')[1] )
    data['Time_taken(min)'] = data['Time_taken(min)'].astype( int )
    data['week_of_year'] = data['Order_Date'].dt.strftime( "%U" )
    return data

def get_avg_rating_by_traffic( df ):
    df_aux = ( df.loc[:, ['Delivery_person_Ratings', 'Road_traffic_density']]
                 .groupby( 'Road_traffic_density')
                 .agg( {'Delivery_person_Ratings': ['mean', 'std' ]} ) )
    # mudanca de nome das colunas
    df_aux.columns = ['delivery_mean', 'delivery_std']
    # reset do index
    df_aux = df_aux.reset_index()
    return df_aux

def get_avg_rating_by_weather( df ):
    df_aux = ( df.loc[:, ['Delivery_person_Ratings', 'Weatherconditions']]
                 .groupby( 'Weatherconditions' )
                 .agg( {'Delivery_person_Ratings': ['mean', 'std']} ) )
    # mudanca de nome das colunas
    df_aux.columns = ['delivery_mean', 'delivery_std']
    # reset do index
    df_aux = df_aux.reset_index()
    return df_aux


def get_faster_delivery( df ):
    df = ( df.loc[:, ['Delivery_person_ID', 'City', 'Time_taken(min)']]
             .groupby( ['City', 'Delivery_person_ID'] )
             .mean()
             .sort_values( ['City', 'Time_taken(min)'], ascending=True )
             .reset_index() )
    df_aux01 = df.loc[df['City'] == 'Metropolitian', :].head(10)
    df_aux02 = df.loc[df['City'] == 'Urban', :].head(10)
    df_aux03 = df.loc[df['City'] == 'Semi-Urban', :].head(10)
    df3 = pd.concat( [df_aux01, df_aux02, df_aux03] ).reset_index( drop=True )
    return df3

def get_slower_delivery( df ):
    df = ( df.loc[:, ['Delivery_person_ID', 'City', 'Time_taken(min)']]
             .groupby( ['City', 'Delivery_person_ID'] )
             .mean()
             .sort_values( ['City', 'Time_taken(min)'], ascending=False )
             .reset_index() )
    df_aux01 = df.loc[df['City'] == 'Metropolitian', :].head(10)
    df_aux02 = df.loc[df['City'] == 'Urban', :].head(10)
    df_aux03 = df.loc[df['City'] == 'Semi-Urban', :].head(10)
    df3 = pd.concat( [df_aux01, df_aux02, df_aux03] ).reset_index( drop=True )
    return df3

# ===========================
# Título
# ===========================
st.header("Marketplace - Visão Entregadores")  ## Main Title

# ===========================
# Filtros - Side bar
# ===========================
image = Image.open( 'logo.jpg' )
st.sidebar.image( image, width=120 )

st.sidebar.markdown( "# Curry Company" )
st.sidebar.markdown( "## Fastest Delivery in Town" )
st.sidebar.markdown( """---""" )

st.sidebar.markdown( "## Selecione um data limite" )
date_slider = st.sidebar.slider(
        "Até qual valor?",
        value=pd.datetime( 2022, 4, 13 ),
        min_value=pd.datetime( 2022, 2, 11),
        max_value=pd.datetime( 2022, 5, 6 ), 
        format="DD-MM-YYYY"
    )
st.sidebar.markdown( """---""" )
st.sidebar.markdown( "## Selecione uma condição de trânsito" )
traffic_options = st.sidebar.multiselect(
        'Quais a condições do trânsito?',
        ['Low', 'Medium', 'High', 'Jam'], default='Medium' )
# ===========================
# ETL
# ===========================
# Extracao
df = pd.read_csv( 'dataset/train.csv' )
# Limpeza
df = clean_code( df )
# Tranformação
df = df.loc[df['Order_Date'] <= date_slider, :]
df = df.loc[df['Road_traffic_density'].isin( traffic_options ), :]
# ===========================
# Título
# ===========================
#st.set_page_config(layout="wide")
st.markdown("# Marketplace - Entregadores")
# ===========================
# Layout
# ===========================
# Tabs
tab1, tab2 = st.tabs( ['Visão Gerencial', '_'] )

# A maior idade dos entregadores
older_age = df.loc[:, 'Delivery_person_Age'].max()
younger_age = df.loc[:, 'Delivery_person_Age'].min()

# A melhor e a pior condicao
best_vehicle  = df.loc[:, 'Vehicle_condition'].max()
worst_vehicle = df.loc[:, 'Vehicle_condition'].min()

# Avaliacao media por entregador
df_avg_ratings_per_deliver = ( df.loc[:, ['Delivery_person_Ratings', 'Delivery_person_ID']]
                                 .groupby( 'Delivery_person_ID' )
                                 .mean()
                                 .reset_index() )
with tab1:
    with st.container():
        st.title("Overall Metrics")
        col1, col2, col3, col4 = st.columns( 4, gap="large" )
        # Display Number - 
        col1.metric("Older Delivery Age", older_age )
        col2.metric("Younger Delivery Age", younger_age )        
        col3.metric("Best Vehicle Condition", best_vehicle )
        col4.metric("Worst Vehicle Condition", worst_vehicle )
    with st.container():
        st.markdown("""---""")
        st.title("Ratings")
        col1, col2 = st.columns( 2 )
        with col1:
            st.subheader( "Average Ratings per Deliver" )
            st.dataframe( df_avg_ratings_per_deliver )
        with col2:
            st.subheader( "Average Ratings per Traffic" )
            st.dataframe( get_avg_rating_by_traffic( df ) )
            st.subheader( "Average Ratings per Weather" )
            st.dataframe( get_avg_rating_by_weather( df ) )
    with st.container():
        st.markdown("""---""")
        st.title( 'Speed of Delivery' )
        col1, col2 = st.columns( 2 )
        with col1:
            st.subheader( 'Faster Delivery by City' )
            st.dataframe( get_faster_delivery( df ) )
        with col2:
            st.subheader( 'Faster Delivery by City' )
            st.dataframe( get_slower_delivery( df ) )

