#!/usr/bin/python
# author: Rodney Summerscales

import os
import traceback
import math
from operator import attrgetter 

from baseassociator import BaseOutcomeMeasurementAssociator
from baseassociator import FeatureVector
from baseassociator import OutcomeMeasurementAssociation
from mentionquantityassociator import MentionQuantityAssociator
from outcomemeasurementtemplates import OutcomeMeasurement
from findertask import FinderTask
from statlist import StatList
from finder import EntityStats

from munkres import Munkres, print_matrix, make_cost_matrix


#######################################################################
# class definition for object that associates mentions with eventrates and outcome numbers
#######################################################################

class OutcomeMeasurementAssociator(BaseOutcomeMeasurementAssociator):
  """ train/test system that associates eventrates and outcome numbers with groups and outcomes """
  
  probabilityEstimatorTasks = []
  
  def __init__(self, modelPath, useLabels=True, considerPreviousSentences=True):
    """ create a new group size, group associator. """
    BaseOutcomeMeasurementAssociator.__init__(self, useLabels)
    self.finderType = 'om-associator'
    
    probEstimators = []
    for [mType, qType] in self.pairTypeList:
      finder = OutcomeMeasurementPairProbabilityEstimator(mType, qType, considerPreviousSentences=considerPreviousSentences)
      probEstimators.append(finder)
    
    self.probabilityEstimatorTasks = []
    for finder in probEstimators:
      finderTask = FinderTask(finder, modelPath=modelPath)
      self.probabilityEstimatorTasks.append(finderTask)

    
  def train(self, absList, modelFilename):
    """ Train a mention-quantity associator model given a list of abstracts """
    for probEstTask in self.probabilityEstimatorTasks:
      probEstTask.train(absList)   
     
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
      


#  def getFeatureVectors(self, absList, forTraining):
#    """ Ignored. """
#    pass
#
#  def computeTemplateFeatures(self, templates, mode=''):
#    """ compute classifier features for each mention-quantity pair in 
#        a given sentence in an abstract. """
#    pass    

#  def groupOutcomeOverlap(self, group, outcome):
#    """ return True if there is unacceptable overlap between a group and outcome mention """
#    nMatched = 0
#    nUnmatched1 = 0
#    nUnmatched2 = 0
#        
#    groupLemmas = group.mention.interestingLemmas() 
#    outcomeLemmas = outcome.mention.interestingLemmas()
#    
#    nMatched = len(groupLemmas.intersection(outcomeLemmas))
#
#    nGroupLemmas = len(groupLemmas)
#    nOutcomeLemmas = len(outcomeLemmas)
#    if nMatched > 0 and float(nMatched)/nGroupLemmas > 0.74 and float(nMatched)/nOutcomeLemmas > 0.74:
#      return True
#    else:
#      return False
    
  def linkTemplates(self, sentence):
    """ link group size and group templates using Hungarian matching algorithm """
#    print 'linking all templates'
    templates = sentence.templates
    onList = templates.getList('on')
    erList = templates.getList('eventrate')
    outcomeMeasurements = templates.getOutcomeMeasurementList()
    groupList = sentence.abstract.entities.lists['group']
    outcomeList = sentence.abstract.entities.lists['outcome']
       
    nON = len(onList)
    nER = len(erList)
    nGroups = len(groupList)
    nOutcomes = len(outcomeList)
    nGroupOutcomePairs = nGroups * nOutcomes
    if (nON + nER) == 0 or nGroupOutcomePairs == 0:
      return  # missing key information cannot make any associations
     
    goPairs = []
    for group in groupList:
      for outcome in outcomeList:
