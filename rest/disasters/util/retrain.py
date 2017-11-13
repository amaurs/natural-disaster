'''
Created on Oct 11, 2017

@author: agutierrez
'''
import hashlib
import os
import random
import re
import struct
import sys
import tarfile

from django.db.models.query_utils import Q
import numpy
import tensorflow
from tensorflow.contrib.slim.python.slim.nets.resnet_v1 import bottleneck
from tensorflow.python.platform import gfile
from tensorflow.python.util import compat

from rest.disasters.models import Label, Sample, get_samples_by_town_and_label
from rest.disasters.util import make_dir
from six.moves import urllib


def get_query_group(label_name):
    present = Label.objects.all().get(name='Presente')
    absent = Label.objects.all().get(name='Ausente')
        
    if label_name == 'damage':
        query_group = Q(label=present) 
            
    elif label_name == 'nodamage':
        query_group = Q(label=absent)
    else:
        print 'Label should be damage or nodamage.'
        sys.exit(-1)
    return query_group

def get_query_label(label_name):
    dictionary = {'damage':'Presente', 'nodamage':'Ausente'}
    return dictionary[label_name]


def create_image_list_cross_town(training_towns, test_towns, label_name, validation_percentage, query_size, max_num_images_per_class=134217727):
    
    training_images = []
    testing_images = []
    validation_images = []
    
    query_size_by_town = int(query_size / 4)
    
    label_id = Label.objects.get(name=label_name)
    
    
    for test_town in test_towns:
        for town in Sample.objects.filter(town_id=test_town, label=label_id):
            testing_images.append(town.name)
            
    for training_town in training_towns:
        for town in Sample.objects.filter(town_id=training_town, label=label_id)[:query_size_by_town]:
            image_name = town.name
            name_hashed = hashlib.sha1(compat.as_bytes(image_name)).hexdigest()
            percentage_hash = ((int(name_hashed, 16) %
                                (max_num_images_per_class + 1)) *
                               (100.0 / max_num_images_per_class))
            if percentage_hash < validation_percentage:
                validation_images.append(image_name)
            else:
                training_images.append(image_name)
    return {
            'dir':label_name,
            'training': training_images,
            'training_size': len(training_images),
            'testing': testing_images,
            'testing_size': len(testing_images),
            'validation': validation_images,
            'validation_size': len(validation_images)
            }

def create_image_list_from_database(label_name, testing_percentage, validation_percentage, max_num_images_per_class=134217727):
    
    
    
    images = get_samples_by_town_and_label(label_name)
        
        
    training_images = []
    testing_images = []
    validation_images = []
    
    for image_name in images:
        name_hashed = hashlib.sha1(compat.as_bytes(image_name)).hexdigest()
        percentage_hash = ((int(name_hashed, 16) %
                                (max_num_images_per_class + 1)) *
                               (100.0 / max_num_images_per_class))
        if percentage_hash < validation_percentage:
            validation_images.append(image_name)
        elif percentage_hash < (testing_percentage + validation_percentage):
            testing_images.append(image_name)
        else:
            training_images.append(image_name)
    
                
    return {
            'dir':label_name,
            'training': training_images,
            'testing': testing_images,
            'validation': validation_images
            }
    

def create_image_lists_from_database(label_names, testing_percentage, validation_percentage):
    
    result = {}
    for label in label_names:
        result[label] = create_image_list_from_database(get_query_label(label), testing_percentage, validation_percentage) 

    return result


def create_image_lists_from_database_cross(training_towns, testing_towns, label_names, validation_percentage, query_size):
    
    result = {}
    for label in label_names:
        result[label] = create_image_list_cross_town(training_towns, testing_towns, get_query_label(label), validation_percentage, query_size) 

    return result

def maybe_download_and_extract(target_directory, model_url):
    pb_file = ''
    make_dir(target_directory)
    filename = model_url.split('/')[-1]
    filepath = os.path.join(target_directory, filename)
    if not os.path.exists(filepath):

        def _progress(count, block_size, total_size):
            sys.stdout.write('\r>> Downloading %s %.1f%%' %
                       (filename,
                        float(count * block_size) / float(total_size) * 100.0))
            sys.stdout.flush()

        filepath, _ = urllib.request.urlretrieve(model_url,
                                             filepath,
                                             _progress)
        statinfo = os.stat(filepath)
        print 'Successfully downloaded: %s %s bytes' % (filename, statinfo.st_size)
    else:
        statinfo = os.stat(filepath)
        print 'File already exists: %s %s bytes' % (filename, statinfo.st_size)
    tarfile.open(filepath, 'r:gz').extractall(target_directory) 
    print dir(target_directory)

    for f in os.listdir(target_directory):
        if f.endswith('.pb'):
            pb_file = os.path.join(target_directory, f)
            
    return pb_file
    
