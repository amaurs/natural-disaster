import PIL.Image
import numpy
from pyproj import Proj, transform
import rasterio
import tensorflow

from rest.disasters.util import non_max_suppression_fast
from rest.settings import TEMP_FOLDER


def crop(filepath, x, y, size_width, size_height):
    
    with rasterio.open(filepath) as src:
        r, g, b = src.read()
        scene_width = src.width 
        scene_height = src.height
        projection = src.crs.to_dict()['init']
        geotransform = src.transform
        print(src.count)
        print(src.indexes)
        
        
        print dir(src)
        
        
        for val in src.sample([(x, y)]): 
            print "the value:", val 
        
        print src.affine
        
        
     # Unpersists graph from file
    with tensorflow.gfile.FastGFile("/Users/agutierrez/Documents/oaxaca/model/beb47c35-aba5-40c5-8cff-17eada9d6fb5.pb", 'rb') as f:
        graph_def = tensorflow.GraphDef()
        graph_def.ParseFromString(f.read())
        tensorflow.import_graph_def(graph_def, name='')

    with tensorflow.Session() as sess:
        # Feed the image_data as input to the graph and get first prediction
        softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')
        
    stringres = ''
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
                predictions = sess.run(softmax_tensor, {'DecodeJpeg/contents:0': image_data})
                
                top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
    
                result = {}
    
                for node_id in top_k:
                    human_string = label_lines[node_id]
                    score = predictions[0][node_id]
                    result[human_string] = score
                    
                if result['damage'] > .85:
                    boxes.append(numpy.array([i,j,i + w_limit, j + h_limit]))
                
                if (cont % 100) == 0:
                    print 'progress: %s' % (cont * 1.0 / total)
            
    no_overlap_boxes = non_max_suppression_fast(numpy.array(boxes), .1)
    inProj = Proj(init=projection)
    outProj = Proj(init='epsg:4326')
    for box in no_overlap_boxes:
        point = get_box_center(box)
        
        pretty_print(transform(inProj, outProj, point[0], point[1]))
    
    
    
def get_box_center(box):
    return int((box[0]+box[2]) / 2), int((box[1] + box[3]) / 2)
    
def pretty_print(lon_lat):
    
    print lon_lat[1], lon_lat[0]
    
def pixel_to_world(x, y, geotransform):
    
    world_x = geotransform[0] + x * geotransform[1] + y * geotransform[2]
    world_y = geotransform[3] + x * geotransform[4] + y * geotransform[5] 
    
    return world_x, world_y
    