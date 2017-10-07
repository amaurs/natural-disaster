'''
Created on Oct 5, 2017

@author: agutierrez
'''

import os
import random
import sys
import uuid

import PIL
from django.core.management.base import BaseCommand
from django.db.models.query_utils import Q

from rest.disasters.models import Sample, Label
from rest.settings import THUMB_FOLDER, AUGMENT_FOLDER, \
    TARGET_WIDTH, TARGET_HEIGHT


def create_random_transformation(image_path, target_path):
    img = PIL.Image.open(image_path)
    width, height = img.size
    rotate = random.randint(0,359)
    rotated = img.rotate(rotate)
    if random.random() < .5:
        rotated = rotated.transpose(PIL.Image.FLIP_LEFT_RIGHT)
    if random.random() < .5:   
        rotated = rotated.transpose(PIL.Image.FLIP_TOP_BOTTOM)
        
    x = (width - TARGET_WIDTH) / 2
    y = (height - TARGET_HEIGHT) /2
    rotated.crop((x, y, x + TARGET_WIDTH, y + TARGET_HEIGHT)).save(target_path)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--label', help='deletes the database')
        
    args = '<foo bar ...>'
    help = 'our help string comes here'

    def handle(self, *args, **options):
        label_name = options['label']
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
            
        directory = '%s/%s' % (AUGMENT_FOLDER, label_name)
        print directory
        if not os.path.exists(directory):
            os.makedirs(directory) 
        else:
            print 'Path exists.'                   
                                              
        samples = Sample.objects.all().filter(query_group)
        
        print samples.count()
        
        for sample in samples:
            new_path = '%s/%s' % (THUMB_FOLDER, sample.name)
            for i in range(10):
                new_name = '%s.jpg' % uuid.uuid4()
                target_path = '%s/%s' % (directory, new_name)
                create_random_transformation(new_path, target_path)
        