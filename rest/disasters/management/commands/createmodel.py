#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Oct 11, 2017

@author: agutierrez
'''


from datetime import datetime
import json
import random
from shutil import copyfile
import uuid

from django.core.management.base import BaseCommand
from matplotlib.pyplot import savefig
import numpy
from rasterio.rio.insp import plt
from skimage.feature import hog
from sklearn.metrics.ranking import roc_curve, auc
import tensorflow
from tensorflow.python.framework import graph_util
from tensorflow.python.platform import gfile

from rest.disasters.management.commands.createhogmodel import get_test_set, \
    classic_model
from rest.disasters.models import Model
from rest.disasters.util import make_dir
from rest.disasters.util.predict import TensorModel
from rest.disasters.util.retrain import create_image_lists_from_database, \
    maybe_download_and_extract, create_inception_graph, \
    cache_bottlenecks, add_final_training_ops, add_evaluation_step, \
    get_random_cached_bottlenecks, create_image_list_cross_town, \
    create_image_lists_from_database_cross
from rest.settings import MODEL_FOLDER, TEMP_FOLDER, BOTTLENECK_FOLDER


COLOR_3 = '#e66101'
COLOR_4 = '#fdb863'
COLOR_5 = '#b2abd2'
COLOR_6 = '#5e3c99'

def random_model(ground_truth):
    
    total = 0
    for element in ground_truth:

        choice = random.randint(0,1)

        
        if choice == numpy.argmin(element):
            total = total + 1 
    
    print 1.0 * total / len(ground_truth)


def hog_model(image_lists):
    
    print image_lists
    
def tensorflow_model(image_dir, image_lists):
    
    make_dir(TEMP_FOLDER)
    make_dir(BOTTLENECK_FOLDER)
    bottleneck_dir = BOTTLENECK_FOLDER
    
    final_tensor_name = 'final_result'
    
    how_many_training_steps = 1000
    train_batch_size = 10
    summaries_dir = TEMP_FOLDER
    validation_batch_size = 10
    eval_step_interval = 20
    test_batch_size = 200
    output_graph = 'damage_graph.pb'
    output_labels = 'damage_labels.txt'
    
    model_filename = maybe_download_and_extract(TEMP_FOLDER,'http://download.tensorflow.org/models/image/imagenet/inception-2015-12-05.tgz')
    graph, bottleneck_tensor, jpeg_data_tensor, resized_image_tensor = create_inception_graph(model_filename, 'pool_3/_reshape:0','DecodeJpeg/contents:0','ResizeBilinear:0')
    
    
    
    session = tensorflow.Session()
    
    do_distort_images = False
    
    if do_distort_images:
        pass
    else:    
        cache_bottlenecks(session, image_lists, image_dir, BOTTLENECK_FOLDER,
                  jpeg_data_tensor, bottleneck_tensor)
    
    (train_step, cross_entropy, bottleneck_input, ground_truth_input, final_tensor) = add_final_training_ops(len(image_lists.keys()),
                                      final_tensor_name,
                                      bottleneck_tensor)
    
    # Create the operations we need to evaluate the accuracy of our new layer.
    evaluation_step, prediction = add_evaluation_step(
            final_tensor, ground_truth_input)

    # Merge all the summaries and write them out to /tmp/retrain_logs (by default)
    merged = tensorflow.summary.merge_all()
    train_writer = tensorflow.summary.FileWriter(summaries_dir + '/train',
                                   session.graph)
    validation_writer = tensorflow.summary.FileWriter(summaries_dir + '/validation')

    # Set up all our weights to their initial default values.
    init = tensorflow.global_variables_initializer()
    session.run(init)
    
    for i in range(how_many_training_steps):
        if do_distort_images:
            pass
        else:
            train_bottlenecks, train_ground_truth, _ = get_random_cached_bottlenecks(
                session, image_lists, train_batch_size, 'training',
                bottleneck_dir, image_dir, jpeg_data_tensor,
                bottleneck_tensor)
        train_summary, _ = session.run([merged, train_step],
         feed_dict={bottleneck_input: train_bottlenecks,
                    ground_truth_input: train_ground_truth})
        train_writer.add_summary(train_summary, i)
        is_last_step = (i + 1 == how_many_training_steps)
        if (i % eval_step_interval) == 0 or is_last_step:
            train_accuracy, cross_entropy_value = session.run(
                [evaluation_step, cross_entropy],
                feed_dict={bottleneck_input: train_bottlenecks,
                           ground_truth_input: train_ground_truth})
            print('%s: Step %d: Train accuracy = %.1f%%' % (datetime.now(), i,
                                                  train_accuracy * 100))
            print('%s: Step %d: Cross entropy = %f' % (datetime.now(), i,
                                             cross_entropy_value))
            validation_bottlenecks, validation_ground_truth, _ = (
                get_random_cached_bottlenecks(
                    session, image_lists, validation_batch_size, 'validation',
                    bottleneck_dir, image_dir, jpeg_data_tensor,
                    bottleneck_tensor))
            # Run a validation step and capture training summaries for TensorBoard
            # with the `merged` op.
            validation_summary, validation_accuracy = session.run(
                    [merged, evaluation_step],
                    feed_dict={bottleneck_input: validation_bottlenecks,
                               ground_truth_input: validation_ground_truth})
            validation_writer.add_summary(validation_summary, i)
            print('%s: Step %d: Validation accuracy = %.1f%% (N=%d)' %
                  (datetime.now(), i, validation_accuracy * 100,
                   len(validation_bottlenecks)))
    test_bottlenecks, test_ground_truth, test_filenames = (
                get_random_cached_bottlenecks(session, image_lists, test_batch_size,
                                'testing', bottleneck_dir,
                                image_dir, jpeg_data_tensor,
                                bottleneck_tensor))
    test_accuracy, predictions, scores = session.run(
            [evaluation_step, prediction, session.graph.get_tensor_by_name('final_result:0')],
            feed_dict={bottleneck_input: test_bottlenecks,
             ground_truth_input: test_ground_truth})
    
    print test_filenames[:5]
    print predictions
    print scores[:, 1]
    
    
    y_test = map(numpy.argmax,test_ground_truth)
    
    print y_test
    
    
    fpr, tpr, _ = roc_curve(y_test, scores[:, 1])
    roc_auc = auc(fpr, tpr)
        
    plt.figure()
    lw = 2
    plt.plot(fpr, tpr, color=COLOR_4,
                 lw=lw, label='ROC curve (area = %0.2f)' % roc_auc)
    
    for i in range(len(tpr)):
        print "tpr: %s fpr: %s thres: %s" % (tpr[i],fpr[i],_[i])
    #plt.annotate(_[40], (plt.annotate(_[20], (fpr[20],tpr[20])),tpr[40]))
    #plt.annotate(_[35], (fpr[35],tpr[35]))
    #plt.annotate(_[30], (fpr[30],tpr[30]))
    
    plt.plot([0, 1], [0, 1], color=COLOR_6, lw=lw, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    #plt.title('Receiver operating characteristic example')
    plt.legend(loc="lower right")
    savefig('roc.png')
    
    
    
    correct = 0
    for i in range(len(predictions)):
        if numpy.argmax(test_ground_truth[i]) == predictions[i]:
            correct = correct + 1
    
    acc = 1.0 * correct / len(predictions)
    print acc
    print test_accuracy
    print len(predictions)
    
    
    print('Final test accuracy = %.1f%% (N=%d)' % (
        test_accuracy * 100, len(test_bottlenecks)))
    # Write out the trained graph and labels with the weights stored as constants.
    output_graph_def = graph_util.convert_variables_to_constants(
        session, graph.as_graph_def(), [final_tensor_name])
    with gfile.FastGFile(output_graph, 'wb') as f:
        f.write(output_graph_def.SerializeToString())
    with gfile.FastGFile(output_labels, 'w') as f:
        f.write('\n'.join(image_lists.keys()) + '\n')
    
    
    random_model(test_ground_truth)
    
    new_name = '%s.pb' % uuid.uuid4()
    new_path = '%s/%s' % (MODEL_FOLDER, new_name)
    
    model_object = Model(name=new_name,
                         path=new_path,
                         accuracy=float(test_accuracy),
                         original_model=output_graph) 
    model_object.save()
    copyfile(output_graph, new_path)
    
    session.close()
    return acc, new_path
class Command(BaseCommand):


    def handle(self, *args, **options):
        
        
        sizes = [20, 50, 100, 150, 200]
        
        means_acc = []
        means_std_acc = []
        hog_acc = []
        
        size = 200
        
        image_dir = '/Users/agutierrez/Documents/oaxaca/thumb'
        
        image_lists = create_image_lists_from_database(['damage','nodamage'], testing_percentage=33, validation_percentage=22)
        
        print "testing %s" % len(image_lists['damage']['testing'])
        print "validation %s" % len(image_lists['damage']['validation'])
        print "training %s" % len(image_lists['damage']['training'])
        print "testing %s" % len(image_lists['nodamage']['testing'])
        print "validation %s" % len(image_lists['nodamage']['validation'])
        print "training %s" % len(image_lists['nodamage']['training'])
        

        
        train_towns = [2,3]
        test_towns = [1]
        
        
        
        accuracy, model_path = tensorflow_model(image_dir, image_lists)
        
        
        '''
        model = TensorModel(model_path)
        
        y_score = []
        y_test = []
        
        for tag in ['damage','nodamage']:
            for image in image_lists[tag]['testing']:
                image_path = '%s/%s' % (image_dir,image)
                print image_path
                y_score.append(model.predict_from_file(image_path))
                if 'damage' == tag:
                    y_test.append(1)
                else:
                    y_test.append(0)
                    
        fpr, tpr, _ = roc_curve(y_test, y_score)
        roc_auc = auc(fpr, tpr)
        
        plt.figure()
        lw = 2
        plt.plot(fpr, tpr, color='darkorange',
                 lw=lw, label='ROC curve (area = %0.2f)' % roc_auc[2])
        plt.plot([0, 1], [0, 1], color='navy', lw=lw, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver operating characteristic example')
        plt.legend(loc="lower right")
        savefig('roc.png')
                
        '''
        
        
            
       
            
        #with open('accuracies-all.txt', 'a') as myfile:
        #    myfile.write('%s\n' % tensorflow_model(image_dir, image_lists))
        #    #tensorflow_acc.append(tensorflow_model(image_dir, image_lists)) 
        
        
        
        '''
        for size in sizes:
            print 'Size: %s' % size
            image_lists = create_image_lists_from_database_cross(train_towns, test_towns, ['damage','nodamage'], 30, size)
            
            #image_lists = create_image_lists_from_database(['damage','nodamage'], testing_percentage=33, validation_percentage=22, size=size)
            #image_lists_helper = create_image_lists_from_database_cross(train_towns, test_towns, ['damage','nodamage'], 30, size)
          
            #image_lists['damage']['testing'] = image_lists_helper['damage']['testing']
            #image_lists['nodamage']['testing'] = image_lists_helper['nodamage']['testing']
            print "testing %s" % len(image_lists['damage']['testing'])
            print "validation %s" % len(image_lists['damage']['validation'])
            print "training %s" % len(image_lists['damage']['training'])
            print "testing %s" % len(image_lists['nodamage']['testing'])
            print "validation %s" % len(image_lists['nodamage']['validation'])
            print "training %s" % len(image_lists['nodamage']['training'])
            
            #tensorflow_acc.append(tensorflow_model(image_dir, image_lists)) 
            means_acc.append(classic_model(image_dir, image_lists, 'means'))
            means_std_acc.append(classic_model(image_dir, image_lists, 'meanstd'))
            hog_acc.append(classic_model(image_dir, image_lists, 'hog'))
            
        #all
        #tensorflow_acc = [0.845, 0.795,0.915,0.955,0.95]
        #1,2,3
        #tensorflow_acc =[0.825,0.845,0.78,0.73,0.79]
        #1,3,2
        #tensorflow_acc =[0.75,0.885,0.915,0.91,0.93]
        #2,3,1
        tensorflow_acc =[0.755,0.78,0.845,0.845,0.87]
        
        
        plt.scatter(sizes, tensorflow_acc, c=COLOR_3, label='tensorflow')
        plt.plot(sizes, tensorflow_acc, c=COLOR_3)
        plt.scatter(sizes, means_acc, c=COLOR_4, label='means')
        plt.plot(sizes, means_acc, c=COLOR_4)
        plt.scatter(sizes, means_std_acc, c=COLOR_5, label='meanstd')
        plt.plot(sizes, means_std_acc, c=COLOR_5)
        plt.scatter(sizes, hog_acc, c=COLOR_6, label='hog')
        plt.plot(sizes, hog_acc, c=COLOR_6)
        plt.legend(bbox_to_anchor=(0,1.02,1,1.02), loc="lower left", shadow=True, mode='expand', ncol=4)
        plt.ylabel('Accuracy')
        plt.xlabel('Training Set Size')
        savefig('accuracies-%s-%s.png' % (train_towns, test_towns))
        #savefig('accuracies-all.png')
        '''
        
        

        
        
       
        
        
        