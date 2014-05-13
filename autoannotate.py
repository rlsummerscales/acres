#!/usr/bin/python
# author: Rodney Summerscales

import sys
#import nltk
#from nltk.corpus import wordnet as wn

from abstractlist import AbstractList
from summary import SummaryList
from statlist import StatList
from findertask import FinderTask
from rulebasedfinder import RuleBasedFinder

class AutoAnnotate(RuleBasedFinder):
  """ Use trial registries to annotate abstracts.
      """
#  entityTypes = ['condition', 'group', 'outcome']
  entityTypes = ['group', 'outcome']
  
  def __init__(self):
    """ Create a finder that labels tokens with a given type if they have this annotation.
    """
    RuleBasedFinder.__init__(self, self.entityTypes)
              
  def test(self, absList, modelFilename):
    """ Apply the mention finder to a given list of abstracts
        using the given model file.
    """  
    for abstract in absList:
      # find and tag untagged instances in abstract that match registry entries
      if abstract.report != None:
        registryEntries = {}
          
        registryEntries['group'] = []
        registryEntries['outcome'] = []
#        registryEntries['condition'] = []
        print abstract.id, '------------------------------------------'
        print abstract.report.id
        for intervention in abstract.report.interventions:
          if len(intervention.name) == 1:
            print 'R - Group:', intervention.name[0].toString()
            if len(intervention.name[0]) < 5:
              registryEntries['group'].append(intervention.name[0])
            else:
              print '(Discarded)'
        print '---'
        for sentence in abstract.sentences:
          mList = sentence.getAnnotatedMentions('group', recomputeMentions=True)
          for mention in mList:
            print 'A - Group:', mention.text
        print '==='             
        for outcome in abstract.report.outcomes:
          if len(outcome.name) == 1:
            print 'R - outcome:', outcome.name[0].toString()
            if len(outcome.name[0]) < 7:
              registryEntries['outcome'].append(outcome.name[0])
            else:
              print '(Discarded)'
        print '---'
        for sentence in abstract.sentences:
          mList = sentence.getAnnotatedMentions('outcome', recomputeMentions=True)
          for mention in mList:
            print 'A - outcome:', mention.text

#         for eCriteria in abstract.report.exclusionCriteria:
#           if len(eCriteria.sentences) == 1:
#             print 'condition:', eCriteria.sentences[0].toString()
#             registryEntries['condition'].append(eCriteria.sentences[0])
# 
#         for iCriteria in abstract.report.inclusionCriteria:
#           if len(iCriteria.sentences) == 1:
#             print 'condition:', iCriteria.sentences[0].toString()
#             registryEntries['condition'].append(iCriteria.sentences[0])

        
        if len(registryEntries['group']) == 0 or len(registryEntries['outcome']) == 0:
          # registry not useful, candidate abstract not useful for training
          abstract.report = None
        else:
#          self.GroupFilter(abstract)
          for mType, sentenceList in registryEntries.items():
#            nMatches = self.findRepeats(abstract, mType, sentenceList)
#            nMatches = self.labelUMLSMatches(abstract, mType, sentenceList)
            nMatches2 = self.labelMatches(abstract, mType, sentenceList)
#            nMatches2 = self.labelMatches2(abstract, mType, sentenceList)
#            self.expandMentions(abstract, mType)
#           nGroups = self.countMentions(abstract, 'group')
#           nOutcomes = self.countMentions(abstract, 'outcome')
#           print 'nGroups =',nGroups, 'nOutcomes =',nOutcomes
#           if nGroups < 1 or nOutcomes < 1:
#             # ignore abstracts that do not have any annotated groups or outcomes
#             abstract.report = None
            
    for abstract in absList[:]:
      if abstract.report == None:
        absList.remove(abstract)
        
  def countMentions(self, abstract, mType):
    """ count the number of mentions annotated by system """
    nMentions = 0
    for sentence in abstract.sentences:         
      mList = sentence.getDetectedMentions(mType, recomputeMentions=True)
      nMentions += len(mList)
    return nMentions

  def expandMentions(self, abstract, mType):
    """ expand the mentions to include all tokens in current phrase """
    for sentence in abstract.sentences:
      for simpleTreeTokenNode in sentence.getSimpleTree().tokenNodes():
        if simpleTreeTokenNode.isNounPhraseNode():
          npTokens = simpleTreeTokenNode.tokenList()
          labelAllTokens = False
          for token in npTokens:
            if token.hasLabel(mType):
              labelAllTokens = True
              break
          if labelAllTokens:
            for token in npTokens:
              token.addLabel(mType)
            
  def labelUMLSMatches(self, abstract, mType, registryEntries):
    """ find all word sequences in abstract that match words in a give set 
        of registry entries. 
        Label all identified words sequences """
    if len(registryEntries) == 0:
      return 0
    nMatches = 0
    ignoreWords = set(['a', 'the', 'of', 'in', 'for', 'group', 'groups', 'arm'])
  #  print 'Looking for missed', mType, 'mentions'
    conceptList = []
    conceptIDs = set([]) 
    # build list of detected mentions in abstract
    for sentence in registryEntries:
      # get all detected mentions in sentence
      for chunk in sentence.umlsChunks:
        bestConcepts = chunk.getBestConcepts()
        conceptList += bestConcepts
        for concept in bestConcepts:
          conceptIDs.add(concept.id)

         
    for sentence in abstract.sentences:      
      for chunk in sentence.umlsChunks:
        bestConcepts = chunk.getBestConcepts()
        for concept in bestConcepts:
          if concept.id in conceptIDs:
            nMatches += 1
            for token in chunk.getTokens():
              token.addLabel(mType)
            break
    return nMatches
        
  def labelMatches(self, abstract, mType, registryEntries):
    """ find all word sequences in abstract that match words in a give set 
        of registry entries. 
        Label all identified words sequences """
    if len(registryEntries) == 0:
      return
    nMatches = 0
    ignoreWords = set(['a', 'the', 'of', 'in', 'for', 'group', 'groups', 'arm'])
  #  print 'Looking for missed', mType, 'mentions'
    mentionList = [] 
    tokenSet = set([])

    # build list of detected mentions in abstract
    for sentence in registryEntries:
      # get all detected mentions in sentence
      tokenSet = set([])
      for token in sentence:
        if token.isSymbol() == False and token.isStopWord() == False \
          and token.isNumber() == False:
          tokenSet.add(token.text)
          tokenSet.add(token.lemma)
