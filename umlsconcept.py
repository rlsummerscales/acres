#!/usr/bin/env python

""" Maintain a mapping from a term to a UMLS concept
"""

__author__ = 'Rodney L. Summerscales'

import xmlutil

class UMLSConcept:
    """ A mapping from a term to a UMLS concept in the UMLS Metathesaurus """
    id = ''
    sources = None     # list of sources where term is found
    types = []         # list of semantic types
    score = 0          # metamap score, ranges 0-1000
    snomed = ''        # snomed code
    isNegated = False
    inSnomed = False
    inRxnorm = False

    def __init__(self, node):
        """ create a new concept element given a UMLS node """
        self.id = ''
        self.types = set([])
        self.snomed = ''
        self.sources = []
        self.score = 0
        self.isNegated = False
        self.inSnomed = False
        self.inRxnorm = False

        self.id = node.getAttribute('id')
        self.snomed = node.getAttribute('snomed')
        self.score = int(node.getAttribute('score'))
        self.isNegated = node.getAttribute('negated') == 'true'
        tNodeList = node.getElementsByTagName('type')
        for tNode in tNodeList:
            self.types.add(xmlutil.getText(tNode))
        sNodeList = node.getElementsByTagName('source')
        for sNode in sNodeList:
            s = xmlutil.getText(sNode)
            if s == 'SNOMEDCT':
                self.inSnomed = True
            elif s == 'RXNORM':
                self.inRxnorm = True

    def getXML(self, doc):
        node = doc.createElement('umls')
        node.setAttribute('id', self.id)
        if len(self.snomed) > 0:
            node.setAttribute('snomed', self.snomed)
        node.setAttribute('score', str(self.score))
        if self.isNegated:
            node.setAttribute('negated', 'true')
        else:
            node.setAttribute('negated', 'false')
        for type in self.types:
            node.appendChild(xmlutil.createNodeWithTextChild(doc, 'type', type))
        if self.inSnomed:
            node.appendChild(xmlutil.createNodeWithTextChild(doc, 'source', 'SNOMEDCT'))
        if self.inRxnorm:
            node.appendChild(xmlutil.createNodeWithTextChild(doc, 'source', 'RXNORM'))

        return node
