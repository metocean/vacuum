import os
import mock

from ..command import execute, parser

@mock.patch('vacuum.utils.flister')
def test_list_command_with_pattern(flister):
    flister.return_value(['/var/lib','/var/log'])
    args = parser.parse_args(['-p','var','list','/'])
    execute(args)
    flister.assert_called()