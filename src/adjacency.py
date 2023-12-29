import os
import sys
import time
import momepy
import numpy as np
import pandas as pd
import geopandas as gpd
import pickle as pkl
import networkx as nx

from scipy.spatial import KDTree

from .utilities import ProgressBar,Haversine
from .dijkstra import Dijkstra

# Routing functions and related objects

def node_assignment_from_coordinates(graph, x, y):
	'''
	Creates an assignment dict mapping between points and closest nodes
	'''

	# Pulling coordinates from graph
	xy_graph=np.array([(n['x'], n['y']) for n in graph._node.values()])
	xy_graph=xy_graph.reshape((-1,2))

	# Creating spatial KDTree for assignment
	kd_tree=KDTree(xy_graph)

	# Shaping input coordinates
	xy_query=np.vstack((x, y)).T

	# Computing assignment
	result=kd_tree.query(xy_query)

	node_assignment=[]

	for idx in range(len(x)):

		node=result[1][idx]

		node_assignment.append({
			'id':node,
			'query':xy_query[idx],
			'result':xy_graph[node],
			})

	return node_assignment

def single_source_dijkstra(graph, source, targets, weights, return_paths = False):

	if not hasattr(targets, '__iter__'):
		targets=[targets]

	route_weights, routes = Dijkstra(
		graph,
		[source],
		targets,
		weights,
		return_paths,
		)

	keys = np.array(list(route_weights.keys()))
	route_information = np.array(list(route_weights.values()))

	select = np.isin(keys, targets)

	keys_select = keys[select]
	route_information_select = route_information[select]

	result = []

	for idx, key in enumerate(keys_select):

		result.append({
			'source': source,
			'target': key,
			**{weight: route_information_select[idx][idx_weight] \
			for idx_weight, weight in enumerate(weights)},
			})

	return result


def Add_Locations(
	graph,
	chargers,
	weight='length',
	cutoff=300e3,
	fields=['time','length'],
	verbose=True,
	add_all=False,
	):

	# Pulling the charger ids as a list
	charger_ids=np.array([key for key in chargers.keys()])

	# Collecting locations and statuses of all chargers
	lon,lat,added=np.array(
		[[val['Longitude'],val['Latitude'],val['Added']] for val in chargers.values()]
		).T

	# Node assignment maps chargers to nearest node
	node_assignment=Node_Assignment_From_Coordinates(
		graph,charger_ids,lon,lat)

	# print(node_assignment)

	# Pulling assigned nodes for all chargers
	destination_nodes=np.array([val['node'] for val in node_assignment.values()])

	# print(destination_nodes)

	# Calls 1 to N router for chargers that have not been added
	for idx in ProgressBar(range(len(added)),disp=verbose):

		# Only computes distances for non-added chargers
		if (not added[idx]) or add_all:

			# Getting the origin charger ID
			charger_id=charger_ids[idx]

			# Getting the node corresponding to the origin charger
			origin=node_assignment[charger_id]['node']

			# Calling the 1 to N router for the origin charger
			# Attempts to route to all destination charger nodes
			# keys - destination nodes which can be reached from origin
			# distances - distances corresponding to keys
			keys,route_information=Single_Origin_Dijkstra(
				graph,
				origin,
				destinations=destination_nodes,
				fields=fields,
				cutoff=cutoff,
				)

			# Looping on rechable node IDs
			for idx_k in range(len(keys)):

				# Getting the charger IDs for chargers at the given node
				chargers_at_node=destination_nodes==keys[idx_k]
				adjacent_chargers=charger_ids[chargers_at_node]

				# Looping on chargers at node
				for idx_a in range(len(adjacent_chargers)):

					# Adding the adjacency information
					adjacent_charger=adjacent_chargers[idx_a]

					adjacency_information={
					fields[idx_f]:route_information[idx_k,idx_f] \
					for idx_f in range(len(fields))}

					chargers[charger_id]['Adjacency'][adjacent_charger]=(
						adjacency_information)

			chargers[charger_id]['Added']=1.

	return chargers