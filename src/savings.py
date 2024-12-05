import time
import numpy as np
import networkx as nx

from operator import itemgetter
from heapq import heappop, heappush, _heappop_max, _heapify_max
from itertools import count

from .progress_bar import ProgressBar
from .dijkstra import dijkstra

default_rng = np.random.default_rng()

def add_depot_legs(graph, depots, objectives):

    _, depot_paths = dijkstra(
        graph,
        depots,
        weights = {key: np.inf for key in objectives.keys()},
        return_paths = True
    )

    for key, value in depot_paths.items():

        graph._node[key]['depot'] = value['source']
        graph._node[key]['depot_leg'] = value['value']

    return graph

def find_routes(routes, node_0, node_1):

    first_route_index = []
    second_route_index = []

    # print(len(routes))

    itemget = itemgetter(1)

    result = filter(
        lambda idx: itemget(routes[idx]) == (node_0),
        list(range(len(routes)))
        )

    for res in result:
        # print(res)

        first_route_index = res

    itemget = itemgetter(-2)

    result = filter(
        lambda idx: itemget(routes[idx]) == (node_1),
        list(range(len(routes)))
        )

    for res in result:

        # print(res)

        second_route_index = res

    return first_route_index, second_route_index

def pre_process(graph, stations, depots, objective = 'objective', **kwargs):
    '''
    Computing the savings matrix from an adjacency matrix.

    Savings is the difference between:

    depot -> destination 1 -> depot -> destination 2 -> depot

    and

    depot -> destination 1 -> destination 2 -> depot

    '''

    _node = graph._node
    _adj = graph._adj

    # Creating initial routes as one-step routes from closest depot
    initial_routes = []
    initial_route_costs = []

    station_depots = {station: {'depot': depots[0], 'cost': 0} for station in stations}

    for station in stations:

        depot_costs = []

        for depot in depots:

            depot_costs = (
                _adj[depot][station].get(objective, 0) +
                _adj[station][depot].get(objective, 0)
                )

        depot_index = np.argmin(depot_costs)
        station_depot = depots[depot_index]

        # station_depot = depots[depot_index]
        station_depots[station]['depot'] = station_depot
        station_depots[station]['cost'] = (
            _adj[station_depot][station].get(objective, 0) +
            _node[station].get(objective, 0) +
            _adj[station][station_depot].get(objective, 0)
            )

    # Creating the savings tuples
    savings = []

    for source in stations:
        for target in stations:

            source_depot = station_depots[source]['depot']
            target_depot = station_depots[target]['depot']

            comparison_cost = (
                station_depots[source]['cost'] + station_depots[target]['cost']
                )

            combined_cost_source_depot = (
                _adj[source_depot][source].get(objective, 0) +
                _node[source].get(objective, 0) +
                _adj[source][target].get(objective, 0) +
                _node[target].get(objective, 0) +
                _adj[target][source_depot].get(objective, 0)
                )

            combined_cost_target_depot = (
                _adj[target_depot][source].get(objective, 0) +
                _node[source].get(objective, 0) +
                _adj[source][target].get(objective, 0) +
                _node[target].get(objective, 0) +
                _adj[target][target_depot].get(objective, 0)
                )

            if combined_cost_source_depot < comparison_cost:

                delta = comparison_cost - combined_cost_source_depot
                route = (source_depot, source, target, source_depot)

                savings.append((delta, route))

            elif combined_cost_target_depot < comparison_cost:

                delta = comparison_cost - combined_cost_target_depot
                route = (target_depot, source, target, target_depot)

                savings.append((delta, route))


    initial_routes = [(v['depot'], k, v['depot']) for k, v in station_depots.items()]
    initial_route_costs = [v['cost'] for k, v in station_depots.items()]

    return savings, initial_routes, initial_route_costs

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

def route_cost(_adj, route, objective = 'objective'):

    cost = 0

    for idx in range(len(route) - 1):

        cost += _adj[route[idx]][route[idx + 1]][objective]

    return cost

def route_feasible(graph, route, constraints):

    feasible = True

    for constraint in constraints:

        feasible *= constraint(graph, route)

    return feasible

