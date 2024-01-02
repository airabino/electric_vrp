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
	prog = 'module: graph_from_csv',
	description = (
		'Loads CSV files containing information on nodes and builds node-link-graph ' +
		'JSON without adjacency information.'
		),
	epilog = (
		'Call compute_adjacency.py to add adjacency information'
		),
	)

parser.add_argument(
	'-i', '--input_file',
	help = 'Required: formatted csv files to use as inputs',
	)

parser.add_argument(
	'-o', '--output_file',
	help = 'Output file for nlg .json, default is \'graph.json\'',
	default = 'graph.json'
	)

parser.add_argument(
	'-na', '--node_attributes',
	help = (
		'Dictionary of node attributes.\n' +
		'Example:\n' +
		'"{\'dc\':\'lambda node: node[\"dc\"]\'}"'
		),
	default = "{}",
	)

parser.add_argument(
	'-la', '--link_attributes',
	help = (
		'Dictionary of link attributes.\n' +
		'Example:\n' +
		'"{\'length\':\'lambda link: link[\"length\"]*1.609\'}"'
		),
	default = "{}",
	)

parser.add_argument(
	'-v', '--verbose',
	help = 'Optional status printing',
	action='store_false',
	)

parser.add_argument(
	'-p', '--parameters_file',
	help = 'JSON containing inputs which will overwrite command-line inputs',
	)

if __name__ == "__main__":

	t0 = time.time()

	args = vars(parser.parse_args(sys.argv[1:]))
	CondPrint(str_color + '\n' + 'Module graph_from_shapefile' + '\n', args['verbose'])

	args['node_attributes']=eval(args['node_attributes'])
	args['link_attributes']=eval(args['link_attributes'])

	if args['parameters_file'] is not None:

		CondPrint('Loading parameters file', args['verbose'])

		with open(args['parameters_file'], 'r') as file:

			parameters = json.load(file)

		for key in parameters.keys():

			args[key] = parameters[key]

	CondPrint('Loading graph from shapefile', args['verbose'])
	graph = src.graph.graph_from_shapefile(
		args['input_file'],
		node_attributes = args['node_attributes'],
		link_attributes = args['link_attributes'],
		)

	#Writing to file
	CondPrint('Writing to file', args['verbose'])
	src.graph.graph_to_json(graph, args['output_file'])

	CondPrint(
		'\n' + f'Done: {time.time()-t0:.3f} seconds' +
		'\033[0m\n', args['verbose'])