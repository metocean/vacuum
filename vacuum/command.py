import os
import sys
import argparse
import pprint 
import six
import logging

from .utils import flister, delete, archive, setup_logger
from .scrub import WhaleScrubber

parser = argparse.ArgumentParser()

subparser = parser.add_subparsers(help='Available operations for vacuum command')

parser_list = subparser.add_parser('list', help='List files according with conditions' )
parser_clean = subparser.add_parser('clean', help='Clean up [delete] files')
parser_archive = subparser.add_parser('archive', help='Archive [copy] files and directories')
parser_scrub = subparser.add_parser('scrub', help='Clean up docker images and containers')

recursive_args = []


for sub in [parser_list, parser_clean, parser_archive]:
    sub.add_argument('-r','--recursive', 
                        help='Find files inside sub-folders recursivelly',
                        action='store_true')
    sub.add_argument('-p','--pattern', 
                        help='A RE pattern to search files inside root dir, accept multiple values',
                        action='append',
                        default=None)
    sub.add_argument('-o','--older_than', 
                        help='Find files older than a giving period (i.e. 1h or 2min or 5d)',
                        action='store',
                        default=None)
    sub.add_argument('-d','--max_depth', 
                        help='Max depth to recurse directories after root dirs',
                        action='store',
                        default=1,
                        type=int)
    sub.add_argument('--date_strptime', 
                        help='Date strptime formatting for use as older_than',
                        action='store',
                        default=None,
                        type=str)
    sub.add_argument('--time_strptime', 
                        help='Time strptime formatting for use as older_than',
                        action='store',
                        default=None,
                        type=str)
    sub.add_argument('root', help='Root directory to search files for')

parser_clean.add_argument('-e','--empty', 
                          help='Delete empty folders as well',
                          action='store_true')

for sub in [parser_clean, parser_archive]:
    sub.add_argument('-f','--force', help="Don't prompt for confirmation",
                        action='store_true')

parser_archive.add_argument('-a','--action', 
                            help="Action to be used for archive `move` or `copy`")
parser_archive.add_argument('--root_depth', 
                            help="Preserve directory tree from `root_depth`. Default: 0",
                            default=0)
parser_archive.add_argument('destination', 
                            help='Destination directory to archive [copy] files at')

def _list_files(args=None, filelist=None):
    filelist = filelist or flister(args.root, args.pattern, args.older_than, 
                                   args.recursive, args.max_depth,
                                   date_strptime=args.date_strptime, 
                                   time_strptime=args.time_strptime)
    files = []
    for filepath in filelist:
        print(filepath)
        files.append(filepath)
    return files

def clean_or_archive(operation, args, **opargs):
    logger = setup_logger()
    filelist = flister(args.root, args.pattern, args.older_than, args.recursive, 
                       args.max_depth, 
                       date_strptime=args.date_strptime, 
                       time_strptime=args.time_strptime)
    try: 
        first_file = next(filelist)
    except StopIteration: 
        logger.info('Floor is shining, nothing to clean!')
        return

    message = 'There is some dust to be vacuumed, Power ON? (l/y/N):'
    while True:
        if args.force:
            option = 'Y'
        else:
            option = six.moves.input(message) or 'N'
        if option == 'l':
            _list_files(filelist=[first_file])
            _list_files(filelist=filelist)
        elif option in ['y','Y']:
            files0, dirs0, errors0 = operation([first_file], logger=logger, **opargs)
            files, dirs, errors = operation(filelist, logger=logger, **opargs)
            errors.update(errors0)
            if files:
                logger.info('Successfully vacuum-cleaned %d files and %d directories!' %\
                                                 (len(files+files0),
                                                  len(dirs+dirs0)))
            if errors:
                message = 'Oh no! Some dust still glued to the floor (%d)! Show? (y/N):' % len(errors)
                option = six.moves.input(message) if not args.force else option
                if option in ['y','Y']:
                    logger.error('%s: %s%s' % (message, os.linesep, 
                                 os.linesep.join(['%s: %s' % (k,v) for k,v in errors.items()])))
            break
        elif option in ['n','N']:
            break
        else:
            print('Options available [l]ist, [y]es or [n]o')

parser_scrub.add_argument('target', choices=['images', 'containers'])
parser_scrub.add_argument('-i','--ignore', help="Names RE patterns to ignore",
                          action='append')
parser_scrub.add_argument('--filter', help="Add filter values for image/containers",
                          action='append')
parser_scrub.add_argument('-f','--force', help="Force removal of images or containers",
                          action='store_true')

def _scrub(args):
    logger = setup_logger()
    config = {
            'ignore': args.ignore or [],
            'filters': [dict(v.split('=') for v in args.filter)] if args.filter else {},
            'force' : args.force,
        }
    scrubber = WhaleScrubber(logger=logger)
    if args.target == 'images':
        scrubber.images = config
    elif args.target == 'containers':
        scrubber.containers = config
    scrubber.run()

def _clean(args):
    clean_or_archive(delete, args, delete_empty=args.empty)

def _archive(args):
    clean_or_archive(archive, args, root_depth=args.root_depth, 
                                    destination=args.destination,
                                    action=args.action)

parser_list.set_defaults(func=_list_files)
parser_clean.set_defaults(func=_clean)
parser_archive.set_defaults(func=_archive)
parser_scrub.set_defaults(func=_scrub)

if __name__ == "__main__":
    args = parser.parse_args()
    args.func(args)