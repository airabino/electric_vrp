import os
import sys
import time
import numpy as np
import networkx as nx

from copy import deepcopy

from .utilities import ProgressBar

from operator import itemgetter

#CEC Specific functions

def Assign(items,buckets,seed=None):
	'''
	distribute items randomly among sets such that all sets are
	close to evenly represented
	'''

	rng=np.random.default_rng(seed)

	assignment={}

	item_bins=[[] for idx in range(len(buckets))]

	for item in items:

		bin_index=rng.integers(0,len(item_bins))

		item_bins[bin_index].append(item)

	for idx,bucket in enumerate(buckets):

		assignment[bucket]=np.array(item_bins[idx])

	return assignment

def ProcessInputs(graph,parameters):

	vertex_group_field=parameters['vertex_group_field']
	charger_networks=parameters['vertex_group_vehicle_assignment'].keys()

	vehicle_nodes={}

	for network,vehicles in parameters['vertex_group_vehicle_assignment'].items():
		
		network_nodes=np.array(
			[key for key,val in graph._node.items() if \
			 val[vertex_group_field]==network])

		assignment=Assign(network_nodes,vehicles,seed=parameters['rng_seed'])

		for vehicle in vehicles:

			if vehicle in vehicle_nodes.keys():

				vehicle_nodes[vehicle]=np.concatenate(
					(vehicle_nodes[vehicle],assignment[vehicle]))

			else:

				vehicle_nodes[vehicle]=np.concatenate(
					(parameters['depot_vertices'],assignment[vehicle]))

	center_nodes=set(parameters['depot_vertices'])

	depot_nodes=VoronoiCells(graph,center_nodes,weight='length')

	for vehicle in parameters['vehicles']:

		assignment={}

		for depot in parameters['depot_vertices']:

			assignment[depot]=np.intersect1d(vehicle_nodes[vehicle],depot_nodes[depot])
			
		vehicle_nodes[vehicle]=assignment
	
	vehicle_adjacency={}

	for vehicle in parameters['vehicles']:

		vehicle_adjacency[vehicle]={}

		for depot in parameters['depot_vertices']:

			vehicle_adjacency[vehicle][depot]={}
			
			vehicle_adjacency[vehicle][depot]['matrices']=ProduceAdjacency(
				graph,nodelist=vehicle_nodes[vehicle][depot],weights=['length','time'])
		
			node_to_idx,idx_to_node=Assignments(vehicle_nodes[vehicle][depot])
			vehicle_adjacency[vehicle][depot]['node_to_idx']=node_to_idx
			vehicle_adjacency[vehicle][depot]['idx_to_node']=idx_to_node

	return vehicle_adjacency,vehicle_nodes

def ProduceRoutesVehicleDepot(graph,vehicle,depot,parameters,adjacency):

	final_routes=[]
	adj=deepcopy(adjacency)

	constraint_sets=parameters['vehicles'][vehicle]

	for idx_c in range(len(constraint_sets)):

		constraints=constraint_sets[idx_c]
	
		depot_indices=[adj['node_to_idx'][depot]] 

		route_bounds=(
			(constraints['min_route_distance'],constraints['max_route_distance']),
			(constraints['min_route_time'],constraints['max_route_time']),
		)

		leg_bounds=(
			(constraints['min_leg_distance'],constraints['max_leg_distance']),
			(constraints['min_leg_time'],constraints['max_leg_time']),
		)

		stop_weight=(
			constraints['stop_added_distance'],
			constraints['stop_added_time'],
		)

		routes,success=ClarkeWright(
			adj['matrices'],
			depot_indices,
			route_bounds=route_bounds,
			leg_bounds=leg_bounds,
			stop_weight=stop_weight,
			max_iterations=100000,
		)

		routes_nodes=(
			[[adj['idx_to_node'][stop] for stop in route] \
			for route in routes])

		routes_nodes_opt=([
			RouteOptimization(graph,route) for route in routes_nodes])

		len_routes=np.array([len(route) for route in routes_nodes_opt])

		num=-constraints['number']
		indices_keep=np.argsort(len_routes)[num:]
		routes_keep=[routes_nodes_opt[idx_r] for idx_r in indices_keep]

		final_routes.extend(routes_keep)

		for idx in indices_keep:

			visited=routes_nodes_opt[idx][1:-1]
			visited_indices=[adj['node_to_idx'][v] for v in visited]

			for idx_v in visited_indices:

				for idx_m in range(len(adj['matrices'])):

					adj['matrices'][idx_m][idx_v,:]=0
					adj['matrices'][idx_m][:,idx_v]=0

	visited=[]

	for route in final_routes:
		visited.extend(route[1:-1])

	not_visited=np.setdiff1d(list(adjacency['node_to_idx'].keys()),visited+[depot])
	additional_routes=[[depot,nv,depot] for nv in not_visited]
	final_routes.extend(additional_routes)

	return final_routes

#General functions

