#!/usr/bin/env python3
# RDB to DAT Converter
#
# Based on:
# - RDBEd by Schelling (https://github.com/schellingb/RDBEd)
# - RetroArch's libretro-db (https://github.com/libretro/RetroArch/tree/master/libretro-db)
#
# RDBEd License:
#
#  RDBEd - Retro RDB & DAT Editor
#  Copyright (C) 2020-2023 - Bernhard Schelling
#
#  RDBEd is free software: you can redistribute it and/or modify it under the terms
#  of the GNU General Public License as published by the Free Software Found-
#  ation, either version 3 of the License, or (at your option) any later version.
#
#  RDBEd is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#  PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with RDBEd.
#  If not, see <http://www.gnu.org/licenses/>.
#
# RetroArch/libretro-db License (MIT):
# Copyright (c) 2011-2021 RetroArch Team
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# This script is licensed under MIT as derivative work of both projects.

import argparse
import os
import sys
import struct
import traceback
from datetime import datetime
import msgpack
from collections import OrderedDict

class RDBConverter:
    def __init__(self, verbose=False):
        self.entries = []
        self.broken = []
        self.verbose = verbose

    def debug_print(self, *args, **kwargs):
        if self.verbose:
            print(*args, file=sys.stderr, **kwargs)

    def parse_rdb(self, filepath):
        """Parse a RetroArch RDB file using the proper RARCHDB format"""
        try:
            with open(filepath, 'rb') as f:
                header = f.read(16)
                if len(header) < 16:
                    self.debug_print("File too small to be valid RDB")
                    return False

                magic, meta_offset = struct.unpack('>QQ', header)
                self.debug_print(f"Magic: 0x{magic:016X}, Meta Offset: {meta_offset}")

                if magic != 0x5241524348444200: # "RARCHDB\0" in big-endian
                    self.debug_print("Invalid RDB magic number")
                    return False

                data_size = meta_offset - 16 if meta_offset > 16 else os.path.getsize(filepath) - 16
                data = f.read(data_size)
                self.debug_print(f"Reading {data_size} bytes of main data")

                unpacker = msgpack.Unpacker(raw=False, strict_map_key=False)
                unpacker.feed(data)

                entries = [obj for obj in unpacker if obj is not None]
                self.debug_print(f"Found {len(entries)} main entries")

                if meta_offset > 16:
                    f.seek(meta_offset)
                    meta_data = f.read()
                    self.debug_print(f"Reading {len(meta_data)} bytes of meta data")
                    meta_unpacker = msgpack.Unpacker(raw=False, strict_map_key=False)
                    meta_unpacker.feed(meta_data)
                    meta_entries = list(meta_unpacker)
                    self.debug_print(f"Found {len(meta_entries)} meta entries")

                self._process_entries(entries)
                return True

        except Exception as e:
            self.debug_print(f"Exception during parsing: {type(e).__name__}: {e}")
            self.broken.append({"error": f"File parsing failed: {str(e)}"})
            return False

    def _process_entries(self, entries):
        """Process and validate entries from the RDB file"""
        if not isinstance(entries, list):
            error_msg = "Top-level object is not a list"
            self.debug_print(error_msg)
            self.broken.append({"error": error_msg, "data": str(entries)[:200]})
            return

        self.debug_print(f"Processing {len(entries)} entries...")

        for idx, obj in enumerate(entries):
            try:
                if not isinstance(obj, dict):
                    error_msg = f"Entry {idx} is not a dictionary (got {type(obj).__name__})"
                    self.debug_print(error_msg)
                    self.debug_print(f"Raw data: {str(obj)[:200]}")
                    self.broken.append({
                        "parse_error": {
                            "index": idx,
                            "error": error_msg,
                            "type": type(obj).__name__,
                            "data": obj if isinstance(obj, (str, int, float)) else str(obj)[:200]
                        }
                    })
                    continue

                if 'name' in obj or 'rom_name' in obj:
                    if self.verbose:
                        debug_info = f"Entry {idx}: {obj.get('name') or obj.get('rom_name')}"
                        if 'crc' in obj:
                            debug_info += f" [CRC: {obj['crc'].hex().upper()}]"
                        self.debug_print(debug_info)
                    self.entries.append(obj)
                else:
                    error_msg = f"Entry {idx} missing 'name' field"
                    self.debug_print(error_msg)
                    self.debug_print(f"Available fields: {list(obj.keys())}")
                    obj.update({
                        "parse_error": {
                            "index": idx,
                            "error": error_msg,
                        }
                    })
                    self.broken.append(obj)

            except Exception as e:
                error_msg = f"Entry {idx} processing failed: {type(e).__name__}: {str(e)}"
                self.debug_print(error_msg)
                self.debug_print(f"Entry data: {str(obj)[:200]}")
                obj.update({
                    "parse_error": {
                        "index": idx,
                        "error": error_msg,
                        "exception_type": type(e).__name__,
                        "traceback": traceback.format_exc()[:500]
                    }
                })
                self.broken.append(obj)

        self.debug_print(f"Processed {len(self.entries)} valid entries and {len(self.broken)} broken entries")
        if self.broken and self.verbose:
            self.debug_print("\nFirst 10 broken entries:")
            for i, broken in enumerate(self.broken[:10]):
                error_msg = broken.get("parse_error", {}).get("error", broken.get("error", "Unknown"))
                self.debug_print(f"{i + 1}. {error_msg}")

    def write_dat(self, output_path, name, is_broken=False):
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

        entries_to_write = self.broken if is_broken else sorted(
            self.entries,
            key=lambda e: (
                e.get('name', '').lower() == '',
                e.get('name', '').lower(),
                e.get('crc', '') == '',
                e.get('crc', '')
            )
        )

        # Preferred field order (matches RDBEd)
        preferred_order = [
            'name', 'description', 'genre', 'users',
            'releaseyear', 'releasemonth', 'releaseday',
            'rumble', 'analog', 'coop', 'enhancement_hw',
            'franchise', 'original_title', 'developer',
            'publisher', 'origin', 'region', 'tags'
        ]

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("clrmamepro (\n")
            dat_name = os.path.splitext(os.path.basename(output_path))[0]
            f.write(f"\tname \"{dat_name}\"\n")
            desc = "Broken entries from" if is_broken else "Converted from"
            f.write(f"\tdescription \"{desc}: {name}.rdb\"\n")
            f.write(f"\tversion \"{datetime.now().strftime('%Y%m%d')}\"\n")
            f.write("\thomepage \"https://github.com/libretro/RetroArch\"\n")
            f.write(")\n\n")

            for entry in entries_to_write:
                entry = entry.copy()
                if 'rom_name' in entry and 'name' not in entry:
                    entry['name'] = entry['rom_name']

                if 'releaseyear' in entry:
                    entry.setdefault('releasemonth', 1)
                    entry.setdefault('releaseday', 1)

                # Get all non-ROM fields
                rom_keys = {'rom_name', 'size', 'crc', 'md5', 'sha1', 'serial'}
                all_fields = [k for k in entry if k not in rom_keys]

                # Sort fields: preferred order first, then alphabetical
                def field_sort_key(field):
                    try:
                        return (0, preferred_order.index(field))
                    except ValueError:
                        return (1, field)

                sorted_fields = sorted(all_fields, key=field_sort_key)

                f.write("game (\n")
                for field in sorted_fields:
                    val = str(entry[field]).replace('"', "'")
                    f.write(f"\t{field} \"{val}\"\n")

                rom_fields = []
                rom_name = str(entry.get('rom_name') or entry.get('name', '')).replace('"', "'")
                if rom_name:
                    rom_fields.append(f'name "{rom_name}"')

                if 'size' in entry:
                    rom_fields.append(f'size {entry["size"]}')

                for hash_field in ['crc', 'md5', 'sha1']:
                    if hash_field in entry:
                        hash_val = entry[hash_field]
                        if isinstance(hash_val, bytes):
                            hash_val = hash_val.hex().upper()
                        rom_fields.append(f'{hash_field} {hash_val}')

                if 'serial' in entry:
                    serial = str(entry['serial']).replace('"', "'")
                    rom_fields.append(f'serial "{serial}"')

                if rom_fields:
                    f.write("\trom ( " + " ".join(rom_fields) + " )\n")

                f.write(")\n")

