# execute cleanup operations 
import os
import shutil

import logging
import datetime

from .utils import archive, delete, flister

class VacuumCleaner(object):
    """Wrapper to perform cleaning/archive operations"""
    def __init__(self, clean=None, archive=None, 
                 dry_run=False,
                 delete_empty=True,
                 relative_to='cycle',
                 stop_on_error=False,
                 logger=logging, **kwargs):
        super(VacuumCleaner, self).__init__()
        self.clean = clean
        self.archive = archive
        self.dry_run = dry_run
        self.delete_empty = delete_empty
        self.relative_to = relative_to
        self.stop_on_error = stop_on_error
        self.logger = logger
        self.now = datetime.datetime.utcnow()

    def set_cycle(self, cycle_dt):
        if not self.relative_to == 'runtime':
            self.now = cycle_dt

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
        self.logger.info('Processing all "%s" operations...' % operation)
        for rule_id, options in rules:
            options['delete_empty'] = options.get('delete_empty', self.delete_empty)
            options['raise_errors'] = options.get('raise_errors', self.stop_on_error)
            self.logger.info('Processing "%s" for "%s"...'% (operation.__name__, 
                                                          rule_id))
            filelist = flister(now=self.now, **options)
            if self.dry_run:
                self.logger.info('Below files would be %sed: %s%s' %\
                             (operation, os.linesep, os.linesep.join(filelist)))
                
            else:
                success_files, success_dirs, errors = operation(filelist, **options)
                self.logger.info('%s of %s complete: %d files and %d directories %sd' %\
                    (operation.__name__.title(),rule_id,len(success_files),len(success_dirs),operation.__name__))
                if errors:
                    self.logger.warning('Could not %s some files, please check below...' % \
                                                                operation.__name__\
                                                                +os.linesep+'%s'%\
                            os.linesep.join(['%s: %s' % i for i in errors.items()]))

    def run(self):
        self.logger.info('Powering vacuum cleaner...')
        self.logger.info('Older-than will be relative to (%s) %s' %\
                                                 (self.relative_to, self.now))
        if self.archive:
            self._archive_or_clean(archive, self.archive)

        if self.clean:
            self._archive_or_clean(delete, self.clean)
        
