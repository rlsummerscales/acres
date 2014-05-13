#!/usr/bin/python
# Post processing filters to clean up detected mention, numbers, clusters, etc
# author: Rodney Summerscales

import templates

def AgeFilter(abstract):
  """ Perform clean-up of all age mentions in a given abstract """
  for sentence in abstract.sentences:
    ageList = sentence.getDetectedMentions('age', recomputeMentions=True)
    for ageMention in ageList:
      ageTemplate = templates.Age(ageMention)
      if len(ageTemplate.values) == 0:
        # there are no valid age values in the age phrase, discard entire phrase
        ageMention.tokens.removeLabel('age')
  sentence.getDetectedMentions('age', recomputeMentions=True)
          
def GroupFilter(abstract):
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


    # ensure that the common conjunction 'plus' is labeled if the tokens on either side are labeled      
    for token in sentence.tokens[1:-1]:
      if token.text == 'plus' and token.previousToken().hasLabel(label) and token.nextToken().hasLabel(label):
        token.addLabel(label)
    mList = sentence.getDetectedMentions(label, recomputeMentions=True)
    for mention in mList:
      for token in mention.tokens:
        if token.text == 'versus':
          token.removeLabel(label)
  
            
    
  ignoreWords = set(['group', 'groups', 'arm'])
#  findAcronymExpansions(abstract, label)                
  findRepeats(abstract, label)    
  trimMention(abstract, label)
  discardStopWordMentions(abstract, label, ignoreWords)
  addNegationWords(abstract, label)        

def isStopWordMention(mention, ignoreWords=set([])):
  """ return True if this mention only consists of stop words """
  nImportantWords = 0
  for token in mention.tokens:
    if token.isNumber() == False and len(token.text) > 1 \
      and token.isStopWord() == False and token.isSpecialToken() == False \
      and token.isTimeWord() == False and token.isMeasurementWord() == False \
      and token.text not in ignoreWords and token.isValueAcronym() == False \
      and token.isSymbol() == False:
      nImportantWords = 1
      break  # mention contains at least one potentially useful word

  return nImportantWords == 0
    
def discardStopWordMentions(abstract, label, ignoreWords=set([])):
  """ untag mentions that only consist of stop words """
  for sentence in abstract.sentences:
    mList = sentence.getDetectedMentions(label, recomputeMentions=True)
    for mention in mList:
      if isStopWordMention(mention, ignoreWords):
        # the outcome mention includes no useful words, assume it is an error 
        # and delete the mention
        mention.tokens.removeLabel(label)
    sentence.getDetectedMentions(label, recomputeMentions=True) 

def findAcronymExpansions(abstract, label):
  for sentence in abstract.sentences:          
    mList = sentence.getDetectedMentions(label, recomputeMentions=True)
    for mention in mList:
      for token in mention.tokens:
        if token.isAcronym():
          # look for expanded version of acronym
          for sentence in abstract.sentences:
            for tIdx in range(0, len(sentence)):
              i = 0
              while tIdx + i < len(sentence) and i < len(token.text) \
                  and sentence[tIdx+i].text[0].upper() == token.text[i]:
                i += 1
              if i == len(token.text):
                # found acronym match, label each token in matching list of tokens
                for j in range(tIdx, tIdx+i):
                  sentence[j].addLabel(label)
    sentence.getDetectedMentions(label, recomputeMentions=True)       

def OutcomeFilter(abstract):
  """ apply rules to clean-up outcome mentions and discard those that cannot be
      outcomes"""
  # discard an outcome if it does not contain at least one word of more than one char
  # (that does not refer to a special value such as hazard ratio)
  label = 'outcome' 
  ignoreWords = set(['less', 'greater', 'than'])
  discardStopWordMentions(abstract, label, ignoreWords)

#  findAcronymExpansions(abstract, label)            
  findRepeats(abstract, label)    
  trimMention(abstract, label)
  addNegationWords(abstract, label)  
  resolveGroupOutcomeConflicts(abstract)
  labelMissingPrimarySecondaryOutcomes(abstract)
  
