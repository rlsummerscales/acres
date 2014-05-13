#!/usr/bin/python
# author: Rodney Summerscales
# add lemmas to each token

import sys

import nltk
from nltk.stem.wordnet import WordNetLemmatizer

from abstractlist import AbstractList

if len(sys.argv) < 2:
  print "Usage: lemmatizeabstracts.py <PATH>"
  print "Lookup lemmas for each token in a directory of abstracts."
  print "Modified files written to same directory"
  sys.exit()
  
absPath = sys.argv[1]
absList = AbstractList(absPath)

lemmatizer = WordNetLemmatizer()

for abs in absList:
  for sentence in abs.sentences:
    for token in sentence:
      if token.pos[0] == 'N':
        token.lemma = lemmatizer.lemmatize(token.text, 'n')
      elif token.pos[0] == 'V':
        token.lemma = lemmatizer.lemmatize(token.text, 'v')
      else:
        token.lemma = lemmatizer.lemmatize(token.text)

absList.writeXML(absPath, 'raw')