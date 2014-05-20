#!/usr/bin/python
# author: Rodney Summerscales

"""
 define classes for a sentence in an abstract
"""

import Queue
import xmlutil
import simplifiedsentence
import umlschunk
import sentencetoken
import tokenlist

from mention import Mention
from parsetree import ParseTreeNode
from parsetree import SimplifiedTreeNode



class Sentence:
    index = 0  # index of sentence within the abstract
    abstract = None
    tokens = []  # tokens in the sentence
    phrases = None
    __index = 0  # index in list of tokens
    templates = None
    annotatedTemplates = None
    section = ''  # section label from abstract
    nlmCategory = ''  # label assigned to section from pubmed
    parseString = ''  # penn treebank style parse tree for sentence
    parseTree = None  # root of parse tree
    simpleTree = None  # root of simplified parse tree
    dependencyGraphRoot = None  # root token of dependency graph for sentence
    umlsChunks = []  # list of umls terms found by metemap
    annotatedMentions = None
    detectedMentions = None
    reductionLemmas = {'less', 'reduction', 'decrease'}
    increaseLemmas = {'increase', 'more'}
    singularTimeWords = {'day', 'week', 'month', 'year'}

    def __init__(self, tokenList=None):
        self.index = None
        if tokenList == None:
            self.tokens = tokenlist.TokenList()
        else:
            assert isinstance(tokenList, tokenlist.TokenList)
            self.createFromTokenList(tokenList)
        self.phrases = None
        self.__index = 0
        self.templates = None
        self.abstract = None
        self.annotatedTemplates = None
        self.section = None
        self.nlmCategory = None
        self.parseString = ''
        self.parseTree = None
        self.dependencyGraphRoot = []
        self.umlsChunks = []
        self.annotatedMentions = {}
        self.detectedMentions = {}

    def createFromTokenList(self, tokenList):
        """ create a sentence TokenList object """
        self.tokens = tokenList
        for idx, token in enumerate(self.tokens):
            token.index = idx
            token.sentence = self

    def createFromString(self, sentenceText):
        """ create a sentence from a string of text. Tokenize on whitespace """
        tokenList = tokenlist.TokenList()
        tokenList.convertString(sentenceText)
        self.createFromTokenList(tokenList)

    def parseXML(self, sNode, index, abstract):
        self.section = sNode.getAttribute('section').replace(' ', '_')
        self.index = index
        self.abstract = abstract
        self.nlmCategory = sNode.getAttribute('nlmCategory')

        tNodes = sNode.getElementsByTagName('token')
        i = 0
        for node in tNodes:
            t = sentencetoken.Token()
            t.parseXML(node, i, self)
            self.tokens.append(t)
            i = i + 1
        if self.tokens[-1].text == '.':
            self.tokens[-1].text = '-EOS-'
            self.tokens[-1].lemma = '-EOS-'
            self.tokens[-1].pos = 'eos'

        # parse the parse tree
        pNodes = sNode.getElementsByTagName('parse')
        if len(pNodes) == 1:
            self.parseString = xmlutil.getText(pNodes[0])
            # build parse trees
            if len(self.parseString) > 0:
                self.parseTree = ParseTreeNode()
                self.parseTree.buildParseTree(self.parseString, self.tokens)
                #         self.simpleTree = SimplifiedTreeNode()
                #         self.simpleTree.buildSimplifiedTree(self.parseTree)

                for token in self.tokens:
                    for dep in token.dependents:
                        dep.token = self.tokens[dep.index]
                    for gov in token.governors:
                        gov.token = self.tokens[gov.index]
                    if token.isRoot():
                        self.dependencyGraphRoot.append(token)
                        #        self.dependencyGraphBFS()

        # build list of umls terms in sentence
        uNodeList = sNode.getElementsByTagName('umlsChunk')
        for uNode in uNodeList:
            umlsChunk = umlschunk.UMLSChunk(uNode, self)
            self.umlsChunks.append(umlsChunk)
            for i in range(umlsChunk.startIdx, umlsChunk.endIdx + 1):
                token = self.tokens[i]
                token.umlsChunks.append(umlsChunk)

        # see if we can determine the types of some of the numbers
        self.findSpecialValues()

    def findSpecialValues(self):
        """ Use rules to identify special values in the sentence """

        # First look for unlabeled intervals and measurement
        for token in self.tokens:
            if token.isNumber() and token.specialValueType == None:
                if token.index + 2 < len(self.tokens):
                    nextTokens = self.tokens[(token.index + 1):(token.index + 3)]
                    if nextTokens[0].text == 'to' and nextTokens[1].isNumber():
                        nextNextToken = nextTokens[1].nextToken()
                        if nextNextToken != None and nextNextToken.isMeasurementWord():
                            # units after next value -> measurement interval
                            token.specialValueType = 'MEASUREMENT_INTERVAL_BEGIN'
                            nextTokens[1].specialValueType = 'MEASUREMENT_INTERVAL_END'
                        else:
                            token.specialValueType = 'INTERVAL_BEGIN'
                            nextTokens[1].specialValueType = 'INTERVAL_END'

        sepTokens = {'-RRB-', '=', ','}
        inConfidenceInterval = False
        for token in self.tokens:
            if token.isSpecialValueTerm():
                valueType = token.getSpecialValueAnnotation()
                # check if the current term refers to a confidence interval
                if valueType == '95_confidence_interval':
                    inConfidenceInterval = True
                else:
                    inConfidenceInterval = False
            elif token.text.lower() == 'p':
                # look for p values
                if token.index + 2 < len(self.tokens):
                    tList = self.tokens[(token.index + 1):(token.index + 3)]
                    if tList[0].text == '=' and tList[1].isNumber():
                        tList[1].specialValueType = 'p_value'
                    elif tList[1].text == 'than' and token.index + 3 < len(self.tokens):
                        tList = self.tokens[(token.index + 1):(token.index + 4)]
                        if tList[0].text == 'less' and tList[2].isNumber():
                            tList[2].specialValueType = 'p_value'  #'p_value_less'
                        elif tList[0].text == 'greater' and tList[2].isNumber():
                            tList[2].specialValueType = 'p_value'  #'p_value_greater'

            elif token.isNumber():
                # current token is a number. Can we tell what it is?
                if token.specialValueType == 'INTERVAL_BEGIN' and inConfidenceInterval:
                    # number is the beginning of an interval and we are within scope of confidence interval term
                    token.specialValueType = 'CI_MIN'
                elif token.specialValueType == 'INTERVAL_END' and inConfidenceInterval:
                    token.specialValueType = 'CI_MAX'
                    inConfidenceInterval = False
                elif token.specialValueType != None:
                    # not a confidence interval, end scope of confidence interval
                    inConfidenceInterval = False
                elif token.specialValueType == None:
                    # Not sure what this number is yet. It is NOT an interval or a confidence interval
                    inConfidenceInterval = False

                    # get token context for the number and look for units and other keywords
                    # that will help us determine the type of number it is

                    # look at next token
                    nextToken = token.nextToken()
                    if nextToken != None:
                        if nextToken.isTimeUnitWord():
                            token.specialValueType = 'time_value'
                        elif nextToken.isMeasurementWord():
                            token.specialValueType = 'measurement_value'
                        elif nextToken.lemma == 'event':
                            token.specialValueType = 'event_count'
                        elif nextToken.text == 'times':
                            token.specialValueType = 'n_times'
                        elif token.isPercentage():
                            if nextToken.text == 'confidence':
                                # look for a different confidence interval
                                nextNextToken = nextToken.nextToken()
                                if nextNextToken != None and nextNextToken.text == 'interval':
                                    token.specialValueType = 'confidence_interval'
                                    inConfidenceInterval = True
                            # identify patterns indicated % change
                            elif nextToken.lemma in self.reductionLemmas:
                                token.specialValueType = 'percent_reduction'
                            elif nextToken.lemma == 'difference':
                                token.specialValueType = 'percent_difference'
                            elif nextToken.lemma in self.increaseLemmas:
                                token.specialValueType = 'percent_increase'

                    # if necessary, look at previous token(s)
                    prevToken = token.previousToken()
                    if token.specialValueType == None and prevToken != None:
                        # check if previous token specifies the type of number this is.
                        if prevToken.isSpecialValueTerm():
                            token.specialValueType = prevToken.getSpecialValueAnnotation()
                        # sometimes the token before that specifies the type
                        elif prevToken.text in sepTokens or prevToken.lemma == 'be':
                            prevToken = prevToken.previousToken()
                            if prevToken != None and prevToken.isSpecialValueTerm():
                                token.specialValueType = prevToken.getSpecialValueAnnotation()
                        elif prevToken.text in self.singularTimeWords and token.isInteger():
                            token.specialValueType = 'time_value'

                        # look for patterns indicating % change
                        if token.specialValueType == None and token.isPercentage():
                            prevToken = token.previousToken()
                            if prevToken.text == 'of':
                                prevToken = prevToken.previousToken()

                            if prevToken != None:
                                if prevToken.lemma in self.reductionLemmas:
                                    token.specialValueType = 'percent_reduction'
                                elif prevToken.lemma == 'difference':
                                    token.specialValueType = 'percent_difference'
                                elif prevToken.lemma in self.increaseLemmas:
                                    token.specialValueType = 'percent_increase'


    def getSimpleTree(self):
        """ build and return the simplified parse tree for this sentence """
        simpleTree = SimplifiedTreeNode()
        simpleTree.buildSimplifiedTree(self.parseTree)
        return simpleTree

    def getPrettyParseString(self):
        """ return the parse tree string with indentation added for the start of
             each new phrase """
        s = self.parseTree.prettyTreebankString()
        #    sys.exit()
        return s

    def getAnnotatedMentions(self, mType, recomputeMentions=False):
        """ return a list of annotated mentions (Mention objects) found in the
            sentence.
            mType = the type of mentions (e.g. group, outcome, etc) to find """
        if recomputeMentions == False and mType in self.annotatedMentions:
            return self.annotatedMentions[mType]
        else:
            mentionList = []
            tList = tokenlist.TokenList()
            for token in self.tokens:
                if token.hasAnnotation(mType):
                    tList.append(token)
                elif len(tList) > 0:
                    # no longer in a mention, but previous token was
                    mentionList.append(Mention(tList, annotated=True))
                    tList = tokenlist.TokenList()

            if len(tList) > 0:
                # add mention that includes last token in sentence
                mentionList.append(Mention(tList, annotated=True))
            self.annotatedMentions[mType] = mentionList

            return self.annotatedMentions[mType]

    def getDetectedMentions(self, mType, recomputeMentions=False):
        """ return a list of detected mentions (Mention objects) found in the
            sentence.
            mType = the type of mentions (e.g. group, outcome, etc) to find """
        if recomputeMentions == False and mType in self.detectedMentions:
            return self.detectedMentions[mType]
        else:
            mentionList = []
            tList = tokenlist.TokenList()
            for token in self.tokens:
                if token.hasLabel(mType):
                    tList.append(token)
                elif len(tList) > 0:
                    # no longer in a mention, but previous token was
                    mentionList.append(Mention(tList, annotated=False))
                    tList = tokenlist.TokenList()

            if len(tList) > 0:
                # add mention that includes last token in sentence
                mentionList.append(Mention(tList, annotated=False))
            self.detectedMentions[mType] = mentionList
            return self.detectedMentions[mType]

    def hasIntegers(self):
        return self.countIntegers() > 0

    def hasNumbers(self):
        return self.countNumbers() > 0

    def countIntegers(self):
        nInt = 0
        for t in self.tokens:
            if t.isInteger():
                nInt = nInt + 1
        return nInt

    def countNumbers(self):
        n = 0
        for t in self.tokens:
            #if t.isImportantNumber():
            if t.isNumber():
                n += 1
        return n

    def containsEntities(self, typeList, useAnnotation):
        """ return true if the sentence contains tokens with any of a given set of labels/annotations """
        for token in self:
            for eType in typeList:
                if useAnnotation and token.hasAnnotation(eType):
                    return True
                elif useAnnotation == False and token.hasLabel(eType):
                    return True
        return False

    def __len__(self):
        """ return number of tokens in sentence """
        return len(self.tokens)

    def getSimplifiedSentence(self, entityTypes, mode):
        """ Create and return a simplified version of the sentence that only consists
            of tokens for mentions and special tokens (e.g. numbers, verbs, symbols)
            if mode == 'train', use annotated mentions instead of detected ones. """
        return simplifiedsentence.SimplifiedSentence(self, entityTypes, mode)

        # routines needed for implementing the iterator

    def __iter__(self):
        self.__index = 0
        return self

    def next(self):
        if self.__index == len(self.tokens):
            raise StopIteration
        self.__index = self.__index + 1
        return self.tokens[self.__index - 1]

    def __getitem__(self, idx):
        """ return the ith token in the sentence """
        if 0 <= idx and idx <= len(self.tokens):
            return self.tokens[idx]
        else:
            return None


    def toString(self):
        """ return the sentence as a string """
        return self.tokens.toString()

    def getXML(self, doc):
        """ return an xml element containing sentence information """
        node = doc.createElement('sentence')
        if len(self.section) > 0:
            node.setAttribute('section', self.section)
        if len(self.nlmCategory) > 0:
            node.setAttribute('nlmCategory', self.nlmCategory)
        #    if self.templates.noTemplates() == False:
        #      node.appendChild(self.templates.getXML(doc))

        for token in self.tokens:
            node.appendChild(token.getXML(doc))

        for umlsChunk in self.umlsChunks:
            node.appendChild(umlsChunk.getXML(doc))

        if self.parseTree != None:
            s = self.parseTree.treebankString()
            #      s = self.parseString
            node.appendChild(xmlutil.createNodeWithTextChild(doc, 'parse', s))

        return node

    def dependencyGraphBFS(self):
        """ perform a Breadth-First search of the dependency graph for this sentence """
        self.markNodesUnvisited()
        for root in self.dependencyGraphRoot:
            q = Queue.Queue()
            q.put(root)
            while q.empty() == False:
                token = q.get_nowait()
                for dep in token.dependents:
                    if dep.token.isDiscovered() == False:
                        dep.token.discover()
                        for gov in dep.token.governors:
                            if gov.token == token:
                                dep.token.parent = gov
                        q.put(dep.token)
                token.visit()


    def markNodesUnvisited(self):
        """ mark each node in the graph as undiscovered and unvisited """
        for token in self.tokens:
            token.unvisit()
      
    