#!/usr/bin/python
# author: Rodney Summerscales

from rulebasedfinder import RuleBasedFinder

######################################################################
# Dictionary based finder
######################################################################

class DictionaryFinder(RuleBasedFinder):
  """ Label words based on their presence in a list of words.
      """
  wordSet = None
  
  def __init__(self, entityType,  dictionaryFilename):
    """ Create a finder that labels tokens with a given type if they appear
        in a list of words.
        entityType = the mention types to find (e.g. group, outcome)
        dictionaryFilename = the path of the file containing the list of words
    """
    RuleBasedFinder.__init__(self, [entityType])
    self.wordSet = set([])
    lines = open(dictionaryFilename, 'r').readlines()
    for line in lines:
      self.wordSet.add(line.strip())
              
  def applyRules(self, token):
    """ Label given token if it appears in a list of words """
    if token.text in self.wordSet or token.lemma in self.wordSet:
      token.addLabel(self.entityTypes[0])
  
