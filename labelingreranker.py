#!/usr/bin/python
# Re-rank sequence labelings for each sentence
# author: Rodney Summerscales

import sys
import os.path
import nltk
import random
import math

import templates
from finder import Finder
from basetokenclassifier import TokenLabel
from tokenlist import TokenList
from mention import Mention
from ensemble import BallotBox
from irstats import IRstats

class Labeling:
  labels = None
  rank = None
  finder = None
  sentence = None
  entities = None
  
  def __init__(self, sentence, labels, rank, finder):
    self.sentence = sentence
    self.labels = labels
    self.rank = rank
    self.finder = finder
    self.entities = {}
    for eType in finder.entityTypes:
      self.entities[eType] = self.finder.getTopKMentions(sentence, eType, rank)
#      print eType, len(self.entities[eType])
    


class LabelTuple:
  """ combination of top-k label sequences """
  sentence = None
  groupLabeling = None
  outcomeLabeling = None
  eventrateLabeling = None
  numberLabeling = None
  featureValues = None
#  timesLabeled = 0
  
  def __init__(self):
    self.sentence = None
    self.groupLabeling = None
    self.outcomeLabeling = None
    self.eventrateLabeling = None
    self.numberLabeling = None
    self.featureValues = {}
#    self.timesLabeled = {}
   
  def addAllLabels(self, tIdx, includeLabeling):
    """ add all labels from each labeling to token at given index in sentence """
#    if tIdx in self.timesLabeled:
#      self.timesLabeled[tIdx] += 1
#    else:
#      self.timesLabeled[tIdx] = 0
#      
#    m = self.sentence[tIdx].getLabelMatches(['on', 'gs'])   
#    if len(m) > 0:
#      print '############# token already has labels', m
#      print includeLabeling, self.timesLabeled[tIdx]
#      raise

    if len(includeLabeling) == 0 or 'group' in includeLabeling:
      self.addLabel(tIdx, self.groupLabeling)

    if len(includeLabeling) == 0 or 'outcome' in includeLabeling:
      self.addLabel(tIdx, self.outcomeLabeling)

    if len(includeLabeling) == 0 or 'eventrate' in includeLabeling:
      self.addLabel(tIdx, self.eventrateLabeling)

    if len(includeLabeling) == 0 or 'number' in includeLabeling: 
      self.addLabel(tIdx, self.numberLabeling)


  def addLabel(self, tIdx, labeling):
    """ add the label at the given index in the labeling to token at that index in the sentence """
    try:
      token = self.sentence[tIdx]
      if labeling.labels[tIdx].label != 'other':
        token.addLabel(labeling.labels[tIdx].label)
    except:
      print 'Error assigning label:', sys.exc_info()[0]
      print 'tIdx=%d, len(sentence)=%d, len(labeling)=%d\n'%(tIdx, len(self.sentence), len(labeling.labels))
  
  def getLabeling(self, labelingName):
    """ return the labeling corresponding to 'group', 'outcome', 'eventrate', or 'number' """
    if labelingName == 'group':
      return self.groupLabeling
    elif labelingName == 'outcome':
      return self.outcomeLabeling
    elif labelingName == 'eventrate':
      return self.eventrateLabeling
    elif labelingName == 'number':
      return self.numberLabeling
    else:
      print 'getLabeling: Unknown labelingName value:', labelingName
      raise
        
  def computeTupleValues(self, includeLabeling=['group', 'outcome', 'eventrate', 'number']):
    """ compute values used as features for this tuple of labelings """   
      
    self.featureValues['nLastTokenOther'] = (self.lastTokenOther(self.groupLabeling) \
                                           + self.lastTokenOther(self.outcomeLabeling))/2
    self.featureValues['nConflict'] = float(self.countConflict()) / len(self.sentence)

      
    self.featureValues['pPopularGroup'] = self.percentMatchesPopular(self.groupLabeling)
#    self.featureValues['pGroupTokens'] = self.percentEntityLabels(self.groupLabeling.labels)
#    self.featureValues['gRank'] = self.groupLabeling.rank

    self.featureValues['pPopularOutcome'] = self.percentMatchesPopular(self.outcomeLabeling)
#    self.featureValues['pOutcomeTokens'] = self.percentEntityLabels(self.outcomeLabeling.labels)
#    self.featureValues['oRank'] = self.outcomeLabeling.rank        
  
