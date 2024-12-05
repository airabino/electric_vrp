import numpy as np
import networkx as nx

from itertools import count
from heapq import heappop, heappush

from .graph import graph_from_nlg

def dijkstra(graph, origins, **kwargs):

    terminals = kwargs.get('terminals', [])
    objective = kwargs.get('objective', 'objective')
    fields = kwargs.get('fields', ['distance', 'time'])
    maximum_cost = kwargs.get('maximum_cost', np.inf) # Maximum acceptable edge cost
    maximum_depth = kwargs.get('maximum_depth', np.inf) # Maximum acceptable path cost

    terminals = [t for t in terminals if t not in origins]

    nodes = graph._node
    edges = graph._adj

    costs = {}
    values = {}
    paths = {}
    extreme = {k: True for k in graph.nodes()}

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

                extreme[source] = False

                heappush(heap, (path_cost, next(c), target))

    extremities = {k: extreme[k] for k in costs.keys()}

    return costs, values, paths, extremities

def reduction(graph, **kwargs):

    origins = kwargs.get('origins', [])
    objective = kwargs.get('objective', 'distance')
    maximum_cost = kwargs.get('maximum_cost', np.inf)
    maximum_depth = kwargs.get('maximum_depth', np.inf)
    fields = kwargs.get('fields', ['distance', 'time'])
    snowball = kwargs.get('snowball', False)
    verbose = kwargs.get('verbose', False)

    _node = graph._node

    intersections = []

    for source, adj in graph._adj.items():

        if len(adj) != 2:

            intersections.append(source)

    origins = origins + intersections

    heap = []
    c = count()

    for node in origins:

        heappush(heap, (next(c), node))

    nodes = []
    links = []

    while heap:

        idx, origin = heappop(heap)

        if verbose:
            print(f'{idx} done, {len(heap)} in queue                 ', end = '\r')

        node = _node[origin]
        node['id'] = origin

        nodes.append(node)

        costs, values, _, extremities = dijkstra(
            graph,
            [origin],
            objective = objective,
            terminals = origins,
            maximum_cost = maximum_cost,
            maximum_depth = maximum_depth,
            fields = fields,
            )

        extreme_nodes = [k for k, v in extremities.items() if v]

        destinations_reached = np.intersect1d(
            extreme_nodes,
            origins,
            )

        for destination in destinations_reached:

            link = {**values.get(destination, {})}

            link['source'] = origin
            link['target'] = destination

            links.append(link)

        if snowball:

            new_destinations = np.setdiff1d(
                extreme_nodes,
                origins,
                )

            for destination in new_destinations:

                heappush(heap, (next(c), destination))

                origins.append(destination)

    return graph_from_nlg({'nodes': nodes, 'links': links})

def giant_connected_component(graph):

    cc = list(nx.connected_components(graph))

    gcc = cc[np.argmax([len(c) for c in cc])]

    cc.remove(gcc)

    exclude = [n for c in cc for n in list(c)[:]]

    graph.remove_nodes_from(exclude)

    return graph