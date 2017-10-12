'''
Created on Oct 11, 2017

@author: agutierrez
'''


import json

from django.core.management.base import BaseCommand

from rest.disasters.util.retrain import create_image_lists_from_database, \
    create_image_lists


class Command(BaseCommand):


    def handle(self, *args, **options):
        parsed = create_image_lists('/Users/agutierrez/tf_files/augment/',10,10)
        #parsed = create_image_lists_from_database(['damage','nodamage'], 10, 10)
        print json.dumps(parsed, indent=4, sort_keys=True)