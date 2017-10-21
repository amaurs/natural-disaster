'''
Created on Oct 20, 2017

@author: agutierrez
'''
import sys

import cv2
from fiona import collection
from fiona.crs import from_epsg
import numpy
from pyproj import Proj, transform
import rasterio
from shapely.geometry import Point, mapping
from skimage.io import imread

from rest.disasters.models import Model
from rest.disasters.util import non_max_suppression_fast, get_basename
from rest.disasters.util.predict import TensorModel
from rest.settings import TEMP_FOLDER


OVERLAP_THRESHOLD = 0.1
DECISION_THRESHOLD = 0.95
LABEL_LINES = ['nodamage','damage']

def apply_prediction_on_raster(filepath):
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

    no_overlap_boxes = apply_prediction_on_array(r, g, b, scene_height, scene_width, 299, 299)
    original = Proj(init=projection)    
    target = Proj(init='epsg:4326')
    world_boxes = {'latlon':[],'world':[]}
    for box in no_overlap_boxes:
        point = get_box_center(box)
        point_world = pixel_to_world(point[0], point[1], geotransform)
        world_boxes['world'].append(point_world)
        world_boxes['latlon'].append(transform(original, target, point_world[0], point_world[1]))
    
    shape_path = '%s/%s.shp' % (TEMP_FOLDER, get_basename(filepath))
    list_to_shape(shape_path, world_boxes, int(projection.split(':')[1]))
    

    
def apply_prediction_on_image(filepath):
    '''
    This method opens an image from a jpg file using the skimage package.
    '''
    image_array = imread(filepath)[0]
    r = image_array[..., 0]
    g = image_array[..., 1]
    b = image_array[..., 2]
    
    scene_height = image_array.shape[0]
    scene_width = image_array.shape[1]
    
    
    
    no_overlap_boxes = apply_prediction_on_array(r, g, b, scene_height, scene_width, 299, 299)
    
    
    cv2_image_array = numpy.zeros(image_array.shape)
    
    cv2_image_array[..., 0] = image_array[..., 2]
    cv2_image_array[..., 1] = image_array[..., 1]
    cv2_image_array[..., 2] = image_array[..., 0]
    
    del image_array
    
    for box in no_overlap_boxes:
        cv2.rectangle(cv2_image_array,(box[0],box[1]),(box[2],box[3]),(0,255,0),3)
    image_path = '%s/%s.jpg' % (TEMP_FOLDER, get_basename(filepath))
    cv2.imwrite(image_path, cv2_image_array)
        
    
def apply_prediction_on_array(r, g, b, height, width, vertical_window, horizontal_window):
    
    horizontal_step = vertical_step = 229
    total = len(range(0, height, vertical_step)) * len(range(0, width, horizontal_step))
    processed = 0
    tensor_model = get_tensor_model()
    boxes = []
    for y in range(0, height, vertical_step):
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
                    
                if result[LABEL_LINES[1]] > DECISION_THRESHOLD:
                    boxes.append(numpy.array([x,y,x + horizontal_window, y + vertical_window]))
                
                if (processed % 10) == 0:
                    progress = (processed * 1.0 / total) * 100.0
                    sys.stdout.write('\rProgress %.1f%%' % progress)
                    sys.stdout.flush()
    print ''
    no_overlap_boxes = non_max_suppression_fast(numpy.array(boxes), OVERLAP_THRESHOLD)
    return no_overlap_boxes 

def get_tensor_model():
    models = Model.objects.all().order_by('-accuracy')
    tensor_model = TensorModel(models[0].path)
    return tensor_model
    
def list_to_shape(path, points, epsg):
    '''
    Creates a shape file with points in the given coordinate system.
    '''
    schema = { 'geometry': 'Point', 'properties': { 'lat': 'float', 'lon': 'float' } }
    with collection(path, 'w' ,crs=from_epsg(epsg), driver='ESRI Shapefile', schema=schema) as output:
        for i in range(len(points['world'])):
            point = Point(points['world'][i][0], points['world'][i][1])
            output.write({'geometry':mapping(point), 'properties':{'lon':points['latlon'][i][0], 
                                                                   'lat':points['latlon'][i][1]}
                          })
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
    
def pixel_to_world(x, y, geotransform):
    world_x = geotransform[0] + x * geotransform[1] + y * geotransform[2]
    world_y = geotransform[3] + x * geotransform[4] + y * geotransform[5] 
    return world_x, world_y
    