'''
Created on Jun 23, 2017

@author: agutierrez
'''
from __future__ import unicode_literals

import logging

from flood.persistence.database.connection import Scene
from flood.persistence.database.connection import SESSION_MAKER
import flood.persistence.database.operations as database
import flood.persistence.filesystem.operations as filesystem
from flood.util import create_directory_path


LOGGER = logging.getLogger(__name__)

def persist_data(bundle, keep=False):
    '''
    This function persist a bundle in both the database and the file system. It
    is responsibility of the bundle to provide information about which files
    should be persisted in the file system, and to build the database object
    that will be inserted in the database. The database is configured using the
    session maker in the connection module.
    In order to achieve its purpose, this method creates a list of the actions
    to perform. Once the list is fully populated, it calls the act method for
    each element in the list. If any of the actions in the list fails, a
    rollback is performed in all of them, the result is the same state as before
    the method was called.
    '''
    destination = bundle.get_output_directory()
    create_directory_path(destination)
    actions = []
    session = SESSION_MAKER()
    try:
        if not session.query(Scene).filter(Scene.name == bundle.get_database_object().name).count():
            if not keep:
                LOGGER.debug('This process will move the files to a new destination.')
                for file_name in bundle.get_files():
                    actions.append(filesystem.InsertAction(file_name, destination))
            else:
                LOGGER.debug('This process will keep the original path for the files.')
            actions.append(database.InsertAction(
                bundle.get_database_object(),
                session)
                )
            def do_result(action):
                '''
                Lambda function to perform an action and return the result.
                '''
                action.act()
                return action.success
            if not reduce(lambda x, y: x and y, map(do_result, actions)):
                LOGGER.debug('Some action went wrong at persistence process, '
                    'rollback will be performed.')
                for action in actions:
                    action.undo()
            else:
                LOGGER.info('Ingestion was successful.')
        else:
            LOGGER.info('An instance of this object already exist in the database.')
    except Exception:
        LOGGER.error('Not expected error at persistence.driver')
        raise
    finally:
        session.close()

def ingest_sample(sample):
    session = SESSION_MAKER()
    my_action = database.InsertAction(
                                      sample.get_database_object(),
                                      session)
    my_action.act()

def update_sample(name, value):
    session = SESSION_MAKER()
    query = "UPDATE sample SET water = %s WHERE sample.name = '%s';" % (value, name)
    print query
    try:
        result = session.execute(query)
        session.commit()
    except Exception:
        LOGGER.error('Not expected error in host insertion.')
        raise
    finally:
        session.close()
    return result

def get_random_scene():
    session = SESSION_MAKER()
    query = 'SELECT * FROM scene ORDER BY RANDOM() LIMIT 1'
    try:
        result = session.execute(query)
    except Exception:
        LOGGER.error('Not expected error in host insertion.')
        raise
    finally:
        session.close()
    return result

def get_scene_paths(water, limit=100):
    session = SESSION_MAKER()
    query = 'SELECT * FROM sample WHERE water=%s LIMIT %s;' % (water, limit)
    try:
        result = session.execute(query)
    except Exception:
        LOGGER.error('Not expected error in host insertion.')
        raise
    finally:
        session.close()
    return result



