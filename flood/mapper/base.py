'''
Created on Jun 23, 2017

@author: agutierrez
'''
from __future__ import unicode_literals

import abc
from datetime import datetime
import logging
import logging.config
import os
import re
import uuid

import geoalchemy2
print geoalchemy2.__file__

from geoalchemy2.elements import WKTElement

import ogr
import osr
try:
    from flood.persistence.database.connection import Scene, Sample
except:
    pass 

from flood.util import get_files_from_folder, create_file_name
import xml.dom.minidom as dom
import gdal


METADATA = "metadata"
IMAGE = "image"
FILE = "file"
QUICKLOOK = "quicklook"

LOGGER = logging.getLogger(__name__)

def _xml_to_json(element, stack, dictionary):
    '''
    This method creates a json representation of the given xml structure. It
    traverses the dom tree and adds elements to the dictionary as it goes.
    '''
    stack.append(element.nodeName)
    LOGGER.debug('Processing %s element.', element.nodeName)
    if (
        element.firstChild and
        element.firstChild.nodeValue and
        len(element.firstChild.nodeValue.strip())
        ):
        put_in_dictionary(dictionary, stack, parse_value(element.firstChild.nodeValue.strip()))
    else:
        # This line might be removed.
        put_in_dictionary(dictionary, stack, {})
    for child in element.childNodes:
        if child.nodeType == dom.Node.ELEMENT_NODE:
            _xml_to_json(child, stack, dictionary)
            stack.pop()

def put_in_dictionary(dictionary, stack, value):
    '''
    This method puts the given value into a tree represented by the dictionary
    the path to the leaf will be retrieved from the stack. If the a leaf is
    missing, a empty dictionary will be inserted in its place.
    '''
    current = dictionary
    for i in range(len(stack) - 1):
        if stack[i] not in current:
            current[stack[i]] = {}
        current = current[stack[i]]
    current[stack[len(stack) - 1]] = value

def parse_value(value):
    '''
    This method tries to identify the value of a given string, if it is in fact
    a string it removes the unnecessary quotes. If value represents a numeric
    object such as an int or a float it parses it into one. If the previous
    tests fail, the value is returned.
    '''
    pattern = r'\"(.*)\"'
    string_matcher = re.compile(pattern)
    if string_matcher.match(value):
        return re.sub(pattern, r'\1', value)
    else:
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                pass
    return value

def _get_attribute(path_to_metadata, dictionary):
    '''
    This method gets an attribute from the given dictionary that represents
    a field in the real world object that is being parsed.
    '''
    if not isinstance(path_to_metadata, list) or len(path_to_metadata) == 0:
        return None
    try:
        local = dictionary
        length = len(path_to_metadata)
        for i in range(length):
            local = local[path_to_metadata[i]]
        return local
    except KeyError:
        return None

class BundleError(Exception):
    '''
    Exception class indicating a problem when trying to parse a bundle.
    '''
    pass

class BaseData(object):
    '''
    Implementers of this class will represent a Data object from the outside
    world. In this case Data can be a raster image.
    '''
    def __init__(self):
        '''
        Constructor
        '''
    def get_output_directory(self):
        '''
        Returns the directory where the image is going to be persisted.
        '''
        raise NotImplementedError('Implementing classes must provide a'
            'method to get the extent of the image.')    
    def _get_footprint(self):
        '''
        Returns the extent of the raster image.
        '''
        raise NotImplementedError('Implementing classes must provide a'
            'method to get the extent of the image.')
    def _footprint_helper(self, ring, spacial_reference):
        '''
        Calculates transformations that are common to raster and shape objects.
        '''
        spatial_reference = osr.SpatialReference()
        spatial_reference.ImportFromEPSG(4326)  # Geo WGS84
        coordinate_transformation = osr.CoordinateTransformation(
            spacial_reference,
            spatial_reference
            )
        footprint = ogr.Geometry(ogr.wkbPolygon)
        footprint.AddGeometry(ring)
        footprint.Transform(coordinate_transformation)
        wkt = WKTElement(footprint.ExportToWkt(), srid=4326)
        return wkt
    def create_from_reference(self, output, width, height, bands, geotransform, projection, data_type=gdal.GDT_Float32, options=[]):
        '''
        This method creates a gdal data file using the width, height and bands
        specified. options could be:
        options = ['COMPRESS=LZW']
        '''
        format_create = 'GTiff'
        driver = gdal.GetDriverByName(str(format_create))
        data = driver.Create(output, width, height, bands, data_type, options)
        data.SetGeoTransform(geotransform)
        data.SetProjection(projection)
        return data
    def create_raster_in_memory(self):
        '''
        Creates a raster in memory
        '''
        format_create = 'MEM'
        driver = gdal.GetDriverByName(str(format_create))
        print 'driver for raster memory'
        print driver
    def write_raster(self, data_file, data_to_write):
        '''
        data_file: data that will have the data in parameter data_to_write
        data_to_write: array
        '''
        if len(data_to_write.shape) > 2:
            bands = data_to_write.shape[0]
            for band in range(bands):
                data_file.GetRasterBand(band + 1).WriteArray(data_to_write[band, :, :])    
        else:
            data_file.GetRasterBand(1).WriteArray(data_to_write)    
    def write_array(self, data_file, data_to_write):
        data_file.GetRasterBand(1).WriteArray(data_to_write)

class BaseSensor(object):
    '''
    Implementers of this class represent a sensor.
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.uuid = str(uuid.uuid4())
        self.format = "not set"
        self.product = "not set"
        self.nodata = -1
        self.parser = None
    def get_attribute(self, path_to_attribute):
        '''
        Returns the attribute found in the given path.
        '''
        return self.parser.get_attribute(path_to_attribute)

class BaseFormat(object):
    '''
    Implementers of this class will represent a data format.
    '''

class ParseError(Exception):
    '''
    Handy exception for any error that happens during the parsing process.
    '''

class BaseParser(object):
    '''
    Helper class to parse meta data from the different providers.
    '''
    def __init__(self, filepath):
        '''
        Constructor
        '''
        self.version = None
        self.filepath = filepath
        self.metadata = None
    def parse(self):
        '''
        The method that starts the parsing process. Depending on the file
        that will be parsed, the implementors should be aware of what things
        are necessary in order to parse the given format.
        '''
        pass
    def get_attribute(self, path_to_metadata):
        '''
        This method is just a decorator for the protected _get_attribute method
        to provide a nice interface to get attributes from each parser.
        Classes extending a BaseParser may want to override the behavior of
        this method to adequate it to their needs.
        '''
        return _get_attribute(path_to_metadata, self.metadata)
    def set_attribute(self, stack, value):
        '''
        Puts the given value in the dictionary, using the list of strings to
        set a path.
        '''
        put_in_dictionary(self.metadata, stack, value)
    def apply_format(self, attribute, formatter):
        '''
        This method looks for the value at the given position and replaces it
        with the result of that value after applying the given formatter.
        '''
        put_in_dictionary(self.metadata, attribute, formatter(self.get_attribute(attribute)))