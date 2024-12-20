'''
' Route Creation Automation - MyGeotab Route Completion Upload
' Converts any line Shapefile into an uploadable file.
' Created for testing purposes.
' Written by Alexander Moore.
' Last Updated on Monday December 20th, 2024.
'''

import math

## Variables 
#################################################################################

segmentName = ''# This is the field used to make SEGMENT, it doesnt need to be used.
groupName = 'group_'
routeName = 'route_'
projectedCRS = 'EPSG:3857' # Ideally, set this to a local projected CRS.
maxSegmentLength = 300 # Unit depends on CRS, could be in metres, feet, etc.
updateGeometry = True 
passCountDefault = 2
roadWidthDefault = 10

## Functions 
#################################################################################
        
def projected_crs(layer, crs):
    proj_layer = processing.run("native:reprojectlayer", 
        {'INPUT': layer,
        'TARGET_CRS':QgsCoordinateReferenceSystem(crs),
        'OUTPUT':'TEMPORARY_OUTPUT'})
    result1 = proj_layer['OUTPUT']
    return result1
    
def add_route(layer):
    layer.startEditing()
    layer.addAttribute(QgsField('route', QVariant.String))
    layer.updateFields()
    features = layer.getFeatures()
    index = 0
    count = layer.featureCount()
    for feature in features:
        index+=1
        if count / 2 > index:
            feature['route'] = 'Route A'
        else:
            feature['route'] = 'Route B'
        layer.updateFeature(feature)
    layer.commitChanges()
    
def create_grid(layer):
    extent_geom = QgsGeometry.fromRect(layer.extent())
    area_geom = extent_geom.area()

    grid_size = math.sqrt((area_geom / 4))
    grid_out = processing.run("native:creategrid", {'TYPE':2,
        'EXTENT':extent_geom,
        'HSPACING':grid_size,
        'VSPACING':grid_size,
        'CRS':QgsCoordinateReferenceSystem('EPSG:2958'),
        'OUTPUT':'TEMPORARY_OUTPUT'})
    grid_layer = grid_out['OUTPUT']
    return grid_layer
    
def fix_geometry(layer): 
    split_out1 = processing.run("native:splitlinesbylength", {'INPUT':layer,
        'LENGTH':maxSegmentLength,
        'OUTPUT':'TEMPORARY_OUTPUT'})
    split_layer1 = split_out1['OUTPUT']

    split_out2 = processing.run("native:splitwithlines", 
        {'INPUT':split_layer1,
        'LINES':split_layer1,
        'OUTPUT':'TEMPORARY_OUTPUT'})
    split_layer2 = split_out2['OUTPUT']

    split_out3 = processing.run("native:multiparttosingleparts", {'INPUT':split_layer2,
        'OUTPUT':'TEMPORARY_OUTPUT'})
    split_layer3 = split_out3['OUTPUT']
    return split_layer3

def add_group(layer, grid_layer): # Uses grid to assign group layer.
    joined_out = processing.run("native:joinattributesbylocation", {'INPUT':layer,
        'JOIN':grid_layer,
        'JOIN_FIELDS':['id'],
        'METHOD':2,
        'PREFIX':'grouptool_',
        'OUTPUT':'TEMPORARY_OUTPUT'})
    joined_layer = joined_out['OUTPUT']
    joined_layer.startEditing()
    joined_layer.addAttribute(QgsField('group', QVariant.String))
    joined_layer.updateFields()
    features = joined_layer.getFeatures()
    for feature in features:
        feature['group'] = 'Zone ' + str(feature['grouptool_id'])
        joined_layer.updateFeature(feature)
    joined_layer.deleteAttribute(joined_layer.fields().indexOf('grouptool_id'))
    return joined_layer
    
def check_field(layer, fieldName): # return true if missing, false if exists.
    notExists = True 
    for field in layer.fields():
        if field.displayName().lower() == fieldName.lower():
            notExists = False 
            break
    return notExists

def replace_nulls(layer, field, replacement):
    layer.startEditing()
    layer.selectByExpression(field + ' is NULL')
    selection = layer.getSelectedFeatures()
    for feature in selection:
        feature[field] = replacement
        layer.updateFeature(feature)
    layer.commitChanges()
    
def add_segment(layer, missingField):
    layer.startEditing()
    if missingField:
        layer.addAttribute(QgsField('segment', QVariant.String))
        layer.updateFields()
    features = layer.getFeatures()
    count = 0
    missingSegment = check_field(layer, segmentName)
    for feature in features:
        count+=1
        if missingSegment:
            feature['segment'] = str(feature['segment']) + '_' + str(count)
        else:
            feature['segment'] = str(feature[segmentName]) + '_' + str(count)
        layer.updateFeature(feature)

def adjust_field(layer, attribute, default):
    if check_field(layer, attribute):
        return
    layer.selectByExpression(attribute + ' < 1 OR ' + attribute +' is NULL')
    layer.startEditing()
    selection = layer.getSelectedFeatures()
    for feature in selection:
        feature[attribute] = default
        layer.updateFeature(feature)
    layer.commitChanges()

def calc_len(layer):
    layer.startEditing()
    layer.addAttribute(QgsField('segLength', QVariant.Double))
    layer.updateFields()
    features = layer.getFeatures()
    for feature in features:
        len = feature.geometry().length()
        feature['segLength'] = len
        layer.updateFeature(feature)
    layer.commitChanges()

def copy_field(layer, field, attribute):
    layer.startEditing()
    layer.addAttribute(QgsField(attribute, QVariant.String))
    layer.updateFields()
    features = layer.getFeatures()
    for feature in features:
        feature[attribute] = feature[field]
        layer.updateFeature(feature)
    layer.commitChanges()
    
## Main Script
#################################################################################

layer = iface.activeLayer()

result = projected_crs(layer, projectedCRS) 

## Determine what needs to be done with route attribute
missing_route = check_field(result, 'route')
missing_sub = check_field(result, routeName)
if missing_route and not missing_sub: ## Incorrectly named route field
    copy_field(result, routeName, 'route')
    replace_nulls(result, 'route', 'Route NULL')
elif missing_route and missing_sub: ## There is no route field.
    add_route(result)
else:
    replace_nulls(result, 'route', 'Route NULL')

if updateGeometry: 
    result = fix_geometry(result)

## Determine what needs to be done with group attribute 
group_sub = check_field(result, groupName)
group_missing = check_field(result, 'group')  
if group_missing and not group_sub: ## There is an incorrectly named group field
    copy_field(result, groupName, 'group')
    replace_nulls(result, 'group', 'Zone NULL')
elif group_missing and group_sub: ## There is no group field
    grid_layer = create_grid(result)
    result = add_group(result, grid_layer)
else: ## group field already exists
    replace_nulls(result, 'group', 'Zone NULL')
    
add_segment(result, check_field(result, 'segment'))
adjust_field(result, 'roadwidth', roadWidthDefault)
adjust_field(result, 'passcount', passCountDefault)

calc_len(result)

final_layer = projected_crs(result, 'EPSG:4326')
final_layer.selectByExpression('segLength < 1')
final_layer.startEditing()
final_layer.deleteSelectedFeatures()
final_layer.commitChanges()

QgsProject.instance().addMapLayer(final_layer)
print('Script has finished.')
