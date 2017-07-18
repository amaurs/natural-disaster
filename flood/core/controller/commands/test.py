'''
Created on Jul 17, 2017

@author: agutierrez
'''

from __future__ import unicode_literals

import shutil
from subprocess import PIPE
import subprocess

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
        parser.add_argument('--image', help='deletes the database')

    def handle(self, **options):
        '''
        In this example command, the values that come from the user input are
        added up and the result is printed in the screen.
        '''
        image = options['image']
        response = subprocess.Popen('/usr/local/bin/docker run --publish 6006:6006   --volume /Users/agutierrez/tf_files:/tf_files   --workdir /tf_files   tensorflow/tensorflow:1.1.0 python label_image.py %s' % image, stdout=PIPE, shell=True).stdout.read()
        print response.split('\n')[0]
            