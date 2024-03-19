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
	prog = 'module: add_adjacency',
	description = (
		'Computes adjacency for graph based by routing on atlas'
		),
	)

parser.add_argument(
	'-g', '--graph_file',
	help = 'JSON file storing NLG for graph to which links will be added'
	)

parser.add_argument(
	'-a', '--atlas_file',
	help = 'JSON file storing NLG for atlas on which links will be computed'
	)

parser.add_argument(
	'-r','--recompute',
	help = 'Recompute adjacency for all nodes',
	action = 'store_true',
	)

parser.add_argument(
	'-o', '--output_file',
	help = 'Output file for nlg .json, default is same as graph file',
	default = None
	)

parser.add_argument(
	'-d', '--depots',
	help = 'Nodes which are depots',
	default = [],
	nargs = '+',
	)

parser.add_argument(
	'-w', '--weights',
	help = (
		'Dictionary off routing weights -> {edge_field: limit}.\n' +
		'Example:\n' +
		'"{\'length\':\'300e3\'}".' +
		'Limits <= 0 will be treated as infinite'
		),
	default = "{}",
	)

parser.add_argument(
	'-v', '--verbose',
	help = 'Optional status printing',
	action='store_true',
	)

parser.add_argument(
	'-p', '--parameters_file',
	help = 'JSON containing inputs which will overwrite command-line inputs',
	)

if __name__ == "__main__":

	t0 = time.time()

	args = vars(parser.parse_args(sys.argv[1:]))
	CondPrint(str_color + '\n' + 'Module add_adjacency' + '\n', args['verbose'])

	args['weights']=eval(args['weights'])

	if args['parameters_file'] is not None:

		CondPrint('Loading parameters file', args['verbose'])

		with open(args['parameters_file'], 'r') as file:

			parameters = json.load(file)

		for key in parameters.keys():

			args[key] = parameters[key]

	# #Loading in node .csv files as DataFrame
	CondPrint('Loading graph', args['verbose'])
	graph = src.graph.graph_from_json(args['graph_file'])

	CondPrint('Loading atlas', args['verbose'])
	atlas = src.graph.graph_from_json(args['atlas_file'])

	CondPrint('Computing adjacency\n', args['verbose'])
	graph = src.adjacency.adjacency(
		atlas, graph, args['weights'], end_color = '', depots = args['depots']
		)

	#Writing to file
	if args['output_file'] is None:

		args['output_file'] = args['graph_file']

	CondPrint('\nWriting to file\n', args['verbose'])
	src.graph.graph_to_json(graph, args['output_file'])

	CondPrint(
		f'\nDone: {time.time()-t0:.3f} seconds' +
		'\033[0m\n', args['verbose'])