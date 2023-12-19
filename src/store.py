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

def Parse(chargers_df):
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
		}

		chargers[int(row['ID'])]=charger

	return chargers

def Write(chargers,filename='vertices.json',permission='w'):
	'''
	Writes data to JSON, overwrites previous
	'''

	with open(filename,permission) as file:

		json.dump(chargers,file,indent=4)

def Append(chargers,filename='vertices.json'):
	'''
	Writes data to JSON, appends to previous
	'''

	with open(filename,'a') as file:

		json.dump(chargers,file,indent=4)

def Load(filename='vertices.json'):
	'''
	Loads the chargers
	'''

	with open(filename,'r') as file:

		chargers=json.load(file)

	return chargers
	

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