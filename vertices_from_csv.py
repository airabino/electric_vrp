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
	prog = 'module: vertices_from_csv',
	description = (
		'Loads formatted CSV files containing information on chargers ' +
		'and depots and formats them as vertices in formatted .json without ' +
		'adjacency information.'
		),
	epilog = (
		'Call compute_adjacency.py on a vertices .json file ' +
		'to compute adjacency information for vertices.'
		),
	)

parser.add_argument(
	'-i', '--input_files',
	nargs = '+',
	help = 'Required: formatted csv files to use as inputs',
	required = True,
	)

parser.add_argument(
	'-o', '--output_file',
	help = 'Output file for vertices .json, default is \'vertices.json\'',
	default = 'vertices.json'
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
	'-p', '--permission',
	help = 'Output file permission - w for overwrite, a for append - default is w',
	default = 'w',
	)

parser.add_argument(
	'-v', '--verbose',
	help = 'Optional status printing',
	action='store_true',
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

	args = parser.parse_args(sys.argv[1:])
	CondPrint(str_color + '\n' + 'Module vertices_from_csv', args.verbose)

	#Loading in charger .csv files as DataFrame
	CondPrint(str_color + 'Loading CSV files', args.verbose)
	df = src.store.Read(args.input_files)

	#Down-selection
	CondPrint(str_color + 'Down-selection', args.verbose)
	if args.exclude is not None:

		attributes = ParseAttributes(args.exclude)

		df = src.store.Exclude(df,attributes)

	if args.keep is not None:

		attributes = ParseAttributes(args.keep)

		df = src.store.Keep(df,attributes)

	#Creating vertices dictionary
	CondPrint(str_color + 'Creating vertices', args.verbose)
	vertices = src.store.Parse(df)

	#Writing to file
	CondPrint(str_color + 'Writing to file', args.verbose)
	src.store.Write(
		vertices,
		filename = args.output_file,
		permission = args.permission
		)

	CondPrint(str_color + '\n' + f'Done: {time.time()-t0:.3f} seconds' + '\n', args.verbose)