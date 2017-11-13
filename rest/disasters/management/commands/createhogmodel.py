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
from rest.disasters.util.retrain import create_image_lists_from_database, \
    create_image_lists_from_database_cross
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
    classifier = RandomForestClassifier(n_jobs=4, random_state=0)
    classifier.fit(X, y)
        
    X_train, y_train = get_X_y(image_dir, image_lists, ['testing'], method)
    predictions = classifier.predict(X_train)
    confusion = pandas.crosstab(y_train, predictions, rownames=['Actual Class'], colnames=['Predicted Class'])
        
    return accuracy_score(y_train, predictions)

class Command(BaseCommand):
    def handle(self, *args, **options):
        import numpy as np
        import matplotlib.pyplot as plt
        from itertools import cycle

        from sklearn import svm, datasets
        from sklearn.metrics import roc_curve, auc
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import label_binarize
        from sklearn.multiclass import OneVsRestClassifier
        from scipy import interp

        # Import some data to play with
        iris = datasets.load_iris()
        X = iris.data
        y = iris.target

        # Binarize the output
        y = label_binarize(y, classes=[0, 1, 2])
        n_classes = y.shape[1]

        # Add noisy features to make the problem harder    
        random_state = np.random.RandomState(0)
        n_samples, n_features = X.shape
        X = np.c_[X, random_state.randn(n_samples, 200 * n_features)]

        # shuffle and split training and test sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.5,
                                                    random_state=0)

        # Learn to predict each class against the other
        classifier = OneVsRestClassifier(svm.SVC(kernel='linear', probability=True,
                                 random_state=random_state))
        y_score = classifier.fit(X_train, y_train).decision_function(X_test)

        print y_test[:, 0]
        print y_score[:, 0]
        
        # Compute ROC curve and ROC area for each class
        fpr = dict()
        tpr = dict()
        roc_auc = dict()
        for i in range(n_classes):
            fpr[i], tpr[i], _ = roc_curve(y_test[:, i], y_score[:, i])
            roc_auc[i] = auc(fpr[i], tpr[i])

        # Compute micro-average ROC curve and ROC area
        fpr["micro"], tpr["micro"], _ = roc_curve(y_test.ravel(), y_score.ravel())
        roc_auc["micro"] = auc(fpr["micro"], tpr["micro"])
        