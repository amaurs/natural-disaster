'''
Created on Oct 11, 2017

@author: agutierrez
'''
import hashlib
import os
import re
import struct
import sys
import tarfile

from django.db.models.query_utils import Q
from tensorflow.python.platform import gfile
from tensorflow.python.util import compat

from rest.disasters.models import Label, Sample
from rest.disasters.util import make_dir
from six.moves import urllib


def get_query_group(label_name):
    low = Label.objects.all().get(name='Bajo')
    medium = Label.objects.all().get(name='Medio')
    severe = Label.objects.all().get(name='Severo')
    absent = Label.objects.all().get(name='Ausente')
        
    if label_name == 'damage':
        query_group = Q(label=low) | Q(label=medium) | Q(label=severe)
            
    elif label_name == 'nodamage':
        query_group = Q(label=absent)
    else:
        print 'Label should be damage or nodamage.'
        sys.exit(-1)
    return query_group

def create_image_lists(image_dir, testing_percentage, validation_percentage, max_num_images_per_class=134217727):

    if not gfile.Exists(image_dir):
        print("Image directory '" + image_dir + "' not found.")
        return None
    result = {}
    sub_dirs = [x[0] for x in gfile.Walk(image_dir)]
    print sub_dirs
    # The root directory comes first, so skip it.
    is_root_dir = True
    for sub_dir in sub_dirs:
        if is_root_dir:
            is_root_dir = False
            continue
        extensions = ['jpg', 'jpeg', 'JPG', 'JPEG']
        file_list = []
        dir_name = os.path.basename(sub_dir)
        if dir_name == image_dir:
            continue
        print("Looking for images in '" + dir_name + "'")
        for extension in extensions:
            file_glob = os.path.join(image_dir, dir_name, '*.' + extension)
            print gfile.Glob(file_glob)
            file_list.extend(gfile.Glob(file_glob))
        if not file_list:
            print('No files found')
            continue
        if len(file_list) < 20:
            print('WARNING: Folder has less than 20 images, which may cause issues.')
        elif len(file_list) > max_num_images_per_class:
            print('WARNING: Folder {} has more than {} images. Some images will '
                  'never be selected.'.format(dir_name, max_num_images_per_class))
        label_name = re.sub(r'[^a-z0-9]+', ' ', dir_name.lower())
        training_images = []
        testing_images = []
        validation_images = []
        for file_name in file_list:
            print file_name
            base_name = os.path.basename(file_name)
            # We want to ignore anything after '_nohash_' in the file name when
            # deciding which set to put an image in, the data set creator has a way of
            # grouping photos that are close variations of each other. For example
            # this is used in the plant disease data set to group multiple pictures of
            # the same leaf.
            print base_name
            hash_name = re.sub(r'_nohash_.*$', '', file_name)
            print hash_name
            # This looks a bit magical, but we need to decide whether this file should
            # go into the training, testing, or validation sets, and we want to keep
            # existing files in the same set even if more files are subsequently
            # added.
            # To do that, we need a stable way of deciding based on just the file name
            # itself, so we do a hash of that and then use that to generate a
            # probability value that we use to assign it.
            hash_name_hashed = hashlib.sha1(compat.as_bytes(hash_name)).hexdigest()
            print hash_name_hashed
            print int(hash_name_hashed, 16)
            percentage_hash = ((int(hash_name_hashed, 16) %
                                (max_num_images_per_class + 1)) *
                               (100.0 / max_num_images_per_class))
            print percentage_hash
            if percentage_hash < validation_percentage:
                validation_images.append(base_name)
            elif percentage_hash < (testing_percentage + validation_percentage):
                testing_images.append(base_name)
            else:
                training_images.append(base_name)
        result[label_name] = {
               'dir': dir_name,
               'training': training_images,
               'testing': testing_images,
               'validation': validation_images,
            }
    return result

def create_image_list_from_database(label_name, testing_percentage, validation_percentage, max_num_images_per_class=134217727):
    
    
    images = []
    query_group = get_query_group(label_name)
    samples = Sample.objects.all().filter(query_group)
    
    for sample in samples.iterator():
        images.append(sample.name)
        
        
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
            'training': training_images,
            'testing': testing_images,
            'validation': validation_images
            }
    

def create_image_lists_from_database(label_names, testing_percentage, validation_percentage):
    
    result = {}
    for label in label_names:
        result[label] = create_image_list_from_database(label, testing_percentage, validation_percentage) 

    return result

def maybe_download_and_extract(target_directory, model_url):

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
    
def write_list_of_floats_to_file(list_of_floats , file_path, bottleneck_tensor_size=2048):
    s = struct.pack('d' * bottleneck_tensor_size, *list_of_floats)
    with open(file_path, 'wb') as f:
        f.write(s)


def read_list_of_floats_from_file(file_path, bottleneck_tensor_size=2048):
    with open(file_path, 'rb') as f:
        s = struct.unpack('d' * bottleneck_tensor_size, f.read())
    return list(s) 
