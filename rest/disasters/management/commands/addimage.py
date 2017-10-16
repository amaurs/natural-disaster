'''
Created on Oct 2, 2017

@author: agutierrez
'''
import json
import os
from shutil import copyfile
import uuid

from PIL.ExifTags import TAGS
import PIL.Image
from django.core.management.base import BaseCommand

from rest.disasters.models import Image, Town
from rest.settings import IMAGE_FOLDER, BASE_URL


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--image', help='deletes the database')
        parser.add_argument('--town', help='deletes the database')
        

    args = '<foo bar ...>'
    help = 'our help string comes here'

    def handle(self, *args, **options):
        '''
        This method adds a new image to the database. It also copies the image into the
        file system to make it easier to handle them. Originally the copy was made by
        creating a new image using PIL but this ended up in losing the metadata contained
        in the images.
        '''
        filename = options['image']
        town_name = str(options['town'])
        metadata = {}
        
        image_mem = PIL.Image.open(filename)
        
        for (k,v) in image_mem._getexif().iteritems():
            metadata[TAGS.get(k)] = v
            
        date_time =  metadata['DateTime'].split(' ')
        date_time[0] = date_time[0].replace(':','-')
        date_string = ' '.join(date_time)
        
        image_mem.copy()
        new_name = '%s.jpg' % uuid.uuid4()
        new_path = '%s/%s' % (IMAGE_FOLDER, new_name)

        copyfile(filename, new_path)
        
        town = Town.objects.get(name=town_name)
        image = Image(name=new_name,
                      date=date_string,
                      checked=False,
                      town=town,
                      url='%s/images/%s' % (BASE_URL,new_name),
                      gps=json.dumps(metadata['GPSInfo']),
                      original_name=os.path.splitext(os.path.basename(filename))[0]) 
        image.save()
        

            
        