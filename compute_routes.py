import warnings
warnings.filterwarnings("ignore")

import sys
import time
import json
import argparse
import numpy as np
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

    graph = src.router.assign_rng(graph, seed = parameters['rng_seed'])
    graph = src.router.assign_vehicle(graph, parameters['vehicles'])

    graph = src.rng.assign_link_parameters(graph, parameters)
    graph = src.rng.assign_node_parameters(graph, parameters)

    objective_fields = set()

    for vehicle in parameters['vehicles'].values():
        for case in vehicle['cases']:
            for objective in case['objectives'].keys():

                objective_fields.add(objective)

    objectives = {key: np.inf for key in list(objective_fields)}

    graph = src.savings_stochastic.add_depot_legs(
        graph, parameters['depot_nodes'], objectives,
    )

    CondPrint('Computing raw routes\n', args['verbose'])

    kwargs = {
        'pb_kwargs': {
            'freq': 1000,
        },
    }

    final_routes = []

    for vehicle_name, vehicle in parameters['vehicles'].items():

        keep_nodes = [k for k, v in graph._node.items() if vehicle_name in v['vehicle']]

        sg = src.graph.subgraph(
            graph, np.concatenate((keep_nodes, parameters['depot_nodes']))
        )

        for idx, case in enumerate(vehicle['cases']):

            print(f'\n{vehicle_name}, {case["name"]}\n')
            
            objectives = case['objectives']

            routes, route_values, success = src.savings_stochastic.savings(
                sg, objectives, **kwargs,
            )

            routes = src.router.route_information(sg, routes, parameters['route_fields'])

            full_routes = []
            
            for idx, route in enumerate(routes):

                condition_1 = len(route['nodes']) > 3
                condition_2 = idx == len(vehicle['cases'])
        
                if condition_1 or condition_2:
            
                    route['vehicle'] = vehicle_name

                    for objective in objectives.keys():

                        route[objective] = route_values[idx][objective]
                        route[f'{objective}_expected'] = np.mean(route_values[idx][objective])

                    full_routes.append(route)

            final_routes.extend(full_routes)
        
            all_nodes = np.array(list(sg.nodes))
            
            if full_routes:
                
                nodes_visited = np.unique(
                    np.concatenate([r['nodes'] for r in full_routes])
                )
                
            else:
                
                nodes_visited = []
            
            nodes_not_visited = np.unique(
                np.concatenate((
                    parameters['depot_nodes'],
                    np.setdiff1d(all_nodes, nodes_visited)
                )))

            sg = src.graph.subgraph(sg, nodes_not_visited)

    #Writing to file
    CondPrint('\n\nWriting to file\n', args['verbose'])
    src.graph.nlg_to_json(final_routes, args['output_file'])

    CondPrint(
        f'\nDone: {time.time()-t0:.3f} seconds' +
        '\033[0m\n', args['verbose'])