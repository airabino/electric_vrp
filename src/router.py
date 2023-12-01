import os
import sys
import time
import numpy as np
import networkx as nx

from .utilities import ProgressBar


def ComputeSavingsMatrix(graph,depot_index=0,distance_field='distance',
	min_distance=0) -> np.ndarray:
	'''
	Computing the savings matrix from a graph. Savings is the difference between:

	home -> destination 1 -> home -> destination 2 -> home

	and

	home -> destination 1 -> destination 2 -> home


	Values for links with negative savings or invalid lnks will be set to zero

	Requires the definition of a home location
	'''

	adjacency=nx.to_numpy_array(graph,weight=distance_field)

	cost_from,cost_to=np.meshgrid(adjacency[:,depot_index],adjacency[depot_index])

	savings=cost_from+cost_to-adjacency

	savings[savings<0]=0
	savings[np.diag_indices(adjacency.shape[0])]=0
	savings[adjacency<min_distance]=0

	return savings

def InitialRoutes(graph,depot_field='is_depot',distance_field='distance'):
	'''
	Prodces list of initial 1-stop routes for the Clarke Wright algorithm where
	each route connects a stop to the nearest depot
	'''

	# Pulling depot indices
	depot_indices=np.array([key for key,val in graph._node.items() if val[depot_field]])

	#Pulling destination indices
	destination_indices=np.array(
		[key for key,val in graph._node.items() if not val[depot_field]])

	# Pulling adjacency matrix
	adjacency=nx.to_numpy_array(graph,weight=distance_field)

	# Finding closest depots for all destination
	depot_adjacency=adjacency[:,depot_indices]
	closest_depots=depot_indices[np.argmin(depot_adjacency,axis=1)]

	# Creating initial routes
	routes=[]

	for destination_index in destination_indices:
		depot_index=closest_depots[destination_index]

		routes.append([depot_index,destination_index,depot_index])

	return routes

def RouteDistance(graph,route,distance_field='distance'):

	from_indices=route[:-1]
	to_indices=route[1:]

	route_distance=0

	for idx in range(len(from_indices)):

		route_distance+=graph[from_indices[idx]][to_indices[idx]][distance_field]

	return route_distance

def RouteTime(graph,route,vertex_time_field='time',edge_time_field='time'):

	from_indices=route[:-1]
	to_indices=route[1:]

	route_time=0

	for idx in range(len(from_indices)):

		route_time+=graph[from_indices[idx]][to_indices[idx]][edge_time_field]
		route_time+=graph._node[to_indices[idx]][vertex_time_field]

	return route_time

def ValidRoute(graph,route,min_distance,distance_field='distance'):

	from_indices=route[:-1]
	to_indices=route[1:]

	valid=True

	for idx in range(len(from_indices)):

		distance=graph[from_indices[idx]][to_indices[idx]][distance_field]

		if distance<min_distance:

			valid=False
			break

	return valid

