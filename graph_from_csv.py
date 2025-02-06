import warnings
warnings.filterwarnings("ignore")

import sys
import time
import json
import argparse
import pandas as pd


import src
from src.utilities import cprint

str_color = '\033[1m\033[38;5;34m\033[48;5;0m'

#ArgumentParser objecct configuration
parser = argparse.ArgumentParser()

parser.add_argument(
    '-p', '--parameters_file',
    help = 'JSON containing inputs which will overwrite command-line inputs',
    )

def graph_from_csv(parameters):

    t0 = time.time()

    verbose = parameters.get('verbose', True)

    cprint(str_color + '\n' + 'Module graph_from_csv' + '\n', verbose)

    #Loading in node .csv files as DataFrame
    cprint('Loading CSV files', verbose)
    df = src.graph.dataframe_from_csv(parameters['input_files'])

    cprint('Creating graph', verbose)
    nlg = src.graph.nlg_from_dataframe(
        df, node_attributes = parameters['node_attributes'],
        )

    cprint('Writing to file', verbose)
    src.graph.nlg_to_json(nlg, parameters['output_file'])

    cprint(
        str_color + '\n' + f'Done: {time.time()-t0:.3f} seconds' +
        '\033[0m\n', verbose)

if __name__ == "__main__":

    args = vars(parser.parse_args(sys.argv[1:]))

    with open(args['parameters_file'], 'r') as file:

        parameters = json.load(file)

    graph_from_csv(parameters)