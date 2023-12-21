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
	prog = 'module: add_vertex_fields',
	description = (
		'Loads formatted CSV files containing information on chargers ' +
		'and adds information to vertices in .json file'
		),
	)

parser.add_argument(
	'-j', '--json_file',
	help = 'Required: .json file containing vertices',
	required = True,
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
	'-i', '--input_files',
	nargs = '+',
	help = 'Required: formatted csv files to use as inputs',
	required = True,
	)

parser.add_argument(
	'-o', '--output_file',
	help = 'Output file for vertices .json, default behavior is to overwrite json_file',
	)

parser.add_argument(
	'-v', '--verbose',
	help = 'Optional status printing',
	action='store_true',
	)

if __name__ == "__main__":

	t0 = time.time()

	args = parser.parse_args(sys.argv[1:])
	CondPrint(str_color + '\n' + 'Module add_vertex_fields', args.verbose)

	# Loading in charger .csv files as DataFrame
	CondPrint('Loading CSV files', args.verbose)
	df = src.store.Read(args.input_files)

	# Loading vertices file
	CondPrint('Loading vertices file', args.verbose)
	vertices = src.store.Load(args.json_file)

	# Fields
	if args.parameters_file is not None:

		CondPrint('Loading parameters file', args.verbose)
		parameters = src.store.Load(args.parameters_file)
		fields = parameters['vertex_fields']

	elif args.fields is not None:

		fields = args.fields

	else:

		print('Please specify either a parameters file or fields')

	# Adding fields
	CondPrint('Adding fields to vertices', args.verbose)
	vertices = src.store.AddFields(vertices, df, fields)

	if args.output_file is None:

		output_file = args.json_file

	else:

		output_file = args.output_file

	# Writing to file
	CondPrint('Writing to file', args.verbose)
	src.store.Write(
		vertices,
		filename = output_file,
		permission = 'w'
		)

	CondPrint('\n' + f'Done: {time.time()-t0:.3f} seconds' + '\n', args.verbose)