'''
Created on Oct 20, 2017

@author: agutierrez
'''
import PIL.Image
import tensorflow

from rest.disasters.models import Model
from rest.settings import TEMP_FOLDER


def simple_predict(image_path):
    '''
    This is a quick and dirty method to perform a prediction
    on a patch of an image.
    '''
    label_lines = ['nodamage', 'damage']
    models = Model.objects.all().order_by('-accuracy')
    tensor_model = TensorModel(models[0].path)
    predictions = tensor_model.predict_from_file(image_path)
    top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
    result = {}
    for node_id in top_k:
        human_string = label_lines[node_id]
        score = predictions[0][node_id]
        result[human_string] = score
    return result


class TensorModel(object):
    '''
    classdocs
    '''
    def __init__(self, model_path):
        
        with tensorflow.gfile.FastGFile(model_path, 'rb') as model_file:
            graph_def = tensorflow.GraphDef()
            graph_def.ParseFromString(model_file.read())
            tensorflow.import_graph_def(graph_def, name='')
        self.session = tensorflow.Session()
        self.softmax_tensor = self.session.graph.get_tensor_by_name('final_result:0')
    def predict_from_file(self, image_path):
        '''
        This method loads a jpg from memory and then predicts using the loaded model.
        '''
        image_data = tensorflow.gfile.FastGFile(image_path, 'rb').read()
        predictions = self.session.run(self.softmax_tensor, {'DecodeJpeg/contents:0': image_data})
        return predictions
    def predict_from_array(self, data_array):
        '''
        This method writes the array into a jpg and the reads it using predict from file.
        '''
        im = PIL.Image.fromarray(data_array)
        temporary_file = '%s/%s' % (TEMP_FOLDER, 'temp.jpg')
        im.save(temporary_file)
        return self.predict_from_file(temporary_file)
        
        