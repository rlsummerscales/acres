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
    
class MentionQuantityAssociator(BaseMentionQuantityAssociator):
  """ train/test system that associates mentions with quantities in a sentence """
  
  def __init__(self, mentionType, quantityType, useLabels=True):
    """ create a new mention-quantity associator given a specific mention type
        and quantity type. """
    BaseMentionQuantityAssociator.__init__(self, mentionType, quantityType, \
                                           useLabels)
      
  def train(self, absList, modelFilename):
    """ Train a mention-quantity associator model given a list of abstracts """
    trainFilename = 'features.'+self.mentionType+'-'+self.quantityType+'.train.txt'

    self.writeFeatureFile(absList, trainFilename, forTraining=True)
    cmd = 'bin/megam.opt -quiet -tune binary ' + trainFilename + ' > ' \
      + modelFilename
    print cmd
    os.system(cmd)
     
  def test(self, absList, modelFilename, fold=None):
    """ Apply the mention-quantity associator to a given list of abstracts
        using the given model file.
        """
    if fold != None:
      foldString = '.%d' % fold
    else:
      foldString = ''
    
    testFilename = 'features.%s-%s%s.test.txt'%(self.mentionType, self.quantityType, foldString)
    resultFilename = '%s-%s%s.results.txt'%(self.mentionType, self.quantityType, foldString)

    self.writeFeatureFile(absList, testFilename, forTraining=False)
    cmd = 'bin/megam.opt -quiet -predict ' + modelFilename + ' binary ' \
       + testFilename + ' > ' + resultFilename 
    print cmd
    os.system(cmd)
    
    # get probabilites from result file
    resultLines = open(resultFilename, 'r').readlines()
    featureVectors = self.getFeatureVectors(absList, forTraining=False)
    i = 0    # current feature vector
    for line in resultLines:
      parsedLine = line.strip().split()
      prob = float(parsedLine[-1])
      featureVectors[i].prob = prob
      i = i + 1
    # chose the most likely association for each value
    for abstract in absList:
      for s in abstract.sentences:
        self.linkTemplates(s)

  def getFeatureVectors(self, absList, forTraining):
    """ return list of features vectors to use for training/testing associator
        in all sentences in a given list of abstracts.
        
        absList = list of abstracts to get features vectors for
        forTraining = True if feature vectors will be used for training, 
                      False if used for testing. 
                      If used for training, use annotated mentions."""
    list = []
    for abstract in absList:
      for sentence in abstract.sentences:
        if forTraining == True:
          # use annotated templates
          templates = sentence.annotatedTemplates
        else:
          # use detected templates
          templates = sentence.templates
        for fv in templates.featureVectors:
          list.append(fv)          
    return list       

  def writeFeatureFile(self, absList, featureFilename, forTraining):
    """ write features to a file that can be read by megam  """
    featureVectors = self.getFeatureVectors(absList, forTraining)
    out = open(featureFilename, 'w')
    debugout = open('debug.'+featureFilename, 'w')

    for fv in featureVectors:
      fv.writeToMegamFile(out)
      debugout.write('%0.2f, %s (ID=%s), '%(fv.qTemplate.value, fv.mTemplate.name, fv.mTemplate.getAnnotatedId()))
#      debugout.write(str(fv.qTemplate.value)+', ')
#      debugout.write(fv.mTemplate.name+', '+fv.mTemplate.getAnnotatedId()+', ')
      fv.writeToMegamFile(debugout)
    debugout.close()
    
  def computeTemplateFeatures(self, templates, mode=''):
    """ compute classifier features for each mention-quantity pair in 
        a given sentence in an abstract. """
    qTemplateList = templates.lists.get(self.quantityType, None)
    if qTemplateList == None:
      print 'Error: invalid value type:', self.quantityType
      return

    mTemplateList = templates.lists.get(self.mentionType, None) 
    if mTemplateList == None:
      print 'Error: invalid mention type:', self.mentionType
      return
    
    templates.featureVectors = []
    for qIdx in range(0, len(qTemplateList)):
      qTemplate = qTemplateList[qIdx]
      (closestMention, dist) = templates.closestMention(qTemplate, self.mentionType)

      for mIdx in range(0, len(mTemplateList)):
        mTemplate = mTemplateList[mIdx]
        # determine if this pair is the correct association
        if qTemplate.shouldBeAssociated(mTemplate):
          label = '1'
        else:
          label = '0'
        fv = FeatureVector(qIdx, mIdx, label)
        fv.mTemplate = mTemplate
        fv.qTemplate = qTemplate
        templates.featureVectors.append(fv)
        self.computePairFeatures(fv, closestMention, qTemplateList, mTemplateList, templates)



  def computePairFeatures(self, fv, closestMention, qTemplateList, mTemplateList, templates):
    """ compute features for given quantity, mention pair.
        add features to given feature vector """
    (start, end) = self.getRange(fv.qTemplate, fv.mTemplate)

    fv.addList(self.proximityFeatures(fv.qTemplate, fv.mTemplate, closestMention))            
    fv.addList(self.dependencyFeatures(fv.qTemplate, fv.mTemplate))            
    fv.addList(self.entityInBetweenFeatures(start, end, templates))    
    fv.addList(self.specialTokensInRangeFeatures(start, end, templates.sentence))
        
