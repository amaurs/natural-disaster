# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models


class Town(models.Model):
    name = models.CharField(max_length=50)
    
class Label(models.Model):
    name = models.CharField(max_length=50)

class Image(models.Model):
    name = models.CharField(max_length=50)
    date = models.DateTimeField()
    original_name = models.CharField(max_length=50,default=None)
    gps = models.CharField(max_length=200)
    checked = models.BooleanField()
    url = models.CharField(max_length=50,default=None)
    town = models.ForeignKey(Town, related_name='town')
    models.CharField(max_length=50)

class Sample(models.Model):
    name = models.CharField(max_length=50)
    url = models.CharField(max_length=50)
    image = models.ForeignKey(Image, related_name='image')
    width = models.IntegerField()
    height = models.IntegerField()
    x = models.IntegerField()
    y = models.IntegerField()
    label = models.ForeignKey(Label, related_name='label')



