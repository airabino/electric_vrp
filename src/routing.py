'''
Module for Dijkstra routing

Code is based on (is an edited version of):
NetworkX shortest_paths.weighted._dijkstra_multisource

Edits are to allow for native tracking of multiple shortest path simultaneously.
For example, one could get a shortest path weighted by 'distance' but also
want to know path 'time', this edited code allows for this to be done efficiently.
'''
import time
import numpy as np
import networkx as nx

from copy import deepcopy
from heapq import heappop, heappush
from itertools import count
from sys import float_info, maxsize

default_states = {
    'network_distance': {
        'field': 'network_distance',
        'initial': [0],
        'update': lambda x, v: [xi + v for xi in x],
    }
}

default_objectives = {
    'network_distance': lambda x: np.mean(s['network_distance']),
}

class Charger_Old():

    def __init__(self, **kwargs):

        self.n_cases = kwargs.get('n_cases', 1)

        self.reset_function = kwargs.get(
            'reset_function', lambda x: np.array([1] * self.n_cases))
        self.rate_function = kwargs.get(
            'rate_function', lambda x: np.array([1] * self.n_cases))
        self.delay_function = kwargs.get(
            'delay_function', lambda x: np.array([0] * self.n_cases))
        self.price_function = kwargs.get(
            'price_function', lambda x: np.array([0] * self.n_cases))

        self.range_field = kwargs.get('range_field', 'range')
        self.time_field = kwargs.get('time_field', 'time')
        self.price_field = kwargs.get('price_field', 'price')

        self.rng = kwargs.get('rng',np.random.default_rng(None))

        self.random_state()

    def random_state(self):

        rn = self.rng.random((self.n_cases, ))
        # print(rn)

        self.reset = self.reset_function(rn)
        self.rate = self.rate_function(rn)
        self.delay = self.delay_function(rn)
        self.price = self.price_function(rn)

        # print(self.rate, self.delay)

    def update(self, cost):

        reset_indices = cost[self.range_field] < self.reset
            
        cost[self.time_field][reset_indices] += (
            (self.reset[reset_indices] - cost[self.range_field][reset_indices]) /
            self.rate[reset_indices] +
            self.delay[reset_indices])

        cost[self.price_field][reset_indices] += (
            (self.reset[reset_indices] - cost[self.range_field][reset_indices]) *
            self.price[reset_indices])

        cost[self.range_field][reset_indices] = self.reset[reset_indices]

        return cost

class Charger():

    def __init__(self, **kwargs):

        self.n_cases = kwargs.get('n_cases', 1)

        self.reset_function = kwargs.get(
            'reset_function', lambda x: np.array([1] * self.n_cases))
        self.rate_function = kwargs.get(
            'rate_function', lambda x: np.array([1] * self.n_cases))
        self.delay_function = kwargs.get(
            'delay_function', lambda x: np.array([0] * self.n_cases))
        self.price_function = kwargs.get(
            'price_function', lambda x: np.array([0] * self.n_cases))

        self.range_field = kwargs.get('range_field', 'range')
        self.time_field = kwargs.get('time_field', 'time')
        self.price_field = kwargs.get('price_field', 'price')

        self.rng = kwargs.get('rng',np.random.default_rng(None))

        self.random_state()

    def random_state(self):

        rn = self.rng.random((self.n_cases, ))
        # print(rn)

        self.reset = self.reset_function(rn)
        self.rate = self.rate_function(rn)
        self.delay = self.delay_function(rn)
        self.price = self.price_function(rn)

        # print(self.rate, self.delay)

    def update(self, cost):

        reset_indices = cost[self.range_field] < self.reset
            
        cost[self.time_field][reset_indices] += (
            (self.reset[reset_indices] - cost[self.range_field][reset_indices]) /
            self.rate[reset_indices] +
            self.delay[reset_indices])

        cost[self.price_field][reset_indices] += (
            (self.reset[reset_indices] - cost[self.range_field][reset_indices]) *
            self.price[reset_indices])

        cost[self.range_field][reset_indices] = self.reset[reset_indices]

        return cost

