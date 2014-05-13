#!/usr/bin/python
# author: Rodney Summerscales


class SemanticSentenceToken:
  """ A token in the semantic tag sentence. """

  token = None
  type = ''    # type of phrase
  
  def __init__(self, type, token):
    self.token = token
    self.type = type    
       
  def isMention(self, entityTypes):
    return self.type in entityTypes

  def toString(self):
    """ return string representing this token in the simplified sentence """
    return self.type
    
    
    
class SemanticSentence(list):
  """ Version of a given where tokens are replaced with entity labels or special token labels.
      Mentions are chunked into single tokens """
  tokenMapping = {}
  entityTypes = None
  specialTokens = set(['/', 'versus', '=', ',', 'n', 'interval', 'risk',\
       'ratio', ';', '-LRB-', '-RRB-'])     

  def __init__(self, sentence, entityTypes, useLabels):
    """ Create a version of a given sentences where tokens are replaced with entity labels 
        or special token labels.
        """
    self.tokenMapping = {}
    for token in sentence:
      self.append(SemanticSentenceToken(None, token))
      
    
    
    self.entityTypes = entityTypes
   
    curToken = None
    simpleTree = sentence.getSimpleTree()
    for tNode in simpleTree.tokenNodes():
      if tNode.isNounPhraseNode():
        # in a base noun phrase
        npUnbroken = True
        for npToken in tNode.npTokens:
          newToken = self.createOrAddToToken(curToken, npToken.token, mode)
          if newToken != None:
            curToken = newToken
            npUnbroken = False
        if npUnbroken:
          # NP did not contain any mentions or special tokens
          # create a token in simplified sentence for it
          curToken = SimpleSentenceToken('NP')     
          for npToken in tNode.npTokens:
            curToken.addToken(npToken)
          self.append(curToken)
      else: # not a base noun phrase
        newToken = self.createOrAddToToken(curToken, tNode.token, mode)
        if newToken != None:
          curToken = newToken

  def createOrAddToToken(self, simpleToken, token, mode):
    """ Either add the given sentence token to a simple sentence token 
        (if appropriate) or create, return a new simple token, or ignore the token
        If a new token is created, it is added to the simplified sentence.
    """    
    newToken = None
    
    if self.belongsWithToken(simpleToken, token, mode):
      simpleToken.addToken(token)
    elif token.isNumber():
      if token.isInteger():
        type = 'INT'
      elif token.isPercentage():
        type = 'PERCENT'
      else:
        type = 'NUM'
      newToken = SimpleSentenceToken(type, token)
      self.append(newToken)  
    elif token.lemma in self.specialTokens \
        or token.pos[0:2] == 'VB':
      newToken = SimpleSentenceToken(token.lemma, token)
      self.append(newToken)
    else:
      for type in self.entityTypes:
        if token.hasLabel(type, mode):
          newToken = SimpleSentenceToken(type, token)
          self.append(newToken)
          break
          
    return newToken
          
             
  def belongsWithToken(self, simpleToken, token, mode):
    """ return True if a given token is part of the same mention as the one
        in a given simple sentence token. """   
    if simpleToken == None or simpleToken.isMention(self.entityTypes) == False:
      return False
    return token.hasLabel(simpleToken.type, mode)  
    
  def toString(self):
    """ return a string containing all of the tokens in the simplified sentence."""
    s = []
    for sToken in self:
      s.append(sToken.type)
    return ' '.join(s)    