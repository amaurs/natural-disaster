'''
Created on Oct 5, 2017

@author: agutierrez
'''

from django.core.management.base import BaseCommand

from rest.disasters.models import Town


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--label', help='deletes the database')
        
    args = '<foo bar ...>'
    help = 'our help string comes here'

    def handle(self, *args, **options):
        label_name = options['label']
        print label_name
        