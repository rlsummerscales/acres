#!/usr/bin/python
# Filters used to determine which sentences to read when loading abstracts
# author: Rodney Summerscales

def integerSentencesOnly(sentence):
  """ return True if the sentence contains an integer, False otherwise """
  if nonTrivialSentences(sentence) == False:
    return False
  
  return sentence.hasIntegers()

def numberSentencesOnly(sentence):
  """ return True if the sentence contains a number, False otherwise """
  if nonTrivialSentences(sentence) == False:
    return False

  return sentence.hasNumbers()

def candidateGroupSentences(sentence):
  """ return True if the sentence is likely to contain a group mention """
  if nonTrivialSentences(sentence) == False:
    return False

#  nlmLabels = set(['OBJECTIVE', 'RESULTS'])
  sectionSet = set(['INTERVENTION', 'INTERVENTIONS'])
#  if sentence.index == 0:
#    return True

  if sentence.section in sectionSet:
#    print 'ignoring:', sentence.toString()
    return False
#   if sentence.section == None or len(sentence.section) == 0:
#     return True      
#   if sentence.nlmCategory in nlmLabels or sentence.section in sectionSet:
#     return True
  return numberSentencesOnly(sentence)
        
def nonNumberSentencesOnly(sentence):
  if nonTrivialSentences(sentence) == False:
    return False

  return sentence.hasNumbers() == False
  
def primaryOutcomeSentences(sentence):
  if nonTrivialSentences(sentence) == False:
    return False

  for token in sentence:
    if token.hasLabel('primary_outcome'):
      return True
  return False
  
def outcomeNeededSentences(useAnnotations):
  keyTypes = ['on', 'eventrate']
  def sfilter(sentence):
    for token in sentence:
      for kType in keyTypes:
        if useAnnotations and token.hasAnnotation(kType):
          return True
        elif useAnnotations == False and token.hasLabel(kType):
          return True
    return False
  return sfilter
 
def numberAndOutcomeSentencesOnly(sentence):
  return numberSentencesOnly(sentence) or primaryOutcomeSentences(sentence)

def nonTrivialSentences(sentence):
  """ Ignore trivial sentences (those with less than four words) """
  return len(sentence) > 4

def allSentences(sentence):
  """ always return true. """
  return True
