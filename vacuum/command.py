import argparse

from .utils import flister

parser = argparse.ArgumentParser()
parser.add_argument('-r','--root', 
                    help='Root directory to search files for',
                    default=None)
parser.add_argument('-p','--pattern', 
                    help='A RE pattern to search files inside root dir',
                    action='append',
                    default=None)
parser.add_argument('-o','--older', 
                    help='Find files older then a giving period (i.e. 1h or 2min or 5d)',
                    action='store',
                    default=None)
parser.add_argument('command', help='List files that matches the given conditions',
                    choices=['list', 'clean', 'archive'])

def vacuumme(args):
    filelist = flister(args.root, args.pattern, args.older)
    if args.command == 'list':
        for filepath in sorted(filelist):
            print(filepath)
    elif args.command == 'clean':
        print('Clean up not implemented yet')
    elif args.command == 'archive':
        print('Archiving not implemented yet')

if __name__ == "__main__":
    args = parser.parse_args()
    vacuumme(args)