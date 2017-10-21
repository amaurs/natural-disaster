'''
Created on Oct 18, 2017

@author: agutierrez
'''
import time

from django.core.management.base import BaseCommand

from rest.disasters.util.geo import apply_prediction_on_raster, \
    apply_prediction_on_image


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--path', help='path to the new model')
        parser.add_argument('--image', help='path to the new model')

    def handle(self, *args, **options):
        filepath = options['path']
        imagepath = options['image']
        start_time = time.time()
        
        #crop(filepath, 0, 0, 299, 299)
        
        #apply_prediction_on_raster(filepath)
        apply_prediction_on_image(imagepath)
        
        print 'Command execution is done in %s seconds.' % (time.time() - start_time)