#    self.featureValues['pPopularEventrate'] = self.percentMatchesPopular(self.eventrateLabeling)
##    self.featureValues['pEventrateTokens'] = self.percentEntityLabels(self.eventrateLabeling.labels)
####    self.featureValues['eRank'] = self.eventrateLabeling.rank
#      
#    self.featureValues['pPopularNumber'] = self.percentMatchesPopular(self.numberLabeling)
##    self.featureValues['pNumberTokens'] = self.percentEntityLabels(self.numberLabeling.labels)
###    self.featureValues['nRank'] = self.numberLabeling.rank
#  
    nGroup = len(self.groupLabeling.entities['group'])
    nOutcome = len(self.outcomeLabeling.entities['outcome'])
    nEventrate = len(self.eventrateLabeling.entities['eventrate'])
    nON = len(self.numberLabeling.entities['on'])
    nGS = len(self.numberLabeling.entities['gs'])
    
#    self.featureValues['nGroup'] = nGroup
#    self.featureValues['nOutcome'] = nOutcome
#    self.featureValues['nEventrate'] = nEventrate
#    self.featureValues['nON'] = nON
#    self.featureValues['nGS'] = nGS    
###       
    uniqueGroups = []
#    print '**',len(self.groupLabeling.entities['group']), [m.text for m in self.groupLabeling.entities['group']]
    for gMention in self.groupLabeling.entities['group']:
      gTemplate = templates.Group(gMention, useAnnotations=False)
#      print gMention.text, '=' , gTemplate.toString()
#      print len(uniqueGroups), [gTemplate.name for gTemplate in uniqueGroups]
      self.mergeMention(gTemplate, uniqueGroups)
      
    uniqueOutcomes = []
    for oMention in self.outcomeLabeling.entities['outcome']:
      oTemplate = templates.Outcome(oMention, useAnnotations=False)
      self.mergeMention(oTemplate, uniqueOutcomes)
    
    nUniqueGroups = len(uniqueGroups)
    nUniqueOutcomes = len(uniqueOutcomes)
