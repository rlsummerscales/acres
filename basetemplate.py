#!/usr/bin/python
# author: Rodney Summerscales
# class definitions for group, outcome, outcome number 
# and summary statistic templates

class Evaluation:
  """ An evaluation for a summary element """
  rating = None
  id = None
  
  def __init__(self):
    self.id = None
    self.rating = None
  
  def isComplete(self):
    """ return true if this evaluation has both a rating and an id """
    return self.rating != None and self.id != None
     
  def markCorrect(self):
    """ this element has been determined to be CORRECT """
    self.rating = 'Correct'

  def markIncorrect(self):
    """ this element has been determined to be INCORRECT """
    self.rating = 'Incorrect'

  def markQualitativelyCorrect(self):
    """ this element has been determined to be QUALITATIVELY CORRECT """
    self.rating = 'Qualitatively Correct'

  def markDuplicate(self):
    """ this element has been determined to be a DUPLICATE """
    self.rating = 'Duplicate'
  
  def isCorrect(self):
    return self.rating[0] == 'C'

  def isIncorrect(self):
    return self.rating[0] == 'I'
  
  def isQualitativelyCorrect(self):
    return self.rating[0] == 'Q'
  
  def isDuplicate(self):
    return self.rating[0] == 'D'
  
  def getRating(self):
    return self.rating
  
##############################################
# Base class definition for all templates
##############################################
class BaseTemplate:
  links = {}   # links to other templates
  type = ''    # type of template
  start = -1   # index of first token in mention
  end = -1     # index of last token in mention
  evaluation = None
   
  def __init__(self, type):
    self.links = {}
    self.type = type
    self.start = -1
    self.end = -1
    self.evaluation = Evaluation()
    
  def getAssociation(self, type):
    return self.links.get(type, None)
    
  def toString(self):
    """ return string describing this entity """
    return 'toString() undefined for type = '+self.type
  
  def getSentence(self):  
    """ return sentence containing tokens associated with this template """
    raise NotImplementedError("Need to implement getSentence()")
    
  def getAbstract(self):
    """ return the abstract containing tokens associated with this template """
    sentence = self.getSentence()
    if sentence != None:
      return sentence.abstract
    else:
      return None
  