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
        print('\n', new_region)
        profile_json["profiles"].append(new_region)
    

    with open('profiles.json', 'w') as t:
        t.write(json.dumps(profile_json, indent = 4, sort_keys = True))
    

def get_mean_elevation(bounding_geometry):
    """
    Returns a mean elevation for queried region as int.
    Uses ee.reduceRegion to get stats
    """
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
                "Other": round(100 - (sand + clay + orgc), 2)}
    return profile

def create_soil_data(soil_dict):
    # Soil depths [in cm] where we have data.
    olm_depths = [0, 10, 30, 60, 100, 200]
    # Names of bands associated with reference depths.
    olm_bands = ["b" + str(sd) for sd in olm_depths]

    sum = 0
    for band in olm_bands:
        sum = sum + soil_dict.get(band).getInfo()
    
    return round(sum / len(olm_bands)*100,3)

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

main()