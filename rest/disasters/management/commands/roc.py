#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Oct 11, 2017

@author: agutierrez
'''



import csv
import os

from django.core.management.base import BaseCommand
from matplotlib.pyplot import savefig
from rasterio.rio.insp import plt
from sklearn.metrics.ranking import roc_curve, auc


COLOR_3 = '#e66101'
COLOR_4 = '#fdb863'
COLOR_5 = '#b2abd2'
COLOR_6 = '#5e3c99'
class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--file', help='path to the new model')

    def handle(self, *args, **options):
        filepath = options['file']
        
        print filepath

        x = []
        y = []

        with open(filepath, 'rb') as csvfile:
            data = csv.reader(csvfile, delimiter=',')
            for row in data:
                x.append(float(row[0]))
                y.append(int(row[1]))
        print(x)
        print(y)
        
        fpr, tpr, _ = roc_curve(y, x)
        roc_auc = auc(fpr, tpr)
            
        plt.figure()
        lw = 2
        plt.plot(fpr, tpr, color=COLOR_4,
                     lw=lw, label='ROC curve (area = %0.2f)' % roc_auc)
        
        for i in range(len(tpr)):
            print "tpr: %s fpr: %s thres: %s" % (tpr[i],fpr[i],_[i])
        
        plt.plot([0, 1], [0, 1], color=COLOR_6, lw=lw, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.legend(loc="lower right")
        
        base = os.path.basename(filepath)
        os.path.splitext(base)[0]
        
        savefig('%s-roc.png' % base)