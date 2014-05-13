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
    
class TrueMentionQuantityAssociator(BaseMentionQuantityAssociator):
  """ Associate mentions with quantities in a sentence using annotated information.
      Uses true associations found in the annotations of the mentions and quantities
       """
  
  def __init__(self, mentionType, quantityType, useLabels=True):
    """ create a new mention-quantity associator given a specific mention type
        and quantity type. """
    BaseMentionQuantityAssociator.__init__(self, mentionType, quantityType, \
                                           useLabels)
      
  def train(self, absList, modelFilename):
    """ Does nothing. There is no model to train. """
    pass 
         
  def test(self, absList, modelFilename, fold=None):
    """ Apply the mention-quantity associator to a given list of abstracts
        using the given model file.
        """
        
    # link quantities with the mention that they should be associated with.
    # this assumes that the mention was correctly detected
    for abs in absList:
      for s in abs.sentences:
        self.linkTemplates(s)

  def computeTemplateFeatures(self, templates, mode=''):
    """ compute classifier features for each mention-quantity pair in 
        a given sentence in an abstract. """
    pass

  def linkTemplates(self, sentence):
    """ link value template to best matching mention template in the same sentence"""
    # sort feature vectors by probability
    templates = sentence.templates

    for qTemplate in templates.getList(self.quantityType):    
      for mTemplate in templates.getList(self.mentionType):
        if qTemplate.shouldBeAssociated(mTemplate):
          if self.mentionType == 'outcome' and self.quantityType == 'on':
            # outcome number not currently linked to any outcome, link it
            qTemplate.outcome = mTemplate
            qTemplate.outcomeProb = 1.0
            mTemplate.numbers.append(qTemplate)
            break
          elif self.mentionType == 'group' and self.quantityType == 'gs':
            # group & group size both unlinked, link them to each other
            qTemplate.group = mTemplate
            qTemplate.groupProb = 1.0
            mTemplate.addSize(qTemplate)
            break
          elif self.mentionType == 'group' and self.quantityType == 'on':
            # outcome number is not linked to any group, check if this one works
            qTemplate.group = mTemplate
            qTemplate.groupProb = 1.0
    
            mTemplate.outcomeNumbers.append(qTemplate)
            if qTemplate.groupSize != None:
              gsTemplate = qTemplate.groupSize
              gsTemplate.group = mTemplate
              mTemplate.addSize(gsTemplate)
            break

#             oTemplate = qTemplate.outcome
#             foundOutcome = False
#             # make sure that the group does not already have a number 
#             # for this outcome
#             if oTemplate != None:
#               for onTemplate in mTemplate.outcomeNumbers:
#                 if onTemplate.outcome == oTemplate:
#                   # this group already has an outcome number for this 
#                   # outcome number's outcome
#                   foundOutcome = True
#                   break
#             if foundOutcome == False:
#               # no number for this outcome, link group and outcome number
#               qTemplate.group = mTemplate
#               qTemplate.groupProb = 1.0
#       
#               mTemplate.outcomeNumbers.append(qTemplate)
#               if qTemplate.groupSize != None:
#                 gsTemplate = qTemplate.groupSize
#                 gsTemplate.group = mTemplate
#                 mTemplate.addSize(gsTemplate)
#               break
          elif self.mentionType == 'group' and self.quantityType == 'eventrate':
            # event rate not linked to a group, link it
            qTemplate.group = mTemplate
            qTemplate.groupProb = 1.0
            mTemplate.eventrates.append(qTemplate)
            break
          elif self.mentionType == 'outcome' and self.quantityType == 'eventrate':
            # event rate not currently linked to any outcome, link it
            qTemplate.outcome = mTemplate
            qTemplate.outcomeProb = 1.0
            break
      #        mTemplate.eventrates.append(qTemplate)
        
