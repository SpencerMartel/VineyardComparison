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
    st.markdown('<script src="https://platform.linkedin.com/badges/js/profile.js" async defer type="text/javascript"></script>', unsafe_allow_html=True)
    
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
    
    tab1, tab2 = st.tabs(["The App", "How It Works"])
    
    with tab2:
        st.title('How the app works')
        st.write("""
        The concept for this app was to compare Canadian terroir to that of the famous wine regions of the world.
        \nThere have been attempts at an app like this as a [research project](https://www.cgit.vt.edu/research/archive/vineyard-site-evaluation.html) but none in Canada and none at this scale.
        \nThis app was written in python using some HTML and CSS injections for customizing the frontend.
        """)
        st.write('')
        st.subheader('The Workflow')
        st.write("""
        1.\tCreate the profiles of the major wine regions using Google Earth Engine.
        \n2.\tCreate the profile for the queried location.
        \n3.\tCompare the queried location profile to all famous location profiles to find the most similar one.
        \n4.\tPass the results back to frontend for display.\n\n
        """)
        st.write('')
        st.write('')

        st.write("Here is the template I used when creating new location profiles following GeoJSON format:")
        with st.expander("GeoJSON Profile Template"):
            st.code("""
{
    "type": "Feature",
    "geometry": {
        "type": "",
        "coordinates": [0, 0]
    },
    "properties": {
        "country" : "",
        "region": "",
        "red_grapes": ["",""],
        "white_grapes": ["", ""],
        "mean_elevation": "",
        "mean_temp": "",
        "mean_soil_content_%" : {},
        "avg_diurnal_range" : 0,
        "image": "",
        "source": ""
    }
}""", language='json')

        st.write('')
        st.write("""Getting the data for the profiles consisted of opening the file where I have stored the templates with their bounding geometries, clipping Google Earth Engine images to that area, grabbing the mean data values of the clipped image, and writing that data to the correct location.
        I would have to manually input some fields but
        here is the script I used to programatically fill the elevation, temperature, soil content, and diurnal range values.""")
        
        with st.expander("Earth Engine Automation"):
            st.code("""
import ee
import json
import cloud

ee.Initialize()

# Main file for creating the profiles, can do everything programatically once the coordinates are in the profile.
def main():

    with open('profiles.json', 'r') as f:
        dict_profiles = json.load(f)

    profile_json = {"profiles" : []}
    for region in dict_profiles["profiles"]:
        new_region = region
        new_region["properties"]["mean_elevation"] = get_mean_elevation(region["geometry"]["coordinates"])
        new_region["properties"]["mean_soil_content_%"] = profile_mean_soil_content(region["geometry"]["coordinates"])
        new_region["properties"]["avg_diurnal_range"] = get_diurnal_range(region["geometry"]["coordinates"])
        new_region["properties"]["mean_temp"] = get_mean_temp(region["geometry"]["coordinates"])
        print(new_region)
        profile_json["profiles"].append(new_region)


    with open('profiles.json', 'w') as t:
        t.write(json.dumps(profile_json, indent = 4, sort_keys = True))


def get_mean_elevation(bounding_geometry):
    "
    Returns a mean elevation for queried region as int.
    Uses ee.reduceRegion to get stats
    "
    ee_geometry = ee.Geometry.Polygon(bounding_geometry)


    image = ee.Image('NASA/NASADEM_HGT/001').clip(ee_geometry).select('elevation')
    mean_dict = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=ee_geometry,
        scale=30,
        maxPixels=1e9
    )

    mean_elevation = (round(mean_dict.get('elevation').getInfo(),2))
    return mean_elevation


def profile_mean_soil_content(queried_polygon):

    ee_geometry = ee.Geometry.Polygon(queried_polygon)
    sand = cloud.get_data("sand").clip(ee_geometry)
    clay = cloud.get_data("clay").clip(ee_geometry)
    orgc = cloud.get_data("orgc").clip(ee_geometry)


    sand_dict = sand.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=ee_geometry,
    )
    clay_dict = clay.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=ee_geometry,
    )
    orgc_dict = orgc.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=ee_geometry,
    )

    sand = create_soil_data(sand_dict)
    clay = create_soil_data(clay_dict)
    orgc = create_soil_data(orgc_dict)
    profile = { "Sand": sand,
                "Clay" : clay,
                "Organic Matter" : orgc,
                "Other": round(100 - (sand + clay + orgc), 2)
                }
    return profile


def get_diurnal_range(bounding_geometry):
    ee_geometry = ee.Geometry.Polygon(bounding_geometry)
    image = ee.Image("OpenLandMap/CLM/CLM_LST_MOD11A2-DAYNIGHT_M/v01").clip(ee_geometry).select('may', 'jun','jul', 'aug','sep')
    image = image.multiply(0.02)

    mean_dict = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=ee_geometry,
        scale=30,
        maxPixels=1e9
    )
    mean_diurnal_range = mean_dict.getInfo()

    mean = round(sum(mean_diurnal_range.values()) / len(mean_diurnal_range), 2)
    return mean


def get_mean_temp(bounding_geometry):

    ee_geometry = ee.Geometry.Polygon(bounding_geometry)
    image = ee.Image("WORLDCLIM/V1/BIO")
    dataset = image.select("bio01")

    mean_dict = dataset.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=ee_geometry,
        scale=30,
        maxPixels=1e9
    )
    value = list(mean_dict.getInfo().values())
    return round((value[0]*0.1), 2)

main()""", 'python')
        st.write('')
        
        st.write("""Once I had the profiles, I need to compare the selected location profile to the famous regions, I do that using this function.
        Simply put I take the sum of the absolute value of the difference between the queried location value and the famous regions value to create a score for each location.
        Whichever location has the lowest score is the region I tell the frontend to display. Notice the difference in elevation is worth less since if it weren't it would be entirely responsable for deciding the most similar region.""")
        with st.expander('Comparison Function'):
            st.code("""
def comparison(queried_profile, profiles):

    comparative_profiles = make_profile_comparative_json(profiles)
    closest_profile = ''
    lowest_score = 1000000
    region_scores = []

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

        comparative_dict = ({f'{comparative_region["region"]}': score})
        region_scores.append(comparative_dict)
    print(f'closest profile is: {closest_profile}')
    print(f'List of regions and scores: {region_scores}')

    return closest_profile""", 'python')
        st.write('')
        
        st.write("""That\'s how it all works. Using streamlit for the frontend let me focus on the geographic aspects of this project while being able to dip my toe in database management.
        \nFeel free to [contact me](https://www.linkedin.com/in/spencer-martel-576367239/) if you have any questions or would like a deeper explanation.
        \nHere is the [GitHub repo](https://github.com/SpencerMartel/VineyardComparison) for this project.""")
    with tab1:
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

            # Mapping tab (actual app)
            try:
                df = queried_df(queried_sand_profile, queried_clay_profile, queried_orgc_profile)
                location_soil_mean_df = calculate_soil_mean(df.T)
                
                elevation = get_elevation(clicked_lat, clicked_lng)
                elevation_result = elevation['altitude']

                location_dict = make_queried_json(location_soil_mean_df, elevation_result, clicked_lat, clicked_lng)
                try:
                    closest_region_string, all_scores = comparison(location_dict, profiles)
                except TypeError:
                    st.subheader('No data for that location, make sure to click in Canada and not on a body of water.')
                    return
                
                for region in profiles["profiles"]:
                    if region["properties"]["region"] == closest_region_string:
                        closest_region_dict = region

                st.markdown(f'<div style="text-align: center;font-weight: bold;font-size: 25px;">Most Similar Region</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="text-align: center;font-weight: bold;font-size: 35px;"><u>{closest_region_dict["properties"]["region"]} - {closest_region_dict["properties"]["country"]}</u></div>', unsafe_allow_html=True)
                st.write('')
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
                st.subheader(f'According to this analysis you should try growing {red_grapes}, {white_grapes}.')
                st.write("These metrics show the data for your selected location, the smaller numbers in red and green show the difference between the location's values and those of the most similar region.")
            except KeyError:
                st.subheader('No data for that location, make sure to click in Canada and not on a body of water.')

def map_creater(marker_location):
    my_map = folium.Map(location=(57.70414723434193, -108.28125000000001), zoom_start = 3, max_bounds=[[-180, -90], [180, 90]], tiles= "openstreetmap")
    if marker_location != None:
        folium.Marker(marker_location).add_to(my_map)
    return my_map

if __name__ == '__main__':
    main()