def VoronoiCells(graph,center_nodes,nodes=None,weight=None):
	'''
	assign nodes to reference nodes by proximity
	'''

	voronoi_cells=nx.voronoi_cells(graph,center_nodes,weight=weight)

	for key in voronoi_cells.keys():

		if nodes is not None:

			voronoi_cells[key]=np.intersect1d(list(voronoi_cells[key]),nodes)

		else:

			voronoi_cells[key]=np.array(list(voronoi_cells[key]))

	return voronoi_cells

def ProduceAdjacency(graph,nodelist=None,weights=[]):
	'''
	Produces list of adjacency matrices for each weight in weights
	'''
	adjacency=[]

	for weight in weights:

		adjacency.append(
			nx.to_numpy_array(graph,nodelist=nodelist,weight=weight)
			)

	return adjacency

def ComputeSavingsMatrix(adjacency,depot_index=0,bounds=(0,np.inf)):
	'''
	Computing the savings matrix from an adjacency matrix.

	Savings is the difference between:

	depot -> destination 1 -> depot -> destination 2 -> depot

	and

	depot -> destination 1 -> destination 2 -> depot


	Values for links with negative savings or invalid lnks will be set to zero

	Requires the definition of a depot location
	'''

	cost_from,cost_to=np.meshgrid(adjacency[:,depot_index],adjacency[depot_index])

	savings=cost_from+cost_to-adjacency

	# Negative savings should nobe be considered
	savings[savings<0]=0

	# No self-savings
	savings[np.diag_indices(adjacency.shape[0])]=0

	#No savings from infeasible edges
	savings[adjacency<bounds[0]]=0
	savings[adjacency>bounds[1]]=0

	return savings

def InitialRoutes(adjacency,depot_indices):
	'''
	Prodces list of initial 1-stop routes for the Clarke Wright algorithm where
	each route connects a stop to the nearest depot
	'''

	depot_indices=np.array(depot_indices)

	if type(adjacency) is np.ndarray:
		adjacency=[adjacency]

	#Pulling destination indices
	destination_indices=np.array([idx for idx in range(adjacency[0].shape[0])])
		# if idx not in depot_indices])

	# Finding closest depots for all destination
	depot_adjacency=adjacency[0][:,depot_indices]
	closest_depots=depot_indices[np.argmin(depot_adjacency,axis=1)]

	# Creating initial routes
	routes=[]
	route_weights=[]

	for destination_index in destination_indices:
		depot_index=closest_depots[destination_index]

		routes.append([
			depot_index,
			destination_index,
			depot_index,
			])

		route_weight=([
			adj[depot_index,destination_index]+
			adj[destination_index,depot_index] \
			for adj in adjacency
		])

		route_weights.append(route_weight)

	return routes,route_weights

def RouteTime(graph,route,vertex_time_field='time',edge_time_field='time'):

	from_indices=route[:-1]
	to_indices=route[1:]

	route_time=0

	for idx in range(len(from_indices)):

		# print(graph._adj[from_indices[idx]][to_indices[idx]])

		route_time+=graph._adj[from_indices[idx]][to_indices[idx]][edge_time_field]
		route_time+=graph._node[to_indices[idx]][vertex_time_field]

	return route_time

def RouteInformation(graph,route,distance_field='length',time_field='time'):

	from_indices=route[:-1]
	to_indices=route[1:]

	route_distance=0
	route_time=0

	for idx in range(len(from_indices)):

		route_distance+=graph._adj[from_indices[idx]][to_indices[idx]][distance_field]

		route_time+=graph._adj[from_indices[idx]][to_indices[idx]][time_field]
		route_time+=graph._node[to_indices[idx]][time_field]

	return route_distance,route_time

def Assignments(nodes):

	node_to_idx={nodes[idx]:idx for idx in range(len(nodes))}
	idx_to_node={val:key for key,val in node_to_idx.items()}

	return node_to_idx,idx_to_node

def FindRoutes(routes,node_0,node_1):

	first_route_index=[]
	second_route_index=[]

	itemget=itemgetter(1)

	result=filter(
		lambda idx: itemget(routes[idx])==(node_0),
		list(range(len(routes)))
		)

	for res in result:

		first_route_index=res

	itemget=itemgetter(-2)

	result=filter(
		lambda idx: itemget(routes[idx])==(node_1),
		list(range(len(routes)))
		)

	for res in result:

		second_route_index=res

	

	return first_route_index,second_route_index

