'''
Created on Oct 2, 2017

@author: agutierrez
'''

from django.contrib.auth.models import User
from rest_framework import serializers

from rest.disasters.models import Image


class ImageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Image
        fields = '__all__'