#        goPairs.append((group,outcome))

        (nMatched, nUnmatched1, nUnmatched2) = group.partialSetMatch(outcome)

        if self.groupOutcomeOverlap(group, outcome) == False:
          # overlap between group/outcome may be no more than ONE word and this may be no more than 1/3 of smaller mention
          goPairs.append((group,outcome))
        else:
          print sentence.abstract.id, '#### skipping:', group.rootMention().name, ';', outcome.rootMention().name

    nGroupOutcomePairs = len(goPairs)
    if nGroupOutcomePairs == 0:
      return  # missing key information cannot make any associations

    
    # get unmatched event rates and outcome numbers
    unmatchedON = []    
    unmatchedER = []
    for om in outcomeMeasurements:
      on = om.getOutcomeNumber()
      er = om.getTextEventRate()
      if er != None and on == None: 
        # unmatched event rate 
        unmatchedER.append(er)
      elif on != None and er == None:
        # unmatched number of outcomes 
        unmatchedON.append(on)
    
    # identify as of yet unmatched event rates and outcome numbers that could potentially match each other    
    erMatches = {}
    onMatches = {}    
    for on in unmatchedON:
      onMatches[on] = []
    for er in unmatchedER:
      erMatches[er] = []
    
    for on in unmatchedON:
      couldCalculateER = False
      if on.hasAssociatedGroupSize():
        calculatedER = on.eventRate()
        couldCalculateER = True
        for er in unmatchedER:
          if er.equivalentEventRates(calculatedER):
            onMatches[on].append(er) 
            erMatches[er].append(on)      
      else:
        for group in groupList:
          groupFV = on.getMatchFeatures(group)
          if groupFV != None and groupFV.prob > 0:
            # it is possible to associate with this group
            gs = group.getSize(sentenceIndex=sentence.index)
            if gs > 0:
              calculatedER = on.eventRate(groupSize=gs)
              couldCalculateER = True
              for er in unmatchedER:    
                if er.equivalentEventRates(calculatedER):
                  onMatches[on].append(er) 
                  erMatches[er].append(on) 
      if couldCalculateER == False:
        outcomeMeasurements.remove(on.outcomeMeasurement)
     
    # discard any outcome numbers that potentially match multiple event rates
    for on in onMatches.keys():
      if len(onMatches[on]) == 1 and len(erMatches[onMatches[on][0]]) == 1:
        # this outcome number is a potential match for only one event rate
        # similarly, the event rate is only a match for this outcome number
        # assume they belong to same outcome measurement
        erOM = er.outcomeMeasurement
        on.outcomeMeasurement.addEventRate(er)
        outcomeMeasurements.remove(erOM)              
        
    # now consider all possible valid ON,ER pairings
#    for on in unmatchedON:
#      for er in unmatchedER:
#        if on.hasAssociatedGroupSize() == False or on.equivalentEventRates(er.eventRate()) == True:
#          om = OutcomeMeasurement(on)
#          om.addEventRate(er)
#          outcomeMeasurements.append(om)

    nOutcomeMeasurements = len(outcomeMeasurements)           
    maxSize = max(nOutcomeMeasurements, nGroupOutcomePairs)
    
    # initialize cost matrix for matching outcome measurements with group,outcome pairs        
    probMatrix = []
    probMultiplier = 100000

    for omIdx in range(maxSize):
      probMatrix.append([])
      for goIdx in range(maxSize):
        if omIdx < nOutcomeMeasurements and goIdx < nGroupOutcomePairs:
          om = outcomeMeasurements[omIdx]
          (group, outcome) = goPairs[goIdx]
          er = om.getTextEventRate()
          on = om.getOutcomeNumber()

          if er != None:
            outcomeFV = er.getMatchFeatures(outcome)
            groupFV = er.getMatchFeatures(group)
            if outcomeFV == None or groupFV == None:
              # this quantity has no chance of being associated with either the group or outcome mention
              # this can happen if all mentions for the entity appear in a sentence after the quantity
              probG_ER = 0
              probO_ER = 0
            else:
              probO_ER = outcomeFV.prob
              probG_ER = groupFV.prob
          else:
            probG_ER = 1
            probO_ER = 1

          if on != None:
            # this outcome measurement has an outcome number
            # is this number useful? Can we compute an event rate for this group? 
            # If not, discard this measurement (set probability to zero).
            # if so, is the event rate compatible with the textual event rate?
            # If not, discard.
            calculatedER = -1
            gs = group.getSize(sentenceIndex=sentence.index)
            outcomeFV = on.getMatchFeatures(outcome)
            groupFV = on.getMatchFeatures(group)
            if outcomeFV == None or groupFV == None:
              # this quantity has no chance of being associated with either the group or outcome mention
              probG_ON = 0
              probO_ON = 0
            else:
              probO_ON = outcomeFV.prob
              probG_ON = groupFV.prob
              
            if on.hasAssociatedGroupSize() == False:
              # there is no group size already associated with the outcome number
              # does the group have a group size? 
              # If so, is the resulting event rate compatible with the text one?
              if gs <= 0 and er == None:
                # there is no way to compute an event rate with this outcome measurement. 
                # it does not add any useful information. 
                # discard it by setting probability to zero
                probG_ON = 0
                probO_ON = 0
              elif gs > 0:
                # the proposed group has an associated size            
                # we can compute an event rate for this group/outcome
                calculatedER = on.eventRate(groupSize=gs)
                if (er != None and er.equivalentEventRates(calculatedER) == False) or abs(calculatedER) > 1:
                  # event rates are incompatible
                  probG_ON = 0
                  probO_ON = 0          
          else:
            probG_ON = 1
            probO_ON = 1
          
          if er != None and on != None:
            probG_OM = math.sqrt(probG_ER * probG_ON)
            probO_OM = math.sqrt(probO_ER * probO_ON)
          elif er != None:
            probG_OM = probG_ER 
            probO_OM = probO_ER 
          else:
            # on != None
            probG_OM = probG_ON
            probO_OM = probO_ON
                        
          prob = round(probG_OM * probO_OM * probMultiplier)
        else:
          prob = 0
          
        probMatrix[omIdx].append(prob)
    
