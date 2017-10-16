'''
Created on Oct 11, 2017

@author: agutierrez
'''


from datetime import datetime
import json

from django.core.management.base import BaseCommand
import tensorflow
from tensorflow.python.framework import graph_util
from tensorflow.python.platform import gfile

from rest.disasters.util import make_dir
from rest.disasters.util.retrain import create_image_lists_from_database, \
    create_image_lists, maybe_download_and_extract, create_inception_graph, \
    cache_bottlenecks, add_final_training_ops, add_evaluation_step, \
    get_random_cached_bottlenecks
from rest.settings import MODEL_FOLDER, TEMP_FOLDER, BOTTLENECK_FOLDER


class Command(BaseCommand):


    def handle(self, *args, **options):
        #parsed = create_image_lists('/Users/agutierrez/tf_files/augment/',10,10)
        image_lists = create_image_lists_from_database(['damage','nodamage'], 10, 10)
        image_dir = '/Users/agutierrez/Documents/oaxaca/thumb'
        #print json.dumps(parsed, indent=4, sort_keys=True)
        make_dir(TEMP_FOLDER)
        make_dir(BOTTLENECK_FOLDER)
        bottleneck_dir = BOTTLENECK_FOLDER
        
        final_tensor_name = 'final_result'
        
        how_many_training_steps = 5000
        train_batch_size = 100
        summaries_dir = TEMP_FOLDER
        validation_batch_size = 100
        eval_step_interval = 10
        test_batch_size = -1
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
        test_accuracy, predictions = session.run(
                [evaluation_step, prediction],
                feed_dict={bottleneck_input: test_bottlenecks,
                 ground_truth_input: test_ground_truth})
        print('Final test accuracy = %.1f%% (N=%d)' % (
            test_accuracy * 100, len(test_bottlenecks)))
        # Write out the trained graph and labels with the weights stored as constants.
        output_graph_def = graph_util.convert_variables_to_constants(
            session, graph.as_graph_def(), [final_tensor_name])
        with gfile.FastGFile(output_graph, 'wb') as f:
            f.write(output_graph_def.SerializeToString())
        with gfile.FastGFile(output_labels, 'w') as f:
            f.write('\n'.join(image_lists.keys()) + '\n')
        print 'Done'