#!/usr/bin/python
# author: Rodney Summerscales

from rulebasedfinder import RuleBasedFinder
from dictionaryfinder import DictionaryFinder

######################################################################
# Population finder
######################################################################

class PopulationFinder(RuleBasedFinder):
  """ Find and label tokens in phrase describing a population in a trial 

      """
  label = 'population'
#  popWordFinder = None
  
  def __init__(self):
    """ Create a finder that identifies population phrases. All tokens in 
        the phrases are labeled 'population'.
    """
    RuleBasedFinder.__init__(self, [self.label])
#    self.popWordFinder = DictionaryFinder(self.label, wordFilename)
              
  def applyRules(self, token):
    """ Label the given token as a 'population'. Also label all of the neighboring 
        tokens in the same phrase.
        """
    pass   # for now we do nothing and rely on the "people" semantic tag for this info
    
#     if token.hasLabel(self.label) == True:
#       # token has already been labeled
#       return
#     
#     if 'people' in token.semanticTags:
#       token.addLabel(self.label)
        
  
            
          
      
  
