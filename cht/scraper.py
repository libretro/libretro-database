from lxml import html
from sys import argv
import requests
import os

#cheat scraper for http://bsfree.shadowflareindustries.com/ navigate to the system and codetype you want, copy url
#run the script with "python scraper.py 'url'"

systempage = argv[1]
baseurl = 'http://bsfree.shadowflareindustries.com/'
outdir = argv[2]


page = requests.get(systempage)
tree = html.fromstring(page.text)

#urls and game names to be used as file names
url = tree.xpath('//td[@class="codedescalt"]//a/@href')
chtfilenames = [slash.replace('/', '_') for slash in tree.xpath('//td[@class="codedescalt"]/a[@href]/text()')]

for number, codepage in enumerate(url):
	outfile = outdir + chtfilenames[number] + '.cht'

	page = requests.get(baseurl + codepage)
	tree = html.fromstring(page.text)
	
	target = open(outfile, 'wb')
	code=[]
#This will create a list of code descriptions
	codedesc = [x.encode('UTF8') for x in tree.xpath('//td[@class="codedesc"]/text()')]
#This will create a list of codes
	for td in tree.xpath('//tr/td[@class="code"][last()]'):
		hacker = td.text
		code.append('+'.join(
        text.replace('\n', '') for text in td.getprevious().itertext()))

	codesamount = len(codedesc) -1
	
	print "writing %s" % (outfile)
	
	target.write("cheats = {0} \n\n".format(codesamount))

#writes the codes
	for idx, val in enumerate(codedesc):
		target.write("cheat%d_desc = \" %s\"\n" % (idx, val))
		target.write("cheat%d_code = \"%s\"\n" % (idx, code[idx].encode('utf')))
		target.write("cheat%d_enable = false \n" % (idx))
		target.write('\n')
	
	print "finished writing %s" % (outfile)