#    self.featureValues['ON=ER'] = self.onEqualEventrate(nON, nEventrate)    
    self.featureValues['G=GS'] = self.groupEqualGroupSize(nUniqueGroups, nGS)
    self.featureValues['GO=ON'] = self.groupOutcomeEqualOutcomeMeasurement(nUniqueGroups, nUniqueOutcomes, nON)  
    self.featureValues['GO=ER'] = self.groupOutcomeEqualOutcomeMeasurement(nUniqueGroups, nUniqueOutcomes, nEventrate)     
    

  def mergeMention(self, mention, mentionList):
    """ merge a mention template with given list of mention templates """
    matches = [rootMention for rootMention in mentionList if rootMention.exactSetMatch(mention) ]
    if len(matches) > 0:
      matches[0].merge(mention)
    else:
      mentionList.append(mention)
  
  def groupOutcomeEqualOutcomeMeasurement(self, nUniqueGroups, nUniqueOutcomes, nOM):
    if nOM > 0:     
      return abs(nUniqueGroups*nUniqueOutcomes - nOM)    
    else:
      return 0.0  
        
  def groupEqualGroupSize(self, nUniqueGroups, nGS):
    if nGS > 0:
      return abs(nUniqueGroups - nGS)
    else:
      return 0.0
    
  def onEqualEventrate(self, nON, nEventrate):
    if nON == 0 or nEventrate == 0:
      return 0
    else:
      return abs(nON - nEventrate) 
    
  def countConflict(self):
    """ count the number of tokens with conflicting labels given two label lists """
    nConflict = 0
    labelSet = set([])
    for idx, tLabel in enumerate(self.groupLabeling.labels):
      nRealLabels = 0
      if tLabel.label != 'other':
        nRealLabels += 1
      if self.outcomeLabeling.labels[idx].label != 'other':
        nRealLabels += 1
      if self.eventrateLabeling.labels[idx].label != 'other':
        nRealLabels += 1
      if self.numberLabeling.labels[idx].label != 'other':
        nRealLabels += 1
      if nRealLabels > 1:
        nConflict += nRealLabels - 1  
    return nConflict

  def percentEntityLabels(self, labeling):
    """ return the percentage of tokens that are NOT labeled 'other' """
    nTokens = len(labeling)
    if nTokens == 0:
      return 0
    
    nEntityLabels = 0  
    for tLabel in labeling:
      if tLabel.label != 'other':
        nEntityLabels += 1
    
    return float(nEntityLabels) / nTokens
  
  def percentMatchesPopular(self, labeling, weights=[]):
    """ percent of tokens in the labeling with labels from the most popular labeling of the sentence """
    (mostPopularLabels, bestK) = labeling.finder.selectMostPopular(self.sentence, countOther=True, weights=weights) 
    return self.percentMatches(labeling.labels, mostPopularLabels)  

  def percentMatches(self, labelList, targetLabeling):
    """ return the percentage of sentence tokens with labels matches those from a given labeling """
    nMatches = self.countMatches(labelList, targetLabeling)
    nTargetLabels = len(targetLabeling)
    if nTargetLabels == 0:
      # this situation only happens with numbers since only number tokens are labeled.
      # if there are no number tokens to label, the length of targetLabeling will be zero
      # (none of the alternate labelings will exist)
      # also labeling is padded with 'other' labels for non-number tokens, so labeling will consist
      # of all other tokens in this case
      # there is trivial agreement between the two labelings here
      return 1.0
    else:
      return float(nMatches) / nTargetLabels
  
  def countMatches(self, labelList, targetLabeling):
    """ return the number of tokens with labels matches those from a given labeling """ 
    nMatches = 0
    idx = 0
    for tLabel in labelList:
      if tLabel.prob > 0:
        if tLabel.label == targetLabeling[idx]:
          nMatches += 1 
        idx += 1
    return nMatches
          
  def lastTokenOther(self, labelList):
    """ return 1 if last token of labeling is 'other', zero otherwise """
    if labelList.labels[-1].label == 'other':
      return 1.0
    else:
      return 0.0
        
  def computeTupleMentionError(self, recomputeAnnotatedMentions, errorWeights={}):
    """ compute the number of FP, FN, Duplicate mentions in the sentence """
    totalFP = 0
    totalFN = 0
    totalDuplicates = 0
    stats = {}
    aList = {}
    if len(errorWeights) == 0:
      errorWeights['group']      = {'fp':1, 'fn':1, 'dup':1}
      errorWeights['outcome']    = {'fp':1, 'fn':1, 'dup':1}
      errorWeights['eventrate']  = {'fp':1, 'fn':1, 'dup':1}
      errorWeights['on']         = {'fp':1, 'fn':1, 'dup':1}
      errorWeights['gs']         = {'fp':1, 'fn':1, 'dup':1}

    
    mentions = {}
    mentions['group'] = (self.groupLabeling.entities['group'], self.groupLabeling.finder)
    mentions['outcome'] = (self.outcomeLabeling.entities['outcome'], self.outcomeLabeling.finder)
    mentions['eventrate'] = (self.eventrateLabeling.entities['eventrate'], self.eventrateLabeling.finder)
    mentions['on'] = (self.numberLabeling.entities['on'], self.numberLabeling.finder)
    mentions['gs'] = (self.numberLabeling.entities['gs'], self.numberLabeling.finder)
    
    for mType, (dList, finder) in mentions.items():
      aList[mType] = self.sentence.getAnnotatedMentions(mType, recomputeMentions=recomputeAnnotatedMentions)
      stats[mType] = IRstats()  
      finder.compareMentionLists(dList, aList[mType], mType, stats[mType])
      totalFP += stats[mType].fp * errorWeights[mType]['fp']
      totalFN += stats[mType].fn * errorWeights[mType]['fn']
      totalDuplicates += stats[mType].duplicates * errorWeights[mType]['dup']
    
#    mType = 'eventrate'
#    print 'True:', [m.text for m in aList[mType]]
#    print 'Detected:',[m.text for m in mentions[mType][0]]
    totalError = totalFP + totalDuplicates + totalFN   
