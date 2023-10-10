#import packages
import requests
import json
import os
import zipfile
import pprint
from io import BytesIO
import arcpy
import csv

# NDAWN api request
ndawn_url = "https://ndawn.ndsu.nodak.edu/current-map.json?cs=0"
response = requests.get(ndawn_url)
data = json.loads(response.text)

station_coordinates_data = data["im"]
pprint.pprint(station_coordinates_data[0:5])

# Define the coordinate system for WGS 1984 

coord_system = arcpy.SpatialReference(4326)  # 4326 is the code for WGS 1984 
arcpy.management.CreateFeatureclass("","NDAWN_RAINFALL","POINT", spatial_reference=coord_system)
arcpy.management.CreateFeatureclass("","NDAWN_EVAPORATION","POINT", spatial_reference=coord_system)
#[rowarcpy.da.SearchCursor("NDAWN_RAINFALL","*")]

# Set the coordinate system for the feature class
arcpy.management.DefineProjection("NDAWN_RAINFALL", coord_system)
arcpy.management.DefineProjection("NDAWN_EVAPORATION", coord_system)

arcpy.management.AddField("NDAWN_RAINFALL","Post_Name","STRING")
arcpy.management.AddField("NDAWN_RAINFALL","Latitude","DOUBLE")
arcpy.management.AddField("NDAWN_RAINFALL","Longitude","DOUBLE")

arcpy.management.AddField("NDAWN_RAINFALL","Year","DOUBLE")
arcpy.management.AddField("NDAWN_RAINFALL","Elevation","DOUBLE")
arcpy.management.AddField("NDAWN_RAINFALL","Total_Monthly_Rainfall","DOUBLE")
#arcpy.management.AddField("NDAWN_RAINFALL","Total_Monthly_Evaporation","DOUBLE")

ndawn_url_2 = """https://ndawn.ndsu.nodak.edu/table.csv?station=78&station=111&station=98&station=162&station=174&station=142&station=164&station=138&station=161&station=9&station=160&station=159&station=10&station=118&station=56&station=165&station=11&station=12&station=58&station=13&station=84&station=55&station=179&station=7&station=186&station=87&station=14&station=15&station=96&station=191&station=16&station=201&station=137&station=124&station=143&station=17&station=85&station=140&station=134&station=18&station=136&station=65&station=104&station=99&station=192&station=19&station=129&station=20&station=101&station=166&station=178&station=81&station=21&station=97&station=22&station=75&station=184&station=2&station=172&station=139&station=158&station=23&station=157&station=62&station=86&station=24&station=89&station=126&station=167&station=93&station=183&station=90&station=25&station=83&station=107&station=156&station=77&station=26&station=155&station=70&station=127&station=144&station=27&station=173&station=132&station=28&station=195&station=185&station=29&station=30&station=154&station=31&station=187&station=102&station=32&station=119&station=4&station=80&station=33&station=59&station=153&station=105&station=82&station=34&station=198&station=72&station=135&station=35&station=76&station=120&station=141&station=109&station=36&station=79&station=193&station=71&station=37&station=38&station=189&station=39&station=130&station=73&station=188&station=40&station=41&station=54&station=69&station=194&station=145&station=113&station=128&station=42&station=43&station=103&station=171&station=116&station=196&station=88&station=114&station=3&station=163&station=200&station=64&station=115&station=168&station=67&station=175&station=146&station=170&station=197&station=44&station=133&station=106&station=100&station=121&station=45&station=46&station=61&station=66&station=181&station=74&station=60&station=199&station=125&station=176&station=177&station=8&station=180&station=204&station=47&station=122&station=108&station=5&station=152&station=48&station=151&station=147&station=68&station=169&station=49&station=50&station=91&station=182&station=117&station=63&station=150&station=51&station=6&station=52&station=92&station=112&station=131&station=123&station=95&station=53&station=203&station=190&station=57&station=149&station=148&station=202&station=110&variable=ydtpet&ttype=yearly"""

response = requests.get(ndawn_url_2)
reader = csv.reader(response.text.split('\n'), delimiter=',')
        
with arcpy.da.InsertCursor("NDAWN_RAINFALL",["SHAPE@XY","Post_Name","Latitude","Longitude","Year","Elevation","Total_Monthly_Rainfall"]) as cursor:
    for i, line in enumerate(reader):
        if (i>6) and (len(line)>6):
            cursor.insertRow([arcpy.Point(line[2], line[1]), line[0], line[1], line[2],line[4],line[3],line[5]])

arcpy.management.AddField("NDAWN_EVAPORATION","Post_Name","STRING")
arcpy.management.AddField("NDAWN_EVAPORATION","Latitude","DOUBLE")
arcpy.management.AddField("NDAWN_EVAPORATION","Longitude","DOUBLE")

arcpy.management.AddField("NDAWN_EVAPORATION","Year","DOUBLE")
arcpy.management.AddField("NDAWN_EVAPORATION","Elevation","DOUBLE")
arcpy.management.AddField("NDAWN_EVAPORATION","Total_Monthly_Evaporation","DOUBLE")

