#!/usr/bin/python
# author: Rodney Summerscales

import os
import traceback
import math
from operator import attrgetter 

from baseassociator import BaseOutcomeMeasurementAssociator
from baseassociator import OutcomeMeasurementAssociation

from statlist import StatList
from finder import EntityStats



#######################################################################
# class definition for object that associates mentions with eventrates and outcome numbers
#######################################################################

class TrueOutcomeMeasurementAssociator(BaseOutcomeMeasurementAssociator):
  """ train/test system that associates eventrates and outcome numbers with groups and outcomes """
  
  
  def __init__(self):
    """ create a new group size, group associator. """
    BaseOutcomeMeasurementAssociator.__init__(self, useLabels=False)
    self.finderType = 'true-om-associator'
    
    
  def train(self, absList, modelFilename):
    """ Train a mention-quantity associator model given a list of abstracts """
    pass
       
  def test(self, absList, modelFilename, fold=None):
    """ Apply the mention-quantity associator to a given list of abstracts
        using the given model file.
        """
    self.statList.clear()    

    # chose the most likely association for each value
    self.associationList = {}         # list of (G,O, OM) associations made
    self.incompleteMatches = {}
    for abstract in absList:
      for s in abstract.sentences:
        self.linkTemplates(s)
      


    
  def linkTemplates(self, sentence):
    """ link group size and outcome measurements with outcome and group templates using annotated information"""
#    print 'linking all templates'
    templates = sentence.templates
    gsList = templates.getList('gs')
    omList = templates.getOutcomeMeasurementList()
    groupList = sentence.abstract.entities.lists['group']
    outcomeList = sentence.abstract.entities.lists['outcome']
       
    # link groups and group sizes
    for gs in gsList:
      for group in groupList:
        if gs.shouldBeAssociated(group):
          self.linkQuantityAndMention(gs, group, 1.0)
          
    omListComplete = []
    # link outcome measurements with outcomes and groups
    for om in omList:
      er = om.getTextEventRate()
      on = om.getOutcomeNumber()
      errorMsgs = []
      if er != None:
        omQuantity = er
      else:
        omQuantity = on
    
      om.display()
      for group in groupList:
        for outcome in outcomeList:            
          if omQuantity.shouldBeAssociated(group) and omQuantity.shouldBeAssociated(outcome) \
            and omQuantity.isInSameSentence(group) and omQuantity.isInSameSentence(outcome):
            # outcome measurement should be associated with this group/outcome pair
            if er != None:
              er.groupProb = 1.0
              er.outcomeProb = 1.0
        
            if on != None:
              on.groupProb = 1.0
              on.outcomeProb = 1.0
        
            om.addGroup(group)
            om.addOutcome(outcome)
            if om.eventRate() != None:
              abstract = group.getAbstract()
              if abstract not in self.associationList:
                self.associationList[abstract] = []
              self.associationList[abstract].append(OutcomeMeasurementAssociation(group, outcome, om, 1.0))
              omListComplete.append(om)
    templates.addOutcomeMeasurementList(omListComplete)

