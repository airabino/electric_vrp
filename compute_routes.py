import warnings
warnings.filterwarnings("ignore")

import sys
import time
import json
import argparse
import pandas as pd


import src
from src.utilities import CondPrint
from src.progress_bar import ProgressBar

str_color = '\033[1m\033[38;5;34m\033[48;5;0m'

#ArgumentParser objecct configuration
parser = argparse.ArgumentParser(
	prog = 'module: compute_routes',
	description = (
		'Solves Vehicle Routing Problem (VRP) for graph and parameters'
		),
	)

parser.add_argument(
	'-g', '--graph_file',
	help = 'JSON file storing NLG for graph with links',
	)

parser.add_argument(
	'-o', '--output_file',
	help = 'Output file for routes .json',
	default = 'routes.json',
	)

parser.add_argument(
	'-v', '--verbose',
	help = 'Optional status printing',
	action='store_true',
	)

parser.add_argument(
	'-p', '--parameters_file',
	help = 'JSON containing inputs for VRP',
	required = True,
	)

if __name__ == "__main__":

	t0 = time.time()

	args = vars(parser.parse_args(sys.argv[1:]))
	CondPrint(str_color + '\n' + 'Module compute_routes' + '\n', args['verbose'])

	CondPrint('Loading parameters file', args['verbose'])
	with open(args['parameters_file'], 'r') as file:

		parameters = json.load(file)

	for key in parameters.keys():

		args[key] = parameters[key]

	CondPrint('Loading graph', args['verbose'])
	graph = src.graph.graph_from_json(args['graph_file'])

	CondPrint('Creating routing inputs', args['verbose'])
	cases = src.router.produce_routing_inputs(graph, parameters)

	CondPrint('Computing raw routes\n', args['verbose'])
	final_routes = []
	for key in ProgressBar(list(cases.keys()), end_color = ''):

		case = cases[key]

		raw_routes, success = src.router.router(case)

		routes = src.router.route_information(graph, raw_routes, parameters['route_fields'])

		for route in routes:

			route['vehicle'] = case['information']['vehicle']
			route['depot'] = case['information']['depot']

		final_routes.extend(routes)

		#REMOVING routes?

	#Writing to file
	CondPrint('\n\nWriting to file\n', args['verbose'])
	src.graph.nlg_to_json(final_routes, args['output_file'])

	CondPrint(
		f'\nDone: {time.time()-t0:.3f} seconds' +
		'\033[0m\n', args['verbose'])