def routes(graph, depot, **kwargs):

    beta = kwargs.get('beta', (1, 1))

    beta_0 = 1e-10

    print(beta)

    objective = kwargs.get('objective', 'objective')
    constraints = kwargs.get('constraints', [])
    steps = kwargs.get('steps', 1000)
    initial_temperature = kwargs.get('initial_temperature', 1)
    final_temperature = kwargs.get('final_temperature', 0)
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
                route_cost(_adj, route, objective = objective) ** beta[1]
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

        tentative_cost_1 = route_cost(_adj, tentative_route_1, objective = objective) ** beta[1]
        tentative_cost_2 = route_cost(_adj, tentative_route_2, objective = objective) ** beta[1]

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

        

    return routes

def savings_graph(graph, partition, objective = 'objective'):

    for depot, stations in partition.items():
        for station in stations:

            graph._node[station]['depot'] = depot

    for source, node in graph._node.items():

        depot = node['depot']
        
        for target, edge in graph._adj[source].items():

            edge['savings'] = (
                graph._adj[source][depot][objective] +
                graph._adj[depot][target][objective] -
                edge[objective]
            )

    return graph

def modval(graph, partition, objective = 'objective'):

    value = 0.

    for depot, stations in partition.items():
        for source in stations:
            for target in stations:

                value += graph._adj[source][target][objective]

    return value

def anneal_partition(graph, partition, objective = 'objective', steps = 1000):

    depots = list(partition.keys())

    # Setting temperature and cooling rate
    temperature = 1
    delta = 1 / steps

    # Initializing rng
    rng = np.random.default_rng()

    current_value = modval(graph, partition, objective = objective)

    # Adding savings to the graph
    # graph = savings_graph(graph, partition, objective = objective)

    # current_value = nx.community.modularity(
    #     graph, list(partition.values()), weight = 'time',
    #     )

    for step in range(steps):

        depot_from, depot_to = rng.choice(depots, size = (2, ), replace = False)

        part_from = partition[depot_from]
        part_to = partition[depot_to]

        node = rng.choice(part_from)

        part_to.append(node)
        part_from.remove(node)

        # graph = savings_graph(graph, partition, objective = objective)

        # tentative_value = nx.community.modularity(
        #     graph, list(partition.values()), weight = 'time',
        #     )

        tentative_value = modval(graph, partition, objective = objective)

        accept = acceptance(current_value, tentative_value, temperature)
        # accept = acceptance(tentative_value, current_value, temperature)
        # accept = tentative_value < current_value
        # print(accept, tentative_value, current_value)

        if accept:

            current_value = tentative_value
            # break

        else:

            part_to.remove(node)
            part_from.append(node)

        temperature -= delta

    return partition

def clarke_wright(graph, stations, depots, objective = 'objective', **kwargs):

    max_iterations = min([kwargs.get('max_iterations', int(1e7)), len(savings)])
    progress_bar_kw = kwargs.get('progress_bar_kw', {})

    # Pre-processing
    savings, initial_routes, initial_route_costs = pre_process(
        graph, stations, depots, objective = objective,
    )

    # Converting savings to max-heap
    _heapify_max(savings)

    # Implementing savings
    success = False

    for idx in ProgressBar(range(max_iterations), **progress_bar_kw):

        # If all savings incorporated then exit
        if not savings:

            success = True

            break

        delta, route = _heappop_max(savings)

        # Finding routes to merge - the routes can only be merged if there are
        # routes which start with and end with the to and from index respectively.

        first_route_index = []
        second_route_index = []

        first_route_index, second_route_index = find_routes(
            routes,
            source,
            target,
            )

        # If a valid merge combination is found create a tentative route and evaluate
        if first_route_index and second_route_index:

            # Creating tentative route
            combined_route = (
                routes[first_route_index][:-1] +
                routes[second_route_index][1:]
                )

            # Finding the best of the tentative routes
            combined_values = {}
            feasible = True

            for objective, limits in objectives.items():

                combined_values[objective] = (
                    route_values[first_route_index][objective] +
                    route_values[second_route_index][objective] +
                    delta[objective]
                    )

                feasible *= combined_values[objective] >= limits['route'][0]
                feasible *= combined_values[objective] <= limits['route'][1]

            # If the merged route is an improvement and feasible it is integrated
            if feasible:

                # Adding the merged route
                routes[first_route_index] = combined_route
                route_values[first_route_index] = combined_values

                # Removing the individual routes
                routes.pop(second_route_index)
                route_values.pop(second_route_index)

    return routes, route_values, success

