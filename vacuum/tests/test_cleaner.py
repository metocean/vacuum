import os
import unittest
import mock
import logging
import tempfile
import shutil
import datetime
from os.path import *

import docker

from ..cleaner import VacuumCleaner
from ..utils import pastdt


class VacuumCleanerCleanTest(unittest.TestCase):
    def setUp(self):
        self.vacuum = VacuumCleaner()
        self.rootdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.rootdir)

    def test_instance(self):
        assert isinstance(self.vacuum, VacuumCleaner)

    def test_clean(self):
        files = []
        for i in range(5):
            tmpfile = tempfile.NamedTemporaryFile(dir=self.rootdir,
                                                  suffix='test_clean')
            tmpfile.file.close()
            files.append(tmpfile.name)
            assert exists(tmpfile.name)
        self.vacuum.clean = [{
            'rootdir': self.rootdir,
            'patterns': ['test_clean'],
        }]
        self.vacuum.run()
        assert not all([exists(f) for f in files])

    def test_clean_with_cycle(self):
        self.vacuum.relative_to = 'cycle'
        self.vacuum.set_cycle(datetime.datetime.now())
        files = []
        for i in range(5):
            tmpfile = tempfile.NamedTemporaryFile(dir=self.rootdir,
                                                  suffix='test_clean')
            tmpfile.file.close()
            files.append(tmpfile.name)
            assert exists(tmpfile.name)
        self.vacuum.clean = [{
            'rootdir': self.rootdir,
            'older_than': '0s',
            'patterns': ['test_clean'],
        }]
        self.vacuum.run()
        assert not all([exists(f) for f in files])

    @mock.patch('os.remove', side_effect=OSError('Not permitted'))
    def test_clean_with_errors(self, remove):
        files = []
        tmpfile = tempfile.NamedTemporaryFile(dir=self.rootdir,
                                              suffix='test_clean')
        tmpfile.file.close()

        files.append(tmpfile.name)
        self.vacuum.clean = [{
            'rootdir': self.rootdir,
            'patterns': ['test_clean'],
        }]
        self.vacuum.run()
        assert all([exists(f) for f in files])


class VacuumCleanerArchiveTest(unittest.TestCase):
    def setUp(self):
        self.vacuum = VacuumCleaner()
        self.rootdir = tempfile.mkdtemp()
        self.destination = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.rootdir)
        shutil.rmtree(self.destination)

    def test_archive_simple(self):
        tmpfile = tempfile.NamedTemporaryFile(dir=self.rootdir, delete=False)
        tmpfile.close()
        self.vacuum.archive = [{
            'destination' : self.destination,
            'rootdir': self.rootdir,
            'patterns': ['.+'],
            'raise_errors': True,
        }]
        self.vacuum.run()
        assert os.listdir(self.destination)

    def test_archive_move(self):
        tmpfile = tempfile.NamedTemporaryFile(dir=self.rootdir, delete=False)
        tmpfile.close()
        self.vacuum.archive = [{
            'destination' : self.destination,
            'rootdir': self.rootdir,
            'patterns': ['.+'],
            'raise_errors': True,
            'action': 'move',
        }]
        self.vacuum.run()
        assert not os.listdir(self.rootdir)
        assert os.listdir(self.destination)

    def test_archive_overwites_on_existing(self):
        _, tmpfile = tempfile.mkstemp(dir=self.rootdir)
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
        tmpfile = tempfile.mkstemp(dir=self.rootdir)
        self.vacuum.archive = [{
            'destination' : self.destination,
            'rootdir': self.rootdir,
            'patterns': ['.+'],
        }]
        self.vacuum.run()
        assert not os.listdir(self.destination)
        assert os.listdir(self.rootdir)
        