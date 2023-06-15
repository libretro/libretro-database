import sys
import codecs
from xml.etree.cElementTree import parse as xmlparse

def header(data):
    if data.tag == 'mame':
        return {
            'name': 'MAME',
            'version': data.attrib['build'].split(' ')[0]
        }
    header = data.find('header')
    if header:
        return {
            'name': header.find('name').text,
            'version': header.find('version').text
        }
    return {
        'name': 'MAME',
        'version': 'unknown'
    }

# Treat a machine as arcade if it has coin slots
def is_arcade(data):
    input = data.find('input')
    return bool(input and input.attrib.get('coins'))

def machine(data):
    attr = data.attrib
    name = attr['name']
    desc = data.find('description').text
    year = data.find('year')
    manu = data.find('manufacturer')

    info = {}
    info['name'] = name
    info['description'] = desc
    if year:
        info['year'] = year.text
    if manu:
        info['manufacturer'] = manu.text

    roms = []
    for r in data.findall('rom'):
        ra = r.attrib
        if 'crc' not in ra or 'size' not in ra:
            continue
        rinfo = {
            'name': ra['name'],
            'size': ra['size'],
            'crc': ra['crc']
        }
        if 'sha1' in ra:
            rinfo['sha1'] = ra['sha1']
        roms.append(rinfo)
    info['roms'] = roms

    return info

def machines(data):
    info = {}
    for m in data.findall('machine'):
        if not is_arcade(m):
            sys.stderr.write("Skipping non-arcade machine {}\n".format(repr(m.find('description').text)))
            continue
        minfo = machine(m)
        info[minfo['name']] = minfo
    for g in data.findall('game'):
        minfo = machine(g)
        info[minfo['name']] = minfo
    return info

def crcmap(data):
    seen = {}
    info = {}

    # Look for CRC collisions
    for machine in data.items():
        for rom in machine[1]["roms"]:
            crc = rom['crc']
            if crc in seen:
                seen[crc] += 1
            else:
                seen[crc] = 1

    for machine in data.items():
        unique = None
        for rom in machine[1]["roms"]:
            name = rom['name']
            if ' ' in name:
                continue
            crc = rom['crc']
            if seen[crc] > 1:
                continue
            unique = crc
            continue
        sys.stderr.write("{}: {}\n".format(unique, repr(machine[1]["description"])))
        if unique is not None:
            info[unique] = machine

    return info

def emit(header, data, out):
    out.write('clrmamepro (\n')
    out.write('        name "{}"\n'.format(header['name']))
    out.write('        version {}\n'.format(header['version']))
    out.write(')\n\n')

    for crc, game in data.items():
        out.write('game (\n')
        out.write(u'        name "{}"\n'.format(game[1]["description"]))
        if 'year' in game:
            out.write('        year "{}"\n'.format(game[1]["year"]))
        if 'manufacturer' in game:
            out.write(u'        developer "{}"\n'.format(game[1]["manufacturer"]))

        for rom in filter(lambda r: r['crc'] == crc, game[1]["roms"]):
            if 'sha1' in rom:
                out.write('        rom ( name {name} size {size} crc {crc} sha1 {sha1} )\n'.format(**rom))
            else:
                out.write('        rom ( name {name} size {size} crc {crc} )\n'.format(**rom))
        out.write(')\n\n')

data = xmlparse(sys.argv[1]).getroot()

with codecs.open(sys.argv[2], 'w', 'utf-8') as out:
    emit(header(data), crcmap(machines(data)), out)
