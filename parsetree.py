#!/usr/bin/python
# author: Rodney Summerscales
# contents: analyze context of mentions and values for the purpose of 
# identifying good features for mention and value detection

import sys
#import nltk
import re
import xmlutil

##############################################################
# node in a parse tree for a sentence
##############################################################
class ParseTreeNode:
  """ node in a phrase structure parse tree """
  token = None
  text = ''
  type = ''               # POS label/phrase label for node
  parent = None          # reference to parent node in parse tree
  childNodes = []        # list of children for current phrase
  
  def __init__(self, parent=None):
    self.token = None
    self.text = ''
    self.type = ''
    self.parent = parent
    self.childNodes = []
    
  def copyNodeInfo(self, node):
    """ copy data member values from given node to this one.
        A shallow copy is performed. 
        NOTE: The values of the parent and childNodes attribute are NOT copied.
    """
    self.text = node.text
    self.token = node.token
    self.type = node.type
    
  def setToken(self, token):
    """ set the token attribute to a given token object """
    self.token = token
    token.parseTreeNode = self
    self.text = token.text
    
  def buildParseTree(self, parseString, tokens):
    """ parse a given parse tree string (in penn treebank format)
        and build a parse tree rooted at this node. 
        Set the parseTreeNode attribute for each token in the list of sentence tokens
        """
    # normalize the whitespace (e.g. replace '\n' with ' ')
    parseString = re.sub('\s+', ' ', parseString)

    [treeTokenNodes, s] = self.parse(parseString)

    i = 0
    # associate token objects with their node in the parse tree
    for treeTokenNode in treeTokenNodes:
      treeTokenNode.setToken(tokens[i])
      i += 1

    
  def parse(self, parseString):
    """ take a parse tree string in penn treebank style 
        and parse it and add the children of the current node.
        input string is assumed to be the following
               ' (TYPE X) ...'
       where X may be a list of subtrees for this node (self).
       returns the list of references to token nodes that are decendents 
       of this node.
       also returns the remaining parse tree string that still needs to be parsed
    """
    tokenNodeList = []
    
    if len(parseString) > 0:
      parseString = parseString.lstrip()  # remove leading whitespace
      parseString = parseString.lstrip('(')         # remove leading parenthesis
      # remove the phrase type from the front of the string
      [self.type, space, parseString] = parseString.partition(' ')
      
      if parseString[0] != '(':
        # current node is a token node
        [self.text, rParen, parseString] = parseString.partition(')')
        self.text = xmlutil.normalizeText(self.text)
        tokenNodeList = [self]
      else:
        # current node is an internal node with children
        # process children of this node until we hit end of phrase
        while len(parseString) > 0 and parseString[0] != ')':
          # a phrase is next, parse it
          newNode = ParseTreeNode(self)
          [list, parseString] = newNode.parse(parseString)
          tokenNodeList = tokenNodeList + list
          self.childNodes.append(newNode)
        # remove right paren that marks end of current phrase  
        parseString = parseString[1:]
          
    return [tokenNodeList, parseString]
    
  def isTokenNode(self):
    """ return true if the node only contains a token (i.e. it is a leaf) """
    if len(self.childNodes) == 0:
      return True
    else:
      return False
            
  def treebankString(self):
    """ convert the subtree to a treebank style string and return it.
        """
    if self.isTokenNode():
      return ' ('+self.type+' '+self.text+')'
    else:
      s = ' ('+self.type         
      for child in self.childNodes:
        s += child.treebankString()
      return s + ')'

  def prettyTreebankString(self, indentLevel=0, indentLeaf=False):
    """ convert the subtree to a treebank style string and return it.
        indent new phrases 
        indentLevel = the number of tab widths to indent the tree."""
    indent = '  ' * indentLevel
    
    if self.isTokenNode():
      if indentLeaf:
        prefix = indent
      else:
        prefix = ''
      return prefix + '('+self.type+' '+self.text+')'
    else:
      s = indent+'('+self.type + ' '

      separator = ' '          
      indentAllNodes = False
      for child in self.childNodes:
        if child.isTokenNode() == False:
          indentAllNodes = True
          separator = '\n'
          
      for i in range(0, len(self.childNodes)):
        child = self.childNodes[i]
        if i == 0 and child.isTokenNode():
          s += child.prettyTreebankString(indentLevel + 1)
        else:
          s += separator + child.prettyTreebankString(indentLevel + 1,\
                             indentLeaf=indentAllNodes)
                
      s += ')'  
      return s
      
  def pathToRoot(self):
    """ return a string that contains the path from the current node to the root 
    """
    if self.parent == None:
      return self.type
    else:
      return self.type+'->'+self.parent.pathToRoot()

  def closestParentVerbNode(self):
    """ return the closest ancestor verb node for this node or return None"""
    if self.parent == None:
      return None
    elif self.parent.type == 'VP' and len(self.parent.childNodes) > 0 \
      and self.parent.childNodes[0] != self \
      and len(self.parent.childNodes[0].text) > 0:
      return self.parent.childNodes[0]
    else:
      return self.parent.closestParentVerbNode()
        
  def allChildrenAreTokens(self):
    """ return true if all children are leaves (token nodes) """
    for child in self.childNodes:
      if child.isTokenNode() == False:
        return False
    return True
      
  def tokenNodes(self):
    """ return list of leaf nodes (token nodes) from left to right in tree """  
    if self.isTokenNode():
      return [self]
    
    list = []
    # otherwise, node must have at least one child
    for child in self.childNodes:
      list += child.tokenNodes()
      
    return list
    
  def tokenString(self):
    """ return string containing text from token nodes from left to right in tree """
    tNodeList = self.tokenNodes()
    textList = []
    for tNode in tNodeList:
      textList.append(tNode.text)
    return ' '.join(textList)
    
  def firstToken(self):
    """ return the first token in the phrase """
    if self.isTokenNode():
      return self.token
    else:
      return self.childNodes[0].firstToken()
       
  def lastToken(self):
    """ return the last token in the phrase """
    if self.isTokenNode():
      return self.token
    else:
      return self.childNodes[-1].lastToken()
       
