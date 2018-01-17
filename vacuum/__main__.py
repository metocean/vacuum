#!/usr/bin/env python

from __future__ import absolute_import

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)+'..' ))

from vacuum.command import parser

def main():
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
    