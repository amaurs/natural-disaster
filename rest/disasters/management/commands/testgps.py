'''
Created on Oct 17, 2017

@author: agutierrez
'''

from django.core.management.base import BaseCommand

from rest.disasters.models import Image
from rest.disasters.util import get_lat_lon_from_database


class Command(BaseCommand):
    def handle(self, *args, **options):
       
        for image in Image.objects.all():
            lat, lon = get_lat_lon_from_database(image.gps)
            image.lat = lat
            image.lon = lon
            image.save()