##############################################################
# simplified parse tree for a sentence
##############################################################

class SimplifiedTreeNode(ParseTreeNode):
  """ This is a node in a simplified parse tree. Noun phrases are chunked
      and represented by a single token.
      """
  npTokens = None   # list of tokens for a noun phrase node
  features = None
  
  def __init__(self, parent=None, node=None):
    """ initialze a new parse tree node 
          parent = parent node for this one in the simplified parse tree.
          node = parse tree node to copy info from """
    ParseTreeNode.__init__(self, parent)
    self.npTokens = None
    self.features = None
    if node != None:
      self.copyNodeInfo(node)
      self.filterTokenValue()
      if node.isTokenNode():
        self.setToken(node.token)
      
  def filterTokenValue(self):
    """ look for special token types (e.g. integer, real numbers) and 
        given them special token value """
    if self.token != None:
      if self.token.isInteger():
        self.text = 'INT'
      elif self.token.isNumber():
        self.text = 'FP_VAL'
    
    
  def setToken(self, token):
    """ set the token attribute to a given token object """
    self.token = token
    token.simplifiedTreeNode = self
    self.text = token.text
    
      
  def buildSimplifiedTree(self, root):
    """ Build a simplified parse tree given the root from a full parse tree.
        This node becomes the root of the new simplified (sub)tree.""" 
        
    self.copyNodeInfo(root)
    self.filterTokenValue()
    
    if root.type == 'NP' and len(root.childNodes) > 0 \
       and root.allChildrenAreTokens():
      # this is the root of a subtree of tokens for a base noun phrase.
      # replace this subtree with a single NP token
      self.text = '-NP-'
      self.npTokens = []
      for node in root.childNodes:
        newChild = SimplifiedTreeNode(self, node)  
        self.npTokens.append(newChild)
    else:
      # copy the node and continue to build the new simplified tree recursively
      self.childNodes = []      
      for node in root.childNodes:
        newChild = SimplifiedTreeNode(self)
        newChild.buildSimplifiedTree(node)
        self.childNodes.append(newChild)
      
  def isEntityNP(self, entityType):
    """ return true if this node is a NP and all of the tokens in have same annotation """
    if self.isNounPhraseNode() == False:
      return False
    
    nTokens = 0
    labeledTokens = 0
    ignoreTokens = set(['a', 'an', 'the'])
    for child in self.npTokens:
      if child.token != None and child.token.text not in ignoreTokens:
        nTokens += 1
        if child.token.hasAnnotation(entityType):
          labeledTokens += 1
    return nTokens == labeledTokens  
    
  def countEntityNP(self, entityType):
    """ return the number of base noun phrases where all the tokens have the same
        entity label and the number of noun phrases with at least one token annotated """
    
    entityPhrases = 0
    allNounPhrases = 0 
    nTokens = 0   
    ignoreTokens = set(['a', 'an', 'the'])

    if self.isNounPhraseNode():
      labeledTokens = 0
      for child in self.npTokens:
        if child.token != None and child.token.text not in ignoreTokens:
          nTokens += 1
          if child.token != None and child.token.hasAnnotation(entityType):
            labeledTokens += 1
          
      if labeledTokens > 0:
        allNounPhrases += 1
        if labeledTokens == nTokens:
          entityPhrases += 1

    for child in self.childNodes:
      [ep, np] = child.countEntityNP(entityType)
      entityPhrases += ep
      allNounPhrases += np
      
    return [entityPhrases, allNounPhrases]
  
  
        
  def treeString(self, includeNP=False, npEntityType=None):
    """ convert subtree rooted at this node to a string of tokens.
        if includeNP = True, include chunked noun phrase tokens in the string.
        otherwise just noun phrase tokens. """
    if self.isNounPhraseNode() == True:
      if includeNP == True and npEntityType != None:
        tokens = []
        inEntity = False
        for child in self.npTokens:
          if child.token != None and child.token.hasAnnotation(npEntityType) == False: 
            tokens.append(child.treeString(includeNP, npEntityType))
            inEntity = False
          elif inEntity == False:
            tokens.append(npEntityType.upper())
            inEntity=True
        return '['+(' '.join(tokens))+']_NP'
      elif includeNP == True:
        tokens = []
        for child in self.npTokens:
          if child.token != None:
            tokens.append(child.treeString(includeNP, npEntityType))
        return '['+(' '.join(tokens))+']_NP'
      else:
        return self.text
    elif self.isTokenNode() == True:
      return self.text
    else:
      tokens = []
      for child in self.childNodes:
        tokens.append(child.treeString(includeNP, npEntityType))
      return ' '.join(tokens)
     
  def tokenList(self):
    """ return list of tokens associated with this node (or an empty list, if none)"""
    if self.isNounPhraseNode():
      tList = []
      for child in self.npTokens:
        tList.append(child.token)
      return tList
    elif self.isTokenNode():
      return [self.token]
    else:
      return []      
       
  def isNounPhraseNode(self):
    """ return True if this node is a noun phrase token node """
    return (self.npTokens != None and len(self.npTokens) > 0)
    
  def headToken(self):
    """ return the head token (the last) in the token node """
    if self.isNounPhraseNode():
      return self.npTokens[-1].token
    elif self.isTokenNode():
      return self.token
    else:
      return None
      
