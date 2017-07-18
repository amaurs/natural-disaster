'''
Created on Jul 17, 2017

@author: agutierrez
'''

from __future__ import unicode_literals

import shutil

from flood.configuration import SETTINGS
from flood.core.controller.base import BaseCommand
from flood.persistence.database.connection import delete_database, \
    create_database
from flood.persistence.driver import get_scene_paths
from flood.util import create_directory_path, create_file_name


class Command(BaseCommand):
    '''
    classdocs
    '''
    def add_arguments(self, parser):
        '''
        Adds the sum argument for this command, of course this will change in
        the final implementation.
        '''
        parser.add_argument('--folder', help='deletes the database')

    def handle(self, **options):
        '''
        In this example command, the values that come from the user input are
        added up and the result is printed in the screen.
        '''
        print 'hello'
        print options['folder']
        
        water_keys = {'water':2,
                      'land':0,
                      'mixed':1}
        
        create_directory_path(options['folder'])
        
        for key in water_keys:
            result = get_scene_paths(water_keys[key], 250)
            print key
            destination = create_file_name(options['folder'],key)
            print destination
            for row in result:
                create_directory_path(destination)
                filename = '%s/%s' % (getattr(SETTINGS, 'TRAINING_DATA_FOLDER'), row['name'])
                shutil.copy(filename, destination)
                print filename
            