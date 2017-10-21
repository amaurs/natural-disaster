'''
Created on Oct 18, 2017

@author: agutierrez
'''
import json
import time
import urllib2

from django.core.management.base import BaseCommand

from rest.disasters.util.geo import apply_prediction_on_raster, \
    apply_prediction_on_image, address_from_lat_lon


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--path', help='path to the new model')
        parser.add_argument('--town', help='path to the new model')

    def handle(self, *args, **options):
        filepath = options['path']
        town_name = options['town']
        start_time = time.time()
        
        
        apply_prediction_on_raster(filepath, town_name)
        #apply_prediction_on_image(imagepath)
        
        print 'Command execution is done in %s seconds.' % (time.time() - start_time)