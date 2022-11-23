import folium
import numpy as np
import streamlit as st
import streamlit_folium as stf
from data_analysis import *
from cloud import *
import matplotlib.pyplot as plt

title = 'Vineyard Site Selection'

def main():
    # Config for website
    st.set_page_config(
        title,
        page_icon=":wine_glass:",
        layout = "wide",
        initial_sidebar_state="expanded")

    st.markdown(
        """
        <style>
        .css-1xtoq5p e1fqkh3o2 {
            display: none;
        }
        div[class="css-1pd56a0 e1tzin5v0"] {
            background-image: linear-gradient(to bottom, red 10%, #900c3f,0%);
        }
        MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
        )
    

    # Sidebar
    with st.sidebar:
        # Load profiles as python dict.
        p = open('profiles.json')
        profiles = json.load(p)

        st.header('Select the Location you would like to compare to:')

        # Lets me programatically build the sidebar based on data in profiles.
        france_options = []
        usa_options = []
        italy_options = []
        for obj in profiles['profiles']:
            if obj['properties']['country'] == 'France':
                france_options.append(obj['properties']['region'])
            elif obj['properties']['country'] == 'Italy':
                italy_options.append(obj['properties']['region'])
            elif obj['properties']['country'] == 'USA':
                usa_options.append(obj['properties']['region'])


        country = st.selectbox(label = 'Country', label_visibility='collapsed',options=('France', 'Italy', 'USA',))
        if country == 'France':
            region = st.radio(label='Region', options=france_options)
            
            # Grab the profile associated with the queried region to build the data card.
            queried_region_profile = {}
            for obj in profiles['profiles']:
                if obj['properties']['region'] == region:
                    queried_region_profile.update(obj)

            # This is where I build the sidebar region cards
            make_profile_card(queried_region_profile)

        
        if country == 'Italy':
            region = st.radio(label='Region', options=italy_options)
            # Grab the profile associated with the queried region to build the card.
            queried_region_profile = {}
            for obj in profiles['profiles']:
                if obj['properties']['region'] == region:
                    queried_region_profile.update(obj)
            
            make_profile_card(queried_region_profile)

        if country == 'USA':
            region = st.radio(label='Region', options=usa_options)
            # Grab the profile associated with the queried region to build the card.
            queried_region_profile = {}
            for obj in profiles['profiles']:
                if obj['properties']['region'] == region:
                    queried_region_profile.update(obj)
            make_profile_card(queried_region_profile)


    st.title('Vineyard Site Selection')


    # Load data
    sand = get_data("sand")
    clay = get_data("clay")
    orgc = get_data("orgc")

    # Display map
    map_data = stf.st_folium(map_creater(), width = 1500)
    
    queried_col,profile_col = st.columns(2)
    # Data for graphs / tables
    clicked_lat_lng = (map_data["last_clicked"])


    if not clicked_lat_lng:
        st.header('Click anywhere in Canada to load data for that point!')
    else:
        clicked_lat, clicked_lng = round(map_data["last_clicked"]['lat'], 2), round(map_data["last_clicked"]['lng'], 2)
        # Used to debug data passed back from folium
        # st.write(map_data['last_clicked'])

        
        # Data analysis
        queried_clay_profile = local_profile(clay, (clicked_lng,clicked_lat), 1000)
        queried_sand_profile = local_profile(sand, (clicked_lng,clicked_lat), 1000)
        queried_orgc_profile = local_profile(orgc, (clicked_lng,clicked_lat), 1000)
        
        if queried_clay_profile is None:
            st.write('No data available')
        else:
            # This is where we begin the comparison.
            with queried_col:
                st.title('Selected Location')
                df = queried_df(queried_sand_profile, queried_clay_profile, queried_orgc_profile)
                location_soil_mean_df = calculate_soil_mean(df.T)

                profile_soil_mean_df = pandas.DataFrame({
                    "Clay": 0.279,
                    "Organic Matter": 0.0117,
                    "Other": 0.040,
                    "Sand": 0.3067
                }, index = ["Profile Mean"])

                fig = comparative_soil_chart(location_soil_mean_df, profile_soil_mean_df)
                st.write(fig)
                
                elevation = get_elevation(clicked_lat, clicked_lng)
                result = elevation['altitude']
                st.write(f'Elevation: {result}')
            with profile_col:
                return


def map_creater():
    
    my_map = folium.Map(location=(57.70414723434193, -108.28125000000001), zoom_start = 3, max_bounds=[[-180, -90], [180, 90]], tiles= "Stamen Terrain")
    return my_map


if __name__ == '__main__':
    main()