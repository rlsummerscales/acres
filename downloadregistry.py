#!/usr/bin/python
# author: Rodney Summerscales

import sys
import os.path
import urllib2
import re
import xml.dom
from xml.dom import minidom
from xml.dom.minidom import Document

import xmlutil

if len(sys.argv) < 2:
  print "Usage: downloadregistry.py <FILES>"
  print "Download clinicaltrials.gov registry info"
  print "for each file in the list of files <FILES>"
  print "downloaded registry information is written to the file '<PMID>.nct.xml'" 
  sys.exit()

nctCount = 0
isrctnCount = 0
  
nctPattern = re.compile('.*NCT\s*\d+.*')

for i in range(1, len(sys.argv)):
  file = sys.argv[i]
  print file
  
  xmldoc = minidom.parse(file)
  idNodeList = xmldoc.getElementsByTagName('AccessionNumber')
  for node in idNodeList:
    id = xmlutil.getText(node)    
    if len(id) > 3 and id[0:3] == 'NCT':
      try:
#        fetchCmd = 'http://clinicaltrials.gov/show/'+id+'?resultsxml=true'
        fetchCmd = 'http://clinicaltrials.gov/show/'+id+'?displayxml=true'
        print 'Downloading:', fetchCmd
        doc = urllib2.urlopen(fetchCmd)
        out = open(id+'.xml', 'w')
        out.write(doc.read())
        out.close()
        nctCount += 1
      except:
        print '***Could not download:', fetchCmd
    elif len(id) > 6 and id[0:6] == 'ISRCTN':
      print id
      isrctnID = id
      isrctnCount += 1
    
print 'NCT count:', nctCount
print 'ISRCTN count:', isrctnCount