ndawn_url_3 = """https://ndawn.ndsu.nodak.edu/table.csv?station=78&station=111&station=98&station=162&station=174&station=142&station=164&station=138&station=161&station=9&station=160&station=159&station=10&station=118&station=56&station=165&station=11&station=12&station=58&station=13&station=84&station=55&station=179&station=7&station=186&station=87&station=14&station=15&station=96&station=191&station=16&station=201&station=137&station=124&station=143&station=17&station=85&station=140&station=134&station=18&station=136&station=65&station=104&station=99&station=192&station=19&station=129&station=20&station=101&station=166&station=178&station=81&station=21&station=97&station=22&station=75&station=184&station=2&station=172&station=139&station=158&station=23&station=157&station=62&station=86&station=24&station=89&station=126&station=167&station=93&station=183&station=90&station=25&station=83&station=107&station=156&station=77&station=26&station=155&station=70&station=127&station=144&station=27&station=173&station=132&station=28&station=195&station=185&station=29&station=30&station=154&station=31&station=187&station=102&station=32&station=119&station=4&station=80&station=33&station=59&station=153&station=105&station=82&station=34&station=198&station=72&station=135&station=35&station=76&station=120&station=141&station=109&station=36&station=79&station=193&station=71&station=37&station=38&station=189&station=39&station=130&station=73&station=188&station=40&station=41&station=54&station=69&station=194&station=145&station=113&station=128&station=42&station=43&station=103&station=171&station=116&station=196&station=88&station=114&station=3&station=163&station=200&station=64&station=115&station=168&station=67&station=175&station=146&station=170&station=197&station=44&station=133&station=106&station=100&station=121&station=45&station=46&station=61&station=66&station=181&station=74&station=60&station=199&station=125&station=176&station=177&station=8&station=180&station=204&station=47&station=122&station=108&station=5&station=152&station=48&station=151&station=147&station=68&station=169&station=49&station=50&station=91&station=182&station=117&station=63&station=150&station=51&station=6&station=52&station=92&station=112&station=131&station=123&station=95&station=53&station=203&station=190&station=57&station=149&station=148&station=202&station=110&variable=ydr&ttype=yearly"""

response = requests.get(ndawn_url_3)
reader = csv.reader(response.text.split('\n'), delimiter=',')
        
with arcpy.da.InsertCursor("NDAWN_EVAPORATION",["SHAPE@XY","Post_Name","Latitude","Longitude","Year","Elevation","Total_Monthly_Evaporation"]) as cursor:
    for i, line in enumerate(reader):
        if (i>6) and (len(line)>6):
            cursor.insertRow([arcpy.Point(line[2], line[1]), line[0], line[1], line[2],line[4],line[3],line[5]])


      
# join the two tables based on latitude
ndawn_joined_table = arcpy.management.AddJoin("NDAWN_RAINFALL","Latitude", "NDAWN_EVAPORATION","Latitude")
arcpy.management.CopyFeatures(ndawn_joined_table, "ndawnjoin")

# set projected coordinate system to utm zone 15n

zone15_coord_system = arcpy.SpatialReference(2027)

arcpy.management.Project("NDAWN_RAINFALL","NDAWN_RAINFALL_Z15", zone15_coord_system)
arcpy.management.Project("NDAWN_EVAPORATION","NDAWN_EVAPORATION_Z15", zone15_coord_system)
arcpy.management.Project("ndawnjoin","ndawnjoin_z15", zone15_coord_system)

# add table to geodatabase
arcpy.conversion.FeatureClassToGeodatabase('ndawnjoin', 'C:/Users/18284/Documents/ArcGIS/Projects')


# google places api request
api_key = "AIzaSyCgXMl2s-PTJ_yalvvc8rECMRLn5hZ5WN4"
request_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id=ChIJrTLr-GyuEmsRBfy61i59si0&fields=address_components&key={api_key}"
data = requests.get(request_url)
pprint.pprint(json.loads(data.content))

mn_gsc_api_url = "https://gisdata.mn.gov/api/3/action"

# MN geospatial commons api search datasets request

search_datasets_url = mn_gsc_api_url + "/package_search"
query = "Land Surface Temperature"
request_url = search_datasets_url + f"?q={query}"
response = requests.get(request_url, verify=False) # verify=False disables SSL certification validation which makes it mad but i cant get it to work without disabling it
response_data = json.loads(response.text)
found_dataset_names = [dataset["title"] for dataset in response_data["result"]["results"]]
print(found_dataset_names)

# MN geospatial commons api get dataset request

first_dataset_result_id = response_data["result"]["results"][0]["id"] # grab dataset that is first in returned dataset results
get_dataset_url = mn_gsc_api_url + "/package_show"
id = first_dataset_result_id
request_url = get_dataset_url + f"?id={id}"
response = requests.get(request_url, verify=False) # again disabling ssl cert validation
response_data = json.loads(response.text)
resources = response_data["result"]["resources"]
raw_zip_dataset_file_download_url = [resource for resource in resources if resource["resource_type"] == "fgdb"][0]["url"]
print(raw_zip_dataset_file_download_url)

response = requests.get(raw_zip_dataset_file_download_url)
# check response.status_code to see if download was successful, should return '200'
if response.status_code == 200:
    # Open zipfile
    with zipfile.ZipFile(BytesIO(response.content)) as z:
        # extract contents of zipfile
        z.extractall('fgdb_data') # extracts contents into a folder named 'fgdb_data'
        
        # assuming there's only one fgdb file in the zip, get its name
        fgdb_file = [name for name in z.namelist()]
        print(fgdb_file)


