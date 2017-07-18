'''
Created on Jun 23, 2017

@author: agutierrez
'''

import shutil
from subprocess import PIPE
import subprocess
import uuid

from PIL import ImageOps, Image
from flask import Flask, jsonify, abort, make_response, request
from flask_cors.extension import CORS
import numpy
import rasterio

from flood.configuration import SETTINGS
from flood.mapper.data import sample
from flood.persistence.driver import get_random_scene, ingest_sample, \
    update_sample
from flood.util import  create_file_name


app = Flask(__name__)
CORS(app)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)
  
@app.route('/floods/training/<string:image_id>', methods=['GET'])
def image(image_id):
    training_destiny = getattr(SETTINGS, 'TRAINING_DATA_FOLDER')
    image_name = create_file_name(training_destiny, image_id)
    response = make_response(open(image_name).read())
    response.content_type = 'image/jpg'
    return response

@app.route("/floods/image", methods=['GET'])
def images():
    random_scene = get_random_scene().first()
    name = random_scene['name']
    path = random_scene['path']
    scene_id = random_scene['pk_id']
    filename = '%s.tif' % create_file_name(path, name)
    print filename
    with rasterio.open(filename) as src:
        r, g, b, a = src.read()
        scene_width = src.width
        scene_height = src.height
    image = numpy.array([r,g,b,a])
    print 'Array shape is %s, %s' % r.shape
    size_width = 322
    size_height = 322
    size = size_height
    offset_x = numpy.random.randint(size_width, scene_width) - size_width
    offset_y = numpy.random.randint(size_height, scene_height) - size_height
    print offset_x, offset_y
    rgbArray = numpy.zeros((size,size,3), 'uint8')
    rgbArray[..., 0] = r[offset_y:offset_y + size_height,offset_x:offset_x + size_width]
    rgbArray[..., 1] = g[offset_y:offset_y + size_height,offset_x:offset_x + size_width]
    rgbArray[..., 2] = b[offset_y:offset_y + size_height,offset_x:offset_x + size_width]
    
    im = Image.fromarray(rgbArray)
    training_data = getattr(SETTINGS, 'TRAINING_DATA_FOLDER')
    image_name = '%s.jpg' % uuid.uuid4()
    static_url = '/floods/training/%s' % image_name
    image_path = create_file_name(training_data, image_name)
    my_sample = sample.Data(image_name, offset_x, offset_y, size_width, size_height, scene_id, static_url)
    ingest_sample(my_sample)
    im.save(image_path)
    '''
    
    flip  = ImageOps.flip(im)
    mirror = ImageOps.mirror(im)
    diag = ImageOps.flip(mirror)
    name = 0
    for image in [im, flip, mirror, diag]:
        for i in range(0):    
            rot = image.rotate(i)
            width = rot.size[0]
            height = rot.size[1]
        
            final_width = (width - final_size) / 2
            final_height = (height - final_size) / 2
        
            crop = rot.crop((final_width, final_height, final_width + final_size, final_height + final_size))
        
            crop.save("/Users/agutierrez/Documents/stevens/test/rotate-%s-%s.jpg" % (name,i))
        name = name + 1
    
    '''
    response = jsonify({'image_name' : image_name})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route("/floods/predict", methods=['GET'])
def predict():
    random_scene = get_random_scene().first()
    name = random_scene['name']
    path = random_scene['path']
    scene_id = random_scene['pk_id']
    filename = '%s.tif' % create_file_name(path, name)
    print filename
    with rasterio.open(filename) as src:
        r, g, b, a = src.read()
        scene_width = src.width
        scene_height = src.height
    image = numpy.array([r,g,b,a])
    size_width = 322
    size_height = 322
    size = size_height
    offset_x = numpy.random.randint(size_width, scene_width) - size_width
    offset_y = numpy.random.randint(size_height, scene_height) - size_height
    rgbArray = numpy.zeros((size,size,3), 'uint8')
    rgbArray[..., 0] = r[offset_y:offset_y + size_height,offset_x:offset_x + size_width]
    rgbArray[..., 1] = g[offset_y:offset_y + size_height,offset_x:offset_x + size_width]
    rgbArray[..., 2] = b[offset_y:offset_y + size_height,offset_x:offset_x + size_width]
    im = Image.fromarray(rgbArray)
    training_data = getattr(SETTINGS, 'TRAINING_DATA_FOLDER')
    image_name = '%s.jpg' % uuid.uuid4()
    static_url = '/floods/training/%s' % image_name
    image_path = create_file_name(training_data, image_name)
    my_sample = sample.Data(image_name, offset_x, offset_y, size_width, size_height, scene_id, static_url)
    ingest_sample(my_sample)
    im.save(image_path)
    
    tensorflow_folder = '%s:/tf_files' % getattr(SETTINGS, 'TENSORFLOW_FOLDER')
    
    print tensorflow_folder
    
    destination = create_file_name(getattr(SETTINGS, 'TENSORFLOW_FOLDER'), 'unseen')
    print destination
    
    
    shutil.copy(image_path, destination)
    
    command_array = ['/usr/local/bin/docker','run', '--rm', '--volume', tensorflow_folder, '--workdir', '/tf_files', 'tensorflow/tensorflow:1.1.0', 'python', 'label_image.py', '/tf_files/unseen/%s' % image_name]
    
    command_string = ' '.join(command_array)
    print command_string
    
    docker_response = subprocess.Popen(command_string, stdout=PIPE, shell=True).stdout.read()
    
    
    response = jsonify({'image_name' : image_name, 'prediction' : docker_response.strip().split('\n')})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route("/floods/update", methods=['POST'])
def update():
    if not request.json or not 'water' in request.json or not 'name' in request.json:
        abort(400)
    name = request.json['name']
    water = request.json['water']
    update_sample(name, water)
    response = jsonify({'status': 'good'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

def run():
    app.run(debug=True)
