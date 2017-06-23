'''
Created on Jun 22, 2017

@author: agutierrez
'''

from __future__ import unicode_literals

import logging

import rasterio

from flood.core.controller.base import BaseCommand
from flood.mapper.data import scene
from flood.persistence.database.connection import delete_database, \
    create_database
from flood.persistence.driver import persist_data


LOGGER = logging.getLogger(__name__)

class Command(BaseCommand):
    '''
    classdocs
    '''
    def add_arguments(self, parser):
        '''
        Adds the sum argument for this command, of course this will change in
        the final implementation.
        '''
        parser.add_argument('--file', help='deletes the database')

    def handle(self, **options):
        '''
        In this example command, the values that come from the user input are
        added up and the result is printed in the screen.
        '''
        images_file = options['file']
        print images_file
        with open(images_file) as urls:
            content = urls.readlines()
            for url in content:
                LOGGER.info('Ingesting %s ' % url)
                my_scene = scene.Data(2014, url.strip())
                print my_scene.image_path
                persist_data(my_scene)