def isEndpointToken(token):
  """ return true if this token is a match for 'outcome', 'endpoint' or part of a match for 'end point' """
  if token.lemma == 'endpoint' or token.lemma == 'outcome':
    return True
  elif token.text == 'end':
    nextToken = token.nextToken()
    if nextToken != None and nextToken.lemma == 'point':
      return True

  return False
  
def labelMissingPrimarySecondaryOutcomes(abstract):
  """ look for and label common phrases that refer to primary/secondary outcomes """
  startPhraseSet = set(['primary', 'secondary', 'composite'])
  for sentence in abstract.sentences:
    phraseStartIdx = -1
    phraseStopIdx = -1
    recomputeMentions = False
    for token in sentence:
      if phraseStartIdx < 0 and token.lemma in startPhraseSet:
        # found start of potential outcome phrase
        phraseStartIdx = token.index
      elif phraseStartIdx >= 0 and isEndpointToken(token):
        # found end of outcome phrase
        if token.text == 'end':
          # next token is "point", include it
          phraseStopIdx = token.index + 1
        else:
          phraseStopIdx = token.index
        # label tokens in this phrase
        for i in range(phraseStartIdx, phraseStopIdx+1):
          sentence[i].addLabel('outcome')
          sentence[i].addLabel('primary_outcome')
          recomputeMentions = True
        phraseStartIdx = -1
        phraseStopIdx = -1
      elif phraseStartIdx >= 0 and token.lemma not in startPhraseSet and isEndpointToken(token) == False:
        # not a potential outcome phrase
        phraseStartIdx = -1
        phraseStopIdx = -1
    if recomputeMentions:
      outcomeList = sentence.getDetectedMentions('outcome', recomputeMentions=True)              
              
  
def resolveGroupOutcomeConflicts(abstract):
  """ if a token has multiple conflicts, use the label that assigns the token to the longest mention """
  gLabel = 'group'
  oLabel = 'outcome'
  for sentence in abstract.sentences:
    groupList = sentence.getDetectedMentions(gLabel, recomputeMentions=True)      
    outcomeList = sentence.getDetectedMentions(oLabel, recomputeMentions=True)      
    recomputeGroups = False
    recomputeOutcomes = False
    for gMention in groupList:
      for oMention in outcomeList:
        if gMention.contains(oMention) and gMention.length() > oMention.length():
          oMention.tokens.removeLabel(oLabel)
          recomputeOutcomes = True
        elif oMention.contains(gMention) and oMention.length() > gMention.length():
          gMention.tokens.removeLabel(gLabel)
          recomputeGroups = True
          
    if recomputeGroups:
      groupList = sentence.getDetectedMentions(gLabel, recomputeMentions=True)      
      
    if recomputeOutcomes:
      outcomeList = sentence.getDetectedMentions(oLabel, recomputeMentions=True)      
                
   
def ConditionFilter(abstract):
  """ apply rules to clean-up condition mentions and discard those that cannot be
      outcomes"""
  label = 'condition'
  findRepeats(abstract, label)    
  trimMention(abstract, label)
  addNegationWords(abstract, label)        
        
def PopulationFilter(abstract):
  """ apply rules to clean-up condition mentions and discard those that cannot be
      outcomes"""
  label = 'population'
  findRepeats(abstract, label)    
  trimMention(abstract, label)
   
def NumberFilter(abstract):
  """ Deal with situations where a number has multiple labels of incompatible types.
      e.g. a number labeled both outcome and outcome number. """
  # set of disjoint mention types. A token should not have a label from more than
  # one of these types.  
  mentionTypes = set(['outcome', 'group', 'condition', 'population', 'age'])
  numberTypes = set(['on', 'gs', 'eventrate'])
  for sentence in abstract.sentences:
    for nType in numberTypes:
      for token in sentence:
        if token.hasLabel(nType):
