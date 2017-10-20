

import sys

import PIL.Image
from fiona import collection
from fiona.crs import from_epsg
import numpy
from pyproj import Proj, transform
import rasterio
from shapely.geometry import Point, mapping
import tensorflow

from rest.disasters.util import non_max_suppression_fast, get_basename
from rest.settings import TEMP_FOLDER


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
        
    with tensorflow.gfile.FastGFile("/Users/agutierrez/Documents/oaxaca/model/beb47c35-aba5-40c5-8cff-17eada9d6fb5.pb", 'rb') as model_file:
        graph_def = tensorflow.GraphDef()
        graph_def.ParseFromString(model_file.read())
        tensorflow.import_graph_def(graph_def, name='')

    with tensorflow.Session() as session:
        # Feed the image_data as input to the graph and get first prediction
        softmax_tensor = session.graph.get_tensor_by_name('final_result:0')
    
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
                im = PIL.Image.fromarray(rgbArray)
                name = '%s/%s' % (TEMP_FOLDER, 'test.jpg')
                im.save(name)
                
                
                image_data = tensorflow.gfile.FastGFile(name, 'rb').read()
                predictions = session.run(softmax_tensor, {'DecodeJpeg/contents:0': image_data})
                
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
    
def list_to_shape(path, boxes, epsg):
    schema = { 'geometry': 'Point', 'properties': { 'lat': 'float', 'lon': 'float' } }
    with collection(path, 'w' ,crs=from_epsg(epsg), driver='ESRI Shapefile', schema=schema) as output:
        for i in range(len(boxes['world'])):
            point = Point(boxes['world'][i][0], boxes['world'][i][1])
            output.write({'geometry':mapping(point), 'properties':{'lon':boxes['latlon'][i][0], 
                                                                   'lat':boxes['latlon'][i][1]}
                          })
def get_box_center(box):
    return int((box[0]+box[2]) / 2), int((box[1] + box[3]) / 2)
    
def pretty_print(lon_lat):
    
    print lon_lat[1], lon_lat[0]
    
def pixel_to_world(x, y, geotransform):
    
    world_x = geotransform[0] + x * geotransform[1] + y * geotransform[2]
    world_y = geotransform[3] + x * geotransform[4] + y * geotransform[5] 
    
    return world_x, world_y
    