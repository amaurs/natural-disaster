'''
Created on Jun 23, 2017

@author: agutierrez
'''

from __future__ import unicode_literals

import logging

from flood.core.controller.base import BaseCommand
from flood.web.app import run

LOGGER = logging.getLogger(__name__)

class Command(BaseCommand):
    def handle(self, **options):
        run()