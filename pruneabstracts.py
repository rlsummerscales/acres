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
  print "Usage: pruneabstracts.py <ABSTRACT_FILES>"
  print "Delete all abstracts in <ABSTRACT_FILES> that do not have trial registries."
  sys.exit()

nctCount = 0
nctPattern = re.compile('.*NCT\s*\d+.*')
registryList = []
registrySet = set([])

for i in range(1, len(sys.argv)):
  file = sys.argv[i]
  print file
  
  xmldoc = minidom.parse(file)
  idNodeList = xmldoc.getElementsByTagName('AccessionNumber')
  hasRegistry = False
  for node in idNodeList:
    id = xmlutil.getText(node)    
    if len(id) > 3 and id[0:3] == 'NCT':
      hasRegistry = True
  if hasRegistry == False:
    print 'Deleting:', file
    os.remove(file)
  else:
    print 'Registry =', id
    nctCount += 1
    registrySet.add(id)
    registryList.append(id)
    
print 'NCT count:', nctCount
print 'Registry count:', len(registryList), len(registrySet)