#    if sentence.abstract.id == '21600592':
#      for omIdx in range(maxSize):
#        for goIdx in range(maxSize):
#          if omIdx < nOutcomeMeasurements and goIdx < nGroupOutcomePairs:
#            om = outcomeMeasurements[omIdx]
#            (group, outcome) = goPairs[goIdx]
#            print probMatrix[omIdx][goIdx], om.statisticString(), group.name, outcome.name
               
    costMatrix = make_cost_matrix(probMatrix, lambda cost: probMultiplier - cost)
    m = Munkres()
#    print probMatrix
#    print costMatrix
    indices = m.compute(costMatrix)
    # threshold is (1/2)^4
    threshold = 0.0625 * probMultiplier
    threshold = 0.0001 * probMultiplier
#    threshold = 0.25 * probMultiplier

    for omIdx, goIdx in indices:
      if omIdx < nOutcomeMeasurements and goIdx < nGroupOutcomePairs:
        prob = probMatrix[omIdx][goIdx]
        if prob > threshold:
          # this quantity and mention should be associated
          prob = float(prob) / probMultiplier
          om = outcomeMeasurements[omIdx]
          (group, outcome) = goPairs[goIdx]
          self.linkOutcomeMeasurementAssociations(om, group, outcome, prob)
      # record those outcome measurements that were not succefully matched to G,O    
      if omIdx < nOutcomeMeasurements and (goIdx >= nGroupOutcomePairs or probMatrix[omIdx][goIdx] <= threshold):
        om = outcomeMeasurements[omIdx]
        prob = float(probMatrix[omIdx][goIdx])/probMultiplier
        if goIdx < nGroupOutcomePairs:
          (group, outcome) = goPairs[goIdx]
        else:
          group = None
          outcome = None   
        abstract = sentence.abstract  
        if abstract not in self.incompleteMatches:
          self.incompleteMatches[abstract] = []                 
        self.incompleteMatches[abstract].append(OutcomeMeasurementAssociation(group, outcome, om, prob))
  

    

    
#######################################################################
# class definition for object that associates mentions with eventrates and outcome numbers
#######################################################################
    
class OutcomeMeasurementPairProbabilityEstimator(MentionQuantityAssociator):
  """ train/test system that associates eventrates and outcome numbers with groups and outcomes """
  considerPreviousSentences = True
  
  def __init__(self, mentionType, quantityType, useLabels=True, considerPreviousSentences=True):
    """ create a new group size, group associator. """
    MentionQuantityAssociator.__init__(self, mentionType, quantityType, useLabels)
    self.considerPreviousSentences = considerPreviousSentences          

  def computeTemplateFeatures(self, templates, mode=''):
    """ compute classifier features for each mention-quantity pair in 
        a given sentence in an abstract. """
