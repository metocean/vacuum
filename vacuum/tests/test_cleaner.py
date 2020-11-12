import os
import unittest
import mock
import logging
import tempfile
import shutil
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
    stat = os.stat(filename)
    atime = stat.st_atime
    os.utime(filename, times=(atime, mtime.timestamp()))

def create_files(nfiles=5, **kwargs):
    return [tempfile.mkstemp(**kwargs)[1] for f in range(nfiles)]

class VacuumCleanerCleanTest(unittest.TestCase):
    def setUp(self):
        self.vacuum = VacuumCleaner()
        self.rootdir = tempfile.mkdtemp()
        self.files = create_files(dir=self.rootdir)

    def tearDown(self):
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
    def test_clean_with_errors(self, remove):
        self.vacuum.clean = [dict(rootdir=self.rootdir)]
        self.vacuum.run()
        assert all([exists(f) for f in self.files])

class VacuumCleanerArchiveTest(unittest.TestCase):
    def setUp(self):
        self.vacuum = VacuumCleaner()
        self.rootdir = tempfile.mkdtemp()
        self.destination = tempfile.mkdtemp()
        self.rootdir = tempfile.mkdtemp()
        self.files = create_files(dir=self.rootdir)

    def tearDown(self):
        shutil.rmtree(self.rootdir)
        shutil.rmtree(self.destination)

    def test_archive_copy(self):
        self.vacuum.archive = [{
            'destination' : self.destination,
            'rootdir': self.rootdir,
        }]
        self.vacuum.run()
        assert os.listdir(self.rootdir)
        assert os.listdir(self.destination)

    def test_archive_move(self):
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
            'patterns': ['.+'],
        }]
        self.vacuum.run()
        assert not os.listdir(self.destination)
        assert os.listdir(self.rootdir)
        
