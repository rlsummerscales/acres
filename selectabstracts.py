#!/usr/bin/python
# author: Rodney Summerscales

import sys
#import nltk
#from nltk.corpus import wordnet as wn
import shutil
import os
import glob
import random

from abstractlist import AbstractList

if len(sys.argv) < 2:
  print "Usage: selectabstracts.py <INPUT_PATH>"
  print "Randomly select abstracts for evaluation from abstract in <INPUT_PATH>"
  sys.exit()

random.seed(13)

inputPath = sys.argv[1]
absList = AbstractList(inputPath, loadRegistries=False)

structuredAbstracts = []
unstructuredAbstracts = []
abstractIds = []

for abstract in absList:
  abstractIds.append(abstract.id)
#   nLabels = 0
#   curLabel = ''
#   for sentence in abstract.sentences:
#     if sentence.section != curLabel:
#       curLabel = sentence.section
#       nLabels += 1
#   if nLabels > 1:
#     print 'STRUCTURED:', abstract.id
#     structuredAbstracts.append(abstract.id)
#   else:
#     print 'UNSTRUCTURED:', abstract.id
#     unstructuredAbstracts.append(abstract.id)

#random.shuffle(structuredAbstracts)
random.shuffle(abstractIds)
startIdx = 1
endIdx = 10
out = open('abstracts10.sql','w')
out.write('INSERT INTO `abstract` (`id`, `entry_id`, `abstract_id`, `summary_id`) VALUES\n')
for i in range(startIdx, endIdx+1):
  absId = abstractIds[i-1]
  print absId
  out.write('(%d, %d, %s, \'%s.summary.xml\')'%(i, i, absId, absId))
  if i == endIdx:
    out.write(';\n')
  else:
    out.write(',\n')

out.close()  
  
