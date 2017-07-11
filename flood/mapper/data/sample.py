'''
Created on Jun 23, 2017

@author: agutierrez
'''
from __future__ import unicode_literals

from flood.mapper.base import BaseData
from flood.persistence.database.connection import Sample


class Data(BaseData):
    def __init__(self, name, x, y, width, height, scene_id, path):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.scene_id = scene_id
        self.path = path
        
    def get_database_object(self):
        return Sample(x=self.x,
                      y=self.y,
                      width=self.width,
                      height=self.height,
                      scene_id=self.scene_id,
                      name=self.name,
                      static_url=self.path,
                      water=None)
    def get_output_directory(self):
        return self.destiny
    def get_files(self):
        return [self.image_path]