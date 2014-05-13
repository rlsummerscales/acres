#!/usr/bin/python
# author: Rodney Summerscales
# define classes for an entity mention

import re
import xml.dom
from xml.dom import minidom
from xml.dom.minidom import Document

import xmlutil
import tokenlist

##############################################################
# store a mention
##############################################################

class Mention:
  """ An object that contains all of the Token objects in a mention """
  tokens = []
  start = -1         # index of first token in mention
  end = -1           # index of last token in mention
  shortSets = []     # lists of tokens in short section(s) of mention
  text = ''          # mention text
  ignoreWords = set(['a','an','the','of','group', 'groups','arm', 'had'])
  matchedMention = None  # link to mention that has been matched with this one
  
  def __init__(self, tList, annotated=True):
    """ create a new mention object from a given list of tokens (optional)
        tList = list of token objects
        annotated = True if mention is an annotated mention
                    False if it is a detected mention 
        """
    self.tokens = tList
    self.start = -1
    self.end = -1
    self.shortSets = []
    self.text = self.tokens.toString()
    self.matchedMention = None
    if len(self.tokens) > 0:
      self.start = self.tokens[0].index
      self.end = self.tokens[-1].index
      if annotated == True:
        # build list of tokens in short sections of mention
        inShort = False   
        for i in range(0, len(self.tokens)):
          # is current token tagged as short?
          if self.tokens[i].hasAnnotation('short'):
            if inShort == False and self.tokens[i].text not in self.ignoreWords:
              # start of short section
              self.shortSets.append(set([self.tokens[i].text]))
              inShort = True
            elif self.tokens[i].text not in self.ignoreWords:
              # already in a short section, add token to last set 
              self.shortSets[-1].add(self.tokens[i].text)
          elif inShort == True:
            # reached end of short section
            inShort = False 
            
  def toString(self):
    """ return a string containing the mention text """
    return self.tokens.toString()
              
  def getSentence(self):
    """ return the sentence that contains this abstract """
    return self.tokens[0].sentence
      
  def importantTokenList(self, ignoreSemanticTagList=[]):
    """ return a TokenList with the mentions tokens (with acronyms expanded) that are
        not symbols, stop words, or common group words. 
    """
    list = tokenlist.TokenList()
    for token in self.tokens:
      if token.isAcronym():
        expansion = token.getAcronymExpansion()
        
#         print token.text, '=', 
#         for t in expansion:
#           print t.text,
#         print

