#!/usr/bin/env python3

# FBA_dat_gen.py
# Written in 2017 by SpiralBrad <SpiralBrad@spiralgoat.com>

## usage: FBA_dat_gen.py [-h] -dat DAT -path PATH [-output_file OUTPUT_FILE]
##                       [-header_name HEADER_NAME]
##                       [-header_description HEADER_DESCRIPTION]
##                       [-header_version HEADER_VERSION]
## 
## Generates Final Burn Alpha .dat file needed for RetroArch/libretro-
## db/c_converter
## 
## optional arguments:
##   -h, --help            show this help message and exit
##   -output_file OUTPUT_FILE
##                         Path to the target output file; example: FB Alpha - 
##                         Arcade games.dat
##   -header_name HEADER_NAME
##                         Override the clrmamepro(name) in the output .dat
##   -header_description HEADER_DESCRIPTION
##                         Override the clrmamepro(description) in the output 
##                         .dat
##   -header_version HEADER_VERSION
##                         Override the clrmamepro(version) in the output .dat
## 
## required arguments:
##   -dat DAT              Misc -> Generate dat file -> Generate dat (Arcade 
##                         only)
##   -path PATH            Path to a split, ClrMamePro verified and TorrentZipped 
##                         ROM set matching the Arcade only dat
## 
## example usage: python3 FBA_dat_gen.py -dat "FB Alpha v0.2.97.42 (ClrMame Pro 
##                  XML).dat" -path  "/path/to/split/verified/torrentzipped/roms/" 
##                  -output_file "FB Alpha - Arcade Games.dat"

#-   To the extent possible under law, the author(s) have dedicated all 
#-   copyright and related and neighboring rights to this software to the 
#-   public domain worldwide. This software is distributed without any 
#-   warranty.
#-
#-   You should have received a copy of the CC0 Public Domain Dedication 
#-   along with this software. If not, see 
#-   <http://creativecommons.org/publicdomain/zero/1.0/>.

import argparse
import hashlib
import operator
import os
import os.path
import sys
import xml.etree.ElementTree as ET
import zlib

def main():
    parser = setup_argparse()
    args = parser.parse_args()
    dat_root = get_datroot(args.dat, parser)
    header_name = get_header_name(args)
    header_version = get_header_version(args, dat_root, parser)
    header_description = get_header_description(args, header_version)
    header = generate_dat_header(header_name, header_description, header_version)
    game_list = generate_game_list(dat_root, args.path)
    output(args, header, game_list)

def setup_argparse():
    """Set up the argparse arguments and return the argparse instance"""
    parser = argparse.ArgumentParser(prog='FBgen.py', description='Generates Final Burn Alpha .dat file needed for RetroArch/libretro-db/c_converter')
    required_arguments = parser.add_argument_group('required arguments')
    required_arguments.add_argument('-dat', help='Misc -> Generate dat file -> Generate dat (Arcade only)', required=True)
    required_arguments.add_argument('-path', help='Path to a split, ClrMamePro verified and TorrentZipped ROM set matching the Arcade only dat', required=True)
    parser.add_argument('-output_file', help='Path to the target output file; example: FB Alpha - Arcade games.dat')
    parser.add_argument('-header_name', help='Override the clrmamepro(name) in the output .dat')
    parser.add_argument('-header_description', help='Override the clrmamepro(description) in the output .dat')
    parser.add_argument('-header_version', help='Override the clrmamepro(version) in the output .dat')

    if len(sys.argv[1:])==0:
        parser.print_help()
        print('\n'.join(['',
                         'example usage: python3 FBA_dat_gen.py -dat "FB Alpha v0.2.97.42 (ClrMame Pro ', 
                         '                 XML).dat" -path  "/path/to/split/verified/torrentzipped/roms/" ',
                         '                 -output_file "FB Alpha - Arcade Games.dat"']))
        parser.exit()
    return parser

def get_datroot(dat, parser):
    """Get the ElementTree root from the specified <dat> file and return the ElementTree root element"""
    if not os.path.isfile(dat):
        print('File not found: ' + dat)
        print('')
        parser.print_help()
        parser.exit()
    else:
        dat_tree = ET.parse(dat)
        dat_root = dat_tree.getroot()
    return dat_root