#    print 'computeTemplateFeatures:', mode    
    qTemplateList = templates.lists.get(self.quantityType, None)
    if qTemplateList == None:
      print 'Error: invalid value type:', self.quantityType
      return

#    print len(qTemplateList), len(templates.lists.get(self.mentionType, None))

    templates.featureVectors = []
    for qIdx in range(0, len(qTemplateList)):
      qTemplate = qTemplateList[qIdx]
      # get the closest mention to this quantity for each entity in abstract.
      # if no closest mention exists, the value for the entity in the list is None
      sentence = qTemplate.token.sentence
      abstract = sentence.abstract
      if mode == 'train':
        entityList = abstract.annotatedEntities.getList(self.mentionType)  
#        print 'entityList:', self.mentionType, len(entityList)    
#        print  len(abstract.annotatedEntities.getList('group')), len(abstract.annotatedEntities.getList('outcome'))
      else:
        entityList = abstract.entities.getList(self.mentionType)

      (mTemplateList, closestMention) = self.closestMentionList(qTemplate, entityList, considerPreviousSentences=False)
      if self.considerPreviousSentences and self.mentionType == 'group':
        # count number of groups with mentions in this sentence
        nGroupsInSentence = 0
        for m in mTemplateList:
          if m != None:
            nGroupsInSentence += 1
        if nGroupsInSentence < len(mTemplateList):
          # there are groups without mentions in this sentence
          if nGroupsInSentence < len(qTemplateList) and nGroupsInSentence < 2:
            # we need to consider groups that appear in previous sentences
            (mTemplateList, closestMention) = self.closestMentionList(qTemplate, entityList, considerPreviousSentences=True)
            
      
      
      for mIdx in range(0, len(mTemplateList)):
        mTemplate = mTemplateList[mIdx]
        if mTemplate != None:
          # determine if this pair is the correct association
          if qTemplate.shouldBeAssociated(mTemplate):
            label = '1'
          else:
            label = '0'
          fv = FeatureVector(qIdx, mIdx, label)
          fv.mTemplate = mTemplate
          fv.qTemplate = qTemplate
          templates.featureVectors.append(fv)
          if mTemplate.getSentence() == qTemplate.getSentence():
            # both entities are in same sentence. use sentence-based features
            self.computePairFeatures(fv, closestMention, qTemplateList, mTemplateList, templates)
            fv.add('SAME_SENTENCE')
          elif self.considerPreviousSentences:    
            # both entities are in *different* sentences. 
            # use features that capture a relationship that spans sentences
            self.computeSentenceSpanningFeatures(fv, closestMention, qTemplateList, mTemplateList, templates)
          
#    print len(templates.featureVectors)

  def computePairFeatures(self, fv, closestMention, qTemplateList, mTemplateList, templates):
    """ compute features for given quantity, mention pair.
        add features to given feature vector """
    (start, end) = self.getRange(fv.qTemplate, fv.mTemplate)

#    if fv.mTemplate.type == 'group':
#      fv.addList(self.groupFeatures(fv.qTemplate, fv.mTemplate, closestMention))            
      
    fv.addList(self.proximityFeatures(fv.qTemplate, fv.mTemplate, closestMention))            
    fv.addList(self.dependencyFeatures(fv.qTemplate, fv.mTemplate))            
    fv.addList(self.entityInBetweenFeatures(start, end, templates))    
    fv.addList(self.specialTokensInRangeFeatures(start, end, templates.sentence))
        
    fv.addList(self.sameSentenceOrderFeatures(fv.qTemplate, fv.mTemplate, templates)) 


        
  def groupFeatures(self, qTemplate, mTemplate, closestMention):
    """ features characterizing group mention """
    fv = set([])

    nGroupMentions = mTemplate.getMentionChain()
    lemmas = mTemplate.mention.interestingLemmas()
    if nGroupMentions > 1 or 'group' in lemmas or 'arm' in lemmas or mTemplate.isControl() or mTemplate.isExperiment():
      fv.add('HIGH_CONFIDENCE_GROUP')
    
    return fv
    
             
            
  def closestMentionList(self, qTemplate, abstractEntityList, considerPreviousSentences):
    """ for each entity for a given type, find the mention from that entity that is closest to the given value.
        NOTE: if an entity does not have a mention in the current or preceeding sentences, then its closest mention
              is None.
    """    
    closestMention = None
    shortestDistance = float('inf')
    mTemplateList = []
    
    for entity in abstractEntityList:
      # find closest mention to the value (if any)
      (m, dist) = entity.getClosestMention(qTemplate, considerPreviousSentences=considerPreviousSentences)
      mTemplateList.append(m)
      if dist < shortestDistance:
        shortestDistance = dist
        closestMention = m  
         