#    if totalError > 9:
#      for mType in mentions.keys():
#        print 'Type: %s, FP: %d, FN: %d, DUP: %d'%(mType, stats[mType].fp, stats[mType].fn, stats[mType].duplicates)         
#      print self.sentence.abstract.id, 'Total error = ', totalError
      
    return totalError
          
  def computeTupleTokenError(self):
    """ compute number of tokens with incorrect labels across all labelings """
    nError = 0
    nError += self.labelingErrors(self.groupLabeling)
    nError += self.labelingErrors(self.outcomeLabeling)
    nError += self.labelingErrors(self.eventrateLabeling)
    nError += self.labelingErrors(self.numberLabeling)
    return nError

  def labelingErrors(self, labeling):
    """ return number of incorrect labels """
    nErrors = 0
    for tIdx, tLabel in enumerate(labeling.labels):
      trueLabels = self.sentence[tIdx].getAnnotationMatches(labeling.finder.entityTypes) 
      if tLabel.label == 'other' and len(trueLabels) > 0:
        # false negative
        nErrors += 1
      elif tLabel.label != 'other' and tLabel.label not in trueLabels:
        # false positive
        nErrors += 1
    return nErrors
  
class FeatureVector:
  """ feature vector for set of labelings """
  features = None
  score = 0
  tuple = None
  label = None
  qid = None
  
  def __init__(self, currentTuple):
    self.features = {}
    self.score = 0
    self.label = None
    self.tuple = currentTuple
    self.quid = None
    
  def addFeature(self, featureId, value):
    """ add feature and its value to feature vector """
    self.features[featureId] = value
    
  def write(self, out):
    """ write feature vectors to test/training file  """
    out.write('%d qid:%d'%(self.label, self.qid))
    for fid, value in self.features.items():
      if value != 0:
        out.write('\t%d:%f' % (fid, value))
    out.write('  #  (group=%d, outcome=%d, eventrate=%d, number=%d), label=%d\n' \
          % (self.tuple.groupLabeling.rank, self.tuple.outcomeLabeling.rank, \
             self.tuple.eventrateLabeling.rank, self.tuple.numberLabeling.rank, self.label))
      
  


class LabelingReRanker(Finder):
  """ Used for training/testing a classifier identify the best combination
       of alternate labeling sequences for groups, outcomes, event rates,
       outcome numbers and group sizes.
      """
  groupFinder = None
  outcomeFinder = None
  eventrateFinder = None
  numberFinder = None
  modelPath = None
  rerankerClassifier = None
  sentenceFilter = None
  featureIds = {}
  trainFolds = 1
  jointAssignment = True
  useRules = False
  theta = 0
  labelingWeights = None
  
  def __init__(self, groupFinder, outcomeFinder, eventrateFinder, numberFinder, modelPath, jointAssignment=True, \
               useRules=False, maxTopK=2, theta=0.8):
    """ Create a new re-ranker.
    """
    Finder.__init__(self, ['group', 'outcome', 'eventrate', 'on', 'gs'])
    self.groupFinder = groupFinder
    self.outcomeFinder = outcomeFinder
    self.eventrateFinder = eventrateFinder
    self.numberFinder = numberFinder
    self.modelPath = modelPath
    self.featureIds = {}
    self.trainFolds = 5
    self.maxTopK = maxTopK
    self.jointAssignment = jointAssignment
    self.useRules = useRules
    self.theta = theta
    self.labelingWeights = []
#    self.labelingWeights = self.poissonWeights()
    self.labelingWeights = self.linearWeights()
#    self.labelingWeights = self.exponentialWeights()    
    
         
    for i, w in enumerate(self.labelingWeights):
      print '%2d %.8f' % (i, w)
  
  def exponentialWeights(self):
    nLabelings = max(self.outcomeFinder.tokenClassifier.topK, self.groupFinder.tokenClassifier.topK)
    labelingWeights = []

    for i in range(0, nLabelings):
      w = self.theta*math.exp(-self.theta*i)
      labelingWeights.append(w)
    return labelingWeights
    
  def linearWeights(self):
    nLabelings = max(self.outcomeFinder.tokenClassifier.topK, self.groupFinder.tokenClassifier.topK)
    
    labelingWeights = []
    for i in range(nLabelings, 0, -1):