def create_inception_graph(model_filename, bottleneck_tensor_name, jpeg_data_tensor_name, resized_input_tensor_name):
  
    with tensorflow.Session() as sess:
        with gfile.FastGFile(model_filename, 'rb') as f:
            graph_def = tensorflow.GraphDef()
            graph_def.ParseFromString(f.read())
            bottleneck_tensor, jpeg_data_tensor, resized_input_tensor = (
                tensorflow.import_graph_def(graph_def, name='', return_elements=[
                    bottleneck_tensor_name, jpeg_data_tensor_name,
                    resized_input_tensor_name]))
    return sess.graph, bottleneck_tensor, jpeg_data_tensor, resized_input_tensor

def get_image_path(image_lists, label_name, index, image_dir, category):

    if label_name not in image_lists:
        tensorflow.logging.fatal('Label does not exist %s.', label_name)
    label_lists = image_lists[label_name]
    if category not in label_lists:
        tensorflow.logging.fatal('Category does not exist %s.', category)
    category_list = label_lists[category]
    if not category_list:
        tensorflow.logging.fatal('Label %s has no images in the category %s.',
                     label_name, category)
    mod_index = index % len(category_list)
    base_name = category_list[mod_index]
    #print label_lists
    #sub_dir = label_lists['dir']
    full_path = os.path.join(image_dir, base_name)
    return full_path

def write_list_of_floats_to_file(list_of_floats , file_path, bottleneck_tensor_size=2048):
    s = struct.pack('d' * bottleneck_tensor_size, *list_of_floats)
    with open(file_path, 'wb') as f:
        f.write(s)


def read_list_of_floats_from_file(file_path, bottleneck_tensor_size=2048):
    with open(file_path, 'rb') as f:
        s = struct.unpack('d' * bottleneck_tensor_size, f.read())
    return list(s) 

def cache_bottlenecks(session, image_lists, image_dir, bottleneck_dir,
                      jpeg_data_tensor, bottleneck_tensor):
    how_many_bottlenecks = 0
    make_dir(bottleneck_dir)
    for label_name, label_lists in image_lists.items():
        for category in ['training', 'testing', 'validation']:
            category_list = label_lists[category]
            for index, unused_base_name in enumerate(category_list):
                get_or_create_bottleneck(session, image_lists, label_name, index,
                                 image_dir, category, bottleneck_dir,
                                 jpeg_data_tensor, bottleneck_tensor)

                how_many_bottlenecks += 1

                print(str(how_many_bottlenecks) + ' bottleneck files created.')
                
                
def get_or_create_bottleneck(sess, image_lists, label_name, index, image_dir,
                             category, bottleneck_dir, jpeg_data_tensor,
                             bottleneck_tensor):

    label_lists = image_lists[label_name]
    sub_dir = label_lists['dir']
    sub_dir_path = os.path.join(bottleneck_dir, sub_dir)
    make_dir(sub_dir_path)
    bottleneck_path = get_bottleneck_path(image_lists, label_name, index, bottleneck_dir, category)
    if not os.path.exists(bottleneck_path):
        create_bottleneck_file(bottleneck_path, image_lists, label_name, index, image_dir, category, sess, jpeg_data_tensor, bottleneck_tensor)
    with open(bottleneck_path, 'r') as bottleneck_file:
        bottleneck_string = bottleneck_file.read()
    did_hit_error = False
    try:
        bottleneck_values = [float(x) for x in bottleneck_string.split(',')]
    except:
        print("Invalid float found, recreating bottleneck")
        did_hit_error = True
    if did_hit_error:
        create_bottleneck_file(bottleneck_path, image_lists, label_name, index, image_dir, category, sess, jpeg_data_tensor, bottleneck_tensor)
        with open(bottleneck_path, 'r') as bottleneck_file:
            bottleneck_string = bottleneck_file.read()
        # Allow exceptions to propagate here, since they shouldn't happen after a fresh creation
        bottleneck_values = [float(x) for x in bottleneck_string.split(',')]
    return bottleneck_values


def create_bottleneck_file(bottleneck_path, image_lists, label_name, index,
                           image_dir, category, sess, jpeg_data_tensor, bottleneck_tensor):
    print('Creating bottleneck at ' + bottleneck_path)
    image_path = get_image_path(image_lists, label_name, index, image_dir, category)
    if not gfile.Exists(image_path):
        tensorflow.logging.fatal('File does not exist %s', image_path)
    image_data = gfile.FastGFile(image_path, 'rb').read()
    bottleneck_values = run_bottleneck_on_image(sess, image_data, jpeg_data_tensor, bottleneck_tensor)
    bottleneck_string = ','.join(str(x) for x in bottleneck_values)
    with open(bottleneck_path, 'w') as bottleneck_file:
        bottleneck_file.write(bottleneck_string)
        
def get_bottleneck_path(image_lists, label_name, index, bottleneck_dir,
                        category):
    return get_image_path(image_lists, label_name, index, bottleneck_dir,
                        category) + '.txt'
def run_bottleneck_on_image(sess, image_data, image_data_tensor,
                            bottleneck_tensor):

    bottleneck_values = sess.run(
        bottleneck_tensor,
        {image_data_tensor: image_data})
    bottleneck_values = numpy.squeeze(bottleneck_values)
    return bottleneck_values

