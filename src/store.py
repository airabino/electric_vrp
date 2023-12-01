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

def Write(chargers,filename='Data/GeneratedData/chargers.json'):
	'''
	Writes data to JSON, overwrites previous
	'''

	with open(filename,'w') as file:

		json.dump(chargers,file,indent=4)

def Append(chargers,filename='Data/GeneratedData/chargers.json'):
	'''
	Writes data to JSON, appends to previous
	'''

	with open(filename,'a') as file:

		json.dump(chargers,file,indent=4)

def Load(filename='Data/GeneratedData/chargers.json'):
	'''
	Loads the chargers
	'''

	with open(filename,'r') as file:

		chargers=json.load(file)

	return chargers