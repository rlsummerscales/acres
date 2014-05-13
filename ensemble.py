#!/usr/bin/python
# author: Rodney Summerscales

import sys
import os.path
import random
from finder import Finder
from basetokenclassifier import TokenLabel

class BallotBox:
  """ Manage label votes. determine majority voter """
  candidates = {}
  entityTypes = None
  
  def __init__(self, entityTypes):
    self.entityTypes = entityTypes + ['other']
    self.candidates = {}
    self.clear()
    
  def clear(self):
    """ erase votes """
    for eType in self.entityTypes:
      self.candidates[eType] = 0
  
  def addVote(self, label, nVotes=1, weight=1):
    """ count new label vote """
    self.candidates[label] += nVotes*weight
    
  def winner(self, countOther=True):
    """ return winning label or None if tie """
    maxVotes = 0
    winningLabel = None

    for label, voteCount in self.candidates.items():
      if label != 'other' or countOther:          
        if voteCount > maxVotes:
          maxVotes = voteCount
          winningLabel = label
  #      elif voteCount == maxVotes and label != 'other':
        elif voteCount == maxVotes:
          winningLabel = None
    return winningLabel                                              

class EnsembleFinder(Finder):
  """ Implements an ensemble classifier using a given classifier.
      """
  finderType = 'ensemble'
  finder = None
  type = None
  nClassifiers = 1
  ensembleTypes = None    
  modelFilenames = None
  modelPath = None
  duplicatesAllowed = False
  percentOfTraining = 0
  randomSeed=42
  baggedFeatures = []
  countOther = True
  rerankType = 'vote'
  
  def __init__(self, ensembleType, finder, nClassifiers, modelPath, percentOfTraining=0,\
                duplicatesAllowed=False, randomSeed=42, rerankType='vote', countOther=True):
    """ Create an ensemble classifier.
        type = 'feature', 'featureType', 'abstract'
        finder = classifier to create copies of
        nClassifiers = number of classifiers in the ensemble
        percentOfTraining = is percentage of the training set used for each classifier's training set
        (if 0, then the training sets are disjoint and there is no overlap)
        duplicates = are duplicate training examples allowed
        entityTypes = list of mention types (e.g. group, outcome) to find
        """
    Finder.__init__(self, finder.entityTypes)
    self.finderType = 'ensemble'
    self.type = ensembleType
    self.finder = finder
    self.nClassifiers = nClassifiers
    self.duplicatesAllowed = duplicatesAllowed
    self.percentOfTraining = percentOfTraining
    self.randomSeed = randomSeed
    self.baggedFeatures = []
    self.modelPath = modelPath
    if self.modelPath[-1] != '/':
      self.modelPath = self.modelPath + '/'
    self.countOther = countOther
    self.rerankType = rerankType
    
    self.modelFilenames = []    
    for i in range(self.nClassifiers):
      self.modelFilenames.append('%s%s.%d.train.model' %(self.modelPath,self.entityTypesString,i))

    self.ensembleTypes = set([])
    for i in range(self.nClassifiers):
      for eType in self.entityTypes:
        self.ensembleTypes.add(self.toEnsembleLabel(eType, i))


 
  def toEnsembleLabel(self, label, i):
    """ return string for the unique ensemble version of the label """
    return '%s_%d' % (label, i)

  def toRegularLabel(self, ensembleLabel):
    """ parse ensemble label and return a string containing the original label and index of classifier """
    [label, cIndex] = ensembleLabel.split('_') 
    return (label, int(cIndex))
  
  def computeFeatures(self, absList, mode=''):
    """ compute classifier features for each token in each abstract in a
        given list of abstracts. 

        mode = 'test', 'train', or 'crossval'
        
    """
    self.finder.computeFeatures(absList, mode)
    
  def train(self, absList, modelfilename=''):
    """ Train an ensemble of models given a list of abstracts 
        ignores modelfilename """
    if self.type == 'featureType':
      self.featureTypeBagging(absList, modelfilename)
    elif self.type == 'feature':
      self.featureBagging(absList, modelfilename)
    else:
      self.abstractBagging(absList, modelfilename)
    
        
  def featureTypeBagging(self, absList, modelfilename):
    self.baggedFeatures = []
    self.nClassifiers = 3
    for i in range(3):
      self.baggedFeatures.append(set([]))
    for abstract in absList:  
#      print abstract.id 
      for sentence in abstract.sentences:
        for token in sentence:
          for f in token.features['lexical']:
            self.baggedFeatures[0].add(f)
#            self.baggedFeatures[-1].add(f)
          for f in token.features['semantic']:
            self.baggedFeatures[0].add(f)
#            self.baggedFeatures[-1].add(f)
          for f in token.features['sentence']:
            self.baggedFeatures[0].add(f)
#            self.baggedFeatures[-1].add(f)
          for f in token.features['syntactic']:
            self.baggedFeatures[1].add(f)
#            self.baggedFeatures[-1].add(f)
          for f in token.features['tContext']:
            self.baggedFeatures[2].add(f)
