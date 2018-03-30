'''
Created on Oct 20, 2017

@author: agutierrez
'''
import json
import random
import sys
import time
import urllib2

import cv2
from fiona import collection
from fiona.crs import from_epsg
import numpy
from pyproj import Proj, transform
import rasterio
import requests
from requests.exceptions import ReadTimeout
from shapely.geometry import Point, mapping
from skimage.io import imread

from rest.disasters.models import Model, Town, Debris
from rest.disasters.util import non_max_suppression_fast, get_basename
from rest.disasters.util.predict import TensorModel
from rest.settings import TEMP_FOLDER


OVERLAP_THRESHOLD = 0.0005
LABEL_LINES = ['nodamage','damage']

def apply_prediction_on_raster(filepath, town_id, model_path, threshold):
    '''
    This method opens an image from a raster file using the rasterio package.
    '''
    with rasterio.open(filepath) as src:
        bands = src.read()
        if len(bands) == 4:
            r, g , b, a = bands
            del a
        elif len(bands) == 3:
            r, g , b = bands
        else:
            sys.exit(-1)
        scene_width = src.width 
        scene_height = src.height
        projection = src.crs.to_dict()['init']
        geotransform = src.transform

    boxes, no_overlap_boxes, scores = apply_prediction_random_on_array(r, g, b, scene_height, scene_width, 322, 322, model_path, threshold)
    original = Proj(init=projection)    
    target = Proj(init='epsg:4326')
    world_boxes = {'latlon':[],'world':[],'score':[], 'address':[]}
    print len(no_overlap_boxes)
    print 'About to get centers'
    for i in range(len(no_overlap_boxes)):
        point = get_box_center(no_overlap_boxes[i])
        point_world = pixel_to_world(point[0], point[1], geotransform)
        lat_lon = transform(original, target, point_world[0], point_world[1])
        world_boxes['world'].append(point_world)
        world_boxes['latlon'].append(lat_lon)
        world_boxes['score'].append(scores[i])
        world_boxes['address'].append(address_from_lat_lon(lat_lon[1], lat_lon[0]))
    shape_path = '%s/%s.shp' % (TEMP_FOLDER, get_basename(filepath))
    print 'About to write shape'
    list_to_shape(shape_path, world_boxes, int(projection.split(':')[1]))
    print 'About to write in database'
    list_to_database(world_boxes, town_id, model_path, threshold)

    
def apply_prediction_on_image(filepath, contrast, model_path, threshold):
    '''
    This method opens an image from a jpg file using the skimage package.
    '''
    image_array = imread(filepath)[0]
    r = image_array[..., 0]
    g = image_array[..., 1]
    b = image_array[..., 2]
    
    scene_height = image_array.shape[0]
    scene_width = image_array.shape[1]
    
    boxes, no_overlap_boxes, scores = apply_prediction_random_on_array(r, g, b, scene_height, scene_width, 322, 322, model_path, threshold)
    
    del image_array
    
    image_array = imread(contrast)
    
    print image_array.shape
    
    cv2_image_array = numpy.zeros(image_array.shape)
    cv2_other_image_array = numpy.zeros(image_array.shape)
    
    cv2_image_array[..., 0] = image_array[..., 2]
    cv2_image_array[..., 1] = image_array[..., 1]
    cv2_image_array[..., 2] = image_array[..., 0]
    
    cv2_other_image_array[..., 0] = image_array[..., 2]
    cv2_other_image_array[..., 1] = image_array[..., 1]
    cv2_other_image_array[..., 2] = image_array[..., 0]
    
    del image_array
    
    
    
    for box in no_overlap_boxes:
        cv2.rectangle(cv2_image_array,(box[0],box[1]),(box[2],box[3]),(0,255,0),4)
    for box in boxes:
        cv2.rectangle(cv2_other_image_array,(box[0],box[1]),(box[2],box[3]),(0,0,255),4)
    image_path = '%s/%s.jpg' % (TEMP_FOLDER, get_basename(filepath))
    print image_path
    cv2.imwrite(image_path, cv2_image_array)
    
    image_path = '%s/%s-boxes.jpg' % (TEMP_FOLDER, get_basename(filepath))
    print image_path
    cv2.imwrite(image_path, cv2_other_image_array)
        
    
def apply_prediction_on_array(r, g, b, height, width, vertical_window, horizontal_window, model_path, threshold):
    
    horizontal_step = vertical_step = 50 + random.randint(0,100)
    total = len(range(0, height, vertical_step)) * len(range(0, width, horizontal_step))
    processed = 0
    tensor_model = get_tensor_model_by_path(model_path)
    boxes = []
    scores = []
    for y in range(0, height, vertical_step):
        horizontal_step = 50 + random.randint(0,50)
        for x in range(0, width, horizontal_step):
            processed = processed + 1 
            if(x + horizontal_window < width and y + vertical_window < height):
                size = horizontal_window
                offset_x = x
                offset_y = y 
                image_array = numpy.zeros((size,size,3), 'uint8')
                image_array[..., 0] = r[offset_y:offset_y + vertical_window,offset_x:offset_x + horizontal_window]
                image_array[..., 1] = g[offset_y:offset_y + vertical_window,offset_x:offset_x + horizontal_window]
                image_array[..., 2] = b[offset_y:offset_y + vertical_window,offset_x:offset_x + horizontal_window]
                predictions = tensor_model.predict_from_array(image_array)
                top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
                result = {}
                for node_id in top_k:
                    human_string = LABEL_LINES[node_id]
                    score = predictions[0][node_id]
                    result[human_string] = score
                    
                if result[LABEL_LINES[1]] > threshold:
                    scores.append(result[LABEL_LINES[1]])
                    boxes.append(numpy.array([x,y,x + horizontal_window, y + vertical_window]))
                
                if (processed % 10) == 0:
                    progress = (processed * 1.0 / total) * 100.0
                    sys.stdout.write('\rProgress %.1f%%' % progress)
                    sys.stdout.flush()
    print 'About to calculate nom max suppression fast.'
    random.shuffle(boxes)
    no_overlap_boxes = non_max_suppression_fast(numpy.array(boxes), OVERLAP_THRESHOLD)
    
    return boxes, no_overlap_boxes, scores

