#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Oct 17, 2017

@author: agutierrez
'''

import PIL.Image
from django.core.management.base import BaseCommand
import matplotlib
from matplotlib.pyplot import savefig
from numpy import shape
import numpy
from skimage import io, color
from skimage.feature._hog import hog
from sklearn.manifold import TSNE

import matplotlib.pyplot as plt
from rest.disasters.management.commands.createmodel import COLOR_3, COLOR_4, \
    COLOR_6
from rest.disasters.models import Image, get_images_by_town_id
from rest.settings import IMAGE_FOLDER


def extract_mean_std_feature_vector(image_path):
    image_array = PIL.Image.open(image_path)    
    mean_array = numpy.mean(image_array, axis=(0, 1))
    std_array = numpy.std(image_array, axis=(0, 1))
    return numpy.concatenate((mean_array, std_array), axis=0)

def extract_hog_feature_vector(image_path):
    image_array = io.imread(image_path)[0]
    
    image = color.rgb2gray(image_array)
    feature_array = hog(image, orientations=8, pixels_per_cell=(16, 16),
                    cells_per_block=(1, 1))
    del image_array
    return feature_array


class Command(BaseCommand):
    def handle(self, *args, **options):
        
        #image_path = '%s/%s' % (IMAGE_FOLDER, '1f66274c-7900-4a65-9a53-26fb5e79d52d.jpg')
        #image_path = '%s/%s' % (IMAGE_FOLDER, '25460d51-6b6e-4417-a728-615be7d3da0b.jpg')
        #print extract_mean_std_feature_vector(image_path)
        
        colors = {1:'#d53e4f',2:'#99d594',3:'#3288bd'}
        colors = {1:'#ffeda0',3:'#feb24c',2:'#f03b20'}
        labels = {3:r'$Uni\acute{o}n$ $Hidalgo$', 2:r'$Juchit\acute{a}n$ $de$ $Zaragoza$', 1:r'$Santa$ $Mar\acute{i}a$ $Xadani$'}
        towns_x = {1:[], 2:[], 3:[]}
        towns_y = {1:[], 2:[], 3:[]}
        feature_array = []
        towns = []
        cont = 0
        for town in range(1,4):
            for image in get_images_by_town_id(town):
                image_path = '%s/%s' % (IMAGE_FOLDER, image)
                
                print image_path
                feature_array.append(extract_mean_std_feature_vector(image_path))
                towns.append(town)
                cont = cont + 1
                print cont 
        tsne = TSNE(n_components=2, init='random', verbose=1,
                         random_state=0, perplexity=40, n_iter=300)
        
        X = numpy.array(feature_array)
        result = tsne.fit_transform(X)
        
        for i in range(len(result)):
            towns_x[towns[i]].append(result[i][0])
            towns_y[towns[i]].append(result[i][1])
        plt.scatter(towns_x[2],towns_y[2], c=colors[2], alpha=0.3, label=labels[2])
        plt.scatter(towns_x[1],towns_y[1], c=colors[1], alpha=0.3, label=labels[1])
        plt.scatter(towns_x[3],towns_y[3], c=colors[3], alpha=0.3, label=labels[3])
    
        #plt.title('t-SNE embedding of the images')
        plt.legend(loc="lower left", shadow=True)
        savefig('t-sne-bis.png')
        
        
        
        
    