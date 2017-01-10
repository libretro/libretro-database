#!/usr/bin/python
# public domain by @bparker06
# https://github.com/libretro/libretro-database/issues/388
# https://raw.githubusercontent.com/mupen64plus/mupen64plus-core/master/data/mupencheat.txt
import re, os

cheatfile = ''
cheats = ''
game = ''
gamefile = None
gamefilename = ''
cheatnum = -1
subcheatnum = 0

def slugify(value):
    # ripped off from Django and modified
    import unicodedata
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s\-\.\(\)]', '', value).strip())

    return value

with open('mupencheat.txt', 'rb') as f:
  cheatfile = f.read()

for line in cheatfile.split('\n'):
  if line.startswith('gn '):
    if gamefile is not None:
      if cheatnum >= 0:
        gamefile.write('cheats = ' + str(cheatnum + 1) + '\n')
        gamefile.write(cheats + '\"\n')

      gamefile.close()
      gamefile = None
      subcheatnum = 0
      cheats = ''

      if cheatnum < 0:
        os.unlink(gamefilename)

      cheatnum = -1

    game = line.split('gn ')[1]
    game = re.sub(r'^[\s*|=]', '', game)
    gamefilename = 'cheats/' + str(slugify(unicode(game))) + '.cht'
    gamefile = open(gamefilename, 'wb')
  elif line.startswith(' cn '):
    name = line.split(' cn ')[1]
    cheatnum += 1

    if subcheatnum > 0:
      cheats += '\"\n'
      subcheatnum = 0

    cheats += 'cheat' + str(cheatnum) + '_desc = \"' + name + '\"\n'
    cheats += 'cheat' + str(cheatnum) + '_enable = false\n'
  elif line.startswith('  ') and not line.startswith('  cd '):
    cheat = line.split('  ')[1]
    cheat = re.sub(r'(\?\?\?\?).*', '\\1', cheat)
    cheat = re.sub(r'\?\?\?\?', 'XXXX', cheat)

    if subcheatnum == 0:
      cheats += 'cheat' + str(cheatnum) + '_code = \"' + cheat
    else:
      cheats += ';' + cheat

    subcheatnum += 1
