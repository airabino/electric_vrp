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
	'-i', '--input_files',
	nargs = '+',
	help = 'Required: formatted csv files to use as inputs',
	)

parser.add_argument(
	'-o', '--output_file',
	help = 'Output file for nlg .json, default is \'graph.json\'',
	default = 'graph.json'
	)

parser.add_argument(
	'-e', '--exclude',
	help = (
		'Down selection - removes vertices which HAVE the specified key/value pair. ' +
		'Usage is URL-like, sequence: ' +
		'key_1 value_1_1 ... value_1_n ...' +
		'and key_n value_n_1 ... value_n_n. ' +
		'If a keyword contains spaces use quotes ex: \'EV Network Clean\''
		),
	nargs = '+',
	)

parser.add_argument(
	'-k', '--keep',
	help = (
		'Down selection - removes vertices which DO NOT HAVE the specified key/value pair. ' +
		'Usage is URL-like, sequence: ' +
		'key_1 value_1_1 ... value_1_n ...' +
		'and key_n value_n_1 ... value_n_n. ' +
		'If a keyword contains spaces use quotes ex: \'EV Network Clean\''
		),
	nargs = '+',
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
	'-v', '--verbose',
	help = 'Optional status printing',
	action='store_false',
	)

parser.add_argument(
	'-p', '--parameters_file',
	help = 'JSON containing inputs which will overwrite command-line inputs',
	)

def ParseAttributes(arguments):

	attributes={}

	key_flag=True

	for argument in arguments:

		if key_flag:

			key=argument
			attributes[key] = []
			key_flag = False

		elif argument == 'and':

			key_flag = True

		else:

			attributes[key].append(argument)

	return attributes

if __name__ == "__main__":

	t0 = time.time()

	args = vars(parser.parse_args(sys.argv[1:]))
	CondPrint(str_color + '\n' + 'Module graph_from_csv' + '\n', args['verbose'])

	args['node_attributes']=eval(args['node_attributes'])

	if args['parameters_file'] is not None:

		CondPrint('Loading parameters file', args['verbose'])

		with open(args['parameters_file'], 'r') as file:

			parameters = json.load(file)

		for key in parameters.keys():

			args[key] = parameters[key]

	#Loading in node .csv files as DataFrame
	CondPrint(str_color + 'Loading CSV files', args['verbose'])
	df = src.graph.dataframe_from_csv(args['input_files'])

	#Down-selection
	CondPrint(str_color + 'Down-selection', args['verbose'])
	if args['exclude'] is not None:

		fields = ParseAttributes(args['exclude'])

		df = src.graph.exclude_rows(df,fields)

	if args['keep'] is not None:

		fields = ParseAttributes(args['keep'])

		df = src.graph.keep_rows(df,fields)

	# Attributes
	if args['node_attributes']:

		CondPrint('Loading parameters file', args['verbose'])

		node_attributes = args['node_attributes']

	else:

		df_keys = list(df.keys())

		node_attributes = {}

		for key in df_keys:

		    node_attributes[key] = lambda r: r[key]

	#Creating vertices dictionary
	CondPrint(str_color + 'Creating vertices', args['verbose'])
	nlg = src.graph.nlg_from_dataframe(df, node_attributes = node_attributes)

	#Writing to file
	CondPrint(str_color + 'Writing to file', args['verbose'])
	src.graph.nlg_to_json(nlg, args['output_file'])

	CondPrint(
		str_color + '\n' + f'Done: {time.time()-t0:.3f} seconds' +
		'\033[0m\n', args['verbose'])