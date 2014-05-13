#!/usr/bin/python
# author: Rodney Summerscales

import os
import traceback
import math
from operator import attrgetter 

from baseassociator import BaseOutcomeMeasurementAssociator
from baseassociator import FeatureVector
from baseassociator import OutcomeMeasurementAssociation
from baselinementionquantityassociator import BaselineMentionQuantityAssociator
from outcomemeasurementtemplates import OutcomeMeasurement
from findertask import FinderTask
from statlist import StatList
from finder import EntityStats

from munkres import Munkres, print_matrix, make_cost_matrix


#######################################################################
# class definition for object that associates mentions with eventrates and outcome numbers
#######################################################################

class BaselineOutcomeMeasurementAssociator(BaseOutcomeMeasurementAssociator):
  """ train/test system that associates eventrates and outcome numbers with groups and outcomes """
  
  probabilityEstimatorTasks = []
  
  def __init__(self, useLabels=True):
    """ create a new group size, group associator. """
    BaseOutcomeMeasurementAssociator.__init__(self, useLabels)
    self.finderType = 'baseline-om-associator'
    
    probEstimators = []
    for [mType, qType] in self.pairTypeList:
      finder = BaselineMentionQuantityAssociator(mType, qType, useLabels)
      probEstimators.append(finder)
    
    self.probabilityEstimatorTasks = []
    for finder in probEstimators:
      finderTask = FinderTask(finder)
      self.probabilityEstimatorTasks.append(finderTask)

    
  def train(self, absList, modelFilename):
    """ Train a mention-quantity associator model given a list of abstracts """
     
  def test(self, absList, modelFilename, fold=None):
    """ Apply the mention-quantity associator to a given list of abstracts
        using the given model file.
        """
    self.statList.clear()    
    for probEstTask in self.probabilityEstimatorTasks:
      probEstTask.test(absList, statOut=self.statList, fold=fold)

    # chose the most likely association for each value
    self.associationList = {}         # list of (G,O, OM) associations made
    self.incompleteMatches = {}
    for abstract in absList:
      for s in abstract.sentences:
        self.linkTemplates(s)
      
    
  def linkTemplates(self, sentence):
    """ link group size and group templates using Hungarian matching algorithm """
#    print 'linking all templates'
    templates = sentence.templates
    onList = templates.getList('on')
    erList = templates.getList('eventrate')

    abstract = sentence.abstract  
    if abstract not in self.incompleteMatches:
      self.incompleteMatches[abstract] = []                 
            
    omHash = {}
    for er in erList:
      if er.group != None and er.outcome != None:
        # remember the mention matched with the value
        # save this information in a feature vector to be retrieved in linkQuantityAndMention()
        fv = FeatureVector(-1, -1, None)
        fv.mTemplate = er.group
        fv.qTemplate = er
        er.addMatchFeatures(fv)
        fv = FeatureVector(-1, -1, None)
        fv.mTemplate = er.outcome
        fv.qTemplate = er
        er.addMatchFeatures(fv)
        
        groupEntity = er.group.rootMention()
        outcomeEntity = er.outcome.rootMention()
        
        er.group = None
        er.outcome = None

        om = OutcomeMeasurement(er)
        
        if (groupEntity, outcomeEntity) not in omHash:
          omHash[(groupEntity, outcomeEntity)] = om
                    
        elif omHash[(groupEntity, outcomeEntity)] != None:
          # there is already an outcome measurement for this group, outcome
          # check if this one is closer 
          # closer if it distance to closest mention is less
          #     if the same, use total distance
          #     if that is the same, use value that occurs earlier in sentence
          currentOM = omHash[(groupEntity, outcomeEntity)]
          current = currentOM.getTextEventRate()
          closest = self.closestValue(er, current)
          if closest == None:
            # both same distance, discard both
            omHash[(groupEntity, outcomeEntity)] = None
          elif closest == er:
            omHash[(groupEntity, outcomeEntity)] = om
            self.incompleteMatches[abstract].append(OutcomeMeasurementAssociation(groupEntity, outcomeEntity, currentOM, 0))
          else:
            self.incompleteMatches[abstract].append(OutcomeMeasurementAssociation(groupEntity, outcomeEntity, om, 0))
          
                    

    for on in onList:
      if on.group != None and on.outcome != None:
        fv = FeatureVector(-1, -1, None)
        fv.mTemplate = on.group
        fv.qTemplate = on
        on.addMatchFeatures(fv)
        fv = FeatureVector(-1, -1, None)
        fv.mTemplate = on.outcome
        fv.qTemplate = on
        on.addMatchFeatures(fv)
        
        groupEntity = on.group.rootMention()
        outcomeEntity = on.outcome.rootMention()

        on.group = None
        on.outcome = None
        
        # check if this ON is useful, can we compute an event rate with it?
        gs = on.getGroupSize()
        if gs > 0:
          # we can compute an event rate
          om = OutcomeMeasurement(on)
        
          if (groupEntity, outcomeEntity) not in omHash:
            omHash[(groupEntity, outcomeEntity)] = om 
                     
          elif omHash[(groupEntity, outcomeEntity)] != None:
            # there is already a outcome measurement
            currentOM = omHash[(groupEntity, outcomeEntity)]
            currentON = currentOM.getOutcomeNumber()
            currentER = currentOM.getTextEventRate()
            # check if this on should be merged with an event rate
            if currentON == None and currentER != None and on.equivalentEventRates(currentER.eventRate()):
              currentOM.addOutcomeNumber(on)
            else:
              # on not compatible with existing value
              # is it closer?
              if currentON != None and currentER != None:
                closestVal = self.closestValue(currentON, currentER)
                if closestVal == None:
                  # if both the same distance, just use the ER
                  closestVal = currentER
              elif currentON != None:
                closestVal = currentON
              else:
                closestVal = currentER
              
              closestVal = self.closestValue(closestVal, on)
              if closestVal == None:
                # both same distance, discard both
                omHash[(groupEntity, outcomeEntity)] = None
              elif closestVal == on:
                omHash[(groupEntity, outcomeEntity)] = om 
                self.incompleteMatches[abstract].append(OutcomeMeasurementAssociation(groupEntity, outcomeEntity, currentOM, 0))
              else:
                self.incompleteMatches[abstract].append(OutcomeMeasurementAssociation(groupEntity, outcomeEntity, om, 0))
                  
    omList = []                 
    for (group, outcome), om in omHash.items():
      if om != None:
        self.linkOutcomeMeasurementAssociations(om, group, outcome, 0.5)
        omList.append(om)
      
    sentence.templates.addOutcomeMeasurementList(omList)
    

  

  def closestValue(self, v1, v2):
    # return the value that is the closest to group/outcome pair
    # closer if it distance to closest mention is less
    #     if the same, use total distance
    #     if that is the same, return None
                  
    v1MaxProb = max(v1.groupProb, v1.outcomeProb)
    v2MaxProb = max(v2.groupProb, v2.outcomeProb)
    v1ProbSum = v1.groupProb + v1.outcomeProb
    v2ProbSum = v2.groupProb + v2.outcomeProb
    
    if v1MaxProb > v2MaxProb:
      return v2
    elif v1MaxProb < v2MaxProb:
      return v2
    else: 
      # i.e., v1MaxProb == v2
      if v1ProbSum > v2ProbSum:
        return v1
      elif v1ProbSum < v2ProbSum:
        return v2
      else:
        return None
#      else:
#        # i.e. prob sums the same, go with one that appears earlier
#        if v1.start < v2.start:
#          return v1
#        else:
#          return v2    

    

        

  
 