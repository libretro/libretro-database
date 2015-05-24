from lxml import html
import sys
import requests
import os
import re



def cheatwriter( baseurl, chttype, outdir ):
	page = requests.get(baseurl + chttype)
	tree = html.fromstring(page.text)
#urls and game names to be used as file names	
	gameurl = tree.xpath('//td[@class="codedescalt"]//a/@href')
	chtfilenames = [re.sub('[^0-9a-zA-Z\s]+', '', nogo).replace('  ', ' ').rstrip().lstrip() for nogo in tree.xpath('//td[@class="codedescalt"]/a[@href]/text()')]

	for number, codepage in enumerate(gameurl):
		outfile = outdir + '/' + chtfilenames[number] + '.cht'

		page = requests.get(baseurl + codepage)
		tree = html.fromstring(page.text)
	

		code=[]
#This will create a list of code descriptions
		codedesc = [x.encode('UTF8') for x in tree.xpath('//td[@class="codedesc"]/text()')]
#This will create a list of codes and format them for the outfile
		for td in tree.xpath('//tr/td[@class="code"][last()]'):
			hacker = td.text
			code.append('+'.join(
    	    text.replace('\n', '').replace(' ', '+') for text in td.getprevious().itertext()))
		
		codesamount = len(codedesc)
		codes = [dubplus.replace('++', '+') for dubplus in code]

		
		
#writes the codes
		if codesamount == 0:
			continue
		target = open(outfile, 'wb')
		target.write("cheats = {0} \n\n".format(codesamount))
		print "writing %s" % (outfile)
		try:
			for idx, val in enumerate(codes):
				target.write("cheat%d_desc = \" %s\"\n" % (idx, codedesc[idx]))
				target.write("cheat%d_code = \"%s\"\n" % (idx, val))
				target.write("cheat%d_enable = false \n" % (idx))
				target.write('\n')
			
			print "finished writing %s" % (outfile)
		except Exception:
			pass
			print "error writing " + outfile
	return;