def dijkstra(graph, origins, **kwargs):  
    """
    Uses Dijkstra's algorithm to find weighted shortest paths

    Code is based on NetworkX shortest_paths.weighted._dijkstra_multisource

    This implementation of Dijkstra's method is designed for high flexibility
    at some cost to efficiency. Specifically, this function implements Stochastic
    Cost with Risk Allowance Minimization Dijkstra (SCRAM-D) routing. As such
    this function allows for an optimal route to be computed for probabilistic
    node/link costs by tracking N scenarios in parallel with randomly sampled
    costs and minimizing the expectation of cost subject to constraints which
    may also be based on cost expectation. Additionally, nodes amy contain Charger
    objects which serve to reset a given state to a pre-determined value and
    may effect other states.

    Example - Battery Electric Vehicle (BEV) routing:

    graph - Graph or DiGraph containing a home location, several destinations,
    and M chargers of varying reliability and links for all objects less than
    300 km apart.

    origins - [home]

    destinations - [Yellowstone Park, Yosemite Park, Grand Canyon]

    states - {
        'distance': {
            'field': 'distance',
            'initial': [0] * n_cases,
            'update': lambda x, v: [xi + v for xi in x],
            'cost': lambda x: 0,
        },
        'price': {
            'field': 'price',
            'initial': [0] * n_cases,
            'update': lambda x, v: [xi + v for xi in x],
            'cost': lambda x: 0,
        },
        'time': {
            'field': 'time',
            'initial': [0] * n_cases,
            'update': lambda x, v: [xi + v for xi in x],
            'cost': lambda x: src.utilities.super_quantile(x, risk_tolerance),
        },
    }

    constraints - {
        'range': {
            'field': 'range',
            'initial': [vehicle_range] * n_cases,
            'update': lambda x, v: [xi + v for xi in x],
            'feasible': lambda x: src.utilities.super_quantile(x, risk_tolerance) > min_range,
        },
    }

    Parameters
    ----------
    graph: a NetworkX Graph or DiGraph

    origins: non-empty iterable of nodes
        Starting nodes for paths. If origins is an iterable containing
        a single node, then all paths computed by this function will
        start from that node. If there are two or more nodes in origins
        the shortest path to a given destination may begin from any one
        of the start nodes.

    destinations: iterable of nodes - optionally empty
        Ending nodes for path. If destinations is not empty then search
        continues until all reachable destinations are visited. If destinations
        is empty then the search continues until all reachable nodes are visited.

    states: dictionary with the below fields:
        'field': The relevant node/link property for integration
        'initial': Initial values for integration
        'update': Function which updates path values for nodes/links
        'cost': Function for computing a cost expectation from values

        states are used to compute the cost expectation

    constraints: dictionary with the below fields:
        'field': The relevant node/link property for integration
        'initinal': Iitial values for integration
        'update': Function which updates path values for nodes/links
        'feasible': Function which returns a Boolean for feasibility from values

    parameters: dictionary with the below fields:
        'field': The relevant node/link property for integration
        'initinal': Iitial values for integration
        'update': Function which updates path values for nodes/links

        parameters are NOT used to compute the cost expectation

    return_paths: Boolean
        Boolean whether or not to compute paths dictionary. If False None
        is returned for the paths output. COMPUTING PATHS WILL INCREASE RUN-TIME.

    Returns
    -------

    path_costs : dictionary
        Path cost expectations.

    path_values : dictionary
        Path objective values.

    paths : dictionary
        Dictionary containing ordered lists of nodes passed on shortest
        path between the origin node and other nodes. If return_paths == False
        then None will be returned.
    """

    destinations = kwargs.get('destinations', [])
    states = kwargs.get('states', default_states)
    constraints = kwargs.get('constraints', {})
    objectives = kwargs.get('objectives', default_objectives)
    return_paths = kwargs.get('return_paths', False)

    if return_paths:

        paths = {origin: origin for origin in origins}

    else:

        paths = None

    adjacency = graph._adj

    path_values = {}  # dictionary of costs for paths

    path_costs = {} # dictionary of objective values for paths

    visited = {} # dictionary of costs-to-reach for nodes

    destinations_visited = 0

    if len(destinations) == 0:

        # If no destinations are provided then search all nodes
        destinations_to_visit = maxsize

    else:

        #If destinations are provided then search until all are seen
        destinations_to_visit = len(destinations)

    c = count() # use the count c to avoid comparing nodes (may not be able to)
    heap = [] # heap is heapq with 3-tuples (cost, c, node)

    for origin in origins:

        visited[origin] = 0 # Source is seen at the start of iteration and at 0 cost

        # Adding the source tuple to the heap (initial cost, count, id)
        values = {}

        for key, info in states.items():

            values[key] = info['initial']

        heappush(heap, (0, next(c), values, origin))

    while heap: # Iterating while there are accessible unseen nodes

        # Popping the lowest cost unseen node from the heap
        (cost,  _, values, source) = heappop(heap)

        if source in path_values:

            continue  # already searched this node.

        path_values[source] = values
        path_costs[source] = cost

        # Checking if the current source is a search target
        # If all targets are reached then the search is terminated
        if source in destinations:

            destinations_visited += 1

        if destinations_visited >= destinations_to_visit:

            break

        # Iterating through the current source node's adjacency
        for target, link in adjacency[source].items():

            current = graph._node[target]

            current_values = deepcopy(values)            

            for key, info in states.items():

                # Updating objective for link
                current_values[key] = info['update'](
                    current_values[key], link.get(info['field'], 1)
                    )

                # Adding the target node cost
                current_values[key] = info['update'](
                    current_values[key], current.get(info['field'], 1)
                    )
            
            cost = 0

            for key, info in objectives.items():

                # Updating the weighted cost for the path
                cost += info(current_values)

            feasible = True

            for key, info in constraints.items():

                # Checking if link traversal is possible
                feasible *= info(current_values)

            # print(feasible)

            if not feasible:

                continue
                
            # Charging if availabe
            if 'charger' in current:

                # print('a',current_values)

                current_values = current['charger'].update(current_values)
                # print('b',current_values)

            # not_visited = target not in visited
            savings = cost < visited.get(target, np.inf)
            # print(savings)

            if savings:

                visited[target] = cost

                heappush(heap, (cost, next(c), current_values, target))

                # print(paths)

                if paths is not None:

                    paths[target] = paths[source]

    return path_costs, path_values, paths