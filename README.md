Description:

Module for solving multi-depot Vehicle Routing Problem (VRP) built for UC Davis CEC data collection project.

This module provides a road map based off of arcgis opendata roads standard using North American roads. Download at:

https://opendata.arcgis.com/api/v3/datasets/169745624b194c1d913b9d9fb41a3f76_0/downloads/data?format=shp&spatialRefId=3857&where=1%3D1

Usage:

1. Creating the empty graph from csv files:

python graph_from_csv.py -p Inputs/parameters_csv.json

2. Create depot subgraphs:

python depot_subgraphs.py -p Inputs/parameters_subgraph.json

3. Generating routes:

python generate_routes.py -p Inputs/parameters_routes.json