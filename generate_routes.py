import warnings
warnings.filterwarnings("ignore")

import os
import sys
import time
import json
import argparse
import numpy as np
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

def generate_routes(parameters):

    t0 = time.time()

    verbose = parameters.get('verbose', True)

    cprint(str_color + '\n' + 'Module generate_routes' + '\n', verbose)

    cprint('Loading graphs', verbose)
    directory = parameters['graphs_path']

    files = os.listdir(directory)

    graphs = {}

    for file in files:

        handle = int(file.split('.')[0].split('_')[1])

        graphs[handle] = src.graph.graph_from_json(directory + file)


    cprint('Loading vehicles', verbose)
    with open('Inputs/parameters_vehicle.json', 'r') as file:

        vehicles = json.load(file)

    for key, val in vehicles.items():

        vehicles[key]['object'] = src.routing.Vehicle(**val)


    cprint('Creating subgraphs', verbose)
    subgraphs = {}

    for depot, graph in graphs.items():
        for handle, vehicle in vehicles.items():

            subgraphs[f'{depot}::{handle}'] = vehicle['object'].subgraph(
                graph, parameters['exclude']
            )

    cprint('Generating routes', verbose)
    rng = np.random.default_rng(parameters['rng_seed'])

    routes_lists = {}
    routes_graphs = {}

    index_offset = 0

    for key, subgraph in subgraphs.items():

        depot = int(key.split('::')[0])

        routes_lists[key] = src.routing.routes(
            subgraph, depot,
            objective = 'cost',
            steps = subgraph.number_of_nodes() * 30,
            rng = rng,
            beta = parameters['beta'],
        )

        index_offset = len(routes_lists[key])

        routes_graphs[key] = src.routing.routes_graph(
            subgraph, routes_lists[key], index_offset = index_offset
        )

    routes = []

    for handle, subgraph in subgraphs.items():
        
        routes.extend(
            src.routing.route_information(
                subgraph, routes_lists[handle], parameters['functions']
            )
        )

    cprint('Writing to file', verbose)

    with open(parameters['output_file'], 'w') as file:

        json.dump(routes, file, indent = 4)

    cprint(
        f'\nDone: {time.time()-t0:.3f} seconds' +
        '\033[0m\n', verbose)

if __name__ == "__main__":

    args = vars(parser.parse_args(sys.argv[1:]))

    with open(args['parameters_file'], 'r') as file:

        parameters = json.load(file)

    generate_routes(parameters)

