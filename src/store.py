'''
Module for converting CSV charger info to JSON for router

JSON fields:

ID
Longitude
Latitude
Added - tells router whether or not to add the charger to the graph
Adjacency - dictionary {id:{field:value}
'''

import json
import numpy as np
import pandas as pd

def Read(files):
	'''
	Loads data provided as CSV
	'''

	dataframes=[]

	for file in files:

		dataframes.append(pd.read_csv(file))

	out=pd.concat(dataframes,axis=0)
	out.reset_index(inplace=True,drop=True)

	return out

def Parse(chargers_df,fields):
	'''
	converts data to nested dict format
	'''

	chargers=dict()

	for idx,row in chargers_df.iterrows():

		charger={
			'Longitude':row['Longitude'],
			'Latitude':row['Latitude'],
			'Adjacency':{},
			'Added':0,
			'visited':0,
		}

		for field in fields:

			charger[field]=row[field]

		chargers[int(row['ID'])]=charger

	return chargers

def AddFields(vertices,df,fields):
	'''
	Adds fields from df to vertices
	'''

	for vertex_id,vertex in vertices.items():

		row=df[df['ID']==int(vertex_id)]

		for field in fields:

			vertex[field]=str(row[field].values[0])

	return vertices

class NpEncoder(json.JSONEncoder):

    def default(self, obj):

        if isinstance(obj, np.integer):

            return int(obj)

        if isinstance(obj, np.floating):

            return float(obj)

        if isinstance(obj, np.ndarray):

            return obj.tolist()

        return super(NpEncoder, self).default(obj)

def Write(chargers,filename='vertices.json',permission='w'):
	'''
	Writes data to JSON, overwrites previous
	'''

	with open(filename,permission) as file:

		json.dump(chargers,file,indent=4,cls=NpEncoder)

def Append(vertices,filename='vertices.json'):
	'''
	Writes data to JSON, appends to previous
	'''

	vertices_existing=Load(filename)

	vertices=dict(**vertices_existing,**vertices)

	with open(filename,'a') as file:

		json.dump(vertices,file,indent=4,cls=NpEncoder)

def Load(filename='vertices.json'):
	'''
	Loads the vertices
	'''

	with open(filename,'r') as file:

		vertices=json.load(file)

	return vertices
	

def Exclude(df,attributes):
	'''
	Removes vertices that meet criteria
	'''

	for attribute,values in attributes.items():

		df=df[~np.isin(df[attribute].to_numpy(),values)].copy()
		df.reset_index(inplace=True,drop=True)

	return df

def Keep(df,attributes):
	'''
	Removes vertices that do not meet criteria
	'''

	for attribute,values in attributes.items():

		df=df[np.isin(df[attribute].to_numpy(),values)].copy()
		df.reset_index(inplace=True,drop=True)

	return df