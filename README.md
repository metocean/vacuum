# vacuum

![](https://github.com/metocean/ops-core/workflows/unittests/badge.svg)

Python library to handle deleting and archive of files and cleanup of dockers containers and images.


Configuration example for VaccumCleaner:

```yaml
relative_to: runtime # older_than relative to "cycle" or to "runtime" (option "cycle" is default)
stop_on_error: True # make process stop if any unexpected error is encountered (default: False)
delete_empty: False # don't delete empty folders (default: true)
dry_run: True # Only list files target to be vacuumed
archive:
    some_archive_rule_name:
        rootdir: /data/roms/*/* # <--- directory glob matching pattern
        destination: /archive # destination root directory to archive
        root_depth: 2 # preserve directory tree after root_depth level. (Default: 0 - preserve all tree)
        older_than: 60d
        action: move # Delete source file once has copied to destination, default is 'copy'
        date_strptime: %Y%m%d
        time_strptime: %Hz
        recursive: True
        max_depth: 2 # Set max recursion depth for rule (default: -1 (infinite))
        patterns: # <- RE filters to include
            - .+\.txt # same as *.txt in shell

clean:
    some_rule_name:
        rootdir: /data # <--- directory glob matching pattern
        older_than: 60d
        delete_empty: false # Do not delete empty folders for this rule
        date_strptime: %Y%m%d
        time_strptime: %Hz
        recursive: True
        patterns: # <- RE filters to include
            - .+\.txt

    some_other_rule:
        rootdir: '/data/roms/*'
        recursive: True
        patterns:
            - '\.nc$'

```

Example using WhaleScruber:

```yaml
scrub:
    images:  
        ignore: # Accept list of image names or matching RE
            - !!python/object/apply:scheduler.core.get_active_images [] # A function that generates a list of image names
            - user/.+  # All images from user
            - metocean/some_image:1.1.1
        force: True # False (default) will only remove images with no container associated with
        filters: # filters for https://docker-py.readthedocs.io/en/stable/images.html#docker.models.images.ImageCollection.list
            - name: 'user/repo:tag' # filter all tags for this related repository name or specify tag
              dangling: true # This will only clean dangling images 
    containers:
        ignore: # sames images:ignore but containers names instead
            - conteiner1
        force: True # SIGKILL for running containers
        filters: # https://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.list
            - name: dedicated
              status: exited
              older_than: 2m # created more than 2 months ago

            -  name: container_b
```