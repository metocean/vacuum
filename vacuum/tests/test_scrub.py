import unittest
import mock
import logging
import docker
import datetime

from ..scrub import WhaleScrubber
from ..utils import pastdt

class TestWhaleScrubber(unittest.TestCase):

    def setUp(self):
        self.scrubber = WhaleScrubber()
    
    def test_instance_scrubber(self):
        assert self.scrubber.client

    def test_listfy_ignores(self):
        ignore = ['example1', 'example2', ['example3', 'example4']]
        ignores = self.scrubber._listify_ignore(ignore)
        assert len(ignores) == 4

    def test_not_matches_ignores_re(self):
        ignores = ['test/scrub', 'example.+', 'dedicated']
        not_matchers = ['notmatcher', 'surenotmatch'] 
        matchers = ['test/scrub:willmatch', 'example_match', 'dedicated.31nzx33t42ga']

        for name in not_matchers:
            assert self.scrubber._not_matches_ignores(ignores, name)

        for name in matchers:
            assert not self.scrubber._not_matches_ignores(ignores, name)

    def test_remove_container(self):
        container = mock.MagicMock()
        container.remove.return_value = 'OK'
        self.scrubber._maybe_remove_container(container, False)
        container.remove.assert_called()

    def test_remove_container_error(self):
        self.scrubber.logger = mock.MagicMock()
        container = mock.MagicMock()
        container.remove.side_effect = docker.errors.APIError('Not found')
        self.scrubber._maybe_remove_container(container, False)
        container.remove.assert_called()
        self.scrubber.logger.warning.assert_called()
        self.scrubber.logger = logging

    @mock.patch('docker.client.ImageCollection')
    def test_remove_image(self, images_class):
        image = mock.MagicMock()
        image.tags = ['test/image:version']
        image.id = 'blablabla'
        images = mock.MagicMock()
        images_class.return_value = images
        images.remove.return_value = mock.MagicMock()
        self.scrubber._maybe_remove_image(image, False)
        images.remove.assert_called_with(image.id, force=False)

    def test_containers_older_than(self):
        container1 = mock.MagicMock()
        container2 = mock.MagicMock()
        container1.attrs = {'Created': pastdt('10d',utc=True).isoformat()}
        container2.attrs = {'Created': pastdt('20d',utc=True).isoformat()}
        containers = [container1, container2]
        result = self.scrubber._created_before_than(containers, '9d')
        assert result == [container1, container2]
        result = self.scrubber._created_before_than(containers, '15d')
        assert result == [container2]
        result = self.scrubber._created_before_than(containers, '21d')
        assert result == []

    def test_containers_older_than_with_cycle(self):
        self.scrubber.relative_to = 'cycle'
        self.scrubber.set_cycle(datetime.datetime.now())
        container1 = mock.MagicMock()
        container2 = mock.MagicMock()
        container1.attrs = {'Created': pastdt('10d',utc=True).isoformat()}
        container2.attrs = {'Created': pastdt('20d',utc=True).isoformat()}
        containers = [container1, container2]
        result = self.scrubber._created_before_than(containers, '9d')
        assert result == [container1, container2]
        result = self.scrubber._created_before_than(containers, '15d')
        assert result == [container2]
        result = self.scrubber._created_before_than(containers, '21d')
        assert result == []

    @mock.patch('docker.client.ContainerCollection')
    def test_clean_containers_without_filters(self, containers_class):
        containers = mock.MagicMock()
        containers_class.return_value = containers
        self.scrubber._clean_containers() 
        containers.list.assert_called_with(all=True)

    @mock.patch('docker.client.ContainerCollection')
    def test_clean_containers_with_filters(self, containers_class):
        containers = mock.MagicMock()
        containers_class.return_value = containers
        filters = [{'name':'bla'}]
        self.scrubber._clean_containers(filters=filters) 
        containers.list.assert_called_with(all=True, filters=filters[0])

    
    @mock.patch('docker.client.ContainerCollection')
    def test_clean_containers_with_older_than_filters(self, containers_class):
        containers = mock.MagicMock()
        containers_class.return_value = containers
        container1 = mock.MagicMock()
        container2 = mock.MagicMock()
        container1.name = 'magic_leap'
        container1.name = 'magic_leap2' 
        container1.attrs = {'Created': pastdt('10d',utc=True).isoformat()}
        container2.attrs = {'Created': pastdt('20d',utc=True).isoformat()}
        containers.list.return_value = [container1, container2]
        filters = [{'older_than':'15d'}]
        self.scrubber._clean_containers(filters=filters) 
        containers.list.assert_called_with(all=True, filters={})
        container2.remove.assert_called()
        container1.remove.assert_not_called()

    @mock.patch('docker.client.ImageCollection')
    def test_clean_images_without_filters(self, images_class):
        images = mock.MagicMock()
        images_class.return_value = images
        self.scrubber._clean_images() 
        images.list.assert_called_with()

    @mock.patch('docker.client.ImageCollection')
    def test_clean_images_with_filters(self, images_class):
        images = mock.MagicMock()
        images_class.return_value = images
        filters = [{'name':'bla'}]
        self.scrubber._clean_images(filters=filters) 
        images.list.assert_called_with(name='bla', filters={})