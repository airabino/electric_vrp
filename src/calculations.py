import os
import time
import numpy as np
import pandas as pd
import geopandas as gpd
import pickle as pkl
import matplotlib.pyplot as plt

from shapely.geometry import Point
from scipy.spatial import KDTree

from .utilities import ProgressBar

def ClosestLine(gdf_points,gdf_lines,crs=2163):

	points=gdf_points.to_crs(crs).geometry
	lines=gdf_lines.to_crs(crs).geometry

	assignment=np.array([-1]*len(points))

	for idx in ProgressBar(range(len(points))):

		assignment[idx]=np.argmin(lines.distance(points[idx]))

	return assignment

def AssignVertex(graph,query):

	if isinstance(query,gpd.GeoDataFrame):

		query_points=np.array([[geom.xy[0][0],geom.xy[1][0]] for geom in query.geometry])

	else:

		query_points=query

	xy=np.array([(value['x'],value['y']) for value in graph._node.values()])
	xy=xy.reshape((-1,2))
	kd_tree=KDTree(xy)

	assignment=kd_tree.query(query_points)[1]

	return assignment