#    if closestMention != None:
#      print 'closest mention to', qTemplate.value, 'is', closestMention.name, closestMention
#      print shortestDistance
#    else:
#      print 'No mention is closest to', qTemplate.value
#    print mTemplateList              
    return (mTemplateList, closestMention)     
    
  def computeSentenceSpanningFeatures(self, fv, closestMention, qTemplateList, mTemplateList, templates):
    """ compute features for given quantity, mention pair.
        add features to given feature vector """

    fv.add('IN_PREVIOUS_SENTENCE')
    
    mSentence = fv.mTemplate.getSentence()
    qSentence = fv.qTemplate.getSentence()
    if (mSentence.index + 1) == qSentence.index:
      fv.add('IN_ADJACENT_SENTENCE')
    
    if fv.mTemplate == closestMention:
      fv.add('CLOSEST')

    fv.addList(self.sentenceGroupFeatures(mTemplateList)) 
    fv.addList(self.sentenceEntityInBetweenFeatures(fv.qTemplate, fv.mTemplate, qTemplateList, mTemplateList))       
#    fv.addList(self.sentenceOrderFeatures(fv.qTemplate, fv.mTemplate, qTemplateList)) 
    
               
  def sentenceEntityInBetweenFeatures(self, qTemplate, mTemplate, qTemplateList, mTemplateList):              
    """ check for other entities in between the (value, entity) pair where mention is in a previous sentence"""
    fv = set([])

    mSentence = mTemplate.getSentence()
    qSentence = qTemplate.getSentence()
    
    # check for other *mentions* of the same type between the mention, value pair
    for m in mTemplateList:
      if m != None and m != mTemplate:
        sid = m.getSentence().index  
        if (mSentence.index < sid or (mSentence.index == sid and mTemplate.end < m.start)) \
          and (sid < qSentence.index or m.end < qTemplate.start):
          # this mention is between the original mention and the value
          fv.add(m.type+'_IB')
          break
    # check for other *values* of the same type between the mention, value pair
    for q in qTemplateList:
      if q.end < qTemplate.start:
        # this value appears before the value in our mention, value pair
        if mSentence.index < qSentence.index or mTemplate.end < q.start:
          # this value appears between the mention and value in our pair
          fv.add(q.type+'_IB')
          break
                
    return fv
  


  def sameSentenceOrderFeatures(self, qTemplate, mTemplate, templates):
    """ feature for determining if the mention and quantity have the same order when mentioned in different sentences """
    fv = set([])
    
    qTemplateList = templates.lists.get(self.quantityType, None)
    nQuantities = len(qTemplateList)
    mTemplateList = templates.lists.get(self.mentionType, None)
    nMentions = len(mTemplateList)
    minSize = min(nQuantities, nMentions)
    
    mIdx = self.getIndexOfEntity(mTemplate, mTemplateList)
    qIdx = self.getIndexOfEntity(qTemplate, qTemplateList)
    if mIdx < 0 or qIdx < 0:
      print "??? sentenceOrderFeatures: Could not find value or mention in sentences lists."
      print "%s: Value=%f, Mention=%s, qIdx = %d, mIdx = %d" % (qTemplate.getSentence().abstract.id, qTemplate.value, mTemplate.name, qIdx, mIdx)
      return fv

