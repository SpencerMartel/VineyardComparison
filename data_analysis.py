import json
import ee
import numpy as np
import pandas
import plotly.express as px
import requests
import streamlit as st
import matplotlib as mpl
from matplotlib import pyplot as plt

service_account = st.secrets["ee_email"]
credentials = ee.ServiceAccountCredentials(email = service_account, key_data = st.secrets["ee_key"])
ee.Initialize(credentials)


def queried_df (sand_profile, clay_profile, orgc_profile):
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
        st.markdown(f'<div style="text-align: center;font-weight: bold;font-size: 22px;">{region}, {country}</div>', unsafe_allow_html=True)
        st.write('##')
        st.image(str(region_dict['properties']['image']), caption=f"Source: {region_dict['properties']['source']}")
        st.write(f'**Red grapes:**    {red_grapes}')
        st.write(f'**White grapes:**    {white_grapes}')
        st.write(f'**Mean elevation:**    {elevation} m')
        st.write(f'**Mean diurnal Range:**    {diurnal_range}°C')
        st.write(f'**Soil Content:**')
        st.write(make_card_chart(region_dict).style.format("{:.4}%"))
        st.write('##')


def make_card_chart (region_dict):
    
    df = pandas.DataFrame(data = [region_dict["properties"]["mean_soil_content_%"]], index = ["Mean"])
    df.columns = df.columns.str.capitalize()
    df = df.T

    return df

def comparison(queried_profile, profiles):

    comparative_profiles = make_profile_comparative_json(profiles)
    closest_profile = ''
    lowest_score = 1000000
    list_of_dicts = []

    for comparative_region in comparative_profiles:
        # Loop through regions, compare values of clicked location to region
        # Whichever one has the lowest score is the most similar
        elev = abs(queried_profile["mean_elevation"] - comparative_region["mean_elevation"]) * 0.02
        temp = abs(queried_profile["mean_temp"] - comparative_region["mean_temp"])
        clay = abs(queried_profile["mean_soil_content_%"]["Clay"] - comparative_region["mean_soil_content_%"]["Clay"])
        org = abs(queried_profile["mean_soil_content_%"]["Organic Matter"] - comparative_region["mean_soil_content_%"]["Organic Matter"])
        other = abs(queried_profile["mean_soil_content_%"]["Other"] - comparative_region["mean_soil_content_%"]["Other"])
        sand = abs(queried_profile["mean_soil_content_%"]["Sand"] - comparative_region["mean_soil_content_%"]["Sand"])
        score = round(elev + temp + clay + org + other + sand, 2)
        
        if score < lowest_score:
            lowest_score = score
            closest_profile = comparative_region["region"]

        comparative_dict = {"region": comparative_region["region"], "score": score}
        list_of_dicts.append(comparative_dict)

    return closest_profile, list_of_dicts
    

        

def make_queried_json(soil_df, elevation, lat, long):
    soil = pandas.DataFrame.to_dict(soil_df)

    location_dict = {
            "mean_elevation": elevation,
            "mean_temp": get_location_temp(lat,long),
            "mean_soil_content_%" : {
                "Clay": round((soil["Mean"]["Clay"] * 100),2),
                "Organic Matter": round((soil["Mean"]["Organic Matter"] * 100),2),
                "Other": round((soil["Mean"]["Other"] * 100),2),
                "Sand": round((soil["Mean"]["Sand"] * 100), 2),
            },
            "avg_diurnal_range" : get_location_diurnal_range(long, lat),
        }
    
    return location_dict

def make_profile_comparative_json(profiles):
    """
    returns a list of dicts from the pre-made profiles containing only the data we want to compare to the queried location
    """
    
    list_of_dicts = []
    for region in profiles["profiles"]:
        location_dict = {
            "region" : region["properties"]["region"],
            "mean_elevation": region["properties"]["mean_elevation"],
            "mean_temp": region["properties"]["mean_temp"],
            "mean_soil_content_%" : {
                "Clay": region["properties"]["mean_soil_content_%"]["Clay"],
                "Organic Matter": region["properties"]["mean_soil_content_%"]["Organic Matter"],
                "Other": region["properties"]["mean_soil_content_%"]["Other"],
                "Sand": region["properties"]["mean_soil_content_%"]["Sand"]
            },
            "avg_diurnal_range" : region["properties"]["avg_diurnal_range"],
        }
        list_of_dicts.append(location_dict)

    return list_of_dicts

def get_location_temp(lat,long):
    
    point = ee.Geometry.Point(long,lat)
    image = ee.Image("WORLDCLIM/V1/BIO")
    image = image.multiply(0.1)
    dataset = image.select("bio01")
    
    mean_dict = dataset.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=30,
        maxPixels=1,
    )
    info = mean_dict.getInfo()
    mean = round(sum(info.values()), 2)
    return mean


def get_location_diurnal_range(long, lat):
    ee_geometry = ee.Geometry.Point(long, lat)
    image = ee.Image("OpenLandMap/CLM/CLM_LST_MOD11A2-DAYNIGHT_M/v01").select('may', 'jun','jul', 'aug','sep')
    image = image.multiply(0.02)

    mean_dict = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=ee_geometry,
        scale=30,
        maxPixels=1e9
    )
    mean_diurnal_range = mean_dict.getInfo()

    mean = round(sum(mean_diurnal_range.values()) / len(mean_diurnal_range),2)
    return mean