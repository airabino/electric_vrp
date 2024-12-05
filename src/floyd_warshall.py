import time

import numpy as np
import networkx as nx

from heapq import heappop, heappush
from itertools import count
from sys import maxsize

from numba import types
from numba import typed
from numba import jit

def shortest_paths(graph, **kwargs):

    # Processing kwargs
    fields = kwargs.get('fields', ['objective'])
    
    kwargs['objective'] = fields[0]

    costs, predecessors = floyd_warshall(graph, **kwargs)

    # print(predecessors)
    paths = recover_paths(graph, predecessors, **kwargs)
    values = recover_values(graph, paths, **kwargs)

    # arr = np.array([[v['time'] for v in val.values()] for val in values.values()])

    # sym = True

    # for source, sp in paths.items():
    #     for target, p in sp.items():

    #         path = paths[source][target]
    #         rpath = np.flip(paths[target][source])
    #         # print(all([path[i] == rpath[i] for i in range(len(path))]))

    #         sym *= all([path[i] == rpath[i] for i in range(len(path))])

    # print(sym)
    # print((arr == arr.T).all())
    # print((costs == costs.T).all())

    return predecessors, values, paths

def floyd_warshall(graph, **kwargs):
    '''
    Implements the Floyd-Warshall algorithm for all-pairs routing

    args:

    graph is a NetworkX Graph
    fields is a list of edge attributes - the first one listed will be used for routing

    kwargs:

    origins - list of nodes in graph from which routes will start
    destinations - list of nodes in graph at which reoutes will end
    pivots - list of nodes in graph which can serve as intermediaries in routes

    if origins, destinations, or pivots are not provided then all nodes will be used

    tolerance - float threshold of disambiguation for selecting alterante paths

    if a non-zero tolerance is provided then alternate paths may be produced
    '''

    # Processing kwargs
    objective = kwargs.get('objective', 'objective')
    maximum_edge_cost = kwargs.get('maximum_edge_cost', np.inf)
    maximum_path_cost = kwargs.get('maximum_path_cost', np.inf)
    # field = kwargs.get('field', None)
    pivots = kwargs.get('pivots', list(graph.nodes))
    perturbation = kwargs.get('perturbation', 0)
    adjacency = kwargs.get('adjacency', None)

    if adjacency is None:

        # Creating adjacency matrix
        adjacency = nx.to_numpy_array(graph, weight = objective, nonedge = np.inf)
    
    adjacency[adjacency > maximum_edge_cost] = np.inf

    # print(adjacency)
    # print((adjacency == adjacency.T).all())

    node_to_idx = {k: idx for idx, k in enumerate(graph.nodes)}
    idx_to_node = {idx: k for idx, k in enumerate(graph.nodes)}

    n = len(adjacency)

    if perturbation > 0:

        adjacency *= np.random.uniform(
            1 - perturbation,
            1 + perturbation,
            size = adjacency.shape
            )

    pivots_idx = [node_to_idx[k] for k in pivots]

    # Running the Floyd Warshall algorithm
    costs = np.zeros_like(adjacency)
    predecessors = np.zeros_like(adjacency, dtype = int)

    costs, predecessors = _floyd_warshall(
        adjacency,
        pivots_idx,
        costs,
        predecessors,
        maximum_path_cost,
    )

    # print(costs)
    # print((costs == costs.T).all())

    return costs, predecessors

@jit(nopython = True, cache = True)
def _floyd_warshall(adjacency, pivots, costs, predecessors, max_cost):
    '''
    Implementation of Floyd Warshall algorithm
    https://en.wikipedia.org/wiki/Floyd%E2%80%93Warshall_algorithm
    '''

    n = len(adjacency)

    # Creating initial approximations
    for source in range(n):
        for target in range(n):

            # Initial assumption is that source is the direct predecessor to target
            # and that the cost is adjacency[source][target]. Non-edges should be
            # set to infinite cost for the algorithm to produce correct results
            costs[source][target] = adjacency[source][target]
            predecessors[source][target] = source

    # Updating approximations
    for pivot in pivots:
        for source in range(n):
            for target in range(n):

                tentative_cost = costs[source][pivot] + costs[pivot][target]

                # if source-pivot-target is lower cost than source-target then update
                if (tentative_cost < costs[source][target]) and (tentative_cost <= max_cost):

                    costs[source][target] = costs[source][pivot] + costs[pivot][target]
                    predecessors[source][target] = predecessors[pivot][target]

    return costs, predecessors

def recover_paths(graph, predecessors, **kwargs):

    node_to_idx = {k: idx for idx, k in enumerate(graph.nodes)}
    idx_to_node = {idx: k for idx, k in enumerate(graph.nodes)}

    # Recovering paths
    paths = {}

    for origin in graph.nodes:

        paths[origin] = {}

        for destination in graph.nodes:

            # print(origin, destination)

            path = _recover_path(
                predecessors, node_to_idx[origin], node_to_idx[destination]
                )

            paths[origin][destination] = [idx_to_node[n] for n in path]

    return paths

