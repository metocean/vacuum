import os
import unittest
import mock
import logging
import tempfile
import shutil
import pytest
import time
from datetime import datetime,timedelta
from os.path import *

import docker

from ..cleaner import VacuumCleaner
from ..utils import pastdt


def set_mtime(filename, mtime):
    """
    Set the modification time of a given filename to the given mtime.
    mtime must be a datetime object.
    """
    timestamp = time.mktime(mtime.timetuple()) + mtime.microsecond/1e6
    os.utime(filename, (os.stat(filename).st_atime, timestamp))

def create_files(nfiles=5, **kwargs):
    return [tempfile.mkstemp(**kwargs)[1] for f in range(nfiles)]

class VacuumCleanerCleanTest(unittest.TestCase):
    def setUp(self):
        self.vacuum = VacuumCleaner()
        self.rootdir = tempfile.mkdtemp()
        self.files = create_files(dir=self.rootdir)

    def tearDown(self):
        if exists(self.rootdir):
            shutil.rmtree(self.rootdir)

    def test_instance(self):
        assert isinstance(self.vacuum, VacuumCleaner)

    def test_dry_run_on_clean(self):
        self.vacuum.dry_run = True
        self.vacuum.clean = [dict(rootdir=self.rootdir)]
        self.vacuum.run()
        assert all([exists(f) for f in self.files])

    def test_clean(self):
        self.vacuum.clean = [dict(rootdir=self.rootdir)]
        self.vacuum.run()
        assert not all([exists(f) for f in self.files])

    def test_clean_with_cycle(self):
        cycle = datetime(2000,1,1)
        [set_mtime(f, cycle-timedelta(days=1)) for f in self.files[1:]]
        set_mtime(self.files[0], cycle+timedelta(days=1))
        self.vacuum.relative_to = 'cycle'
        self.vacuum.set_cycle(cycle)
        self.vacuum.clean = [dict(rootdir=self.rootdir, older_than=0)]
        self.vacuum.run()
        assert sum([exists(f) for f in self.files]) == 1
        assert sum([not exists(f) for f in self.files]) == 4

    def test_clean_with_cycle_but_relative_to_runtime(self):
        self.vacuum.relative_to = 'runtime'
        self.vacuum.set_cycle(datetime(3000,1,1))
        [set_mtime(f, self.vacuum.now-timedelta(days=1)) for f in self.files[1:]]
        set_mtime(self.files[0], self.vacuum.now+timedelta(days=1))
        self.vacuum.clean = [dict(rootdir=self.rootdir, older_than=0)]
        self.vacuum.run()
        assert sum([exists(f) for f in self.files]) == 1
        assert sum([not exists(f) for f in self.files]) == 4

    def test_clean_relative_to_runtime(self):
        self.vacuum.relative_to = 'runtime'
        [set_mtime(f, self.vacuum.now-timedelta(days=1)) for f in self.files[1:]]
        set_mtime(self.files[0], self.vacuum.now+timedelta(days=1))
        self.vacuum.clean = [dict(rootdir=self.rootdir, older_than=0)]
        self.vacuum.run()
        assert sum([exists(f) for f in self.files]) == 1
        assert sum([not exists(f) for f in self.files]) == 4

    @mock.patch('os.remove', side_effect=OSError('Not permitted'))
    def test_clean_with_errors_dont_stop(self, remove):
        self.vacuum.clean = [dict(rootdir=self.rootdir)]
        self.vacuum.run()
        assert all([exists(f) for f in self.files])

    @mock.patch('os.remove', side_effect=OSError('Not permitted'))
    def test_clean_with_errors_stop(self, remove):
        self.vacuum.clean = [dict(rootdir=self.rootdir, raise_errors=True)]
        with pytest.raises(Exception):
            self.vacuum.run()

    @mock.patch('os.remove', side_effect=OSError('Not permitted'))
    def test_clean_with_errors_stop_general_rule(self, remove):
        self.vacuum.stop_on_error = True
        self.vacuum.clean = [dict(rootdir=self.rootdir)]
        with pytest.raises(Exception):
            self.vacuum.run()

class VacuumCleanerArchiveTest(unittest.TestCase):
    def setUp(self):
        self.vacuum = VacuumCleaner()
        self.rootdir = tempfile.mkdtemp()
        self.destination = tempfile.mkdtemp()
        self.rootdir = tempfile.mkdtemp()
        self.files = create_files(dir=self.rootdir)

    def tearDown(self):
        if exists(self.rootdir):
            shutil.rmtree(self.rootdir)
        if exists(self.destination):            
            shutil.rmtree(self.destination)

    def test_archive_copy(self):
        self.vacuum.archive = [{
            'destination' : self.destination,
            'action': 'copy',
            'rootdir': self.rootdir,
        }]
        self.vacuum.run()
        assert os.listdir(self.rootdir)
        assert os.listdir(self.destination)

    def test_archive_move(self):
        self.vacuum.delete_empty = False
        self.vacuum.archive = [{
            'destination' : self.destination,
            'rootdir': self.rootdir,
            'action': 'move',
        }]
        self.vacuum.run()
        assert not os.listdir(self.rootdir)
        assert os.listdir(self.destination)

    def test_archive_links(self):
        tmpfile = self.files[0]
        self.vacuum.archive = [{
            'destination' : self.destination,
            'rootdir': self.rootdir,
            'action': 'copy',
            'patterns': ['.+'],
            'raise_errors': True,
        }]
        os.symlink(basename(tmpfile), tmpfile+'.link')
        self.vacuum.run()
        assert os.listdir(self.destination)
        dst = join(self.destination, basename(tmpfile))
        assert islink(dst+'.link')
        assert os.readlink(dst+'.link') == basename(tmpfile)
        assert isfile(dst)

    def test_archive_overwites_on_existing(self):
        tmpfile = self.files[0]
        shutil.copy2(tmpfile, self.destination)
        with open(tmpfile, 'w') as of:
            of.write('oi')
        self.vacuum.archive = [{
            'destination' : self.destination,
            'rootdir': self.rootdir,
            'action': 'copy',
            'patterns': ['.+'],
        }]
        self.vacuum.run()
        basename = os.path.basename(tmpfile)
        assert open(os.path.join(self.destination, basename)).read() == open(tmpfile).read()

    @mock.patch('shutil.copy2', side_effect=OSError('Not permitted'))
    def test_archive_with_errors(self, move):
        self.vacuum.archive = [{
            'destination' : self.destination,
            'rootdir': self.rootdir,
            'action' : 'copy',
            'patterns': ['.+'],
        }]
        self.vacuum.run()
        assert not os.listdir(self.destination)
        assert os.listdir(self.rootdir)
        