def add_final_training_ops(class_count, final_tensor_name, bottleneck_tensor, bottleneck_tensor_size=2048, learning_rate=0.01):

    with tensorflow.name_scope('input'):
        bottleneck_input = tensorflow.placeholder_with_default(
            bottleneck_tensor, shape=[None, bottleneck_tensor_size],
            name='BottleneckInputPlaceholder')

        ground_truth_input = tensorflow.placeholder(tensorflow.float32,
                                        [None, class_count],
                                        name='GroundTruthInput')

    # Organizing the following ops as `final_training_ops` so they're easier
    # to see in TensorBoard
    layer_name = 'final_training_ops'
    with tensorflow.name_scope(layer_name):
        with tensorflow.name_scope('weights'):
            layer_weights = tensorflow.Variable(tensorflow.truncated_normal([bottleneck_tensor_size, class_count], stddev=0.001), name='final_weights')
            variable_summaries(layer_weights)
        with tensorflow.name_scope('biases'):
            layer_biases = tensorflow.Variable(tensorflow.zeros([class_count]), name='final_biases')
            variable_summaries(layer_biases)
        with tensorflow.name_scope('Wx_plus_b'):
            logits = tensorflow.matmul(bottleneck_input, layer_weights) + layer_biases
            tensorflow.summary.histogram('pre_activations', logits)

    final_tensor = tensorflow.nn.softmax(logits, name=final_tensor_name)
    tensorflow.summary.histogram('activations', final_tensor)

    with tensorflow.name_scope('cross_entropy'):
        cross_entropy = tensorflow.nn.softmax_cross_entropy_with_logits(
            labels=ground_truth_input, logits=logits)
        with tensorflow.name_scope('total'):
            cross_entropy_mean = tensorflow.reduce_mean(cross_entropy)
    tensorflow.summary.scalar('cross_entropy', cross_entropy_mean)

    with tensorflow.name_scope('train'):
        train_step = tensorflow.train.GradientDescentOptimizer(learning_rate).minimize(
            cross_entropy_mean)

    return (train_step, cross_entropy_mean, bottleneck_input, ground_truth_input, final_tensor)

def variable_summaries(var):

    with tensorflow.name_scope('summaries'):
        mean = tensorflow.reduce_mean(var)
        tensorflow.summary.scalar('mean', mean)
        with tensorflow.name_scope('stddev'):
            stddev = tensorflow.sqrt(tensorflow.reduce_mean(tensorflow.square(var - mean)))
        tensorflow.summary.scalar('stddev', stddev)
        tensorflow.summary.scalar('max', tensorflow.reduce_max(var))
        tensorflow.summary.scalar('min', tensorflow.reduce_min(var))
        tensorflow.summary.histogram('histogram', var)
        
def add_evaluation_step(result_tensor, ground_truth_tensor):

    with tensorflow.name_scope('accuracy'):
        with tensorflow.name_scope('correct_prediction'):
            prediction = tensorflow.argmax(result_tensor, 1)
            correct_prediction = tensorflow.equal(
                prediction, tensorflow.argmax(ground_truth_tensor, 1))
        with tensorflow.name_scope('accuracy'):
            evaluation_step = tensorflow.reduce_mean(tensorflow.cast(correct_prediction, tensorflow.float32))
    tensorflow.summary.scalar('accuracy', evaluation_step)
    return evaluation_step, prediction

def get_random_cached_bottlenecks(sess, image_lists, how_many, category,
                                  bottleneck_dir, image_dir, jpeg_data_tensor,
                                  bottleneck_tensor, max_num_images_per_class=134217727):

    class_count = len(image_lists.keys())
    bottlenecks = []
    ground_truths = []
    filenames = []
    if how_many >= 0:
        # Retrieve a random sample of bottlenecks.
        for unused_i in range(how_many):
            label_index = random.randrange(class_count)
            label_name = list(image_lists.keys())[label_index]
            image_index = random.randrange(max_num_images_per_class + 1)
            image_name = get_image_path(image_lists, label_name, image_index,
                                        image_dir, category)
            bottleneck = get_or_create_bottleneck(sess, image_lists, label_name,
                                                  image_index, image_dir, category,
                                                  bottleneck_dir, jpeg_data_tensor,
                                                  bottleneck_tensor)
            ground_truth = numpy.zeros(class_count, dtype=numpy.float32)
            ground_truth[label_index] = 1.0
            bottlenecks.append(bottleneck)
            ground_truths.append(ground_truth)
            filenames.append(image_name)
    else:
        # Retrieve all bottlenecks.
        for label_index, label_name in enumerate(image_lists.keys()):
            for image_index, image_name in enumerate(
                image_lists[label_name][category]):
                image_name = get_image_path(image_lists, label_name, image_index,
                                          image_dir, category)
                bottleneck = get_or_create_bottleneck(sess, image_lists, label_name,
                                                    image_index, image_dir, category,
                                                    bottleneck_dir, jpeg_data_tensor,
                                                    bottleneck_tensor)
                ground_truth = numpy.zeros(class_count, dtype=numpy.float32)
                ground_truth[label_index] = 1.0
                bottlenecks.append(bottleneck)
                ground_truths.append(ground_truth)
                filenames.append(image_name)
    return bottlenecks, ground_truths, filenames