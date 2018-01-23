# execute cleanup operations 
import os
import shutil

import logging

from .utils import *

class VaccumCleaner(object):
    """Wrapper to perform cleaning/archive operations"""
    def __init__(self, clean=None, archive=None, logger=logging):
        super(VaccumCleaner, self).__init__()
        self.clean = clean
        self.archive = archive

    def _clean(self):
        if isinstance(self.clean, (list,tuple)):
            rules = enumerate(self.clean)
        elif isinstance(self.clean, dict):
            rules = self.clean.items()
        else:
            self.logging.info('There is no cleaning rules to be applied')
            return

        for rule_id, options in rules:
            self.logger.info('Processing cleanup of %s rule'%rule_id)
            filelist = flister(**options)
            success_files, success_dirs, errors = delete(filelist, **options)
            self.logger.info('Cleanup of %s complete: %d files and %d directories deleted' %\
                                        (len(success_files),len(success_dirs)))
            if self.errors:
                self.logger.warning('Could not delete some files, please check below...'+os.linesep+'%s'%
                    os.linesep.join(['%s: %s' % i for i in errors.items()])

    def _archive(self):
        pass

    def run(self):
        if self.archive:
            self._archive()

        if self.clean:
            self._clean()
        
