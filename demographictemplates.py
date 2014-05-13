#!/usr/bin/python
# author: Rodney Summerscales


import nltk
import numpy
import xmlutil
import sys
import math

from nltk.corpus import stopwords
from basementiontemplate import BaseMentionTemplate
from basetemplate import Evaluation



#############################################
# Template for population description
#############################################

class Population(BaseMentionTemplate):
  """ Contains a description of the participants in the study """
  genericWords = set(['patients', 'participant', 'participants', 'subjects', \
                   'subject', 'people', 'persons', 'person', 'individuals', \
                   'individual', 'users', 'user', 'clients', 'client', \
                   'volunteers', 'volunteer'])

  def __init__(self, mention):
    """ initialize population template given a population mention """
    BaseMentionTemplate.__init__(self, mention, 'population')

  def isInteresting(self):
    """ return True if the population mention is informative and not generic """
    words = self.mention.interestingWords()
    if len(words-self.genericWords) > 0:
      return True
    else:
      return False

  def mergeMentionData(self, mTemplate):
    """ merge the mention specific data from a given mention with this
        mention """
    pass

  def copyDataFromParent(self):
    """ copy the mention specific data from the parent mention """
    pass
    
#############################################
# Template for common medical condition
#############################################

class Condition(BaseMentionTemplate):
  """ Contains information related to a common medical condition that 
      all subjects may have or may try to prevent """
  def __init__(self, mention, useAnnotations=False):
    """ initialize condition template given a condition mention """
    BaseMentionTemplate.__init__(self, mention, 'condition', useAnnotations)
 
  def mergeMentionData(self, mTemplate):
    """ merge the mention specific data from a given mention with this
        mention """
    pass

  def copyDataFromParent(self):
    """ copy the mention specific data from the parent mention """
    pass

  def setId(self, id):
    """ set the ID for this condition """
    id = 'c'+id
    BaseMentionTemplate.setId(self, id)
    


#############################################
# class definition for a location template
#############################################

class Location(BaseMentionTemplate):
  """ Contains information related to the location phrase that describes
      where the trial took place. 
  """
  
  def __init__(self, mention):
    """ initialize population template given a population mention """
    BaseMentionTemplate.__init__(self, mention, 'location')

  def mergeMentionData(self, mTemplate):
    """ merge the mention specific data from a given mention with this
        mention """
    pass

  def copyDataFromParent(self):
    """ copy the mention specific data from the parent mention """
    pass
