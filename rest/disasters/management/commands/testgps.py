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
from skimage import io
from sklearn.manifold import TSNE

import matplotlib.pyplot as plt
from rest.disasters.models import Image, get_images_by_town_id
from rest.settings import IMAGE_FOLDER


def extract_mean_std_feature_vector(image_path):
    image_array = PIL.Image.open(image_path)    
    mean_array = numpy.mean(image_array, axis=(0, 1))
    std_array = numpy.std(image_array, axis=(0, 1))
    return numpy.concatenate((mean_array, std_array), axis=0)

class Command(BaseCommand):
    def handle(self, *args, **options):
        
        #image_path = '%s/%s' % (IMAGE_FOLDER, '1f66274c-7900-4a65-9a53-26fb5e79d52d.jpg')
        image_path = '%s/%s' % (IMAGE_FOLDER, '25460d51-6b6e-4417-a728-615be7d3da0b.jpg')
        print extract_mean_std_feature_vector(image_path)
        
        colors = {1:'r',2:'g',3:'b'}
        feature_array = []
        towns = []
        for town in range(1,4):
            for image in get_images_by_town_id(town):
                print image
                image_path = '%s/%s' % (IMAGE_FOLDER, image)
                feature_array.append(extract_mean_std_feature_vector(image_path))
                towns.append(town)
        tsne = TSNE(n_components=2, init='random', verbose=1,
                         random_state=0, perplexity=40, n_iter=300)
        
        X = numpy.array(feature_array)
        result = tsne.fit_transform(X)
        
        for i in range(len(result)):
            plt.scatter(result[i][0], result[i][1], c=colors[towns[i]], alpha=0.5)
        savefig('t-sne.png')
        
        
        
        
    