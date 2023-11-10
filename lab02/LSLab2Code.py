# import packages
import requests
import zipfile
import arcpy
import pprint
import json
import os
import csv
from io import BytesIO
import shutil
import arcpy.mp as mp


# mndnr api request
las_url = "https://resources.gisdata.mn.gov/pub/data/elevation/lidar/examples/lidar_sample/las/4342-16-03.las"
response = requests.get(las_url, stream = True)
with open('sample.las', 'wb') as out_file:
  shutil.copyfileobj(response.raw, out_file)

# extract .las to give proj coord system so it can be converted
arcpy.env.workspace = 'C:\\Users\\18284\\Documents\\ArcGIS\\Projects\\arc1lab2'
arcpy.ddd.ExtractLas('sample.las', 'C:\\Users\\18284\\Documents\\ArcGIS\\Projects\\arc1lab2')

# convert .las to .dem
arcpy.env.workspace = 'C:\\Users\\18284\\Documents\\ArcGIS\\Projects\\arc1lab2'
tif = arcpy.conversion.LasDatasetToRaster('sample.las', 'sample.tif')
print(tif)

# convert .las to .tin
arcpy.env.workspace = 'C:\\Users\\18284\\Documents\\ArcGIS\\Projects\\arc1lab2'
tin = arcpy.ddd.LasDatasetToTin('sample.las', 'sample.tin', 'WINDOW_SIZE', 'MIN', 15, 5000000, 1, "CLIP")
print(tin)

# identify current layouts in the project
arcpy.env.workspace = 'C:\\Users\\18284\\Documents\\ArcGIS\\Projects\\arc1lab2'
aprx = arcpy.mp.ArcGISProject("CURRENT")
for m in aprx.listMaps():
    print("Map: " + m.name)
    for lyr in m.listLayers():
        print("  " + lyr.name)
print("Layouts:")
for lyt in aprx.listLayouts():
    print(f"  {lyt.name} ({lyt.pageHeight} x {lyt.pageWidth} {lyt.pageUnits})")

# export layouts to pdf
# Define the output folder where PDFs will be saved
output_folder = r'C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2'

# Load the current project
aprx = mp.ArcGISProject('CURRENT')

# List all layouts in the project
layouts = aprx.listLayouts()

# Loop through each layout and export it to PDF
for layout in layouts:
    pdf_output = f"{output_folder}\\{layout.name}.pdf"
    layout.exportToPDF(pdf_output)

# Clean up
del aprx

print(f"All layouts in the current project have been exported to PDFs in '{output_folder}'.")

# prism data request
prismurl = "https://ftp.prism.oregonstate.edu/normals_4km/ppt/PRISM_ppt_30yr_normal_4kmM4_all_bil.zip"
response = requests.get(prismurl)
# check response.status_code to see if download was successful, should return '200'
if response.status_code == 200:
    # Open zipfile
    with zipfile.ZipFile(BytesIO(response.content)) as z:
        # extract contents of zipfile
        z.extractall('prismdata') # extracts contents into a folder named 'prismdata'
        
        # assuming there's only one fgdb file in the zip, get its name
        prismfile = [name for name in z.namelist()]
        print(prismfile)

# create mosaic dataset
arcpy.management.CreateMosaicDataset(
    in_workspace=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb",
    in_mosaicdataset_name="spacetimecube",
    coordinate_system='PROJCS["WGS_1984_UTM_Zone_15N",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-93.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]],VERTCS["NAVD88 - Geoid03 (Meters)",VDATUM["unknown"],PARAMETER["Vertical_Shift",0.0],PARAMETER["Direction",1.0],UNIT["Meter",1.0]]',
    num_bands=None,
    pixel_type="",
    product_definition="NONE",
    product_band_definitions=None
)

