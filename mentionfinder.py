#!/usr/bin/python
# Compute features for labeling noun phrases as group, outcome, other
# author: Rodney Summerscales

import sys
import os.path
import nltk
import random

from nltk.corpus import stopwords
from basementionfinder import BaseMentionFinder
from tokenlist import TokenList
from mention import Mention
from ensemble import BallotBox
from irstats import IRstats

def findPathToVerb(sentence, entityType, pathCounts):
  """ find the path from each word to a verb in the sentence. 
      record the path in pathCounts"""
#  sentence.dependencyGraphBFS()
#  print '------------'
#  print sentence.toString()+':'
  for token in sentence:
    depVerbPath = token.pathToVerb()
#    print '  --',depVerbPath
    if depVerbPath not in pathCounts:
      pathCounts[depVerbPath] = IRstats()  
    if token.hasAnnotation(entityType):
      pathCounts[depVerbPath].incTP()
    else:
      pathCounts[depVerbPath].incFP()


def importantDependencyPaths(absList, entityTypes):  
  pathCounts = {}
  dependencyPaths = {}
  for eType in entityTypes:
    dependencyPaths[eType] = set([])
    pathCounts[eType] = {}

  for abstract in absList:
    for sentence in abstract.sentences:
      for eType in entityTypes:
        findPathToVerb(sentence, eType, pathCounts[eType])
  for depPath, irstats in pathCounts[eType].items():
    if irstats.tp > 5 and irstats.precision() > 0.5:
      dependencyPaths[eType].add(depPath)
#    for eType in entityTypes:
#      print self.dependencyPaths[eType]
  return dependencyPaths

######################################################################
# Experimental mention finder
######################################################################

class MentionFinder(BaseMentionFinder):
  """ Used for training/testing a classifier to find mentions 
      in a list of abstracts.
      """
  useReport = True
  labelSet = None
  validSemanticTypes = set(['aapp', 'acab', 'acty', 'aggp', 'antb', 'bacs', 'blor', \
      'bmod', 'bodm', 'bpoc', 'carb', 'cgab', 'chvs', 'clna', 'clnd', 'diap', \
      'dsyn', 'edac', 'evnt', 'fndg', 'grup', 'hcro', 'hlca', 'hops', 'horm', \
      'inbe', 'inch', 'inpo', 'medd', 'menp', 'mnob', 'orch', 'orga', 'orgf', \
      'ortf', 'patf', 'phsf', 'phsu', 'sbst', 'sosy', 'strd', 'tmco', 'topp', \
      'virs', 'vita'])
  intOnlyTypes = set(['gs', 'on'])
  rateOnlyTypes = set(['eventrate'])
  allNumberTypes = intOnlyTypes.union(rateOnlyTypes)
  commonLemmas = {}
#  dependencyPaths = {}
  tokenFilter = None
  randomSeed = 42
  
  def __init__(self, entityTypes, tokenClassifier, labelFeatures=[], useReport=True, tokenFilter=None, randomSeed=42):
    """ Create a new mention finder to find a given list of mention types.
        entityTypes = list of mention types to find (e.g. group, outcome)
    """
    BaseMentionFinder.__init__(self, entityTypes, tokenClassifier)
    self.useReport = useReport
    self.commonLemmas['group'] = set(['group', 'control', 'placebo', 'treatment'])
    self.commonLemmas['outcome'] = set(['cure', 'recover', 'improve', 'mortality', 
                                 'morbidity', 'die', 'adverse', 'event'])
    self.dependencyPaths = {}
    self.labelSet = set(labelFeatures)
    self.tokenFilter = tokenFilter
    self.randomSeed = randomSeed
    random.seed(self.randomSeed)    

  def train(self, absList, modelfilename):
    """ Train a mention finder model given a list of abstracts """
    self.tokenClassifier.train(absList, modelfilename, self.entityTypes, self.tokenFilter)
#    pass
  
  def test(self, absList, modelfilename, fold=None):
    """ Apply the mention finder to a given list of abstracts
        using the given model file.
        """
    foldString = self.getFoldString(fold)
    
    labeledFilename = 'tokens.%d.%s%s.txt' % (self.randomSeed, self.entityTypesString, foldString)    
    self.tokenClassifier.test(absList, modelfilename, labeledFilename, self.entityTypes, self.tokenFilter)
    self.readLabelsAndAssign(absList, labeledFilename)

  def readLabelsAndAssign(self, absList, labeledFilename, fold=None):
    """ read the file containing labels assigned by the classifier and 
        assign the labels to the appropriate tokens """
    # store assigned labels in abstract list
    # read labeled phrase file
    labels = self.tokenClassifier.readLabelFile(labeledFilename, self.entityTypes)
    nSentences = 0
    i = 0
    for abstract in absList:
      for sentence in abstract.sentences:
        nSentences += 1
        for token in sentence.tokens:
          if self.tokenFilter == None or self.tokenFilter(token) == True:
            if i >= len(labels):
              raise StandardError("not all tokens are labeled")
 
            token.topKLabels[self.entityTypesString] = labels[i]   
            token.addLabel(labels[i][0].label)         

            i += 1
    
