Description:

Module for solving multi-depot Vehicle Routing Problem (VRP) built for UC Davis CEC data collection project but generally applicable.

This module provides a road map based off of arcgis opendata roads standard using North American roads. Download at:

https://opendata.arcgis.com/api/v3/datasets/169745624b194c1d913b9d9fb41a3f76_0/downloads/data?format=shp&spatialRefId=3857&where=1%3D1

Because the above file is very large and CEC data collection takes place in California the map provided in this repository only contains California.

The module stores graphs as JSON using the Node-Link Graph (NLG) format. The graph on which the VRP will be solved is called the graph. If needed a second graph, called atlas, can be used to compute adjacecny for graph (for example graph containing nodes at coordinates and atlas being a road map). Several parameters files are also JSONs.

Usage:

Ultimate output is a .json file containing information for optimal routes. There are several paths which can be followed to get outputs.

1. Graph NLG JSON + parameters JSON -> routes JSON

Top Level Functions: compute_routes.py

2. (Nodes CSV + parameters JSON) + Atlas NLG JSON -> Graph NLG JSON + parameters JSON -> routes JSON

Top Level Functions: graph_from_csv.py, add_adjacency.py, compute_routes.py

3. (Nodes CSV + parameters JSON) + (Atlas Shapefile + parameters JSON) -> Graph NLG JSON + parameters JSON -> routes JSON

Top Level Functions: graph_from_csv.py, graph_from_shapefile.py, add_adjacency.py, compute_routes.py

Example input and parameters files are in /CEC/

4. In order to remove nddes from routing they should be marekd as visited using mark_visited.py

Top level scripts are:

1. graph_from_csv.py:

Creates an "empty" - (meaning that adjecency has not been calculated) NLG JSON from CSV(s)

Example(s):

All vertices:

python graph_from_csv.py -p CEC/parameters_cec_csv.json -v

Selection by county:

python graph_from_csv.py -p CEC/parameters_cec_csv.json -v -k County Sacremento 'San Joaquin' Amador Yolo Solano 'El Dorado' 'Contra Costa' Sutter Pacer

Call with -h/--help for options.

2. graph_from_shapefile.py:

Creates a NLG JSON from a shapefile

Example(s):

python graph_from_shapefile.py -p  CEC/parameters_cec_shp.json -v

Call with -h/--help for options.

3. add_adjacency.py:

Computes edge values for all O/D combinations in NLG JSON subject to limits. Run-time scales exponentially with number of vertices.

Example(s):

python add_adjacency.py -p CEC/parameters_cec_adj.json -v

Call with -h/--help for options.

4. compute_routes.py:

Solves VRP and produces optimal routes

Example(s):

python compute_routes.py -p CEC/parameters_cec_router.json -v

Call with -h/--help for options.

5. mark_visited.py:

Marks nodes as visited - visited nodes will not be included in routing

Example(s):

With nodes via commad line:

python mark_visited.py -g graph.json -n 183850 221160

With nodes in file:

python mark_visited.py -g graph.json -nf example_visited_nodes.json

Call with -h/--help for options.