#      mentionList.append(tokenSet)
    print tokenSet
    for sentence in abstract.sentences:
      for simpleTreeTokenNode in sentence.getSimpleTree().tokenNodes():
        if simpleTreeTokenNode.isNounPhraseNode():
          npTokens = simpleTreeTokenNode.tokenList()
          labelAllTokens = False
          for token in npTokens:
            if token.text in tokenSet:
              labelAllTokens = True
              break
          if labelAllTokens:
            for token in npTokens:
              token.addLabel(mType)
         
#     for sentence in abstract.sentences:      
#       i = 0
# #      print sentence.toString()
#       # check each token to see if it matches a detected mention
#       while i < len(sentence):          
#         maxTokensMatched = 0
#         bestMatch = None
#         for mention in mentionList:
#           j = 0
#           nImportantWords = 0
#           keepMatching = True
#           while keepMatching and i+j < len(sentence):
#             token = sentence[i+j]
#             if token.text in mention or token.lemma in mention:
#               keepMatching = True
#             elif token.isAcronym():
#               # token is an acronym check if all tokens in expansion in mention
#               expansionTokens = token.getAcronymExpansion()
#               if len(expansionTokens) == 0:
#                 keepMatching = False
#               for eToken in expansionTokens:
#                 if eToken.text not in mention:
#                   keepMatching = False
#             else:
#               keepMatching = False
#             if keepMatching:
#               j += 1
#               if token.isStopWord() == False and token.isSymbol() == False \
#                 and token.isNumber() == False:
#                 nImportantWords += 1
#               
#           if  j > maxTokensMatched and nImportantWords > 0:
#             maxTokensMatched = j                
#             bestMatch = mention
#             
#         if maxTokensMatched == 0:
#           # no match, move to next token
#           i = i + 1
#         else:
#           nMatches += 1
#           for j in range(i, i+maxTokensMatched):
#             token = sentence[j]
# #               print abs.id, ': Tagging', token.text, 'as', mType
#             token.addLabel(mType)
#           i = i + maxTokensMatched
    return nMatches        
        
  def labelMatches2(self, abstract, mType, registryEntries):
    """ find all word sequences in abstract that match words in a give set 
        of registry entries. 
        Label all identified words sequences """
    if len(registryEntries) == 0:
      return
    nMatches = 0
    ignoreWords = set(['a', 'the', 'of', 'in', 'for', 'group', 'groups', 'arm'])
  #  print 'Looking for missed', mType, 'mentions'
    mentionList = [] 
    # build list of detected mentions in abstract
    for sentence in registryEntries:
      # get all detected mentions in sentence
      tokenSet = set([])
      for token in sentence:
        if token.isSymbol() == False:
          tokenSet.add(token.text)
          tokenSet.add(token.lemma)
      mentionList.append(tokenSet)

         
    for sentence in abstract.sentences:      
      i = 0
