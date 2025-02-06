import time
import numpy as np
import networkx as nx

from heapq import heappop, heappush
from itertools import count

default_rng = np.random.default_rng()

class Vehicle():

    def __init__(self, **kwargs):

        self.capacity = kwargs.get('capacity', 80 * 3.6e6)
        self.speeds = kwargs.get('speeds', [13.4, 25.3, 31.3])
        self.consumptions = kwargs.get('consumptions', [338, 515, 423])

    def energy(self, distance, speed):

        return np.interp(speed, self.speeds, self.consumptions) * distance

    def update_graph(self, graph):

        for source, _adj in graph._adj.items():
            for target, edge in _adj.items():

                speed = 0 if edge['time'] == 0 else edge['distance'] / edge['time']

                edge['energy'] = self.energy(edge['distance'], speed)

        return graph

def random_partition(graph, n, rng = None):

    if rng is None:

        rng = np.random.default_rng()

    nodes = list(graph.nodes)

    rng.shuffle(nodes)

    partition = np.array_split(nodes, n)

    return partition

def depot_partition(graph, depots, objective = 'objective'):

    nodes = graph._node
    edges = graph._adj

    costs = {} # dictionary of objective values for paths
    origins = {}

    c = count() # use the count c to avoid comparing nodes (may not be able to)
    heap = [] # heap is heapq with 3-tuples (cost, c, node)

    for origin in depots:

        origins[origin] = origin
        costs[origin] = 0

        heappush(heap, (0, next(c), origin))

    while heap: # Iterating while there are accessible unseen nodes

        # Popping the lowest cost unseen node from the heap
        cost, _, source = heappop(heap)

        for target, edge in edges[source].items():

            # Updating states for edge traversal
            cost_target = cost + edge.get(objective, 1)

            # Updating the weighted cost for the path
            savings = cost_target < costs.get(target, np.inf)

            if savings:
               
                costs[target] = cost_target

                origins[target] = origins[source]

                heappush(heap, (cost_target, next(c), target))

    partition = {depot: [] for depot in depots}

    for node, depot in origins.items():

        if node == depot:

            continue

        partition[depot].append(node)

    return partition

def acceptance_probability(current, tentative, temperature):

    return min([1, np.exp(-(tentative - current) / temperature)])

def acceptance(current, tentative, temperature):

    return acceptance_probability(current, tentative, temperature) > np.random.rand()

def route_cost(graph, route, objective = 'objective'):

    _node = graph._node
    _adj = graph._adj

    cost = 0

    for idx in range(len(route) - 1):

        cost += (
            _adj[route[idx]][route[idx + 1]].get(objective, 0) +
            _node[route[idx]].get(objective, 0)
            )

    return cost

def route_feasible(graph, route, constraints):

    feasible = True

    for constraint in constraints:

        feasible *= constraint(graph, route)

    return feasible

def routes(graph, depot, **kwargs):

    objective = kwargs.get('objective', 'objective')
    constraints = kwargs.get('constraints', [])
    steps = kwargs.get('steps', 1000)
    initial_temperature = kwargs.get('initial_temperature', 1)
    final_temperature = kwargs.get('final_temperature', 0)
    beta = kwargs.get('beta', 1)
    rng = kwargs.get('rng', default_rng)

    _adj = graph._adj

    # Initial routes
    routes = []

    for station in graph.nodes():

        if station == depot:

            continue

        route = [depot, station, depot]

        routes.append(
            (
                route,
                route_cost(graph, route, objective = objective) ** beta
                )
            )

    # Annealing
    temperature = initial_temperature
    delta = (initial_temperature - final_temperature) / steps

    while (temperature > final_temperature) and (len(routes) >= 2):

        temperature -= delta

        index_1, index_2 = rng.choice(list(range(len(routes))), size = 2, replace = False)

        tuple_1 = routes[index_1]
        tuple_2 = routes[index_2]

        route_1, cost_1 = tuple_1
        route_2, cost_2 = tuple_2

        if route_2[1] not in _adj[route_1[-2]]:

            continue

        tentative_route = route_1[:-1] + route_2[1:]

        tentative_cost = route_cost(
            graph, tentative_route, objective = objective
            ) ** beta

        feasible = route_feasible(graph, tentative_route, constraints)

        accept = acceptance(cost_1 + cost_2, tentative_cost, temperature)

        if feasible and accept:

            routes.remove(tuple_1)
            routes.remove(tuple_2)

            routes.append((tentative_route, tentative_cost))

    return [r[0] for r in routes]

