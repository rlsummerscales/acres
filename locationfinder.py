#!/usr/bin/python
# author: Rodney Summerscales

from rulebasedfinder import RuleBasedFinder

class LocationFinder(RuleBasedFinder):
  """ Label words that define a location 
      """
  label = 'location'
    
  def __init__(self):
    """ Create a finder that labels tokens with a given type if they appear 
        to be a location of a trial.
    """
    RuleBasedFinder.__init__(self, [self.label])
              
  def applyRules(self, token):
    """  Label the given token as a 'threshold'. """
    if token.hasLabel(self.label) == True:
      # token has already been labeled
      return
    
    if token.isLocation() \
       and token.sentence.index < len(token.sentence.abstract.allSentences()):
      token.addLabel(self.label)
  
