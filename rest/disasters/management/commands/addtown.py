'''
Created on Oct 2, 2017

@author: agutierrez
'''
from django.core.management.base import BaseCommand

from rest.disasters.models import Town


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--town', help='deletes the database')
        
    args = '<foo bar ...>'
    help = 'our help string comes here'

    def handle(self, *args, **options):
        town_name = options['town']
        town = Town(name=town_name)
        town.save()
        

            
        