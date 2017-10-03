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
    checked = models.BooleanField()
    town = models.ForeignKey(Town, related_name='image')
    models.CharField(max_length=50)

class Sample(models.Model):
    name = models.CharField(max_length=50)
    url = models.CharField(max_length=50)
    image = models.ForeignKey(Image, related_name='features')
    width = models.IntegerField()
    height = models.IntegerField()
    x = models.IntegerField()
    y = models.IntegerField()
    label = models.ForeignKey(Label, related_name='label')



