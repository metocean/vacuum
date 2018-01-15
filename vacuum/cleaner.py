# execute cleanup operations 
import os
import shutil

import logging


class VacuumBase(object):
    """docstring for VacuumBase"""
    def __init__(self, logger=logging):
        super(VacuumBase, self).__init__()
        self.logger = logger  

    def run(self):
        pass
        


class VaccumCleaner(object):
    """docstring for VaccumCleaner"""
    def __init__(self, arg):
        super(VaccumCleaner, self).__init__()
    

    def _delete(self, filelist):
        pass

    def run()