#      print sentence.toString()
      # check each token to see if it matches a detected mention
      while i < len(sentence):          
        maxTokensMatched = 0
        bestMatch = None
        for mention in mentionList:
          j = 0
          nImportantWords = 0
          keepMatching = True
          while keepMatching and i+j < len(sentence):
            token = sentence[i+j]
            if token.text in mention or token.lemma in mention:
              keepMatching = True
            elif token.isAcronym():
              # token is an acronym check if all tokens in expansion in mention
              expansionTokens = token.getAcronymExpansion()
              if len(expansionTokens) == 0:
                keepMatching = False
              for eToken in expansionTokens:
                if eToken.text not in mention:
                  keepMatching = False
            else:
              keepMatching = False
            if keepMatching:
              j += 1
              if token.isStopWord() == False and token.isSymbol() == False \
                and token.isNumber() == False:
                nImportantWords += 1
              
          if  j > maxTokensMatched and nImportantWords > 0:
            maxTokensMatched = j                
            bestMatch = mention
            
        if maxTokensMatched == 0:
          # no match, move to next token
          i = i + 1
        else:
          nMatches += 1
          for j in range(i, i+maxTokensMatched):
            token = sentence[j]
#               print abs.id, ': Tagging', token.text, 'as', mType
            token.addLabel(mType)
          i = i + maxTokensMatched
    return nMatches
                 
  def GroupFilter(self, abstract):
    """ apply simple rules to list of abstracts to recognize groups """
    commonGroupWords = set(['intervention', 'control', 'controls', 'group', \
                             'placebo'])
    label = 'group'
    groupWords = set(['group', 'arm'])
    for sentence in abstract.sentences:
      for simpleTreeTokenNode in sentence.getSimpleTree().tokenNodes():
        if simpleTreeTokenNode.isNounPhraseNode() \
           and simpleTreeTokenNode.headToken().text in groupWords:
          nImportantWords = 0
          phraseTokens = simpleTreeTokenNode.tokenList() 
          for token in phraseTokens:
            if token.isStopWord() == False and token.isSymbol() == False \
              and token.isNumber() == False and token.text != 'group':
              nImportantWords += 1
              break
          if nImportantWords > 0:
            for token in phraseTokens:
              token.addLabel(label)
          
  def findRepeats(self, abstract, mType, registryEntries):
    """ find untagged token sequences that match those from detected mentions
        and tag them """
    ignoreWords = set(['a', 'the', 'of', 'in', 'for', 'group', 'groups', 'arm'])
  #  print 'Looking for missed', mType, 'mentions'
    mentions = [] 
    # get all detected mentions in sentence
    for sentence in registryEntries:
      longTokenSet = set([])
      shortTokenSet = set([])
      for token in sentence.tokens:
        longTokenSet.add(token.text)
        if token.text not in ignoreWords and token.isSymbol() == False:
          shortTokenSet.add(token.text)
      mentions.append(longTokenSet)
      mentions.append(shortTokenSet)
  
    # find and tag untagged instances in abstract that match detected mentions
    nMatches = 0
    for sentence in abstract.sentences:
      if len(mentions) > 0:
        i = 0
        
        # check each token to see if it matches a detected mention
        while i < len(sentence):
          nMatchedTokens = 0
          curMentionList = mentions
          longestMatch = None
          # match current token (and those following it) to detected mentions
          while len(curMentionList) > 0 \
              and (i+nMatchedTokens) < len(sentence):
            nextMentionList = []
            # look for detected mentions that have this token
            for mTokenSet in curMentionList:
              if sentence[i+nMatchedTokens].text in mTokenSet:
                # current token matches a token in the mention
                if (nMatchedTokens+1) == len(mTokenSet):
                  # we have matched this entire mention
                  # it is currently the longest mention that we have
                  # matched all of the tokens from 
                  longestMatch = mTokenSet
                else:
                  # there are still more tokens in this mention that
                  # we need to match
                  nextMentionList.append(mTokenSet)
            # move to set of mentions that have the most matches so far 
            curMentionList = nextMentionList
            if len(curMentionList) > 0:
              nMatchedTokens = nMatchedTokens + 1
                
            
          if longestMatch == None:
            # no match, move to next token
            i = i + 1
          else:
            nMatches += 1
            nMatchedTokens = len(longestMatch)
            for j in range(i, i+nMatchedTokens):
              token = sentence[j]
  #               print abs.id, ': Tagging', token.text, 'as', mType
              token.addLabel(mType)
            i = i + nMatchedTokens  
    return nMatches

#############################################################################

if len(sys.argv) < 2:
  print "Usage: autoannotate.py <INPUT_PATH>"
  print "Automatically annotate a collection of abstracts with trial registries"
  print "in the directory specified by <INPUT_PATH>"
  print "using rules and trial registry info."
  sys.exit()

statList = StatList()
inputPath = sys.argv[1]
absList = AbstractList(inputPath)

finder = AutoAnnotate()
finderTask = FinderTask(finder)
finderTask.test(absList, statList)

# absList.labelsToAnnotations(['group', 'outcome'])
# 
# for abs in absList:
#   if abs.report != None:
#     abs.writeXML(abs.id+'.auto.xml')
#     
# statList.write('stats.auto.txt', separator=',')
