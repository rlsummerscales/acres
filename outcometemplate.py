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
# class definition for an outcome template
#############################################

class Outcome(BaseMentionTemplate):
  """ manage all information relevant to an outcome mention. """
  __annotatedPolarityIsBad = True    # is the outcome good or bad? (default is bad)
  __annotatedIsPrimaryOutcome = False  # is the outcome really a primary outcome
  __hasPrimaryOutcomeLabel = False
  numbers = []    # list of outcome number templates
  summaryStats = []  # list of summary statistics for this outcome
  unusedNumbers = []  # numbers not used in summary stats
  eventrates = []
  isReferring = False
  primaryOutcomeId = None
  primaryOutcomeEvaluation = None
  badOutcomeLemmas = set(['adverse','sick','injury', 'die', 'death', 'mortality', \
                          'problem','condition', 'disease','recurrence','incidence'])
  goodOutcomeLemmas = set(['recover','cure','quit','stop'])
  __outcomeLemmas = set(['primary', 'secondary', 'composite', 'end', 'point', 'endpoint', 'outcome'])
  
  
  def __init__(self, mention, useAnnotations=False):
    """ initialize outcome template given a outcome mention """
    BaseMentionTemplate.__init__(self, mention, 'outcome', useAnnotations)
    self.numbers = []
    self.unusedNumbers = []
    self.eventrates = []
    self.summaryStats = []
    self.__annotatedIsPrimaryOutcome = False
    self.__hasPrimaryOutcomeLabel = False
    self.__annotatedPolarityIsBad = True
    self.primaryOutcomeId = ''
    self.primaryOutcomeEvaluation = Evaluation()
    self.isReferring = False
    # check annotation (if any) to see if outcome is good or bad
    polarity = ''
    for token in self.mention.tokens:
      if self.__annotatedIsPrimaryOutcome == False:
        focus = token.getAnnotationAttribute(self.type, 'focus')
        if focus == 'primary':
          self.__annotatedIsPrimaryOutcome = True
           
      if useAnnotations == False and token.hasLabel('primary_outcome'):
        # token was identified as part of a primary outcome by the primary outcome finder
        self.__hasPrimaryOutcomeLabel = True        
#        self.primaryOutcomeId = token.getLabelAttribute('primary_outcome', 'id')
#        if self.isReferring == False and token.hasLabel('referring_outcome'):
#          self.isReferring = True
        
      if len(polarity) == 0:
        polarity = token.getAnnotationAttribute(self.type, 'type')
        if polarity == 'good':
          self.__annotatedPolarityIsBad = False
  
  def isPrimary(self, useAnnotated=False):
    """ is the outcome a primary outcome? """
    if useAnnotated:
      return self.__annotatedIsPrimaryOutcome
    else:
      return self.__hasPrimaryOutcomeLabel
    
  def isGenericMention(self):
    """ return True if this mention is a generic primary/secondary outcome mention, e.g. "primary outcome", "secondary end points" """
    mentionLemmas = self.mention.interestingLemmas()
    nonGenericLemmas = mentionLemmas - self.__outcomeLemmas
    return len(nonGenericLemmas) == 0 

  def outcomeIsBad(self, useAnnotatedPolarity=False):
    """ use rules to determine if the outcome is good or bad """
    if useAnnotatedPolarity:
      if self.__annotatedPolarityIsBad == False:
        return False
#       for child in self.children:
#         if child.outcomeIsBad() == False:
#           return False
      return True
    else:
      for token in self.mention.tokens:
        if token.lemma in self.badOutcomeLemmas:
          for uc in token.umlsConcepts:
            if uc.isNegated:
              return False  # bad outcome term is negated
          return True
        elif token.lemma in self.goodOutcomeLemmas:
          for uc in token.umlsConcepts:
            if uc.isNegated:
              return True  # good outcome term is negated
          return False  # outcome term is good and not negated
      return True      # assume outcome was bad
        
             
  def getCanonicalName(self):
    """ return the canonical name for the mention cluster """
    if self.isReferring:
      for child in self.children:
        if child.isReferring == False:
          return child.name
    return self.name
      
  def mergeMentionData(self, mTemplate):
    """ merge the mention specific data from a given mention with this mention.
         This mention (self) is the root mention.  """
    # self should be the root mention     
    if self.isRootMention == False:
      raise StandardError('mergeMentionData() called outside of merge()')

    # add outcome number templates that are not already in this templates list
    for onTemplate in mTemplate.numbers:
      if onTemplate not in self.numbers:
        self.numbers.append(onTemplate)
      onTemplate.outcome = self
    
    for omTemplate in mTemplate.unusedNumbers:
      if omTemplate not in self.unusedNumbers:
        self.unusedNumbers.append(omTemplate)
        omTemplate.addOutcome(self)
    
    for ssTemplate in self.summaryStats:
      if ssTemplate not in self.summaryStats:
        self.summaryStats.append(ssTemplate)
        ssTemplate.addOutcome(self)
    
    if mTemplate.isPrimary():
      self.__hasPrimaryOutcomeLabel = True
    if mTemplate.isPrimary(useAnnotated=True):
      self.__annotatedIsPrimaryOutcome = True
      
  def copyDataFromParent(self):
    """ copy the mention specific data from the parent mention """
    if self.parent == None:
      return
    
    self.numbers = self.parent.numbers
    self.summaryStats = self.parent.summaryStats
    self.unusedNumbers = self.parent.unusedNumbers
    if self.parent.isPrimary():
      self.__hasPrimaryOutcomeLabel = True
    if self.parent.isPrimary(useAnnotated=True):
      self.__annotatedIsPrimaryOutcome = True


  def setId(self, id):
    """ set the ID for this outcome """
    id = 'o'+id
    BaseMentionTemplate.setId(self, id)
       
  