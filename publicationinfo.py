#!/usr/bin/env python 

"""
 Maintain publication information for an abstract
"""

__author__ = 'Rodney L. Summerscales'

import xml
import xmlutil


class PublicationInfo:
    """ Contains Journal and author information for an abstract
    """

    _journalNode = None
    _authorListNode = None
    _country = ""
    _publicationTypeListNode = None

    def __init__(self, pubInfoNode):
        """ Parse a PublicationInformation
        """
        assert pubInfoNode is not None
        assert isinstance(pubInfoNode, xml.dom.minidom.Element)

        self._journalNode = None
        self._authorListNode = None
        self._country = ""
        self._publicationTypeListNode = None

        journalNodes = pubInfoNode.getElementsByTagName('Journal')
        if len(journalNodes) > 0:
            self._journalNode = journalNodes[0].cloneNode(deep=True)

        countryNodes = pubInfoNode.getElementsByTagName('Country')
        if len(countryNodes) > 0:
            self._country = xmlutil.getText(countryNodes[0])

        authorListNodes = pubInfoNode.getElementsByTagName('AuthorList')
        if len(authorListNodes) > 0:
            self._authorListNode = authorListNodes[0].cloneNode(deep=True)

        publicationTypeListNodes = pubInfoNode.getElementsByTagName('PublicationTypeList')
        if len(publicationTypeListNodes) > 0:
            self._publicationTypeListNode = publicationTypeListNodes[0].cloneNode(deep=True)


    def getCountry(self):
        """
         Return the country of publication
        """
        return self._country

    def getJournal(self):
        """
         Return name of journal
        """
        if self._journalNode is None:
            return ''

        journalName = xmlutil.getTextFromNodeCalled('Title', self._journalNode)
        return journalName


    def getPublicationDate(self):
        """
         Return a string with month and year of publication
        """
        if self._journalNode is None:
            return ''

        year = xmlutil.getTextFromNodeCalled('Year', self._journalNode)
        return year

    def getAuthors(self):
        """
         Return list of authors for the abstract
        """
        if self._authorListNode is None:
            return []
        authorNodeList = self._authorListNode.getElementsByTagName('Author')
        authorList = []
        for authorNode in authorNodeList:
            initials = xmlutil.getTextFromNodeCalled('Initials', authorNode)
            lastName = xmlutil.getTextFromNodeCalled('LastName', authorNode)
            if lastName is  "" and initials is "":
                # no author name, it could be a collective
                collectiveName = xmlutil.getTextFromNodeCalled('CollectiveName', authorNode)
                if collectiveName is not "":
                    authorList.append(collectiveName)
            else:
                authorList.append('%s %s' % (initials, lastName))

        return authorList

    def getPublicationTypes(self):
        """
         Return list of strings describing the type of publication that the abstract is
        """
        if self._publicationTypeListNode is None:
            return []
        pTypes = []
        publicationTypeNodes = self._publicationTypeListNode.getElementsByTagName('PublicationType')
        for node in publicationTypeNodes:
            pType = xmlutil.getText(node)
            if pType is not None and pType is not "":
                pTypes.append(pType)

        return pTypes


    def getXML(self, doc):
        """
          Create an XML element with publication information
        """
        node = doc.createElement('PublicationInformation')
        if self._journalNode is not None:
            node.appendChild(self._journalNode)
        node.appendChild(xmlutil.createNodeWithTextChild(doc, 'Country', self._country))
        if self._authorListNode is not None:
            node.appendChild(self._authorListNode)
        if self._publicationTypeListNode is not None:
            node.appendChild(self._publicationTypeListNode)
        xmlutil.normalizeXMLTree(node)
        return node