#      labelingWeights.append(1.0/k)
#      labelingWeights.append(i)
      labelingWeights.append(1.0)
    return labelingWeights
  
  def poissonWeights(self):
    nLabelings = max(self.outcomeFinder.tokenClassifier.topK, self.groupFinder.tokenClassifier.topK)
    t = 1
    eTheta = math.exp(-self.theta)
    labelingWeights = [eTheta]

    for i in range(1, nLabelings):
      t *= self.theta/i 
      w = t*eTheta
      labelingWeights.append(w)
    return labelingWeights
     
  def train(self, absList, modelFilename):
    """ Train a re-ranker model given a list of abstracts """
    print 'Training re-ranker'
    if self.useRules == False:
      # get top-k labels for training set
      absList.createCrossValidationSets(nFolds=self.trainFolds)
      self.groupFinder.crossvalidate(absList, self.modelPath)
      self.outcomeFinder.crossvalidate(absList, self.modelPath)
      self.eventrateFinder.crossvalidate(absList, self.modelPath)
      self.numberFinder.crossvalidate(absList, self.modelPath)
      
      self.groupFinder.writeLabelings(absList, 'group.labels.train%d.txt'%self.trainFolds)
      self.outcomeFinder.writeLabelings(absList, 'outcome.labels.train%d.txt'%self.trainFolds)
      self.eventrateFinder.writeLabelings(absList, 'eventrate.labels.train%d.txt'%self.trainFolds)
      self.numberFinder.writeLabelings(absList, 'on-gs.labels.train%d.txt'%self.trainFolds)
  
      # train re-ranker model
      if self.jointAssignment:
        self.trainRanker(absList, modelFilename)
      else:
        # train separate ranker models for each CRF output
        for lf in ['group', 'outcome', 'eventrate', 'number']:
          self.trainRanker(absList, modelFilename, includeLabeling=[lf])
        
  def test(self, absList, modelFilename, fold=None):
    """ Apply the labeling re-ranker to a given list of abstracts
        using the given model file.
        """        
    self.removeCurrentLabels(absList)
    
    if self.useRules:
      # use rules to re-rank labelings
      if self.jointAssignment:
        self.assignUsingRules(absList)
      else:
        for lf in ['group', 'outcome', 'eventrate', 'number']:
          self.assignUsingRules(absList, includeLabeling=[lf])            
    else:
      # train classifier to re-rank labelings      
      if self.jointAssignment:    
        self.testRanker(absList, modelFilename, fold=fold)
      else:
        for lf in ['group', 'outcome', 'eventrate', 'number']:
          self.testRanker(absList, modelFilename, fold=fold, includeLabeling=[lf])
          
  def assignUsingRules(self, absList, includeLabeling=[]): 
    """ assign re-ranked labels using rules """                         
    self.computeSentenceFeatureVectors(absList, includeLabeling, forTraining=False)
    for abstract in absList:
      for sentence in abstract.sentences:
        self.assignMostPopularLabeling(sentence, includeLabeling)    
           
  
      
  def trainRanker(self, absList, modelFilename, includeLabeling=[]):
    """ train a ranker model from a given training file """
    trainFilename = self.__getFilename('features.rerank.train.txt', fold=None, includeLabeling=includeLabeling)
    modelFilename = self.__getFilename(modelFilename, fold=None, includeLabeling=includeLabeling)
   
    self.computeAndWriteFeatures(absList, trainFilename, includeLabeling, forTraining=True)

    cmd = 'bin/svm_rank_learn -c 20.0 %s %s' % (trainFilename, modelFilename)
    print cmd
    os.system(cmd)
  
    
  def testRanker(self, absList, modelFilename, fold, includeLabeling=[]):
    """ apply a trained ranker to a given test file """         
    fString = '.' + '-'.join(includeLabeling)
    
    testFilename = self.__getFilename('features.rerank.test.txt', fold, includeLabeling)
    resultFilename = self.__getFilename('rerank.results.txt', fold, includeLabeling)
    modelFilename = self.__getFilename(modelFilename, fold=None, includeLabeling=includeLabeling)
        
    featureVectors = self.computeAndWriteFeatures(absList, testFilename, includeLabeling, forTraining=False)
      
    cmd = 'bin/svm_rank_classify %s %s %s' % (testFilename, modelFilename, resultFilename) 
    print cmd
    os.system(cmd)

    
    # get probabilites from result file
    self.readResultFileAndAssignScores(featureVectors, resultFilename)

    # chose the most likely association for each value
    for abstract in absList:
      for s in abstract.sentences:
        self.assignMostLikelyLabels(s, includeLabeling)
