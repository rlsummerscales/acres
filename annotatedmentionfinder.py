#!/usr/bin/python
# author: Rodney Summerscales

from rulebasedfinder import RuleBasedFinder

class AnnotatedMentionFinder(RuleBasedFinder):
  """ Label words with their mention annotations. This finder is for comparison only.
      It should result in perfect recall and precision.
      """
  
  def __init__(self, entityTypes):
    """ Create a finder that labels tokens with a given type if they have this annotation.
        entityType = the mention types to find (e.g. group, outcome)
    """
    RuleBasedFinder.__init__(self, entityTypes)
              
  def applyRules(self, token):
    """ Label given token if it appears in a list of words """
    for type in self.entityTypes:
      if token.hasAnnotation(type):
        token.addLabel(type)
  
