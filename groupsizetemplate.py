#!/usr/bin/python
# author: Rodney Summerscales

from basequantitytemplate import BaseQuantityTemplate

#############################################
# class definition for an outcome template
#############################################

class GroupSize(BaseQuantityTemplate):
  """ manage the information relevant to a Group size template """
  group = None          # link to group template
  groupProb = 0.0       # probability that group should be associated with this value
  sentence = None       # sentence group size appears in
  outcome = None        # link to outcome template for outcome group size was associated with
  outcomeNumber = None  # group size was reported with an outcome number, e.g. '23 of 98 patients...' 
  
  def __init__(self, token):
    """ Initialize a group size template given an integer token object """
    BaseQuantityTemplate.__init__(self, token, 'gs')
    self.group = None
    self.groupProb = 0.0
    self.outcome = None
    self.sentence = token.sentence
    self.outcomeNumber = None

  def correctAssociation(self, mType):
    """ return True if quantity is correctly associated 
      with mention of given type. """
    if self.group == None:
      return -1     # no association can be made
    if self.shouldBeAssociated(self.group):
      return 1
    return 0
  
  def toString(self):
    """ return a string containing all relevant info for this value """
    s = str(self.value) + ', GROUP = '
    if self.group != None:
      s += self.group.name + ', '
    return s + ', prob = ' + str(self.groupProb)