def get_header_name(args):
    """Return the default header name or the -header_name argument"""
    if not args.header_name:
        header_name = 'FB Alpha - Arcade Games'
    else:
        header_name = args.header_name
    return header_name

def get_header_version(args, dat_root, parser):
    """Return the version from the <dat_root> header version, or the -header_version argument"""
    if not args.header_version:
        header_version = dat_root.find('header').find('version').text
        if not header_version:
            print('Version not found in ClrMame Pro XML dat. Please specify with -header_version')
            print('')
            parser.print_help()
            parser.exit()
            raise SystemExit()
    else:
        header_version = args.header_version
    return header_version

def get_header_description(args, version):
    """Return the description by generationg via the <version> or the -header_description argument"""
    if not args.header_description:
        header_description = 'FB Alpha v' + version + ' Arcade Games'
    else:
        header_description = args.header_description
    return header_description

def generate_dat_header(name, description, version):
    """Return the textual DAT header from a given <name>, <description>, and <version>"""
    header = ['clrmamepro (',
              '\t' + 'name "%s"' % name,
              '\t' + 'description "%s"' % description,
              '\t' + 'version %s' % version,
              ')']
    return '\n'.join(header)

def generate_game_list(dat_root, path):
    """Generate the sorted list of games with all metadata and return a textual dat list"""
    game_list = []
    
    if not os.path.isdir(path):
        print('Path not found: ' + path)
        print('')
        parser.print_help()
        parser.exit()
    else:
        game_entries = []
        for game in dat_root.iter('game'):
            # 'gpriders.zip' kludge hack, as of at least 0.2.97.42
            #   - rom is exact to 'gprider.zip' and does not exist in a split set
            if game.get('name') != 'gpriders':
                entry = GameEntry()
                # set name ('description' in FBA-generated-dat)
                entry.name = game.find('description').text
                # set year
                entry.year = game.find('year').text
                # set publisher ('manufacturer' in FBA-generated-dat)
                entry.publisher = game.find('manufacturer').text
                # set zip filename
                entry.zip = game.get('name') + '.zip'
                zip_path = os.path.join(path, entry.zip)
                # set zip size
                entry.size = os.path.getsize(zip_path)
                # set zip crc
                entry.crc = get_crc(zip_path)
                # set zip md5
                entry.md5 = get_md5(zip_path)
                # set zip sha1
                entry.sha1 = get_sha1(zip_path)
                # Add to game_entries list
                game_entries.append(entry)

            # Sort game_entries list
            game_entries.sort(key=operator.attrgetter('name'))
        
        # Generate formatted textual list
        for entry in game_entries:
            text_entry = ['game (',
                          '\t' + 'name "%s"' % entry.name,
                          '\t' + 'year %s' % entry.year,
                          '\t' + 'publisher "%s"' % entry.publisher,
                          '\t' + 'rom ( name %s size %s crc %s md5 %s sha1 %s )' % (entry.zip, entry.size, entry.crc, entry.md5, entry.sha1),
                          ')',
                          '']
            game_list.append('\n'.join(text_entry))
    return '\n'.join(game_list)

def output(args, header, game_list):
    """Combine <header> and <game_list> and print to stdout, or write to specified -output_file"""
    if not args.output_file:
        # print to stdout
        print('\n'.join([header, '', game_list]).rstrip())
    else:
        # write to args.output_file
        with open(args.output_file, 'w') as f:
            f.write('\n'.join([header, '', game_list]))

class GameEntry:
    name = None
    year = None
    publisher = None
    zip = None
    size = None
    crc = None
    md5 = None
    sha1 = None
    
def get_crc(file):
    """Return the CRC32 hash of <file>"""
    prev = 0
    for eachLine in open(file, 'rb'):
        prev = zlib.crc32(eachLine, prev)
    return str("%X"%(prev & 0xFFFFFFFF)).zfill(8)

def get_md5(file):
    """Return the MD5 hash of <file>"""
    m = hashlib.md5()
    with open(file, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            m.update(chunk)
    return m.hexdigest().zfill(32)

def get_sha1(file):
    """Return the SHA1 hash of <file>"""
    m = hashlib.sha1()
    with open(file, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            m.update(chunk)
    return m.hexdigest().zfill(40)

if __name__ == '__main__':
    main()