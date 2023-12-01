import os
import time
import numpy as np
import pandas as pd
import geopandas as gpd
import pickle as pkl
import matplotlib.pyplot as plt

from shapely.geometry import Point

def LoadRoads():

	gdf=pkl.load(open('Data/Cali_Roads.pkl','rb'))
	gdf.reset_index(drop=True,inplace=True)

	return gdf

def LoadAADT():

	return gpd.read_file('Data/HWY_Traffic_Volumes_AADT.shp').to_crs(4326)

def LoadTMASLocations():

	return gpd.read_file(
		'Data/Travel_Monitoring_Analysis_System_Stations_CA.shp').to_crs(4326)

def LoadChargerLocations():

	df_chg=pd.read_csv('Data/Caltrans_data.csv')
	df_chg=df_chg.groupby('ID_num').first()
	df_chg['Coordinates']=list(zip(df_chg.Longitude,df_chg.Latitude))
	df_chg['Coordinates']=df_chg['Coordinates'].apply(Point)
	df_chg.reset_index(inplace=True)
	gdf_chg=gpd.GeoDataFrame(geometry=df_chg['Coordinates'])
	gdf_chg['DCFC_ID']=df_chg['DCFC_ID']

	gdf_chg.reset_index(inplace=True,drop=True)

	gdf_chg.crs=4326

	return gdf_chg

def LoadLocations():

	gdf_roads=LoadRoads()
	gdf_aadt=LoadAADT()
	gdf_tmas_loc=LoadTMASLocations()
	gdf_chg_loc=LoadChargerLocations()

	return gdf_roads,gdf_aadt,gdf_tmas_loc,load_chg_loc

def LoadChargerData():

	df_chg_data=pd.read_csv('Data/Caltrans_data.csv')

	df_chg_data['datestring']=df_chg_data['s_yymmdd']
	df_chg_data=df_chg_data[~np.isnan(df_chg_data['datestring'])]
	df_chg_data['datestring']=df_chg_data['s_yymmdd']
	df_chg_data['datestring']=df_chg_data['datestring'].astype(int)

	df_chg_data['datetime']=pd.to_datetime(df_chg_data['datestring'],format='%y%m%d')
	df_chg_data.sort_values('datetime',inplace=True)
	df_chg_data.reset_index(inplace=True,drop=True)
	
	return df_chg_data

def LoadTMASData(tmas_dir='Data/TMAS'):

	tmas_data_frames=[]

	for folder_name in os.listdir(tmas_dir):
		if '.zip' not in folder_name:

			folder_path=tmas_dir+'/'+folder_name

			for file_name in os.listdir(folder_path):
				if 'CA' in file_name:

					file_path=tmas_dir+'/'+folder_name+'/'+file_name

					tmas_data_frames.append(pd.read_csv(file_path,delimiter='|'))

	df_tmas=pd.concat(tmas_data_frames,ignore_index=True)

	df_tmas['year']=df_tmas['year_record'].astype(str)
	df_tmas['year']=df_tmas['year'].apply(lambda x: '20'+x)
	df_tmas['month']=df_tmas['month_record'].astype(str)
	df_tmas['day']=df_tmas['day_record'].astype(str)
	df_tmas['datetime']=pd.to_datetime(df_tmas[['year','month','day']])

	df_tmas.sort_values('datetime',inplace=True)
	df_tmas.reset_index(inplace=True,drop=True)

	hour_keys=[key for key in df_tmas.keys() if 'hour_' in key]
	df_tmas['daily_total']=df_tmas[hour_keys].sum(axis=1)

	return df_tmas