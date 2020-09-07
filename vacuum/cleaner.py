# execute cleanup operations 
import os
import shutil

import logging

from .utils import *

class VacuumCleaner(object):
    """Wrapper to perform cleaning/archive operations"""
    def __init__(self, clean=None, archive=None, logger=logging, **kwargs):
        super(VacuumCleaner, self).__init__()
        self.clean = clean
        self.archive = archive
        self.logger = logger

    def _prepare_rules(self, rules):
        if isinstance(rules, (list,tuple)):
            return enumerate(rules)
        elif isinstance(rules, dict):
            if 'rootdir' in rules:
                return [('single', rules)]
            else:
                return rules.items()
        else:
            raise Exception('Archive and Cleaning rules must a dict or list of rules')

    def _archive_or_clean(self, operation, rules):
        rules = self._prepare_rules(rules)
        for rule_id, options in rules:
            self.logger.info('Processing %s of %s rule'% (operation.__name__, 
                                                          rule_id))
            filelist = flister(**options)
            success_files, success_dirs, errors = operation(filelist, **options)
            self.logger.info('%s of %s complete: %d files and %d directories %sd' %\
                (operation.__name__.title(),rule_id,len(success_files),len(success_dirs),operation.__name__))
            if errors:
                self.logger.warning('Could not %s some files, please check below...' % \
                                                            operation.__name__\
                                                            +os.linesep+'%s'%\
                        os.linesep.join(['%s: %s' % i for i in errors.items()]))

    def run(self):
        if self.archive:
            self._archive_or_clean(archive, self.archive)

        if self.clean:
            self._archive_or_clean(delete, self.clean)
        
