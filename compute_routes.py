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


#ArgumentParser objecct configuration
parser = argparse.ArgumentParser(
	prog = 'module: compute_routes',
	description = (
		'Computes optimal routes for vertices'
		),
	)

parser.add_argument(
	'-i', '--input_file',
	nargs = '+',
	help = 'Required: vertices .json file',
	required = True,
	)

parser.add_argument(
	'-o', '--output_file',
	help = 'Output file for routes, default is \'routes.json\'',
	default = 'routes.json'
	)

parser.add_argument(
	'-p', '--parameters_file',
	help = 'Required: .json file containing vertices',
	)

parser.add_argument(
	'-f', '--fields',
	help = (
		'Fields to add to vertices' +
		'If a keyword contains spaces use quotes ex: \'EV Network Clean\''
		),
	nargs = '+',
	)

parser.add_argument(
	'-v', '--verbose',
	help = 'Optional status printing',
	action='store_true',
	)

def RawRoutes(graph,vehicle_adjacency,parameters,args):

	vehicles=list(parameters['vehicles'].keys())
	depots=parameters['depot_vertices']

	raw_routes={}

	t0=time.time()

	for vehicle in vehicles:

		raw_routes[vehicle]={}

		for depot in depots:

			t1=time.time()
			CondPrint(f'Routing for {vehicle} from {depot} ... ', args.verbose, end='')

			adjacency=vehicle_adjacency[vehicle][depot]

			raw_routes[vehicle][depot]=src.router.ProduceRoutesVehicleDepot(
				graph,vehicle,depot,parameters,adjacency)

			CondPrint(f'Done, {time.time()-t1:.4f} seconds elapsed', args.verbose)

	return raw_routes

if __name__ == "__main__":

	t0 = time.time()

	args = parser.parse_args(sys.argv[1:])
	CondPrint(str_color + '\n' + 'Module compute_routes', args.verbose)

	# Loading vertices into graph
	t1 = time.time()
	CondPrint('Loading vertices as graph ... ', args.verbose, end = '', flush = True)
	vertices=src.store.Load('vertices.json')
	graph=src.network.NX_Graph_From_Vertices(vertices)

	CondPrint(f'Done: {time.time()-t1:.3f} seconds', args.verbose)

	# Loading parameters
	t1 = time.time()
	CondPrint('Loading parameters ... ', args.verbose, end = '', flush = True)
	parameters = src.store.Load(args.parameters_file)

	CondPrint(f'Done: {time.time()-t1:.3f} seconds', args.verbose)

	# Producing adjacency matrices
	t1 = time.time()
	CondPrint('Producing adjacency information ... ', args.verbose, end = '', flush = True)
	vehicle_adjacency,vehicle_nodes=src.router.ProcessInputs(graph, parameters)
	CondPrint(f'Done: {time.time()-t1:.3f} seconds', args.verbose)

	# Computing routes for each vehicle and depot
	t1 = time.time()
	CondPrint('Computing raw routes:', args.verbose, flush = True)
	raw_routes=RawRoutes(graph, vehicle_adjacency, parameters, args)
	CondPrint(f'Done: {time.time()-t1:.3f} seconds', args.verbose)

	# Adding route information
	t1 = time.time()
	CondPrint('Adding route information ... ', args.verbose, end = '', flush = True)
	vehicles=list(parameters['vehicles'].keys())
	depots=parameters['depot_vertices']

	if args.fields is not None:

		fields = args.fields

	else:

		fields=parameters['vertex_fields']

	full_routes={}

	for vehicle in vehicles:

		full_routes[vehicle]={}

		for depot in depots:

			full_routes[vehicle][depot]=src.post_processing.AddRouteInformation(
				graph, raw_routes[vehicle][depot], fields)

	CondPrint(f'Done: {time.time()-t1:.3f} seconds', args.verbose)

	# Writing to file
	CondPrint('Writing to file ... ', args.verbose, end = '', flush = True)
	src.store.Write(
		vertices,
		filename = args.output_file,
		permission = 'w'
		)

	CondPrint(f'Done: {time.time()-t1:.3f} seconds', args.verbose)

	CondPrint('\n' + f'Done: {time.time()-t0:.3f} seconds' + '\n', args.verbose)