#    if 'condition' in self.entityTypes:        
#      self.rerankLabelsAndAssign(absList, rerankType='popular', topKMax=3)  
    labelFilename = '%s.r%d%s.labels.txt'%(self.entityTypesString, self.randomSeed, self.getFoldString(fold))        
    self.writeLabelings(absList, labelFilename)
        
  def writeLabelings(self, absList, filename, topK=0):
    """ output label assignments for each token along with alternate labelings (if available) to a file """
    nTokens = 0
    tokenErrors = []
    ensembleLabels = []
    sharedErrors = []
    for i in range(topK):
      ensembleLabels.append('other')
      tokenErrors.append(0)
      sharedErrors.append([])
      for j in range(topK):
        sharedErrors[i].append(0)
    
    
    resultsOut = open(filename,'w')
    for abstract in absList:
      resultsOut.write('---%s---\n' % abstract.id)      
      for sentence in abstract.sentences:
        for token in sentence:
          if self.entityTypesString in token.topKLabels:
            resultsOut.write('%s' % ' '.ljust(50))
            for k in range(len(token.topKLabels[self.entityTypesString])):   
              resultsOut.write('%2d ' % int(100*token.topKLabels[self.entityTypesString][k].sequenceProb))
            resultsOut.write('\n')
            break
          
        for token in sentence:
          if self.entityTypesString in token.topKLabels:
            eLabelMatches = token.getLabelMatches(self.entityTypes)
            nMatches = len(eLabelMatches)
            if nMatches == 0:
              label = 'other'
            elif nMatches == 1:
              label = eLabelMatches.pop()
            else:
              # ??? create combined label from first char of each label
              label = ''
              for m in eLabelMatches:
                label = label + m[0]
              print '%s Warning: %s has multiple label matches'%(abstract.id, token.text)
              print eLabelMatches   
            self.writeResults(resultsOut, token, label, token.topKLabels[self.entityTypesString])
          

            nTokens += 1
            ensembleLabels = token.topKLabels[self.entityTypesString][:topK]           
            annotationList = token.getAnnotationMatches(self.entityTypes)
            if len(annotationList) == 0:
              trueLabel = 'other'
            elif len(annotationList) == 1:
              trueLabel = annotationList.pop()
            else:
              print abstract.id, 'ERROR: token has multiple annotations!!!'
              print sentence.toString()
              print token.text
              print annotationList
              sys.exit(-1)
            
                   
            for i in range(topK):
              if ensembleLabels[i].label != trueLabel:
                tokenErrors[i] += 1
                
                for j in range(topK):
                  if ensembleLabels[j].label == ensembleLabels[i].label:
                    sharedErrors[i][j] += 1 

        resultsOut.write('\n')
                    
      resultsOut.write('Total Errors: %s\n'%(str(tokenErrors)))    
      for i in range(topK):
        resultsOut.write('%d (shared errors): %s\n' %(i, str(sharedErrors[i])))       
                     
    resultsOut.write('Total tokens: %d\n'%(nTokens))    
    resultsOut.write('Error rates: ')
    for i in range(topK):
      resultsOut.write('%.2f '%(float(tokenErrors[i])/nTokens))
      
    resultsOut.write('\nComplementarity:\n')
    totalComp = 0
    for i in range(topK):
      for j in range(topK):
        if tokenErrors[i] == 0:
          c = 0
        else:
          c = 1-float(sharedErrors[i][j])/tokenErrors[i]
        totalComp += c
        resultsOut.write('%.2f '%(c))
      resultsOut.write('\n')
        
    nComparisons = topK * topK - topK
    if nComparisons > 0:
      resultsOut.write('Number of comparisons = %d\n'%(nComparisons)) 
      resultsOut.write('Total complementarity = %.4f\n'%(totalComp/nComparisons))     
    resultsOut.close() 
        
  def rerankLabelsAndAssign(self, absList, rerankType='popular', topKMax=0, fold=None, countOther=True):
    """ re-rank top K sentence labelings and assign 
        Assumes the top labeling was previously applied. Removes this labeling then applies the new one
        
        rerankType = algorithm used for selecting alternate ranking
             'popular' (default) selects the labeling containing the most tokens which have the most popular tag
             'best'    uses annotated information to identify the best labeling 
             'vote'    uses majority vote for each token 
             'any'     uses any non-other label for each token
             """
    nSentences = 0
    usedAlternateLabeling = 0
    nPerfectAltLabelings = 0
    nPerfectTopLabelings = 0
    weights = []
    k = self.tokenClassifier.topK
    topKsum = k*(k+1)/2
    for i in range(self.tokenClassifier.topK, 0, -1):
