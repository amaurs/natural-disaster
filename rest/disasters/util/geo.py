'''
Created on Oct 20, 2017

@author: agutierrez
'''
import sys

from fiona import collection
from fiona.crs import from_epsg
import numpy
from pyproj import Proj, transform
import rasterio
from shapely.geometry import Point, mapping

from rest.disasters.models import Model
from rest.disasters.util import non_max_suppression_fast, get_basename
from rest.disasters.util.predict import TensorModel


def crop(filepath, x, y, size_width, size_height):
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
    models = Model.objects.all().order_by('-accuracy')
    tensor_model = TensorModel(models[0].path)
    label_lines = ['nodamage','damage']
    boxes = []
    w_limit = size_width
    h_limit = size_height
    w = h = 229
    
    total = len(range(0, scene_height, h)) * len(range(0, scene_width, w))
    cont = 0
        
    for j in range(0, scene_height, h):
        for i in range(0, scene_width, w):
            cont = cont + 1 
            if(i + w_limit < scene_width and j + h_limit < scene_height):
                size = size_width
                offset_x = i
                offset_y = j
                
                rgbArray = numpy.zeros((size,size,3), 'uint8')
                rgbArray[..., 0] = r[offset_y:offset_y + size_height,offset_x:offset_x + size_width]
                rgbArray[..., 1] = g[offset_y:offset_y + size_height,offset_x:offset_x + size_width]
                rgbArray[..., 2] = b[offset_y:offset_y + size_height,offset_x:offset_x + size_width]
                predictions = tensor_model.predict_from_array(rgbArray)
                top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
                result = {}
                for node_id in top_k:
                    human_string = label_lines[node_id]
                    score = predictions[0][node_id]
                    result[human_string] = score
                    
                if result['damage'] > .95:
                    boxes.append(numpy.array([i,j,i + w_limit, j + h_limit]))
                
                if (cont % 100) == 0:
                    print 'progress: %s' % (cont * 1.0 / total)
    
    
    no_overlap_boxes = non_max_suppression_fast(numpy.array(boxes), .1)
    inProj = Proj(init=projection)
    outProj = Proj(init='epsg:4326')
  
    world_boxes = {'latlon':[],'world':[]}
  
    for box in no_overlap_boxes:
        point = get_box_center(box)
        point_world = pixel_to_world(point[0], point[1], geotransform)
        world_boxes['world'].append(point_world)
        world_boxes['latlon'].append(transform(inProj, outProj, point_world[0], point_world[1]))
        
    list_to_shape('%s.shp' % get_basename(filepath), world_boxes, 32615)    
    
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
    