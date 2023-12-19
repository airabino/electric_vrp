import warnings
warnings.filterwarnings("ignore")

import os
import sys
import time
import argparse
import numpy as np
import pandas as pd
import geopandas as gpd
import pickle as pkl
import matplotlib.pyplot as plt

import src
from src.utilities import CondPrint

str_color='\r\033[32m'


# ArgumentParser object configuration
parser = argparse.ArgumentParser(
	prog = 'module: compute_adjacency',
	description = (
		'Loads vertices from .json and computes adjacency using Dijsktra routing ' +
		'on a network defined by a roadmap pickle file'
		),
	)

parser.add_argument(
	'-i', '--input_file',
	help = 'Required: vertices .json file',
	required = True,
	)

parser.add_argument(
	'-o', '--output_file',
	help = 'Output file for vertices .json, default is same as input file',
	default = 'vertices.json',
	)

parser.add_argument(
	'-r', '--roadmap_file',
	help = 'Roadmap file for use in routing - can be a shapefile or pickle',
	default = 'Data/RoadMap/roadmap.shp',
	)

parser.add_argument(
	'-a', '--all_vertices',
	help = 'Whether to compute adjacency for all vertices or just those withh Added == 0',
	action = 'store_true',
	)

parser.add_argument(
	'-c', '--cutoff',
	help = 'Cutoff distance for routing - default is 300 km',
	default = 300e3,
	)

parser.add_argument(
	'-v', '--verbose',
	help = 'Optional status printing',
	action = 'store_true',
	)

if __name__ == "__main__":

	t0 = time.time()

	args = parser.parse_args(sys.argv[1:])
	CondPrint(str_color + '\n' + 'Module compute_adjacency', args.verbose)

	# print(args)

	# Loading in RoadMap
	t1 = time.time()
	CondPrint('Loading RoadMap ... ', args.verbose, end = '', flush = True)

	filename,extension = args.roadmap_file.split('.')

	if extension == 'shp':

		roadmap, gdf = src.network.RoadMap_From_Shapefile(
			filepath = args.roadmap_file,
			savepath = filename + '.pkl',
			)

	elif extension == 'pkl':

		roadmap, gdf = src.network.RoadMap_From_Pickle(args.roadmap_file)

	CondPrint(
		f'Done: {time.time()-t1:.3f} seconds',
		args.verbose
		)

	# Loading vertices
	t1 = time.time()
	CondPrint('Loading vertices ... ', args.verbose, end = '', flush = True)

	vertices = src.store.Load(args.input_file)

	CondPrint(
		f'Done: {time.time()-t1:.3f} seconds',
		args.verbose
		)

	# Routing
	t1 = time.time()
	CondPrint('Routing ... ', args.verbose, end = '', flush = True)

	vertices_with_adjacency = src.network.Add_Locations(
		roadmap,
		vertices,
		cutoff = 300e3,
		fields = ['time', 'length'],
		verbose = False,
		add_all = args.all_vertices,
		)

	CondPrint(
		f'Done: {time.time()-t1:.3f} seconds',
		args.verbose
		)

	#Writing to file
	CondPrint('Writing to file ... ', args.verbose, end = '', flush = True)
	src.store.Write(
		vertices_with_adjacency,
		filename = args.output_file,
		)

	CondPrint(
		f'Done: {time.time()-t1:.3f} seconds' + '\n',
		args.verbose
		)