#      weights.append(1.0/k)
#      weights.append(float(i)/topKsum)
#      weights.append(i)
      weights.append(1.0)
#    print weights
    
#    resultsOut = open(self.entityTypesString+'.rerank.labels.txt','w')
    for abstract in absList:
#      resultsOut.write('---%s---\n' % abstract.id)
      for sentence in abstract.sentences:
        nSentences += 1
        nError = 0        
        if self.tokenClassifier.returnsAlternateLabels():
          if rerankType == 'best':
            (labelList, bestK, nError) = self.selectBestLabeling(sentence, topKMax)
          elif rerankType == 'vote':
            (labelList, bestK) = self.selectMostPopular(sentence, countOther, topKMax=topKMax)
          elif rerankType == 'any':
            (labelList, bestK) = self.selectMostPopular(sentence, countOther=False, topKMax=topKMax)            
          else:            
            (labelList, bestK) = self.selectLabelingByReranking(sentence, countOther=countOther, weights=weights,\
                                                                 topKSelectMax=topKMax)
        else:
          (labelList, bestK) = self.selectTopKLabeling(sentence, 0)
          
        if bestK != 0:
          usedAlternateLabeling += 1
          if nError == 0:
            nPerfectAltLabelings += 1
        else:
          if nError == 0:
            nPerfectTopLabelings += 1
        
        
        # output sentence labeling probabilities
#        for token in sentence:
#          if self.entityTypesString in token.topKLabels:
#            resultsOut.write('%s' % ' '.ljust(50))
#            for k in range(len(token.topKLabels[self.entityTypesString])):   
#              resultsOut.write('%2d ' % int(100*token.topKLabels[self.entityTypesString][k].sequenceProb))
#            resultsOut.write('\n')
#            break
            
        labelIdx = 0         
        for token in sentence:
          if self.entityTypesString in token.topKLabels:
            newLabel = labelList[labelIdx]
#            print token.text, newLabel, ':',
#            for tlabel in token.topKLabels[self.entityTypesString]:
#              print tlabel.label,
#            print 'has newLabel =',token.topKLabels[self.entityTypesString][0].label, token.hasLabel(token.topKLabels[self.entityTypesString][0].label)
            token.removeAllLabels(self.entityTypes)
            if newLabel != 'other':
              self.assignLabel(token, newLabel)
            labelIdx += 1  
