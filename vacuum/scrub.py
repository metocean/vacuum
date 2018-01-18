# Placeholder for docker cleaning operations
import docker
import logging
import six
import re
import datetime

from .utils import older_then, pastdt

class WhaleScrubber(object):
    """
    Perform cleaning operations of images and containers
    """
    def __init__(self, images={}, containers={}, client=None, logger=logging):
        super(WhaleScrubber, self).__init__()
        self.client = client or docker.from_env()
        self.logger = logger
        self.images = images
        self.containers = containers

    def _listify_ignore(self, ignore):
        ignores = set()
        for i in ignore:
            if not isinstance(i, (list,tuple)):
                i = [i]
            ignores.update(set(i))
        return list(ignores)

    def _not_matches_ignores(self, ignores, names):
        if not isinstance(names, (list,tuple)):
            names = [names]
        not_matches = True
        for ignore in ignores:
            reignore = re.compile(ignore)
            for name in names:
                if reignore.match(name):
                    return False
        return not_matches

    def _maybe_remove_image(self, image, force, ignores=[]):
        tag = ','.join(image.tags) or image.id
        try:
            if self._not_matches_ignores(ignores, image.tags):
                self.logger.debug('Scrubbing image (%s)...' % tag)
                self.client.images.remove(image.id, force=force)
                self.logger.info('Ahoy! Image scrubbed: (%s)' % tag)
        except docker.errors.APIError as exc:
            self.logger.warning('Arrgh! Sticky image (%s): %s' %\
                                             (tag,exc.explanation))

    def _maybe_remove_container(self, container, force, ignores=[]):
        try:
            if self._not_matches_ignores(ignores, container.name):
                self.logger.debug('Scrubbing (%s) container ...' % container.name)
                container.remove(force=force)
                self.logger.info('Ahoy! Container scrubbed: (%s)' % container.name)
        except docker.errors.APIError as exc:
            self.logger.warning('Arrgh! Sticky container (%s): %s' %\
                                         (container.name, exc.explanation))

    def _created_before_then(self, containers, older_then):
        older_containers = []
        then = pastdt(older_then, utc=True)
        for container in containers:
            created_at = container.attrs['Created'].split('.')[0]
            created_at = datetime.datetime.strptime(created_at,
                                                 "%Y-%m-%dT%H:%M:%S")
            if created_at < then:
                older_containers.append(container)
        return older_containers

    def _clean_images(self, ignore=[], filters=[], force=False):
        ignores = self._listify_ignore(ignore)
        images = []
        if not filters:
            images.extend(self.client.images.list())
        else:
            for ifilter in filters:
                name = ifilter.pop('name', None)
                images.extend(self.client.images.list(name=name, filters=ifilter))

        if images:
            self.logger.info('Scrubbing images...')
        else:
            self.logger.info('Blimey! No fouling images to scrub for the giving filters.')

        for image in images:
            self._maybe_remove_image(image, force, ignores)

    def _clean_containers(self, ignore=[], filters=[], force=False):
        ignores = self._listify_ignore(ignore)
        containers = []
        if not filters:
            containers.extend(self.client.containers.list(all=True))
        else:
            for ifilter in filters:
                older_then = ifilter.pop('older_then', None)
                filtered = self.client.containers.list(all=True, 
                                                          filters=ifilter)
                if older_then:
                    filtered = self._created_before_then(filtered, older_then)
                containers.extend(filtered)
        if containers:
            self.logger.info('Scrubbing containers...')
        else:
            self.logger.info('Blimey! No fouling containers to scrub for the giving filters.')

        for container in containers:
            self._maybe_remove_container(container, force, ignores)
    
    def run(self):
        if self.containers:
            self._clean_containers(**self.containers)
        if self.images:
            self._clean_images(**self.images)
