'''
Module for handling of graphs.

Graphs must be in Node-Link Graph (NLG) format:
Long example can be found at - https://gist.github.com/mbostock/4062045

Short example (right triangle):

{
	"nodes":[
	{"id": 0, "x": 0, "y": 0},
	{"id": 1, "x": 1, "y": 0},
	{"id": 2, "x": 0, "y": 1}
	],
	"links":[
	{"source": 0, "target": 1, "length": 1},
	{"source": 1, "target": 2, "length": "1.414"},
	{"source": 2, "target": 0, "length": 1},
	]
}

NLG dictionaries can be loaded from JSON or shapefile with or without links (adjacency)

NLG dictionaries can be created from DataFrames without links

NLG dictionaries are saved as .json files

!!!!! In this module graph refers to a networkx graph, nlg to a NLG graph !!!!!

NLG terminology maps to NetworkX terminology as follows:
Node -> node,
Link -> edge, adj

Nodes of a graph may also be referred to as vertices
'''

import json
import numpy as np
import pandas as pd
import networkx as nx

class NpEncoder(json.JSONEncoder):
	'''
	Encoder to allow for numpy types to be converted to default types for
	JSON serialization. For use with json.dump(s)/load(s).
	'''
    def default(self, obj):

        if isinstance(obj, np.integer):

            return int(obj)

        if isinstance(obj, np.floating):

            return float(obj)

        if isinstance(obj, np.ndarray):

            return obj.tolist()

        return super(NpEncoder, self).default(obj)

def Write(nlg, filename = 'nlg.json'):
	'''
	Writes nlg to JSON, overwrites previous
	'''

	with open(filename, 'w') as file:

		json.dump(nlg, file, indent = 4, cls = NpEncoder)

def Append(nlg, filename = 'nlg.json'):
	'''
	Writes nlg to JSON, appends to existing - NEEDS UPDATING
	'''

	nlg_from_file = Load(filename)

	nlg = dict(**nlg_from_file, **nlg)

	with open(filename, 'a') as file:

		json.dump(nlg, file, indent = 4, cls = NpEncoder)

def Load(filename = 'nlg.json'):
	'''
	Loads nlg from JSON
	'''

	with open(nlg, 'r') as file:

		nlg = json.load(file)

	return nlg

# Functions for CSV handling - move these

def DataFrame_From_CSV(files):
	'''
	Loads data provided as CSV
	'''
	dataframes = []

	for file in files:

		dataframes.append(pd.read_csv(file))

	dataframe = pd.concat(dataframes, axis = 0)
	dataframe.reset_index(inplace = True, drop = True)

	return dataframe

def Parse(df, fields):
	'''
	converts vertex to nested dict format
	'''

	vertices=dict()

	for idx,row in df.iterrows():

		vertex={
			'x': row['Longitude'],
			'y': row['Latitude'],
			'links': {},
			'added': 0,
			'visited': 0,
		}

		for field in fields:

			vertex[field]=row[field]

		vertices[int(row['ID'])]=vertex

	return vertices

def AddFields(vertices, df, fields):
	'''
	Adds fields from df to vertices
	'''

	for vertex_id,vertex in vertices.items():

		row=df[df['ID']==int(vertex_id)]

		for field in fields:

			vertex[field]=str(row[field].values[0])

	return vertices

def Exclude(df, attributes):
	'''
	Removes DataFrame rows that meet criteria
	'''

	for attribute, values in attributes.items():

		df = df[~np.isin(df[attribute].to_numpy(), values)].copy()
		df.reset_index(inplace = True, drop = True)

	return df

def Keep(df, attributes):
	'''
	Removes DataFrame rows that do not meet criteria
	'''

	for attribute,values in attributes.items():

		df = df[np.isin(df[attribute].to_numpy(), values)].copy()
		df.reset_index(inplace = True, drop = True)

	return df