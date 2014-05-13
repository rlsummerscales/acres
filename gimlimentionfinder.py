#!/usr/bin/python
# Use GIMLI for mention finding
# author: Rodney Summerscales

import sys
import os.path
from bannermentionfinder import BannerMentionFinder

class GimliMentionFinder(BannerMentionFinder):
  """ A mention finder that uses the GIMLI NER system
      to identify mentions.
      """
  classpath = None
  gimliPath = None
  gimli = None
  parseDirection = None
  
  def __init__(self, entityTypes, parseDirection='bw'):
    """ Create a new mention finder to find a given list of mention types """
    BannerMentionFinder.__init__(self, entityTypes)
    self.finderType = 'gimli'
#    self.gimliPath = '../tools/gimli-1.0.1/' 
    self.propertiesFilename = 'models/gimli/bc.config'
    self.gimli = 'bin/gimli.sh'
    self.parseDirection = parseDirection
#    self.classpath = self.gimliPath + 'lib/gimli-1.0.1-jar-with-dependencies.jar:$CLASSPATH'
    
  def computeFeatures(self, absList, mode='train'):
    """ compute classifier features for each token in each abstract in a
        given list of abstracts. """
    pass       # function does nothing. banner computes its own features

  def train(self, absList, modelFilename):
    """ Train a BANNER model given a list of abstracts
        (Ignores the model filename parameter.) """
    for mType in self.entityTypes:
      print mType
      # train phrase labeler
      sentenceFilename = mType+'.sentence.train.txt'
      mentionFilename = mType+'.mentions.train.txt'
      gdepFilename = mType+'.train.gdep.gz'
      outputFilename = mType + '.train.gz'
#      os.system('CLASSPATH='+self.classpath)
      convertCmd = '%s convert BC2 -a %s -c %s -g %s -o %s' \
          % (self.gimli, mentionFilename, sentenceFilename, gdepFilename, outputFilename)
  
      self.writeBannerFiles(absList, sentenceFilename, mentionFilename, mType)
      print convertCmd
      os.system(convertCmd)
  
      trainCmd = '%s model -p %s -t train -e protein -c %s -m %s -f %s' \
          % (self.gimli, self.parseDirection, outputFilename, modelFilename, self.propertiesFilename)
      print trainCmd
      os.system(trainCmd)
 

    
  def test(self, absList, modelFilename):
    """ Apply the mention finder to a given list of abstracts
        using the given model file.
        (Ignores the model filename parameter.)
        return mention finder statistics (MentionStats) object."""
    for mType in self.entityTypes:
      print mType
      sentenceFilename = mType+'.sentence.test.txt'
      mentionFilename = mType+'.mentions.test.txt'
      resultFilename = mType+'.gimli.out.txt'
      gdepFilename = mType+'.test.gdep.gz'
      outputFilename = mType + '.test.gz'       
#      os.system('CLASSPATH='+self.classpath)
    
      convertCmd = '%s convert BC2 -a %s -c %s -g %s -o %s' \
          % (self.gimli, mentionFilename, sentenceFilename, gdepFilename, outputFilename)
  
      self.writeBannerFiles(absList, sentenceFilename, mentionFilename, mType)
      print convertCmd
      os.system(convertCmd)
      
      testCmd = '%s annotate BC2 -c %s -m %s,%s,%s -o %s' \
          % (self.gimli, outputFilename, modelFilename, self.parseDirection, self.propertiesFilename, \
              resultFilename)
      print testCmd
      os.system(testCmd)

      self.assignLabels(resultFilename, absList, mType)

  def assignLabels(self, resultFilename, absList, mType):
      # store assigned labels in abstract list
      # read labeled phrase file
      lines = open(resultFilename, 'r').readlines()
      specialTokens = set(['.', ')', ','])
     
      absHash = {}
      for abstract in absList:
        absHash[abstract.id] = abstract
#      print absHash
      
      for line in lines:
        [id, mentionBounds, mention] = line.split('|')
        sid = int(id[8:])
        id = id[:8]
        [firstCharIdx, lastCharIdx] = mentionBounds.split(' ')
        firstCharIdx = int(firstCharIdx)
        lastCharIdx = int(lastCharIdx)
        sList = absHash[id].allSentences()
        sentence = sList[sid]
        charIndex = 0
#        print id, sid, mentionBounds
        for token in sentence:
#          print '%d_%s_%d '%(charIndex,token.text,charIndex+len(token.text)-1),
          if charIndex >= firstCharIdx and charIndex <= lastCharIdx:
            token.addLabel(mType)
#            print charIndex, token.text, mentionBounds
          charIndex += len(token.text)
#        print      



  

