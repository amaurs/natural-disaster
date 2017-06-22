'''
Created on Jun 22, 2017

@author: agutierrez
'''

from __future__ import unicode_literals

from flood.core.controller.base import BaseCommand
from flood.persistence.database.connection import delete_database, \
    create_database


class Command(BaseCommand):
    '''
    classdocs
    '''
    def add_arguments(self, parser):
        '''
        Adds the sum argument for this command, of course this will change in
        the final implementation.
        '''
        parser.add_argument('--delete', help='deletes the database',  action='store_true')

    def handle(self, **options):
        '''
        In this example command, the values that come from the user input are
        added up and the result is printed in the screen.
        '''
        if options['delete']:
            delete_database()
        else:
            create_database()