#!/usr/bin/env python

"""
Store all relevant information for a token from a sentence.
"""

import re
import nltk.corpus

import xmlutil
import umlsconcept
import parsetree
from annotation import Annotation, AnnotationList


__author__ = 'Rodney L. Summerscales'


class Token:
    """ This object contains all relevant information about a token. """
    text = ''  # the token itself
    pos = ''  # part of speech tag
    #  stem=''              # stem of the token with affixes stripped
    lemma = ''  # common lemma for the word
    __units = ''
    index = -1  # position of token in sentence
    governors = None  # dependencies where this token is the dependent
    dependents = None  # dependencies where this token is the governor
    __visited = False  # has the node been officially "visited"
    __discovered = False  # has the node been discovered yet?
    parent = False  # parent on shortest path to a node in dependency graph

    features = {}
    allFeatures = {}
    semanticTags = None
    annotations = None  # annotations from original corpus
    labels = None  # annotations that have been detected by later systems
    specialValueType = None  # token is a number of a special type that we do not classify
    # e.g. HR, ARR, NNT, CI
    #  stemmer = nltk.stem.PorterStemmer()
    #  lemmatizer = nltk.stem.wordnet.WordNetLemmatizer()
    sentence = None
    parseTreeNode = None
    simplifiedTreeNode = None
    umlsChunks = None
    umlsConcepts = None
    #  numberPattern = re.compile('(-?\d+\.\d*$)|(-?\d+$)|(-?\.\d+$)')

    acronymPattern = re.compile('[A-Z]+[A-Z0-9]*$')

    specialTokenAnnotations = {'itt_analysis': 'intention to treat analysis',
                               'per_protocol_analysis': 'per protocol analysis',
                               '95_confidence_interval': '95% confidence interval',
                               'odds_ratio': 'odds ratio',
                               'hazard_ratio': 'hazard ratio',
                               'absolute_risk_reduction': 'absolute risk reduction',
                               'absolute_risk_increase': 'absolute risk increase',
                               'number_needed_to_treat': 'number needed to treat',
                               'number_needed_to_harm': 'number needed to harm',
                               'relative_risk_reduction': 'relative risk reduction',
                               'relative_risk_increase': 'relative risk increase',
                               'relative_risk': 'relative risk'}

    valueAcronyms = {'OR': 'odds_ratio', 'HR': 'hazard_ratio',
                     'ARR': 'absolute_risk_reduction', 'ARI': 'absolute_risk_increase',
                     'NNT': 'number_needed_to_treat', 'NNH': 'number_needed_to_harm',
                     'RRR': 'relative_risk_reduction', 'RRI': 'relative_risk_increase',
                     'RR': 'relative_risk', 'CI': '95_confidence_interval',
                     'SD': 'standard_deviation'}

    symbolTokens = {'~', '`', '!', '@', '#', '$', '%', '^', '&', '*', '-LRB-',
                    '-RRB-', '-', '+', '=', '<', '>', 'plus_minus', ',', '.', '/', '?',
                    '\'', ':', ';'}

    currencyWordSet = {"pound", "dollar", "euro", "$"}
    stopWordSet = nltk.corpus.stopwords.words('english')
    negationWordSet = {'not', 'no', 'without', 'never', 'neither', 'none', 'non'}
    nullNumberWords = {'none', 'no'}
    timeFrequencyWords = {'hourly', 'daily', 'weekly', 'monthly', 'yearly', 'diem'}

    def __init__(self, text='', lemma=None, pos=None):
        """ create a new token
            """
        self.text = text
        if lemma == None:
            self.lemma = self.text
        else:
            self.lemma = lemma
        if pos == None:
            self.pos = ''
        else:
            self.pos = pos

        self.__units = ''
        self.features = {}
        self.allFeatures = {}
        self.topKLabels = {}
        self.index = None
        self.semanticTags = set([])
        self.umlsChunks = []
        self.umlsConcepts = []
        self.parseTreeNode = None
        self.sentence = None
        self.simplifiedTreeNode = None
        self.__visited = False
        self.parent = None
        self.__discovered = False
        self.specialValueType = None
        self.dependents = None
        self.governors = None
        self.annotations = set([])
        self.labels = set([])

    def parseXML(self, tNode, index, sentence):
        """ create a new token from an xml token element.
            tNode = xml token element
            index = the index of the element in the sentence (0 indexed)
            sentence = the Sentence object containing this token
            """
        self.sentence = sentence
        self.index = index

        self.text = xmlutil.normalizeText(tNode.getAttribute('text'))
        if self.index == 0 and self.text[0] >= 'A' and self.text[0] <= 'Z' \
                and (len(self.text) == 1 or (self.text[1] >= 'a' and self.text[1] <= 'z')):
            # first word in the sentence is capitalized and is not part of an acronym
            self.text = self.text.lower()

        self.lemma = xmlutil.normalizeText(tNode.getAttribute('lemma'))
        if len(self.lemma) == 0:
            self.lemma = self.text

        self.pos = tNode.getAttribute('pos')
        if self.pos == None:
            self.pos = ''

        dNodes = tNode.getElementsByTagName('dep')
        self.dependents = parsetree.DependencyList(dNodes)

        gNodes = tNode.getElementsByTagName('gov')
        self.governors = parsetree.DependencyList(gNodes)
        for gov in self.governors:
            if gov.index == self.index:
                #         print 'Governor index matches dependent index'
                #         print self.text
                #         print self.sentence.toString()
                #         sys.exit()
                self.governors.remove(gov)

        aNodes = tNode.getElementsByTagName('annotation')
        self.annotations = AnnotationList(aNodes)

        lNodes = tNode.getElementsByTagName('label')
        self.labels = AnnotationList(lNodes)

        sNodes = tNode.getElementsByTagName('semantic')
        for node in sNodes:
            semTag = xmlutil.getText(node)
            self.semanticTags.add(semTag)

        uNodes = tNode.getElementsByTagName('umls')
        for node in uNodes:
            self.umlsConcepts.append(umlsconcept.UMLSConcept(node))

    def isRoot(self):
        """ return True if this token has a dependency from the root """
        if len(self.governors) == 0 and len(self.dependents) > 0:
            return True
        #       print 'ERROR: Token "'+self.text+'" has dependents, but no governors'
        #       print self.sentence.toString()
        #       sys.exit()

        for gov in self.governors:
            if gov.isRoot():
                return True
        return False

    def listOfNextTokens(self, nTokens):
        """ return list of tokens following this token """
        startIndex = self.index + 1
        stopIndex = startIndex + nTokens
        if nTokens > 0 and startIndex > 0 and stopIndex < len(self.sentence):
            return self.sentence.tokens[startIndex:stopIndex]
        else:
            return []

    def listOfPreviousTokens(self, nTokens):
        """ return list of tokens before this token """
        startIndex = self.index - nTokens
        stopIndex = self.index
        if nTokens > 0 and startIndex >= 0 and stopIndex < len(self.sentence):
            return self.sentence.tokens[startIndex:stopIndex]
        else:
            return []

    def nextToken(self):
        """ return the next token in the sentence or None if this is the
            last token in the sentence """
        nextIndex = self.index + 1
        if nextIndex < len(self.sentence):
            return self.sentence[nextIndex]
        else:
            return None

    def previousToken(self):
        """ return the previous token in the sentence or None if this is the
            first token in the sentence """
        prevIndex = self.index - 1
        if prevIndex >= 0:
            return self.sentence[prevIndex]
        else:
            return None

    def hasAnnotation(self, name):
        """ return true if the token has a given annotation """
        if name in self.annotations:
            return True
        else:
            return False

    def getAnnotationAttribute(self, name, attrib):
        """ return the given attribute value for a given annotation.
            return empty string if the token does not have the annotation or attribute

            name = name of the annotation
            attrib = name of the attribute
            """
        annotation = self.annotations.get(name)
        if annotation != None:
            return annotation.getAttributeValue(attrib)
        else:
            return ''

    def getLabelAttribute(self, name, attrib):
        """ return the given attribute value for a given label.
            return empty string if the token does not have the label or attribute

            name = name of the annotation
            attrib = name of the attribute
            """
        label = self.labels.get(name)
        if label != None:
            return label.getAttributeValue(attrib)
        else:
            return ''

    def hasLabel(self, name, mode='test'):
        """ return true if the token has a given label (assigned by classifier)
            if mode is 'train', check if the token is actually annotated with
               the given label.
            Otherwise, check the token's list of labels assigned by the system.
            (The mode parameter is optional and the default value is 'test'.)
        """
        if mode == 'train':
            return self.hasAnnotation(name)
        else:
            return name in self.labels

    def getAnnotationMatches(self, nameSet):
        """ return list of annotations matching a name in the given name set """
        matches = set([])
        for name in nameSet:
            if self.hasAnnotation(name):
                matches.add(name)
        return matches

    def getLabelMatches(self, nameSet):
        """ return list of labels matching a name in the given name set """
        matches = set([])
        for name in nameSet:
            if self.hasLabel(name):
                matches.add(name)
        return matches


    def addLabel(self, name):
        """ add a new label (assigned by a classifier) """
        label = Annotation(name)
        self.labels.add(label)

    def setLabelAttribute(self, name, attrib, value):
        """ add an attribute value to a given label.
            name = name of label
            attrib = name of attribute
            value = value of attribute
        """
        label = self.labels.get(name)
        if label == None:
            # label does not exist, create it first
            self.addLabel(name)
            label = self.labels.get(name)
        label.setAttributeValue(attrib, value)

    def addAnnotation(self, name):
        """ add a new annotation (treated as ground truth. use wisely).
            It does not add the annotation if it already exists.
        """
        if self.hasAnnotation(name) == False:
            annotation = Annotation(name)
            self.annotations.add(annotation)

    def setAnnotationAttribute(self, name, attrib, value):
        """ add an attribute value to a given Annotation.
            (treated as ground truth. use wisely).
            name = name of annotation
            attrib = name of attribute
            value = value of attribute
        """
        annotation = self.annotations.get(name)
        if annotation == None:
            # label does not exist, create it first
            self.addAnnotation(name)
            annotation = self.annotations.get(name)
        annotation.setAttributeValue(attrib, value)

    def copyAnnotation(self, token, name):
        """ copy an annotation with a given name from a given token """
        if token.hasAnnotation(name) == True and self.hasAnnotation(name) == False:
            annotation = token.annotations.get(name)
            newAnnotation = Annotation(name)
            newAnnotation.copy(annotation)
            self.annotations.add(newAnnotation)

    def convertLabelToAnnotation(self, name):
        """ transform the label with the given name into an annotation for this token.
            then remove the label from the the token. """
        if name in self.labels:
            self.annotations.add(self.labels.get(name))
            self.labels.remove(name)

    def removeAnnotation(self, name):
        """ remove an annotation that was manually assigned. """
        if name in self.annotations:
            self.annotations.remove(name)

    def removeLabel(self, name):
        """ remove a label assigned by a classifier """
        if name in self.labels:
            self.labels.remove(name)

    def removeAllLabels(self, labelList=[]):
        """ remove ALL labels assigned by a classifier. If given a list of labels,
            remove only those labels that appear on the list. """
        if len(labelList) == 0:
            self.labels = AnnotationList()
        else:
            for label in labelList:
                self.removeLabel(label)

    def addSemanticTag(self, tag):
        """ add a new semantic tag to list of semantic tags for this token """
        self.semanticTags.add(tag)

    def hasSemanticTag(self, tag):
        """ return True if token has given semantic tag """
        return tag in self.semanticTags

    def getSemanticTagMatches(self, tagList):
        """ return list of semantic tags that this token has """
        tagMatches = []
        for tag in tagList:
            if self.hasSemanticTag(tag):
                tagMatches.append(tag)
        return tagMatches

    def getFeatureSet(self):
        """ return set of all features """
        features = set([])
        for featureSet in self.features.values():
            for f in featureSet:
                features.add(f)
        return features

    def filterFeatures(self, targetFeatures):
        """ only keep features that also appear in target feature set """
        self.allFeatures = self.features
        oldFeatures = self.getFeatureSet()
        newFeatureSet = oldFeatures.intersection(targetFeatures)
        if len(newFeatureSet) == 0:
            newFeatureSet.add('NO_FEATURES')
        self.features = {}
        self.features['filtered'] = newFeatureSet

    def restoreFeatures(self):
        """ restore all features. This undoes any filtering performed by filterFeatures """
        self.features = self.allFeatures

    def getAbstract(self):
        """ return the abstract that contains this token """
        if self.sentence != None:
            return self.sentence.abstract
        else:
            return None

    def getAcronymExpansion(self):
        """ If this token is an acronym, return the list of tokens in its expansion
            (if known) """
        abstract = self.getAbstract()
        if abstract != None and self.isAcronym() and self.text in abstract.acronyms:
            return abstract.acronyms[self.text]
        else:
            return []

    def getTerm(self):
        """ return the base term used for a token in n-gram counts """
        return self.lemma

    def getFeatureText(self):
        """ get the text string to be used for generating features """
        if self.isNumber():
            #       if self.isInteger():
            #         return 'integer'
            #       else:
            #         return 'float_value'
            return 'numeric_value'
        else:
            return self.lemma
            #      return self.text.lower()

    def getSpecialTokenAnnotation(self):
        """ return the special token annotation for this token or None if it does not
            have one"""
        if self.isSpecialToken() == False:
            return None

        for annotation in self.specialTokenAnnotations:
            if self.hasAnnotation(annotation):
                return annotation
        return None

    def getDisplayText(self, capitalizeFirstLetter):
        """ Return the version of the token text meant for human reading. """
        if self.text == '-LRB-':
            return '('
        if self.text == '-RRB-':
            return ')'
        if self.text == 'plus_minus':
            return '&plusmn;'
        if self.text == '-EOS-':
            return '.'
        annotation = self.getSpecialTokenAnnotation()
        if annotation != None:
            return self.specialTokenAnnotations[annotation]
        if self.hasAnnotation('percentage'):
            return self.text + '%'
        if capitalizeFirstLetter and len(self.text) > 0:
            firstLetter = self.text[0].upper()
            return firstLetter + self.text[1:]
        return self.text

    def getXML(self, doc):
        """ return an xml element containing all token information """
        node = doc.createElement('token')
        node.setAttribute('id', str(self.index))
        node.setAttribute('text', self.text)
        if len(self.lemma) > 0 and self.lemma != self.text:
            node.setAttribute('lemma', self.lemma)
        if len(self.pos) > 0:
            node.setAttribute('pos', self.pos)

        # add governors
        for gov in self.governors:
            node.appendChild(gov.getXML(doc, 'gov'))

        # add dependents
        for dep in self.dependents:
            node.appendChild(dep.getXML(doc, 'dep'))
        # add semantic tags
        for tag in self.semanticTags:
            sNode = xmlutil.createNodeWithTextChild(doc, 'semantic', tag)
            node.appendChild(sNode)
        # add true (original) annotations
        for annotation in self.annotations:
            node.appendChild(annotation.getXML(doc, 'annotation'))
        # add detected labels
        for label in self.labels:
            node.appendChild(label.getXML(doc, 'label'))

        for uc in self.umlsConcepts:
            node.appendChild(uc.getXML(doc))

        return node

    def isImportantInteger(self):
        """  return true if the integer is one that could be an outcome number
             or group size """
        if (self.specialValueType == None and self.isInteger() == True and self.getValue() >= 0
                    and self.isPercentage() == False):
            return True
        else:
            return False

    def isImportantNumber(self):
        """  return true if the integer is one that could be an outcome number,
             group size, or event rate
        """
        if self.isNumber() and self.specialValueType is None and self.getValue() >= 0:
            return True
        else:
            return False

    def isInteger(self):
        """ return true if the token is an integer """
        if self.text.isdigit() or self.isNullNumberWord():
            return True
        else:
            return False

    def isNumber(self):
        """ return true if the token is a number (integer or floating point) """
        if self.isNullNumberWord():
            return True
        try:
            float(self.text)
            return True
        except:
            return False
            #    if self.numberPattern.match(self.text) != None or self.isNullNumberWord():
            #      return True
            #    else:
            #      return False

    def isNullNumberWord(self):
        """ return true if the token is a word that is sometimes interpreted as zero.
            {"none", "no"}
            """
        return self.text.lower() in self.nullNumberWords

    def isPercentage(self):
        """ return true if the token is a percentage number (e.g. 50%) """
        return self.hasAnnotation('percentage')

    def isSymbol(self):
        """ return true if the token is a symbol token (e.g. !, @, /, <, >)"""
        return self.text in self.symbolTokens

    def isAcronym(self):
        """ return true if the token is an acronym """
        return len(self.text) > 1 and self.acronymPattern.match(self.text) != None

    def isLocation(self):
        """ return true if the token is a location word """
        if self.text == 'USA' or self.text == 'UK':
            return True
        if self.text[0] >= 'A' and self.text[0] <= 'Z' and self.isAcronym() == False:
            for uc in self.umlsConcepts:
                if 'geoa' in uc.types:
                    return True
        return False

    def isStopWord(self):
        """ return true if the token is in a list of stop words """
        return self.text in self.stopWordSet or self.text == 'versus'

    def isSpecialToken(self):
        """ return true if the token is in a list of special tokens added during
            preprocessing phase"""
        return self.text == 'SPECIAL_TERM'

    def isSpecialValueTerm(self):
        """ return true if this token is a term that refers to a type of value found in
            medical research papers (e.g. NNT, confidence interval) """
        return (self.isSpecialToken() and self.hasAnnotation('itt_analysis') == False \
                    and self.hasAnnotation('per_protocol_analysis') == False) \
            or self.text in self.valueAcronyms

    def getSpecialValueAnnotation(self):
        """ if this token is a term that refers to a special value,
            return the corresponding annotation """
        if self.isSpecialValueTerm() == False:
            return None
        elif self.isSpecialToken():
            return self.getSpecialTokenAnnotation()
        elif self.text in self.valueAcronyms:
            return self.valueAcronyms[self.text]
        else:
            return None

    def isTimeWord(self):
        """ return true if this token appears in a list of common time words """
        return 'time' in self.semanticTags

    def isTimeUnitWord(self):
        """ return true if this token appears in a list of common time UNITS
            e.g. seconds, minutes, yrs
            but exclude time words that describe the frequency (daily, monthly, yearly) """
        return 'time' in self.semanticTags and self.text.lower() not in self.timeFrequencyWords

    def isMeasurementWord(self):
        """ return true if this token appears in a list of common units of measurement"""
        if 'measurement' in self.semanticTags:
            return True
        elif '/' in self.text:
            # check if this token matches a common pattern for ratio of units
            # i.e. units1 / units2
            parts = self.text.split('/')
            # the first character of each part should be a letter.
            # assume that this implies they are units.
            for part in parts:
                part = part.lower()
                if len(part) == 0 or part[0] < 'a' or part[0] > 'z':
                    return False
            return True

        return False

    def isCurrencyWord(self):
        """ return true if this token appears in a list of common currencies (e.g. dollars, pounds, euros)."""
        if self.lemma in self.currencyWordSet:
            return True
        else:
            return False

    def isLeftParenthesis(self):
        """ return true if this token is a left parenthesis character """
        return self.text == '-LRB-'

    def isRightParenthesis(self):
        """ return true if this token is a right parenthesis character """
        return self.text == '-RRB-'

    def getUnits(self):
        """ if this token is a measurement, e.g. mass, volume, time, return its units,
            if we know what they are, otherwise, return None.
            For now assume that the next token is the units. """
        if self.__units is not '':
            return self.__units
        elif self.isNumber():
            nextToken = self.nextToken()
            if nextToken is not None and (nextToken.isMeasurementWord() or nextToken.isCurrencyWord()):
                self.__units = nextToken.text
            elif self.previousToken() is not None and self.previousToken().isCurrencyWord():
                self.__units = self.previousToken().text

            if self.__units == '$':
                self.__units = 'dollars'

        return self.__units

    def isGroupWord(self):
        """ return true if this token is in a list of common group words."""
        return 'group' in self.semanticTags

    def isOutcomeWord(self):
        """ return true if this token is in a list of common outcome words."""
        return 'outcome' in self.semanticTags

    def isNegationWord(self):
        """ return true if this token is in a list of common negation words. """
        return self.text in self.negationWordSet

    def isValueAcronym(self):
        """ return true if this token is in a list of common value acronyms.
            (e.g. ARR, NNT, HR) """
        return self.text in self.valueAcronyms

    def isVerb(self):
        """ return true if this token is tagged as a verb """
        return self.pos[0:2] == 'VB'

    def getValue(self):
        """ return the numeric value for this token or the value 'None' if it is not a number"""
        if self.isNullNumberWord():
            return 0
        if self.isInteger():
            return int(self.text)
        if self.isNumber():
            return float(self.text)
        return None

    def visit(self):
        """ mark this token as visited """
        self.__visited = True
        self.__discovered = True

    def unvisit(self):
        """ mark token as unvisited """
        self.__visited = False
        self.__discovered = False
        self.parent = None

    def discover(self):
        """ mark token as discovered, but unvisited """
        self.__visited = False
        self.__discovered = True

    def isVisited(self):
        """ return True if token has been visited """
        return self.__visited()

    def isDiscovered(self):
        """ return True if token has been discovered """
        return self.__discovered

    def pathToRoot(self):
        if self.parent == None:
            return self.text
        else:
            return self.parent.token.pathToRoot() + '<-' + self.text

    def pathToVerb(self, includeSpecific=True):
        """ find the path from word to nearest verb in the sentence.
            follow governors. return string of dependency relationships leading to verb."""
        if self.parent == None and self.isVerb() == False:
            return 'ROOT<-' + self.lemma
        elif self.isVerb():
            return 'VB_' + self.lemma
        else:
            if includeSpecific and self.parent.specific != None and len(self.parent.specific) > 0:
                parentType = self.parent.type + '_' + self.parent.specific
            else:
                parentType = self.parent.type
            return self.parent.token.pathToVerb() + '<-' + parentType  #+':'+self.lemma

    def parentVerb(self, includeSpecific=True):
        """ find the path from word to nearest verb in the sentence.
            follow governors. return the verb."""
        if self.parent == None and self.isVerb() == False:
            return None
        elif self.isVerb():
            return self
        else:
            return self.parent.token.parentVerb()

