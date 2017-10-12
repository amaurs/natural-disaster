'''
Created on Oct 11, 2017

@author: agutierrez
'''


import json

from django.core.management.base import BaseCommand

from rest.disasters.util.retrain import create_image_lists_from_database, \
    create_image_lists, maybe_download_and_extract
from rest.settings import MODEL_FOLDER


class Command(BaseCommand):


    def handle(self, *args, **options):
        #parsed = create_image_lists('/Users/agutierrez/tf_files/augment/',10,10)
        #parsed = create_image_lists_from_database(['damage','nodamage'], 10, 10)
        #print json.dumps(parsed, indent=4, sort_keys=True)
        maybe_download_and_extract(MODEL_FOLDER,'http://download.tensorflow.org/models/image/imagenet/inception-2015-12-05.tgz')