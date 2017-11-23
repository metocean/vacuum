import os
import mock

from ..command import *

@mock.patch('builtins.print')
def test_list_command_with_pattern(printer):
    args = parser.parse_args(['-p','var','list','/'])
    execute(args)
    printer.assert_called()