#            if bestK != 0 and newLabel != token.topKLabels[self.entityTypesString][0].newLabel:
#              # must remove previous newLabel
#              token.removeLabel(token.topKLabels[self.entityTypesString][0].newLabel)
#              self.assignLabel(token, newLabel)
#            self.writeResults(resultsOut, token, newLabel, token.topKLabels[self.entityTypesString], bestK)
            
          
#        resultsOut.write('\n')
#    resultsOut.close() 

    labelFilename = '%s.r%d%s.rerank.%s.labels.txt'%(self.entityTypesString, self.randomSeed, self.getFoldString(fold), rerankType)            
    self.writeLabelings(absList, labelFilename, topK=topKMax)
    
    if nPerfectTopLabelings > 0 and usedAlternateLabeling > 0:
      print '%d/%d (%.1f%%) sentences used alternate labeling' \
              % (usedAlternateLabeling, nSentences, float(usedAlternateLabeling)/nSentences*100)
      nTopLabelings = nSentences - usedAlternateLabeling           
      print '%d/%d (%.1f%%) top labelings are error-free' \
              % (nPerfectTopLabelings, nTopLabelings, float(nPerfectTopLabelings)/nTopLabelings*100)
      if usedAlternateLabeling > 0:
        print '%d/%d (%.1f%%) alternate labelings are error-free' \
              % (nPerfectAltLabelings, usedAlternateLabeling, float(nPerfectAltLabelings)/usedAlternateLabeling*100)
         


    
  def outputLabel(self, label):
    """ return abbreviated label for output purposes """
    if label == 'other':
      return '--'
    else:
      return label[0:2].upper()
    
  def trueLabel(self, token):
    """ return the true label for a given token """
    trueLabels = token.getAnnotationMatches(self.entityTypes)
    if len(trueLabels) == 0:
      return 'other'
    else:
      return trueLabels.pop()
     
  def writeResults(self, out, token, label, topKLabels=[], bestK=-1):
    """ output token labeling results """
    if len(topKLabels) > 0: 
      if bestK < 0:
        tProb = 0.0
        for tkLabel in topKLabels:
          if label == tkLabel.label:
            tProb = tkLabel.prob
      else:
        tProb = topKLabels[bestK].prob
      out.write('%s %8s  %s %s %.2f [ ' %(token.text.ljust(20), self.isLabelCorrect(token, label),\
                  self.outputLabel(self.trueLabel(token)).ljust(5), self.outputLabel(label).ljust(5), \
                  tProb))
      for tkLabel in topKLabels:
        out.write('%s '%self.outputLabel(tkLabel.label))
      out.write(']\n')
    else:
      out.write('%s %8s  %s %s \n' %(token.text.ljust(20), self.isLabelCorrect(token, label), \
              self.outputLabel(self.trueLabel(token)).ljust(5), self.outputLabel(label).ljust(5)))
           
  def isLabelCorrect(self, token, label):
    """ return true if the given label is correct for the token """
    if label != 'other':
      return token.hasAnnotation(label) 
    else:
      for mType in self.entityTypes:
        if token.hasAnnotation(mType):
          return False  # false negative. token should have this label
    return True
         
  def selectTopKLabeling(self, sentence, k):
    """ Select the labeling with index k """
    labelList = [] 
    bestK = k   
    for token in sentence.tokens:
      if self.entityTypesString in token.topKLabels:
        label = token.topKLabels[self.entityTypesString][bestK].label
        labelList.append(label)

    return (labelList, bestK)  
              
  def selectMostPopular(self, sentence, countOther, weights=[], topKMax=0, topKPercent=0):
    """ select the label from given set of alternative labels that is the most popular for this token """
    if topKMax == 0:
      topKMax = self.tokenClassifier.topK
    
    nLabels = len(self.entityTypes)+1
    
    if topKPercent > 0:
      topKPercent = 0.1
  #    topKPercent = 0.25
      realisticMaxK = int(topKPercent*pow(nLabels, len(sentence)))
      if realisticMaxK % 2 == 0:
        realisticMaxK += 1
      
      if realisticMaxK < topKMax:
  #      print '%%%%%%%%: len(sentence)=%d, nLabels=%d, topKMax=%d, realisticTopK=%d' % (len(sentence), nLabels, topKMax, realisticMaxK)  
        topKMax = realisticMaxK
      
    if len(weights) < topKMax:
      weights = []
      for i in range(topKMax, 0, -1):
  #      weights.append(1.0/k)
#        weights.append(i)
        weights.append(1.0)

    ballotBox = BallotBox(self.entityTypes)
    labelList = []
    for token in sentence:
      ballotBox.clear()
      if self.entityTypesString in token.topKLabels:
#        print self.entityTypesString, len(token.topKLabels[self.entityTypesString]), topKMax
        for k in range(min(len(token.topKLabels[self.entityTypesString]), topKMax)):
          tokenLabel = token.topKLabels[self.entityTypesString][k]
          ballotBox.addVote(tokenLabel.label, weight=weights[k])
#          print tokenLabel.label,
      
        winningLabel = ballotBox.winner(countOther)
        if winningLabel == None:
          winningLabel = 'other'
