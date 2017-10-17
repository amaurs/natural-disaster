#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, connection


class Town(models.Model):
    name = models.CharField(max_length=50)
    
class Label(models.Model):
    '''
    This model just represents the label to which each 
    sample is classified.
    '''
    name = models.CharField(max_length=50)

class Image(models.Model):
    name = models.CharField(max_length=50)
    date = models.DateTimeField()
    original_name = models.CharField(max_length=50,default=None)
    gps = models.CharField(max_length=200)
    checked = models.BooleanField()
    url = models.CharField(max_length=200,default=None)
    town = models.ForeignKey(Town, related_name='town')
    models.CharField(max_length=50)
    lat = models.FloatField(default=0.0)
    lon = models.FloatField(default=0.0)
    

class Sample(models.Model):
    name = models.CharField(max_length=50)
    url = models.CharField(max_length=200)
    image = models.ForeignKey(Image, related_name='image')
    width = models.IntegerField()
    height = models.IntegerField()
    x = models.IntegerField()
    y = models.IntegerField()
    label = models.ForeignKey(Label, related_name='label')

class Model(models.Model):
    '''
    Represents a model that was trained to predict on new data. Different
    models can achieve different accuracies.
    '''
    name = models.CharField(max_length=50)
    path = models.CharField(max_length=200)
    original_model = models.CharField(max_length=200)
    accuracy = models.FloatField()
    trains_with = models.ManyToManyField(Sample, through='TrainsWith')
    
    class Meta:
        ordering = ['accuracy']
    
class TrainsWith(models.Model):
    '''
    This extra table represents the relationship between the models
    and the samples it is trained with. A sample can be part of the
    test, training or validation sets.
    '''
    model = models.ForeignKey(Model, related_name='model', on_delete=models.CASCADE)
    sample = models.ForeignKey(Sample, related_name='sample', on_delete=models.CASCADE)
    type = models.CharField(max_length=50)
    
def get_samples_by_town(town):
    with connection.cursor() as cursor:
        cursor.execute('SELECT s.name FROM disasters_sample AS s, disasters_image \
                                                       AS i, disasters_town \
                                                       AS t \
                                                       WHERE s.image_id=i.id \
                                                       AND i.town_id=t.id \
                                                       AND t.name=%s', [town])
        result = cursor.fetchall()
    return [row[0] for row in result]

def get_samples_by_town_and_label(town, label):
    
    with connection.cursor() as cursor:
        cursor.execute('SELECT s.name FROM disasters_sample AS s, \
                                           disasters_image AS i, \
                                           disasters_town AS t, \
                                           disasters_label AS l \
                                                       WHERE s.image_id=i.id \
                                                       AND i.town_id=t.id \
                                                       AND s.label_id=l.id \
                                                       AND t.name=%s \
                                                       AND l.name=%s', [town, label])
        
        
        result = cursor.fetchall()
    return [row[0] for row in result]
    

    