# add .bil data to mosaic dataset
arcpy.management.AddRastersToMosaicDataset(
    in_mosaic_dataset="spacetimecube",
    raster_type="Raster Dataset",
    input_path=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\prismdata",
    update_cellsize_ranges="UPDATE_CELL_SIZES",
    update_boundary="UPDATE_BOUNDARY",
    update_overviews="NO_OVERVIEWS",
    maximum_pyramid_levels=None,
    maximum_cell_size=0,
    minimum_dimension=1500,
    spatial_reference=None,
    filter="",
    sub_folder="SUBFOLDERS",
    duplicate_items_action="ALLOW_DUPLICATES",
    build_pyramids="NO_PYRAMIDS",
    calculate_statistics="NO_STATISTICS",
    build_thumbnails="NO_THUMBNAILS",
    operation_description="",
    force_spatial_reference="NO_FORCE_SPATIAL_REFERENCE",
    estimate_statistics="NO_STATISTICS",
    aux_inputs=None,
    enable_pixel_cache="NO_PIXEL_CACHE",
    cache_location=r"C:\Users\18284\AppData\Local\ESRI\rasterproxies\spacetimecube"
)

# add precip field
arcpy.management.CalculateField(
    in_table=r"spacetimecube\Footprint",
    field="Variable",
    expression='"Precip"',
    expression_type="PYTHON3",
    code_block="",
    field_type="TEXT",
    enforce_domains="NO_ENFORCE_DOMAINS"
)

# fill precip field with date info

arcpy.management.CalculateField(
    in_table=r"spacetimecube\Footprint",
    field="Timestamp",
    expression='DateAdd(Date(2022, 0, 1), $feature.OBJECTID-1, "month")',
    expression_type="ARCADE",
    code_block="",
    field_type="DATE",
    enforce_domains="NO_ENFORCE_DOMAINS"
)

# build multidimensional info
arcpy.md.BuildMultidimensionalInfo(
    in_mosaic_dataset="spacetimecube",
    variable_field="Variable",
    dimension_fields="Timestamp # #",
    variable_desc_units=None,
    delete_multidimensional_info="NO_DELETE_MULTIDIMENSIONAL_INFO"
)

# make multidimensional raster layer
arcpy.md.MakeMultidimensionalRasterLayer(
    in_multidimensional_raster="spacetimecube",
    out_multidimensional_raster_layer="spacetimecube_MultidimLayer",
    variables="Precip",
    dimension_def="ALL",
    dimension_ranges=None,
    dimension_values=None,
    dimension="",
    start_of_first_iteration="",
    end_of_first_iteration="",
    iteration_step=None,
    iteration_unit="",
    template='-2871588.8749 2660355.52462727 3264898.0551283 6041685.0575 PROJCS["WGS_1984_UTM_Zone_15N",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-93.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]],VERTCS["NAVD88 - Geoid03 (Meters)",VDATUM["unknown"],PARAMETER["Vertical_Shift",0.0],PARAMETER["Direction",1.0],UNIT["Meter",1.0]]',
    dimensionless="DIMENSIONS",
    spatial_reference=None
)

# create spaceitme cube
arcpy.stpm.CreateSpaceTimeCubeMDRasterLayer(
    in_md_raster="spacetimecube_MultidimLayer",
    output_cube=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\spacecube.nc",
    fill_empty_bins="ZEROS"
)

mn_gsc_api_url = "https://gisdata.mn.gov/api/3/action"

# MN geospatial commons api search datasets request for land use

search_datasets_url = mn_gsc_api_url + "/package_search"
query = "Land Use/Cover, Agricultural and Transition Areas, Minnesota, 1990"
request_url = search_datasets_url + f"?q={query}"
response = requests.get(request_url, verify=False) # verify=False disables SSL certification validation which makes it mad but i cant get it to work without disabling it
response_data = json.loads(response.text)
found_dataset_names = [dataset["title"] for dataset in response_data["result"]["results"]]
print(found_dataset_names)

# MN geospatial commons api get dataset request for land use

first_dataset_result_id = response_data["result"]["results"][0]["id"] # grab dataset that is first in returned dataset results
get_dataset_url = mn_gsc_api_url + "/package_show"
id = first_dataset_result_id
request_url = get_dataset_url + f"?id={id}"
response = requests.get(request_url, verify=False) # again disabling ssl cert validation
response_data = json.loads(response.text)
resources = response_data["result"]["resources"]
raw_zip_dataset_file_download_url = [resource for resource in resources if resource["resource_type"] == "fgdb"][0]["url"]
print(raw_zip_dataset_file_download_url)

