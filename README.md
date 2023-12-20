Repository for building a graph for VRP

This repository contains two top-level modules which are as follows:

vertices_from_csv.py - module for taking data from formatted CSV files and creating
a vertices .json without adjacency. Call with --help for options.

Example Call:

All vertices

python vertices_from_csv.py -i 'UCDavis_L2_Weighted_Sample.csv' 'UCDavis_DCFC_Weighted_Sample.csv' 'Depots.csv' -o vertices.json -p w -v

Selection by county

python vertices_from_csv.py -i 'UCDavis_L2_Weighted_Sample.csv' 'UCDavis_DCFC_Weighted_Sample.csv' 'Depots.csv' -k County Sacremento 'San Joaquin' Amador Yolo Solano 'El Dorado' 'Contra Costa' Sutter Pacer -o vertices.json -p w -v

compute_adjacency.py - module for computing adjacency. Call with --help for options.

Example Call:

Compute all edges

python compute_adjacency.py -i vertices.json -r Data/RoadMap/roadmap.pkl -v -a

Compute non-added edges

python compute_adjacency.py -i vertices.json -r Data/RoadMap/roadmap.pkl -v