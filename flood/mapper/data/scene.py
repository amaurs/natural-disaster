'''
Created on Jun 23, 2017

@author: agutierrez
'''
from __future__ import unicode_literals

import rasterio

from flood.configuration import SETTINGS
from flood.mapper.base import BaseData
from flood.persistence.database.connection import Scene
from flood.util import get_base_name, create_file_name, check_if_file_exists, get_basename_of_file


def maybe_download(filename, work_directory, url):
    print filename
    print work_directory
    
    image_file = create_file_name(work_directory, filename)
    
    print image_file
    if check_if_file_exists(image_file):
        print 'The file already exists!'
    else:
        print 'Does not exist, must download it.'
        import urllib
        urllib.urlretrieve (url, image_file)

class Data(BaseData):
    def __init__(self, image_path, year, url):
        self.image_path = image_path
        self.year = year
        self.temporary = getattr(SETTINGS, 'TEMP_FOLDER')
        self.destiny = getattr(SETTINGS, 'DATA_FOLDER')
        self.url = url
        self.name = get_base_name(self.image_path)
        filename = get_basename_of_file(self.image_path)
        maybe_download(filename, self.temporary, self.url)
        print url
        
        with rasterio.open(self.image_path) as dataset:
            self.width = dataset.width
            self.height = dataset.height
        
    def get_database_object(self):
        
        
        
        return Scene(name=self.name,
                     width=self.width,
                     height=self.height,
                     year=self.year,
                     path=self.destiny,
                     url=self.url)
    def get_output_directory(self):
        return self.destiny
    
    def get_files(self):
        return [self.image_path]

