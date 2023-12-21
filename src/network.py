'''
Module for computing adjacency between chargers.

For a list of charger dicts all non-added chargers ('added':0) are processed
Processing involves computing shortest routes between a given charger and all others
When a shortest route is computed, the adjacency dict for both the origin and destination
charger are updated to reflect.

NetworkX terminology uses "node" rather than "vertex". In this modeule where the terms
node or nodes are used it is in reference to NetworkX objects. Where vertix and vertices
are used it is in relation to non-NetworkX objects.
'''

import os
import sys
import time
import momepy
import numpy as np
import pandas as pd
import geopandas as gpd
import pickle as pkl
import networkx as nx

from scipy.stats import binom as binom_dist
from scipy.spatial import KDTree

from .utilities import ProgressBar,Haversine
from .dijkstra import Dijkstra

# Assumed road speed limits based on classification
# (https://www.census.gov/library/reference/code-lists/route-type-codes.html)
road_class_speeds={
	'C':24.58, # [m/s] - 55 mph
	'I':31.29, # [m/s] - 70 mph
	'S':29.05, # [m/s] - 65 mph
	'U':29.05, # [m/s] - 65 mph
	'N':15.64, # [m/s] - 35 mph
	'O':11.17, # [m/s] - 25 mph
}

# Functions for loading the road map from shapefile

def Graph_From_GDF(gdf,directed=False):
	'''
	Calls momepy gdf_to_nx function to make a Graph from a GeoDataFrame.
	In this case the primal graph (vertex-defined) is called for, multi-paths
	are disallowed (including self-loops), and directed Graphs are kept as directed.
	'''

	graph=momepy.gdf_to_nx(
		gdf,
		approach='primal',
		multigraph=False,
		directed=directed,
		)

	return graph

def Vertices_From_Coordinates(x,y):
	'''
	Creates a vertices structure which is a list-of-dicts containing basic
	vertex information and empty adjacency
	'''

	n=len(x)

	vertices=[]

	for idx in range(n):

		vertices.append({
			'id':idx,
			'x':x[idx],
			'y':y[idx],
			'edges':[],
			})

	return np.array(vertices)

def Fields_From_Vertices(vertices,keys=[]):
	'''
	Extract fields from all instances in vertices structure. Returns an ndarray.
	'''

	out=np.empty((len(keys),len(vertices)))

	for idx0,key in enumerate(keys):

		for idx1,vertex in enumerate(vertices):

			out[idx0,idx1]=vertex[key]

	return out

def NX_Graph_From_Vertices(vertices):

	# vertex_ids=np.array(list(vertices.keys()))

	# x,y=np.array([[v['Longitude'],v['Latitude']] for v in vertices.values()]).T

	vertex_info=[]
	# keep=[True]*len(vertex_ids)

	edge_ids=[]

	required_fields=['Longitude','Latitude','Added','Visited']

	for vertex_from,vertex in vertices.items():

		vertex_from_info=(
			vertex_from,
				{
					'id':vertex_from,
					'x':vertex['Longitude'],
					'y':vertex['Latitude'],
					'added':vertex['Added'],
					'visited':vertex['Visited'],
				}
			)

		additional_fields=list(vertex.keys())
		# additional_fields=np.setdiff1d(additional_fields,required_fields)

		for key in additional_fields:

			vertex_from_info[1][key]=vertex[key]

		vertex_info.append(vertex_from_info)
			

		# vertex_ids[idx]=vertex['id']

		edge_ids_temp=[]

		for vertex_to,edge in vertex['Adjacency'].items():
			# print(edge)
			# break

			# keep[idx]=True

			edge_ids_temp.append((vertex_from,vertex_to,edge))

		edge_ids.extend(edge_ids_temp)

	# return vertex_info, edge_ids

	nx_graph=nx.Graph()
	nx_graph.add_nodes_from(vertex_info)
	nx_graph.add_edges_from(edge_ids)

	return nx_graph

def Graph_From_Vertices(vertices,fields=[],x_field='x',y_field='y',edges_field='edges'):
	'''
	Converts vertices structure into a NetworkX Graph
	'''

	vertex_ids=np.zeros(len(vertices),dtype=int)

	x,y=Fields_From_Vertices(vertices,[x_field,y_field])

	vertex_info=[]
	keep=[True]*len(vertex_ids)

	edge_ids=[]

	for idx,vertex in enumerate(vertices):

		vertex_info.append((vertex['id'],{'id':vertex['id'],'x':x[idx],'y':y[idx]}))
		vertex_ids[idx]=vertex['id']

		edge_ids_temp=[]

		for idx1,edge in enumerate(vertex[edges_field]):

			keep[idx]=True

			edge_information={}

			for key in fields:

				edge_information[key]=edge[key]

			edge_ids_temp.append((edge['vertices'][0],edge['vertices'][1],
				edge_information))

		edge_ids.extend(edge_ids_temp)

	nx_graph=nx.Graph()
	nx_graph.add_nodes_from(np.array(vertex_info))
	nx_graph.add_edges_from(edge_ids)

	return nx_graph

