'''
Created on Oct 2, 2017

@author: agutierrez
'''

from django.contrib.auth.models import User
from rest_framework import serializers

from rest.disasters.models import Image, Sample, Label, Town


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
        fields = ('url',)
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
        sample = Sample.objects.create(label=label_object, image=image_object,**validated_data)
        return sample
        