#        list.append(token)
#        for t in token.getAcronymExpansion():
#          if self.isImportantToken(t):
#            list.append(t)

        if expansion == None or len(expansion) == 0:
          list.append(token)
        else:
          for t in token.getAcronymExpansion():
            if self.isImportantToken(t, ignoreSemanticTagList=ignoreSemanticTagList):
              list.append(t)
      elif self.isImportantToken(token, ignoreSemanticTagList=ignoreSemanticTagList):
        list.append(token)
        
    return list

  def allWords(self):
    """ return the list of words (actual token text) in mention.
        Do not filter out any text """
    words = set([])
    for token in self.tokens:
      words.add(token.text)
    return words

  def importantWords(self, ignoreSemanticTagList=[]):
    """ return list of important words (actual token text) in mention.
        Exclude symbols and ['the','a','of', 'an', 'group', 'groups','arm', 'had']  """
    words = set([])
    for token in self.importantTokenList(ignoreSemanticTagList=ignoreSemanticTagList):
      words.add(token.text.lower())
    return words
  
  def importantLemmas(self, ignoreSemanticTagList=[]):
    """ return list of important lemmas (lemma of actual token text) in mention.
        Exclude symbols and ['the','a','of', 'an', 'group', 'groups','arm', 'had']  """
    lemmas = set([])
    for token in self.importantTokenList(ignoreSemanticTagList=ignoreSemanticTagList):
      lemmas.add(token.lemma.lower())
    return lemmas
          
  def isImportantToken(self, token, ignoreSemanticTagList=[]):
    """ return True if a given token is considered to be important, that is,
        the token is important for determining if two mentions match """
    if len(ignoreSemanticTagList) > 0:     
      tags = token.getSemanticTagMatches(ignoreSemanticTagList)
    else:
      tags = []
    return token.isSymbol() == False \
        and token.text not in self.ignoreWords and len(tags) == 0
          
  def interestingLemmas(self):
    """ return the set of lemmas in the mention that are not symbols, stop words,
         or common group words
    """
    lemmas = set([])
    for token in self.importantTokenList():
      if token.isStopWord() == False:
        lemmas.add(token.lemma)    
    return lemmas
    
  def interestingWords(self):
    """ return the set of words in the mention that are not symbols, stop words,
         or common group words """
    words = set([])
    for token in self.importantTokenList():
      if token.isStopWord() == False:
        words.add(token.text.lower())
    return words
    
  def countOccurrences(self, wordsToCheck):
    """ return the number of times a given word appears in this mention """
    count = 0
    for token in self.importantTokenList():
      w = token.text
      for wtc in wordsToCheck:
        if wtc == w:
          count = count + 1
    return count


  def partialSetMatchAnnotated(self, annotatedMention):
    """ return true if this mention (a detected one) matches an annotated one 
        using a partial match criteria. The detected mention must match the 
        short sections of the annotated one. """
    aWords = annotatedMention.importantWords()
    dWords = self.importantWords()
     
    if dWords.intersection(aWords) == dWords:
      # this mention is a subset of the annotated mention
      if dWords == aWords:
        return True   # exact match
      if len(annotatedMention.shortSets) > 0:
        # annotated mention has short sections, try to if one is included
        # in the detected mention
        for ss in annotatedMention.shortSets:
          if ss.intersection(dWords) == ss:
            # detected mention contains all of the words in a short section
            return True
        
    return False

  def contains(self, mention):
    """ return true if this mention contains a given mention """
    return self.start <= mention.start and mention.end <= self.end
    
  def containsToken(self, token):
    """ return True if this mention contains a given token """
    if token.sentence != self.tokens[0].sentence:
      return False   # not in same sentence
    
    return self.tokens[0].index <= token.index and token.index <= self.tokens[-1].index
   
  def length(self):
    """ return the number of tokens in this mention """
    return len(self.tokens)
    
  def countOverlapTokens(self, annotatedMention):
    """ return the number of non-stopword, non-symbol tokens in the positional
        overlap between this mention and the given annotated mention.
        The overlap is based on position in the sentence. """
    if self.tokens[0].sentence != annotatedMention.tokens[0].sentence:
      return 0  # mentions in different sentences, no overlap      
    
    if self.end < annotatedMention.start or self.start > annotatedMention.end:
      return 0  # mention ends before or starts after annotated one
      
    if self.start == annotatedMention.start and self.end == annotatedMention.end:
      return len(self.tokens)  # exact match for annotated mention
      
    # There is some overlap. Does it consist of anything substantial?
    importantTokens = 0
    for token in self.tokens:
      if token.index >= annotatedMention.start \
         and token.index <= annotatedMention.end \
         and token.isSymbol() == False and token.isStopWord() == False:
         importantTokens += 1
    
    return importantTokens    
       
  def exactSetMatch(self, mention, ignoreSemanticTagList=[]):
    """ return true if this mention exactly matches annotated mention
        (ignoring common words and word order) """
    
    dWords = self.importantWords(ignoreSemanticTagList)
    aWords = mention.importantWords(ignoreSemanticTagList) 

    if len(aWords) == 0:
      # annotated mention consists of "unimportant" words.
      # use all words in mention
      dWords = self.allWords()
      aWords = mention.allWords() 

    if len(dWords) > 0 and dWords == aWords:
      return True
    else:
      return False

  def exactMatch(self, mention):
    """ return true if this mention is identical, word-for-word to given mention (ignoring word order) """
    w1 = self.allWords()
    w2 = mention.allWords()
    if len(w1) == len(w2) and w1 == w2:
      return True
    else:
      return False

  def matchAnnotated(self, annotatedMention, partialMatch=True):
    """ use the current scheme to match detected and annotated mentions.
        If this mention matches the annotated one, set the matchedMention field to 
        annotatedMention.
        
        Note: this function exists to ensure consistency between mention finder
        and summary stat matcher """
    if annotatedMention == None:
      return False

    if self.exactSetMatch(annotatedMention):
      return True
    elif partialMatch and self.countOverlapTokens(annotatedMention) > 0:
      return True

    return False
