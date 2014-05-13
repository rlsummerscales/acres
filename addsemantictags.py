#!/usr/bin/python
# author: Rodney Summerscales
# add semantic tags to each token in list of abstracts

import sys

from abstract import AbstractList
from dictionaryfinder import DictionaryFinder

class SemanticTagAnnotator(DictionaryFinder):
  """ This finder labels tokens with a semantic tag defined by a file of terms."""
  
  def __init__(self, entityType, dictionaryFilename):
    """ Create a finder that labels tokens with a given type if they appear
      in a list of words.
      entityType = the mention types to find (e.g. group, outcome)
      dictionaryFilename = the path of the file containing the list of words
    """
    DictionaryFinder.__init__(self, entityType, dictionaryFilename)

  def applyRules(self, token):
    """ Label given token if it appears in a list of words """
    if token.text in self.wordSet or token.lemma in self.wordSet:
      token.semanticTags.add(self.entityTypes[0])

if len(sys.argv) < 2:
  print "Usage: addsemantictags.py <PATH>"
  print "Add semantic tags to each token in a directory of abstracts."
  print "Modified files written to same directory"
  sys.exit()
  
absPath = sys.argv[1]
absList = AbstractList(absPath)

finders = []
finders.append(SemanticTagAnnotator('people', 'models/semantic/people.txt'))
finders.append(SemanticTagAnnotator('group', 'models/semantic/group.txt'))
finders.append(SemanticTagAnnotator('statistic', 'models/semantic/statistic.txt'))
finders.append(SemanticTagAnnotator('outcome', 'models/semantic/outcome.txt'))
finders.append(SemanticTagAnnotator('anatomy', 'models/semantic/anatomy.txt'))
#finders.append(SemanticTagAnnotator('disease', 'models/semantic/disease.txt'))
# disease file contains terms that are not diseases
finders.append(SemanticTagAnnotator('drug', 'models/semantic/drug.txt'))
finders.append(SemanticTagAnnotator('measurement','models/semantic/measurement.txt'))
finders.append(SemanticTagAnnotator('procedure','models/semantic/procedure.txt'))
finders.append(SemanticTagAnnotator('symptom','models/semantic/symptom.txt'))
finders.append(SemanticTagAnnotator('time','models/semantic/time.txt'))

for abs in absList:
  for sentence in abs.sentences:
    for token in sentence:
      for dFinder in finders:
        dFinder.applyRules(token)
        
absList.writeXML(absPath, 'raw')