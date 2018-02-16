#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Oct 16, 2017

@author: agutierrez
'''
import itertools
import json

from django.core.management.base import BaseCommand
from matplotlib.pyplot import savefig
import numpy
import pandas
from skimage import data, io, color
from skimage.feature._hog import hog
from sklearn import svm
from sklearn.ensemble.forest import RandomForestClassifier
from sklearn.metrics.classification import accuracy_score

import matplotlib.pyplot as plt
from rest.disasters.models import get_samples_by_town_and_label
from rest.disasters.util.retrain import create_image_lists_from_database, \
    create_image_lists_from_database_cross, \
    create_image_dict_from_database_by_town
from rest.settings import IMAGE_FOLDER, THUMB_FOLDER


def extract_hog_feature_vector(image_path):
    image_array = io.imread(image_path)
    image = color.rgb2gray(image_array)
    feature_array = hog(image, orientations=8, pixels_per_cell=(16, 16),
                    cells_per_block=(1, 1))
    del image_array
    return feature_array

def extract_mean_feature_vector(image_path):
    image_array = io.imread(image_path)
    mean_array = numpy.mean(image_array, axis=(0, 1))
    del image_array
    return mean_array

def extract_mean_std_feature_vector(image_path):
    image_array = io.imread(image_path)
    mean_array = numpy.mean(image_array, axis=(0, 1))
    std_array = numpy.std(image_array, axis=(0, 1))
    
    del image_array
    return numpy.concatenate((mean_array, std_array), axis=0)

def get_test_set():
    test_damage_list = get_samples_by_town_and_label('Unión Hidalgo', 'Presente') + \
                        get_samples_by_town_and_label('Santa María Xadani', 'Presente')
    
    test_no_damage_list = get_samples_by_town_and_label('Unión Hidalgo', 'Ausente') + \
                            get_samples_by_town_and_label('Santa María Xadani', 'Ausente')
    result = {}
    
    result['damage'] = {'testing' : test_damage_list}
    result['nodamage'] = {'testing' : test_no_damage_list}

    return result

def get_X_y(image_dir, image_lists, labels, method='hog'):
    feature_array = []
    target_array = []
    
    
    
    for tag in image_lists.keys():
        for label in labels:
            for image in image_lists[tag][label]:
                image_path = '%s/%s' % (image_dir,image)
                if method == 'hog':
                    feature_array.append(extract_hog_feature_vector(image_path))
                elif method == 'meanstd':
                    feature_array.append(extract_mean_std_feature_vector(image_path))
                elif method == 'means':
                    feature_array.append(extract_mean_feature_vector(image_path))
                target_array.append(tag)
    X = numpy.array(feature_array)
    y = pandas.factorize(target_array)[0]
    return X, y

def classic_model(image_dir, image_lists, method):

    X, y = get_X_y(image_dir, image_lists, ['training', 'validation'], method)
    classifier = RandomForestClassifier(n_estimators=1000, n_jobs=4)
    classifier.fit(X, y)
        
    X_test, y_test = get_X_y(image_dir, image_lists, ['testing'], method)
    predictions = classifier.predict(X_test)
    confusion = pandas.crosstab(y_test, predictions, rownames=['Actual Class'], colnames=['Predicted Class'])
    print confusion
    return accuracy_score(y_test, predictions)

class Command(BaseCommand):
    

    def handle(self, *args, **options):
        


        image_dir = '/Users/agutierrez/Documents/oaxaca/thumb'
        
        perms = list(itertools.permutations([0, 1, 2]))
        

        
        # 0 Unión Hidalgo        Juchitán de Zaragoza Santa María Xadani 
        # 1 Unión Hidalgo        Santa María Xadani   Juchitán de Zaragoza
        # 2 Juchitán de Zaragoza Unión Hidalgo        Santa María Xadani *
        # 3 Juchitán de Zaragoza Santa María Xadani   Unión Hidalgo *
        # 4 Santa María Xadani   Unión Hidalgo        Juchitán de Zaragoza  
        # 5 Santa María Xadani   Juchitán de Zaragoza Unión Hidalgo *
        
        towns = ['Unión Hidalgo','Juchitán de Zaragoza','Santa María Xadani']
        
        sizes = [10, 25, 50, 100]
        perm_nums = [2, 3, 4]
        models = ['hog', 'meanstd', 'means']
        
        final_data = {}
        
        labels = {3:'JS-U',2:'JU-S',4:'SU-J'}
        
        colors = {'U-J-S':'#d53e4f',
                  'U-S-J':'#fc8d59',
                  'J-U-S':'#fee08b',
                  'J-S-U':'#e6f598',
                  'S-U-J':'#99d594',
                  'S-J-U':'#3288bd'}
        colors = {2:'#ffeda0',3:'#feb24c',4:'#f03b20'}
        
        for model in models:
            print '*************************************************'
            print model
            model_data = {}
            for perm_num in perm_nums:
                perm = perms[perm_num]
                x = []
                y = []
                town_data = {}
                for size in sizes:
                    image_lists = create_image_dict_from_database_by_town(['damage','nodamage'], towns[perm[0]], towns[perm[2]], towns[perm[1]], size)
                    
                    print "%s%s-%s" % (towns[perm[0]][0],towns[perm[1]][0], towns[perm[2]][0])
                    print "%s" % labels[perm_num]
                    print "Testing town ************* %s" % towns[perm[2]]
                    print "testing %s" % len(image_lists['damage']['testing'])
                    print "validation %s" % len(image_lists['damage']['validation'])
                    print "training %s" % len(image_lists['damage']['training'])
                    print "testing %s" % len(image_lists['nodamage']['testing'])
                    print "validation %s" % len(image_lists['nodamage']['validation'])
                    print "training %s" % len(image_lists['nodamage']['training'])
                    accuracy = classic_model(image_dir, image_lists, method=model)
                    
                    x.append(size * 4)
                    y.append(accuracy)
                    
                    #print 'Size: %s Accuracy: %s'
        
                town_data['x'] = x
                town_data['y'] = y
        
                model_data[labels[perm_num]] = town_data
            final_data[model] = model_data
            
        with open('classic-data.txt', 'w') as outfile:
            json.dump(final_data, outfile)
        for model in models:
            model_data = final_data[model]
            for perm_num in perm_nums:
                town_data = model_data[labels[perm_num]]
    
                plt.plot(town_data['x'], town_data['y'], 'o-', c=colors[perm_num], alpha=1, label=labels[perm_num])

                plt.xlabel('Training Set Size')
                plt.ylabel('Accuracy')
        
        
            plt.legend(loc="lower right",title="Permutation", shadow=False)
            savefig('classic-%s.png' % model)
            plt.clf() 

    
        
        
        

        