#    fv.addList(self.binaryParityFeature(fv.mentionId, fv.valueId))    
    fv.addList(self.orderFeatures(fv.mentionId, fv.valueId, qTemplateList, mTemplateList))    
    
    
  def orderFeatures(self, qIdx, mIdx, qTemplateList, mTemplateList):
    """ feature for determining if the mention and quantity have the same order """
    fv = set([])
    nQuantities = len(qTemplateList)
    nMentions = len(mTemplateList)
    minSize = min(nQuantities, nMentions)
    
    if nQuantities % minSize == 0 and nMentions % minSize == 0 \
       and (qIdx % minSize) == (mIdx % minSize):
      fv.add('SAME_ORDER')
        
    return fv        
        
  def getRange(self, qTemplate, mTemplate): 
    """ return start and end indices for tokens between the quantity and mention. """
    firstTokenInMention = mTemplate.mention.tokens[0]
    # mention before/after value in sentence
    if qTemplate.token.index < firstTokenInMention.index:
      # mention is after value
      start = qTemplate.token.index 
      end = firstTokenInMention.index 
    else:
      start = mTemplate.mention.tokens[-1].index
      end = qTemplate.token.index  
    
    start += 1
    end -= 1
    
    return (start, end)  
      
         
  def proximityFeatures(self, qTemplate, mTemplate, closestMention):
    """ compute features capturing proximity relationship to each other. """
    fv = set([])
    firstTokenInMention = mTemplate.mention.tokens[0]
    # mention before/after value in sentence
    if qTemplate.token.index < firstTokenInMention.index:
      fv.add('VALUE_BEFORE')   # mention is after value

    # add feature if this entity is the closest one to the value
    if mTemplate == closestMention:
      fv.add('CLOSEST')
      
    # check if the two are adjacent
    (start, end) = self.getRange(qTemplate, mTemplate)  
    if start > end:
      # no tokens in between
      fv.add('ADJACENT')
    elif start == end:
      # only one token in between
      ibToken = qTemplate.token.sentence[start]
      if ibToken.text == '-LRB-' or ibToken.text == '-RRB-':
        fv.add('ADJACENT')
      
    return fv        
          
  def binaryParityFeature(self, mIdx, qIdx):        
    """ check if the value and entity are mentioned in the same order
     e.g. value and entity are both second ones mentioned """
    fv = set([]) 
    nVBefore = qIdx    # number of values (of desired type) before this one
    nEBefore = mIdx    # number of mentions (of desired type) before this one
    if nVBefore % 2 == nEBefore %2:
      fv.add('BIN_PARITY')
    return fv

  def dependencyFeatures(self, qTemplate, mTemplate):
    """ does the value have a dependency relationship with the mention?"""
    fv = set([])
    for token in mTemplate.mention.tokens:
      for dep in token.dependents:
        if qTemplate.token.index == dep.index:
          fv.add('VALUE_IS_DEP')
          fv.add('VALUE_IS_DEP_'+dep.type)
      for gov in token.governors:
        if qTemplate.token.index == gov.index:
          fv.add('VALUE_IS_GOV')
          fv.add('VALUE_IS_GOV_'+gov.type)
    return fv
  
  def entityInBetweenFeatures(self, start, end, templates):              
    """ check for other entities in between the (value, entity) pair """
    fv = set([])
    if templates.templateBetween('group', start, end) == True:
      fv.add('GROUP_IB')
    if templates.templateBetween('outcome', start, end) == True:
      fv.add('OUTCOME_IB')
    if templates.templateBetween('gs', start, end) == True:
      fv.add('GROUP_SIZE_IB')
    if templates.templateBetween('on', start, end) == True:
      fv.add('OUTCOME_NUMBER_IB')
    if templates.templateBetween('eventrate', start, end) == True:
      fv.add('EVENT_RATE_IB')
    return fv

  def specialTokensInRangeFeatures(self, start, end, sentence):
    """ add features for special tokens that appear between start and end token in sentence """
    fv = set([])
    conjTokens = set(['and', 'or'])
    containsSep = False
    # check for special tokens in between
    for i in range(start, end+1):
      token = sentence[i]
      if token.text == ',':
        fv.add('COMMA_IB')
      elif token.text == ';':
        fv.add('SEMI_IB')
      elif token.text == 'versus':
        fv.add('VERSUS_IB')
      elif token.text in conjTokens:
        fv.add('CONJ_IB')
