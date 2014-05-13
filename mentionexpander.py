#!/usr/bin/python
# Compute features for labeling noun phrases as group, outcome, other
# author: Rodney Summerscales

import sys
import os.path
import nltk
from nltk.corpus import stopwords
from basementionfinder import BaseMentionFinder

######################################################################
# Expand detected mentions
######################################################################

class MentionExpander(BaseMentionFinder):
  """ Used for training/testing a classifier to find mentions 
      in a list of abstracts.
      """
  classpath = 'lib/mallet/mallet-deps.jar:lib/mallet/mallet.jar'
  simpleTagger = ''   # command for mallet simple tagger
  labelSet = None
  
  def __init__(self, entityTypes,  labelList=[]):
    """ Create a new mention finder to find a given list of mention types.
        entityTypes = list of mention types to find (e.g. group, outcome)

    """
    BaseMentionFinder.__init__(self, entityTypes)
    self.simpleTagger = 'java -cp ' + self.classpath  \
                         + ' cc.mallet.fst.SimpleTagger'
    self.labelSet = set(labelList)
    
  
  def train(self, absList, modelFilename):
    """ Train a mention finder model given a list of abstracts """
    featureFilename = 'features.expander.'+self.entityTypesString+'.train.txt'
    self.writeFeatureFile(absList, featureFilename, True)
    options = '--train true --fully-connected false --feature-induction false' \
          + ' --orders 1 --iterations 100 --gaussian-variance 1'
    outputOptions = ''
    cmd = self.simpleTagger + ' ' + options +' --model-file ' + modelFilename   \
            + ' ' + featureFilename + ' ' + outputOptions + ' 2>/dev/null'
  
    os.system(cmd)
    
  def test(self, absList, modelFilename):
    """ Apply the mention finder to a given list of abstracts
        using the given model file.
    """  
    labeledFilename = 'tokens.labeled.txt' 
    featureFilename = 'features.expander.'+self.entityTypesString+'.test.txt'
    self.writeFeatureFile(absList, featureFilename, False)
    options = ''
    outputOptions = '> ' + labeledFilename
  
    cmd = self.simpleTagger + ' ' + options +' --model-file ' + modelFilename   \
            + ' ' + featureFilename + ' ' + outputOptions + ' 2>/dev/null'
  
    os.system(cmd)
  
    # store assigned labels in abstract list
    # read labeled phrase file
    labels = open(labeledFilename, 'r').readlines()
    i = 0
    for abs in absList:
      for sentence in abs.sentences:
        for token in self.tokensToClassify(sentence):
          label = labels[i].strip()
          while len(label) == 0 and i < len(labels):
            i += 1
            label = labels[i].strip()
          if i == len(labels):
            print "Error: not all tokens are labeled"
            raise
          if label != 'other':
            token.addLabel(label)
          i += 1

    # post processing, clean up classification results
    if 'group' in self.entityTypes:
      self.applyGroupRules(absList)
    self.findRepeats(absList)
#    self.cleanupMentions(absList)
      
     
  def writeFeatureFile(self, absList, filename, includeLabels):
    """ write features for each token to a file that can be read by 
        the Mallet simple tagger """
    featureFile = open(filename,'w')
    for abs in absList:
      s = 0
      for sentence in abs.sentences:
        for token in self.tokensToClassify(sentence):
          # write features for the token
          for featureSet in token.features.values():
            for feature in featureSet:
              try:
                featureFile.write(feature+' ')
              except UnicodeEncodeError: 
                print 'UnicodeEncodeError:',
                print 'abs=',abs.id, 'sentence=', s, 'token=',token.index
                print 'feature=', feature
                featureFile.write(feature.encode('ascii', 'xmlcharrefreplace'))
          # write the label for the token
          if includeLabels == True:
            # see if the token has one of the labels the finder will look for
            label='other'
            for mType in self.entityTypes:
              if token.hasAnnotation(mType):
                label = mType
                break
            featureFile.write(label+'\n')
          else:
            featureFile.write('\n')
        featureFile.write('\n')
        s += 1
    featureFile.close()
    
  def tokensToClassify(self, sentence):
    """ return list of tokens that are to be classified. In this case, 
        all tokens that are NOT labeled. """
    list = []
    for token in sentence:
      for label in self.entityTypes:
        if token.hasLabel(label) == False:
          list.append(token)
          break
    return list
    
  def computeFeatures(self, absList, mode):
    """ compute features for each token in each abstract in a given
        list of abstracts.
        
        mode = 'train', 'test', or 'crossval'
    """
    phraseList = []
    parenDepth = 0
  #  commonGroupWords = set(['intervention', 'control', 'controls', 'group', \
  #                           'placebo'])
  
    for abs in absList:
      for sentence in abs.sentences:
        sentenceFeatures = set(['nlm_'+sentence.nlmCategory])
        
        for token in self.tokensToClassify(sentence):
          # compute features for this token
          token.features = {}
                      
          # keyword features
          keywordFeatures = set([])                  

          # compute features
          token.features['lexical'] = self.lexicalFeatures(token)
          token.features['semantic'] = self.semanticFeatures(token, mode)
          token.features['syntactic'] = self.syntacticContextFeatures(token, mode)
          token.features['phrase'] = self.phraseFeatures(token)
          token.features['tContext'] = self.tokenContextFeatures(token, 4, mode)
          token.features['sentence'] = sentenceFeatures
