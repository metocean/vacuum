import os
import argparse
import pprint 
import six

from .utils import flister, delete

parser = argparse.ArgumentParser()

subparser = parser.add_subparsers(help='Available opertions for vaccum')

parser_list = subparser.add_parser('list', help='List files according with conditions' )
parser_clean = subparser.add_parser('clean', help='Clean up files')
parser_scrub = subparser.add_parser('scrub', help='Clean up docker images and containers')
parser_archive = subparser.add_parser('archive', help='Archive files and directories')

recursive_args = []


for sub in [parser_list, parser_clean]:
    sub.add_argument('-r','--recursive', 
                        help='Find files inside sub-folders recursivelly',
                        action='store_true')
    sub.add_argument('-p','--pattern', 
                        help='A RE pattern to search files inside root dir, accept multiple values',
                        action='append',
                        default=None)
    sub.add_argument('-o','--older_then', 
                        help='Find files older then a giving period (i.e. 1h or 2min or 5d)',
                        action='store',
                        default=None)
    sub.add_argument('-d','--max_depth', 
                        help='Max depth to recurse directories after root dirs',
                        action='store',
                        default=1,
                        type=int)
    sub.add_argument('root', help='Root directory to search files for')

parser_clean.add_argument('-f','--force', help="Don't prompt for confirmation",
                        action='store_true')

def list_files(args=None, filelist=None):
    filelist = filelist or flister(args.root, args.pattern, args.older_then, args.recursive, 
                                   args.max_depth)
    files = []
    for filepath in filelist:
        print(filepath)
        files.append(filepath)
    return files

def clean(args):
    filelist = flister(args.root, args.pattern, args.older_then, args.recursive, 
                       args.max_depth)
    try: 
        first_file = filelist.next()
    except StopIteration: 
        print('Floor is shining, nothing to clean!')
        return

    message = 'There is dust to be vacuum-cleaned, Power ON? (l/y/N):'
    while True:
        if args.force:
            option = 'Y'
        else:
            option = six.moves.input(message) or 'N'
        if option == 'l':
            list_files(filelist=[first_file])
            list_files(filelist=filelist)
        elif option in ['y','Y']:
            files0, dirs0, errors0 = delete([first_file])
            files, dirs, errors = delete(filelist)
            errors.update(errors0)
            if files:
                print('Successfully vacuum-cleaned %d files and %d directories!' %\
                                                 (len(files+files0),
                                                  len(dirs+dirs0)))
            if errors:

                message = 'Oh no! Some dust seems glued to the floor (%d)! Show? (y/N):' % len(errors)
                option = six.moves.input(message) if not args.force else option
                if option in ['y','Y']:
                    for error in errors.items():
                        print('%s ---> %s' % error )
            break
        elif option in ['n','N']:
            break
        else:
            print('Options available [l]ist, [y]es or [n]o')

def scrub(args):
    print ('Archiving not implemented yet')

def archive(args):
    print('Archiving not implemented yet')


parser_list.set_defaults(func=list_files)
parser_clean.set_defaults(func=clean)
parser_scrub.set_defaults(func=scrub)
parser_archive.set_defaults(func=archive)

if __name__ == "__main__":
    args = parser.parse_args()
    args.func(args)