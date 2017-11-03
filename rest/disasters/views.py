# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

import PIL
from rest_framework import viewsets, generics
from rest_framework.mixins import UpdateModelMixin
from rest_framework.response import Response
import tensorflow

from rest.disasters.models import Image, Sample, Model, Town, Debris
from rest.disasters.serializers import ImageSerializer, SampleSerializer, \
    DebrisSerializer
from rest.disasters.util import make_dir
from rest.disasters.util.predict import TensorModel, simple_predict
from rest.settings import IMAGE_FOLDER, PREDICT_FOLDER


class DebrisList(generics.ListCreateAPIView):
    '''
    This method shows the damaged places.
    '''
    queryset = Debris.objects.all()
    serializer_class = DebrisSerializer
    pagination_class = None

class ImageList(generics.ListCreateAPIView):
    '''
    This method creates a queryset filtering by town, this means
    only images from that town will be displayed.
    '''
    town = Town.objects.get(pk=3)
    queryset = Image.objects.filter(town=town)
    serializer_class = ImageSerializer
    
class ImageAllList(generics.ListCreateAPIView):
    '''
    This method creates a queryset filtering by town, this means
    only images from that town will be displayed.
    '''
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

class ImageDetail(generics.RetrieveUpdateDestroyAPIView):

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        make_dir(PREDICT_FOLDER)
        new_path = '%s/%s' % (IMAGE_FOLDER, instance.name)
        predict_path = '%s/%s' % (PREDICT_FOLDER, instance.name)
        
        x = int(kwargs['x'])
        y = int(kwargs['y'])
        w = int(kwargs['w'])
        h = int(kwargs['h'])

        image_mem = PIL.Image.open(new_path)
        
        image_mem.crop((x,
                        y,
                        x + w,
                        y + h)).save(predict_path)    
        
        return Response(simple_predict(predict_path))
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    
class SampleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Sample.objects.all().order_by('-pk')
    serializer_class = SampleSerializer
    
    