def ClarkeWright(
	adjacency,
	depot_indices,
	route_bounds,
	leg_bounds,
	stop_weight,
	max_iterations=100000,
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

	# #Dictionary assignemnts for graph indexing
	# node_to_idx,idx_to_node=Assignments(graph)
	
	#Computing savings matrices for all adjacency matrices and all depots
	savings=[]

	for idx,adj in enumerate(adjacency):

		savings_adj=[]

		for depot_index in depot_indices:

			savings_adj.append(
				ComputeSavingsMatrix(adj,depot_index,leg_bounds[idx])
				)

		savings.append(np.array(savings_adj))

	# Initializing routes - initial assumption is that locations will be served by
	# closest depot. All initial routes are 1-stop (depot -> destination -> depot)
	routes,route_weights=InitialRoutes(adjacency,depot_indices)

	# print(route_weights)

	routes=np.array(routes)
	route_weights=np.array(route_weights)

	# print(routes.shape,route_weights.shape)

	combinable=(route_weights[:,0]/2<=leg_bounds[0][1])&(route_weights[:,0]>0)
	non_combinable=(route_weights[:,0]/2>=leg_bounds[0][1])|(route_weights[:,0]<=0)
	# print(combinable,non_combinable)

	savings[0][:,non_combinable,:]=0
	savings[0][:,:,non_combinable]=0

	# print(non_combinable.shape,savings[0].shape)

	routes=routes[combinable].tolist()
	route_weights=route_weights[combinable].tolist()

	# print(len(routes),len(route_weights))

	k=0

	# Implementing savings
	success=False
	for idx in range(max_iterations):

		# Computing remaining savings
		remaining_savings=savings[0].sum()

		# If all savings incorporated then exit
		if remaining_savings==0:
			success=True
			break

		# Finding link with highest remaining savings
		best_savings_link=np.unravel_index(np.argmax(savings[0]),savings[0].shape)

		t0=time.time()

		# Finding routes to merge - the routes can only be merged if there are
		# routes which start with and end with the to and from index respectively.
		# Routes with different depots can be merged if the savings call for it but
		# all routes have to begin and terminate at the same depot

		first_route_index=[]
		second_route_index=[]

		first_route_index,second_route_index=FindRoutes(
			routes,
			best_savings_link[1],
			best_savings_link[2],
			)
		# print(best_savings_link)

		k+=time.time()-t0

		# print([idx,primary_savings.sum(),k/(idx+1)],end='\r')

		# If a valid merge combination is found create a tentative route and evaluate
		if first_route_index and second_route_index:

			if routes[first_route_index][0]==routes[second_route_index][-1]:

				# Combining non-depot elements of merged routes
				tentative_route_core=(
					routes[first_route_index][1:-1]+routes[second_route_index][1:-1])

				# Creating tentative routes based out of each depot
				tentative_routes=(
					[[depot]+tentative_route_core+[depot]\
					 for depot in depot_indices])

				# tentative_routes=(
				# 	[routes[first_route_index][:-1]+routes[second_route_index][1:]]
				# 	)

				# Finding the best of the tentative routes
				tentative_route_weights=[]

				for tentative_route in enumerate(tentative_routes):

					tentative_route_weight=[]

					for idx_savings,savings_matrix in enumerate(savings):

						tentative_route_weight.append(
							route_weights[first_route_index][idx_savings]+
							route_weights[second_route_index][idx_savings]-
							savings_matrix[*best_savings_link]
							)
					
					tentative_route_weights.append(
						tentative_route_weight
						)

				selected_route_index=np.argmin([rw[0] for rw in tentative_route_weights])

				selected_tentative_route=tentative_routes[selected_route_index]

				selected_tentative_route_weight=(
					tentative_route_weights[selected_route_index])


				# Checking if the merged route represents savings over the individual routes
				improvement=selected_tentative_route_weight[0]<=(
					route_weights[first_route_index][0]+
					route_weights[second_route_index][0]
					)

				selected_tentative_route_offset=[]

				for idx_offset,offset in enumerate(stop_weight):

					selected_tentative_route_offset.append(
						sum([offset for idx in range(1,len(selected_tentative_route)-1)])
						)

				# Checking if the merged route is feasible
				checks=[]

				for idx_bounds,bounds in enumerate(route_bounds):

					checks.append(
						(
							selected_tentative_route_weight[idx_bounds]+
							selected_tentative_route_offset[idx_bounds]
						)>=bounds[0]
						)

					checks.append(
						(
							selected_tentative_route_weight[idx_bounds]+
							selected_tentative_route_offset[idx_bounds]
						)<=bounds[1]
						)


				feasible=np.all(checks)

				# If the merged route is an improvement and feasible it is integrated
				if improvement and feasible:

					# Adding the merged route
					routes[first_route_index]=selected_tentative_route
					route_weights[first_route_index]=selected_tentative_route_weight

					# Removing the individual routes
					routes.remove(routes[second_route_index])
					route_weights.remove(route_weights[second_route_index])

		# Removing the savings
		savings[0][:,best_savings_link[1],best_savings_link[2]]=0
		savings[0][:,best_savings_link[2],best_savings_link[1]]=0

	return routes,success

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

def AcceptanceProbability(e,e_prime,temperature):

	return min([1,np.exp(-(e_prime-e)/temperature)])

def Acceptance(e,e_prime,temperature):

	return AcceptanceProbability(e,e_prime,temperature)>np.random.rand()

def RouteOptimization(graph,route,steps=100,weight='length',
	initial_temperature=1,min_weight=0):

	# At lease 2 destinations need to be present for annealing
	if len(route)<4:

		return route

	else:

		# Initializing temperature
		temperature=initial_temperature

		# Getting initial route distance
		route_distance=RouteDistance(graph,route,weight=weight)

		# Saving initial route and distance
		initial_route=route.copy()
		initial_route_distance=route_distance

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
