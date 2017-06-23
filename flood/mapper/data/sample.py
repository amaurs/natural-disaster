'''
Created on Jun 23, 2017

@author: agutierrez
'''
from __future__ import unicode_literals

from flood.mapper.base import BaseData


class Data(BaseData):
    def __init__(self, image_path):
        self.image_path = image_path