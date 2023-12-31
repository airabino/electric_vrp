import numpy as np

def ValidRoute(graph,route,min_weight,weight='length'):

	from_indices=route[:-1]
	to_indices=route[1:]

	valid=True

	for idx in range(len(from_indices)):

		distance=graph[from_indices[idx]][to_indices[idx]][weight]

		if distance<min_weight:

			valid=False
			break

	return valid

def RouteDistance(graph,route,weight='length'):

	from_indices=route[:-1]
	to_indices=route[1:]

	route_distance=0

	for idx in range(len(from_indices)):

		route_distance+=graph._adj[from_indices[idx]][to_indices[idx]][weight]

	return route_distance

def acceptance_probability(e, e_prime, temperature):

	return min([1, np.exp(-(e_prime - e) / temperature)])

def acceptance(e, e_prime, temperature):

	return acceptance_probability(e, e_prime, temperature) > np.random.rand()

def evaluate_route(adjacency, route, route_bounds, leg_bounds, stop_weights):

	n = len(adjacency)

	weights = [0] * n

	validity = [True] * n

	for idx_adj in range(n):

		from_indices = route[1:-2]
		to_indices = route[2:-1]

		weights[idx_adj] += adjacency[idx_adj][route[0], route[1]]
		weights[idx_adj] += adjacency[idx_adj][route[-2], route[-1]]

		for idx_leg in range(len(from_indices)):

			leg_weight = adjacency[idx_adj][from_indices[idx_leg], to_indices[idx_leg]]

			weights[idx_adj] += leg_weight + stop_weights[idx_adj]

			validity[idx_adj] *= leg_weight >= leg_bounds[idx_adj][0]
			validity[idx_adj] *= leg_weight <= leg_bounds[idx_adj][1]

		validity[idx_adj] *= weights[idx_adj] >= route_bounds[idx_adj][0]
		validity[idx_adj] *= weights[idx_adj] <= route_bounds[idx_adj][1]

	return weights, validity

def evaluate_routes(adjacency, routes, route_bounds, leg_bounds, stop_weights):

	weights = []

	validity = []

	for route in routes:

		route_weights, route_validity = evaluate_route(
			adjacency,
			route,
			route_bounds,
			leg_bounds,
			stop_weights,
			)

		weights.append(route_weights)
		validity.append(route_validity)

	return weights, validity

def anneal_route(adjacency, route, leg_bounds, route_bounds, stop_weights, steps=100, initial_temperature=1):

	# At lease 2 destinations need to be present for annealing
	if len(route) < 4:

		return route

	else:

		# Initializing temperature
		temperature = initial_temperature

		# Getting initial route distance
		route_distance=RouteDistance(graph,route,weight=weight)

		# Saving initial route and distance
		initial_route = route.copy()
		initial_route_weight = route_weight

		# print(route_distance)

		# Looping while there is still temperature
		k=0
		while temperature>0:

			# Randomly selecting swap vertices
			swap_indices=np.random.choice(list(range(1,len(route)-1)),size=2,replace=False)

			# Creating tentative route by swapping vertex order
			tentative_route=route.copy()
			tentative_route[swap_indices[0]]=route[swap_indices[1]]
			tentative_route[swap_indices[1]]=route[swap_indices[0]]

			# Checking if tentative route is valid
			valid_route=ValidRoute(graph,tentative_route,min_weight,
				weight=weight)

			# Proceeding only for valid routes
			if valid_route:

				# Computing tentative route distance
				tentative_route_distance=RouteDistance(graph,tentative_route,
					weight=weight)

				# Determining acceptance of tentative route
				accept=Acceptance(route_distance,tentative_route_distance,temperature)

				# print(route_distance,tentative_route_distance,accept,temperature)

				# If accepted, replace route with tentative route
				if accept:
					
					route=tentative_route
					route_distance=tentative_route_distance

			# Reducing temperature
			temperature-=initial_temperature/steps

		if route_distance<=initial_route_distance:

			return route

		else:

			return initial_route
