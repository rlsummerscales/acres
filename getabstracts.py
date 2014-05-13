#!/usr/bin/python
# author: Rodney Summerscales

import sys
import os.path
import urllib2

import xml.dom
from xml.dom import minidom
from xml.dom.minidom import Document

import xmlutil

eutils = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/'

# search for texts
# searchArgs = '&term="cardiovascular%20disease"[title]%20AND%20("humans"' \
#              +'[MeSH%20Terms]%20AND%20Randomized%20Controlled%20Trial' \
#              + '[ptyp])&cmd=DetailsSearch&retmax=500'
# searchArgs = '&term=("cardiovascular%20diseases"[MeSH%20Terms]%20OR%20' \
#              + '("cardiovascular"[All%20Fields]%20AND%20"diseases"[All%20Fields])'\
#              + '%20OR%20"cardiovascular%20diseases"[All%20Fields]' \
#              + '%20OR%20("cardiovascular"[All%20Fields]' \
#              + '%20AND%20"disease"[All%20Fields])' \
#              + '%20OR%20"cardiovascular%20disease"[All%20Fields])'\
#              + '%20AND%20("humans"[MeSH%20Terms]' \
#              + '%20AND%20Randomized%20Controlled%20Trial[ptyp]'\
#              + '%20AND%20jsubsetaim[text])' \
#              + '&cmd=DetailsSearch&retmax=500'
# #             '&term="cardiovascular%20disease AND (Humans[Mesh] AND Randomized Controlled Trial[ptyp] AND jsubsetaim[text])
searchArgs = '&term=("myocardial%20ischemia"[MeSH%20Terms]'\
             + '%20AND%20("humans"[MeSH%20Terms]' \
             + '%20AND%20Randomized%20Controlled%20Trial[ptyp]'\
             + '%20AND%20jsubsetaim[text])' \
             + '&cmd=DetailsSearch&retmax=500'
             
searchCmd = eutils + 'esearch.fcgi?db=pubmed'+ searchArgs
searchResults = urllib2.urlopen(searchCmd)

# parse results
xmldoc = minidom.parseString(searchResults.read())
idNodeList = xmldoc.getElementsByTagName('Id')
print 'Number of documents found =', len(idNodeList)

#idNodeList = open('abs.txt', 'r').readlines()

# download files
for idNode in idNodeList:
  print 'Fetching article with id =', id
#   id = idNode[:-1]
#   fetchCmd = 'http://www.ncbi.nlm.nih.gov/pubmed/'+id
#   doc = urllib2.urlopen(fetchCmd)
#   out = open(id+'.htm', 'w')

  id = xmlutil.getText(idNode)
  fetchCmd = eutils+'efetch.fcgi?db=pubmed&id='+id+'&retmode=xml&rettype=abstract'
  doc = urllib2.urlopen(fetchCmd)
  out = open(id+'.xml', 'w')

  out.write(doc.read())
  out.close()
