import warnings
warnings.filterwarnings("ignore")

import sys
import time
import json
import argparse
import pandas as pd


import src
from src.utilities import CondPrint

str_color = '\033[1m\033[38;5;34m\033[48;5;0m'

#ArgumentParser objecct configuration
parser = argparse.ArgumentParser(
	prog = 'module: mark_visited',
	description = (
		'Computes adjacency for graph based by routing on atlas'
		),
	)

parser.add_argument(
	'-g', '--graph_file',
	help = 'JSON file storing NLG',
	)

parser.add_argument(
	'-nf', '--nodes_file',
	help = 'JSON containing a list of nodes to mark',
	)

parser.add_argument(
	'-n', '--nodes',
	help = 'Nodes to be marked',
	nargs = '+',
	type = int,
	)

parser.add_argument(
	'-f','--field',
	help = 'Field to mark',
	default = 'visited',
	)

parser.add_argument(
	'-fv', '--field_value',
	help = 'Value to be assigned to field in nodes',
	default = 1,
	)

parser.add_argument(
	'-o','--output_file',
	help = 'Output NLG filename - default is to overwrite graph_file',
	)

parser.add_argument(
	'-v', '--verbose',
	help = 'Optional status printing',
	action='store_true',
	)

if __name__ == "__main__":

	t0 = time.time()

	args = vars(parser.parse_args(sys.argv[1:]))
	CondPrint(str_color + '\n' + 'Module mark_visited' + '\n', args['verbose'])

	# print(args)
	if args['nodes_file'] is not None:

		with open(args['nodes_file'], 'r') as file:

			nodes = json.load(file)

	else:

		nodes = args['nodes']

	# Loading in graph
	CondPrint('Loading graph', args['verbose'])
	graph = src.graph.graph_from_json(args['graph_file'])

	CondPrint('Marking nodes\n', args['verbose'])
	graph = src.graph.mark_nodes(graph, nodes, args['field'], args['field_value'])

	#Writing to file
	if args['output_file'] is None:

		args['output_file'] = args['graph_file']

	CondPrint('Writing to file\n', args['verbose'])
	src.graph.graph_to_json(graph, args['output_file'])

	CondPrint(
		f'\nDone: {time.time()-t0:.3f} seconds' +
		'\033[0m\n', args['verbose'])