#        print 'winner=',winningLabel  
        labelList.append(winningLabel)
    return (labelList, -1)
    
  def selectLabelingByReranking(self, sentence, countOther, weights=[], topKSelectMax=0, topKCountMax=0):
    """ select the sentence labeling with the most tokens which have the most popular tags in the top k labelings
        topKSelectMax is the max k value to consider when selecting alternate labelings
        topKCountMax is the max k value to consider when determining which label is the most popular one for each token """
    if topKCountMax == 0:
      topKCountMax = self.tokenClassifier.topK
    if topKSelectMax == 0:
      topKSelectMax = self.tokenClassifier.topK

    (mostPopularLabels, bestK) = self.selectMostPopular(sentence, countOther, weights=weights, topKMax=topKCountMax, topKPercent=0.1)
    bestK = 0
    maxScore = 0
    minOther = 0

    for k in range(topKSelectMax):
      labelScore = 0
      nOther = 0
      i=0
      for token in sentence:
        if self.entityTypesString in token.topKLabels and k < len(token.topKLabels[self.entityTypesString]):
          if mostPopularLabels[i] == token.topKLabels[self.entityTypesString][k].label:
            labelScore += 1
            if mostPopularLabels[i] == 'other':
              nOther += 1
          i += 1
      if labelScore > maxScore or (labelScore == maxScore and nOther < minOther):
        bestK = k
        maxScore = labelScore
        minOther = nOther
    
    return self.selectTopKLabeling(sentence, bestK)   
  
  def nSentenceLabelings(self, sentence):
    """ return the number of top k labelings for the given sentence """
    for token in sentence:
      if self.entityTypesString in token.topKLabels:
        return len(token.topKLabels[self.entityTypesString]) 
    return 0  
  
  def selectBestLabeling(self, sentence, topKMax=0):
    """ Select the alternate labeling that best matches annotations -- for analysis purposes. """
    # there were alternate labelings. need to look at all of them to assign labels
    if topKMax == 0:
      topKMax = self.tokenClassifier.topK

    bestK = 0
    minTotalFP = 0
    minTotalFN = 0
    minTotalDuplicates = 0
    stats = {}
    aList = {}
    for mType in self.entityTypes:
      aList[mType] = sentence.getAnnotatedMentions(mType, recomputeMentions=True)
      dList = self.getTopKMentions(sentence, mType, 0) 
      stats[mType] = IRstats()   
      self.compareMentionLists(dList, aList[mType], mType, stats[mType])
      minTotalFP += stats[mType].fp
      minTotalFN += stats[mType].fn
      minTotalDuplicates += stats[mType].duplicates
      
    minTotalError = minTotalFP + minTotalDuplicates + minTotalFN
       
    if minTotalFP > 0 or minTotalFN > 0 or minTotalDuplicates > 0: 
      # find labeling that has fewest missing mentions and fewest false positives
      topK = min(self.nSentenceLabelings(sentence), topKMax) 
      for k in range(1, topK):
        totalFP = 0
        totalFN = 0
        totalDup = 0
        for mType in self.entityTypes:
          stats[mType].clear()
          dList = self.getTopKMentions(sentence, mType, k)
          self.compareMentionLists(dList, aList[mType], mType, stats[mType])
          totalFN += stats[mType].fn
          totalFP += stats[mType].fp
          totalDup += stats[mType].duplicates
        totalError = totalFP + totalDup + totalFN
        if (totalFN < minTotalFN and totalError <= minTotalError) \
          or (totalFN == minTotalFN and totalError < minTotalError):
          bestK = k
          minTotalFN = totalFN
          minTotalFP = totalFP
          minTotalDuplicates = totalDup
#    else:  
#      print sentence.toString()   
#      for mType in self.entityTypes:
#        print mType,
#        stats[mType].displayrpf()
        
              
    (labelList, bestK) = self.selectTopKLabeling(sentence, bestK)
      
    nError = minTotalFN + minTotalFP + minTotalDuplicates
    return (labelList, bestK, nError)
       
#  def selectMostMentions(self, sentence, mType, prob=1):
#    """ with a given probability, select alternate labeling that leads to max possible mentions of a given type """
#    # there were alternate labelings. need to look at all of them to assign labels
#    bestK = 0
#    maxMentions = 0
#    if random.random() < prob:
#      # find labeling that yields the most mentions
#      for k in range(self.tokenClassifier.topK):
#        mList = self.getTopKMentions(sentence, mType, k)
#        if len(mList) > maxMentions:
#          bestK = k
#          maxMentions = len(mList)
#          
#    (labelList, bestK) = self.selectTopKLabeling(sentence, bestK)
#      
#    return (labelList, bestK)
  
            
  def assignLabel(self, token, label):
    """ assign given label to a token assuming that the label is interesting and it is okay to do so """  
    if label != 'other' and self.safeToLabelNumber(token, label):
      # only one label
      token.addLabel(label)  
       
  def getTopKMentions(self, sentence, mType, k):
    """ return a list of detected mentions (Mention objects) found in the
        sentence using specified alternate labeling. 
        mType = the type of mentions (e.g. group, outcome, etc) to find 
        k = index of alternate labeling in list of alternate labelings"""
    mentionList = []
    tList = TokenList()
    for token in sentence.tokens:
      if self.entityTypesString in token.topKLabels and token.topKLabels[self.entityTypesString][k].label == mType:
        tList.append(token)
      elif len(tList) > 0:
        # no longer in a mention, but previous token was
        mentionList.append(Mention(tList, annotated=False))
        tList = TokenList()

    if len(tList) > 0:
      # add mention that includes last token in sentence
      mentionList.append(Mention(tList, annotated=False))
    return mentionList


  def safeToLabelNumber(self, token, label):
    """ return true if the token does not already have a label that conflicts with this
        one """
    if token.isNumber() == False and label not in self.allNumberTypes:
      return True
