#!/usr/bin/python
# author: Rodney Summerscales

from basementionfinder import BaseMentionFinder

######################################################################
# Rule-based based finder
######################################################################

class RuleBasedFinder(BaseMentionFinder):
  """ Label tokens if they satistfy predefined rules.
      """
  
  def __init__(self, entityTypes):
    """ Create a finder that labels tokens using rules
        entityTypes = the mention types to find (e.g. group, outcome)
    """
    BaseMentionFinder.__init__(self, entityTypes, tokenClassifier=None)
    
  
  def train(self, absList, modelFilename):
    """ (Does nothing. Finder is rule-based, there is nothing to train.) """
    pass    # nothing to train
    
  def test(self, absList, modelFilename, fold=None):
    """ Apply the mention finder to a given list of abstracts
        using the given model file.
    """  
    for abs in absList:
      for sentence in abs.sentences:
        for token in sentence:
          self.applyRules(token)
          
  def applyRules(self, token):
    """ Label given token using rules. """
    raise NotImplementedError("Need to implement applyRules()")
     
  def computeFeatures(self, absList, mode):
    """ (Does nothing. Finder is rule-based, there is nothing to train.) """
    pass    # nothing to train
