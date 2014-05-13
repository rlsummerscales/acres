#!/usr/bin/python
# author: Rodney Summerscales

from basetemplate import BaseTemplate

##############################################
# Base class definition for all QUANTITY templates
##############################################
   
class BaseQuantityTemplate(BaseTemplate):
  value = -1     # quantity value
  token = None   # token object containing the quantity
  time = None    # time when quantity was measured

  
  def __init__(self, token, quantityType):
    """ initialize template given a token containing a quantity """
    BaseTemplate.__init__(self, quantityType)
    self.token = token
    self.time = None
    self.start = self.token.index
    self.end = self.token.index
    self.value = token.getValue()

  def getSentence(self):    
    """ return sentence containing this token """
    return self.token.sentence
  
  def correctAssociation(self, mType):
    """ return True if quantity is correctly associated 
        with mention of given type. """
    raise NotImplementedError("Need to implement correctAssociation()")
    
  def isTruePositive(self):
    """ return True if this value is correctly labeled """
    return self.token.hasAnnotation(self.type)
    
  def shouldBeAssociated(self, mTemplate):
    """ return true if this quantity template should be associated with
        a given mention template. """
    mId = mTemplate.getAnnotatedId()
    vId = self.token.getAnnotationAttribute(self.type, mTemplate.type)
    if len(mId) > 0 and len(vId) > 0 and vId == mId:
      return True
    else:
      return False

  def isInSameSentence(self, mTemplate):
    """ return True if this quantity is in same sentence as one of the mention 
        in the mention template """
    s = self.token.sentence
    if mTemplate.mention.tokens[0].sentence == s:
      return True
    else:
      for child in mTemplate.children:
        if child.mention.tokens[0].sentence == s:
          return True
        
    return False
  
  def toString(self):
    """ return a string containing all relevant info for this value """
    raise NotImplementedError("Need to implement toString()")
  