#!/usr/bin/python
# author: Rodney Summerscales

from rulebasedfinder import RuleBasedFinder

######################################################################
# Time phrase finder
######################################################################

class TimeFinder(RuleBasedFinder):
  """ Find and label time phrases.
      """
  label = 'time'
  
  def __init__(self):
    """ Create a finder that identifies TIME phrases. All tokens in 
        time phrases are labeled 'time'.
    """
    RuleBasedFinder.__init__(self, [self.label])
              
  def applyRules(self, token):
    """ Give all tokens in a given phrase, the label 'time' if token
        matches following rules.
        
        NUMBER  UNITS_OF_TIME
        baseline [follow-up]
        
        """
    if token.hasLabel(self.label) == True:
      # token has already been labeled
      return
              
    if token.isTimeUnitWord():   
      if token.text == 'baseline' or token.lemma == 'baseline':
        token.addLabel(self.label)
        
      nextToken = token.nextToken()
      if nextToken != None and nextToken.text == 'follow-up':
        token.addLabel(self.label)
          
      prevToken = token.previousToken()
      if prevToken != None:
        if prevToken.isNumber():
          prevToken.addLabel(self.label)
          token.addLabel(self.label)
          

      
  
