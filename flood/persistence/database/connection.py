'''
Created on Jun 4, 2015

@author: agutierrez
'''
from __future__ import unicode_literals

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.sqltypes import Boolean

from flood.configuration import SETTINGS

BASE = declarative_base()

ENGINE = create_engine(getattr(SETTINGS, 'FLOOD_DATABASE'))

SESSION_MAKER = sessionmaker(ENGINE)

class Scene(BASE):
    '''
    This table stands for companies or organizations that are somewhat related
    to the system. Imagery providers, satellite developers, government
    organizations all fit in this category.
    '''
    __tablename__ = 'scene'
    pk_id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    width = Column(Integer)
    height = Column(Integer)
    year = Column(Integer)
    path = Column(String)
    url = Column(String)
    
class Sample(BASE):
    '''
    Satellites are the actual hardware that takes images. A satellite is
    equipped with a sensor, so we have a foreign key pointing to the Sensor
    table. The reason that we have two tables instead of one, is that several
    satellites can have the same sensor installed. The canonical example for
    this is the RapidEye mission that has five satellites equipped with the
    same sensor.
    '''
    __tablename__ = 'sample'
    pk_id = Column(Integer, primary_key=True)
    x = Column(Integer)
    y = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    water = Column(Boolean)
    scene_id = Column(Integer, ForeignKey('scene.pk_id'))
    scene = relationship('Scene')

def create_database():
    '''
    #This method creates the database model in the database engine.
    '''
    BASE.metadata.create_all(ENGINE)
def delete_database():
    '''
    #This method deletes the database model in the database engine.
    '''
    BASE.metadata.drop_all(ENGINE)