#            self.baggedFeatures[-1].add(f)
          
    for i in range(self.nClassifiers):        
      print 'Number of bagged features =', len(self.baggedFeatures[i])
      print 'training:', self.entityTypesString, i
      self.useBaggedFeatures(self.baggedFeatures[i], absList, self.modelFilenames[i], self.finder.train)
            
              
    
        
  def featureBagging(self, absList, modelfilename):
    """ Train an ensemble of models given a list of abstracts.
        Ensemble is created with different random subsets of features 
        ignores modelfilename """            
    random.seed(self.randomSeed)    
    allFeatures = set([])        
    for abstract in absList:  
#      print abstract.id 
      for sentence in abstract.sentences:
        for token in sentence:
          fs = token.getFeatureSet()
          for f in fs:
            allFeatures.add(f)
    nFeatures = len(allFeatures)
    nBagged = int(nFeatures*self.percentOfTraining)
    print 'Total number of features =', nFeatures
    print 'Number of bagged features =', nBagged
    for i in range(self.nClassifiers):
      self.baggedFeatures.append(set(random.sample(allFeatures, nBagged)))
#      print allFeatures-baggedFeatures
      print 'training:', self.entityTypesString, i
      self.useBaggedFeatures(self.baggedFeatures[i], absList, self.modelFilenames[i], self.finder.train)
      
  def abstractBagging(self, absList, modelfilename=''):
    """ Train an ensemble of models given a list of abstracts.
        Ensemble is created with different subsets of abstracts 
        ignores modelfilename """        
    tmpList = absList[:]
    nAbstracts = len(tmpList)
    random.seed(self.randomSeed)    
    random.shuffle(tmpList)
    
    # no replacement. perfect partition
    if self.percentOfTraining == 0:
      setSize = nAbstracts / float(self.nClassifiers) 
      trainSet = [tmpList[int(round(setSize * i)): int(round(setSize * (i + 1)))] for i in xrange(self.nClassifiers) ]
    else:
      setSize = int(nAbstracts*self.percentOfTraining)
      trainSet = []      
      for i in range(self.nClassifiers):
        trainSet.append([])
        if self.duplicatesAllowed:
          for trainEx in range(setSize):
            absIdx = random.randint(0,nAbstracts-1)
            trainSet[i].append(tmpList[absIdx])
        else:
          trainSet[i].append(random.sample(tmpList, setSize))
        
    
    for i in range(self.nClassifiers):
      print 'training:', self.entityTypesString, i, len(trainSet[i])
      for abstract in sorted(trainSet[i]):
        print abstract.id,
      print
      self.finder.train(trainSet[i], self.modelFilenames[i])
    
    
  def renameLabels(self, absList, classifierIndex):
    for abstract in absList:
      for sentence in abstract.sentences:
        for token in sentence:
          lMatches = token.getLabelMatches(self.entityTypes)
          for label in lMatches:
            token.addLabel(self.toEnsembleLabel(label, classifierIndex))
            token.removeLabel(label)
            
  def useBaggedFeatures(self, baggedFeatures, absList, modelfilename, f):
    for abstract in absList:   
      for sentence in abstract.sentences:
        for token in sentence:
          token.filterFeatures(baggedFeatures)
          
    f(absList, modelfilename)
    
    for abstract in absList:   
      for sentence in abstract.sentences:
        for token in sentence:
          token.restoreFeatures()
              
              
  def test(self, absList, modelfilename='', fold=None):
    """ Apply ensemble of classifiers to given list of abstracts. 
        Ignores any given model file.
        """           
    for i in range(self.nClassifiers):
      print 'test:', self.entityTypesString, i
      if self.type == 'abstract':
        self.finder.test(absList, self.modelFilenames[i])
      else:
        self.useBaggedFeatures(self.baggedFeatures[i], absList, self.modelFilenames[i], self.finder.test)
      self.renameLabels(absList, i)
      
#    resultFilename = '%s%s.r%d.ensemble.txt'%(self.entityTypesString, self.getFoldString(fold), self.randomSeed)
#    resultsOut = open(resultFilename,'w')
    
    print self.entityTypesString
    for abstract in absList:
#      resultsOut.write('---%s---' % abstract.id)
      for sentence in abstract.sentences:
        for token in sentence:
          token.topKLabels[self.entityTypesString] = []  
          for i in range(self.nClassifiers):
            token.topKLabels[self.entityTypesString].append(TokenLabel('other'))
          
          eLabelMatches = token.getLabelMatches(self.ensembleTypes)
          
          for eLabel in eLabelMatches:
            [label, i] = self.toRegularLabel(eLabel)
            tLabel = TokenLabel(label)
            token.topKLabels[self.entityTypesString][i] = tLabel
#              tLabel.prob = prob
#              tLabel.sequenceProb = sequenceProb[i/2]            
            token.removeLabel(eLabel)
#            if label != 'other':
#              token.addLabel(label)            
          