def requisites(graph, objectives, **kwargs):
    '''
    Computing the savings matrix from an adjacency matrix.

    Savings is the difference between:

    depot -> destination 1 -> depot -> destination 2 -> depot

    and

    depot -> destination 1 -> destination 2 -> depot

    '''

    adjacency = graph._adj
    nodes = graph._node

    primary = list(objectives.keys())[0]

    seen = {s: {t: False for t in graph.nodes} for s in graph.nodes}

    savings = []
    initial_routes = []
    initial_route_values = []

    counter = count()

    for source, source_links in adjacency.items():

        source_depot = nodes[source]['depot']
        source_depot_leg = nodes[source]['depot_leg']

        if source != source_depot:

            initial_routes.append([source_depot, source, source_depot])
            initial_route_values.append({
                key: value * 2 + nodes[source]['value'][key] \
                for key, value in source_depot_leg.items()
            })
            for target, target_link in source_links.items():

                if (source != target) and (not seen[source][target]):

                    seen[source][target] = True
                    seen[target][source] = True

                    target_depot = nodes[target]['depot']
                    target_depot_leg = nodes[target]['depot_leg']

                    if source_depot == target_depot:

                        pair_savings = {}
                        savings_weighted_sum = 0
                        feasible = True

                        for objective, limits in objectives.items():

                            combined_path_value = (
                                target_link[objective]
                                )

                            naive_path_value = (
                                source_depot_leg[objective] +
                                target_depot_leg[objective]
                                )

                            pair_savings[objective] = (
                                combined_path_value - naive_path_value
                                )

                            savings_weighted_sum += (
                                limits['weight'] * pair_savings[objective]
                                )

                            feasible *= combined_path_value >= limits['leg'][0]
                            feasible *= combined_path_value <= limits['leg'][1]

                        if feasible and (savings_weighted_sum < 0):

                            heappush(
                                savings,
                                (
                                    savings_weighted_sum,
                                    next(counter),
                                    pair_savings,
                                    source,
                                    target
                                    ),
                                )

    return savings, initial_routes, initial_route_values

def clarke_wright1(graph, objectives, savings, routes, route_values, **kwargs):
    
    kwargs.setdefault('max_iterations', int(1e7))

    max_iterations = min([kwargs.get('max_iterations', int(1e7)), len(savings)])

    # savings, routes, route_values = requisites(graph, objectives)

    # Implementing savings
    success = False

    for idx in ProgressBar(
        range(max_iterations), **kwargs.get('pb_kwargs', {})
        ):

        # Computing remaining savings
        remaining_savings = len(savings)

        # If all savings incorporated then exit
        if remaining_savings == 0:

            success = True

            break

        _, _, delta, source, target = heappop(savings)

        # Finding routes to merge - the routes can only be merged if there are
        # routes which start with and end with the to and from index respectively.

        first_route_index = []
        second_route_index = []

        first_route_index, second_route_index = find_routes(
            routes,
            source,
            target,
            )

        # If a valid merge combination is found create a tentative route and evaluate
        if first_route_index and second_route_index:

            # Creating tentative route
            combined_route = (
                routes[first_route_index][:-1] +
                routes[second_route_index][1:]
                )

            # Finding the best of the tentative routes
            combined_values = {}
            feasible = True

            for objective, limits in objectives.items():

                combined_values[objective] = (
                    route_values[first_route_index][objective] +
                    route_values[second_route_index][objective] +
                    delta[objective]
                    )

                feasible *= combined_values[objective] >= limits['route'][0]
                feasible *= combined_values[objective] <= limits['route'][1]

            # If the merged route is an improvement and feasible it is integrated
            if feasible:

                # Adding the merged route
                routes[first_route_index] = combined_route
                route_values[first_route_index] = combined_values

                # Removing the individual routes
                routes.pop(second_route_index)
                route_values.pop(second_route_index)

    return routes, route_values, success

def savings(graph, objectives, **kwargs):

    savings, initial_routes, initial_route_values = requisites(graph, objectives)

    routes, route_values, success = clarke_wright(
        graph, objectives, savings, initial_routes, initial_route_values, **kwargs
        )

    return routes, route_values, success