#     if token.getValue() < 0:
#       return False
    if label in self.intOnlyTypes and (token.isInteger() == False \
             or token.isPercentage() == True):
      return False
    if label in self.rateOnlyTypes and token.isPercentage() == False:
      return False   # only allow explicit percentages
#    if label in self.rateOnlyTypes and (token.isPercentage() == False \
#             and token.isInteger() == True):
#      return False
    return True
    
  def computeFeatures(self, absList, mode):
    """ compute features for each token in each abstract in a given
        list of abstracts.
        
        mode = 'train', 'test', or 'crossval'
    """
    phraseList = []
    for abs in absList:
      registryWords = self.registryWordSets(abs)
                                      
      for sentence in abs.sentences:
        sFeatures = self.sentenceFeatures(sentence)
        parenDepth = 0
        for token in sentence.tokens:
          # compute features for this token
          token.features = {}
                      
          # compute features
          token.features['lexical'] = self.tokenFeatures(token)
          token.features['semantic'] = self.semanticFeatures(token, mode, \
                                         wordSets=registryWords)
          token.features['syntactic'] = self.syntacticContextFeatures(token, mode, \
                                            parenDepth, registryWords)
          token.features['tContext'] = self.tokenContextFeatures(token, mode, 4,\
                                             registryWords)
          token.features['sentence'] = sFeatures
          
          if token.text == '-LRB-':
            parenDepth = parenDepth + 1
          elif token.text == '-RRB-':
            parenDepth = parenDepth - 1

      for sentence in abs.sentences:
        for token in sentence.tokens:          
          token.features['acronym'] = self.acronymFeatures(token, abs)
                  
  def acronymFeatures(self, token, abstract):
    """ if this token is an acronym, return features based on its expansion """
    features = set([])
    if token.isAcronym() and token.text in abstract.acronyms:
      for t in abstract.acronyms[token.text]:
        if 'lexical' in t.features:
          features = features.union(t.features['lexical'])
        if 'semantic' in t.features:   
          features = features.union(t.features['semantic'])
    return features
            
  def registryWordSets(self, abstract):
    """ build list of words for intervention, outcome and condition
        from trial registry entries """
    registryWords = {}
    if self.useReport == False or abstract.report == None:
      return registryWords
      
    registryWords['intervention'] = set([])
    registryWords['outcome'] = set([])
    registryWords['condition'] = set([])
    for intervention in abstract.report.interventions:
      for sentence in intervention.name:       
        for token in sentence:
          if token.isStopWord() == False and token.isNumber() == False \
             and token.isSymbol() == False:
            registryWords['intervention'].add(token.lemma)
    for outcome in abstract.report.outcomes:
      for sentence in outcome.name:
        for token in sentence:
          if token.isStopWord() == False and token.isNumber() == False \
             and token.isSymbol() == False:
            registryWords['outcome'].add(token.lemma)
    for condition in abstract.report.conditions:
      for sentence in condition.sentences:
        for token in sentence:
          if token.isStopWord() == False and token.isNumber() == False \
             and token.isSymbol() == False:
            registryWords['condition'].add(token.lemma)
    return registryWords
  
  

  def lexicalFeatures(self, token, prefix=''):
    """ compute and return features based only on token itself """
    features = set([])

    if token.isNumber():
      return features
            
    if token.isSpecialToken():
      if token.getSpecialTokenAnnotation() == None:
        print token.text
        print token.sentence.toString()
      features.add(prefix + 'special_term')
      features.add(prefix + token.getSpecialTokenAnnotation())
    else:
      features.add(prefix+'t_' + token.text)          
      features.add(prefix+'lemma_' + token.lemma)          
      features.add(prefix+'pos_' + token.pos)
    
    if token.isAcronym():
      features.add(prefix + 'IS_ACRONYM')
    
    return features       
    
  def numberTokenFeatures(self, token, prefix=''):
    """ compute and return features based only on token itself """
    features = set([])
      
    features.add(prefix+'is_number')  
    if token.isPercentage():
      features.add(prefix+'is_percent')  
    elif token.isInteger() or token.isNullNumberWord():
      features.add(prefix+'is_int')
    else:
      features.add(prefix+'is_float')
    
    value = token.getValue()
    if value < 0:
      features.add(prefix+'is_negative')
    else:
      if value < 10:
        features.add(prefix+'is_under_10')
  
    return features   
    
  def tokenFeatures(self, token, prefix=''):
    """ compute features based on token itself """
    if token.isNumber():
      return self.numberTokenFeatures(token, prefix)
    else:
      return self.lexicalFeatures(token, prefix)  
    
    
    
  def numberPatternFeatures(self, token, prefix=''):
    """ compute features based on token pattern that often indicate certain 
        types of quantities."""
    features = set([])
  
    if token.isImportantInteger() == False:
      return features
      
    value = token.getValue()
  
    if token.index >= 2:
      t1 = token.sentence[token.index-2]
      t2 = token.sentence[token.index-1]
      # check for n = <int>
      if t1.text == 'n' and t2.text == '=':
        features.add(prefix+'p_groupsize')
      # check for <int> / <current_token>
      if t1.isImportantInteger() and (t2.text == '/' or t2.text == 'of') \
          and t1.getValue() <= value:
        features.add(prefix+'p_groupsize')
    if (token.index + 2) < len(token.sentence):
      t1 = token.sentence[token.index + 1]
      t2 = token.sentence[token.index + 2]
      # check for <current_token>/<int>
      if (t1.text == '/' or t1.text == 'of') and t2.isImportantInteger() \
        and value <= t2.getValue():
        features.add(prefix+'p_outcomenumber')
        
    return features
    
  def umlsFeatures(self, token, prefix=''):
    """ features based on semantic types of umls chunk containing token """
    features = set([])
    
    for uc in token.umlsConcepts:
      if uc.inRxnorm:
        features.add(prefix + 'umls_rxnorm')
      for type in uc.types:
        features.add(prefix + 'umls_type_'+type)
      features.add(prefix + 'umls_'+uc.id)
    
    return features
    
  def semanticTagFeatures(self, token, prefix=''):
    """ features based on semantic tags assigned to a given token """
    features = set([])
    for tag in token.semanticTags:
#      if tag != 'group' and tag != 'people':
        features.add(prefix + 'sem_' + tag)

    return features
  
  def labelFeatures(self, token, mode, prefix=''):
    """ features based on whether a token has a given label assigned by a classifier"""
    features = set([])

    for label in self.labelSet: 
      if token.hasLabel(label, mode):
#      if token.hasLabel(label):
        features.add(prefix + 'label_' + label) 
    
    return features      
    
  def semanticFeatures(self, token, mode, prefix='', wordSets={}):
    """ features based on labels assigned by metamap and a token's presence
        in a list of words defining semantic classes
        """
    features = set([])
    features = features.union(self.labelFeatures(token, mode, prefix))  

    if token.isNumber():
      # semantic features for numbers
      if token.specialValueType != None:
        features.add(prefix + 'vtype_' + token.specialValueType)
        features.add(prefix + 'is_special_value')
      features = features.union(self.numberPatternFeatures(token, prefix))    
    else:
      # semantic features for words and other tokens      
      features = features.union(self.umlsFeatures(token, prefix))     
      features = features.union(self.semanticTagFeatures(token, prefix))    
        
      for label,wordSet in wordSets.items():
        if token.lemma in wordSet:
          features.add(prefix + 'wordset_'+label) 
      if token.hasLabel('primary_outcome'):
        features.add(prefix + 'primary_outcome') 
    return features    
 
 
 
  def closestVerb(self, token):
    """ return closest ancestor verb in phrase structure parse tree """
    verbNode = token.parseTreeNode.closestParentVerbNode()
    if verbNode == None:
      return None
    else:
      return verbNode.token
          
  def syntacticContextFeatures(self, token, mode, parenthesisDepth, wordSets={}):
    """ features based on collapsed typed dependency parse of sentence """
    features = set([])
    prefix = ''
    verbSet = set(['receive', 'allocate', 'assign', 'randomize', 'randomise', 'compare', \
                   'treat'])
    if parenthesisDepth > 0:
      features.add('inside_parens')

    if token.isNumber() == False:
      for dep in token.dependents:
        depToken = token.sentence[dep.index]
        prefix = 'dep_'
        features.add(prefix + 'type_'+dep.type)
        features = features.union(self.tokenFeatures(depToken, prefix))
        features = features.union(self.semanticFeatures(depToken, mode, prefix, wordSets))
      
    for gov in token.governors:
      if gov.isRoot() == False:
        govToken = token.sentence[gov.index]
        prefix = 'gov_'
        features.add(prefix+'type_'+gov.type)
        features = features.union(self.tokenFeatures(govToken, prefix))
        features = features.union(self.semanticFeatures(govToken, mode, prefix, wordSets))

    verbToken = self.closestVerb(token)
    if verbToken != None:
      features.add('closest_verb_' + verbToken.lemma)

    return features

  def tokenContextFeatures(self, token, mode, window, wordSets):
    """ compute features for tokens surrounding a given token """
    features = set([])
    nTokens = len(token.sentence)
    for i in range(max(0, token.index-window), min(nTokens, token.index+window+1)):
      if i == token.index:
        continue
      prefix = 'tcontext_'+str(i-token.index)+'_'
      cToken = token.sentence[i]
      features = features.union(self.tokenFeatures(cToken, prefix))
      features = features.union(self.semanticFeatures(cToken, mode, prefix, wordSets))
      
    return features
   
  def sentenceFeatures(self, sentence):
    """ features based on the sentence """
    if sentence.section != None and len(sentence.section) > 0:
      features = set(['section_'+sentence.section, 'nlm_'+sentence.nlmCategory])
    else:
      features = set([])
    return features
 