#          resultsOut.write(str(ensembleLabels)+'\n')  
#          resultsOut.write('%s,  %s\n' %(token.text.ljust(12), eLabelMatches))
    self.finder.rerankLabelsAndAssign(absList, rerankType=self.rerankType, topKMax=5, fold=fold, countOther=self.countOther)
    
#    resultsOut.close()              
              
  def testWithCombination(self, absList, modelfilename='', fold=None):
    """ Apply ensemble of classifiers to given list of abstracts. 
        Ignores any given model file.
        """
    if fold != None:
      foldString = '.%d' % fold
    else:
      foldString = ''
           
    for i in range(self.nClassifiers):
      print 'test:', self.entityTypesString, i
      if self.type == 'abstract':
        self.finder.test(absList, self.modelFilenames[i])
      else:
        self.useBaggedFeatures(self.baggedFeatures[i], absList, self.modelFilenames[i], self.finder.test)
      self.renameLabels(absList, i)
      
    resultFilename = '%s%s.r%d.ensemble.txt'%(self.entityTypesString, foldString, self.randomSeed)
    resultsOut = open(resultFilename,'w')
    
    nTokens = 0
    tokenErrors = []
    ensembleLabels = []
    sharedErrors = []
    for i in range(self.nClassifiers):
      ensembleLabels.append('other')
      tokenErrors.append(0)
      sharedErrors.append([])
      for j in range(self.nClassifiers):
        sharedErrors[i].append(0)
    
    # assign ensembleLabels by majority vote
    ballotBox = BallotBox(self.entityTypes)
    for abstract in absList:
      resultsOut.write('---%s---' % abstract.id)
      for sentence in abstract.sentences:
        for token in sentence:
          nTokens += 1
          for i in range(self.nClassifiers):
            ensembleLabels[i] = 'other'
            
          ballotBox.clear()
          eLabelMatches = token.getLabelMatches(self.ensembleTypes)
          if len(eLabelMatches) < self.nClassifiers:
            otherVotes = self.nClassifiers - len(eLabelMatches)
            ballotBox.addVote('other', nVotes=otherVotes)
          
          for eLabel in eLabelMatches:
            [label, i] = self.toRegularLabel(eLabel)
            ensembleLabels[i] = label
              
            ballotBox.addVote(label)
            token.removeLabel(eLabel)
          winningLabel = ballotBox.winner(self.countOther)
          if winningLabel == None:
            winningLabel = 'other'
          if winningLabel != 'other':
            token.addLabel(winningLabel)
            
          annotationList = token.getAnnotationMatches(self.ensembleTypes)
          if len(annotationList) == 0:
            trueLabel = 'other'
          elif len(annotationList) == 1:
            trueLabel = annotationList[0]
          else:
            print abstract.id, 'ERROR: token has multiple annotations!!!'
            print sentence.toString()
            print token.text
            print annotationList
            sys.exit(-1)
                     
          for i in range(self.nClassifiers):
            if ensembleLabels[i] != trueLabel:
              tokenErrors[i] += 1
              
              for j in range(self.nClassifiers):
                if ensembleLabels[j] == ensembleLabels[i]:
                  sharedErrors[i][j] += 1
          
#          resultsOut.write(str(ensembleLabels)+'\n')  
          resultsOut.write('%s, %10s, %10s, %8s, %s, %s\n' %(token.text.ljust(12), trueLabel, winningLabel, trueLabel==winningLabel,  \
                                  ballotBox.candidates, eLabelMatches))
      
      resultsOut.write('Total Errors: %s\n'%(str(tokenErrors)))    
      for i in range(self.nClassifiers):
        resultsOut.write('%d (shared errors): %s\n' %(i, str(sharedErrors[i])))       

    resultsOut.write('Total tokens: %d\n'%(nTokens))    
    resultsOut.write('Error rates: ')
    for i in range(self.nClassifiers):
      resultsOut.write('%.2f '%(float(tokenErrors[i])/nTokens))
      
    resultsOut.write('\nComplementarity:\n')
    totalComp = 0
    for i in range(self.nClassifiers):
      for j in range(self.nClassifiers):
        if tokenErrors[i] == 0:
          c = 0
        else:
          c = 1-float(sharedErrors[i][j])/tokenErrors[i]
        totalComp += c
        resultsOut.write('%.2f '%(c))
      resultsOut.write('\n')
    nComparisons = self.nClassifiers * self.nClassifiers - self.nClassifiers
    resultsOut.write('Number of comparisons = %d\n'%(nComparisons)) 
    resultsOut.write('Total complementarity = %.4f\n'%(totalComp/nComparisons))      
    resultsOut.close()
    
  def crossvalidate(self, absList, modelPath):
    """ Apply mention finder to list of abstracts using k-fold 
        crossvalidation. The crossvalidation sets should be defined
        in the AbstractList object (absList). 
        """    
    raise NotImplementedError("Need to implement crossvalidate()")
 

  def computeStats(self, absList, statOut=None, errorOut=None):
    """ compute RPF stats for detected mentions in a list of abstracts.
        write results to output stream. """
    self.finder.computeStats(absList, statOut, errorOut)
