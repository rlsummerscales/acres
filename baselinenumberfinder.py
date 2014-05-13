import sys
import os.path
import nltk

from nltk.corpus import stopwords
from finder import EntityStats
from numberfinder import NumberFinder
      
######################################################################
# Experimental mention finder
######################################################################

class BaselineNumberFinder(NumberFinder):
  """ Used for training/testing a classifier to find mentions 
      in a list of abstracts.
      """

  def __init__(self, entityTypes):
    """ Create a new number finder to find a given list of number types using rules.
        entityTypes = list of number types to find (e.g. group, outcome)
    """
    NumberFinder.__init__(self, entityTypes, None)
    self.finderType = 'baseline-nf'

  def computeFeatures(self, absList, mode='train'):
    """ compute classifier features for each token in each abstract in a
        given list of abstracts. """
    pass
    
  def train(self, absList, modelfilename):
    """ Train a number finder model given a list of abstracts """
    pass
    
  def test(self, absList, modelfilename, fold=None):
    """ Apply the mention finder to a given list of abstracts
        using the given model file.
        """
    for abstract in absList:
      for sentence in abstract.sentences:
        # build list of numbers that should be classified 
        importantNumbers = []
        for token in sentence:
          if self.isImportantNumber(token):
            importantNumbers.append(token)
            
        for idx in range(0, len(importantNumbers)):
          token = importantNumbers[idx] 
          if token.isPercentage():
            token.addLabel('eventrate')
          else:
            pFeatures = self.numberPatternFeatures(token)  
            if 'p_outcomenumber' in pFeatures:
              token.addLabel('on')
            elif 'p_size' in pFeatures or 'p_groupsize' in pFeatures:
              token.addLabel('gs')
                           