'''
Created on Oct 2, 2017

@author: agutierrez
'''
import json
from uuid import uuid4
import uuid

from PIL.ExifTags import TAGS
import PIL.Image
from django.core.management.base import BaseCommand

from rest.disasters import models
from rest.disasters.models import Image, Town
from rest.settings import IMAGE_FOLDER
from flood.util import get_base_name


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--image', help='deletes the database')
        parser.add_argument('--town', help='deletes the database')
        

    args = '<foo bar ...>'
    help = 'our help string comes here'

    def handle(self, *args, **options):
        
        filename = options['image']
        town_name = options['town']
        metadata = {}
        
        image_mem = PIL.Image.open(filename)
        
        for (k,v) in image_mem._getexif().iteritems():
            metadata[TAGS.get(k)] = v
            
        
        date_time =  metadata['DateTime'].split(' ')
        
        date_time[0] = date_time[0].replace(':','-')
        
        date_string = ' '.join(date_time)
        
        print date_string
        image_mem.copy()
        new_name = '%s.jpg' % uuid.uuid4()
        new_path = '%s/%s' % (IMAGE_FOLDER,new_name)
        image_mem.save(new_path)
        
        town = Town.objects.get(name=town_name)
        image = Image(name=new_name,
                      date=date_string,
                      checked=False,
                      town=town,
                      url='images/%s' % new_name,
                      gps=json.dumps(metadata['GPSInfo']),
                      original_name=get_base_name(filename)) 
        image.save()
        

            
        