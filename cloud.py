import ee
import streamlit as st

service_account = st.secrets["ee_email"]
service_key = st.secrets["ee_key"]
credentials = ee.ServiceAccountCredentials(email = service_account, key_data = service_key)
ee.Initialize(credentials)


# Soil depths [in cm] where we have data.
olm_depths = [0, 10, 30, 60, 100, 200]
# Names of bands associated with reference depths.
olm_bands = ["b" + str(sd) for sd in olm_depths]

def get_data(param):
    """
    This function returns soil properties image
    param (str): must be one of:
        "sand"     - Sand fraction
        "clay"     - Clay fraction
        "orgc"     - Organic Carbon fraction
        "elev"     - DEM Elevation 
    """
    if param == "sand":  # Sand fraction [%w]
        snippet = "OpenLandMap/SOL/SOL_SAND-WFRACTION_USDA-3A1A1A_M/v02"
        # Define the scale factor in accordance with the dataset description.
        scale_factor = 1 * 0.01

    elif param == "clay":  # Clay fraction [%w]
        snippet = "OpenLandMap/SOL/SOL_CLAY-WFRACTION_USDA-3A1A1A_M/v02"
        # Define the scale factor in accordance with the dataset description.
        scale_factor = 1 * 0.01

    elif param == "orgc":  # Organic Carbon fraction [g/kg]
        snippet = "OpenLandMap/SOL/SOL_ORGANIC-CARBON_USDA-6A1C_M/v02"
        # Define the scale factor in accordance with the dataset description.
        scale_factor = 5 * 0.001  # to get kg/kg

    elif param == "elev": # Elevation data Canada wide, no data value of -32,767
        snippet = 'NRCan/CDEM'
        scale_factor = 1
    
    elif param == "diurnal": # Monthly diurnal range 
        snippet = "OpenLandMap/CLM/CLM_LST_MOD11A2-DAYNIGHT_M/v01"
        scale_factor = 	0.02

    else:
        return print("error")
    
    countries = ee.FeatureCollection("FAO/GAUL/2015/level0")
    canada = countries.filter(ee.Filter.eq('ADM0_CODE', 46))

    # Apply the scale factor to the ee.Image.
    dataset = ee.Image(snippet)
    dataset = dataset.multiply(scale_factor)


    return dataset


def local_profile(dataset, poi, buffer):
    poi=ee.Geometry.Point(poi[0],poi[1])
    prop = dataset.sample(poi, buffer).select(olm_bands).getInfo()

    if prop['features'] != []:
        # Selection of the features/properties of interest.
        profile = prop["features"][0]["properties"]
        # Re-shaping of the dict.
        profile = {key: (round(val,5)) for key, val in profile.items()}
        return profile
    else:
        return 'No data :('

