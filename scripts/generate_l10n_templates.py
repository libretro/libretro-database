#!/usr/bin/python3

# Run ./scripts/generate_l10n_templates.py at database project root.
# Localization files are in l10n directory.
# It is not compiled to rdb files but downloaded by users separately.
# Users can download their own languages to save space and bandwidth.

import glob
import re
import configparser
import collections

dat_file_names = glob.glob("dat/*.dat")
dat_file_names.extend(glob.glob("metadat/*/*.dat"))

for dat_file_name in dat_file_names:
    print("parsing: " + dat_file_name)
    with open(dat_file_name, 'r', encoding = 'latin1') as file:
        data = file.read()
        names = re.findall(r"\tname \"(.*)\"", data);
        config = configparser.ConfigParser()
        for name in names:
            escaped = name.replace('%', '%%')
            config['DEFAULT'][name] = escaped
        ini_file_name = "l10n/en/" + dat_file_name.split('/')[-1].replace('.dat', '.ini')
        with open(ini_file_name, 'w') as ini_file:
            config.write(ini_file)
