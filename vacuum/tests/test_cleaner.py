import os
import unittest
import mock
import logging
import tempfile
import shutil
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

    def test_archive(self):
        tmpfile = tempfile.mkstemp(dir=self.rootdir)
        self.vacuum.archive = [{
            'destination' : self.destination,
            'rootdir': self.rootdir,
            'patterns': ['.+'],
        }]
        self.vacuum.run()
        assert os.listdir(self.destination)

    @mock.patch('shutil.move', side_effect=OSError('Not permitted'))
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
        