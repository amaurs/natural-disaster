#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Oct 16, 2017

@author: agutierrez
'''
from django.core.management.base import BaseCommand
import numpy
import pandas
from skimage import data, io, color
from skimage.feature._hog import hog
from sklearn import svm
from sklearn.ensemble.forest import RandomForestClassifier
from sklearn.metrics.classification import accuracy_score

from rest.disasters.models import get_samples_by_town_and_label
from rest.disasters.util.retrain import create_image_lists_from_database
from rest.settings import IMAGE_FOLDER, THUMB_FOLDER


def extract_hog_feature_vector(image_path):
    image_array = io.imread(image_path)
    image = color.rgb2gray(image_array)
    feature_array = hog(image, orientations=8, pixels_per_cell=(16, 16),
                    cells_per_block=(1, 1))
    return feature_array

def extract_mean_feature_vector(image_path):
    image_array = io.imread(image_path)
    mean_array = numpy.mean(image_array, axis=(0, 1))
    return mean_array

def extract_mean_std_feature_vector(image_path):
    image_array = io.imread(image_path)
    mean_array = numpy.mean(image_array, axis=(0, 1))
    std_array = numpy.std(image_array, axis=(0, 1))
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

def get_X_y(image_lists, label, method='hog'):
    feature_array = []
    target_array = []
    for tag in image_lists.keys():
        for image in image_lists[tag][label]:
            image_path = '%s/%s' % (THUMB_FOLDER,image)
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
class Command(BaseCommand):
    def handle(self, *args, **options):
        image_lists = create_image_lists_from_database('Juchitán de Zaragoza', ['damage','nodamage'], 60, 0)
       
        method = 'meanstd'
        X, y = get_X_y(image_lists, 'training', method)
        classifier = RandomForestClassifier(n_jobs=4, random_state=0)

        #classifier = svm.SVC()
        classifier.fit(X, y)
        
        train_image_lists = get_test_set()
        X_train, y_train = get_X_y(train_image_lists, 'testing', method)
        
        predictions = classifier.predict(X_train)
        confusion = pandas.crosstab(y_train, predictions, rownames=['Actual Class'], colnames=['Predicted Class'])
        print confusion
        accuracy = accuracy_score(y_train, predictions)
        print accuracy
        
        