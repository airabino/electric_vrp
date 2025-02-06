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

def depot_subgraphs(parameters):

    t0 = time.time()

    verbose = parameters.get('verbose', True)

    cprint(str_color + '\n' + 'Module depot_subgraphs' + '\n', verbose)

    cprint('Loading graph', verbose)
    graph = src.graph.graph_from_json(parameters['graph_file'])

    cprint('Loading atlas', verbose)
    atlas = src.graph.graph_from_json(parameters['atlas_file'])

    cprint('Loading rules', verbose)
    groups, counts = src.sample.load_groups(parameters['rules_file'])

    graph = src.sample.assign_groups(graph, groups)

    totals = {k: 0 for k in counts.keys()}

    for source, node in graph._node.items():

        if node['group'] is not None:

            totals[node['group']] += 1

    adjusted_counts = {k: min([totals[k], counts[k]]) for k in totals.keys()}

    cprint('Optimizing sample', verbose)

    depots = [k for k, v in graph._node.items() if v['network'] == 'Depot']

    graph = src.sample.station_costs(graph, atlas, depots, objective = '')

    opt = src.sample.Optimization(graph, adjusted_counts)

    solver_kwargs = {'_name': 'cbc', 'executable': 'src/cbc'}

    opt.solve(**solver_kwargs)

    cprint('Creating subgraphs', verbose)

    subgraphs = src.sample.subgraphs(graph, opt.assignment)

    for depot, subgraph in subgraphs.items():

        subgraph = src.adjacency.adjacency(
            atlas, subgraph, depots = list(subgraphs.keys()), **parameters['kwargs']
            )

    cprint('Writing to file', verbose)

    for depot, subgraph in subgraphs.items():

        src.graph.graph_to_json(
            subgraph, f"{parameters['output_path']}subgraph_{depot}.json"
            )

    cprint(
        f'\nDone: {time.time()-t0:.3f} seconds' +
        '\033[0m\n', verbose)

if __name__ == "__main__":

    args = vars(parser.parse_args(sys.argv[1:]))

    with open(args['parameters_file'], 'r') as file:

        parameters = json.load(file)

    depot_subgraphs(parameters)