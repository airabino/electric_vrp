import os
import sys
import time
import numpy as np
import networkx as nx

from copy import deepcopy
from operator import itemgetter
from itertools import product as iter_prod

from .utilities import ProgressBar
from .graph import subgraph
from .clarke_wright  import *
from .simulated_annealing import *

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

def voronoi_cells(graph, center_nodes, nodes = None, weight = None, **kwargs):
	'''
	assign nodes to reference nodes by proximity
	'''

	voronoi_cells = nx.voronoi_cells(graph, center_nodes, weight = weight)

	for key in voronoi_cells.keys():

		if nodes is not None:

			voronoi_cells[key] = np.intersect1d(list(voronoi_cells[key]), nodes)

		else:

			voronoi_cells[key] = np.array(list(voronoi_cells[key]))

	return voronoi_cells

def assign_depot(graph, depot_nodes, nodes = None, weight = None, **kwargs):
	'''
	Assign nodes to depots using weighted Voronoi cells 
	'''
	kwargs.setdefault('field', 'depot')
	kwargs.setdefault('overwrite_depots', True)

	field = kwargs['field']

	vc = voronoi_cells(graph, depot_nodes, nodes = nodes, weight = weight)

	for depot in depot_nodes:

		for node in vc[depot]:

			if kwargs['overwrite_depots'] or (field not in graph._node[node].keys()):

				graph._node[node][field] = depot

	for node in graph.nodes:

		if field not in graph._node[node].keys():

			graph._node[node][field] = ''

	return graph

def assign_rng(graph, seed = None, field = 'rng', **kwargs):
	'''
	Assign a random number to each node
	'''

	rng  = np.random.default_rng(seed)

	for node in graph.nodes:
		graph._node[node][field] = rng.random()

	return graph

def assign_vehicle(graph, vehicles, field = 'vehicle', **kwargs):
	'''
	Assigns vehicles based on vehicle node_criteria functions
	'''

	for node in graph.nodes:

		graph._node[node][field] = []

	for vehicle, vehicle_information in vehicles.items():

		for key, fun in vehicle_information['node_criteria'].items():

			if type(fun) is str:

				vehicles[vehicle]['node_criteria'][key] = eval(fun)
	
	for vehicle, vehicle_information in vehicles.items():

		for node in graph.nodes:

			meets_criteria = True

			try:

				for key, fun in vehicle_information['node_criteria'].items():

					meets_criteria *= fun(graph._node[node])

			except:

				meets_criteria = False

			if meets_criteria:

				graph._node[node][field].append(vehicle)

	return graph

def produce_subgraphs(graph, categories, **kwargs):

	subgraphs = {}

	combinations = list(iter_prod(*[v for v in categories.values()]))

	# print(combinations)

	for combination in combinations:

		nodelist = []

		for node in graph.nodes:

			include = True

			for idx, field in enumerate(categories.keys()):

				val = graph._node[node][field]

				if hasattr(val, '__iter__'):

					if len(val) == 0:

						include = False

					else:

						include *= combination[idx] in graph._node[node][field]

				else:

					include *= graph._node[node][field] == combination[idx]

			if include:

				nodelist.append(node)

		subgraphs[combination] = subgraph(graph, nodelist)

	return subgraphs

def produce_adjacency(subgraphs, weights = [], **kwargs):

	adjacency = {}

	for key, value in subgraphs.items():

		adjacency[key] = adjacency_matrices(value, weights = weights)

	return adjacency

def adjacency_matrices(graph, nodelist = None, weights = [], **kwargs):
	'''
	Produces list of adjacency matrices for each weight in weights
	'''
	adjacency = []

	for weight in weights:

		adjacency.append(nx.to_numpy_array(
			graph,
			nodelist = nodelist,
			weight = weight,
			nonedge = np.inf,
			))

	return adjacency

def produce_assignments(subgraphs, **kwargs):

	subgraph_assignments = {}

	for key, value in subgraphs.items():

		node_to_idx, idx_to_node = assignments(list(value.nodes))

		subgraph_assignments[key] = {}
		subgraph_assignments[key]['node_to_idx'] = node_to_idx
		subgraph_assignments[key]['idx_to_node'] = idx_to_node

	return subgraph_assignments

def assignments(nodes, **kwargs):

	node_to_idx = {nodes[idx]: idx for idx in range(len(nodes))}
	idx_to_node = {val: key for key, val in node_to_idx.items()}

	return node_to_idx, idx_to_node

def produce_bounds(subgraphs, vehicles, weights, **kwargs):

	route_bounds = {}
	leg_bounds = {}
	stop_weights = {}

	for key, value in subgraphs.items():

		vehicle, _ = key

		route_bounds[key] = []
		leg_bounds[key] = []
		stop_weights[key] = []

		for weight in weights:

			route_bounds[key].append(vehicles[vehicle]["route_bounds"][weight])
			leg_bounds[key].append(vehicles[vehicle]["leg_bounds"][weight])
			stop_weights[key].append(vehicles[vehicle]["stop_weights"][weight])

	return route_bounds, leg_bounds, stop_weights

def depot_router(adjacency, depot, route_bounds, leg_bounds, stop_weights, **kwargs):

	kwargs.setdefault('steps_routes', 1000)
	kwargs.setdefault('steps_route', 100)

	routes, success = clarke_wright(
		adjacency,
		depot,
		route_bounds,
		leg_bounds,
		stop_weights,
		)
	
	try:

		routes = anneal_routes(
			adjacency,
			routes,
			route_bounds,
			leg_bounds,
			stop_weights,
			steps = kwargs['steps_routes'],
			)

	except:

		pass

	try:
	
		for route in routes:

			route = anneal_route(
				adjacency,
				opt_route,
				route_bounds,
				leg_bounds,
				stop_weights,
				steps = kwargs['steps_route'],
				)
	
	except:

		pass

	return routes, success

def produce_routing_inputs(graph, parameters, **kwargs):

	# Assigning depots by Voronoi cells unless otherwise specified
	depot_nodes = parameters['depot_nodes']
	voronoi_weight = parameters['voronoi_weight']

	graph = assign_depot(graph, depot_nodes, voronoi_weight = voronoi_weight, **kwargs)

	# Assinging random number to each node for selection
	seed = parameters['rng_seed']

	graph = assign_rng(graph, seed, **kwargs)
	
	# Assinging vehicles to nodes
	vehicles = parameters['vehicles']

	graph = assign_vehicle(graph, vehicles, **kwargs)

	# Producing subgraphs for routing
	categories = {
		'vehicle': list(parameters['vehicles'].keys()),
		'depot': parameters['depot_nodes'],
	}

	subgraphs = produce_subgraphs(graph, categories, **kwargs)

	# Producing adjacency matrices for routing
	route_weights = parameters['route_weights']

	adjacency = produce_adjacency(subgraphs, route_weights, **kwargs)

	# Producing assignments for routing
	assignments = produce_assignments(subgraphs, **kwargs)

	# Producing bounds
	route_bounds, leg_bounds, stop_weights = produce_bounds(
		subgraphs, vehicles, route_weights, **kwargs)

	# Combining
	cases = {}

	for key in subgraphs.keys():

		cases[key]={}

		cases[key]['graph'] = subgraphs[key]
		cases[key]['adjacency'] = adjacency[key]
		cases[key]['assignments'] = assignments[key]
		cases[key]['route_bounds'] = route_bounds[key]
		cases[key]['leg_bounds'] = leg_bounds[key]
		cases[key]['stop_weights'] = stop_weights[key]
	
	return cases
