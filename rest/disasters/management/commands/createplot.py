#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Oct 17, 2017

@author: agutierrez
'''

import csv
import json

import PIL.Image
from django.core.management.base import BaseCommand
import matplotlib
from matplotlib.pyplot import savefig
from numpy import shape
import numpy
from skimage import io
from sklearn.manifold import TSNE

import matplotlib.pyplot as plt
from rest.disasters.management.commands.createmodel import COLOR_3, COLOR_4, \
    COLOR_6
from rest.disasters.models import Image, get_images_by_town_id
from rest.settings import IMAGE_FOLDER


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--file', help='path to the new model')

    def handle(self, *args, **options):
        filepath = options['file']
        
        print filepath


        colors = {'U-J-S':'#d53e4f',
                  'U-S-J':'#fc8d59',
                  'J-U-S':'#fee08b',
                  'J-S-U':'#e6f598',
                  'S-U-J':'#99d594',
                  'S-J-U':'#3288bd'}
        x = []
        y = []
        
        all = []
        with open(filepath, 'rb') as csvfile:
            data = csv.reader(csvfile, delimiter=',')
            headers = data.next()
            for row in data:
                dataPoints = {}
                dataPoints['town'] = row[0]
                dataPoints['y'] = map(float,row[1:])
                all.append(dataPoints)

        x = map(int,headers[1:])

        
        for town in all:
            print town
        
            print x
            print town['y']
            plt.plot(x,town['y'], 'o-', c=colors[town['town']], alpha=1, label=town['town'])
            
        plt.ylim((0.45,0.95))
        
        plt.xlabel('Training Set Size')
        plt.ylabel('Accuracy')
        
        plt.title('Retrained Model')
        
        plt.legend(loc="lower right",title="Permutation", shadow=False)
        savefig('validation-plot.png')
        
        
        
    