def main():
    parser = argparse.ArgumentParser(
        description="Convert RetroArch RDB files to clrmamepro DAT format",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("inputs", nargs="+", help="One or more RDB input files")
    parser.add_argument("-o", "--output", help="Output DAT file directory", default=".")
    parser.add_argument("--broken", help="Custom name for broken entries DAT file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose debug output")
    args = parser.parse_args()

    if len(args.inputs) > 1 and not os.path.isdir(args.output):
        print("When using multiple input files, --output must be a directory", file=sys.stderr)
        sys.exit(1)

    for input_file in args.inputs:
        converter = RDBConverter(verbose=args.verbose)

        if not converter.parse_rdb(input_file):
            print(f"Failed to parse RDB file: {input_file}", file=sys.stderr)
            continue

        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_path = os.path.join(args.output, f"{base_name} - RetroArch.dat")
        broken_path = os.path.join(
            args.output,
            args.broken if args.broken else f"{base_name} - RetroArch (broken).dat"
        ) if converter.broken else None

        converter.write_dat(output_path, base_name)
        print(f"Successfully converted {len(converter.entries)} entries to {output_path}")

        if converter.broken and broken_path:
            converter.write_dat(broken_path, base_name, is_broken=True)
            print(f"Wrote {len(converter.broken)} broken entries to {broken_path}")

if __name__ == "__main__":
    main()
