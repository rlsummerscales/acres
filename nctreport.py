#!/usr/bin/env python 

"""
Maintain data for an clinical trials report
"""
__author__ = 'Rodney L. Summerscales'

import xmlutil

class ReportEntry:
    """ A text block for an entry in a trial registry """
    sentences = None
    name = None

    def __init__(self, node):
        """ create a list of sentences given an XML node containing a list of sentence
            elements """
        self.name = xmlutil.getNodeTagName(node)
        self.sentences = parseSentences(node)

    def getXML(self, doc):
        """ return an xml node with information for this entity """
        return createSentenceListNode(self.name, self.sentences, doc)

class Intervention:
    name = None
    description = None

    """ Intervention information from a trial registry """
    def __init__(self, node):
        self.name = []
        self.description = []
        nodes = node.getElementsByTagName('name')
        if len(nodes) > 0:
            self.name = parseSentences(nodes[0])
        nodes = node.getElementsByTagName('description')
        if len(nodes) > 0:
            self.description = parseSentences(nodes[0])

    def getXML(self, doc):
        node = doc.createElement('intervention')

        if len(self.name) > 0:
            node.appendChild(createSentenceListNode('name', self.name, doc))
        if len(self.description) > 0:
            node.appendChild(createSentenceListNode('description', self.description, doc))
        return node

class Outcome:
    """ Outcome information from a trial registry """
    primary = False
    name = None
    times = None
    description = None

    def __init__(self, node):
        self.name = []
        self.times = []
        self.description = []
        primaryStr = node.getAttribute('primary')
        if primaryStr != None and primaryStr.lower() == 'true':
            self.primary = True
        else:
            self.primary = False
        nodes = node.getElementsByTagName('name')
        if len(nodes) > 0:
            self.name = parseSentences(nodes[0])
        nodes = node.getElementsByTagName('description')
        if len(nodes) > 0:
            self.description = parseSentences(nodes[0])
        nodes = node.getElementsByTagName('times')
        if len(nodes) > 0:
            self.times = parseSentences(nodes[0])

    def getXML(self, doc):
        node = doc.createElement('outcome')
        if self.primary:
            node.setAttribute('primary', 'true')
        else:
            node.setAttribute('primary', 'false')

        if len(self.name) > 0:
            node.appendChild(createSentenceListNode('name', self.name, doc))
        if len(self.description) > 0:
            node.appendChild(createSentenceListNode('description', self.description, doc))
        if len(self.times) > 0:
            node.appendChild(createSentenceListNode('times', self.times, doc))
        return node



class Report:
    """ Data from a NCT report. """
    id = ''
    gender = ''
    minAge = ''
    maxAge = ''
    locations = None
    conditions = None
    eligibilityCriteria = None
    inclusionCriteria = None
    exclusionCriteria = None
    interventions = None
    outcomes = None

    def __init__(self, node):
        self.id = xmlutil.getTextFromNodeCalled('id', node)
        self.gender = xmlutil.getTextFromNodeCalled('gender', node)
        self.minAge = xmlutil.getTextFromNodeCalled('minAge', node)
        self.maxAge = xmlutil.getTextFromNodeCalled('maxAge', node)

        self.locations = []
        lcNodes = node.getElementsByTagName('location_countries')
        if len(lcNodes) > 0:
            cNodes = lcNodes[0].getElementsByTagName('country')
            for countryNode in cNodes:
                self.locations.append(xmlutil.getText(countryNode))

        self.conditions = []
        cNodes = node.getElementsByTagName('condition')
        for cNode in cNodes:
            self.conditions.append(ReportEntry(cNode))

        self.eligibilityCriteria = []
        ecNodes = node.getElementsByTagName('eligibility')
        if len(ecNodes) > 0:
            cNodes = ecNodes[0].getElementsByTagName('criteria')
            for cNode in cNodes:
                self.eligibilityCriteria.append(ReportEntry(cNode))

        self.inclusionCriteria = []
        icNodes = node.getElementsByTagName('inclusion')
        if len(icNodes) > 0:
            cNodes = icNodes[0].getElementsByTagName('criteria')
            for cNode in cNodes:
                self.inclusionCriteria.append(ReportEntry(cNode))

        self.exclusionCriteria = []
        ecNodes = node.getElementsByTagName('exclusion')
        if len(ecNodes) > 0:
            cNodes = ecNodes[0].getElementsByTagName('criteria')
            for cNode in cNodes:
                self.exclusionCriteria.append(ReportEntry(cNode))

        self.interventions = []
        iNodes = node.getElementsByTagName('intervention')
        for iNode in iNodes:
            self.interventions.append(Intervention(iNode))

        self.outcomes = []
        oNodes = node.getElementsByTagName('outcome')
        for oNode in oNodes:
            self.outcomes.append(Outcome(oNode))


    def getXML(self, doc):
        """ return an xml element containing information for a clinical report element"""
        node = doc.createElement('report')
        node.appendChild(xmlutil.createNodeWithTextChild(doc, 'id', self.id))
        node.appendChild(xmlutil.createNodeWithTextChild(doc, 'gender', self.gender))
        node.appendChild(xmlutil.createNodeWithTextChild(doc, 'minAge', self.minAge))
        node.appendChild(xmlutil.createNodeWithTextChild(doc, 'maxAge', self.maxAge))

        if len(self.locations) > 0:
            lcNode = doc.createElement('location_countries')
            node.appendChild(lcNode)
            for country in self.locations:
                lcNode.appendChild(xmlutil.createNodeWithTextChild(doc, 'country', country))

        for condition in self.conditions:
            node.appendChild(condition.getXML(doc))

        if len(self.eligibilityCriteria) > 0:
            ecNode = doc.createElement('eligibility')
            node.appendChild(ecNode)
            for ec in self.eligibilityCriteria:
                ecNode.appendChild(ec.getXML(doc))

        if len(self.inclusionCriteria) > 0:
            icNode = doc.createElement('inclusion')
            node.appendChild(icNode)
            for ic in self.inclusionCriteria:
                icNode.appendChild(ic.getXML(doc))

        if len(self.exclusionCriteria) > 0:
            ecNode = doc.createElement('exclusion')
            node.appendChild(ecNode)
            for ec in self.exclusionCriteria:
                ecNode.appendChild(ec.getXML(doc))

        for intervention in self.interventions:
            node.appendChild(intervention.getXML(doc))

        for outcome in self.outcomes:
            node.appendChild(outcome.getXML(doc))

        return node