#          if len(token.labels) > 1:
#            # remove any other labels that the token may have
#            token.removeAllLabels(mentionTypes)
          if token.getValue() < 0:
            # ignore negative values for now
            token.removeLabel(nType)
            print '#### Deleting label = %s for value %s' % (nType, token.text)
          elif token.hasLabel('on'):
            nextTokens = token.listOfNextTokens(2)
            # check for missed event rate: match pattern "ON ( PERCENTAGE" 
            if len(nextTokens) > 0 and nextTokens[0].text == '-LRB-' and nextTokens[1].isImportantNumber() \
              and nextTokens[1].hasLabel('eventrate') == False and nextTokens[1].isPercentage():
              nextTokens[1].addLabel('eventrate')
            # match pattern "ON of INT"  
            elif len(nextTokens) > 0 and nextTokens[0].text == 'of' and nextTokens[1].isImportantInteger() \
              and nextTokens[1].hasLabel('gs') == False:
              nextTokens[1].addLabel('gs')
            else:
              # match pattern "ON of INT ( PERCENTAGE"
              nextTokens = token.listOfNextTokens(4)
              if len(nextTokens) > 0 and nextTokens[0].text == 'of' \
                and nextTokens[1].isImportantInteger() \
                and nextTokens[2].text == '-LRB-'\
                and nextTokens[3].isImportantNumber() and nextTokens[3].isPercentage() \
                and nextTokens[3].hasLabel('eventrate') == False:
                nextTokens[1].addLabel('gs')
                nextTokens[3].addLabel('eventrate')
              else:
                # check pattern "PERCENTAGE ( ON"
                prevTokens = token.listOfPreviousTokens(2)
                if len(prevTokens) > 0 and prevTokens[0].isPercentage() and prevTokens[1].text == '-LRB-' \
                  and prevTokens[0].hasLabel('eventrate') == False:
                  prevTokens[0].addLabel('eventrate')
          elif token.hasLabel('eventrate'):
            prevTokens = token.listOfPreviousTokens(2)
            # match pattern "INT of INT ( ER"
            prevTokens = token.listOfPreviousTokens(4)
            if len(prevTokens) > 0 and prevTokens[0].isImportantInteger() \
              and prevTokens[1].text == 'of' \
              and prevTokens[2].isImportantInteger() \
              and prevTokens[3].text == '-LRB-'  \
              and (prevTokens[0].hasLabel('on') == False or prevTokens[2].hasLabel('gs') == False):
              prevTokens[0].addLabel('on')
              prevTokens[2].addLabel('gs')
            # check for missed event rate: match pattern "INT ( ER" 
            elif len(prevTokens) > 0 and prevTokens[0].isImportantInteger() and prevTokens[1].text == '-LRB-' \
              and prevTokens[0].hasLabel('on') == False:
              prevTokens[0].addLabel('on')
            else:
              # check pattern "ER ( INT"
              nextTokens = token.listOfNextTokens(2)
              if len(nextTokens) > 0  and nextTokens[0].text == '-LRB-' and nextTokens[1].isImportantInteger() \
                and nextTokens[1].hasLabel('on') == False:
                nextTokens[1].addLabel('on')
                # check pattern "INT of INT"
                nextTokens = token.listOfNextTokens(2)
                if len(nextTokens) > 0 and nextTokens[0].text == 'of' and nextTokens[1].isImportantInteger() \
                  and nextTokens[1].hasLabel('gs') == False:
                  nextTokens[1].addLabel('gs')
              
          
  
def umlsRepeats(abstract):
  """ find UMLS chunks with the same ID and give them the same label """
  chunkLabels = {}
  for sentence in abstract.sentences:
    for chunk in sentence.umlsChunks:
      if chunk.label != None:
        if chunk.id in chunkLabels:
          chunkLabels[chunk.id] = chunk.label
          
  for sentence in abstract.sentences:
    for chunk in sentence.umlsChunks:
      if chunk.label == None and chunk.id in chunkLabels:
        chunk.label = chunkLabels[chunk.id]
        for token in chunk.getTokens():
          token.addLabel(chunk.label)
 