#        self.assignMostPopularLabeling(s, includeLabeling)
        
        

  def computeAndWriteFeatures(self, absList, featureFilename, includeLabeling, forTraining):
    """ pre-computed features for each sentence to a file """
    self.computeSentenceFeatureVectors(absList, includeLabeling, forTraining)
    featureVectors = self.getFeatureVectorList(absList)    
    self.writeFeatureFile(featureVectors, featureFilename, forTraining)
    return featureVectors
  
  
  def __getFilename(self, filename, fold, includeLabeling):
    if fold != None:
      foldString = '%d.' % fold
    else:
      foldString = ''
    filename = filename.strip('txt') + foldString  
   
    if len(includeLabeling) > 0:
      fString = '-'.join(includeLabeling) 
      filename = filename + fString + '.'
       
    filename = filename + 'txt'
    return filename
  


  def hasNumberLabels(self, absList): 
    for abstract in absList:
      for s in abstract.sentences:
        for token in s.tokens:
          m = token.getLabelMatches(['on', 'gs'])
          if len(m) > 1:
            print abstract.id,'!!!!!!!!!!! there be labels'
            print m
            raise
    print '--- clean'
   
  def readResultFileAndAssignScores(self, featureVectors, resultFilename):
    """ read a result file and assign scores to each feature vector in a list of feature vectors """
    resultLines = open(resultFilename, 'r').readlines()
    i = 0    # current feature vector
    for line in resultLines:
      try:
        parsedLine = line.strip().split()
        score = float(parsedLine[0])
        featureVectors[i].score = score
        i = i + 1
      except:
        print 'Error parsing re-ranker result file'
        print 'i = %d, len(featureVectors) = %d, len(resultLines) = %d, line = %s, parsedLine = %s' \
            % (i, len(featureVectors), len(resultLines), line, parsedLine)
    
  def assignMostPopularLabeling(self, sentence, includeLabeling=['group', 'outcome', 'eventrate', 'number']):
    """ ignore re-ranker score. Identify the labeling with largest number of popular tags """
    maxScore = -1
    maxEntityLabels = -1
    bestTuple = None
    minAvgRank = 9999
#    featureNames = {'group':'pPopularGroup', 'outcome':'pPopularOutcome', 'eventrate':'pPopularEventrate', \
#                    'number':'pPopularNumber'}
    for fv in sentence.features:
      score = 0
      pEntityLabels = 0
      avgRank = float(fv.tuple.groupLabeling.rank + fv.tuple.outcomeLabeling.rank + fv.tuple.eventrateLabeling.rank \
               + fv.tuple.numberLabeling.rank) / 4
      for lf in includeLabeling:      
        try:
#          lName = lf[0].upper() + lf[1:]
#          popFeatureName = 'pPopular' + lName
#          featureId = self.getFeatureId(popFeatureName)
#          score += fv.features[featureId]
#          pEntityFeatureName = 'p' + lName + 'Tokens'
#          featureId = self.getFeatureId(pEntityFeatureName)
#          pEntityLabels += fv.features[featureId]
          labeling = fv.tuple.getLabeling(lf)
          score += fv.tuple.percentMatchesPopular(labeling, weights=self.labelingWeights)
          pEntityLabels += fv.tuple.percentEntityLabels(labeling.labels)
        except:
          print fv.features
          print includeLabeling
          raise
      if len(includeLabeling) > 1:
        score = score / len(includeLabeling)
        pEntityLabels = pEntityLabels / len(includeLabeling)
        
      if score > maxScore or (score == maxScore and pEntityLabels > maxEntityLabels) \
         or (score == maxScore and pEntityLabels == maxEntityLabels and avgRank < minAvgRank):
        maxScore = score
        bestTuple = fv.tuple
        maxEntityLabels = pEntityLabels
        minAvgRank = avgRank
        
        
    if bestTuple == None:
      print '@@@@@@ no popular labeling found'
      print includeLabeling
      raise
#      for fv in sentence.features:
#      score = 0
#      for lf in includeLabeling:
#        featureId = self.getFeatureId(featureNames[lf])
#        if featureId in fv.features:
#          score += fv.features[featureId]
  
    for tIdx, token in enumerate(sentence): 
      bestTuple.addAllLabels(tIdx, includeLabeling)
    

  def assignMostLikelyLabels(self, sentence, includeLabeling):
    """ look for the labeling that is most likely out of list of possible labeling combinations for a sentence """
    minScore = 999
    bestTuple = None
    for fv in sentence.features:
      if fv.score < minScore:
        minScore = fv.score
        bestTuple = fv.tuple
