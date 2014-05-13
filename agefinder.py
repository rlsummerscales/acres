#!/usr/bin/python
# author: Rodney Summerscales

from rulebasedfinder import RuleBasedFinder
from agetemplate import Age

######################################################################
# Age finder
######################################################################

class AgeFinder(RuleBasedFinder):
  """ Find and label tokens in phrase describing the age range of participants
      """
  label = 'age'
  ageWords = set(['age', 'old'])
  validSpecialTypes = set(['INTERVAL_BEGIN', 'INTERVAL_END', 'time_value', None])
  
  def __init__(self):
    """ Create a finder that identifies age phrases. All tokens in 
        age phrases are labeled 'age'.
    """
    RuleBasedFinder.__init__(self, [self.label])
              
  def applyRules(self, token):
    """ Label the given token as a 'threshold'. Also label all of the neighboring 
        tokens in the same phrase.
        
        """
    if token.hasLabel(self.label) == True:
      # token has already been labeled
      return
    
    # check if we are at end of age phrase and the next token is a time word
    # If it is, add it to the age phrase. The parser sometimes omits the time unit
    # from the phrase containing the rest of the age phrase
    prev = token.previousToken()
    if prev != None and prev.hasLabel(self.label) and token.isTimeUnitWord():
      token.addLabel(self.label)
    elif token.lemma not in self.ageWords:
      return

    # label all tokens in smallest phrase structure parse subtree that contains
    # age and at least ONE number
    # however, if we also encounter any non age numbers (measurements, special numbers)
    # then we stop and discard the phrase     
    if token.parseTreeNode != None:
      numCount = 0
      nonAgeNumCount = 0
      parent = token.parseTreeNode.parent
      ageStart = 0
      ageEnd = 0
      while parent != None and parent.parent != None \
        and numCount == 0:
        tNodes = parent.tokenNodes()
        # find index of age word
        i = 0
        while tNodes[i].token != token:
          i += 1
        # establish END of age phrase
        ageEnd = i
        while ageEnd+1 < len(tNodes) and self.invalidAgeValue(tNodes[ageEnd+1].token) == False:
          ageEnd += 1
          if tNodes[ageEnd].token.isNumber():
            numCount += 1  # we already know that this is not invalid
            
        # establish START of age phrase
        ageStart = i
        while 0 <= ageStart-1 and self.invalidAgeValue(tNodes[ageStart-1].token) == False:
          ageStart -= 1
          if tNodes[ageStart].token.isNumber():
            numCount += 1  # we already know that this is not invalid
        
        if numCount == 0:
          parent = parent.parent
          
      if numCount > 0:
        for i in range(ageStart, ageEnd+1):
          tNodes[i].token.addLabel(self.label)
          
#         for tn in tNodes:
#           if tn.token.isNumber():
#             print tn.token.text, tn.token.specialValueType in self.validSpecialTypes
#             if tn.token.isPercentage()  \
#                or tn.token.specialValueType not in self.validSpecialTypes:
#                nonAgeNumCount += 1
#             else:
#               value = tn.token.getValue()
#               if value >= 1 and value <= 365:
#                 numCount += 1
#               else:
#                 nonAgeNumCount += 1
#         if numCount == 0:
#           parent = parent.parent
#       if parent != None and numCount > 0: # and nonAgeNumCount == 0:
#         for ptNode in parent.childNodes:
#           if self.labelSubTree(ptNode, token.sentence) == False:
#             break
#       elif parent != None:
#         print numCount, parent.prettyTreebankString()

  def invalidAgeValue(self, token):
    """ return True if the given token is a number that cannot be an age value """
    if token.isNumber():
#      print tn.token.text, tn.token.specialValueType in self.validSpecialTypes
      if token.isPercentage()  \
         or token.specialValueType not in self.validSpecialTypes:
        return True
      value = token.getValue()
      if value < 1 or value > 365:
        return True
    return False


  def labelSubTree(self, node, sentence):
    """ label all nodes in subtree as a 'age'. 
        Return True to continue checking tokens, False if should stop."""
    # ignore prep phrases that begin with 'with/without' as these often
    # start condition phrases.
    fToken = node.firstToken()
    if fToken != None and (fToken.text == 'with' or fToken.text == 'without'):
      return False

    if node.isTokenNode() == True:
      node.token.addLabel(self.label)
    else:
      for ptNode in node.childNodes:
        if self.labelSubTree(ptNode, sentence) == False:
          return False
    return True
            
  def compareMentionLists(self, dList, aList, mType, irStats, errorOut=None):
    """ compare list of annotated mentions with list of detected mentions.
        count number of true positives, false positives, and false negatives.
        """
    # build lists of overlapping mentions for annotated and detected mentions in this sentence
    ageTemplates = {}
    for aMention in aList:
      ageTemplates[aMention] = Age(aMention, useAnnotations=True)
      
    for dMention in dList:
      detectedAgeTemplate = Age(dMention, useAnnotations=True)
      foundMatch = False
      for aMention in aList:
        trueAgeTemplate = ageTemplates[aMention]
        if trueAgeTemplate != None and dMention.countOverlapTokens(aMention) > 1:
          # there is overlap
          # check if the detected age phrase contains all of the age values in the annotated phrase
          valuesMissing = False
          for type, avList in trueAgeTemplate.trueValues.items():
            if type in detectedAgeTemplate.trueValues:
              for trueAV in avList:
                valueMatch = False
                for detectedAV in detectedAgeTemplate.trueValues[type]:
                  if detectedAV.value == trueAV.value \
                     and detectedAV.bounds == trueAV.bounds \
                     and detectedAV.units == trueAV.units:
                    valueMatch = True
                    break
                if valueMatch == False:
                  # phrase does not contain a true age value
                  valuesMissing = True
                  break
            else:
              # no values of this type
              valuesMissing = True
              
          if valuesMissing == False and len(trueAgeTemplate.trueValues) > 0:
            self.write(errorOut, '+TP: %s == %s\n'%(dMention.text, aMention.text))
            irStats.incTP() 
            foundMatch = True
            ageTemplates[aMention] = None  # true phrase has been matched
            break
          
      if foundMatch == False:
        self.write(errorOut, '-FP: '+dMention.text+' ('+mType+')\n')
        irStats.incFP()
              
    for aMention in aList:
      if ageTemplates[aMention] != None:
       # there are no valid matches
        irStats.incFN()
        self.write(errorOut, '-FN: '+aMention.text+'\n')
         
        
      
     
      
  
