Description:

Module for solving multi-depot Vehicle Routing Problem (VRP) built for UC Davis CEC
data collection project but generally applicable.

This module uses a road map based off of arcgis opendata roads standard using
North American roads. Download at:

https://opendata.arcgis.com/api/v3/datasets/169745624b194c1d913b9d9fb41a3f76_0/downloads/data?format=shp&spatialRefId=3857&where=1%3D1

Because the above file is very large and CEC data collection takes place in California the
map provided in this repository only contains California - however code will run on any
road map of the above format.

Function:

Serves to find optimal VRP solution for a set of vehicles to a set of destinations from a set
of depots. In general all locations (destinations and depots) will be defined in a .json
containing, at minimum, coordinates, and all other information will be defined in a separate
.json. CEC destinations and depots are given in .csv files and code is included to create a
.json file from these. Source files contained in src. Package requirements in src/requirements.txt. Tested on Python 3.11.*

Starting point can be a (or multiple) vertices .csv or .json  and a paramerters .json -
refer to example_vertices.csv, example_vertices.json, and example_parameters.json.

Overall output is a .json file containing information for optimal routes.

Top level scripts are:

1. vertices_from_csv.py:

Creates an "empty" - (meaning that adjecency has not been calculated) .json for all vertices
containing the fields defined either as vertex_fields in the parameters .json or using the
-f command line option. Should run quickly.

Example(s):

All vertices:

python vertices_from_csv.py -i 'UCDavis_L2_Weighted_Sample.csv' 'UCDavis_DCFC_Weighted_Sample.csv' 'Depots.csv' -o vertices.json -p w -v

Selection by county:

python vertices_from_csv.py -i 'UCDavis_L2_Weighted_Sample.csv' 'UCDavis_DCFC_Weighted_Sample.csv' 'Depots.csv' -k County Sacremento 'San Joaquin' Amador Yolo Solano 'El Dorado' 'Contra Costa' Sutter Pacer -o vertices.json -p w -v

Call with -h/--help for options.

2. add_vertex_fields.py:

Adds fields from csv to existing vertices .json. Should run quickly.

Example(s):

python add_vertex_fields.py -i 'UCDavis_L2_Weighted_Sample.csv' 'UCDavis_DCFC_Weighted_Sample.csv' 'Depots.csv' -j vertices.json -f 'EV Network Clean' -v

Call with -h/--help for options.

3. compute_adjacency.py:

Computes edge values for all O/D combinations in vertices .json. Run-time scales
exponentially with number of vertices.

Example(s):

Compute all edges:

python compute_adjacency.py -i vertices.json -r Data/RoadMap/roadmap.pkl -v -a

Compute non-added edges:

python compute_adjacency.py -i vertices.json -r Data/RoadMap/roadmap.pkl -v

Call with -h/--help for options.

4. compute_routes.py:

Computes optimal routes for vertices and parameters and produces routes .json.
Run-time scales exponentially with number of vertices.

Example(s):

python compute_routes.py -i vertices.json -o routes.json -p parameters.json -v

Call with -h/--help for options.