def Standard_RoadMap_Graph(graph):
	'''
	Compels a graph into a standard format dubbed RoadMap (but still a Graph object).
	This serves the purpose of facilitating later computations.
	'''

	# Extracting node data from the Graph
	nodes=list(graph.nodes)

	# Extracting the x and y coordinates from the Graph
	xy=np.array([key for key,value in graph._node.items()])
	x,y=xy.reshape((-1,2)).T

	# Creating a spatial KD Tree for quick identification of matches
	# between Graph nodes and equivalent vertices
	kd_tree=KDTree(xy.reshape((-1,2)))

	# Creating empty vertices for each coordinate pair
	vertices=Vertices_From_Coordinates(x,y)

	# Looping on vertices to add edges
	for idx0,node0 in enumerate(nodes):

		edges=[]

		# Pulling the coordinates of the adjacent nodes from the Graph
		coords=graph._adj[node0].keys()

		adjacency_indices=[]

		# Looping on adjacency
		for coord in coords:

			# Finding the matching vertex for the node coordinates
			coord=list(coord)
			adjacency_indices.append(kd_tree.query(coord)[1])

		# Adding edge infomration to vertex
		for idx1 in adjacency_indices:

			node1=nodes[idx1]

			edge=graph._adj[node0][node1]
			length=edge['LENGTH']*1e3
			speed=edge['SPEEDLIM']/3.6
			time=length/speed
			
			edges.append({
				'vertices':[idx0,idx1],
				'length':length,
				'speed':speed,
				'time':time,
				'x':[node0[0],node1[0]],
				'y':[node0[1],node1[1]]
				})

		vertices[idx0]['edges']=edges

	graph=Graph_From_Vertices(
		vertices,
		fields=['length','speed','time']
		)

	return graph

def RoadMap_From_Shapefile(
	filepath='Data/RoadMap/roadmap.shp',
	savepath='Data/RoadMap/roadmap.pkl'
	):
	'''
	Loads in a shapefile containing a road map and processes into a NetworkX
	Graph. The NetworkX graph is then processed to a regular format.
	'''

	# Loading the road map shapefile into a GeoDataFrame
	gdf=gpd.read_file(filepath)

	gdf=gdf.to_crs(4326)

	# Creating a NetworkX Graph
	graph=Graph_From_GDF(gdf)

	# return gdf

	# Reformatting the Graph
	graph=Standard_RoadMap_Graph(graph)

	# Optionally pickling the RoadMap Graph
	if savepath:

		with open(savepath,'wb') as file:

			pkl.dump((graph,gdf),file)

	return graph,gdf

def RoadMap_From_Pickle(filepath='Data/RoadMap/roadmap.pkl'):

	# Loading the pickled RoadMap graph
	with open(filepath,'rb') as file:

		graph,gdf=pkl.load(file)

	return graph,gdf

# Routing functions and related objects


def Node_Assignment_From_Coordinates(graph,ids,lon,lat):
	'''
	Creates an assignment dict mapping between points and closest nodes
	'''

	# Pulling coordinates from RoadMap Graph
	xy=np.array([(value['x'],value['y']) for key,value in graph._node.items()])
	xy=xy.reshape((-1,2))

	# Creating spatial KDTree for assignment
	kd_tree=KDTree(xy)

	# Shaping input coordinates
	lonlat=np.vstack((lon,lat)).T

	# Computing assignment
	result=kd_tree.query(lonlat)

	# Building the assignment dictionary
	node_assignment={}

	for idx in range(len(lon)):

		node=result[1][idx]

		x=[lon[idx],xy[node,0]]
		y=[lat[idx],xy[node,1]]

		distance=Haversine(*x,*y)

		node_assignment[ids[idx]]={
		'node':node,
		'longitude':x,
		'latitude':y,
		'distance':distance,
		}

	return node_assignment

def Route_Information(graph,route,fields):

	route_information=[0]*len(fields)

	for idx in range(len(route)-1):

		node_0=route[idx]
		node_1=route[idx+1]

		for idx_f,field in enumerate(fields):

			route_information[idx_f]+=graph._adj[node_0][node_1][field]

	return route_information

def Single_Origin_Dijkstra(
	graph,
	origin,
	destinations=[],
	fields=['time','length'],
	cutoff=300e3):

	route_weights,routes=Dijkstra(
		graph,
		[origin],
		fields,
		cutoff=cutoff,
		)

	keys=np.array(list(route_weights.keys()))
	route_information=np.array(list(route_weights.values()))


	select=np.isin(keys,destinations)

	keys_select=keys[select]
	route_information_select=route_information[select]

	return keys_select,route_information_select


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

def Subgraph(graph,nodes):

	SG = graph.__class__()
	SG.add_nodes_from((n, graph.nodes[n]) for n in nodes)
	if SG.is_multigraph():
		SG.add_edges_from((n, nbr, key, d)
			for n, nbrs in graph.adj.items() if n in nodes
			for nbr, keydict in nbrs.items() if nbr in nodes
			for key, d in keydict.items())
	else:
		SG.add_edges_from((n, nbr, d)
			for n, nbrs in graph.adj.items() if n in nodes
			for nbr, d in nbrs.items() if nbr in nodes)
	SG.graph.update(graph.graph)

	return SG