#           if token.pos[0] == 'V':
#             fv.add('VERB_IB_'+token.lemma)

#         sepTokens = set(['versus', 'and', 'or', ',', ';'])
#         containsSep = False
#         # is there at least one separator token between value and mention?
#         for i in range(start, end):
#           token = templates.sentence[i]
#           if containsSep == False and token.text in sepTokens:
#             # there is a separator token between value and mention
#             containsSep = True
#             fv.add('CONTAINS_SEP')
    return fv

  def linkTemplates(self, sentence):
    """ link value template to best matching mention template in the same sentence.
        It is assumed that mention clustering has not occurred yet.
        """
    # sort feature vectors by probability
    templates = sentence.templates
    fvList = sorted(templates.featureVectors, key=attrgetter('prob'), reverse=True)

    for fv in fvList:
      # skip pairs that are classified as 'not associated'
      # this is pairs with probability < 0.5
      if fv.prob < 0.5:
        continue  
        
      qIdx = fv.valueId
      qTemplateList = templates.getList(self.quantityType)
      qTemplate = templates.lists[self.quantityType][qIdx]
      
      mIdx = fv.mentionId
      mTemplate = templates.lists[self.mentionType][mIdx]
      
      if self.mentionType == 'outcome' and self.quantityType == 'on' \
          and qTemplate.outcome == None:
        # outcome number not currently linked to any outcome, link it
        qTemplate.outcome = mTemplate
        qTemplate.outcomeProb = fv.prob
        mTemplate.numbers.append(qTemplate)
      elif self.mentionType == 'group' and self.quantityType == 'gs' \
        and qTemplate.group == None \
        and (mTemplate.getSize() == 0 or mTemplate.hasSize(qTemplate.value)):
        # group & group size both unlinked, link them to each other
        qTemplate.group = mTemplate
        qTemplate.groupProb = fv.prob
        mTemplate.addSize(qTemplate)
      elif self.mentionType == 'group' and self.quantityType == 'on' \
          and qTemplate.group == None:
        # outcome number is not linked to any group, check if this one works
        oTemplate = qTemplate.outcome
        foundOutcome = False
        # make sure that the group does not already have a number 
        # for this outcome
        if oTemplate != None:
          for onTemplate in mTemplate.outcomeNumbers:
            if onTemplate.outcome == oTemplate:
              # this group already has an outcome number for this 
              # outcome number's outcome
              foundOutcome = True
              break
        if foundOutcome == False:
          # no number for this outcome, link group and outcome number
          qTemplate.group = mTemplate
          qTemplate.groupProb = fv.prob

          mTemplate.outcomeNumbers.append(qTemplate)
          if qTemplate.groupSize != None:
            gsTemplate = qTemplate.groupSize
            gsTemplate.group = mTemplate
            mTemplate.addSize(gsTemplate)
      elif self.mentionType == 'group' and self.quantityType == 'eventrate' \
        and qTemplate.group == None:
        # event rate not linked to a group, link it
        qTemplate.group = mTemplate
        qTemplate.groupProb = fv.prob
        mTemplate.eventrates.append(qTemplate)
      elif self.mentionType == 'outcome' and self.quantityType == 'eventrate' \
          and qTemplate.outcome == None:
        # event rate not currently linked to any outcome, link it
        qTemplate.outcome = mTemplate
        qTemplate.outcomeProb = fv.prob


        