def apply_prediction_random_on_array(r, g, b, height, width, vertical_window, horizontal_window, model_path, threshold):
    
    horizontal_step = vertical_step = 130
    total = len(range(0, height, vertical_step)) * len(range(0, width, horizontal_step))
    
    print 'Total of windows to be explored: %s' % total
    
    processed = 0
    tensor_model = get_tensor_model_by_path(model_path)
    boxes = []
    scores = []
    
    start_time = time.time()
    
    while processed < total:
        x = random.randint(0, width)
        y = random.randint(0, height)     
        if(x + horizontal_window < width and y + vertical_window < height):
                processed = processed + 1
                size = horizontal_window
                offset_x = x
                offset_y = y 
                image_array = numpy.zeros((size,size,3), 'uint8')
                image_array[..., 0] = r[offset_y:offset_y + vertical_window,offset_x:offset_x + horizontal_window]
                image_array[..., 1] = g[offset_y:offset_y + vertical_window,offset_x:offset_x + horizontal_window]
                image_array[..., 2] = b[offset_y:offset_y + vertical_window,offset_x:offset_x + horizontal_window]
                predictions = tensor_model.predict_from_array(image_array)
                top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
                result = {}
                for node_id in top_k:
                    human_string = LABEL_LINES[node_id]
                    score = predictions[0][node_id]
                    result[human_string] = score
                    
                if result[LABEL_LINES[1]] > threshold:
                    scores.append(result[LABEL_LINES[1]])
                    boxes.append(numpy.array([x,y,x + horizontal_window, y + vertical_window]))
                
                if (processed % 100) == 0:
                    progress = (processed * 1.0 / total) * 100.0
                    so_far = time.time() - start_time
                    left = so_far / (processed * 1.0 / total)
                    sys.stdout.write('\rProgress %.1f%%, windows %s, left %s minutes' % (progress,processed, left))
                    sys.stdout.flush()
                    
                    
                    
    print 'About to calculate nom max suppression fast.'
    random.shuffle(boxes)
    no_overlap_boxes = non_max_suppression_fast(numpy.array(boxes), OVERLAP_THRESHOLD)
    
    return boxes, no_overlap_boxes, scores


def get_tensor_model():
    models = Model.objects.all().order_by('-accuracy')
    tensor_model = TensorModel(models[0].path)
    return tensor_model

def get_model_by_path(path):
    return Model.objects.get(path=path)
def get_tensor_model_by_path(path):
    model = get_model_by_path(path)
    tensor_model = TensorModel(model.path)
    return tensor_model
    
def list_to_shape(path, points, epsg):
    '''
    Creates a shape file with points in the given coordinate system.
    '''
    schema = { 'geometry': 'Point', 'properties': { 'lat': 'float', 'lon': 'float', 'address':'str' } }
    with collection(path, 'w' ,crs=from_epsg(epsg), driver='ESRI Shapefile', schema=schema) as output:
        for i in range(len(points['world'])):
            point = Point(points['world'][i][0], points['world'][i][1])
            output.write({'geometry':mapping(point), 'properties':{'lon':points['latlon'][i][0], 
                                                                   'lat':points['latlon'][i][1],
                                                                   'address':points['address'][i]}
                          
                          })
def list_to_database(points, town_id, model_path, threshold):
    '''
    Persists the points to database.
    '''
    town = Town.objects.get(pk=town_id)
    model = get_model_by_path(model_path)
    for i in range(len(points['world'])):
        score = points['score'][i]
        lon = points['latlon'][i][0]
        lat = points['latlon'][i][1]
        address = points['address'][i]
        debris = Debris(lat = lat,
                        lon = lon,
                        town = town,
                        address = address,
                        threshold = threshold,
                        model = model,
                        score = score)
        debris.save()
    
def get_box_center(box):
    '''
    Computes the centroid of the box represented by the two points.
    '''
    return int((box[0]+box[2]) / 2), int((box[1] + box[3]) / 2)
    
def pretty_print(lon_lat):
    '''
    Just prints the latitude and longitude values in the order that google maps wants.
    '''
    print lon_lat[1], lon_lat[0]

def address_from_lat_lon(lat, lon):
    '''
    This method queries google api to retrieve the address given the latitude and
    longitude coordinates.
    '''
    url = 'https://maps.googleapis.com/maps/api/geocode/json?&latlng=%s,%s' % (lat, lon)
    print url
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
    except ReadTimeout:
        data = {'results':[]}
        print 'Read timeout.'
    address = ''
    if len(data['results']) > 0:
        address = data['results'][0]['formatted_address']
    return address

def pixel_to_world(x, y, geotransform):
    world_x = geotransform[0] + x * geotransform[1] + y * geotransform[2]
    world_y = geotransform[3] + x * geotransform[4] + y * geotransform[5] 
    return world_x, world_y
    