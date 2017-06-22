'''
Created on Jun 22, 2017

@author: agutierrez
'''

from __future__ import unicode_literals

from flood.core.controller.base import BaseCommand


class Command(BaseCommand):
    '''
    classdocs
    '''
    def add_arguments(self, parser):
        '''
        Adds the sum argument for this command, of course this will change in
        the final implementation.
        '''

    def handle(self, **options):
        '''
        In this example command, the values that come from the user input are
        added up and the result is printed in the screen.
        '''
        print 'hello'