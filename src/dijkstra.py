import numpy as np

from heapq import heappop, heappush
from itertools import count
from sys import maxsize

def _dijkstra(graph, origins, **kwargs):

    destinations = kwargs.get('destinations', [])
    objective = kwargs.get('objective', 'objective')
    fields = kwargs.get('fields', [])
    maximum_cost = kwargs.get('maximum_cost', np.inf)


    nodes = graph._node
    edges = graph._adj

    costs = {} # dictionary of objective values for paths

    path_values = {}
    paths = {}

    visited = {} # dictionary of costs-to-reach for nodes


    c = count() # use the count c to avoid comparing nodes (may not be able to)
    heap = [] # heap is heapq with 3-tuples (cost, c, node)

    for origin in origins:

        # Source is seen at the start of iteration and at 0 cost
        visited[origin] = np.inf

        values = {f: 0 for f in fields}
        paths[origin] = [origin]

        heappush(heap, (0, next(c), values, origin))

    while heap: # Iterating while there are accessible unseen nodes

        # Popping the lowest cost unseen node from the heap
        cost, _, values, source = heappop(heap)

        if source in costs:

            continue  # already searched this node.

        costs[source] = cost
        path_values[source] = values

        for target, edge in edges[source].items():

            # Updating states for edge traversal
            cost_target = cost + edge.get(objective, 1)

            # Updating the weighted cost for the path
            savings = cost_target < visited.get(target, np.inf)

            feasible = cost_target <= maximum_cost

            if savings & feasible:

                values_target = {k: v + edge.get(k, 0) for k, v in values.items()}
               
                visited[target] = cost_target

                paths[target] = paths[source] + [target]

                heappush(heap, (cost_target, next(c), values_target, target))

    return costs, path_values, terminal

def dijkstra(graph, origins, **kwargs):

    destinations = kwargs.get('destinations', [])
    objective = kwargs.get('objective', 'objective')
    fields = kwargs.get('fields', [])
    return_paths = kwargs.get('return_paths', True)
    terminate_at_destinations = kwargs.get('terminate_at_destinations', True)
    maximum_cost = kwargs.get('maximum_cost', np.inf)
    maximum_depth = kwargs.get('maximum_depth', np.inf)


    nodes = graph._node
    edges = graph._adj

    costs = {} # dictionary of objective values for paths

    path_values = {}

    visited = {} # dictionary of costs-to-reach for nodes

    terminal = {k: True for k in graph.nodes}

    terminals = []

    if terminate_at_destinations:

        terminals = [d for d in destinations if d not in origins]

    c = count() # use the count c to avoid comparing nodes (may not be able to)
    heap = [] # heap is heapq with 3-tuples (cost, c, node)

    for origin in origins:

        # Source is seen at the start of iteration and at 0 cost
        visited[origin] = np.inf

        values = {f: 0 for f in fields}
        # print(values)

        heappush(heap, (0, next(c), values, origin))

    while heap: # Iterating while there are accessible unseen nodes

        # Popping the lowest cost unseen node from the heap
        cost, _, values, source = heappop(heap)

        # print(values)

        if source in costs:

            continue  # already searched this node.

        costs[source] = cost
        path_values[source] = values

        if len(costs) > maximum_depth:

            break

        # print(values)

        if source in terminals:

            continue

        for target, edge in edges[source].items():

            # Updating states for edge traversal
            cost_target = cost + edge.get(objective, 1)

            # Updating the weighted cost for the path
            savings = cost_target <= visited.get(target, np.inf)

            feasible = cost_target <= maximum_cost

            if savings & feasible:

                # print(edge, {k: v for k, v in values.items()})

                values_target = {k: v + edge.get(k, 0) for k, v in values.items()}
               
                visited[target] = cost_target
                terminal[source] = False
                # terminal[target] = True

                heappush(heap, (cost_target, next(c), values_target, target))

    terminal = {k: terminal[k] for k in costs.keys()}

    return costs, path_values, terminal