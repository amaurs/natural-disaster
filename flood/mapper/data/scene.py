'''
Created on Jun 23, 2017

@author: agutierrez
'''
from __future__ import unicode_literals

import rasterio

from flood.mapper.base import BaseData
from flood.persistence.database.connection import Scene

from flood.util import get_base_name
from flood.configuration import SETTINGS

class Data(BaseData):
    def __init__(self, image_path, year, url):
        self.image_path = image_path
        self.year = year
        self.temporary = getattr(SETTINGS, 'TEMP_FOLDER')
        self.destiny = getattr(SETTINGS, 'DATA_FOLDER')
        self.url = url
        with rasterio.open(self.image_path) as dataset:
            self.width = dataset.width
            self.height = dataset.height
        
    def get_database_object(self):
        name = get_base_name(self.image_path)
        
        
        return Scene(name=name,
                     width=self.width,
                     height=self.height,
                     year=self.year,
                     path=self.destiny,
                     url=self.url)
    def get_output_directory(self):
        return self.destiny
    
    def get_files(self):
        return [self.image_path]

        