#    if bestTuple != None:
#      # an alternate labeling is better 
#      # remove prior labelings and use new one
#      print 'Assigning alternate labeling (group=%d, outcome=%d, eventrate=%d, number=%d), score=%.2f\n' \
#          % (bestTuple.groupLabeling.rank, bestTuple.outcomeLabeling.rank, bestTuple.eventrateLabeling.rank,\
#           bestTuple.numberLabeling.rank, minScore)
      
    for tIdx, token in enumerate(sentence): 
#        if len(includeLabeling) == 0 or 'number' in includeLabeling:   
#          token.removeAllLabels(['on','gs'])    
#          token.removeAllLabels(self.entityTypes)
      bestTuple.addAllLabels(tIdx, includeLabeling)
        
  def removeCurrentLabels(self, absList):
    """ remove all previously assigned labels from each sentence. 
        This only applies to labels addressed by re-ranker """
    print '----------- Removing:', self.entityTypes
    for abstract in absList:
      for sentence in abstract.sentences:
        for token in sentence:
          token.removeAllLabels(self.entityTypes)
          if token.hasLabel('group') or token.hasLabel('outcome') or token.hasLabel('on') or token.hasLabel('gs'):
            print '???? removeAllLabels not removing!!!'
            print self.entityTypes
          

                
  def writeFeatureFile(self, featureVectors, filename, forTraining):
    """ write list of feature vectors out to a file """
    featureFile = open(filename, 'w')
    featureFile.write('# ')
    i = 0
    for f, id in self.featureIds.items():
      if i > 4:
        featureFile.write('\n# ')
        i = 0
      else: 
        i += 1
      featureFile.write('%s:%d, '%(f,id))
      
    featureFile.write('\n')
    for fv in featureVectors:
      fv.write(featureFile)
    featureFile.close()

  def computeStats(self, absList, out=None, errorOut=None):
    """ compute RPF stats for detected mentions in a list of abstracts.
        write results to output stream. """
    self.groupFinder.computeStats(absList, out, errorOut)
    self.groupFinder.writeLabelings(absList, 'groupfinder.rerank.labels.txt')
    
    self.outcomeFinder.computeStats(absList, out, errorOut)
    self.outcomeFinder.writeLabelings(absList, 'outcomeFinder.rerank.labels.txt')
    
    self.eventrateFinder.computeStats(absList, out, errorOut)
    self.eventrateFinder.writeLabelings(absList, 'eventrateFinder.rerank.labels.txt')
    
    self.numberFinder.computeStats(absList, out, errorOut)
    self.numberFinder.writeLabelings(absList, 'numberFinder.rerank.labels.txt')  
    
  def getFeatureVectorList(self, absList):
    """ return list of all feature vectors in for a list of abstracts """
    fvList = []
    for abstract in absList:
      for sentence in abstract.sentences:
        if len(sentence.features) != 1:
          for fv in sentence.features:
            fvList.append(fv)
    return fvList
  
  def computeFeatures(self, absList, mode):
    """ compute features for each token in each abstract in a given
        list of abstracts.
        
        mode = 'train', 'test', or 'crossval'
    """
    pass        
 
  def computeSentenceFeatureVectors(self, absList, includeLabeling, forTraining):    
    """ Calculate feature vectors for each comparison of possible labeling combinations of a sentence 
    """
    qid = 1
    for abstract in absList:
      for sentence in abstract.sentences:
#        featureMax = {}
        labelTuples = self.getLabelTuples(sentence, includeLabeling)
        
        featureVectors = []
        for lTuple in labelTuples:
          lTuple.computeTupleValues(includeLabeling)
        
        recomputeAnnotatedMentions = True
        weights = {}
        weights['group']      = {'fp':1, 'fn':1, 'dup':1}
        weights['outcome']    = {'fp':1, 'fn':1, 'dup':1}
        weights['eventrate']  = {'fp':1, 'fn':1, 'dup':1}
        weights['on']         = {'fp':1, 'fn':1, 'dup':1}
        weights['gs']         = {'fp':1, 'fn':1, 'dup':1}
        
        for lTuple in labelTuples:
          fv = FeatureVector(lTuple)
          lError = lTuple.computeTupleMentionError(recomputeAnnotatedMentions, errorWeights=weights)
          recomputeAnnotatedMentions = False
