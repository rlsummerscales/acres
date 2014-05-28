#!/usr/bin/python
# author: Rodney Summerscales

"""
 Classes for storing/managing abstracts and their contents
"""


import xml.dom
import xmlutil
import nctreport
import htmlutil
import publicationinfo





##############################################################
# store an abstract
##############################################################
class Abstract:
    """ Read/write an abstract from an XML file. """
    id=''
    sentences=None
    __allSentences=None
    nIntegers = 0
    keyTermLists = None
    entities = None
    annotatedEntities = None
    summaryStats = None
    trueSummaryStats = None
    meshHeadingList = None
    __tokenSet = None            # set of all tokens in the abstract
    titleSentences = None
    affiliationSentences = None
    report = None
    acronyms = None
    publicationInformation = None

    def __init__(self, filename=None, sentenceFilter=None, loadRegistries=True):
        """ create a new abstract object
          filename = name of xml file containing abstract (optional)
          sentenceFilter = function that takes a Sentence object as a parameter
                   and returns True if the sentence should be included
                   and False if it should be ignored.
                   (optional. default is to include every sentence.)
          """
        self.id = ''
        self.sentences = []           # filtered sentence list
        self.__allSentences = []
        self.titleSentences = []
        self.affiliationSentences = []
        self.report = None
        self.nIntegers = 0
        self.keyTermLists = None
        self.entities = None
        self.annotatedEntities = None
        self.summaryStats = None
        self.trueSummaryStats = None
        self.meshHeadingList = None
        self.publicationInformation = None
        self.acronyms = {}
        if sentenceFilter == None:
            sentenceFilter = lambda sentence: True
        if filename != None:
            self.loadXML(filename, sentenceFilter, loadRegistries)
        self.__tokenSet = set([])
        self.__lemmaSet = set([])

    def loadXML(self, filename, sentenceFilter, loadRegistries):
        """ read an xml file containing an abstract """
        xmldoc = xml.dom.minidom.parse(filename)
        absNodes = xmldoc.getElementsByTagName('abstract')
        xmlutil.normalizeXMLTree(absNodes[0])

        self.id = absNodes[0].getAttribute('id')

        # read journal, author, publication info
        nodes = absNodes[0].getElementsByTagName('PublicationInformation')
        if len(nodes) > 0:
            self.publicationInformation = publicationinfo.PublicationInfo(nodes[0])

        # read title
        nodes = absNodes[0].getElementsByTagName('title')
        if len(nodes) > 0:
            self.titleSentences = xmlutil.parseSentences(nodes[0], self)

        # read affiliation
        nodes = absNodes[0].getElementsByTagName('affiliation')
        if len(nodes) > 0:
            self.affiliationSentences = xmlutil.parseSentences(nodes[0], self)

        # read abstract body text
        nodes = absNodes[0].getElementsByTagName('body')
        if len(nodes) > 0:
            self.__allSentences = xmlutil.parseSentences(nodes[0], self)
            for s in self.__allSentences:
                if sentenceFilter(s) == True:
                    self.sentences.append(s)

                    # read reports
        if loadRegistries:
            nodes = absNodes[0].getElementsByTagName('report')
            if len(nodes) > 0:
                self.report = nctreport.Report(nodes[0])

            #     meshNodes = absNodes[0].getElementsByTagName('MeshHeadingList')
            #     if meshNodes != None and len(meshNodes) > 0:
            #       self.meshHeadingList = MeshHeadingList(meshNodes[0])
        self.__buildAcronymTable()

    def __buildAcronymTable(self):
        """ look for acronym definitions in each abstract and build a table of acronyms
             and their expansions """
        for sentence in self.allSentences():
            for token in sentence:
                if token.isAcronym() and token.text not in self.acronyms \
                        and token.previousToken() != None and token.previousToken().text == '-LRB-' \
                        and token.nextToken() != None and token.nextToken().text == '-RRB-':
                    # found a new acronym definitions  (e.g.   ".... ( ACRONYM )...")
                    # determine its expansion.
                    # assume the definition is in the same sentence, to the left of the acronym
                    prevToken = token.previousToken().previousToken()
                    if prevToken != None and token.isValueAcronym() == False:
                        #          if prevToken != None:
                        # first try the "first letter" approach
                        # check if the first letter of each word up to the acronym
                        # spell out the acronym
                        i = len(token.text) - 1
                        expansion = []
                        pToken = prevToken
                        ppToken = pToken.previousToken()
                        tokensMatchAcronym = True
                        while i >= 0 and pToken != None and tokensMatchAcronym:
                            if token.text[i].lower() != pToken.text[0].lower():
                                # if first letter in this token does not match,
                                # the current letter in the acronym, try the token before it
                                expansion.append(pToken)
                                pToken = pToken.previousToken()

                            if pToken != None and token.text[i].lower() == pToken.text[0].lower():
                                expansion.append(pToken)
                                pToken = pToken.previousToken()
                                i -= 1
                            else:
                                tokensMatchAcronym = False

                        if i < 0:
                            expansion.reverse()
                        else:
                            #              print i, token.text, pToken.text, token.text[i].lower(), pToken.text[0].lower()
                            expansion = []

                        #             if i >= 0:
                        #               # first letter approach failed
                        #               # use the words in the phrase containing the word just before the acronym
                        #               expansion = []
                        #               parent = prevToken.parseTreeNode.parent
                        #               npNodes = parent.tokenNodes()
                        #               parenToken = token.previousToken()
                        #               for node in npNodes:
                        #                 if node.token == parenToken:
                        #                   break   # stop when we get to the acronymn
                        #                 expansion.append(node.token)

                        if len(expansion) > 0:
                            self.acronyms[token.text] = expansion
                            print token.text, '=',
                            for t in expansion:
                                print t.text,
                            print


    def allSentences(self):
        """ return list of all sentences in abstract, regardless of current sentence filter """
        return self.__allSentences

    def filterSentences(self, sentenceFilter):
        """ apply a given filter to determine which sentences are included in the
            main sentence list (sentence).

            Filter is applied to entire collection of sentences, not the results
            from a previous filter operation."""
        self.sentences = []
        for s in self.__allSentences:
            if sentenceFilter(s) == True:
                self.sentences.append(s)

    def getTokenSet(self):
        """ return the set of tokens contained in this abstract """
        if len(self.__tokenSet) > 0:
            return self.__tokenSet     # token set already computed, just return it

        for sentence in self.sentences:
            for token in sentence:
                self.__tokenSet.add(token.text)

        return self.__tokenSet

    def getLemmaSet(self):
        """ return the set of lemmas contained in this abstract """
        if len(self.__lemmaSet) > 0:
            return self.__lemmaSet     # token set already computed, just return it

        for sentence in self.sentences:
            for token in sentence:
                self.__lemmaSet.add(token.lemma)

        return self.__lemmaSet


    def getXML(self, doc):
        """ return xml element containing the abstract """
        node = doc.createElement('abstract')
        node.setAttribute('id', self.id)

        if self.publicationInformation is not None:
            node.appendChild(self.publicationInformation.getXML(doc))

        if len(self.titleSentences) > 0:
            tNode = xmlutil.createSentenceListNode('title', self.titleSentences, doc)
            node.appendChild(tNode)

        if len(self.affiliationSentences) > 0:
            aNode = xmlutil.createSentenceListNode('affiliation', self.affiliationSentences, doc)
            node.appendChild(aNode)

        if len(self.__allSentences) > 0:
            bNode = xmlutil.createSentenceListNode('body', self.__allSentences, doc)
            node.appendChild(bNode)

        if self.report != None:
            node.appendChild(self.report.getXML(doc))

        if self.meshHeadingList != None:
            node.appendChild(self.meshHeadingList.getXML(doc))
        return node

    def writeXML(self, filename):
        """ write abstract out to xml file with given filename """
        print 'Writing:', filename
        doc = xml.dom.minidom.Document()
        node = self.getXML(doc)
        out = open(filename, 'w')
        out.write('<?xml version="1.0" encoding="utf-8"?>\n')
        out.write('<?xml-stylesheet href="abstract.xsl" type="text/xsl"?>\n')
        xmlutil.writexml(node, out)
        out.close()

    def writeHTML(self, out, labelList=[], showError=True):
        """ write sentences in html to output stream.
            highlight correct and incorrect tokens
            of a given label type (e.g. group, outcome number).
            supports up to 7 label types. colors for label types are (in order):

            blue, green, purple, darkorange, darkcyan, maroon, brown

            if more than 7 types are specified, all types are just blue.
            tokens with incorrect labels are colored red.

            If no labels are specified, all text is black.
        """
        colors = ['blue', '#04B404', 'purple', 'darkorange', 'darkcyan',
                  'maroon', 'brown']
        incorrectColor = 'red'
        correctColor = {}

        if len(labelList) == 0:
            useColors = False  # all text is black
        else:
            useColors = True
            if len(labelList) <= len(colors):
                i = 0
                for label in labelList:
                    correctColor[label] = colors[i]
                    i += 1
            else:
                for label in labelList:
                    correctColor[label] = 'blue'

        currentSectionLabel = None
        out.write('<p>')
        for sentence in self.sentences:
            if currentSectionLabel != sentence.section:
                currentSectionLabel = sentence.section
                out.write('</p>\n<p><strong>%s: </strong>\n' % sentence.section)
            #out.write('<br> ')
            out.write(' ')
            for token in sentence:
                tokenColor = 'black'
                comment = ''
                # capitalize first letter in sentence
                if token.index == 0:
                    capitalize = True
                else:
                    capitalize = False
                text = token.getDisplayText(capitalizeFirstLetter=capitalize)
                if useColors:
                    for label in labelList:
                        if (showError == False and token.hasLabel(label) == True) \
                                or (token.hasAnnotation(label) == True and token.hasLabel(label) == True):
                            tokenColor = correctColor[label]
                        elif showError == True and token.hasAnnotation(label) == True:
                            # false negative
                            #            tokenColor = 'red'
                            #            comment = '_FN_'+label[0:2]
                            tokenColor = correctColor[label]
                            text = '<del>'+text+'</del>'
                            break
                        elif showError == True and token.hasLabel(label) == True:
                            # false positive
                            tokenColor = 'red'
                            #            comment = '_FP_'+label[0:2]
                            text += '_'+label[0:2]
                            break

                    if tokenColor == 'black':
                        makeBold = False
                    else:
                        makeBold = True
                    htmlutil.HTMLWriteText(out, text, tokenColor, bold=makeBold)
                else:
                    out.write(text)
                out.write(' ')
            out.write('\n')

        out.write('</p>')
        #      out.write('<br>'+sentence.parseString+'\n')

    def isKeyTerm(self, token):
        if self.keyTermLists != None:
            return self.keyTermLists.isKeyTerm(token, self)
        else:
            return False

    def isKeyBigram(self, token1, token2):
        if self.keyTermLists != None:
            return self.keyTermLists.isKeyBigram(token1, token2, self)
        else:
            return False

    def isKeyTrigram(self, token1, token2, token3):
        if self.keyTermLists != None:
            return self.keyTermLists.isKeyTrigram(token1, token2, token3, self)
        else:
            return False

