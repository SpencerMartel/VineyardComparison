import folium
import streamlit as st
import streamlit_folium as stf
from data_analysis import *
from cloud import *

title = 'Vineyard Site Selection'

def main():
    # Config for website
    st.set_page_config(
        page_title= 'Vineyard Site Selection',
        page_icon=":wine_glass:",
        layout = "wide",
        initial_sidebar_state="expanded")
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
    st.markdown(
        """
        <style>
        .css-1xtoq5p e1fqkh3o2 {
            display: none;
        }
        MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
        )
    
    @st.cache
    def load_profiles():
        p = open('profiles.json')
        profiles = json.load(p)
        return profiles 
    @st.cache
    def load_sand():
        sand = get_data("sand")
        return sand
    @st.cache
    def load_clay():
        clay = get_data("clay")
        return clay
    @st.cache
    def load_orgc():
        orgc = get_data("orgc")
        return orgc

    profiles = load_profiles()
    # Sidebar
    with st.sidebar:
        # Load profiles as python dict.

        st.header('Profiles currently in our database')
        st.subheader('Click through them to learn about the region')

        # Lets me programatically build the sidebar based on data in profiles.
        france_options = []
        usa_options = []
        italy_options = []
        nz_options = []
        for obj in profiles['profiles']:
            if obj['properties']['country'] == 'France':
                france_options.append(obj['properties']['region'])
            elif obj['properties']['country'] == 'Italy':
                italy_options.append(obj['properties']['region'])
            elif obj['properties']['country'] == 'USA':
                usa_options.append(obj['properties']['region'])
            elif obj['properties']['country'] == 'New Zealand':
                nz_options.append(obj['properties']['region'])            



        country = st.selectbox(label = 'Country', label_visibility='collapsed',options=('France', 'Italy', 'USA','New Zealand'))
        if country == 'France':
            region = st.radio(label='Region', options=france_options)
            # Grab the profile associated with the queried region to build the data card.
            queried_region_profile = {}
            for obj in profiles['profiles']:
                if obj['properties']['region'] == region:
                    queried_region_profile.update(obj)
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
        
        if country == 'New Zealand':
            region = st.radio(label='Region', options=nz_options)
            # Grab the profile associated with the queried region to build the card.
            queried_region_profile = {}
            for obj in profiles['profiles']:
                if obj['properties']['region'] == region:
                    queried_region_profile.update(obj)
            make_profile_card(queried_region_profile)
        
        

    st.title('Site Suitability for Canadian Vineyards')
    st.write("Select any location in Canada to see which of the world's most famous wine regions it is most similar to!")


    # Display map
    my_map = map_creater(None)
    map_data = stf.st_folium(my_map, width = 1500)

    

    # Data from leaflet
    clicked_lat_lng = (map_data["last_clicked"])


    if not clicked_lat_lng:
        st.subheader('Click anywhere in Canada to load data for that point!')
    else:
        clicked_lat, clicked_lng = round(map_data["last_clicked"]['lat'], 2), round(map_data["last_clicked"]['lng'], 2)


        # Data analysis
        queried_clay_profile = local_profile(load_clay(), (clicked_lng,clicked_lat), 1000)
        queried_sand_profile = local_profile(load_sand(), (clicked_lng,clicked_lat), 1000)
        queried_orgc_profile = local_profile(load_orgc(), (clicked_lng,clicked_lat), 1000)
        
        if queried_clay_profile is None:
            st.write('No data available')
        else:
            # This is where we begin the comparison.
            df = queried_df(queried_sand_profile, queried_clay_profile, queried_orgc_profile)
            location_soil_mean_df = calculate_soil_mean(df.T)
            
            elevation = get_elevation(clicked_lat, clicked_lng)
            elevation_result = elevation['altitude']

            location_dict = make_queried_json(location_soil_mean_df, elevation_result, clicked_lat, clicked_lng)
            closest_region_string = comparison(location_dict, profiles)
            for region in profiles["profiles"]:
                if region["properties"]["region"] == closest_region_string:
                    closest_region_dict = region


            st.subheader(f'Most Similar Region: {closest_region_dict["properties"]["region"]}, {closest_region_dict["properties"]["country"]}')
            st.write("These metrics show the data for your selected location, the smaller numbers in red and green show the difference between the location's values and those of the most similar region")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric('Elevation', f'{location_dict["mean_elevation"]} m', delta = f'{round(location_dict["mean_elevation"] - closest_region_dict["properties"]["mean_elevation"],2 )} m')
            with col2:
                st.metric('Average Temperature', f'{location_dict["mean_temp"]} °C', delta = f'{round(location_dict["mean_temp"] - closest_region_dict["properties"]["mean_temp"],2)} °C')
            with col3:
                st.metric('Diurnal Range', f'{location_dict["avg_diurnal_range"]} °C', delta = f'{round(location_dict["avg_diurnal_range"] - closest_region_dict["properties"]["avg_diurnal_range"],2)} °C')
            with col1:
                st.metric('Organic Matter in Soil', f'{location_dict["mean_soil_content_%"]["Organic Matter"]} %', delta = f'{round(location_dict["mean_soil_content_%"]["Organic Matter"] - closest_region_dict["properties"]["mean_soil_content_%"]["Organic Matter"],2)} %')
            with col2:
                st.metric('Clay in Soil', f'{location_dict["mean_soil_content_%"]["Clay"]} %', delta = f'{round(location_dict["mean_soil_content_%"]["Clay"] - closest_region_dict["properties"]["mean_soil_content_%"]["Clay"],2)} %')
            with col3:
                st.metric('Sand in Soil', f'{location_dict["mean_soil_content_%"]["Sand"]} %', delta = f'{round(location_dict["mean_soil_content_%"]["Sand"] - closest_region_dict["properties"]["mean_soil_content_%"]["Sand"],2)} %')
            
            red_grapes = ', '.join(str(p) for p in closest_region_dict['properties']['red_grapes'])
            white_grapes = ', '.join(str(p) for p in closest_region_dict['properties']['white_grapes'])
            # st.write(f'The red grapes grown in {closest_region_dict["properties"]["region"]} are: {red_grapes}')
            # st.write(f'The white grapes grown in {closest_region_dict["properties"]["region"]} are: {white_grapes}')

                


def map_creater(marker_location):
    my_map = folium.Map(location=(57.70414723434193, -108.28125000000001), zoom_start = 3, max_bounds=[[-180, -90], [180, 90]], tiles= "Stamen Terrain")
    if marker_location != None:
        folium.Marker(marker_location).add_to(my_map)
    return my_map

if __name__ == '__main__':
    main()