def recover_values(graph, paths, **kwargs):

    # field = kwargs.get('fields', None)

    node_to_idx = {k: idx for idx, k in enumerate(graph.nodes)}
    # print(node_to_idx)

    adjacencies = kwargs.get('adjacencies', None)
    fields = kwargs.get('fields', ['distance'])

    if adjacencies is None:

        # Creating adjacency matrices
        adjacencies = (
            {f: nx.to_numpy_array(graph, weight = f, nonedge = np.inf) for f in fields}
            )
    
    # print(adjacencies)
    # for k, a in adjacencies.items():

        # print(k, (a == a.T).all())

    # Recovering values
    values = {}

    # print(paths)

    for origin in graph.nodes:

        values[origin] = {}

        for destination in graph.nodes:

            path = [node_to_idx[n] for n in paths[origin][destination]]
            
            # print(path, [node_to_idx[n] for n in paths[destination][origin]])
            rpath = [node_to_idx[n] for n in paths[destination][origin]]

            # print('path', path, rpath)

            # print(
            #     'c',
            #     _recover_path_costs(adjacencies[fields[0]], path) == _recover_path_costs(adjacencies[fields[0]], path)
            #     )

            v = (
                {f: _recover_path_costs(adjacencies[f], path) for f in fields}
                )

            vr = (
               {f: _recover_path_costs(adjacencies[f], rpath) for f in fields}
                )

            # print(v == vr, v, vr)

            values[origin][destination] = v

    arr = np.array([[v[fields[0]] for v in val.values()] for val in values.values()])
    # print(arr == arr.T)
    # print('b', (arr == arr.T).all())

    return values

@jit(nopython = True, cache = True)
def recover_flow(predecessors, flows, origins, destinations, volumes):
    '''
    Back-propogates O/D flows based on optimal predecessors
    '''

    max_iterations = len(predecessors)

    for origin in origins:
        for destination in destinations:

            current = destination

            idx = 0

            while (current != origin) and (idx <= max_iterations):

                current = predecessors[origin][current]
                flows[origin, current] += volumes[origin, destination]

                idx += 1

    return flows

@jit(nopython = True, cache = True)
def _recover_path(predecessors, origin, destination):
    '''
    recovers paths by working backward from destination to origin
    '''

    max_iterations = len(predecessors)

    path = [destination]

    idx = 0

    while (origin != destination) and (idx <= max_iterations):

        # print(origin, destination)
        # print()

        destination = predecessors[origin][destination]
        path = [destination] + path

        # print(origin, destination)

        idx +=1

    return path

@jit(nopython = True, cache = True)
def _recover_path_costs(adjacency, path):
    '''
    Recovers costs for a path on an adjacency matrix
    '''

    cost = 0

    # p = []

    for idx in range(len(path) - 1):

        # p.append((adjacency[path[idx]][path[idx + 1]]))

        cost += adjacency[path[idx]][path[idx + 1]]

    # print('p', p)

    return cost

@jit(nopython = True, cache = True)
def _floyd_warshall_multi(adjacency, pivots, costs, predecessors, tolerance = .05):
    '''
    Implementation of Floyd Warshall algorithm
    https://en.wikipedia.org/wiki/Floyd%E2%80%93Warshall_algorithm

    This implementation stores some sub-optimal approximations in order to
    produce alternate paths
    '''

    tolerance += 1.

    n = len(adjacency)

    store = [] # List for storing non-optimal approximations

    # Creating initial approximations
    for source in range(n):
        for target in range(n):

            # Initial assumption is that source is the direct predecessor to target
            # and that the cost is adjacency[source][target]. Non-edges should be
            # set to infinite cost for the algorithm to produce correct results
            costs[source][target] = adjacency[source][target]
            predecessors[source][target] = source

    # Updating approximations
    for pivot in pivots:
        for source in range(n):
            for target in range(n):

                costs_new = costs[source][pivot] + costs[pivot][target]

                # if source-pivot-target is lower cost than source-target then update
                if costs_new < costs[source][target]:

                    # If the difference is less than the threshold of disambiguation
                    # then store the previous approximation
                    if costs[source][target] < min([tolerance * costs_new, np.inf]):

                        store.append(
                            (
                                source, target,
                                predecessors[source][target],
                                costs[source][target],
                                )
                            )

                    costs[source][target] = costs[source][pivot] + costs[pivot][target]
                    predecessors[source][target] = predecessors[pivot][target]

    return costs, predecessors, store

def extended_predecessors(costs, predecessors, store, tolerance = .05):
    '''
    Computes a multi-predecessors dictionary to allow for alternative routing
    '''

    tolerance += 1.

    n = len(costs)

    extended = {}

    for source in range(n):

        extended[source] = {}

        for target in range(n):

            extended[source][target] = {predecessors[source][target]}

    for predecessor in store:

        s, t, p, c = predecessor

        if c <= tolerance * costs[s][t]:

            extended[s][t].add(p)

    return extended

@jit(nopython = True, cache = True)
def _recover_paths_bfs(predecessors, origin, destination):
    '''
    Recovers multiple branching path alternatives
    '''

    paths = []

    heap = []

    c = count()

    heappush(heap, (next(c), [destination]))

    while heap:

        _, path = heappop(heap)

        destinations = predecessors[origin][path[0]]

        for destination in destinations:

            if destination == origin:

                paths.append([destination] + path)

            else:

                heappush(heap, (c, [destination] + path))

    return paths