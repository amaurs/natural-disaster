# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys

import PIL
from django.shortcuts import render
from rest_framework import viewsets, generics
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.response import Response
import tensorflow

from rest.disasters.models import Image, Sample
from rest.disasters.serializers import ImageSerializer, SampleSerializer
from rest.settings import IMAGE_FOLDER, PREDICT_FOLDER, MODEL_FOLDER


def predict(image_path):
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

    # Read in the image_data
    image_data = tensorflow.gfile.FastGFile(image_path, 'rb').read()

    # Loads label file, strips off carriage return
    label_lines = [line.rstrip() for line 
                   in tensorflow.gfile.GFile("%s/damage_labels.txt" % (MODEL_FOLDER))]

    # Unpersists graph from file
    with tensorflow.gfile.FastGFile("%s/damage_graph.pb"  % (MODEL_FOLDER), 'rb') as f:
        graph_def = tensorflow.GraphDef()
        graph_def.ParseFromString(f.read())
        tensorflow.import_graph_def(graph_def, name='')

    with tensorflow.Session() as sess:
        # Feed the image_data as input to the graph and get first prediction
        softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')
    
    predictions = sess.run(softmax_tensor, \
             {'DecodeJpeg/contents:0': image_data})
    
    # Sort to show labels of first prediction in order of confidence
    top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
    
    result = {}
    
    for node_id in top_k:
        human_string = label_lines[node_id]
        score = predictions[0][node_id]
        result[human_string] = score
    return result

class ImageViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """


    def retrieve(self, request, *args, **kwargs):
        print 'I am in the retrieve method.'
        print args
        print kwargs
        print request.data.viewkeys()
        
        return RetrieveModelMixin.retrieve(self, request, *args, **kwargs)

    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    
class ImageList(generics.ListCreateAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer


class ImageDetail(generics.RetrieveUpdateDestroyAPIView):

    def get(self, request, *args, **kwargs):
        print 'Inside the get method.'
        return self.retrieve(request, *args, **kwargs)

    
    def retrieve(self, request, *args, **kwargs):
        print 'I am in the retrieve method.'
        print args
        print kwargs
        print request.data.viewkeys()
        instance = self.get_object()
        
        print instance.name
        
        if not os.path.exists(PREDICT_FOLDER):
            os.makedirs(PREDICT_FOLDER)
        
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
        
        return Response(predict(predict_path))
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    
class SampleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer