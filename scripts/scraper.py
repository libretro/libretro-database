from lxml import html
import sys
import requests
import os
import re
from chtwrite import cheatwriter
#cheat scraper for http://bsfree.shadowflareindustries.com/ navigate to the system and codetype you want, copy url
#run the script with "python scraper.py 'url'"


baseurl = 'http://bsfree.org/'
supported = "Gameboy", "Gameboy Advance", "Sega Game Gear", "Genesis", "Nintendo Entertainment System", "Sega Master System", "Playstation", "Super Nintendo", "Sega Saturn"


page = requests.get(baseurl)
tree = html.fromstring(page.text)

sysurl = tree.xpath('//td[@class="codedescalt"]//a/@href')
system = tree.xpath('//td[@class="codedescalt"]/a[@href]/text()')

supsys = [system.index(sup) for sup in supported]

for idx3 in supsys:
	page2 = requests.get(baseurl + sysurl[idx3])

	tree2 = html.fromstring(page2.text)

	cdtype = tree2.xpath('//td[@class="codedescalt"]//a/@href')
	nmtype = tree2.xpath('//td[@class="codedescalt"]/a[@href]/text()')
	outdir = system[idx3]
	if not os.path.exists(outdir):
		os.mkdir(outdir)
	for idxnum, chttype in enumerate(cdtype):
	
		contentdir = outdir + "/" + nmtype[idxnum]
		if not os.path.exists(contentdir):
			os.mkdir(contentdir)
			print "created: " + contentdir
		cheatwriter( baseurl=baseurl, chttype=chttype, outdir=contentdir )