#          lError = lTuple.computeTupleTokenError()
          fv.label = lError
          fv.qid = qid
          
          # compute features
          for name, value in lTuple.featureValues.items():
            featureId = self.getFeatureId(name)
            fv.addFeature(featureId, value)
#            if featureId not in featureMax or value > featureMax[featureId]:
#              featureMax[featureId] = value
##            if name not in featureMin or value < featureMin[name]:
##              featureMin[name] = value

          featureVectors.append(fv)
                    
        sentence.features = featureVectors
        qid += 1

        # normalize features for each sentence
#        for fv in sentence.features:
#          for featureId, value in fv.features.items():
#            if featureMax[featureId] > 0:
#              fv.features[featureId] = float(value)/featureMax[featureId]
            
              
 

  
  def getLabelTuples(self, sentence, includeLabeling):
    """ return hash of label tuples (combinations of alternate classifier labelings) for a sentence """
    if len(includeLabeling) == 0:
      includeAll = True
    else:
      includeAll = False
      
    if includeAll or 'group' in includeLabeling:
#      groupMaxK = self.maxTopK
      groupMaxK = 1
    else:
      groupMaxK = 1
    if includeAll or 'outcome' in includeLabeling:
      outcomeMaxK = self.maxTopK
    else:
      outcomeMaxK = 1
    if includeAll or 'eventrate' in includeLabeling:
      eventrateMaxK = 1 #self.maxTopK
    else:
      eventrateMaxK = 1
    if includeAll or 'number' in includeLabeling:
      numberMaxK = 1 #self.maxTopK
    else:
      numberMaxK = 1
      
    gTopK = self.getTopKLabelings(sentence, self.groupFinder, groupMaxK)
    oTopK = self.getTopKLabelings(sentence, self.outcomeFinder, outcomeMaxK)
    eTopK = self.getTopKLabelings(sentence, self.eventrateFinder, eventrateMaxK)
    nTopK = self.getTopKLabelings(sentence, self.numberFinder, numberMaxK)
    
#    print len(gTopK), len(oTopK), len(eTopK), len(nTopK)
    labelTuples = []                    
    for gRank, gLabels in enumerate(gTopK):
      for oRank, oLabels in enumerate(oTopK):
        for eRank, eLabels in enumerate(eTopK):
          for nRank, nLabels in enumerate(nTopK):
            lTuple = LabelTuple()
            lTuple.groupLabeling = Labeling(sentence, gLabels, gRank, self.groupFinder)
            lTuple.outcomeLabeling = Labeling(sentence, oLabels, oRank, self.outcomeFinder)
            lTuple.eventrateLabeling = Labeling(sentence, eLabels, eRank, self.eventrateFinder)
            lTuple.numberLabeling = Labeling(sentence, nLabels, nRank, self.numberFinder)
            lTuple.sentence = sentence
            labelTuples.append(lTuple)
    return labelTuples                
            
        
    
  def getTopKLabelings(self, sentence, finder, topK):
    """ return list of top k sequence labelings for the sentence """
    labelings = []
    for k in range(min(topK,finder.tokenClassifier.topK)):
      topKLabelingExists = False
      sequenceLabels = []
      for token in sentence:
        if finder.entityTypesString in token.topKLabels and k < len(token.topKLabels[finder.entityTypesString]):
          label = token.topKLabels[finder.entityTypesString][k]
          topKLabelingExists = True
        else:
          # give each token a label. number finder labelings typically only label numbers and not other tokens.
          label = TokenLabel('other')
          label.prob = 0
        sequenceLabels.append(label)
      if topKLabelingExists or k == 0:
        # only keep labeling if it is the first one (may be all 'other'), or if the labeling exists.
        labelings.append(sequenceLabels)
    
    return labelings
        
  def getFeatureId(self, feature):
    """ return the official id used for this feature by the classifier.
        Create an Id if it does not already have one """
    if feature in self.featureIds:
      return self.featureIds[feature]
    else: 
      newId = len(self.featureIds)+1
      self.featureIds[feature] = newId
      return newId
        

