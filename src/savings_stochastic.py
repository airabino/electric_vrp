import time
import numpy as np

from operator import itemgetter
from heapq import heappop, heappush
from itertools import count

from .progress_bar import ProgressBar
from .dijkstra import dijkstra

def expectation(x, z = .5):

	mu = x.mean()
	sigma = x.std()

	return mu + z * sigma

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
								limits['weight'] * expectation(pair_savings[objective])
								)

							feasible *= expectation(combined_path_value) >= limits['leg'][0]
							feasible *= expectation(combined_path_value) <= limits['leg'][1]

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

def clarke_wright(graph, objectives, savings, routes, route_values, **kwargs):
	
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

				feasible *= expectation(combined_values[objective]) >= limits['route'][0]
				feasible *= expectation(combined_values[objective]) <= limits['route'][1]

			# If the merged route is an improvement and feasible it is integrated
			if feasible:

				# Adding the merged route
				routes[first_route_index] = combined_route
				route_values[first_route_index] = combined_values

				routes.pop(second_route_index)
				route_values.pop(second_route_index)

	return routes, route_values, success

def savings(graph, objectives, **kwargs):

	savings, initial_routes, initial_route_values = requisites(graph, objectives)

	routes, route_values, success = clarke_wright(
		graph, objectives, savings, initial_routes, initial_route_values, **kwargs
		)

	return routes, route_values, success