def findRepeats(abstract, mType):
  """ find untagged token sequences that match those from detected mentions
      and tag them """
  ignoreWords = set(['a', 'the', 'of', 'in', 'for', 'group', 'groups', 'arm'])
#  print 'Looking for missed', mType, 'mentions'
  mentions = [] 
  # build list of detected mentions in abstract
  for sentence in abstract.sentences:
    # get all detected mentions in sentence
    mList = sentence.getDetectedMentions(mType, recomputeMentions=True)
    for mention in mList:
      longTokenSet = set([])
      shortTokenSet = set([])
      for token in mention.tokens:
        longTokenSet.add(token.lemma)
        if token.lemma not in ignoreWords:
          shortTokenSet.add(token.lemma)
      mentions.append(longTokenSet)
      mentions.append(shortTokenSet)

  # find and tag untagged instances in abstract that match detected mentions
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
            if sentence[i+nMatchedTokens].lemma in mTokenSet:
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
          nMatchedTokens = len(longestMatch)
          for j in range(i, i+nMatchedTokens):
            token = sentence[j]
#               print abs.id, ': Tagging', token.text, 'as', mType
            token.addLabel(mType)
          i = i + nMatchedTokens
    sentence.getDetectedMentions(mType, recomputeMentions=True)  
                  
def trimMention(abstract, mType):
  """ remove certain symbols from beginning/end of mention """
  removeSymbols = set([',', '-LRB-', '-RRB-', '-EOS-'])       

  for sentence in abstract.sentences:
    mentionList = sentence.getDetectedMentions(mType, recomputeMentions=True)      
    for mention in mentionList:
      firstToken = mention.tokens[0]
      lastToken = mention.tokens[-1]
      if firstToken.text in removeSymbols:
        firstToken.removeLabel(mType)
      if lastToken.text in removeSymbols:
        lastToken.removeLabel(mType)
    sentence.getDetectedMentions(mType, recomputeMentions=True)
        
def addNegationWords(abstract, mType):
  """ check if the token that precedes the start of a mention of a given type is a
      negation word """
  for sentence in abstract.sentences:
    mentionList = sentence.getDetectedMentions(mType, recomputeMentions=True)      
    for mention in mentionList:
      firstToken = mention.tokens[0]
      prevToken = firstToken.previousToken()
      if prevToken != None:
        if prevToken.isNegationWord():
          # previous token is a negation word, add it to beginning of mention
          prevToken.addLabel(mType)
    sentence.getDetectedMentions(mType, recomputeMentions=True) 
    
    
def filterGroupList(groupTemplateList):
  """ remove group clusters that are likely to be false positives.
      these are group clusters that are not associated with any other entities
      """  
  filteredList = []
  for gTemplate in groupTemplateList:
    if len(groupTemplateList) <= 2 or len(gTemplate.children) > 0 \
      or gTemplate.getSize() > 0 or len(gTemplate.getOutcomeMeasurements()) > 0:
        filteredList.append(gTemplate)
    else:
      absId = gTemplate.mention.tokens[0].sentence.abstract.id
      print absId,'Discarding group:',
      gTemplate.display()
#      print len(gTemplate.children), gTemplate.getSize(), len(gTemplate.getOutcomeMeasurements())
  return filteredList              

def groupClusterFilter(abstract):
  """ apply group cluster filtering to a given abstract  """
  # discard groups that are likely to be false positives                         
  gList = filterGroupList(abstract.entities.lists['group'])
  abstract.entities.lists['group'] = gList   
  
def outcomeClusterFilter(abstract):
  """ remove outcomes that are not useful or informative or may be incorrect """
  oList = abstract.entities.lists['outcome']
  newList = []
  for outcome in oList:
    if len(outcome.getMentionChain()) > 1 or outcome.isGenericMention() == False or len(outcome.getOutcomeMeasurements()) > 0:
      newList.append(outcome)  
  abstract.entities.lists['outcome'] = newList
  
      
    