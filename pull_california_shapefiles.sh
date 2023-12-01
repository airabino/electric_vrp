#!/bin/bash

mkdir -p Data/Geometries

if [ ! -f Data/Geometries/tracts.zip ]; then
	curl -o Data/Geometries/tracts.zip https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_06_cousub_500k.zip
	echo "Tracts Downloaded"
else
	echo "Tracts Downloaded"
fi

if [ ! -f Data/Geometries/cb_2021_us_tract_500k.shp ]; then
	unzip Data/Geometries/tracts.zip -d Data/Geometries
	echo "Tracts Unzipped"
else
	echo "Tracts Unzipped"
fi