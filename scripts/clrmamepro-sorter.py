#!/usr/bin/env python3

# This implements a very stupid ClrMamePro DAT file sorter. It expects a DAT
# file to be "well formed", so everything except the first level should be
# indented, since that is used to lump lines together into one "entry".

import re
import sys

from typing import List


START_STANZA = re.compile(r'([a-z0-9]+)\s*\(', re.IGNORECASE)
VALID_START = {'clrmamepro', 'game'}


def sortdat(lines: str) -> str:
    data: List[str] = []
    curline: str = ''
    for line in lines.split('\n'):
        start = START_STANZA.match(line)
        if start:
            if start.group(1) not in VALID_START:
                raise Exception("File doesn't look like a valid DAT file!")
            if curline != '':
                data.append(curline)
            curline = line
        else:
            curline += '\n' + line
    if curline != '':
        data.append(curline)

    return '\n'.join(sorted(data))


if __name__ == '__main__':
    for file in sys.argv[1:]:
        print(f'Sorting {file}')
        with open(file, 'r') as infile:
            content = sortdat(infile.read())
        with open(file, 'w') as outfile:
            outfile.write(content)
