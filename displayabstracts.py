#!/usr/bin/python
# author: Rodney Summerscales

import sys
#import nltk
#from nltk.corpus import wordnet as wn

from abstractlist import AbstractList

if len(sys.argv) < 3:
  print "Usage: displayentities.py <ABSTRACT_PATH> <LABEL_1> <LABEL_2> ... <LABEL_N>"
  print "Output the entities with a given label for all of the abstracts in given path."
  sys.exit()

  
inputPath = sys.argv[1]
absList = AbstractList(inputPath)
labelList = sys.argv[2:]
out = open('abstracts.entities.txt', 'w')

for abstract in absList:
  out.write('---%s---\n' % abstract.id)
  for label in labelList:
    entityList = []
    for sentence in abstract.sentences:
      annotatedEntities = sentence.getAnnotatedMentions(label)
      if len(annotatedEntities) > 0:
        entityList += annotatedEntities
    if len(entityList) > 0:
      out.write('%s:\n' % label)
      for m in entityList:
        out.write('\t%s\n' % m.text)
     
out.close()