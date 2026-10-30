#!/usr/bin/env python3

# FBNeo_dat_gen.py
# Written in 2017 by SpiralBrad <SpiralBrad@spiralgoat.com>

## usage: FBNeo_dat_gen.py [-h] --dat DAT [--path PATH]
##                       [--output-file OUTPUT_FILE]
##                       [--header-name HEADER_NAME]
##                       [--header-description HEADER_DESCRIPTION]
##                       [--header-version HEADER_VERSION]
##                       [--set-type {split,non-merged}] [--add-keys DAT]
## 
## Generates Final Burn Neo .dat file needed for RetroArch/libretro-
## db/c_converter
## 
## optional arguments:
##   -h, --help            show this help message and exit
##   -p, --path PATH       Path to a ClrMamePro verified and TorrentZipped
##                         ROM set matching the Arcade only dat (see
##                         --set-type); required unless --add-keys
##   -o, --output_file OUTPUT_FILE
##                         Path to the target output file; example: FBNeo - 
##                         Arcade games.dat
##   --header-name HEADER_NAME
##                         Override the clrmamepro(name) in the output .dat
##   --header-description HEADER_DESCRIPTION
##                         Override the clrmamepro(description) in the output 
##                         .dat
##   --header-version HEADER_VERSION
##                         Override the clrmamepro(version) in the output .dat
##   --set-type {split,non-merged}
##                         The kind of ROM set --path holds, or that the dat
##                         --add-keys reads was made from (default: split)
##   --add-keys DAT        Write DAT with the set fingerprints from --dat
##                         added, changing nothing else in it; --path is not
##                         read
## 
## required arguments:
##   -d, --dat DAT              Misc -> Generate dat file -> Generate dat (Arcade 
##                         only)
## 
## example usage: python3 FBA_dat_gen.py --dat "FBNeo v0.2.97.42 (ClrMame Pro 
##                  XML).dat" --path  "/path/to/split/verified/torrentzipped/roms/" 
##                  --output-file "FBNeo - Arcade Games.dat"

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
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zlib

def main():
    parser = setup_argparse()
    args = parser.parse_args()
    if parser == None:
        print("parser is none")
    dat_root = get_datroot(args.dat, parser)
    if args.add_keys:
        add_keys(args, dat_root)
        return
    if not args.path:
        parser.error('the following arguments are required: -p/--path')
    header_name = get_header_name(args)
    header_version = get_header_version(args, dat_root, parser)
    header_description = get_header_description(args, header_version)
    header = generate_dat_header(header_name, header_description, header_version)
    game_list = generate_game_list(dat_root, args.path, parser, args.set_type)
    output(args, header, game_list)

def setup_argparse():
    """Set up the argparse arguments and return the argparse instance"""
    parser = argparse.ArgumentParser(prog='FBgen.py', description='Generates Final Burn Neo .dat file needed for RetroArch/libretro-db/c_converter')
    required_arguments = parser.add_argument_group('required arguments')
    required_arguments.add_argument('-d', '--dat', help='Misc -> Generate dat file -> Generate dat (Arcade only)', required=True)
    parser.add_argument('-p', '--path', help='Path to a ClrMamePro verified and TorrentZipped ROM set matching the Arcade only dat (see --set-type); required unless --add-keys')
    parser.add_argument('-o', '--output-file', help='Path to the target output file; example: FBNeo - Arcade games.dat')
    parser.add_argument('--header-name', help='Override the clrmamepro(name) in the output .dat')
    parser.add_argument('--header-description', help='Override the clrmamepro(description) in the output .dat')
    parser.add_argument('--header-version', help='Override the clrmamepro(version) in the output .dat')
    parser.add_argument('--set-type', choices=['split', 'non-merged'], default='split', help='The kind of ROM set --path holds, or that the dat --add-keys reads was made from (default: split)')
    parser.add_argument('--add-keys', metavar='DAT', help='Write DAT with the set fingerprints from --dat added, changing nothing else in it; --path is not read')

    if len(sys.argv) == 1:
        parser.print_help()
        print('\n'.join(['',
                         'example usage: python3 FBA_dat_gen.py --dat "FBNeo v0.2.97.42 (ClrMame Pro ', 
                         '                 XML).dat" -path  "/path/to/split/verified/torrentzipped/roms/" ',
                         '                 --output-file "FBNeo - Arcade Games.dat"']))
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
        header_name = 'FBNeo - Arcade Games'
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
        header_description = 'FBNeo v' + version + ' Arcade Games'
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

