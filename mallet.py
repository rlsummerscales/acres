#!/usr/bin/python
# Compute features for labeling noun phrases as group, outcome, other
# author: Rodney Summerscales

#import sys
#import Queue
import os
from basetokenclassifier import BaseTokenClassifier
from basetokenclassifier import TokenLabel

######################################################################
# Experimental mention finder
######################################################################

class MalletTokenClassifier(BaseTokenClassifier):
  """ Used for training/testing a classifier to label mention tokens 
      in a list of abstracts.
      """
  classpath = 'lib/mallet/mallet-deps.jar:lib/mallet/mallet.jar'
  simpleTagger = ''   # command for mallet simple tagger
  crfOrder = 1
  nIterations = 100
      
  def __init__(self, order=1, fullyConnected=False, nIterations=100, topK=1):
    """ Create a new mention finder to find a given list of mention types.
        entityTypes = list of mention types to find (e.g. group, outcome)
    """
    BaseTokenClassifier.__init__(self, 'mallet', topK)
    self.simpleTagger = 'java -Xmx2g -cp ' + self.classpath  \
                         + ' cc.mallet.fst.SimpleTagger'
    self.crfOrder = order
    if fullyConnected:
      self.connectedOption = 'true'
    else:
      self.connectedOption = 'false'
    self.nIterations = nIterations
      
  def train(self, absList, modelFilename, entityTypes, tokenFilter=None):
    """ Train a mention finder model given a list of abstracts """
    featureFilename = 'features.'+self.entityTypesString(entityTypes)+'.train.txt'
            
    self.writeFeatureFile(absList, featureFilename, entityTypes, True, tokenFilter)
    
    options = '--train true --default-label other --fully-connected '+ self.connectedOption \
          +' --feature-induction false' \
          + ' --orders ' + str(self.crfOrder) \
          + ' --iterations ' + str(self.nIterations) \
          + ' --gaussian-variance 1'  
#          + ' --threads 4'

    outputOptions = ''
    cmd = self.simpleTagger + ' ' + options +' --model-file ' + modelFilename   \
            + ' ' + featureFilename + ' ' + outputOptions + ' 2>/dev/null'
    print cmd
    os.system(cmd)
    


  def test(self, absList, modelFilename, labeledFilename, entityTypes, tokenFilter=None):
    """ Apply the mention finder to a given list of abstracts
        using the given model file.
    """  
    featureFilename = 'features.'+self.entityTypesString(entityTypes)+'.test.txt'

    self.writeFeatureFile(absList, featureFilename, entityTypes, False, tokenFilter)
#    options = ''
    options = ' --default-label other --n-best ' + str(self.topK)
    outputOptions = '> ' + labeledFilename
  
#    cmd = '%s %s --model-file %s %s %s 2>/dev/null' \
#       % (self.simpleTagger, options, modelFilename, featureFilename, outputOptions)
    cmd = '%s %s --model-file %s %s %s' \
       % (self.simpleTagger, options, modelFilename, featureFilename, outputOptions)
    
    print cmd
    os.system(cmd)
  
    
  def readLabelFile(self, labelFilename, entityTypes):
    """ read a mallet label file and return the list of labels """
    labelLines = open(labelFilename, 'r').readlines()
    labels = []
    lineNo = 1
    sequenceProb = []
    for i in range(self.topK):
      sequenceProb.append(0.0)
    
    currentTopK = self.topK  
    for line in labelLines:
      try:
        topKLabels = line.strip().split()
        if len(topKLabels) > 0:
          if topKLabels[0] == 'k' :
            newTopK = int(topKLabels[1])
            if newTopK != currentTopK:
              currentTopK = newTopK
              sequenceProb = []
              for i in range(currentTopK):
                sequenceProb.append(0.0)
            # this is the list of sequence probabilities
            for i in range(currentTopK):
              sequenceProb[i] = float(topKLabels[i+2])
#            print lineNo, topKLabels[1], currentTopK, sequenceProb
          elif len(topKLabels) == 2*currentTopK:
            tokenLabelList = []
            for i in range(0,currentTopK*2,2):
              label = topKLabels[i]
              prob = float(topKLabels[i+1])
              tLabel = TokenLabel(label)
              tLabel.prob = prob
              tLabel.sequenceProb = sequenceProb[i/2]
              tokenLabelList.append(tLabel)
#              print 'Read:', tLabel.label, tLabel.sequenceProb, tLabel.prob  
    
            labels.append(tokenLabelList)  
#        if len(topKLabels) == self.topK:
#    #        for i in range(len(topKLabels)):
#    #          if topKLabels[i] == 'O':
#    #            topKLabels[i] = 'other'
#          if self.topK == 1:
#            labels.append(topKLabels[0])
#          else:
#            labels.append(topKLabels) 
      except:
        print '%s: Error at line number %d' % (labelFilename, lineNo)  
      lineNo += 1     
    return labels
        
  def writeFeatureFile(self, absList, filename, entityTypes, includeLabels, tokenFilter=None):
    """ write features for each token to a file that can be read by 
        the Mallet simple tagger """
    featureFile = open(filename,'w')
    featureSetHash = {}
    for abs in absList:
      s = 0
      for sentence in abs.sentences:
#        currentChunkLength = 0
        for token in sentence.tokens:
          # write features for the token
          if tokenFilter == None or tokenFilter(token) == True: 
            hasFeatures = False
            for featureType,featureSet in token.features.items():
              if featureType not in featureSetHash:
                featureSetHash[featureType] = set([])
              for feature in featureSet:
                featureSetHash[featureType].add(feature)
                hasFeatures = True
                try:
                  featureFile.write(feature+' ')
                except UnicodeEncodeError: 
                  print 'UnicodeEncodeError:',
                  print 'abs=',abs.id, 'sentence=', s, 'token=',token.index
                  print 'feature=', feature
                  featureFile.write(feature.encode('ascii', 'xmlcharrefreplace'))
            if hasFeatures == False:
              featureFile.write('NO_FEATURES ')

            # write the label for the token
            if includeLabels == True:
              # see if the token has one of the labels the finder will look for
              label='other'
              for mType in entityTypes:
                if token.hasAnnotation(mType):
                  label = mType
                  break
              featureFile.write(label+'\n')
            else:
              featureFile.write('\n')
#          currentChunkLength += 1    
#          if token.text == ',' and currentChunkLength > 4 and (len(sentence.tokens) - 1 - token.index) > 4:
#            featureFile.write('\n')
#            currentChunkLength = 0
        featureFile.write('\n')
        s += 1
    featureFile.close()
    
    print '----------------------------'
    print 'Feature counts for ', filename
    for featureType, featureSet in featureSetHash.items():
      print featureType, len(featureSet)
      featureSetHash[featureType].clear()
    featureSetHash.clear()
    print '----------------------------'
           


