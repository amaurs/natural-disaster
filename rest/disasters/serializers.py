'''
Created on Oct 2, 2017

@author: agutierrez
'''

import PIL
from django.contrib.auth.models import User
from rest_framework import serializers

from rest.disasters.models import Image, Sample, Label, Town
from rest.settings import IMAGE_FOLDER, THUMB_FOLDER
from rest_framework.serializers import BaseSerializer


class TownSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Town
        fields = ('name',)

class LabelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Label
        fields = ('name',)

class ImageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Image
        fields = ('pk','url',)
        
class SampleSerializer(serializers.HyperlinkedModelSerializer):
    image = ImageSerializer()
    label = LabelSerializer()
    class Meta:
        model = Sample
        fields = ('name', 'url', 'x', 'y', 'width', 'height', 'image', 'label',)
        
    def create(self, validated_data):
        image_url = validated_data.pop('image')['url']
        image_object = Image.objects.all().get(url=image_url)
        label_name = validated_data.pop('label')['name']
        label_object = Label.objects.all().get(name=label_name)
        parts = image_url.split('/')
        
        image_path = '%s/%s' % (IMAGE_FOLDER, parts[1])
        thumb_path = '%s/%s' % (THUMB_FOLDER, validated_data['name'])
        
        x = int(validated_data['x'])
        y = int(validated_data['y'])
        w = int(validated_data['width'])
        h = int(validated_data['height'])

        image_mem = PIL.Image.open(image_path)
        
        image_mem.crop((x,
                        y,
                        x + w,
                        y + h)).save(thumb_path)
        
        sample = Sample.objects.create(label=label_object, image=image_object,**validated_data)
        return sample
        