# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

import PIL
from rest_framework import viewsets, generics
from rest_framework.response import Response
import tensorflow

from rest.disasters.models import Image, Sample, Model, Town
from rest.disasters.serializers import ImageSerializer, SampleSerializer
from rest.disasters.util import make_dir
from rest.settings import IMAGE_FOLDER, PREDICT_FOLDER


def predict(image_path):
    '''
    This is a quick and dirty method to perform a prediction
    on a patch of an image. TODO: create a lazy method for the
    loading of the model so it only gets loaded once.
    '''
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

    image_data = tensorflow.gfile.FastGFile(image_path, 'rb').read()

    label_lines = ['nodamage', 'damage']
    model = Model.objects.all().order_by('-accuracy')

    with tensorflow.gfile.FastGFile(model[0].path, 'rb') as f:
        graph_def = tensorflow.GraphDef()
        graph_def.ParseFromString(f.read())
        tensorflow.import_graph_def(graph_def, name='')

    with tensorflow.Session() as sess:
        # Feed the image_data as input to the graph and get first prediction
        softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')
    
    predictions = sess.run(softmax_tensor, {'DecodeJpeg/contents:0': image_data})
    
    
    # Sort to show labels of first prediction in order of confidence
    top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
    
    result = {}
    for node_id in top_k:
        human_string = label_lines[node_id]
        score = predictions[0][node_id]
        result[human_string] = score
    return result
    
class ImageList(generics.ListCreateAPIView):
    '''
    This method creates a queryset filtering by town, this means
    only images from that town will be displayed.
    '''
    town = Town.objects.get(pk=2)
    queryset = Image.objects.filter(town=town)
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
        
        return Response(predict(predict_path))
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    
class SampleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer
    
    