##############################################################
# store a dependency relationship for a token  
##############################################################
class Dependency:
  """ Store a dependency/governor relationship for a token """
  index = -1  # index of the dependent or governor token 
  type = ''   # type of dependency relationship
  specific = None  # specific type of dependency
  token = None  # the dependent or governor token
  
  def __init__(self, node):
    self.index = int(node.getAttribute('idx'))
    self.type = node.getAttribute('type')
    self.token = None
    self.specific = node.getAttribute('specific')
      
  def isRoot(self):
    """ return True if this is a dependency from the ROOT """
    return self.type == 'root'
    
  def fullname(self):
    """ return the full type name of the dependency including the specific type info.
        e.g. return "prep_on" instead of "prep" """
    if self.specific != None and len(self.specific) > 0:
      return self.type + '_' + self.specific
    else:
      return self.type
           
  def getXML(self, doc, name):
    node = doc.createElement(name)
    node.setAttribute('type', self.type)
    if self.specific != None and len(self.specific) > 0:
      node.setAttribute('specific', self.specific)    
    node.setAttribute('idx', str(self.index))
    return node

##############################################################
# manage a list of dependency relationships for a token  
##############################################################
class DependencyList(list):
  """ A list of dependency relationships for a token """

  def __init__(self, nodeList):
    
    # parse xml node if given one
    for depNode in nodeList:
      self.append(Dependency(depNode))
        


       

