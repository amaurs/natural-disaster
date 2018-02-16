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
        parser.add_argument('--townid', help='path to the new model')
        parser.add_argument('--modelpath', help='path to the new model')
        parser.add_argument('--threshold', help='path to the new model')
        

    def handle(self, *args, **options):
        filepath = options['path']
        town_id = options['townid']
        modelpath = options['modelpath']
        threshold = float(options['threshold'])
        start_time = time.time()
        
        
        apply_prediction_on_raster(filepath, town_id, modelpath, threshold)
        
        #imagepath = '/Users/agutierrez/Documents/oaxaca/images/9bd8763a-d0af-48f5-855e-f29e2659bc24.jpg'
        #contrast = '/Users/agutierrez/Documents/oaxaca/temp/9bd8763a-d0af-48f5-855e-f29e2659bc24-orig.jpg'
        #model_path = '/Users/agutierrez/Documents/oaxaca/model/6ed1bf7a-c1c9-4b6f-ba29-25eeca8699a5.pb'
        #threshold = 0.96
        
        #apply_prediction_on_image(imagepath, contrast, model_path, threshold)
        
        print 'Command execution is done in %s seconds.' % (time.time() - start_time)