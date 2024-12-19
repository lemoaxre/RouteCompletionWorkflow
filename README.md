# MyGeotab Route Completion Automation
## Overview
This is a script that is written using PyQGIS to be used in the GIS software QGIS. The script should not be used to make actual routes but to create demo data. All routes should be created by the individual.

## Requirements
- This script requires that the input layer have no invalid geometries.
- The input file be a line type.
- There is atleast one feature.

## Important to Remember

While this will produce a shapefile that will meet the criteria of Route Completion upload, it is still on the user end to export the shapefile to their own computer and compress the shp, shx and dbf file ONLY for the route completion upload.

## Features
This script accomplishes the following:
- Transforms a shapefile into the correct format. 
- Fills in NULL values and adds necessary attributes.
- Can reference other fields to create the segment attribute.
- Breaks down segments to split with intersections and maximum length.
- Eliminates segments under 1 metre in length.
- Customizability of default values under the "Variables" section.