#          token.features['keyword'] = keywordFeatures

          if token.text == '(':
            parenDepth = parenDepth + 1
          elif token.text == ')':
            parenDepth = parenDepth - 1
          elif parenDepth > 0:
            token.features['syntactic'].add('inside_parens')
    
  def lexicalFeatures(self, token, prefix=''):
    """ compute and return features based only on token itself """
    features = set([])
  
    if token.isNumber():
      if token.isInteger():
        features.add(prefix+'integer')
      else:
        features.add(prefix+'float_value')
    else:
#      features.add('t_' + token.getFeatureText())
      features.add(prefix+'lemma_' + token.lemma)
      features.add(prefix+'pos_' + token.pos)
      
    return features
  
  def semanticFeatures(self, token, mode, prefix=''):
    """ features based on labels assigned by metamap and a token's presence
        in a list of words defining semantic classes
        """
    features = set([])
    for umlsChunk in token.umlsChunks:
      # token is in a umls chunk
#      features.add(prefix + 'in_umls')
#      features.add(prefix + 'umls_id_' + umlsChunk.id)
      for type in umlsChunk.types:
        features.add(prefix + 'umls_' + type)

    features = features.union(self.labelFeatures(token, mode, prefix))
    
    return features

  def labelFeatures(self, token, mode, prefix=''):
    """ return features based whether a token has any of the labels specified
        in the constructor """
    features = set([])
    for label in self.labelSet: 
      if token.hasLabel(label, mode):
        features.add(prefix + 'label_' + label)   
    return features
      
  def syntacticContextFeatures(self, token, mode):
    """ features based on collapsed typed dependency parse of sentence """
    features = set([])
    for label in self.entityTypes:
  #     for dep in token.dependents:
  #       features.add(prefix+'dep_type_'+dep.type)
  #       depToken = token.sentence[dep.index]
  # #      features.add(prefix+'dep_token_'+depToken.lemma)
  #       features = features.union(self.semanticFeatures(depToken, mode, 'dep_'))
        
      for gov in token.governors:
        govToken = token.sentence[gov.index]
        if govToken.hasLabel(label, mode):        
#          features.add(prefix+'gov_type_'+gov.type)
#          features.add(prefix+'gov_token_'+govToken.lemma)
          prefix = 'gov_' + gov.type + '_'
          features = features.union(self.semanticFeatures(govToken, mode, prefix))
    return features
    
  def phraseFeatures(self, token):
    """ compute features based on phrase that token is in """
    features = set([])
    phrase = token.parseTreeNode.parent
    prefix ='phrase_'
    features.add(prefix+'type_'+phrase.type)
  
    return features

          
  def tokenContextFeatures(self, token, window, mode):
    """ compute features for tokens surrounding a given token """
    features = set([])
    
    # is token between two tokens with the same label?
    nextToken = token.nextToken()
    prevToken = token.previousToken()
    if nextToken != None and prevToken != None:
      for label in self.entityTypes:
        if nextToken.hasLabel(label, mode) and prevToken.hasLabel(label, mode):
          features.add('between_'+label+'_tokens')
    
    nTokens = len(token.sentence)
    for i in range(max(0, token.index-window), min(nTokens, token.index+window+1)):
      if i == token.index:
        continue
      prefix = 'tcontext_'+str(i-token.index)+'_'
      cToken = token.sentence[i]
      for label in self.entityTypes:
        if cToken.hasLabel(label, mode):
          cTokenFeaures = self.lexicalFeatures(cToken, prefix)
          features = features.union(cTokenFeaures)
          features.add(prefix+label)
          # is token in same phrase as the one to be classified?
          if cToken.parseTreeNode.parent == token.parseTreeNode.parent:
            features.add(prefix+'in_phrase')

    return features