#!/usr/bin/python
# author: Rodney Summerscales

import sys
import glob
#import nltk
#from nltk.corpus import wordnet as wn
import xml.dom
from xml.dom import minidom
from xml.dom.minidom import Document
import xmlutil

from abstract import Abstract

if len(sys.argv) < 3:
  print "Usage: meshlist.py <INPUT_PATH> <OUTPUT_FILE>"
  print "output list of mesh terms for all abstracts"
  print "in the directory specified by <INPUT_PATH>"
  sys.exit()

  
inputPath = sys.argv[1]
fileList = glob.glob(inputPath+'/*.xml')
meshTerms = set([])

for filename in fileList:
  print filename
  xmldoc = minidom.parse(filename)
  dNodes = xmldoc.getElementsByTagName('DescriptorName')
  for node in dNodes:
    meshTerms.add(xmlutil.getText(node).lower())
#   abs = Abstract(filename)
#   for meshHeading in abs.meshHeadingList:
#     meshTerms.add(meshHeading.descriptorName.name.lower())
    
meshTerms = sorted(list(meshTerms))    
out = open(sys.argv[2], 'w')
for term in meshTerms:
  out.write(term+'\n')
  
out.close()
  
