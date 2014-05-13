#!/usr/bin/python
# author: Rodney Summerscales

import sys
import shutil
import os.path
import glob

import xml.dom
from xml.dom import minidom
from xml.dom.minidom import Document
import nltk
from nltk.tokenize.treebank import TreebankWordTokenizer
import xmlutil

if len(sys.argv) < 4:
  print "Usage: filterabstracts.py <INPUT_PATH> <OUTPUT_PATH> <IGNORE_FILE>"
  print "Read MEDLINE XML abstracts in the directory specified by <INPUT_PATH>"
  print "Copy those abstracts that contain at least 4 integers to <OUTPUT_PATH>"
  print "Ignore abstracts found in the file <IGNORE_FILE>"
  sys.exit()
    
inputPath = sys.argv[1]
outputPath = sys.argv[2]
ignoreFile = sys.argv[3]
if inputPath[-1] != '/':
  inputPath += '/'
if outputPath[-1] != '/':
  outputPath += '/'

tokenizer = TreebankWordTokenizer()
ignoreSet = set([])
file = open(ignoreFile, 'r')
for line in file.readlines():
  [pmid, xml] = line.split('.')
  ignoreSet.add(pmid)

fileList = glob.glob(inputPath+'*.xml')
for filename in fileList:  
  i = 0
  xmldoc = minidom.parse(filename)
  pmidNodes = xmldoc.getElementsByTagName('PMID')
  pmid = xmlutil.getText(pmidNodes[0])
  if pmid in ignoreSet:
    print pmid, 'already annotated'
  else:
    textNodeList = xmldoc.getElementsByTagName('AbstractText')
    for textNode in textNodeList:
      text = xmlutil.getText(textNode)
      tokens = tokenizer.tokenize(text)
      for token in tokens:
        if token.isdigit():
          i += 1
    if i > 3:
      # copy abstract
      shutil.copy(filename, outputPath)  
