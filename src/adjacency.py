'''
Module for computing adjacency for a graph via routing on another graph. An example
would be computing travel times between cities connected by highways or latency between
computers connected via the internet. Another case would be compting network distances
between all points in a subset of a greater network. In any case, the nodes of the former
network must be coincident, or nearly so, with nodes in the latter network.

In this module the graph for which adjacency is being computed will be referred to as the
"graph" while the graph on which the routing occurs will be referred to as the "atlas". In
cases where either could be used "graph" will be used as default.
'''

import numpy as np

from sys import maxsize

from scipy.spatial import KDTree
from itertools import count
from heapq import heappop, heappush

from .progress_bar import ProgressBar

from .graph import graph_from_nlg, cypher
from .utilities import pythagorean, haversine

def closest_nodes_from_coordinates(graph, x, y):
    '''
    Creates an assignment dictionary mapping between points and closest nodes
    '''

    nodes = list(graph.nodes)

    # Pulling coordinates from graph
    xy_graph = np.array([(n['x'], n['y']) for n in graph._node.values()])
    xy_graph = xy_graph.reshape((-1,2))

    # Creating spatial KDTree for assignment
    kd_tree = KDTree(xy_graph)

    # Shaping input coordinates
    xy_query = np.vstack((x, y)).T

    # Computing assignment
    result = kd_tree.query(xy_query)

    node_assignment = []

    for idx in range(len(x)):

        distance = result[0][idx]
        node = result[1][idx]

        node_assignment.append({
            'id': nodes[node],
            'query': xy_query[idx],
            'result': xy_graph[node],
            'distance': distance,
            })

    return node_assignment

def relate(atlas, graph):
    '''
    Creates an assignment dictionary mapping between points and closest nodes
    '''

    # Pulling coordinates from atlas
    id_atlas = list(atlas.nodes())
    xy_atlas = np.array([(n['x'], n['y']) for n in atlas._node.values()])
    xy_atlas = xy_atlas.reshape((-1,2))

    # Pulling coordinates from graph
    id_graph = list(graph.nodes())
    xy_graph = np.array([(n['x'], n['y']) for n in graph._node.values()])
    xy_graph = xy_graph.reshape((-1,2))

    # Creating spatial KDTree for assignment
    kd_tree = KDTree(xy_atlas)

    # Computing assignment
    result = kd_tree.query(xy_graph)

    node_assignment = []

    for idx in range(len(xy_graph)):

        distance = result[0][idx]
        node = result[1][idx]
        

        node_assignment.append({
            'id_atlas':id_atlas[node],
            'id_graph':id_graph[idx],
            'query':xy_graph[idx],
            'result':xy_atlas[node],
            'distance': haversine(*xy_graph[idx], *xy_atlas[node]),
            })

    return node_assignment

def node_assignment(atlas, graph):

    x, y = np.array(
        [[val['x'], val['y']] for key, val in graph._node.items()]
        ).T

    graph_nodes = np.array(
        [key for key, val in graph._node.items()]
        ).T

    # print(graph_nodes)

    atlas_nodes = closest_nodes_from_coordinates(atlas, x, y)

    graph_to_atlas = (
        {graph_nodes[idx]: atlas_nodes[idx]['id'] for idx in range(len(graph_nodes))}
        )
    
    atlas_to_graph = {}

    for key, val in graph_to_atlas.items():

        if val in atlas_to_graph.keys():

            atlas_to_graph[val] += [key]

        else:

            atlas_to_graph[val] = [key]

    return graph_to_atlas, atlas_to_graph

def dijkstra(graph, origins, **kwargs):

    terminals = kwargs.get('terminals', [])
    objective = kwargs.get('objective', 'objective')
    fields = kwargs.get('fields', [])
    return_paths = kwargs.get('return_paths', True)
    maximum_cost = kwargs.get('maximum_cost', np.inf) # Maximum acceptable edge cost
    maximum_depth = kwargs.get('maximum_depth', np.inf) # Maximum acceptable path cost

    terminals = [t for t in terminals if t not in origins]

    nodes = graph._node
    edges = graph._adj

    costs = {}
    values = {}
    paths = {}

    c = count()
    heap = []

    for origin in origins:
        
        costs[origin] = 0
        values[origin] = {f: 0 for f in fields}
        paths[origin] = [origin]

        heappush(heap, (0, next(c), origin))

    while heap: # Iterating while there are accessible unseen nodes

        # Popping the lowest cost unseen node from the heap
        cost, _, source = heappop(heap)

        if source in terminals:

            continue

        for target, edge in edges[source].items():

            edge_cost = edge.get(objective, 1)

            if edge_cost > maximum_cost:

                continue

            # Updating states for edge traversal
            path_cost = cost + edge_cost

            if path_cost > maximum_depth:

                continue

            # Updating the weighted cost for the path
            savings = path_cost < costs.get(target, np.inf)

            if savings:
               
                costs[target] = path_cost
                values[target] = {k: v + edge.get(k, 1) for k, v in values[source].items()}
                paths[target] = paths[source] + [target]

                heappush(heap, (path_cost, next(c), target))

    return costs, values, paths

def adjacency(atlas, graph, **kwargs):
    '''
    Adds adjacency to graph by routing on atlas
    '''
    objective = kwargs.get('objective', 'distance')
    maximum_cost = kwargs.get('maximum_cost', np.inf)
    maximum_depth = kwargs.get('maximum_depth', np.inf)
    fields = kwargs.get('fields', ['distance', 'time'])
    pb_kw = kwargs.get('progress_bar', {})
    depots = kwargs.get('depots', [])

    graph_to_atlas, atlas_to_graph = node_assignment(atlas, graph)

    # print(graph_to_atlas)

    destinations = list(graph.nodes)
    # print(destinations)

    destinations_atlas = [graph_to_atlas[node] for node in destinations]

    # print(len(destinations_atlas), len(np.unique(destinations_atlas)))

    for origin in ProgressBar(destinations, **pb_kw):

        # print(origin, np.inf if origin in depots else maximum_depth)

        origin_atlas = graph_to_atlas[origin]
        # print(origin, origin_atlas)

        costs, values, _ = dijkstra(
            atlas,
            [origin_atlas],
            objective = objective,
            maximum_cost = np.inf if origin in depots else maximum_cost,
            maximum_depth = np.inf if origin in depots else maximum_depth,
            fields = fields,
            )

        adj = {}

        destinations_reached = np.intersect1d(
            list(values.keys()),
            destinations_atlas,
            )

        # print(
        #     origin, len(destinations_reached), np.inf if origin in depots else maximum_depth
        #     )

        # print(len(values.keys()))
        # print(len(np.unique(list(costs.keys()))))
        # print(costs.keys())
        # break

        for destination in destinations_reached:

            nodes = atlas_to_graph[destination]

            for node in nodes:

                adj[node] = values[destination]

        graph._adj[origin] = adj

        # break

    return graph
