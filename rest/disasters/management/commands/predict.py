'''
Created on Oct 9, 2017

@author: agutierrez
'''


import time

from PIL import ImageDraw
import PIL
from django.core.management.base import BaseCommand
import numpy
import tensorflow

from rest.disasters.views import predict
from rest.settings import MODEL_FOLDER


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--path', help='deletes the database')
        
    args = '<foo bar ...>'
    help = 'our help string comes here'

    def handle(self, *args, **options):
        filepath = options['path']
        #print predict(filepath)
        
        image = PIL.Image.open(filepath)
        
        width = image.width
        height = image.height
        
        w = h = 250
        
        result = numpy.zeros((width,height))
        
        
        # Loads label file, strips off carriage return
        label_lines = [line.rstrip() for line 
            in tensorflow.gfile.GFile("%s/damage_labels.txt" % (MODEL_FOLDER))]

        # Unpersists graph from file
        with tensorflow.gfile.FastGFile("%s/damage_graph.pb"  % (MODEL_FOLDER), 'rb') as f:
            graph_def = tensorflow.GraphDef()
            graph_def.ParseFromString(f.read())
            tensorflow.import_graph_def(graph_def, name='')

        with tensorflow.Session() as sess:
            # Feed the image_data as input to the graph and get first prediction
            softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')
        
        stringres = ''
        
        start_time = time.time()
        
        
        draw = ImageDraw.Draw(image)
        
        
        
        for j in range(0, height, h):
            for i in range(0, width, w):
                #print '%s-%s.jpg' % (i,j)
                image.crop((i,
                            j,
                            i + w,
                            j + h)).save('aux.jpg')
                #res = predict('aux.jpg')
                
                image_data = tensorflow.gfile.FastGFile('aux.jpg', 'rb').read()
                
                predictions = sess.run(softmax_tensor, {'DecodeJpeg/contents:0': image_data})
    
                # Sort to show labels of first prediction in order of confidence
                top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
    
                result = {}
    
                for node_id in top_k:
                    human_string = label_lines[node_id]
                    score = predictions[0][node_id]
                    result[human_string] = score
                
                
                
                
                if result['damage'] > .80:
                    draw.rectangle([i, j, i + w, j + w], outline="red")
                    draw.rectangle([i+1, j+1, i + w-1, j + w-1], outline="red")
                    stringres = stringres + "1"
                else:
                    stringres = stringres + "0"
            print stringres
            stringres = ''
        
        image.save('result.jpg')
        print 'Command execution is done in %s seconds.' % (time.time() - start_time)
        del draw
        