def ClarkeWright(
	graph,
	depot_field='is_depot',
	load_field='load',
	distance_field='distance',
	vertex_time_field='time',
	edge_time_field='time',
	vehicle_time=np.inf,
	vehicle_range=np.inf,
	max_iterations=10000,
	min_distance=0,
	):
	
	'''
	Implements Clarke and Wright savings algorith for solving the VRP with flexible
	numbers of vehicles per depot. Vehicles have range and capacity limitations. This
	implementation allows for multiple depots.

	The Clarke and Wright method attempts to implment all savings available in a savings
	matrix by iteratively merging routes. Routes are initialized as 1-stop routes between
	each destination and its closest depot. During iteration, savings are implemented
	by merging the routes which allow for the capture of the greatest savings link
	available.
	'''

	# Pulling depot indices
	depot_indices=[key for key,val in graph._node.items() if val[depot_field]]
	# print(depot_indices)
	
	#Computing savings matrices for all depots
	savings=np.array(
		[ComputeSavingsMatrix(graph,depot_index,min_distance=min_distance)\
		 for depot_index in depot_indices])
	# print(savings)

	# Initializing routes - initial assumption is that locations will be served by
	# closest depot. All initial routes are 1-stop (depot -> destination -> depot)
	routes=InitialRoutes(graph,depot_field)
	route_distances=[RouteDistance(graph,route,distance_field) for route in routes]



	# Implementing savings
	success=False
	# print(max_iterations)
	for idx in range(max_iterations):
		# pass

		# Computing remaining savings
		remaining_savings=savings.sum()

		# If all savings incorporated then exit
		if remaining_savings==0:
			success=True
			break

		# Finding link with highest remaining savings
		best_savings_link=np.unravel_index(np.argmax(savings),savings.shape)

		# Finding routes to merge - the routes can only be merged if there are
		# routes which start with and end with the to and from index respectively.
		# Routes with different depots can be merged if the savings call for it but
		# all routes have to begin and terminate at the same depot

		first_route_index=[]
		second_route_index=[]

		for idx1,route in enumerate(routes):

			if best_savings_link[1] in [route[1],route[-2]]:
				first_route_index=idx1

			elif best_savings_link[2] in [route[1],route[-2]]:
				second_route_index=idx1

		# If a valid merge combination is found create a tentative route and evaluate
		if first_route_index and second_route_index:

			# Combining non-depot elements of merged routes
			tentative_route_core=(
				routes[first_route_index][1:-1]+routes[second_route_index][1:-1])

			# Checking if tentative route is valid
			valid_tentative_route=ValidRoute(graph,tentative_route_core,min_distance,
				distance_field=distance_field)

			# Only proceeding for valid route cores
			if valid_tentative_route:

				# Creating tentative routes based out of each depot
				tentative_routes=(
					[[depot_index]+tentative_route_core+[depot_index]\
					 for depot_index in depot_indices])

				# Finding the best of the tentative routes
				tentative_route_distances=(
					[RouteDistance(graph,tentative_route,distance_field)\
					 for tentative_route in tentative_routes])

				selected_tentative_route=tentative_routes[np.argmin(tentative_route_distances)]
				selected_tentative_route_distance=(
					tentative_route_distances[np.argmin(tentative_route_distances)])

				# Checking if the merged route represents savings over the individual routes
				improvement=selected_tentative_route_distance<=(
					route_distances[first_route_index]+route_distances[second_route_index])

				# Calculating route traversal time
				selected_tentative_route_time=RouteTime(
					graph,selected_tentative_route,
					vertex_time_field=vertex_time_field,
					edge_time_field=edge_time_field)

				# Checking if the merged route is feasible
				feasible=(
					(selected_tentative_route_distance<=vehicle_range)&
					(selected_tentative_route_time<=vehicle_time))

				# If the merged route is an improvement and feasible it is integrated
				if improvement and feasible:

					# Adding the merged route
					routes[first_route_index]=selected_tentative_route
					route_distances[first_route_index]=selected_tentative_route_distance

					# Removing the individual routes
					routes.remove(routes[second_route_index])
					route_distances.remove(route_distances[second_route_index])


		# Removing the savings
		savings[:,best_savings_link[1],best_savings_link[2]]=0
		savings[:,best_savings_link[2],best_savings_link[1]]=0

	return routes,success

def AcceptanceProbability(e,e_prime,temperature):

	return min([1,np.exp(-(e_prime-e)/temperature)])

def Acceptance(e,e_prime,temperature):

	return AcceptanceProbability(e,e_prime,temperature)>np.random.rand()

def RouteOptimization(graph,route,steps=100,distance_field='distance',
	initial_temperature=1,min_distance=0):

	# At lease 2 destinations need to be present for annealing
	if len(route)<4:

		return route

	else:

		# Initializing temperature
		temperature=initial_temperature

		# Getting initial route distance
		route_distance=RouteDistance(graph,route,distance_field=distance_field)

		# Saving initial route and distance
		initial_route=route.copy()
		initial_route_distance=route_distance.copy()

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
			valid_route=ValidRoute(graph,tentative_route,min_distance,
				distance_field=distance_field)

			# Proceeding only for valid routes
			if valid_route:

				# Computing tentative route distance
				tentative_route_distance=RouteDistance(graph,tentative_route,
					distance_field=distance_field)

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