# download landuse
response = requests.get(raw_zip_dataset_file_download_url)
# check response.status_code to see if download was successful, should return '200'
os.chdir(r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2")
if response.status_code == 200:
    # Open zipfile
    with zipfile.ZipFile(BytesIO(response.content)) as z:
        # extract contents of zipfile
        z.extractall('landuse') # extracts contents into a folder named 'landuse'
        
        # assuming there's only one landuse file in the zip, get its name
        landuse_file = [name for name in z.namelist()]
        print(landuse_file)

mn_gsc_api_url = "https://gisdata.mn.gov/api/3/action"

# MN geospatial commons api search datasets request for counties

search_datasets_url = mn_gsc_api_url + "/package_search"
query = "County Boundaries, Minnesota"
request_url = search_datasets_url + f"?q={query}"
response = requests.get(request_url, verify=False) # verify=False disables SSL certification validation which makes it mad but i cant get it to work without disabling it
response_data = json.loads(response.text)
found_dataset_names = [dataset["title"] for dataset in response_data["result"]["results"]]
print(found_dataset_names)

# MN geospatial commons api get dataset request for counties

first_dataset_result_id = response_data["result"]["results"][1]["id"] # grab dataset that is second in returned dataset results
get_dataset_url = mn_gsc_api_url + "/package_show"
id = first_dataset_result_id
request_url = get_dataset_url + f"?id={id}"
response = requests.get(request_url, verify=False) # again disabling ssl cert validation
response_data = json.loads(response.text)
resources = response_data["result"]["resources"]
raw_zip_dataset_file_download_url = [resource for resource in resources if resource["resource_type"] == "fgdb"][0]["url"]
print(raw_zip_dataset_file_download_url)

# download counties 
response = requests.get(raw_zip_dataset_file_download_url)
# check response.status_code to see if download was successful, should return '200'
os.chdir(r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2")
if response.status_code == 200:
    # Open zipfile
    with zipfile.ZipFile(BytesIO(response.content)) as z:
        # extract contents of zipfile
        z.extractall('counties') # extracts contents into a folder named 'counties'
        
        # assuming there's only one counties file in the zip, get its name
        counties_file = [name for name in z.namelist()]
        print(counties_file)

# export out wabasha & winona & olmstead county
arcpy.conversion.ExportFeatures("mn_county_boundaries", r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\counties", "CTY_ABBR = 'WABA' OR CTY_ABBR = 'WINO' OR CTY_ABBR = 'OLMS'")

# clip landuse data with county data
arcpy.analysis.Clip(
    in_features="landcover_landsat_tm_1990",
    clip_features="counties",
    out_feature_class=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\landcover_landsat_tm_19_Clip",
    cluster_tolerance=None
)

# make a dictionary for the .laz api urls
# chatgpt was used to suggest the basic architecture for constructing the for-loop
# results from chatgpt were edited and modified to suit the project. They did not work in the suggested form
folder = r'C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\laz'
laz_dict = {
    "wino1": 'https://resources.gisdata.mn.gov/pub/data/elevation/lidar/county/winona/laz/4342-30-62.laz',
    "wino2": 'https://resources.gisdata.mn.gov/pub/data/elevation/lidar/county/winona/laz/4342-30-63.laz',
    "wino3": 'https://resources.gisdata.mn.gov/pub/data/elevation/lidar/county/winona/laz/4342-30-64.laz',
    "wino4": 'https://resources.gisdata.mn.gov/pub/data/elevation/lidar/county/winona/laz/4342-31-64.laz',
    "wino5": 'https://resources.gisdata.mn.gov/pub/data/elevation/lidar/county/winona/laz/4342-31-63.laz',
    "wino6": 'https://resources.gisdata.mn.gov/pub/data/elevation/lidar/county/winona/laz/4342-31-62.laz',
    "wino7": 'https://resources.gisdata.mn.gov/pub/data/elevation/lidar/county/winona/laz/4342-29-63.laz',
    "wino8": 'https://resources.gisdata.mn.gov/pub/data/elevation/lidar/county/winona/laz/4342-29-64.laz',
    "waba1": 'https://resources.gisdata.mn.gov/pub/data/elevation/lidar/county/wabasha/laz/4342-28-59.laz',
    "waba2": 'https://resources.gisdata.mn.gov/pub/data/elevation/lidar/county/wabasha/laz/4342-28-60.laz',
    "waba3": 'https://resources.gisdata.mn.gov/pub/data/elevation/lidar/county/wabasha/laz/4342-28-61.laz',
    "waba4": 'https://resources.gisdata.mn.gov/pub/data/elevation/lidar/county/wabasha/laz/4342-28-62.laz',
    "waba5": 'https://resources.gisdata.mn.gov/pub/data/elevation/lidar/county/wabasha/laz/4342-29-59.laz',
    "waba6": 'https://resources.gisdata.mn.gov/pub/data/elevation/lidar/county/wabasha/laz/4342-29-60.laz',
    "waba7": 'https://resources.gisdata.mn.gov/pub/data/elevation/lidar/county/wabasha/laz/4342-29-61.laz',
    "waba8": 'https://resources.gisdata.mn.gov/pub/data/elevation/lidar/county/wabasha/laz/4342-29-62.laz'
    
}

# for-loop goes thru and opens all dictionary items
for key, url in laz_dict.items():
    response = requests.get(url, stream = True)
    
    if response.status_code == 200:
        # Save the data with the name of the dictionary key
        with open(os.path.join(folder, f"{key}.laz"), "wb") as file:
         file.write(response.content)
        print(os.path.join(folder, f"{key}.laz"))
    else:
        print(f"Failed to download data from {key}. Status code: {response.status_code}")

# convert laz to las

arcpy.conversion.ConvertLas(
    in_las=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\laz",
    target_folder=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\las",
    file_version="SAME_AS_INPUT",
    point_format="",
    compression="NO_COMPRESSION",
    las_options="REARRANGE_POINTS",
    out_las_dataset=None,
    define_coordinate_system="FILES_MISSING_PROJECTION",
    in_coordinate_system='PROJCS["datum_D_North_American_1983_HARN_UTM_Zone_15N",GEOGCS["GCS_datum_D_North_American_1983_HARN",DATUM["D_unknown",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["false_easting",500000.0],PARAMETER["false_northing",0.0],PARAMETER["central_meridian",-93.0],PARAMETER["scale_factor",0.9996],PARAMETER["latitude_of_origin",0.0],UNIT["Meter",1.0]],VERTCS["NAVD88 - Geoid03 (Meters)",VDATUM["unknown"],PARAMETER["Vertical_Shift",0.0],PARAMETER["Direction",1.0],UNIT["Meter",1.0]]'
)

# convert all las files to dem
# had a lot of trouble getting the for-loop to work for this so I just did it manually 

arcpy.conversion.LasDatasetToRaster(
    in_las_dataset="waba1.las",
    out_raster=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\waba1tif",
    value_field="ELEVATION",
    interpolation_type="BINNING AVERAGE LINEAR",
    data_type="FLOAT",
    sampling_type="CELLSIZE",
    sampling_value=10,
    z_factor=1
)

arcpy.conversion.LasDatasetToRaster(
    in_las_dataset="waba2.las",
    out_raster=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\waba2tif",
    value_field="ELEVATION",
    interpolation_type="BINNING AVERAGE LINEAR",
    data_type="FLOAT",
    sampling_type="CELLSIZE",
    sampling_value=10,
    z_factor=1
)

arcpy.conversion.LasDatasetToRaster(
    in_las_dataset="waba3.las",
    out_raster=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\waba3tif",
    value_field="ELEVATION",
    interpolation_type="BINNING AVERAGE LINEAR",
    data_type="FLOAT",
    sampling_type="CELLSIZE",
    sampling_value=10,
    z_factor=1
)

arcpy.conversion.LasDatasetToRaster(
    in_las_dataset="waba4.las",
    out_raster=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\waba4tif",
    value_field="ELEVATION",
    interpolation_type="BINNING AVERAGE LINEAR",
    data_type="FLOAT",
    sampling_type="CELLSIZE",
    sampling_value=10,
    z_factor=1
)

arcpy.conversion.LasDatasetToRaster(
    in_las_dataset="waba5.las",
    out_raster=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\waba5tif",
    value_field="ELEVATION",
    interpolation_type="BINNING AVERAGE LINEAR",
    data_type="FLOAT",
    sampling_type="CELLSIZE",
    sampling_value=10,
    z_factor=1
)

arcpy.conversion.LasDatasetToRaster(
    in_las_dataset="waba6.las",
    out_raster=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\waba6tif",
    value_field="ELEVATION",
    interpolation_type="BINNING AVERAGE LINEAR",
    data_type="FLOAT",
    sampling_type="CELLSIZE",
    sampling_value=10,
    z_factor=1
)

arcpy.conversion.LasDatasetToRaster(
    in_las_dataset="waba7.las",
    out_raster=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\waba7tif",
    value_field="ELEVATION",
    interpolation_type="BINNING AVERAGE LINEAR",
    data_type="FLOAT",
    sampling_type="CELLSIZE",
    sampling_value=10,
    z_factor=1
)

arcpy.conversion.LasDatasetToRaster(
    in_las_dataset="waba8.las",
    out_raster=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\waba8tif",
    value_field="ELEVATION",
    interpolation_type="BINNING AVERAGE LINEAR",
    data_type="FLOAT",
    sampling_type="CELLSIZE",
    sampling_value=10,
    z_factor=1
)

arcpy.conversion.LasDatasetToRaster(
    in_las_dataset="wino1.las",
    out_raster=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\wino1tif",
    value_field="ELEVATION",
    interpolation_type="BINNING AVERAGE LINEAR",
    data_type="FLOAT",
    sampling_type="CELLSIZE",
    sampling_value=10,
    z_factor=1
)

arcpy.conversion.LasDatasetToRaster(
    in_las_dataset="wino2.las",
    out_raster=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\wino2tif",
    value_field="ELEVATION",
    interpolation_type="BINNING AVERAGE LINEAR",
    data_type="FLOAT",
    sampling_type="CELLSIZE",
    sampling_value=10,
    z_factor=1
)

arcpy.conversion.LasDatasetToRaster(
    in_las_dataset="wino3.las",
    out_raster=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\wino3tif",
    value_field="ELEVATION",
    interpolation_type="BINNING AVERAGE LINEAR",
    data_type="FLOAT",
    sampling_type="CELLSIZE",
    sampling_value=10,
    z_factor=1
)

arcpy.conversion.LasDatasetToRaster(
    in_las_dataset="wino4.las",
    out_raster=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\wino4tif",
    value_field="ELEVATION",
    interpolation_type="BINNING AVERAGE LINEAR",
    data_type="FLOAT",
    sampling_type="CELLSIZE",
    sampling_value=10,
    z_factor=1
)

arcpy.conversion.LasDatasetToRaster(
    in_las_dataset="wino5.las",
    out_raster=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\wino5tif",
    value_field="ELEVATION",
    interpolation_type="BINNING AVERAGE LINEAR",
    data_type="FLOAT",
    sampling_type="CELLSIZE",
    sampling_value=10,
    z_factor=1
)

arcpy.conversion.LasDatasetToRaster(
    in_las_dataset="wino6.las",
    out_raster=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\wino6tif",
    value_field="ELEVATION",
    interpolation_type="BINNING AVERAGE LINEAR",
    data_type="FLOAT",
    sampling_type="CELLSIZE",
    sampling_value=10,
    z_factor=1
)

arcpy.conversion.LasDatasetToRaster(
    in_las_dataset="wino7.las",
    out_raster=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\wino7tif",
    value_field="ELEVATION",
    interpolation_type="BINNING AVERAGE LINEAR",
    data_type="FLOAT",
    sampling_type="CELLSIZE",
    sampling_value=10,
    z_factor=1
)

arcpy.conversion.LasDatasetToRaster(
    in_las_dataset="wino8.las",
    out_raster=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\wino8tif",
    value_field="ELEVATION",
    interpolation_type="BINNING AVERAGE LINEAR",
    data_type="FLOAT",
    sampling_type="CELLSIZE",
    sampling_value=10,
    z_factor=1
)



# merge tifs into one raster

arcpy.management.MosaicToNewRaster(
    input_rasters="wino8tif;wino7tif;wino6tif;wino5tif;wino4tif;wino3tif;wino2tif;wino1tif;waba8tif;waba7tif;waba6tif;waba5tif;waba4tif;waba3tif;waba2tif;waba1tif",
    output_location=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2",
    raster_dataset_name_with_extension="interestarea1",
    coordinate_system_for_the_raster='PROJCS["datum_D_North_American_1983_HARN_UTM_Zone_15N",GEOGCS["GCS_datum_D_North_American_1983_HARN",DATUM["D_unknown",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["false_easting",500000.0],PARAMETER["false_northing",0.0],PARAMETER["central_meridian",-93.0],PARAMETER["scale_factor",0.9996],PARAMETER["latitude_of_origin",0.0],UNIT["Meter",1.0]],VERTCS["NAVD88 - Geoid03 (Meters)",VDATUM["unknown"],PARAMETER["Vertical_Shift",0.0],PARAMETER["Direction",1.0],UNIT["Meter",1.0]]',
    pixel_type="8_BIT_UNSIGNED",
    cellsize=None,
    number_of_bands=1,
    mosaic_method="LAST",
    mosaic_colormap_mode="FIRST"
)



# create dory's starting point

# create feature class

feature_class_path = arcpy.management.CreateFeatureclass(
    out_path=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb",
    out_name="dory_start",
    geometry_type="POINT",
    template=None,
    has_m="DISABLED",
    has_z="DISABLED",
    spatial_reference='GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],VERTCS["NAVD88 - Geoid03 (Meters)",VDATUM["unknown"],PARAMETER["Vertical_Shift",0.0],PARAMETER["Direction",1.0],UNIT["Meter",1.0]];-400 -400 1000000000;-100000 10000;-100000 10000;8.98315284119521E-09;0.001;0.001;IsHighPrecision',
    config_keyword="",
    spatial_grid_1=0,
    spatial_grid_2=0,
    spatial_grid_3=0,
    out_alias=""
)

# create point

latitude = 44.127985  
longitude = -92.148796

point = arcpy.Point(longitude, latitude)

# insert the point into the feature class

with arcpy.da.InsertCursor(feature_class_path, ["SHAPE@"]) as cursor:
    cursor.insertRow([point])


# create dory's destination

# create feature class

feature_class_path = arcpy.management.CreateFeatureclass(
    out_path=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb",
    out_name="dory_end",
    geometry_type="POINT",
    template=None,
    has_m="DISABLED",
    has_z="DISABLED",
    spatial_reference='GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],VERTCS["NAVD88 - Geoid03 (Meters)",VDATUM["unknown"],PARAMETER["Vertical_Shift",0.0],PARAMETER["Direction",1.0],UNIT["Meter",1.0]];-400 -400 1000000000;-100000 10000;-100000 10000;8.98315284119521E-09;0.001;0.001;IsHighPrecision',
    config_keyword="",
    spatial_grid_1=0,
    spatial_grid_2=0,
    spatial_grid_3=0,
    out_alias=""
)

# create point

latitude = 44.0626553  
longitude = -92.044557

point = arcpy.Point(longitude, latitude)

# insert the point into the feature class

with arcpy.da.InsertCursor(feature_class_path, ["SHAPE@"]) as cursor:
    cursor.insertRow([point])


# fill dem

out_surface_raster = arcpy.sa.Fill(
    in_surface_raster="interestarea1",
    z_limit=None
)
out_surface_raster.save(r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\filled_dem")

# calculate slope

arcpy.ddd.Slope(
    in_raster="out_surface_raster",
    out_raster=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\Slope_filled1",
    output_measurement="DEGREE",
    z_factor=1,
    method="PLANAR",
    z_unit="METER",
    analysis_target_device="GPU_THEN_CPU"
)

# reclassify slope raster to integer classes

arcpy.ddd.Reclassify(
    in_raster="Slope_filled1",
    reclass_field="VALUE",
    remap="0 1.720000 1;1.720000 3.430000 2;3.430000 5.710000 3;5.710000 8.530000 4;8.530000 11.300000 5;11.300000 14.040000 6;14.040000 16.700000 7;16.700000 21.800000 8;21.800000 30.960000 9;30.960000 45 10;45 90 11",
    out_raster=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\slope_class",
    missing_values="DATA"
)

# create cost-distance

out_distance_raster = arcpy.sa.CostDistance(
    in_source_data="dory_start",
    in_cost_raster="slope_class",
    maximum_distance=None,
    out_backlink_raster=None,
    source_cost_multiplier=None,
    source_start_cost=None,
    source_resistance_rate=None,
    source_capacity=None,
    source_direction=""
)
out_distance_raster.save(r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\CostDis_dory1")

# create backlink raster

out_backlink_raster = arcpy.sa.CostBackLink(
    in_source_data="dory_start",
    in_cost_raster="slope_class",
    maximum_distance=None,
    out_distance_raster=None,
    source_cost_multiplier=None,
    source_start_cost=None,
    source_resistance_rate=None,
    source_capacity=None,
    source_direction=""
)
out_backlink_raster.save(r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\CostBac_dory1")

# conduct cost-path

out_raster = arcpy.sa.CostPath(
    in_destination_data="dory_end",
    in_cost_distance_raster="out_distance_raster",
    in_cost_backlink_raster="out_backlink_raster",
    path_type="EACH_CELL",
    destination_field="OBJECTID",
    force_flow_direction_convention="INPUT_RANGE"
)
out_raster.save(r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\dorypath1")

# turn land use polygon to raster

arcpy.conversion.PolygonToRaster(
    in_features="landcover_landsat_tm_19_Clip",
    value_field="XLUSE_CODE",
    out_rasterdataset=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\landcover_landsat_tm_19_Clip_PolygonToRaster",
    cell_assignment="CELL_CENTER",
    priority_field="NONE",
    cellsize=280,
    build_rat="BUILD"
)

# clip landuse to interest area

# when i use this tool i get the error "ERROR 160326: The table already exists."
# the ESRI documentation on this error code is basically "we dont know what this error means"
# so i just exported raster extent of the landuse raster to save processing time
# you can still perform all the other steps with the full-sized raster, it will just take longer

arcpy.management.Clip(
    in_raster="landcover_landsat_tm_19_Clip_PolygonToRaster",
    rectangle="564952.77 4875737.57 580112.77 4889657.57",
    out_raster=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\landcover_landsat_tm_19_Clip",
    in_template_dataset="interestarea1",
    nodata_value="127",
    clipping_geometry="NONE",
    maintain_clipping_extent="NO_MAINTAIN_EXTENT"
)

# reclassify landuse bc there are too many classes 
# combine cultivated land class with farmsteads and rural residences

arcpy.ddd.Reclassify(
    in_raster="landcoverInterest.tif",
    reclass_field="XLUSE_CODE",
    remap="'Deciduous Forest' 1;Grassland 2;'Cultivated Land' 3;'Farmsteads and Rural Residences' 3;'Urban and Industrial' 4;'Other Rural Developments' 5;'Grassland-Shrub-Tree (deciduous)' 6;Water 7;'Gravel Pits and Open Mines' 8;Wetlands 10;' ' 11",
    out_raster=r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\Reclass_landcover1",
    missing_values="DATA"
)

# weight the relevant variables appropriately 
# this version weighs slope and landuse factors evenly, 50-50

out_raster = arcpy.sa.WeightedOverlay(
    in_weighted_overlay_table=r"('C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\Reclass_landcover1' 50 'Value' (1 9; 2 9; 3 1; 4 9; 5 2; 6 9; 7 3; 8 9; 10 9; 11 9; NODATA NODATA); 'C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\slope_class' 50 'Value' (1 9; 2 8; 3 7; 4 6; 5 5; 6 4; 7 3; 8 2; 9 1; 10 1; 11 1; NODATA NODATA));1 9 1"
)
out_raster.save(r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\Weighte_Recl1")

# cost distance with weights v1

out_distance_raster = arcpy.sa.CostDistance(
    in_source_data="dory_start",
    in_cost_raster="out_raster",
    maximum_distance=None,
    out_backlink_raster=None,
    source_cost_multiplier=None,
    source_start_cost=None,
    source_resistance_rate=None,
    source_capacity=None,
    source_direction=""
)
out_distance_raster.save(r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\CostDis_dory2")

# cost backlink with weights v1

out_backlink_raster = arcpy.sa.CostBackLink(
    in_source_data="dory_start",
    in_cost_raster="out_raster",
    maximum_distance=None,
    out_distance_raster=None,
    source_cost_multiplier=None,
    source_start_cost=None,
    source_resistance_rate=None,
    source_capacity=None,
    source_direction=""
)
out_backlink_raster.save(r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\CostBac_dory2")

# cost_path weighted v1

out_raster = arcpy.sa.CostPath(
    in_destination_data="dory_end",
    in_cost_distance_raster="out_distance_raster",
    in_cost_backlink_raster="out_backlink_raster",
    path_type="EACH_CELL",
    destination_field="OBJECTID",
    force_flow_direction_convention="INPUT_RANGE"
)
out_raster.save(r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\CostPat_dory1")

# weight the relevant variables appropriately 
# this version weighs slope more heavily than land-use, 80-20

out_raster2 = arcpy.sa.WeightedOverlay(
    in_weighted_overlay_table=r"('C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\Reclass_landcover1' 80 'Value' (1 9; 2 9; 3 1; 4 9; 5 2; 6 9; 7 3; 8 9; 10 9; 11 9; NODATA NODATA); 'C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\slope_class' 20 'Value' (1 9; 2 8; 3 7; 4 6; 5 5; 6 4; 7 3; 8 2; 9 1; 10 1; 11 1; NODATA NODATA));1 9 1"
)
out_raster2.save(r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\Weighte_Recl2")

# cost distance with weights v2

out_distance_raster2 = arcpy.sa.CostDistance(
    in_source_data="dory_start",
    in_cost_raster="out_raster2",
    maximum_distance=None,
    out_backlink_raster=None,
    source_cost_multiplier=None,
    source_start_cost=None,
    source_resistance_rate=None,
    source_capacity=None,
    source_direction=""
)
out_distance_raster2.save(r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\CostDis_dory3")

# cost backlink with weights v2

out_backlink_raster2 = arcpy.sa.CostBackLink(
    in_source_data="dory_start",
    in_cost_raster="out_raster2",
    maximum_distance=None,
    out_distance_raster=None,
    source_cost_multiplier=None,
    source_start_cost=None,
    source_resistance_rate=None,
    source_capacity=None,
    source_direction=""
)
out_backlink_raster2.save(r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\CostBac_dory3")

# cost_path weighted v2

out_raster2 = arcpy.sa.CostPath(
    in_destination_data="dory_end",
    in_cost_distance_raster="out_distance_raster2",
    in_cost_backlink_raster="out_backlink_raster2",
    path_type="EACH_CELL",
    destination_field="OBJECTID",
    force_flow_direction_convention="INPUT_RANGE"
)
out_raster2.save(r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\CostPat_dory2")

# weight the relevant variables appropriately 
# this version weighs land-use more heavily than slope, 80-20

out_raster3 = arcpy.sa.WeightedOverlay(
    in_weighted_overlay_table=r"('C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\Reclass_landcover1' 20 'Value' (1 9; 2 9; 3 1; 4 9; 5 2; 6 9; 7 3; 8 9; 10 9; 11 9; NODATA NODATA); 'C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\slope_class' 80 'Value' (1 9; 2 8; 3 7; 4 6; 5 5; 6 4; 7 3; 8 2; 9 1; 10 1; 11 1; NODATA NODATA));1 9 1"
)
out_raster3.save(r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\Weighte_Recl3")

# cost distance with weights v3

out_distance_raster3 = arcpy.sa.CostDistance(
    in_source_data="dory_start",
    in_cost_raster="out_raster3",
    maximum_distance=None,
    out_backlink_raster=None,
    source_cost_multiplier=None,
    source_start_cost=None,
    source_resistance_rate=None,
    source_capacity=None,
    source_direction=""
)
out_distance_raster3.save(r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\CostDis_dory4")

# cost backlink with weights v3

out_backlink_raster3 = arcpy.sa.CostBackLink(
    in_source_data="dory_start",
    in_cost_raster="out_raster3",
    maximum_distance=None,
    out_distance_raster=None,
    source_cost_multiplier=None,
    source_start_cost=None,
    source_resistance_rate=None,
    source_capacity=None,
    source_direction=""
)
out_backlink_raster3.save(r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\CostBac_dory4")

# cost_path weighted v3

out_raster3 = arcpy.sa.CostPath(
    in_destination_data="dory_end",
    in_cost_distance_raster="out_distance_raster3",
    in_cost_backlink_raster="out_backlink_raster3",
    path_type="EACH_CELL",
    destination_field="OBJECTID",
    force_flow_direction_convention="INPUT_RANGE"
)
out_raster3.save(r"C:\Users\18284\Documents\ArcGIS\Projects\arc1lab2\arc1lab2.gdb\CostPat_dory3")


