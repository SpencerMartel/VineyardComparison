import json
import pandas
import plotly.express as px
import ee
import requests
import streamlit as st

service_account = st.secrets.ee_email
credentials = ee.ServiceAccountCredentials(email = service_account, key_data = st.secrets.ee_key)
ee.Initialize(credentials)


def queried_df (sand_profile, clay_profile, orgc_profile):
    # Initialize dataframe
    data = [sand_profile,clay_profile, orgc_profile]
    df = pandas.DataFrame(data=data)
    df.index = ['Sand', 'Clay', 'Organic Matter']
    df = df[['b0', 'b10', 'b30', 'b60', 'b100', 'b200']]
    df.columns = ['Surface', '10cm', '20cm', '60cm', '100cm', '200cm']
    return df

def calculate_soil_mean(dataframe):

    sand_mean = round(dataframe['Sand'].mean(), 3)
    clay_mean = round(dataframe['Clay'].mean(), 3)
    org_mean = round(dataframe['Organic Matter'].mean(), 3)
    other = 1 - (sand_mean + clay_mean + org_mean)
    df = pandas.DataFrame(data = [sand_mean, clay_mean, org_mean, other])
    df.index = ['Sand', 'Clay', 'Organic Matter', 'Other']
    df.columns=['Mean']
    return df
    
def piechart(dataframe):
    df = calculate_soil_mean(dataframe)

    fig = px.pie(df, values=df['Mean'], names = df.index, hover_name=df.index)
    fig.update_traces(textposition = 'inside', showlegend = False,textinfo='percent+label')
    return fig

def get_elevation(lat,long):
    # This correction is required because of a streamlit problem where you can scroll left or right infinitely and the long values continue forever.

    url = f'http://geogratis.gc.ca/services/elevation/cdem/altitude?lat={lat}&lon={long}'
    result = requests.get(url)
    dict = json.loads(result.text)
    return dict

def make_profile_card(region_dict):

    # Extract values
    region = region_dict['properties']['region']
    country = region_dict['properties']['country']
    red_grapes = ', '.join(str(p) for p in region_dict['properties']['red_grapes'])
    white_grapes = ', '.join(str(p) for p in region_dict['properties']['white_grapes'])
    elevation = region_dict['properties']['mean_elevation']
    diurnal_range = region_dict['properties']['avg_diurnal_range']

    # Write em to screen, no need to return st.container() writes already
    with st.container():
        st.write('#')
        st.markdown(f'<div style="text-align: center;font-weight: bold;font-size: 20px;">{region}, {country}</div>', unsafe_allow_html=True)
        st.write('##')
        st.image(str(region_dict['properties']['image']), caption=f"Source: {region_dict['properties']['source']}")
        st.write(f'**Red grapes:**    {red_grapes}')
        st.write(f'**White grapes:**    {white_grapes}')
        st.write(f'**Mean elevation:**    {elevation}')
        st.write(f'**Mean diurnal Range:**    {diurnal_range}°C')
        st.write(f'**Soil Content:**')
        st.write(make_card_chart(region_dict).style.format("{:.4}%"))
        st.write('##')


def make_card_chart (region_dict):
    
    df = pandas.DataFrame(data = [region_dict["properties"]["mean_soil_content_%"]], index = ["Mean"])
    df.columns = df.columns.str.capitalize()
    df = df.T

    return df