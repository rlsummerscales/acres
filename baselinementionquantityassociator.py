#!/usr/bin/python
# author: Rodney Summerscales
# associate mentions with quantities

import os

from operator import attrgetter 

from baseassociator import BaseMentionQuantityAssociator
from baseassociator import FeatureVector

#######################################################################
# class definition for object that associates mentions with quantities
#######################################################################
    
class BaselineMentionQuantityAssociator(BaseMentionQuantityAssociator):
  """ train/test system that associates mentions with quantities in a sentence """
  
  def __init__(self, mentionType, quantityType, useLabels=True):
    """ create a new mention-quantity associator given a specific mention type
        and quantity type. """
    BaseMentionQuantityAssociator.__init__(self, mentionType, quantityType, \
                                           useLabels)
    self.finderType = 'baseline-assoc'
      
  def train(self, absList, modelFilename):
    """ Train a mention-quantity associator model given a list of abstracts """
    pass
         

  def test(self, absList, modelFilename, fold=None):
    """ Apply the mention-quantity associator to a given list of abstracts
        using the given model file.
        """
    # chose the most likely association for each value
    for abs in absList:
      for s in abs.sentences:
        self.linkTemplates(s)
  
  def computeTemplateFeatures(self, templates, mode=''):
    """ compute classifier features for each mention-quantity pair in 
        a given sentence in an abstract. """
    pass
  

  # use rule-based approach to find associations
  def linkTemplates(self, sentence):
    """ link value template to best matching mention template in the same sentence.
        It is assumed that mention clustering has not occurred yet.
        """
    templates = sentence.templates
    sLength = len(sentence.tokens)
    
    # find the closest mention to each value. 
    # In case of ties, use mention that appears before the quantity in sentence
    for qTemplate in templates.getList(self.quantityType):    
      (mTemplate, dist) = templates.closestMention(qTemplate, self.mentionType)
      if mTemplate != None:
        # use distance between elements to estimate association probability
        prob = 1.0 - float(dist)/sLength
        if self.mentionType == 'outcome':
          qTemplate.outcome = mTemplate
          qTemplate.outcomeProb = prob
        elif self.mentionType == 'group':
          qTemplate.group = mTemplate
          qTemplate.groupProb = prob
          if self.quantityType == 'gs':
            mTemplate.addSize(qTemplate)
          




 