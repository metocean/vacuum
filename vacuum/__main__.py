from __future__ import absolute_import

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)+'..' ))

from vacuum.command import vacuumme, parser

if __name__ == '__main__':
    vacuumme(parser.parse_args())
    