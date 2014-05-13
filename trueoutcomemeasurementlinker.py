#!/usr/bin/python
# author: Rodney Summerscales
# associate event rates and outcome numbers

import os
import math

from operator import attrgetter 

from outcomemeasurementlinker import RuleBasedOutcomeMeasurementLinker
from outcomemeasurementtemplates import OutcomeMeasurement

#######################################################################
# class definition for object that associates mentions with quantities
#######################################################################
    
class TrueOutcomeMeasurementLinker(RuleBasedOutcomeMeasurementLinker):
  """ train/test system that associates event rates and outcome numbers in a sentence """
  
  def __init__(self):
    """ create a new mention-quantity associator given a specific mention type
        and quantity type. """
    RuleBasedOutcomeMeasurementLinker.__init__(self)
    self.useLabels = True
      
  def train(self, absList, modelFilename):
    """ Train an outcome measurement associator model given a list of abstracts """
    pass
       
  def test(self, absList, modelFilename, fold=None):
    """ Apply the outcome measurement associator to a given list of abstracts
        using the given model file.
        """
    # chose the most likely association for each value
    for abs in absList:
      for s in abs.sentences:
        self.linkTemplates(s)
  

  # use rule-based approach to find associations
  def linkTemplates(self, sentence):
    """ link value template to best matching mention template in the same sentence.
        It is assumed that mention clustering has not occurred yet.
        """
    templates = sentence.templates
    onList = templates.getList('on')
    erList = templates.getList('eventrate')
              
    omList = []      
    unmatchedER = []
    unmatchedON = []
    for er in erList:
      for on in onList:
        if on.shouldBelongToSameOutcomeMeasurement(er):
          om = OutcomeMeasurement(on)
          om.addEventRate(er)
          omList.append(om)
#          print '&&&&&&& Associating:', on.value, er.value, on.outcomeMeasurement, er.outcomeMeasurement
#          print er.outcomeNumber, on.textEventrate
          break

               
      if er.outcomeNumber == None:
        unmatchedER.append(er)
#        om = OutcomeMeasurement(er)
#        omList.append(om)
    # create outcome measurement templates lone on templates    
    for on in onList:
      if on.textEventrate == None:
        unmatchedON.append(on)
#        om = OutcomeMeasurement(on)
#        omList.append(om)
     
    for er in unmatchedER:
      if er.outcomeNumber == None:
        # eventrate still not matched, create outcome measurement just for it
        om = OutcomeMeasurement(er)
        omList.append(om)
                  
    for on in unmatchedON:
      if on.textEventrate == None:
        # outcome number still not matched, create outcome measurement just for it
        om = OutcomeMeasurement(on)
        omList.append(om)
                 
#    for om in omList:
#      om.display()
    sentence.templates.addOutcomeMeasurementList(omList)
        
  
    
