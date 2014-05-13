#!/usr/bin/env python 

"""
 phrase identified by MetaMap
"""

__author__ = 'Rodney L. Summerscales'


class UMLSChunk:
    startIdx = -1  # index of first token in phrase
    endIdx = -1  # index of last token in phrase
    features = None
    sentence = None
    label = None

    def __init__(self, node=None, sentence=None):
        self.startIdx = -1
        self.endIdx = -1
        self.features = {}
        self.sentence = None
        self.label = None

        if sentence != None:
            self.sentence = sentence

        # parse xml node (if given)
        if node != None:
            self.startIdx = int(node.getAttribute('start'))
            self.endIdx = int(node.getAttribute('end'))

    def getTypeString(self):
        """ return a string containing list of types separated by an underscore """
        return '_'.join(self.types)

    def getTokens(self):
        """ return list of tokens in the chunk """
        list = []
        for i in range(self.startIdx, self.endIdx + 1):
            token = self.sentence[i]
            list.append(token)
        return list

    def getBestConcepts(self):
        """ return the highest scoring concepts for this chunk """
        maxScore = -1
        bestConcepts = []
        chunkTokens = self.getTokens()
        for token in chunkTokens:
            for concept in token.umlsConcepts:
                if concept.score > maxScore:
                    maxScore = concept.score

        if maxScore > 0:
            for tokens in chunkTokens:
                for concept in token.umlsConcepts:
                    if concept.score == maxScore:
                        bestConcepts.append(concept)
        return bestConcepts

    def getXML(self, doc):
        node = doc.createElement('umlsChunk')
        node.setAttribute('start', str(self.startIdx))
        node.setAttribute('end', str(self.endIdx))
        return node
