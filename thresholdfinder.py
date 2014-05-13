#!/usr/bin/python
# author: Rodney Summerscales

from rulebasedfinder import RuleBasedFinder

######################################################################
# Threshold finder
######################################################################

class ThresholdFinder(RuleBasedFinder):
  """ Find and label tokens in phrase describing a threshold 
      e.g. 'less than 5', 'greater than 24'
      """
  timeWords = set(['s', 'sec', 'second', 'min', 'minute', 'hr', 'hrs', \
               'hour', 'day', 'wk', 'wks', 'week', 'month', 'yr', 'yrs', \
               'year', 'baseline'])
  label = 'threshold'
  
  def __init__(self):
    """ Create a finder that identifies threshold phrases. All tokens in 
        time phrases are labeled 'threshold'.
    """
    RuleBasedFinder.__init__(self, [self.label])
              
  def applyRules(self, token):
    """ Label the given token as a 'threshold'. Also label all of the neighboring 
        tokens in the same phrase.
        
        """
    pass  # do not recognize thresholds at this point. 
          # we do not do anything productive with them right now
    
#     if token.hasLabel(self.label) == True:
#       # token has already been labeled
#       return
#     
#     if token.text != 'greater' and token.text != 'less':
#       return
#     
#     nextToken = token.nextToken()
#     if nextToken == None or nextToken.text != 'than':
#       return     
# 
#     prevToken = token.previousToken()
#     if prevToken == None or prevToken.text.lower() == 'p':
#       return
# 
#     nextNextToken = nextToken.nextToken()
#     if nextNextToken == None or nextNextToken.isNumber() == False:
#       return 
#       
#     token.addLabel(self.label)
#     nextToken.addLabel(self.label)
#     nextNextToken.addLabel(self.label)
#     
#     # so far we have 'greater/less' 'than', check if parent phrase
#     # is a quantifier phrase
#     if token.parseTreeNode != None and token.parseTreeNode.parent != None \
#       and token.parseTreeNode.parent.parent != None \
#       and token.parseTreeNode.parent.parent.parent != None:
#       for ptNode in token.parseTreeNode.parent.parent.parent.tokenNodes():
#         ptNode.token.addLabel(self.label)
#         
    
            
          
      
  