#############################################################
# unused
#############################################################   
   
#  def phraseFeatures(self, token):
#    """ compute features based on phrase that token is in """
#    features = set([])
#    phrase = token.parseTreeNode.parent
#    prefix ='phrase_'
#    features.add(prefix+'type_'+phrase.type)
#    
#    return features
#    
#  def simpleTreeContextFeatures(self, tokenIdx, window, simpleTreeTokenNodes):
#    """ compute features for tokens surrounding a given token in simplified sentence """
#    features = set([])
#    nTokens = len(simpleTreeTokenNodes)
#    
#    for i in range(max(0, tokenIdx-window), min(nTokens, tokenIdx+window+1)):
#      if i == tokenIdx:
#        continue
#      prefix = 'tcontext_'+str(i-tokenIdx)+'_'
#      
#      cToken = simpleTreeTokenNodes[i].headToken()
##       if cToken == None:
##         print simpleTreeTokenNodes[i].text
##         print simpleTreeTokenNodes[i].type
##         print i
##         print len(simpleTreeTokenNodes[i].npTokens)
##         print simpleTreeTokenNodes[i].npTokens[-2].token.text
##         for token in simpleTreeTokenNodes[i].npTokens:
##           print token.token.text, ',',
##         print
#
#        
#      features = features.union(self.lexicalFeatures(cToken, prefix))
#    return features
#  
#  def addPrepPhraseFeatures(self, sentence):
#    """ add features to each token based on characteristics of the prepositional phrase
#        that they are in """
#    for token in sentence:
#      if token.text == 'of':
#        prevToken = token.previousToken()
#        if prevToken != None and prevToken.text == 'incidence' \
#           and token.parseTreeNode.parent != None:
##          parent = token.parseTreeNode.parent
#          nextToken = token.nextToken()
#          if nextToken != None and nextToken.parseTreeNode != None:
#            parent = nextToken.parseTreeNode.parent
#            ppTokens = parent.tokenNodes()
#            for tokenNode in ppTokens[1:]:
#              tokenNode.token.features['syntactic'].add('INCIDENCE_OF_PP')
#              
#  def addVerbFeatures(self, sentence):
#    """ add features to each token in the sentence based on their relationship
#       to certain verbs. """
#       
#    for token in sentence:  
#      if token.text == 'occurred':
#        for dep in token.dependents:
#          if dep.type == 'nsubj':
##          if dep.type in set(['nsubj', 'prep']):
#            parent = dep.token.parseTreeNode.parent
#            if dep.type == 'prep':
#              while parent.type != 'PP' and parent.parent != None:
#                parent = parent.parent
#              featureText = 'OCCURRED_IN'
#            else:
#              if parent.parent != None and parent.parent.type == 'NP':
#                parent = parent.parent
#              featureText = 'NSUBJ_OCCURRED'
#            
#            npNodes = parent.tokenNodes()
#            if len(npNodes) > 0 and (dep.type == 'nsubj' \
#              or (dep.type == 'prep' and npNodes[0].token.text == 'in')):      
#              for node in npNodes:
#                node.token.features['verb'] = set([featureText])
#            
#
