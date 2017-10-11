'''
Created on Oct 2, 2017

@author: agutierrez
'''
import json
import os
from shutil import copyfile
from uuid import uuid4
import uuid

from PIL.ExifTags import TAGS
import PIL.Image
from PIL._imaging import path
from django.core.management.base import BaseCommand
from tensorflow.contrib.metrics.python.metrics.classification import accuracy

from rest.disasters import models
from rest.disasters.models import Image, Town, Model
from rest.settings import IMAGE_FOLDER, MODEL_FOLDER


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--path', help='path to the new model')
        parser.add_argument('--accuracy', help='model accuracy')
        parser.add_argument('--originalmodel', help='model in which this is based on')
        

    args = '<foo bar ...>'
    help = 'our help string comes here'

    def handle(self, *args, **options):
        
        path = options['path']
        accuracy = options['accuracy']
        original_model = options['originalmodel']
        
        if not os.path.exists(MODEL_FOLDER):
            os.makedirs(MODEL_FOLDER) 
        
        new_name = '%s.pb' % uuid.uuid4()
        new_path = '%s/%s' % (MODEL_FOLDER, new_name)
        
        
        copyfile(path, new_path)
        
        model_object = Model(name=new_name,
                             path=new_path,
                             accuracy=float(accuracy),
                             original_model=original_model) 
        model_object.save()

            
        