#    if mTemplate.type == 'group' and qTemplate.type == 'eventrate':
#      print "%s: Value=%f, Mention=%s, qIdx = %d, mIdx = %d" % (qTemplate.getSentence().abstract.id, qTemplate.value, mTemplate.name, qIdx, mIdx)
#      print 'nQuantities=%d, nMentions=%d' %(nQuantities, nMentions)
    
    if nQuantities % minSize == 0 and nMentions % minSize == 0 \
       and (qIdx % minSize) == (mIdx % minSize):
      fv.add('SAME_ORDER')
#    else:
#      if mTemplate.type == 'group' and qTemplate.type == 'eventrate':
##        print "%s: Value=%f, Mention=%s, qIdx = %d, mIdx = %d" % (qTemplate.getSentence().abstract.id, qTemplate.value, mTemplate.name, qIdx, mIdx)
##        print 'nQuantities=%d, nMentions=%d' %(nQuantities, nMentions)
#        print '$$$$ SAME ORDER'
        
    return fv        
  
  
  def getIndexOfEntity(self, entity, templateList):
    """ return the index of an entity in a given list of entities.
        return -1 if element is not in the list """
    for i in range(len(templateList)):
      if templateList[i] == entity:
        return i
    return -1
    
  def sentenceGroupFeatures(self, mTemplateList):
    """ features based on number of Groups mentioned in sentence """
    fv = set([])
    nPresent = 0
    for m in mTemplateList: 
      if m != None:
        nPresent += 1
    
    if nPresent == 0:
      fv.add('NO_GROUPS')
#    elif nPresent == 1:
#      fv.add('ONE_GROUP')
      
    return fv  
      
  
  def linkTemplates(self, sentence):
    """ for now, don't actually link any templates. 
        wait until we have probabilities for all outcome value pairings.
        At this point, just remember the probabilities and feature vectors for each pairing """
    templates = sentence.templates
    qTemplateList = templates.getList(self.quantityType)
    fvList = templates.featureVectors
#    print 'linkTemplates:', len(fvList)
    
    for q in qTemplateList:
      q.clearMatchFeatures(self.mentionType)
    
    for fv in fvList:
      fv.qTemplate.addMatchFeatures(fv)
        
#  def computeStats(self, absList, statOut=None, errorOut=None, typeList=[]):
#    """ Does nothing. """
#    pass
     
  def checkAssociations(self, sentence, errorOut, typeList=[]):
    """ return number of correct associations and total number of values for 
         a given mention and value type """
    if len(typeList) == 2:
      if typeList[0] in self.validMentionTypes and typeList[1] in self.validQuantityTypes:
        mentionType = typeList[0]
        quantityType = typeList[1]
      elif typeList[1] in self.validMentionTypes and typeList[0] in self.validQuantityTypes:
        mentionType = typeList[0]
        quantityType = typeList[1]
      else:
        raise StandardError('Illegal type list for checkAssociations: ' + typeList) 
    elif len(typeList) == 0:
      mentionType = self.mentionType
      quantityType = self.quantityType           
    else:
      raise StandardError('Illegal number of types for checkAssociations: %d'%len(typeList))
        
    tp = 0
    fp = 0
    fn = 0
    falsePairs = 0
    
    for fv in sentence.templates.featureVectors:
      qTemplate = fv.qTemplate
      mTemplate = fv.mTemplate
      associationIsCorrect = False
      
      if fv.prob >= 0.5:
        associatePair = True
      else:
        associatePair = False
        
      if fv.label == '1' and associatePair == True:
        # both value and mention are valid and are correctly associated
        tp += 1
        associationIsCorrect = True
      elif fv.label == '0' and associatePair == True:
        # either the value or mention is incorrect
        # or both are valid, but should not be associated
        # results in a false positive in all cases
        fp += 1
        if qTemplate.isTruePositive() == False:
          falsePairs += 1
      elif fv.label == '1' and associatePair == False:
        # this is the mention that the quantity should have been matched with, 
        # but was not.
        fn += 1
      else:
        # pair is not supposed to be labeled and that is what the classifier determine
        # True negative
        associationIsCorrect = True
      errorOut.write('True Label=%s, prob=%.2f, correct=%s, Value=%f, Mention=%s\n'%(fv.label, fv.prob, str(associationIsCorrect), qTemplate.value, mTemplate.name)) 
                     
    return [tp, fp, fn, falsePairs]    
  
        

  
 