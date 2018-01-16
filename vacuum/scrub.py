# Placeholder for docker cleaning operations
import docker
import logging
import six

class WhaleScrubber(object):
    """
    Perform cleaning operations of images and containers
    """
    def __init__(self, images={}, containers={}, client=None, logger=logging):
        super(WhaleScrubber, self).__init__()
        self.client = client or docker.from_env()
        self.logger = logger
        self.images = images
        self.containers = container

    def _maybe_remove_image(self, image, force, ignores=[]):
        try:
            remove = True    
            for tag in image.tags:
                if tag in ignores:
                    remove = False
                    break
            if remove:
                self.client.images.remove(image.id, force=force)
        except docker.APIError as exc:
            self.logger.warning('Image not deleted: %s' % exc.explanation)

    def _clean_images(self, ignore=[], filters=[], force=False):
        ignores = set()
        for i in ignore:
            if not isinstance(i, list,tuple):
                i = [i]
            ignores.update(set(i))
        images = []
        if not filters:
            images.extend(self.client.images.list())
        else:
            for ifilter in filters:
                name = ifilter.pop('name', None)
                images.exend(self.client.images.list(name=name, filters=ifilter))
        for image in images:
            self._maybe_remove_image(image, force, ignores)
                    

    def _clean_containers(self, all_containers, ):
        pass
        
    def scrub(self):
        if self.containers:
            self._clean_containers(**self.containers)
        if self.images:
            self._clean_images(**self.images)