def generate_game_list(dat_root, path, parser, set_type):
    """Generate the sorted list of games with all metadata and return a textual dat list"""
    game_list = []
    
    if not os.path.isdir(path):
        print(f'Path is not dir or not found: {path}\n')
        parser.print_help()
        parser.exit()
    else:
        game_entries = []
        fps = get_set_fps(dat_root, set_type)
        for game in dat_root.iter('game'):
            # 'gpriders.zip' kludge hack, as of at least 0.2.97.42
            #   - rom is exact to 'gprider.zip' and does not exist in a split set
            if game.get('name') != 'gpriders':
            # same 0.2.97.44
                if game.get('name') != 'natodefa':
                    if game.get('name') != 'marioo':
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
                        if not os.path.exists(zip_path):
                            print(f'Did not find "{zip_path}", skipping.')
                            continue
                        # set zip size
                        entry.size = os.path.getsize(zip_path)
                        # set zip crc
                        entry.crc = get_crc(zip_path)
                        # set zip md5
                        entry.md5 = get_md5(zip_path)
                        # set zip sha1
                        entry.sha1 = get_sha1(zip_path)
                        # set the set fingerprints, from the dat
                        entry.set_fp1, entry.set_fpm1 = fps.get(game.get('name'), (None, None))
                        # Add to game_entries list
                        game_entries.append(entry)

            # Sort game_entries list
            game_entries.sort(key=operator.attrgetter('name'))
        
        # Generate formatted textual list
        for entry in game_entries:
            text_entry = ['game (',
                          '\t' + 'name "%s"' % entry.name,
                          '\t' + 'releaseyear "%s"' % entry.year,
                          '\t' + 'publisher "%s"' % entry.publisher]
            if entry.set_fp1:
                text_entry.append('\t' + 'set_fp1 %s' % entry.set_fp1)
            if entry.set_fpm1:
                text_entry.append('\t' + 'set_fpm1 %s' % entry.set_fpm1)
            text_entry += ['\t' + 'rom ( name %s size %s crc %s md5 %s sha1 %s )' % (entry.zip, entry.size, entry.crc, entry.md5, entry.sha1),
                           ')',
                           '']
            game_list.append('\n'.join(text_entry))
    return '\n'.join(game_list)

def output(args, header, game_list):
    """Combine <header> and <game_list> and print to stdout, or write to specified --output-file"""
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
    set_fp1 = None
    set_fpm1 = None
    
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

def fingerprint(crcs):
    """Return the CRC32 of <crcs>, de-duplicated, sorted, each as 4 big-endian bytes; None for no crcs"""
    if not crcs:
        return None
    prev = 0
    for crc in sorted(set(crcs)):
        prev = zlib.crc32(struct.pack('>I', crc), prev)
    return str("%X"%(prev & 0xFFFFFFFF)).zfill(8)

def get_bios_crcs(games, name):
    """Return the ROM crcs of the BIOS the game <name> reaches through romof, at most 4 steps away; empty if none"""
    romof = games[name][1]
    for step in range(4):
        if romof not in games:
            break
        if games[romof][2]:
            return set(crc for crc, merged in games[romof][3])
        romof = games[romof][1]
    return set()

def get_set_fps(dat_root, set_type):
    """Return game name -> (set_fp1, set_fpm1) from <dat_root> for the records of a <set_type> ROM set: a split record holds the game's own ROMs, a non-merged one its parent's too, neither its BIOS; nodump and empty ROMs are left out.  set_fpm1, over a parent's own ROMs and its clones', is given on a split parent where it differs from set_fp1"""
    games = {}
    for game in dat_root.iter('game'):
        roms = [(int(rom.get('crc'), 16), rom.get('merge') is not None)
                for rom in game.findall('rom')
                if rom.get('crc') and rom.get('status') != 'nodump'
                and rom.get('size') != '0']
        games[game.get('name')] = (game.get('cloneof'), game.get('romof'),
                                   game.get('isbios') == 'yes', roms)
    own = {}
    for name, (cloneof, romof, isbios, roms) in games.items():
        own[name] = [crc for crc, merged in roms if not merged]
    merged_set = {}
    for name, (cloneof, romof, isbios, roms) in games.items():
        if cloneof in games and not games[cloneof][0]:
            merged_set.setdefault(cloneof, list(own[cloneof])).extend(own[name])
    fps = {}
    for name, (cloneof, romof, isbios, roms) in games.items():
        if set_type == 'split':
            set_fp1 = fingerprint(own[name])
            set_fpm1 = fingerprint(merged_set.get(name))
        else:
            bios = get_bios_crcs(games, name)
            set_fp1 = fingerprint([crc for crc, merged in roms
                                   if not (merged and crc in bios)])
            set_fpm1 = None
        if set_fpm1 == set_fp1:
            set_fpm1 = None
        fps[name] = (set_fp1, set_fpm1)
    return fps

def add_keys(args, dat_root):
    """Write the dat --add-keys with the set fingerprints from <dat_root> added to each game, before its rom line, in place of any it has; nothing else in it changes"""
    fps = get_set_fps(dat_root, args.set_type)
    rom_line = re.compile(r'\trom \( name (\S+)\.zip ')
    text = []
    with open(args.add_keys, encoding='utf-8', newline='') as f:
        for line in f:
            if line.startswith(('\tset_fp1 ', '\tset_fpm1 ')):
                continue
            match = rom_line.match(line)
            if match:
                set_fp1, set_fpm1 = fps.get(match.group(1), (None, None))
                if set_fp1:
                    text.append('\tset_fp1 %s\n' % set_fp1)
                if set_fpm1:
                    text.append('\tset_fpm1 %s\n' % set_fpm1)
            text.append(line)
    if not args.output_file:
        sys.stdout.write(''.join(text))
    else:
        with open(args.output_file, 'w', encoding='utf-8', newline='') as f:
            f.write(''.join(text))

if __name__ == '__main__':
    main()
