import os
import mock

from ..command import *

@mock.patch('builtins.print')
def test_list_command_with_pattern(printer):
    args = parser.parse_args(['-r','/','-p','var','list'])
    vacuumme(args)
    printer.assert_called()