def routes_multi_depot(graph, depot, **kwargs):

    objective = kwargs.get('objective', 'objective')
    constraints = kwargs.get('constraints', [])
    steps = kwargs.get('steps', 1000)
    initial_temperature = kwargs.get('initial_temperature', 1)
    final_temperature = kwargs.get('final_temperature', 0)
    beta = kwargs.get('beta', 1)
    rng = kwargs.get('rng', default_rng)

    _adj = graph._adj

    # Initial routes
    routes = []

    for station in graph.nodes():

        if station == depot:

            continue

        route = [depot, station, depot]

        routes.append(
            (
                route,
                route_cost(graph, route, objective = objective) ** beta
                )
            )

    # Annealing
    temperature = initial_temperature
    delta = (initial_temperature - final_temperature) / steps

    while (temperature > final_temperature) and (len(routes) >= 2):

        temperature -= delta

        index_1, index_2 = rng.choice(list(range(len(routes))), size = 2, replace = False)

        tuple_1 = routes[index_1]
        tuple_2 = routes[index_2]

        route_1, cost_1 = tuple_1
        route_2, cost_2 = tuple_2

        depot_1 = route_1[0]
        depot_2 = route_2[0]

        if route_2[1] not in _adj[route_1[-2]]:

            continue

        tentative_route_core = route_1[1:-1] + route_2[1:-1]

        tentative_route_1 = [depot_1] + tentative_route_core + [depot_1]
        tentative_route_2 = [depot_2] + tentative_route_core + [depot_2]

        tentative_cost_1 = route_cost(
            graph, tentative_route_1, objective = objective
            ) ** beta

        tentative_cost_2 = route_cost(
            graph, tentative_route_2, objective = objective
            ) ** beta

        if tentative_cost_1 <= tentative_cost_2:

            feasible = route_feasible(graph, tentative_route_1, constraints)

            accept = acceptance(cost_1 + cost_2, tentative_cost_1, temperature)

            if feasible and accept:

                routes.remove(tuple_1)
                routes.remove(tuple_2)

                routes.append((tentative_route_1, tentative_cost_1))

        else:

            feasible = route_feasible(graph, tentative_route_2, constraints)

            accept = acceptance(cost_1 + cost_2, tentative_cost_2, temperature)

            if feasible and accept:

                routes.remove(tuple_1)
                routes.remove(tuple_2)

                routes.append((tentative_route_2, tentative_cost_2))

    return [r[0] for r in routes]

def routes_graph(graph, routes, index_offset = 0):

    _adj = graph._adj

    new_graph = graph.__class__()

    nodes = [(k, v) for k, v in graph._node.items()]
    new_graph.add_nodes_from(nodes)

    edges = []

    for idx_route, route in enumerate(routes):

        for idx in range(len(route) - 1):

            source = route[idx]
            target = route[idx + 1]

            new_graph._node[source]['route_index'] = idx_route + index_offset

            edges.append((source, target, _adj[source][target]))
    
    new_graph.add_edges_from(edges)

    return new_graph

def route_costs(graph, routes, objectives):

    costs = []

    for route in routes:

        data = {
            'route': route,
        }

        for objective in objectives:

            data[objective] = route_cost(graph, route, objective = objective)

        costs.append(data)

    return costs